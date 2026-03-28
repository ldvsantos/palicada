"""
Sensitivity analysis: Critical thresholds for structural failure.

Varies culm span length and flow velocity to find the combinations
where Tsai-Hill FI >= 1.0, generating design envelopes.

Also computes safety factor evolution over time for each scenario.

Author: Diego Vidal
Date: 2026-03-27
"""

import numpy as np
import pandas as pd
from pathlib import Path
import sys

# Import the main simulation module
sys.path.insert(0, str(Path(__file__).parent))
from fem_palicada_bambu import (
    generate_mesh, section_properties_degraded,
    degradation_factor, sediment_fill_fraction, vegetation_factor,
    compute_total_load, assemble_system, solve_beam, compute_stresses,
    tsai_hill_index, euler_buckling_check,
    D_EXT, D_INT, N_INTERNODE, L_NODE, E_L0, SIGMA_T_L0, TAU_LR0,
    SCENARIOS_K, HYDRO_SCENARIOS, SEGMENTS, NODE_SHEAR_FACTOR,
    WALL_THINNING_RATE, DEFL_LIMIT_RATIO, L_CULM,
)


def sensitivity_span_velocity(output_dir):
    """Sweep span length and flow velocity to find failure thresholds."""
    output_dir = Path(output_dir)

    # Parameter sweep
    span_range = np.arange(1.0, 6.5, 0.5)      # 1.0 to 6.0 m
    v_range = np.arange(0.5, 8.5, 0.5)          # 0.5 to 8.0 m/s
    t_values = [0, 2, 5, 8, 10]                  # years
    k_baseline = 0.06
    seg_data = SEGMENTS["MED"]
    H_util = seg_data["H_util"]

    results = []

    for span in span_range:
        L_e_list, is_node_zone, x_mid = generate_mesh(
            span, N_INTERNODE, L_NODE, n_elem_per_internode=4, n_elem_per_node=2
        )
        n_elem = len(L_e_list)
        n_nodes = n_elem + 1
        bc_dofs = [0, 2 * n_nodes - 2]
        mid_elem = n_elem // 2

        for v_flow in v_range:
            for t in t_values:
                deg = degradation_factor(t, k_baseline)
                E_L_t = E_L0 * deg
                sigma_t_t = SIGMA_T_L0 * deg
                tau_ult_t = TAU_LR0 * deg
                vf_t = vegetation_factor(t)

                t_loss = WALL_THINNING_RATE * t
                (A_t, I_t, Q_t, tw_t), d_int_t = section_properties_degraded(
                    D_EXT, D_INT, t_loss
                )

                h_sed_frac = sediment_fill_fraction(t)

                # Custom hydro with swept velocity
                hydro_sweep = {
                    "precip_mm": 168.1,  # P90 reference
                    "v_flow_ms": v_flow,
                    "debris_N": 200 * (v_flow / 2.0),  # scale debris with velocity
                }
                q_load = compute_total_load(H_util, h_sed_frac, hydro_sweep, t, vf_t, A_t)
                P_debris = hydro_sweep["debris_N"] * (1.0 - 0.3 * vf_t)

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

                max_fi = 0
                max_mode = "bending"
                for i in range(n_elem):
                    tau_ult_i = tau_ult_t * NODE_SHEAR_FACTOR if is_node_zone[i] else tau_ult_t
                    fi = tsai_hill_index(sigma_b[i], tau_s[i], sigma_t_t, tau_ult_i)
                    if fi > max_fi:
                        max_fi = fi
                        fi_b = (sigma_b[i] / sigma_t_t) ** 2
                        fi_s = (tau_s[i] / tau_ult_i) ** 2
                        max_mode = "shear" if fi_s > fi_b else "bending"

                max_defl = max(abs(U[2*j]) for j in range(n_nodes))
                defl_ratio = max_defl / span
                sf = 1.0 / max_fi if max_fi > 0 else 999

                results.append({
                    "span_m": round(span, 1),
                    "v_flow_ms": round(v_flow, 1),
                    "time_yr": t,
                    "max_FI": round(max_fi, 6),
                    "safety_factor": round(sf, 2),
                    "failure_mode": max_mode,
                    "max_defl_mm": round(max_defl * 1000, 4),
                    "defl_span_ratio": round(defl_ratio, 6),
                    "q_total_N_m": round(q_load, 4),
                    "deg_factor": round(deg, 4),
                })

    df = pd.DataFrame(results)
    df.to_csv(output_dir / "sensitivity_span_velocity.csv", index=False)

    # Find critical thresholds (FI >= 1.0)
    failures = df[df["max_FI"] >= 1.0]
    if len(failures) > 0:
        print(f"[OK] {len(failures)} failure combinations found.")
        print("\nFirst failures per time step:")
        for t in t_values:
            ft = failures[failures["time_yr"] == t]
            if len(ft) > 0:
                first = ft.nsmallest(1, "max_FI").iloc[0]
                print(f"  t={t}yr: span={first['span_m']}m, v={first['v_flow_ms']}m/s, "
                      f"FI={first['max_FI']:.3f}, mode={first['failure_mode']}")
    else:
        print("[INFO] No failures found in parameter sweep.")
        print("Min safety factor by time step:")
        for t in t_values:
            sub = df[df["time_yr"] == t]
            min_sf = sub["safety_factor"].min()
            row = sub[sub["safety_factor"] == min_sf].iloc[0]
            print(f"  t={t}yr: SF={min_sf:.1f} (span={row['span_m']}m, v={row['v_flow_ms']}m/s)")

    print(f"\n[OK] Sensitivity: {len(df)} rows -> sensitivity_span_velocity.csv")
    return df


def safety_factor_evolution(output_dir):
    """Safety factor over time for each combination (standard parameters)."""
    output_dir = Path(output_dir)
    times = np.arange(0, 10.5, 0.5)

    L_e_list, is_node_zone, x_mid = generate_mesh(
        L_CULM, N_INTERNODE, L_NODE, n_elem_per_internode=4, n_elem_per_node=2
    )
    n_elem = len(L_e_list)
    n_nodes = n_elem + 1
    bc_dofs = [0, 2 * n_nodes - 2]
    mid_elem = n_elem // 2

    results = []

    for seg_name, seg_data in SEGMENTS.items():
        H_util = seg_data["H_util"]
        for hydro_name, hydro in HYDRO_SCENARIOS.items():
            for scen_name, k_val in SCENARIOS_K.items():
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

                    max_fi = 0
                    max_sigma = 0
                    max_tau = 0
                    for i in range(n_elem):
                        tau_ult_i = tau_ult_t * NODE_SHEAR_FACTOR if is_node_zone[i] else tau_ult_t
                        fi = tsai_hill_index(sigma_b[i], tau_s[i], sigma_t_t, tau_ult_i)
                        if fi > max_fi:
                            max_fi = fi
                            max_sigma = sigma_b[i]
                            max_tau = tau_s[i]

                    sf = 1.0 / max_fi if max_fi > 0 else 999
                    max_defl = max(abs(U[2*j]) for j in range(n_nodes))

                    results.append({
                        "segment": seg_name,
                        "hydro_scenario": hydro_name,
                        "degradation_scenario": scen_name,
                        "time_yr": t,
                        "max_FI": round(max_fi, 6),
                        "safety_factor": round(min(sf, 999), 2),
                        "max_sigma_MPa": round(max_sigma / 1e6, 4),
                        "max_tau_MPa": round(max_tau / 1e6, 4),
                        "max_defl_mm": round(max_defl * 1000, 4),
                        "q_total_N_m": round(q_load, 4),
                        "deg_factor": round(deg, 4),
                        "veg_factor": round(vf_t, 4),
                        "wall_mm": round(tw_t * 1000, 2),
                    })

    df = pd.DataFrame(results)
    df.to_csv(output_dir / "safety_factor_evolution.csv", index=False)
    print(f"[OK] Safety factors: {len(df)} rows -> safety_factor_evolution.csv")

    # Summary table for article
    print("\n=== SAFETY FACTOR SUMMARY (worst case per segment/hydro/time) ===")
    pivot = df.pivot_table(
        index=["segment", "hydro_scenario"],
        columns="time_yr",
        values="safety_factor",
        aggfunc="min"
    )
    print(pivot[[0, 2, 5, 8, 10]].round(1).to_string())

    return df


if __name__ == "__main__":
    out = Path(__file__).parent.parent / "resultados"
    print("=" * 60)
    print("SENSITIVITY ANALYSIS: Span × Velocity")
    print("=" * 60)
    df_sens = sensitivity_span_velocity(out)

    print("\n" + "=" * 60)
    print("SAFETY FACTOR EVOLUTION")
    print("=" * 60)
    df_sf = safety_factor_evolution(out)
