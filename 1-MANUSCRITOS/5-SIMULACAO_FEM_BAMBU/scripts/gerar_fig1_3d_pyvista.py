"""
Gera Figura 1 — Malha FEM 3D (wireframe acadêmico, matplotlib Axes3D).

Painel (a): malha indeformada — cores por tipo, solo como faixa hachurada,
            engaste (triângulos) nos nós fixos (z = −0,70 m).
Painel (b): deformada amplificada (≈5×) + FI (Tsai-Hill) + referência.

Amplificação calibrada para 5× (não 12×):
  - z=0 desloca 100 mm, topo 280 mm → curvatura da estaca visível
  - Com 12× o nó z=0 deslocava 241 mm → parecia que a estrutura tombava

Solo representado APENAS como:
  - Faixa horizontal preenchida (z ≤ 0) nos planos traseiros do gráfico
  - Linha grossa em z=0 (nível do solo)
  - Elementos enterrados (z<0) em cinza claro
  - NÃO usa Poly3DCollection (bloco opaco cobria a estrutura)
"""
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
from matplotlib.lines import Line2D
from matplotlib.patches import Rectangle, FancyArrowPatch
from mpl_toolkits.mplot3d import Axes3D  # noqa: F401
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
from fem_palicada_3d import generate_mesh, SEGMENTS, MESH, BAMBOO
from gerar_figuras_fem3d import _solve_single

BASE = Path(__file__).resolve().parent.parent
FIG = BASE / 'figuras'
FIG.mkdir(parents=True, exist_ok=True)

plt.rcParams.update({
    "font.family": "serif",
    "font.size": 10,
    "axes.labelsize": 10,
    "axes.titlesize": 11,
    "figure.dpi": 150,
    "savefig.dpi": 300,
    "savefig.bbox": "tight",
})

# ---- Parâmetros de visualização ----
SEG = 'MED'
AMP_FRAC = 0.09          # amp ≈ 5× (curvatura sem tombar)
ELEV, AZIM = 25, -55
EMBED = MESH['stake_embed']   # 0,70 m

CLR_SOIL_LINE = '#8B6914'     # marrom escuro — linha z=0
CLR_SOIL_FILL = '#D2B48C'     # bege-areia para preenchimento


def _draw_soil_indicators(ax, x_min, x_max, y_val=0.0):
    """Indica o solo como linhas grossas em z=0 e preenchimento abaixo.
    Não usa Poly3DCollection para evitar bloquear a visualização."""
    # Linha grossa no nível do solo (z=0)
    ax.plot([x_min, x_max], [y_val, y_val], [0, 0],
            color=CLR_SOIL_LINE, lw=2.5, ls='-', alpha=0.8, zorder=2)
    # Linhas tracejadas indicando profundidade do engaste
    ax.plot([x_min, x_max], [y_val, y_val], [-EMBED, -EMBED],
            color=CLR_SOIL_LINE, lw=1.0, ls=':', alpha=0.4, zorder=1)
    # Linhas verticais nos cantos delimitando o perfil de solo
    for x in [x_min, x_max]:
        ax.plot([x, x], [y_val, y_val], [-EMBED, 0],
                color=CLR_SOIL_LINE, lw=0.8, ls='-', alpha=0.3, zorder=1)


def _draw_fixed_markers(ax, nodes):
    """Triângulos de engaste (▲) nos nós enterrados (z < 0)."""
    for ni, nd in enumerate(nodes):
        if nd[2] < -1e-3:
            ax.scatter([nd[0]], [nd[1]], [nd[2]],
                       marker='^', s=70, c='#555555',
                       edgecolors='k', linewidths=0.5,
                       depthshade=False, zorder=7)


def _set_axes_limits(ax, nodes_all, pad=0.15):
    """X e Z na mesma escala; Y independente para revelar bulging."""
    x_min, x_max = nodes_all[:, 0].min() - pad, nodes_all[:, 0].max() + pad
    y_min, y_max = nodes_all[:, 1].min() - pad, nodes_all[:, 1].max() + pad
    z_min, z_max = nodes_all[:, 2].min() - pad, nodes_all[:, 2].max() + pad
    xz_range = max(x_max - x_min, z_max - z_min)
    cx = (x_min + x_max) / 2
    cz = (z_min + z_max) / 2
    ax.set_xlim(cx - xz_range / 2, cx + xz_range / 2)
    ax.set_zlim(cz - xz_range / 2, cz + xz_range / 2)
    y_range = y_max - y_min
    if y_range < 0.05:
        cy = (y_min + y_max) / 2
        ax.set_ylim(cy - 0.20, cy + 0.20)
    else:
        # Expande ligeiramente para dar ar
        margin = y_range * 0.15
        ax.set_ylim(y_min - margin, y_max + margin)


# ================================================================
# PAINEL (a) — Malha indeformada
# ================================================================
def draw_panel_a(ax, seg_name='MED'):
    W = SEGMENTS[seg_name]['width']
    H = SEGMENTS[seg_name]['height']
    nodes, elems, _, _ , _ = generate_mesh(W, H)

    clr = {'stake': '#1f77b4', 'colmo': '#d62728', 'colmo_embed': '#aaaaaa'}
    lw_map = {'stake': 2.2, 'colmo': 1.3, 'colmo_embed': 0.9}

    for e in elems:
        p1, p2 = nodes[e['n1']], nodes[e['n2']]
        both_buried = (p1[2] < -1e-3) and (p2[2] < -1e-3)
        if both_buried:
            # Elementos totalmente enterrados: cinza, mais fino
            ax.plot([p1[0], p2[0]], [p1[1], p2[1]], [p1[2], p2[2]],
                    color='#888888', lw=1.0, alpha=0.45, zorder=2)
        else:
            ax.plot([p1[0], p2[0]], [p1[1], p2[1]], [p1[2], p2[2]],
                    color=clr[e['type']], lw=lw_map[e['type']],
                    solid_capstyle='round', zorder=3)

    # Nós acima do solo (pretos)
    above = nodes[:, 2] >= -1e-3
    ax.scatter(nodes[above, 0], nodes[above, 1], nodes[above, 2],
               s=14, c='k', depthshade=True, zorder=5)

    # Solo e engastes
    _draw_soil_indicators(ax, -0.20, W + 0.20)
    _draw_fixed_markers(ax, nodes)

    ax.set_xlabel('Largura (m)', labelpad=8)
    ax.set_ylabel('Desl. lateral (m)', labelpad=8)
    ax.set_zlabel('Altura (m)', labelpad=8)
    ax.set_title(
        f'(a) Malha indeformada — {seg_name}\n'
        f'{len(nodes)} nós, {len(elems)} elem. '
        f'(L={W:.1f} m, H={H:.2f} m, emb.={EMBED:.2f} m)',
        fontsize=9.5, pad=12)

    _set_axes_limits(ax, nodes)
    ax.view_init(elev=ELEV, azim=AZIM)

    leg = [
        Line2D([0], [0], color=clr['stake'], lw=2.2,
               label='Estacas (verticais)'),
        Line2D([0], [0], color=clr['colmo'], lw=1.3,
               label='Colmos (horizontais)'),
        Line2D([0], [0], color=clr['colmo_embed'], lw=0.9, ls='--',
               label='Embutimento no talude (15 cm)'),
        Line2D([0], [0], marker='o', color='w', markerfacecolor='k',
               ms=4, lw=0, label='Nó interno'),
        Line2D([0], [0], marker='^', color='w', markerfacecolor='#555',
               markeredgecolor='k', ms=6, lw=0, label='Engaste (6 DOF fixo)'),
        Line2D([0], [0], marker='o', color='w', markerfacecolor='#888',
               markeredgecolor='k', ms=5, lw=0, label='Pino talude (u,v,w fixos)'),
        Line2D([0], [0], color=CLR_SOIL_LINE, lw=2.5,
               label='Nível do solo (z = 0)'),
    ]
    ax.legend(handles=leg, loc='upper left', fontsize=7.5, framealpha=0.92)

    # ---- Barra de escala (0,5 m) ----
    x0 = W + 0.05
    z0 = -EMBED + 0.05
    bar_len = 0.50
    ax.plot([x0, x0], [0, 0], [z0, z0 + bar_len],
            color='k', lw=2.0, zorder=10)
    ax.plot([x0 - 0.03, x0 + 0.03], [0, 0], [z0, z0],
            color='k', lw=1.5, zorder=10)
    ax.plot([x0 - 0.03, x0 + 0.03], [0, 0],
            [z0 + bar_len, z0 + bar_len],
            color='k', lw=1.5, zorder=10)
    ax.text(x0 + 0.06, 0, z0 + bar_len / 2, '0,5 m',
            fontsize=8, ha='left', va='center', zorder=10)


# ================================================================
# PAINEL (b) — Malha deformada amplificada + FI
# ================================================================
def draw_panel_b(ax, seg_name='MED'):
    W = SEGMENTS[seg_name]['width']
    H = SEGMENTS[seg_name]['height']

    nodes, elems, U, fi_list = _solve_single(
        seg_name, 'median', 'pessimistic', 10.0)

    # ---- Amplificação (3 componentes) ----
    max_disp = 0.0
    for ni in range(len(nodes)):
        d = np.sqrt(U[ni*6]**2 + U[ni*6+1]**2 + U[ni*6+2]**2)
        max_disp = max(max_disp, d)
    amp = (max(W, H) * AMP_FRAC) / max_disp if max_disp > 1e-12 else 1.0

    # Nós deformados
    nodes_def = nodes.copy()
    for ni in range(len(nodes)):
        nodes_def[ni, 0] += U[ni * 6]     * amp
        nodes_def[ni, 1] += U[ni * 6 + 1] * amp
        nodes_def[ni, 2] += U[ni * 6 + 2] * amp

    fi_arr = np.array(fi_list)
    fi_max = fi_arr.max()
    cmap = plt.cm.RdYlGn_r
    norm = mcolors.Normalize(vmin=0, vmax=fi_max)

    # ---- Malha de referência (indeformada, cinza, acima do solo) ----
    for e in elems:
        p1, p2 = nodes[e['n1']], nodes[e['n2']]
        if p1[2] >= -1e-3 or p2[2] >= -1e-3:
            ax.plot([p1[0], p2[0]], [p1[1], p2[1]], [p1[2], p2[2]],
                    color='#cccccc', lw=0.6, ls='--', alpha=0.45, zorder=1)

    # ---- Malha deformada (cor = FI) ----
    lw_map = {'stake': 2.8, 'colmo': 1.6, 'colmo_embed': 0.9}
    for ei, e in enumerate(elems):
        p1_d = nodes_def[e['n1']]
        p2_d = nodes_def[e['n2']]
        p1_o = nodes[e['n1']]
        p2_o = nodes[e['n2']]

        if p1_o[2] < -1e-3 and p2_o[2] < -1e-3:
            # Enterrado: cinza
            ax.plot([p1_d[0], p2_d[0]], [p1_d[1], p2_d[1]],
                    [p1_d[2], p2_d[2]],
                    color='#999999', lw=0.8, alpha=0.35, zorder=1)
        else:
            ax.plot([p1_d[0], p2_d[0]], [p1_d[1], p2_d[1]],
                    [p1_d[2], p2_d[2]],
                    color=cmap(norm(fi_list[ei])), lw=lw_map[e['type']],
                    solid_capstyle='round', zorder=3)

    # ---- Nós deformados (cor = FI, só acima do solo) ----
    node_fi = np.zeros(len(nodes))
    node_types = {}
    for ei, e in enumerate(elems):
        for ni in (e['n1'], e['n2']):
            node_fi[ni] = max(node_fi[ni], fi_list[ei])
            node_types.setdefault(ni, set()).add(e['type'])

    is_junc = np.array([len(node_types.get(i, set())) > 1
                         for i in range(len(nodes))])
    above = nodes[:, 2] >= -1e-3

    mask_int = (~is_junc) & above
    if mask_int.any():
        ax.scatter(nodes_def[mask_int, 0], nodes_def[mask_int, 1],
                   nodes_def[mask_int, 2],
                   s=12, c=node_fi[mask_int], cmap=cmap, norm=norm,
                   depthshade=False, edgecolors='k', linewidths=0.3,
                   zorder=5, marker='o')

    mask_jnc = is_junc & above
    if mask_jnc.any():
        ax.scatter(nodes_def[mask_jnc, 0], nodes_def[mask_jnc, 1],
                   nodes_def[mask_jnc, 2],
                   s=50, c=node_fi[mask_jnc], cmap=cmap, norm=norm,
                   depthshade=False, edgecolors='k', linewidths=0.5,
                   zorder=6, marker='s')

    # Solo e engastes
    y_max_def = nodes_def[:, 1].max()
    _draw_soil_indicators(ax, -0.20, W + 0.20, y_val=0.0)
    # Segunda linha de solo deslocada em Y para mostrar que o solo não se move
    if y_max_def > 0.05:
        _draw_soil_indicators(ax, -0.20, W + 0.20,
                              y_val=y_max_def * 0.5)
    _draw_fixed_markers(ax, nodes)

    ax.set_xlabel('Largura (m)', labelpad=8)
    ax.set_ylabel('Desl. lateral (m)', labelpad=8)
    ax.set_zlabel('Altura (m)', labelpad=8)
    ax.set_title(
        f'(b) Deformada amplificada (×{amp:.0f}) — Tsai-Hill\n'
        r'FI$_{máx}$' + f' = {fi_max:.3f}  (FS = {1/fi_max:.1f})',
        fontsize=9.5, pad=12)

    all_pts = np.vstack([nodes, nodes_def])
    _set_axes_limits(ax, all_pts)
    ax.view_init(elev=ELEV, azim=AZIM)

    leg = [
        Line2D([0], [0], color='#cccccc', lw=0.6, ls='--',
               label='Referência (indeformada)'),
        Line2D([0], [0], color=cmap(norm(fi_max)), lw=2.8,
               label=r'Deformada (FI$_{máx}$' + f' = {fi_max:.3f})'),
        Line2D([0], [0], marker='o', color='w', markerfacecolor='#888',
               markeredgecolor='k', ms=4, lw=0, label='Nó interno'),
        Line2D([0], [0], marker='s', color='w',
               markerfacecolor=cmap(norm(fi_max)),
               markeredgecolor='k', ms=6, lw=0, label='Nó de junção'),
        Line2D([0], [0], marker='^', color='w', markerfacecolor='#555',
               markeredgecolor='k', ms=6, lw=0, label='Engaste (6 DOF fixo)'),
        Line2D([0], [0], color=CLR_SOIL_LINE, lw=2.5,
               label='Nível do solo (z = 0)'),
    ]
    ax.legend(handles=leg, loc='upper left', fontsize=7, framealpha=0.92)

    return cmap, norm, fi_max, amp


# ================================================================
# COMPOSIÇÃO
# ================================================================
def generate_fig1():
    fig = plt.figure(figsize=(15, 6.5), dpi=300)

    print('  Renderizando painel (a)...')
    ax1 = fig.add_subplot(121, projection='3d')
    draw_panel_a(ax1, SEG)

    print('  Renderizando painel (b)...')
    ax2 = fig.add_subplot(122, projection='3d')
    cmap, norm, fi_max, amp = draw_panel_b(ax2, SEG)

    sm = plt.cm.ScalarMappable(cmap=cmap, norm=norm)
    sm.set_array([])
    cbar = fig.colorbar(sm, ax=ax2, shrink=0.55, pad=0.10, aspect=18)
    cbar.set_label('Índice de Falha (Tsai-Hill)', fontsize=10)

    fig.tight_layout(pad=2.5)

    out = FIG / 'Fig_1_wireframe_3d'
    fig.savefig(f'{out}.png', dpi=300, bbox_inches='tight', facecolor='white')
    fig.savefig(f'{out}.pdf', bbox_inches='tight', facecolor='white')
    plt.close(fig)

    print(f'  Fig_1_wireframe_3d (wireframe 3D, amp ≈ {amp:.0f}×)')


if __name__ == '__main__':
    generate_fig1()
