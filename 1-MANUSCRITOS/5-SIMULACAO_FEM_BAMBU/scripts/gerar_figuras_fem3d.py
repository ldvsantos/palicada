"""
Geração de figuras para o artigo FEM 3D da paliçada de bambu.
Lê resultados de fem_palicada_3d.py (fem3d_full.csv, fem3d_summary.csv).
Salva figuras em PNG e PDF (300 dpi).
"""
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
from pathlib import Path
import json

plt.rcParams.update({
    "font.family": "serif",
    "font.size": 11,
    "axes.labelsize": 12,
    "axes.titlesize": 13,
    "legend.fontsize": 9,
    "figure.dpi": 150,
    "savefig.dpi": 300,
    "savefig.bbox": "tight",
})

BASE = Path(__file__).resolve().parent.parent
RES = BASE / 'resultados'
FIG = BASE / 'figuras'
FIG.mkdir(parents=True, exist_ok=True)


def load():
    df = pd.read_csv(RES / 'fem3d_full.csv')
    ds = pd.read_csv(RES / 'fem3d_summary.csv')
    with open(RES / 'fem3d_parameters.json') as f:
        par = json.load(f)
    return df, ds, par


def save(fig, name):
    for ext in ['png', 'pdf']:
        fig.savefig(FIG / f'{name}.{ext}')
    plt.close(fig)
    print(f'  {name}')


# ================================================================
# HELPER — resolver 1 caso e retornar nós, elementos, U, FI por elemento
# ================================================================
def _solve_single(seg_name, hydro_key, deg_key, t_yr):
    """Roda FEM para 1 cenário e devolve (nodes, elems, U, fi_list)."""
    from fem_palicada_3d import (generate_mesh, SEGMENTS, MESH, DEGRADATION,
                                  degrade, assemble_K, compute_loads,
                                  solve_system, get_fixed, postprocess)
    sp = SEGMENTS[seg_name]
    W, H = sp['width'], sp['height']
    nodes, elems, xs, zl = generate_mesh(W, H)
    fixed = get_fixed(nodes)
    k_deg = DEGRADATION[deg_key]
    mat = degrade(t_yr, k_deg)
    K, sec = assemble_K(nodes, elems, mat)
    Fv = compute_loads(nodes, elems, t_yr, H, W, hydro_key, sec, seg_name)
    U = solve_system(K, Fv, fixed)
    res = postprocess(nodes, elems, U, mat, sec)
    fi_list = [r['FI'] for r in res]
    return nodes, elems, U, fi_list


# ================================================================
# FIG 1 — Malha indeformada + deformada com mapa de FI (cenário crítico)
# ================================================================
def fig1_wireframe(par):
    from fem_palicada_3d import generate_mesh, SEGMENTS, MESH
    import matplotlib.colors as mcolors

    # --- painel: (a) malha indeformada MED, (b) deformada + FI cenário crítico ---
    fig, axes = plt.subplots(1, 2, figsize=(14, 5.5))

    seg_name = 'MED'
    W = SEGMENTS[seg_name]['width']
    H = SEGMENTS[seg_name]['height']

    # ---- (a) Malha indeformada com legenda de componentes ----
    ax = axes[0]
    nodes0, elems0, xs0, zl0 = generate_mesh(W, H)
    colors_type = {'stake': '#1f77b4', 'colmo': '#d62728'}
    for e in elems0:
        x1, x2 = nodes0[e['n1']], nodes0[e['n2']]
        lw = 2.5 if e['type'] == 'stake' else 1.5
        ax.plot([x1[0], x2[0]], [x1[2], x2[2]],
                color=colors_type[e['type']], lw=lw, solid_capstyle='round')
    # Nós
    ax.scatter(nodes0[:, 0], nodes0[:, 2], s=8, c='k', zorder=5)
    # Solo
    ax.axhline(0, color='#8B4513', ls='--', lw=0.8, alpha=0.6)
    ax.fill_between([-0.1, W+0.1], -MESH['stake_embed'], 0,
                    color='#DEB887', alpha=0.2)
    ax.set_xlabel('Largura da paliçada (m)')
    ax.set_ylabel('Altura (m)')
    ax.set_title(f'(a) Malha indeformada — segmento {seg_name}\n'
                 f'(L = {W:.1f} m, H = {H:.2f} m, {len(nodes0)} nós, {len(elems0)} elementos)',
                 fontsize=10, fontweight='bold')
    ax.set_xlim(-0.2, W+0.2)
    ax.set_aspect('equal')
    ax.grid(True, alpha=0.3)
    from matplotlib.lines import Line2D
    lg = [Line2D([0],[0], color=colors_type['stake'], lw=2.5, label='Estacas (verticais)'),
          Line2D([0],[0], color=colors_type['colmo'], lw=1.5, label='Colmos (horizontais)'),
          Line2D([0],[0], marker='o', color='k', lw=0, ms=4, label='Nós')]
    ax.legend(handles=lg, loc='upper center', bbox_to_anchor=(0.5, -0.10),
             fontsize=9, ncol=3, frameon=True, fancybox=False, edgecolor='0.6')

    # ---- (b) Deformada + FI — cenário crítico (MED, median, pessimistic, t=10) ----
    ax = axes[1]
    nodes, elems, U, fi_list = _solve_single('MED', 'median', 'pessimistic', 10.0)

    # Escala de amplificação para deslocamentos (visual)
    max_disp = 0.0
    for ni in range(len(nodes)):
        dx = U[ni*6]
        dz = U[ni*6 + 2]
        d = np.hypot(dx, dz)
        if d > max_disp:
            max_disp = d
    ref_size = max(W, H) * 0.08
    amp = ref_size / max_disp if max_disp > 1e-12 else 1.0

    # Nós deformados
    nodes_def = nodes.copy()
    for ni in range(len(nodes)):
        nodes_def[ni, 0] += U[ni*6] * amp
        nodes_def[ni, 2] += U[ni*6 + 2] * amp

    # Colormap para FI
    fi_arr = np.array(fi_list)
    fi_max = fi_arr.max()
    norm = mcolors.Normalize(vmin=0, vmax=max(fi_max, 0.01))
    cmap = plt.cm.RdYlGn_r  # verde=seguro, vermelho=falha

    # Plotar malha indeformada em cinza claro (referência)
    for e in elems:
        x1, x2 = nodes[e['n1']], nodes[e['n2']]
        ax.plot([x1[0], x2[0]], [x1[2], x2[2]],
                color='#cccccc', lw=0.8, ls='--')

    # Plotar malha deformada com cor = FI
    for ei, e in enumerate(elems):
        x1, x2 = nodes_def[e['n1']], nodes_def[e['n2']]
        fi_val = fi_list[ei]
        lw = 3.0 if e['type'] == 'stake' else 2.0
        ax.plot([x1[0], x2[0]], [x1[2], x2[2]],
                color=cmap(norm(fi_val)), lw=lw, solid_capstyle='round')

    # Nós deformados coloridos pelo FI máximo dos elementos adjacentes
    node_fi = np.zeros(len(nodes_def))
    for ei, e in enumerate(elems):
        for ni in (e['n1'], e['n2']):
            if fi_list[ei] > node_fi[ni]:
                node_fi[ni] = fi_list[ei]

    # Identificar nós de junção (compartilhados por estaca E colmo)
    node_types = {}  # ni -> set of element types
    for e in elems:
        for ni in (e['n1'], e['n2']):
            node_types.setdefault(ni, set()).add(e['type'])
    is_junction = np.array([len(node_types.get(i, set())) > 1
                            for i in range(len(nodes_def))])

    # Nós internos (círculos menores)
    mask_int = ~is_junction
    ax.scatter(nodes_def[mask_int, 0], nodes_def[mask_int, 2],
              s=25, c=node_fi[mask_int], cmap=cmap, norm=norm,
              marker='o', edgecolors='k', linewidths=0.3, zorder=5)
    # Nós de junção (quadrados maiores — pontos críticos)
    mask_jnc = is_junction
    ax.scatter(nodes_def[mask_jnc, 0], nodes_def[mask_jnc, 2],
              s=70, c=node_fi[mask_jnc], cmap=cmap, norm=norm,
              marker='s', edgecolors='k', linewidths=0.5, zorder=6)

    # Solo
    ax.axhline(0, color='#8B4513', ls='--', lw=0.8, alpha=0.6)
    ax.fill_between([-0.2, W+0.2], -MESH['stake_embed'], 0,
                    color='#DEB887', alpha=0.15)

    ax.set_xlabel('Largura da paliçada (m)')
    ax.set_ylabel('Altura (m)')
    ax.set_title(f'(b) Deformada amplificada com Índice de Falha (Tsai-Hill)\n'
                 f'Cenário crítico: {seg_name}, degradação pessimista, t = 10 anos',
                 fontsize=10, fontweight='bold')
    ax.set_xlim(-0.2, W+0.2)
    ax.set_aspect('equal')
    ax.grid(True, alpha=0.3)

    # Colorbar
    sm = plt.cm.ScalarMappable(cmap=cmap, norm=norm)
    sm.set_array([])
    cbar = fig.colorbar(sm, ax=ax, fraction=0.04, pad=0.02)
    cbar.set_label('Índice de Falha (FI)', fontsize=10)

    # Legenda deformada
    lg2 = [Line2D([0],[0], color='#cccccc', lw=0.8, ls='--',
                   label='Indeformada (referência)'),
           Line2D([0],[0], color=cmap(norm(fi_max)), lw=3,
                   label=f'Deformada (FI_máx = {fi_max:.3f})'),
           Line2D([0],[0], marker='o', color='w', markerfacecolor='#888',
                   markeredgecolor='k', ms=5, lw=0, label='Nó interno'),
           Line2D([0],[0], marker='s', color='w', markerfacecolor=cmap(norm(fi_max)),
                   markeredgecolor='k', ms=7, lw=0, label='Nó de junção (crítico)')]
    ax.legend(handles=lg2, loc='upper center', bbox_to_anchor=(0.5, -0.10),
             fontsize=8, ncol=2, frameon=True, fancybox=False, edgecolor='0.6')

    fig.tight_layout()
    fig.subplots_adjust(bottom=0.18)
    save(fig, 'Fig_1_wireframe_3d')


# ================================================================
# FIG 2 — Evolução temporal de FI (MED, 3 degradações × melhor/pior hidro)
# ================================================================
def fig2_fi_evolution(ds):
    """Exporta dados para CSV e delega plot ao script R."""
    rows = []
    for deg in ['optimistic', 'baseline', 'pessimistic']:
        for hydro in ['P95', 'median']:
            sub = ds[(ds['segment']=='MED') & (ds['hydro']==hydro) &
                     (ds['degradation']==deg)].sort_values('time_yr')
            for _, row in sub.iterrows():
                rows.append({
                    'time_yr': row['time_yr'],
                    'degradation': deg,
                    'hydro': hydro,
                    'max_FI': row['max_FI']
                })
    out = pd.DataFrame(rows)
    csv_path = FIG / 'fig3_fi_evolution_data.csv'
    out.to_csv(csv_path, index=False)
    print(f'  CSV exportado: {csv_path}')
    # Plot gerado pelo script R (gerar_fig3_fi_evolution.R)


# ================================================================
# FIG 3 — Fator de segurança ao longo do tempo (3 segmentos, pessimistic)
# ================================================================
def fig3_safety_factor(ds):
    """Exporta dados para CSV e delega plot ao script R."""
    rows = []
    for seg in ['INF', 'MED', 'SUP']:
        sub = ds[(ds['segment']==seg) & (ds['hydro']=='P95') &
                 (ds['degradation']=='pessimistic')].sort_values('time_yr')
        sf = sub['safety_factor'].clip(upper=50)
        for _, row in sub.iterrows():
            rows.append({
                'time_yr': row['time_yr'],
                'segment': seg,
                'safety_factor': min(row['safety_factor'], 50),
                'width_m': row['width_m']
            })
    out = pd.DataFrame(rows)
    csv_path = FIG / 'fig4_safety_factor_data.csv'
    out.to_csv(csv_path, index=False)
    print(f'  CSV exportado: {csv_path}')
    # Plot gerado pelo script R (gerar_fig4_safety.R)


# ================================================================
# FIG 5 — Distribuição de tensão com a altura (MED, pior caso)
# ================================================================
def fig5_stress_height(df):
    """Exporta dados para CSV e delega plot ao script R."""
    rows = []
    for t_yr in [0.0, 5.0, 10.0]:
        sub_t = df[(df['segment']=='MED') & (df['hydro']=='P95') &
                   (df['degradation']=='pessimistic') & (df['time_yr']==t_yr) &
                   (df['type']=='colmo')]
        grp = sub_t.groupby('z_mid').agg(
            sigma=('sigma_b_MPa', 'max'),
            tau=('tau_s_MPa', 'max')).reset_index()
        grp = grp.sort_values('z_mid')
        grp['time_yr'] = t_yr
        rows.append(grp)
    out = pd.concat(rows, ignore_index=True)
    csv_path = FIG / 'fig5_stress_data.csv'
    out.to_csv(csv_path, index=False)
    print(f'  CSV exportado: {csv_path}')
    # Plot gerado pelo script R (gerar_fig5_stress.R)


# ================================================================
# FIG 7 — Concentração nas junções (nodal vs internodal)
# ================================================================
def fig7_node_zone(df):
    """Exporta dados para CSV e delega plot ao script R."""
    sub = df[(df['segment']=='MED') & (df['hydro']=='P95') &
             (df['degradation']=='pessimistic')]
    times = sorted(sub['time_yr'].unique())

    rows = []
    for t in times:
        st = sub[sub['time_yr']==t]
        nz = st[st['is_node_zone']==True]
        iz = st[st['is_node_zone']==False]
        fi_n = nz['FI'].max() if len(nz) > 0 else 0
        fi_i = iz['FI'].max() if len(iz) > 0 else 0
        rows.append({'time_yr': t, 'fi_nodal': fi_n, 'fi_internodal': fi_i,
                     'ratio': fi_n/fi_i if fi_i > 0 else 0})
    out = pd.DataFrame(rows)
    csv_path = FIG / 'fig6_node_zone_data.csv'
    out.to_csv(csv_path, index=False)
    print(f'  CSV exportado: {csv_path}')
    # Plot gerado pelo script R (gerar_fig6_node.R)


# ================================================================
# FIG 8 — Deslocamento lateral máximo ao longo do tempo
# ================================================================
def fig8_displacement(ds):
    fig, ax = plt.subplots(figsize=(8, 5))
    colors_s = {'INF': '#2ca02c', 'MED': '#d62728', 'SUP': '#1f77b4'}

    for seg in ['INF', 'MED', 'SUP']:
        sub = ds[(ds['segment']==seg) & (ds['hydro']=='P95') &
                 (ds['degradation']=='pessimistic')].sort_values('time_yr')
        ax.plot(sub['time_yr'], sub['max_disp_lat_mm'],
                'o-', color=colors_s[seg], lw=1.8, ms=3,
                label=f'{seg} (L={sub["width_m"].iloc[0]:.1f}m)')

    ax.set_xlabel('Tempo (anos)')
    ax.set_ylabel('Deslocamento lateral máximo (mm)')
    ax.set_title('Deflexão lateral — P95 pessimista')
    ax.legend(fontsize=9)
    ax.grid(True, alpha=0.3)
    ax.set_xlim(0, 10)
    fig.tight_layout()
    save(fig, 'Fig_8_displacement')


# ================================================================
# MAIN
# ================================================================
def main():
    import sys
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    df, ds, par = load()
    print('Gerando figuras FEM 3D:')
    fig1_wireframe(par)
    fig2_fi_evolution(ds)
    fig3_safety_factor(ds)
    fig5_stress_height(df)
    fig7_node_zone(df)
    fig8_displacement(ds)
    print(f'\n{6} figuras salvas em: {FIG}')


if __name__ == '__main__':
    main()
