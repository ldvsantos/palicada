"""
FEM 3D — Paliçada de Bambu (Frame Estrutural)
Colmos horizontais empilhados + estacas verticais cravadas no solo.
Elementos Euler-Bernoulli 3D: 12 DOF por elemento, 6 DOF por nó.
Carregamento: empuxo lateral de sedimentos (Rankine), hidrostática,
              arrasto hidrodinâmico, impacto de detritos, peso próprio.
Degradação temporal (exponencial + afinamento de parede).
Critério de falha: Tsai-Hill com SCF nas junções colmo-estaca.
Saída: CSV completo, CSV resumo, JSON de parâmetros.
"""
import numpy as np
import pandas as pd
from pathlib import Path
import json
import time as _time

# ================================================================
# 1. PARÂMETROS GLOBAIS
# ================================================================
SEGMENTS = {
    'INF': {'width': 1.50, 'height': 0.36},
    'MED': {'width': 3.00, 'height': 0.76},
    'SUP': {'width': 1.90, 'height': 0.50},
}

BAMBOO = dict(
    D_ext=0.100, D_int=0.070,          # m  (parede = 15 mm)
    E_L=12e9, G_LR=1e9,                # Pa
    sigma_tL=180e6, sigma_cL=60e6,     # Pa
    tau_LR=10e6,                        # Pa
    rho=680, nu=0.32,                   # kg m-3 , –
    node_shear_factor=0.65,             # redução cisalhante no nó
    SCF=1.8,                            # fator de concentração de tensão
    wall_thinning=0.001,                # m yr-1
    min_wall=0.003,                     # m
)

DEGRADATION = dict(optimistic=0.03, baseline=0.06, pessimistic=0.10)  # yr-1

HYDRO = dict(
    median=dict(v_flow=0.5, debris_N=50),
    P90=dict(v_flow=1.5, debris_N=200),
    P95=dict(v_flow=2.0, debris_N=400),
)

SEDIMENT = dict(gamma=15000.0, Ka=0.333)  # N m-3, –

# Tempos de saturação empíricos (anos) por segmento e cenário hidrológico,
# derivados das eficiências de retenção medidas em campo (2023-2025) e
# da série pluviométrica de 20 anos (2005-2025).
SAT_TIMES = {
    'INF': {'median': 1.7, 'P90': 0.8, 'P95': 0.8},
    'MED': {'median': 2.2, 'P90': 1.1, 'P95': 1.0},
    'SUP': {'median': 4.8, 'P90': 2.4, 'P95': 2.2},
}

VEG_R, VEG_TM, VEG_MAX = 2.0, 2.0, 0.30   # logístico
GRAVITY = 9.81
RHO_W = 1000.0
CD = 1.2

TIME_STEPS = np.arange(0, 10.5, 0.5)

MESH = dict(
    max_stake_spacing=1.50,   # m
    stake_embed=0.70,         # m
    elems_per_span=4,         # subdivisões por vão
    vert_spacing=0.12,        # m entre colmos
    colmo_embed=0.15,         # m embutimento lateral de cada colmo no talude
)


# ================================================================
# 2. PROPRIEDADES DA SEÇÃO TUBULAR
# ================================================================
def section_props(D_ext, D_int):
    A = np.pi / 4 * (D_ext**2 - D_int**2)
    I = np.pi / 64 * (D_ext**4 - D_int**4)
    J = np.pi / 32 * (D_ext**4 - D_int**4)
    Q = (D_ext**3 - D_int**3) / 12          # 1.o momento (tubular)
    t = (D_ext - D_int) / 2
    return dict(A=A, I=I, J=J, Q=Q, t=t)


# ================================================================
# 3. ELEMENTO DE VIGA 3D  (Euler-Bernoulli, 12 DOF)
# ================================================================
def beam3d_Ke(E, G, A, Iy, Iz, J, L):
    """Rigidez local 12×12 (Przemieniecki).
    DOF por nó: [u, v, w, θx, θy, θz].
    """
    k = np.zeros((12, 12))
    ea = E * A / L
    k[0, 0] = k[6, 6] = ea
    k[0, 6] = k[6, 0] = -ea
    # Plano xy (v, θz)
    a1 = 12*E*Iz/L**3; b1 = 6*E*Iz/L**2; c1 = 4*E*Iz/L; d1 = 2*E*Iz/L
    k[1,1] = k[7,7] = a1;   k[1,7] = k[7,1] = -a1
    k[1,5] = k[5,1] = b1;   k[1,11]= k[11,1]= b1
    k[5,7] = k[7,5] = -b1;  k[7,11]= k[11,7]= -b1
    k[5,5] = k[11,11]= c1;  k[5,11]= k[11,5]= d1
    # Plano xz (w, θy) — sinais acoplamento invertidos
    a2 = 12*E*Iy/L**3; b2 = 6*E*Iy/L**2; c2 = 4*E*Iy/L; d2 = 2*E*Iy/L
    k[2,2] = k[8,8] = a2;    k[2,8] = k[8,2] = -a2
    k[2,4] = k[4,2] = -b2;   k[2,10]= k[10,2]= -b2
    k[4,8] = k[8,4] = b2;    k[8,10]= k[10,8]= b2
    k[4,4] = k[10,10]= c2;   k[4,10]= k[10,4]= d2
    # Torção
    gj = G * J / L
    k[3,3] = k[9,9] = gj;  k[3,9] = k[9,3] = -gj
    return k


def rotation_matrix(x1, x2):
    """Λ (3×3): eixos locais expressos em coordenadas globais (linhas)."""
    dx = x2 - x1
    L = np.linalg.norm(dx)
    ex = dx / L
    # Vetor auxiliar: global Z, exceto se elemento quase vertical
    if abs(ex[2]) > 0.95:
        vup = np.array([1.0, 0.0, 0.0])
    else:
        vup = np.array([0.0, 0.0, 1.0])
    ey = np.cross(vup, ex)
    n = np.linalg.norm(ey)
    if n < 1e-10:
        vup = np.array([0.0, 1.0, 0.0])
        ey = np.cross(vup, ex)
        n = np.linalg.norm(ey)
    ey /= n
    ez = np.cross(ex, ey)
    return np.array([ex, ey, ez])


def T12(Lam):
    """T (12×12) bloco-diagonal de Λ."""
    T = np.zeros((12, 12))
    for i in range(4):
        T[3*i:3*i+3, 3*i:3*i+3] = Lam
    return T


# ================================================================
# 4. GERAÇÃO DA MALHA
# ================================================================
def generate_mesh(width, height):
    sp = MESH['max_stake_spacing']
    emb = MESH['stake_embed']
    eps_ = MESH['elems_per_span']
    Sv = MESH['vert_spacing']

    n_stakes = max(2, int(np.ceil(width / sp)) + 1)
    x_stakes = np.linspace(0, width, n_stakes)

    n_layers = max(2, int(np.floor(height / Sv)))
    z_layers = np.linspace(Sv, n_layers * Sv, n_layers)
    z_layers = z_layers[z_layers <= height + 1e-6]
    n_layers = len(z_layers)

    nodes = []
    nmap = {}
    elements = []

    # Nós das estacas (base, solo, junctions nas camadas)
    for si, xs in enumerate(x_stakes):
        idx = len(nodes); nodes.append([xs, 0.0, -emb]); nmap[('sb', si)] = idx
        idx = len(nodes); nodes.append([xs, 0.0, 0.0]);  nmap[('sg', si)] = idx
        for li, zl in enumerate(z_layers):
            idx = len(nodes); nodes.append([xs, 0.0, zl]); nmap[('j', si, li)] = idx

    # Elementos das estacas
    for si in range(n_stakes):
        elements.append(dict(n1=nmap[('sb', si)], n2=nmap[('sg', si)],
                             type='stake', is_nz=False, z=np.nan, layer=-1))
        elements.append(dict(n1=nmap[('sg', si)], n2=nmap[('j', si, 0)],
                             type='stake', is_nz=True, z=z_layers[0]/2, layer=0))
        for li in range(n_layers - 1):
            elements.append(dict(
                n1=nmap[('j', si, li)], n2=nmap[('j', si, li+1)],
                type='stake', is_nz=True,
                z=(z_layers[li]+z_layers[li+1])/2, layer=li+1))

    # Nós internos dos colmos
    for li, zl in enumerate(z_layers):
        for si in range(n_stakes - 1):
            x1, x2 = x_stakes[si], x_stakes[si+1]
            for ki in range(1, eps_):
                xi = x1 + (x2 - x1) * ki / eps_
                idx = len(nodes); nodes.append([xi, 0.0, zl])
                nmap[('ci', li, si, ki)] = idx

    # Elementos dos colmos
    for li, zl in enumerate(z_layers):
        for si in range(n_stakes - 1):
            span_nds = [nmap[('j', si, li)]]
            for ki in range(1, eps_):
                span_nds.append(nmap[('ci', li, si, ki)])
            span_nds.append(nmap[('j', si+1, li)])
            for ei in range(len(span_nds) - 1):
                is_nz = (ei == 0 or ei == len(span_nds) - 2)
                elements.append(dict(
                    n1=span_nds[ei], n2=span_nds[ei+1],
                    type='colmo', is_nz=is_nz, z=zl, layer=li))

    # Embutimento lateral dos colmos nos taludes (pino nas extremidades)
    emb_c = MESH['colmo_embed']
    talude_ids = []
    for li, zl in enumerate(z_layers):
        # Nó do talude esquerdo: x = -emb_c
        idx_l = len(nodes)
        nodes.append([-emb_c, 0.0, zl])
        nmap[('tl', li)] = idx_l
        talude_ids.append(idx_l)
        elements.append(dict(n1=idx_l, n2=nmap[('j', 0, li)],
                             type='colmo_embed', is_nz=False, z=zl, layer=li))
        # Nó do talude direito: x = width + emb_c
        idx_r = len(nodes)
        nodes.append([width + emb_c, 0.0, zl])
        nmap[('tr', li)] = idx_r
        talude_ids.append(idx_r)
        elements.append(dict(n1=nmap[('j', n_stakes - 1, li)], n2=idx_r,
                             type='colmo_embed', is_nz=False, z=zl, layer=li))

    nodes = np.array(nodes, dtype=float)
    return nodes, elements, x_stakes, z_layers, talude_ids


# ================================================================
# 5. DEGRADAÇÃO
# ================================================================
def degrade(t, k_deg):
    f = np.exp(-k_deg * t)
    wt = max(BAMBOO['min_wall'],
             (BAMBOO['D_ext'] - BAMBOO['D_int']) / 2 - BAMBOO['wall_thinning'] * t)
    D_int_t = BAMBOO['D_ext'] - 2 * wt
    return dict(E=BAMBOO['E_L']*f, G=BAMBOO['G_LR']*f,
                sigma_tL=BAMBOO['sigma_tL']*f, sigma_cL=BAMBOO['sigma_cL']*f,
                tau_LR=BAMBOO['tau_LR']*f,
                D_ext=BAMBOO['D_ext'], D_int=D_int_t, wall=wt, factor=f)


# ================================================================
# 6. CARREGAMENTO
# ================================================================
def _fill(t, seg_name, hydro_key):
    """Fração de preenchimento [0..1] linear até T_sat empírico."""
    t_sat = SAT_TIMES[seg_name][hydro_key]
    if t_sat <= 0:
        return 1.0
    return min(1.0, t / t_sat)


def _veg(t):
    return 1.0 / (1.0 + np.exp(-VEG_R * (t - VEG_TM)))


def compute_loads(nodes, elements, t, height, width, hydro_key, sec, seg_name):
    n_dof = len(nodes) * 6
    F = np.zeros(n_dof)
    hyd = HYDRO[hydro_key]
    v_flow, debris = hyd['v_flow'], hyd['debris_N']
    h_sed = _fill(t, seg_name, hydro_key) * height
    lf = 1.0 - VEG_MAX * _veg(t)
    A_sec = sec['A']
    # Pressão de detritos distribuída na face exposta (conserva força total).
    # Quando face exposta < Sv, detritos não impactam (paliçada quase soterrada).
    exposed_h = height - h_sed
    if exposed_h >= MESH['vert_spacing']:
        p_debris = debris / (exposed_h * max(width, 0.01))    # Pa
    else:
        p_debris = 0.0

    for elem in elements:
        n1, n2 = elem['n1'], elem['n2']
        x1, x2 = nodes[n1], nodes[n2]
        Le = np.linalg.norm(x2 - x1)
        if Le < 1e-10:
            continue

        Lam = rotation_matrix(x1, x2)
        T = T12(Lam)

        # Carga distribuída global [qx, qy, qz] N/m
        qg = np.zeros(3)

        if elem['type'] == 'colmo':
            z = elem['z']
            # Empuxo de sedimentos (direção +Y)
            if h_sed > 0 and z <= h_sed:
                p_sed = SEDIMENT['gamma'] * SEDIMENT['Ka'] * (h_sed - z)
                qg[1] += p_sed * BAMBOO['D_ext']
            # Hidrostática acima do sedimento
            h_w = min(height, h_sed * 1.1)
            if z > h_sed and z <= h_w:
                p_hyd = RHO_W * GRAVITY * (h_w - z)
                qg[1] += p_hyd * BAMBOO['D_ext']
            # Arrasto
            if z > h_sed:
                qg[1] += 0.5 * CD * RHO_W * v_flow**2 * BAMBOO['D_ext']
            # Impacto de detritos (distribuído na face exposta)
            if z > h_sed:
                qg[1] += p_debris * BAMBOO['D_ext']
            # Vegetação
            qg[1] *= lf

        # Peso próprio (global –Z)
        qg[2] = -BAMBOO['rho'] * A_sec * GRAVITY

        # Transformar para local
        ql = Lam @ qg
        qx, qy, qz_ = ql

        # Forças nodais equivalentes (local)
        fl = np.zeros(12)
        fl[0]  = qx*Le/2;   fl[6]  = qx*Le/2             # axial
        fl[1]  = qy*Le/2;   fl[5]  = qy*Le**2/12         # xy
        fl[7]  = qy*Le/2;   fl[11] = -qy*Le**2/12
        fl[2]  = qz_*Le/2;  fl[4]  = -qz_*Le**2/12       # xz
        fl[8]  = qz_*Le/2;  fl[10] = qz_*Le**2/12

        # Transformar para global e montar
        fg = T.T @ fl
        dofs = np.concatenate([np.arange(n1*6, n1*6+6),
                               np.arange(n2*6, n2*6+6)])
        F[dofs] += fg

    return F


# ================================================================
# 7. MONTAGEM E SOLUÇÃO
# ================================================================
def assemble_K(nodes, elements, mat):
    sec = section_props(mat['D_ext'], mat['D_int'])
    n_dof = len(nodes) * 6
    K = np.zeros((n_dof, n_dof))
    E, G = mat['E'], mat['G']
    A, I, J = sec['A'], sec['I'], sec['J']

    for elem in elements:
        n1, n2 = elem['n1'], elem['n2']
        x1, x2 = nodes[n1], nodes[n2]
        Le = np.linalg.norm(x2 - x1)
        if Le < 1e-10:
            continue
        ke = beam3d_Ke(E, G, A, I, I, J, Le)
        Lam = rotation_matrix(x1, x2)
        T = T12(Lam)
        kg = T.T @ ke @ T
        dofs = np.concatenate([np.arange(n1*6, n1*6+6),
                               np.arange(n2*6, n2*6+6)])
        ix = np.ix_(dofs, dofs)
        K[ix] += kg
    return K, sec


def get_fixed(nodes, talude_ids=None):
    fixed = set()
    talude_set = set(talude_ids) if talude_ids else set()
    for i, nd in enumerate(nodes):
        if nd[2] < -1e-3:           # nós enterrados → engaste total (6 DOF)
            for d in range(6):
                fixed.add(i*6 + d)
        elif i in talude_set:       # extremos no talude → pino (u,v,w fixos; θ livres)
            for d in range(3):
                fixed.add(i*6 + d)
    return sorted(fixed)


def solve_system(K, F, fixed):
    n = K.shape[0]
    free = np.array([d for d in range(n) if d not in fixed])
    U = np.zeros(n)
    Kff = K[np.ix_(free, free)]
    Ff = F[free]
    U[free] = np.linalg.solve(Kff, Ff)
    return U


# ================================================================
# 8. PÓS-PROCESSAMENTO
# ================================================================
def postprocess(nodes, elements, U, mat, sec):
    E, G = mat['E'], mat['G']
    A, I, J = sec['A'], sec['I'], sec['J']
    c = mat['D_ext'] / 2
    sigma_ult = mat['sigma_tL']
    tau_base = mat['tau_LR']
    rows = []

    for ei, elem in enumerate(elements):
        n1, n2 = elem['n1'], elem['n2']
        x1, x2 = nodes[n1], nodes[n2]
        Le = np.linalg.norm(x2 - x1)
        if Le < 1e-10:
            continue

        Lam = rotation_matrix(x1, x2)
        T = T12(Lam)
        ke = beam3d_Ke(E, G, A, I, I, J, Le)

        dofs = np.concatenate([np.arange(n1*6, n1*6+6),
                               np.arange(n2*6, n2*6+6)])
        ug = U[dofs]
        ul = T @ ug
        fl = ke @ ul

        # Momentos combinados (My, Mz) nos dois nós
        M1 = np.hypot(fl[4], fl[5])
        M2 = np.hypot(fl[10], fl[11])
        Mmax = max(M1, M2)
        # Cortantes combinados
        V1 = np.hypot(fl[1], fl[2])
        V2 = np.hypot(fl[7], fl[8])
        Vmax = max(V1, V2)

        sigma_b = Mmax * c / I if I > 0 else 0
        tau_s = Vmax * sec['Q'] / (I * 2 * sec['t']) if (I > 0 and sec['t'] > 0) else 0

        # SCF nas junções
        if elem['is_nz']:
            sigma_b *= BAMBOO['SCF']
            tau_s   *= BAMBOO['SCF']

        tau_ult = tau_base * (BAMBOO['node_shear_factor'] if elem['is_nz'] else 1.0)
        fi_b = (sigma_b / sigma_ult)**2 if sigma_ult > 0 else 0
        fi_s = (tau_s / tau_ult)**2 if tau_ult > 0 else 0
        FI = fi_b + fi_s
        SF = min(1.0 / FI, 999) if FI > 1e-15 else 999

        dy = abs((ug[1] + ug[7]) / 2)
        dz = abs((ug[2] + ug[8]) / 2)

        rows.append(dict(
            element=ei, type=elem['type'],
            x_mid=(x1[0]+x2[0])/2, z_mid=(x1[2]+x2[2])/2,
            length_m=Le, is_node_zone=elem['is_nz'], layer=elem['layer'],
            N_kN=fl[0]/1e3, V_max_kN=Vmax/1e3, M_max_Nm=Mmax,
            sigma_b_MPa=sigma_b/1e6, tau_s_MPa=tau_s/1e6,
            sigma_ult_MPa=sigma_ult/1e6, tau_ult_MPa=tau_ult/1e6,
            FI=FI, FI_bend=fi_b, FI_shear=fi_s,
            safety_factor=SF,
            mode='bending' if fi_b > fi_s else 'shear',
            disp_lat_mm=dy*1e3, disp_vert_mm=dz*1e3,
            disp_total_mm=np.hypot(dy, dz)*1e3,
        ))
    return rows


# ================================================================
# 9. LOOP PRINCIPAL DE SIMULAÇÃO
# ================================================================
def run_simulation():
    all_rows = []
    summary = []
    total = len(SEGMENTS) * len(DEGRADATION) * len(TIME_STEPS) * len(HYDRO)
    count = 0
    t0 = _time.time()

    for seg_name, sp in SEGMENTS.items():
        W, H = sp['width'], sp['height']
        nodes, elems, xs, zl, talude_ids = generate_mesh(W, H)
        fixed = get_fixed(nodes, talude_ids)
        nc = sum(1 for e in elems if e['type'] == 'colmo')
        ns = sum(1 for e in elems if e['type'] == 'stake')
        print(f"\n[{seg_name}] L={W:.2f}m  H={H:.2f}m | "
              f"{len(nodes)} nós ({nc}c+{ns}s elem)  "
              f"{len(xs)} estacas  {len(zl)} camadas  DOF={len(nodes)*6}")

        for deg_key, k_deg in DEGRADATION.items():
            for t in TIME_STEPS:
                mat = degrade(t, k_deg)
                K, sec = assemble_K(nodes, elems, mat)

                for hydro_key in HYDRO:
                    count += 1
                    Fv = compute_loads(nodes, elems, t, H, W, hydro_key, sec, seg_name)
                    U = solve_system(K, Fv, fixed)
                    res = postprocess(nodes, elems, U, mat, sec)

                    extra = dict(segment=seg_name, hydro=hydro_key,
                                 degradation=deg_key, time_yr=t,
                                 deg_factor=mat['factor'],
                                 wall_mm=mat['wall']*1e3,
                                 width_m=W, height_m=H)
                    for r in res:
                        r.update(extra)
                        all_rows.append(r)

                    res_s = [r for r in res if r['type'] != 'colmo_embed']
                    mx_fi  = max(r['FI'] for r in res_s)
                    mn_sf  = min(r['safety_factor'] for r in res_s)
                    mx_sig = max(r['sigma_b_MPa'] for r in res_s)
                    mx_tau = max(r['tau_s_MPa'] for r in res_s)
                    mx_dl  = max(r['disp_lat_mm'] for r in res_s)
                    summary.append(dict(
                        segment=seg_name, hydro=hydro_key,
                        degradation=deg_key, time_yr=t,
                        max_FI=mx_fi, safety_factor=mn_sf,
                        max_sigma_MPa=mx_sig, max_tau_MPa=mx_tau,
                        max_disp_lat_mm=mx_dl,
                        width_m=W, height_m=H))

                    if count % 100 == 0:
                        el = _time.time() - t0
                        print(f"  [{count}/{total}] {el:.0f}s")

    elapsed = _time.time() - t0
    print(f"\nSimulação concluída em {elapsed:.1f}s  ({count} combinações)")
    return pd.DataFrame(all_rows), pd.DataFrame(summary)


# ================================================================
# 10. MAIN
# ================================================================
def main():
    out = Path(__file__).resolve().parent.parent / 'resultados'
    out.mkdir(parents=True, exist_ok=True)

    hdr = "=" * 65
    print(hdr)
    print("FEM 3D — Paliçada de Bambu (Frame Colmos + Estacas)")
    print(hdr)

    # Preview da malha
    for sn, sp in SEGMENTS.items():
        nd, el, xs, zl, _ = generate_mesh(sp['width'], sp['height'])
        nc = sum(1 for e in el if e['type'] == 'colmo')
        ns = sum(1 for e in el if e['type'] == 'stake')
        print(f"  {sn}: {len(nd)} nós  ({nc} colmo + {ns} estaca elem)  "
              f"{len(xs)} est.  {len(zl)} cam.  DOF={len(nd)*6}")

    ntot = len(SEGMENTS)*len(DEGRADATION)*len(TIME_STEPS)*len(HYDRO)
    print(f"\nTotal combinações: {ntot}")

    # Simulação
    df, ds = run_simulation()

    # Salvar
    df.to_csv(out / 'fem3d_full.csv', index=False)
    ds.to_csv(out / 'fem3d_summary.csv', index=False)
    with open(out / 'fem3d_parameters.json', 'w') as f:
        json.dump(dict(
            segments=SEGMENTS, bamboo=BAMBOO, degradation=DEGRADATION,
            hydro=HYDRO, sediment=SEDIMENT, sat_times=SAT_TIMES,
            mesh=MESH, veg=dict(r=VEG_R, tm=VEG_TM, mx=VEG_MAX)),
            f, indent=2, default=str)

    # Diagnóstico
    print(f"\n{hdr}\nRESULTADOS\n{hdr}")
    print(f"Registros totais: {len(df)}")
    print(f"FI max global:    {df['FI'].max():.6f}")
    print(f"FS min global:    {ds['safety_factor'].min():.1f}")
    print(f"δ lateral max:    {df['disp_lat_mm'].max():.3f} mm")

    print("\n--- Por segmento ---")
    for sn in SEGMENTS:
        sub = df[df['segment'] == sn]
        print(f"  {sn} (L={SEGMENTS[sn]['width']}m): "
              f"FI={sub['FI'].max():.6f}  "
              f"σ={sub['sigma_b_MPa'].max():.3f} MPa  "
              f"τ={sub['tau_s_MPa'].max():.3f} MPa  "
              f"δ={sub['disp_lat_mm'].max():.3f} mm")

    print("\n--- Pior combinação ---")
    w = ds.loc[ds['max_FI'].idxmax()]
    print(f"  {w['segment']}/{w['hydro']}/{w['degradation']}  t={w['time_yr']:.1f}yr")
    print(f"  FI={w['max_FI']:.6f}   FS={w['safety_factor']:.1f}")
    print(f"  σ={w['max_sigma_MPa']:.3f} MPa   τ={w['max_tau_MPa']:.3f} MPa")
    print(f"  δ_lat={w['max_disp_lat_mm']:.3f} mm")

    # Concentração nodal
    nz = df[df['is_node_zone'] == True]
    iz = df[df['is_node_zone'] == False]
    if len(nz) > 0 and len(iz) > 0 and iz['FI'].max() > 0:
        print(f"\n--- Junções colmo-estaca ---")
        print(f"  FI_max nodal:      {nz['FI'].max():.6f}")
        print(f"  FI_max internodal: {iz['FI'].max():.6f}")
        print(f"  Razão:             {nz['FI'].max()/iz['FI'].max():.1f}×")

    # Colmo vs estaca
    co = df[df['type'] == 'colmo']
    st = df[df['type'] == 'stake']
    print(f"\n--- Colmos vs Estacas ---")
    print(f"  Colmos:  FI={co['FI'].max():.6f}  δ={co['disp_lat_mm'].max():.3f} mm")
    print(f"  Estacas: FI={st['FI'].max():.6f}  δ={st['disp_lat_mm'].max():.3f} mm")

    # Evolução temporal
    ws = w['segment']; wh = w['hydro']; wd = w['degradation']
    wc = ds[(ds['segment']==ws) & (ds['hydro']==wh) & (ds['degradation']==wd)]
    print(f"\n--- Evolução SF ({ws}/{wh}/{wd}) ---")
    for _, rr in wc.iterrows():
        bar = '*' if rr['safety_factor'] < 1.5 else ''
        print(f"  t={rr['time_yr']:5.1f}  FI={rr['max_FI']:.6f}  "
              f"FS={rr['safety_factor']:7.1f}  δ={rr['max_disp_lat_mm']:.3f}mm {bar}")

    print(f"\nArquivos salvos em: {out}")
    print(f"  fem3d_full.csv      ({len(df)} linhas)")
    print(f"  fem3d_summary.csv   ({len(ds)} linhas)")
    print(f"  fem3d_parameters.json")


if __name__ == '__main__':
    main()
