"""
Figure 1 — 3D FEM mesh (academic wireframe, matplotlib Axes3D) — EN version.

Panel (a): undeformed mesh — colors by type, soil as hatched strip,
           fixed support (triangles) at constrained nodes (z = -0.70 m).
Panel (b): amplified deformed (≈5×) + FI (Tsai-Hill) + reference.
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
FIG = BASE / 'figuras' / 'versao_EN'
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

# ---- Visualization parameters ----
SEG = 'MED'
AMP_FRAC = 0.09
ELEV, AZIM = 25, -55
EMBED = MESH['stake_embed']

CLR_SOIL_LINE = '#8B6914'
CLR_SOIL_FILL = '#D2B48C'


def _draw_soil_indicators(ax, x_min, x_max, y_val=0.0):
    ax.plot([x_min, x_max], [y_val, y_val], [0, 0],
            color=CLR_SOIL_LINE, lw=2.5, ls='-', alpha=0.8, zorder=2)
    ax.plot([x_min, x_max], [y_val, y_val], [-EMBED, -EMBED],
            color=CLR_SOIL_LINE, lw=1.0, ls=':', alpha=0.4, zorder=1)
    for x in [x_min, x_max]:
        ax.plot([x, x], [y_val, y_val], [-EMBED, 0],
                color=CLR_SOIL_LINE, lw=0.8, ls='-', alpha=0.3, zorder=1)


def _draw_fixed_markers(ax, nodes):
    for ni, nd in enumerate(nodes):
        if nd[2] < -1e-3:
            ax.scatter([nd[0]], [nd[1]], [nd[2]],
                       marker='^', s=70, c='#555555',
                       edgecolors='k', linewidths=0.5,
                       depthshade=False, zorder=7)


def _set_axes_limits(ax, nodes_all, pad=0.15):
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
        margin = y_range * 0.15
        ax.set_ylim(y_min - margin, y_max + margin)


# ================================================================
# PANEL (a) — Undeformed mesh
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
            ax.plot([p1[0], p2[0]], [p1[1], p2[1]], [p1[2], p2[2]],
                    color='#888888', lw=1.0, alpha=0.45, zorder=2)
        else:
            ax.plot([p1[0], p2[0]], [p1[1], p2[1]], [p1[2], p2[2]],
                    color=clr[e['type']], lw=lw_map[e['type']],
                    solid_capstyle='round', zorder=3)

    above = nodes[:, 2] >= -1e-3
    ax.scatter(nodes[above, 0], nodes[above, 1], nodes[above, 2],
               s=14, c='k', depthshade=True, zorder=5)

    _draw_soil_indicators(ax, -0.20, W + 0.20)
    _draw_fixed_markers(ax, nodes)

    ax.set_xlabel('Width (m)', labelpad=8)
    ax.set_ylabel('Lateral displ. (m)', labelpad=8)
    ax.set_zlabel('Height (m)', labelpad=8)
    ax.set_title(
        f'(a) Undeformed mesh — {seg_name}\n'
        f'{len(nodes)} nodes, {len(elems)} elem. '
        f'(L={W:.1f} m, H={H:.2f} m, emb.={EMBED:.2f} m)',
        fontsize=9.5, pad=12)

    _set_axes_limits(ax, nodes)
    ax.view_init(elev=ELEV, azim=AZIM)

    leg = [
        Line2D([0], [0], color=clr['stake'], lw=2.2,
               label='Stakes (vertical)'),
        Line2D([0], [0], color=clr['colmo'], lw=1.3,
               label='Culms (horizontal)'),
        Line2D([0], [0], color=clr['colmo_embed'], lw=0.9, ls='--',
               label='Slope embedment (15 cm)'),
        Line2D([0], [0], marker='o', color='w', markerfacecolor='k',
               ms=4, lw=0, label='Internal node'),
        Line2D([0], [0], marker='^', color='w', markerfacecolor='#555',
               markeredgecolor='k', ms=6, lw=0, label='Fixed support (6 DOF)'),
        Line2D([0], [0], marker='o', color='w', markerfacecolor='#888',
               markeredgecolor='k', ms=5, lw=0, label='Slope pin (u,v,w fixed)'),
        Line2D([0], [0], color=CLR_SOIL_LINE, lw=2.5,
               label='Ground level (z = 0)'),
    ]
    ax.legend(handles=leg, loc='upper left', fontsize=7.5, framealpha=0.92)

    # ---- Scale bar (0.5 m) ----
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
    ax.text(x0 + 0.06, 0, z0 + bar_len / 2, '0.5 m',
            fontsize=8, ha='left', va='center', zorder=10)


# ================================================================
# PANEL (b) — Amplified deformed mesh + FI
# ================================================================
def draw_panel_b(ax, seg_name='MED'):
    W = SEGMENTS[seg_name]['width']
    H = SEGMENTS[seg_name]['height']

    nodes, elems, U, fi_list = _solve_single(
        seg_name, 'median', 'pessimistic', 10.0)

    max_disp = 0.0
    for ni in range(len(nodes)):
        d = np.sqrt(U[ni*6]**2 + U[ni*6+1]**2 + U[ni*6+2]**2)
        max_disp = max(max_disp, d)
    amp = (max(W, H) * AMP_FRAC) / max_disp if max_disp > 1e-12 else 1.0

    nodes_def = nodes.copy()
    for ni in range(len(nodes)):
        nodes_def[ni, 0] += U[ni * 6]     * amp
        nodes_def[ni, 1] += U[ni * 6 + 1] * amp
        nodes_def[ni, 2] += U[ni * 6 + 2] * amp

    fi_arr = np.array(fi_list)
    fi_max = fi_arr.max()
    cmap = plt.cm.RdYlGn_r
    norm = mcolors.Normalize(vmin=0, vmax=fi_max)

    # Reference mesh (undeformed, grey, above ground)
    for e in elems:
        p1, p2 = nodes[e['n1']], nodes[e['n2']]
        if p1[2] >= -1e-3 or p2[2] >= -1e-3:
            ax.plot([p1[0], p2[0]], [p1[1], p2[1]], [p1[2], p2[2]],
                    color='#cccccc', lw=0.6, ls='--', alpha=0.45, zorder=1)

    # Deformed mesh (color = FI)
    lw_map = {'stake': 2.8, 'colmo': 1.6, 'colmo_embed': 0.9}
    for ei, e in enumerate(elems):
        p1_d = nodes_def[e['n1']]
        p2_d = nodes_def[e['n2']]
        p1_o = nodes[e['n1']]
        p2_o = nodes[e['n2']]

        if p1_o[2] < -1e-3 and p2_o[2] < -1e-3:
            ax.plot([p1_d[0], p2_d[0]], [p1_d[1], p2_d[1]],
                    [p1_d[2], p2_d[2]],
                    color='#999999', lw=0.8, alpha=0.35, zorder=1)
        else:
            ax.plot([p1_d[0], p2_d[0]], [p1_d[1], p2_d[1]],
                    [p1_d[2], p2_d[2]],
                    color=cmap(norm(fi_list[ei])), lw=lw_map[e['type']],
                    solid_capstyle='round', zorder=3)

    # Deformed nodes (color = FI, above ground only)
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

    y_max_def = nodes_def[:, 1].max()
    _draw_soil_indicators(ax, -0.20, W + 0.20, y_val=0.0)
    if y_max_def > 0.05:
        _draw_soil_indicators(ax, -0.20, W + 0.20,
                              y_val=y_max_def * 0.5)
    _draw_fixed_markers(ax, nodes)

    ax.set_xlabel('Width (m)', labelpad=8)
    ax.set_ylabel('Lateral displ. (m)', labelpad=8)
    ax.set_zlabel('Height (m)', labelpad=8)
    ax.set_title(
        f'(b) Amplified deformed (\u00d7{amp:.0f}) — Tsai-Hill\n'
        r'FI$_{max}$' + f' = {fi_max:.3f}  (SF = {1/fi_max:.1f})',
        fontsize=9.5, pad=12)

    all_pts = np.vstack([nodes, nodes_def])
    _set_axes_limits(ax, all_pts)
    ax.view_init(elev=ELEV, azim=AZIM)

    leg = [
        Line2D([0], [0], color='#cccccc', lw=0.6, ls='--',
               label='Reference (undeformed)'),
        Line2D([0], [0], color=cmap(norm(fi_max)), lw=2.8,
               label=r'Deformed (FI$_{max}$' + f' = {fi_max:.3f})'),
        Line2D([0], [0], marker='o', color='w', markerfacecolor='#888',
               markeredgecolor='k', ms=4, lw=0, label='Internal node'),
        Line2D([0], [0], marker='s', color='w',
               markerfacecolor=cmap(norm(fi_max)),
               markeredgecolor='k', ms=6, lw=0, label='Junction node'),
        Line2D([0], [0], marker='^', color='w', markerfacecolor='#555',
               markeredgecolor='k', ms=6, lw=0, label='Fixed support (6 DOF)'),
        Line2D([0], [0], color=CLR_SOIL_LINE, lw=2.5,
               label='Ground level (z = 0)'),
    ]
    ax.legend(handles=leg, loc='upper left', fontsize=7, framealpha=0.92)

    return cmap, norm, fi_max, amp


# ================================================================
# COMPOSITION
# ================================================================
def generate_fig1():
    fig = plt.figure(figsize=(15, 6.5), dpi=300)

    print('  Rendering panel (a)...')
    ax1 = fig.add_subplot(121, projection='3d')
    draw_panel_a(ax1, SEG)

    print('  Rendering panel (b)...')
    ax2 = fig.add_subplot(122, projection='3d')
    cmap, norm, fi_max, amp = draw_panel_b(ax2, SEG)

    sm = plt.cm.ScalarMappable(cmap=cmap, norm=norm)
    sm.set_array([])
    cbar = fig.colorbar(sm, ax=ax2, shrink=0.55, pad=0.10, aspect=18)
    cbar.set_label('Failure Index (Tsai-Hill)', fontsize=10)

    fig.tight_layout(pad=2.5)

    out = FIG / 'Fig_1_wireframe_3d'
    fig.savefig(f'{out}.png', dpi=300, bbox_inches='tight', facecolor='white')
    fig.savefig(f'{out}.pdf', bbox_inches='tight', facecolor='white')
    plt.close(fig)

    print(f'  Fig_1_wireframe_3d (EN, amp ≈ {amp:.0f}×)')


if __name__ == '__main__':
    generate_fig1()
