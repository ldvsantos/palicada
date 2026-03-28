"""
FEM Simulation v2: Structural failure analysis of Bambusa vulgaris check dams.

Models each bamboo culm as an Euler-Bernoulli beam with hollow circular cross-section,
orthotropic material degradation, and combined loading:
  - Hydrostatic + active earth pressure from accumulated sediment
  - Hydrodynamic drag from concentrated runoff (velocity-dependent)
  - Debris impact loads (concentrated force at midspan)
  - Self-weight

Includes: material degradation (exponential), wall thinning, sediment fill (empirical),
vegetation factor (logistic), stress concentration at internode zones.

Failure criteria:
  - Tsai-Hill (material failure)
  - Serviceability limit (deflection/span ratio > L/150)
  - Euler buckling (vertical stakes)

Author: Diego Vidal
Date: 2026-03-27
"""

import numpy as np
import pandas as pd
from pathlib import Path
import json
import warnings

warnings.filterwarnings("ignore", category=RuntimeWarning)

# ============================================================
# 1. GEOMETRIC AND MATERIAL PARAMETERS
# ============================================================

D_EXT = 0.10       # External diameter (m)
D_INT = 0.07       # Internal diameter (m) -> wall thickness ~15 mm
L_CULM = 1.50      # Culm span (m)
N_INTERNODE = 5    # Number of internodes per culm
L_NODE = 0.02      # Length of internode diaphragm zone (m)

# Orthotropic material (initial, t=0)
E_L0 = 12.0e9      # Longitudinal modulus (Pa)
E_R0 = 1.0e9       # Radial modulus (Pa)
SIGMA_T_L0 = 180e6  # Tensile strength (Pa)
SIGMA_C_L0 = 60e6   # Compressive strength (Pa)
TAU_LR0 = 10e6      # Interlaminar shear strength (Pa)
NU_LR = 0.32
RHO_BAMBOO = 680    # kg/m3

# Degradation scenarios
SCENARIOS_K = {
    "optimistic": 0.03,
    "baseline": 0.06,
    "pessimistic": 0.10,
}

# Internode weakness
NODE_SHEAR_FACTOR = 0.65
# Stress concentration factor at nodes (geometric discontinuity)
NODE_SCF = 1.8  # typical for re-entrant geometry at diaphragm

# Wall thinning due to biological attack (additional to property degradation)
WALL_THINNING_RATE = 0.001  # m/year (1 mm/year loss from inner surface)

# ============================================================
# 2. LOADING PARAMETERS
# ============================================================

RHO_W = 1000.0
RHO_S = 1500.0
G = 9.81

SEGMENTS = {
    "SUP": {"H_util": 0.50, "eff_retention": 1.12e-4, "slope_deg": 12},
    "MED": {"H_util": 0.76, "eff_retention": 1.55e-4, "slope_deg": 10},
    "INF": {"H_util": 0.36, "eff_retention": 1.97e-4, "slope_deg": 15},
}

PHI_SED = 30.0
K_A = np.tan(np.radians(45 - PHI_SED / 2)) ** 2

HYDRO_SCENARIOS = {
    "median": {"precip_mm": 95.0,  "v_flow_ms": 0.8, "debris_N": 50},
    "P90":    {"precip_mm": 168.1, "v_flow_ms": 2.0, "debris_N": 200},
    "P95":    {"precip_mm": 181.8, "v_flow_ms": 3.0, "debris_N": 400},
}

# Sediment fill curve (empirical, from Table 2)
FILL_YEARS = np.arange(0, 11)
FILL_PCT = np.array([0, 35, 60, 75, 85, 92, 96, 98, 99, 100, 100]) / 100.0

# Vegetation
VF_R = 2.0
VF_TM = 2.0

# Drag coefficient for cylinder
C_D = 1.2

# Serviceability: maximum allowable deflection
DEFL_LIMIT_RATIO = 1.0 / 150.0  # L/150

# ============================================================
# 3. CROSS-SECTION PROPERTIES
# ============================================================

def section_properties(d_ext, d_int):
    """Hollow circular cross-section."""
    A = np.pi / 4 * (d_ext**2 - d_int**2)
    I = np.pi / 64 * (d_ext**4 - d_int**4)
    Q_max = (d_ext**3 - d_int**3) / 12.0
    t_wall = (d_ext - d_int) / 2.0
    return A, I, Q_max, t_wall


def section_properties_degraded(d_ext, d_int, t_loss):
    """Section with wall thinning from inner surface."""
    d_int_new = min(d_int + 2 * t_loss, d_ext - 0.004)  # min 2mm wall
    return section_properties(d_ext, d_int_new), d_int_new

# ============================================================
# 4. FEM BEAM MODEL (Euler-Bernoulli)
# ============================================================

def beam_element_stiffness(E, I, L_e):
    c = E * I / L_e**3
    K_e = c * np.array([
        [12,     6*L_e,    -12,     6*L_e],
        [6*L_e,  4*L_e**2, -6*L_e,  2*L_e**2],
        [-12,    -6*L_e,    12,     -6*L_e],
        [6*L_e,  2*L_e**2, -6*L_e,  4*L_e**2],
    ])
    return K_e


def consistent_load_vector_udl(q, L_e):
    """UDL consistent load."""
    return q * L_e / 12.0 * np.array([6, L_e, 6, -L_e])


def concentrated_load_vector(P, L_e, a_frac=0.5):
    """Concentrated load P at fraction a_frac of element length."""
    a = a_frac * L_e
    N1 = 1 - 3*(a/L_e)**2 + 2*(a/L_e)**3
    N2 = a * (1 - a/L_e)**2
    N3 = 3*(a/L_e)**2 - 2*(a/L_e)**3
    N4 = a * ((a/L_e)**2 - a/L_e)
    return P * np.array([N1, N2, N3, N4])


def assemble_system(n_elem, L_e_list, E_list, I_list, q_list, P_conc=None, P_elem=None):
    """Assemble global K and F."""
    n_dof = 2 * (n_elem + 1)
    K_global = np.zeros((n_dof, n_dof))
    F_global = np.zeros(n_dof)

    for i in range(n_elem):
        L_e = L_e_list[i]
        K_e = beam_element_stiffness(E_list[i], I_list[i], L_e)
        f_e = consistent_load_vector_udl(q_list[i], L_e)

        dofs = [2*i, 2*i+1, 2*i+2, 2*i+3]
        for a in range(4):
            F_global[dofs[a]] += f_e[a]
            for b in range(4):
                K_global[dofs[a], dofs[b]] += K_e[a, b]

    # Concentrated load at specific element
    if P_conc is not None and P_elem is not None and P_conc > 0:
        i = P_elem
        L_e = L_e_list[i]
        f_conc = concentrated_load_vector(P_conc, L_e, 0.5)
        dofs = [2*i, 2*i+1, 2*i+2, 2*i+3]
        for a in range(4):
            F_global[dofs[a]] += f_conc[a]

    return K_global, F_global


def solve_beam(K_global, F_global, bc_dofs):
    n_dof = len(F_global)
    free_dofs = [d for d in range(n_dof) if d not in bc_dofs]
    K_ff = K_global[np.ix_(free_dofs, free_dofs)]
    F_f = F_global[free_dofs]
    U_f = np.linalg.solve(K_ff, F_f)
    U = np.zeros(n_dof)
    U[free_dofs] = U_f
    return U


def compute_stresses(U, n_elem, L_e_list, E_list, I_list, d_ext, d_int_list, is_node_zone):
    """Bending and shear stresses with SCF at node zones."""
    sigma_b = np.zeros(n_elem)
    tau_s = np.zeros(n_elem)

    for i in range(n_elem):
        L_e = L_e_list[i]
        E_i = E_list[i]
        I_i = I_list[i]
        v1, th1 = U[2*i], U[2*i+1]
        v2, th2 = U[2*i+2], U[2*i+3]

        xi = 0.5
        d2N1 = (12*xi - 6) / L_e**2
        d2N2 = (6*xi - 4) / L_e
        d2N3 = (-12*xi + 6) / L_e**2
        d2N4 = (6*xi - 2) / L_e

        d2v = d2N1*v1 + d2N2*th1 + d2N3*v2 + d2N4*th2
        M = E_i * I_i * d2v

        d3N1 = 12 / L_e**3
        d3N2 = 6 / L_e**2
        d3N3 = -12 / L_e**3
        d3N4 = 6 / L_e**2
        d3v = d3N1*v1 + d3N2*th1 + d3N3*v2 + d3N4*th2
        V = E_i * I_i * d3v

        c_out = d_ext / 2
        sigma_b[i] = abs(M * c_out / I_i)
        
        d_int_i = d_int_list[i]
        Q_i = (d_ext**3 - d_int_i**3) / 12.0
        t_wall_i = (d_ext - d_int_i) / 2.0
        if t_wall_i > 0 and I_i > 0:
            tau_s[i] = abs(V * Q_i / (I_i * 2 * t_wall_i))
        
        # Stress concentration at node zones
        if is_node_zone[i]:
            sigma_b[i] *= NODE_SCF
            tau_s[i] *= NODE_SCF

    return sigma_b, tau_s


# ============================================================
# 5. MESH GENERATION
# ============================================================

def generate_mesh(L_total, n_internode, L_node_zone, n_elem_per_internode=4, n_elem_per_node=2):
    elements = []
    positions = []
    is_node = []

    x_current = 0.0
    for seg in range(n_internode):
        L_internode = L_total / n_internode
        L_main = L_internode - L_node_zone if seg < n_internode - 1 else L_internode
        L_e_main = L_main / n_elem_per_internode
        
        for j in range(n_elem_per_internode):
            elements.append(L_e_main)
            positions.append(x_current + L_e_main / 2)
            is_node.append(False)
            x_current += L_e_main

        if seg < n_internode - 1:
            L_e_node = L_node_zone / n_elem_per_node
            for j in range(n_elem_per_node):
                elements.append(L_e_node)
                positions.append(x_current + L_e_node / 2)
                is_node.append(True)
                x_current += L_e_node

    return np.array(elements), np.array(is_node), np.array(positions)


# ============================================================
# 6. PHYSICS FUNCTIONS
# ============================================================

def degradation_factor(t, k):
    return np.exp(-k * t)


def sediment_fill_fraction(t):
    return np.interp(t, FILL_YEARS, FILL_PCT)


def vegetation_factor(t):
    return 1.0 / (1.0 + np.exp(-VF_R * (t - VF_TM)))


def compute_total_load(H_util, h_sed_frac, hydro, t, vf_t, A_cross):
    """Total distributed load q (N/m) on horizontal culm."""
    precip = hydro["precip_mm"]
    v_flow = hydro["v_flow_ms"]
    
    h_sed = h_sed_frac * H_util
    h_water = max(0, H_util - h_sed) * min(1.0, precip / 100.0)
    
    # 1. Sediment active pressure
    if h_sed > 0:
        p_sed_base = RHO_S * G * h_sed * K_A
        q_sed = p_sed_base * h_sed / 2.0 * D_EXT
    else:
        q_sed = 0.0
    
    # 2. Hydrostatic
    if h_water > 0:
        p_water_base = RHO_W * G * h_water
        q_water = p_water_base * h_water / 2.0 * D_EXT
    else:
        q_water = 0.0
    
    # 3. Hydrodynamic drag
    h_flow = min(h_water + 0.05, H_util)
    q_drag = 0.5 * C_D * RHO_W * v_flow**2 * D_EXT * h_flow / H_util
    
    # 4. Self-weight
    q_self = RHO_BAMBOO * A_cross * G
    
    # Vegetation reduces hydraulic loads
    veg_reduction = 0.4 * vf_t
    q_total = (q_sed + q_self) + (q_water + q_drag) * (1.0 - veg_reduction)
    
    return q_total


def saturation_time_from_curve(H_util, hydro, eff_retention):
    """Estimate saturation time using deposition rate."""
    precip = hydro["precip_mm"]
    rate_cm_month = eff_retention * precip
    rate_m_year = rate_cm_month * 12 / 100.0
    if rate_m_year > 0:
        t_fill = H_util / rate_m_year
        return round(min(t_fill, 10.0), 2)
    return 10.0


# ============================================================
# 7. TSAI-HILL
# ============================================================

def tsai_hill_index(sigma_b, tau_s, sigma_t_ult, tau_ult):
    return (sigma_b / sigma_t_ult) ** 2 + (tau_s / tau_ult) ** 2


# ============================================================
# 8. EULER BUCKLING
# ============================================================

def euler_buckling_check(E_L, I, H_util, h_sed_frac):
    P_cr = np.pi**2 * E_L * I / (1.2 * H_util)**2
    h_sed = h_sed_frac * H_util
    V_sed = h_sed * H_util * L_CULM * 0.3
    P_axial = V_sed * RHO_S * G / 3.0
    return P_axial / P_cr if P_cr > 0 else 0


# ============================================================
# 9. MAIN SIMULATION
# ============================================================

def run_simulation(output_dir):
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    times = np.arange(0, 10.5, 0.5)

    L_e_list, is_node_zone, x_mid = generate_mesh(
        L_CULM, N_INTERNODE, L_NODE, n_elem_per_internode=4, n_elem_per_node=2
    )
    n_elem = len(L_e_list)
    n_nodes = n_elem + 1
    bc_dofs = [0, 2 * n_nodes - 2]
    mid_elem = n_elem // 2

    all_results = []
    summary_results = []

    for seg_name, seg_data in SEGMENTS.items():
        H_util = seg_data["H_util"]

        for hydro_name, hydro in HYDRO_SCENARIOS.items():
            for scen_name, k_val in SCENARIOS_K.items():

                first_failure_time = None
                first_failure_loc = None
                first_failure_mode = None

                for t in times:
                    deg = degradation_factor(t, k_val)
                    E_L_t = E_L0 * deg
                    sigma_t_t = SIGMA_T_L0 * deg
                    tau_ult_t = TAU_LR0 * deg
                    vf_t = vegetation_factor(t)

                    t_loss = WALL_THINNING_RATE * t
                    (A_t, I_t, Q_t, tw_t), d_int_t = section_properties_degraded(
                        D_EXT, D_INT, t_loss
                    )

                    h_sed_frac = sediment_fill_fraction(t)
                    q_load = compute_total_load(H_util, h_sed_frac, hydro, t, vf_t, A_t)
                    P_debris = hydro["debris_N"] * (1.0 - 0.3 * vf_t)

                    E_arr = np.full(n_elem, E_L_t)
                    I_arr = np.full(n_elem, I_t)
                    q_arr = np.full(n_elem, q_load)
                    d_int_arr = np.full(n_elem, d_int_t)

                    K_global, F_global = assemble_system(
                        n_elem, L_e_list, E_arr, I_arr, q_arr,
                        P_conc=P_debris, P_elem=mid_elem
                    )
                    U = solve_beam(K_global, F_global, bc_dofs)

                    sigma_b, tau_s = compute_stresses(
                        U, n_elem, L_e_list, E_arr, I_arr, D_EXT, d_int_arr, is_node_zone
                    )

                    max_defl = max(abs(U[2*j]) for j in range(n_nodes))
                    defl_ratio = max_defl / L_CULM

                    for i in range(n_elem):
                        tau_ult_i = tau_ult_t * NODE_SHEAR_FACTOR if is_node_zone[i] else tau_ult_t
                        fi = tsai_hill_index(sigma_b[i], tau_s[i], sigma_t_t, tau_ult_i)

                        fi_bending = (sigma_b[i] / sigma_t_t) ** 2
                        fi_shear = (tau_s[i] / tau_ult_i) ** 2
                        mode = "shear" if fi_shear > fi_bending else "bending"

                        all_results.append({
                            "segment": seg_name,
                            "hydro_scenario": hydro_name,
                            "degradation_scenario": scen_name,
                            "time_yr": t,
                            "element": i,
                            "x_mid_m": round(x_mid[i], 4),
                            "is_node_zone": bool(is_node_zone[i]),
                            "q_effective_N_m": round(q_load, 4),
                            "deflection_mm": round(abs(U[2*(i+1)]) * 1000, 4),
                            "sigma_bending_MPa": round(sigma_b[i] / 1e6, 6),
                            "tau_shear_MPa": round(tau_s[i] / 1e6, 6),
                            "failure_index": round(fi, 6),
                            "failure_mode": mode,
                            "E_L_GPa": round(E_L_t / 1e9, 4),
                            "sigma_t_ult_MPa": round(sigma_t_t / 1e6, 4),
                            "tau_ult_MPa": round(tau_ult_i / 1e6, 4),
                            "sed_fill_pct": round(h_sed_frac * 100, 1),
                            "veg_factor": round(vf_t, 4),
                            "deg_factor": round(deg, 4),
                            "defl_span_ratio": round(defl_ratio, 6),
                            "wall_thickness_mm": round(tw_t * 1000, 2),
                        })

                        if fi >= 1.0 and first_failure_time is None:
                            first_failure_time = t
                            first_failure_loc = x_mid[i]
                            first_failure_mode = mode

                    if defl_ratio >= DEFL_LIMIT_RATIO and first_failure_time is None:
                        first_failure_time = t
                        first_failure_loc = x_mid[mid_elem]
                        first_failure_mode = "serviceability"

                    buck_ratio = euler_buckling_check(E_L_t, I_t, H_util, h_sed_frac)
                    if buck_ratio >= 1.0 and first_failure_time is None:
                        first_failure_time = t
                        first_failure_loc = -1
                        first_failure_mode = "buckling"

                sat_time = saturation_time_from_curve(H_util, hydro, seg_data["eff_retention"])

                summary_results.append({
                    "segment": seg_name,
                    "hydro_scenario": hydro_name,
                    "degradation_scenario": scen_name,
                    "first_failure_time_yr": first_failure_time,
                    "first_failure_x_m": first_failure_loc,
                    "first_failure_mode": first_failure_mode,
                    "saturation_time_yr": sat_time,
                })

    df_all = pd.DataFrame(all_results)
    df_summary = pd.DataFrame(summary_results)

    df_all.to_csv(output_dir / "fem_results_full.csv", index=False)
    df_summary.to_csv(output_dir / "fem_summary_failure.csv", index=False)

    params = {
        "geometry": {
            "D_ext_m": D_EXT, "D_int_m": D_INT, "L_culm_m": L_CULM,
            "n_internode": N_INTERNODE, "L_node_m": L_NODE,
            "wall_thinning_rate_m_yr": WALL_THINNING_RATE,
        },
        "material_initial": {
            "E_L_GPa": E_L0/1e9, "E_R_GPa": E_R0/1e9,
            "sigma_T_L_MPa": SIGMA_T_L0/1e6, "sigma_C_L_MPa": SIGMA_C_L0/1e6,
            "tau_LR_MPa": TAU_LR0/1e6, "nu_LR": NU_LR, "rho_kg_m3": RHO_BAMBOO,
        },
        "degradation_k": SCENARIOS_K,
        "node_zone": {
            "shear_factor": NODE_SHEAR_FACTOR,
            "stress_concentration_factor": NODE_SCF,
        },
        "segments": {k: {"H_util_m": v["H_util"], "slope_deg": v["slope_deg"]}
                     for k, v in SEGMENTS.items()},
        "hydrological": {k: v for k, v in HYDRO_SCENARIOS.items()},
        "n_elements": int(n_elem),
        "n_nodes": int(n_nodes),
        "drag_coefficient": C_D,
        "serviceability_limit": DEFL_LIMIT_RATIO,
    }
    with open(output_dir / "simulation_parameters.json", "w") as f:
        json.dump(params, f, indent=2)

    print(f"[OK] Full: {len(df_all)} rows -> fem_results_full.csv")
    print(f"[OK] Summary: {len(df_summary)} rows -> fem_summary_failure.csv")
    print("\n=== FAILURE SUMMARY ===")
    pd.set_option("display.max_columns", 10)
    pd.set_option("display.width", 150)
    print(df_summary.to_string(index=False))

    print("\n=== MAX FAILURE INDEX (top 10) ===")
    top = df_all.nlargest(10, "failure_index")[
        ["segment", "hydro_scenario", "degradation_scenario", "time_yr",
         "x_mid_m", "is_node_zone", "failure_index", "failure_mode",
         "sigma_bending_MPa", "tau_shear_MPa"]
    ]
    print(top.to_string(index=False))

    return df_all, df_summary


if __name__ == "__main__":
    out = Path(__file__).parent.parent / "resultados"
    run_simulation(out)
