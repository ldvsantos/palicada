"""
Gera esquema do ensaio de chuva simulada em laboratório:
  - Setup do simulador (bicos oscilantes, 3 m altura)
  - Comparação amostra natural vs. desferrificada (DCB)
  - Coleta de escoamento e sedimentos
  - Intensidades de 30, 60, 90, 120 mm/h
"""

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch, Rectangle, Circle
import numpy as np

C_BG     = "#FAFAFA"
C_TEXT   = "#1A1A1A"
C_STRUCT = "#555555"
C_WATER  = "#3498DB"
C_SOIL_N = "#A0522D"  # amostra natural (marrom)
C_SOIL_D = "#D2B48C"  # amostra desferrificada (bege)
C_IRON   = "#C0392B"  # ferro
C_SED    = "#E67E22"  # sedimento
C_LIGHT  = "#ECF0F1"
C_MECH   = "#8E44AD"


def rbox(ax, x, y, w, h, text, fc, tc=C_TEXT, fs=8, fw="normal", ec="#555555", lw=1.0):
    box = FancyBboxPatch(
        (x - w/2, y - h/2), w, h,
        boxstyle="round,pad=0.08", facecolor=fc, edgecolor=ec,
        linewidth=lw, zorder=2
    )
    ax.add_patch(box)
    ax.text(x, y, text, ha="center", va="center", fontsize=fs,
            color=tc, fontweight=fw, zorder=3, linespacing=1.25)


def arrow(ax, x0, y0, x1, y1, color="#555555", lw=1.2, style="-|>"):
    arr = FancyArrowPatch(
        (x0, y0), (x1, y1),
        arrowstyle=style, color=color, linewidth=lw,
        mutation_scale=12, zorder=1
    )
    ax.add_patch(arr)


fig, (ax_left, ax_right) = plt.subplots(1, 2, figsize=(15, 8), facecolor=C_BG,
                                         gridspec_kw={"width_ratios": [1.1, 1]})

for ax in (ax_left, ax_right):
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 10)
    ax.set_aspect("equal")
    ax.axis("off")
    ax.set_facecolor(C_BG)

# ═══════════════════════════════════════════════════════
# PAINEL (a) — Setup do simulador de chuva
# ═══════════════════════════════════════════════════════
ax = ax_left
ax.text(5, 9.7, "(a) Rainfall simulator setup", ha="center", fontsize=11,
        fontweight="bold", color=C_TEXT)

# ── Estrutura do simulador (suporte vertical) ──
# Postes
ax.plot([1.5, 1.5], [1.0, 8.5], color=C_STRUCT, lw=3, zorder=1)
ax.plot([8.5, 8.5], [1.0, 8.5], color=C_STRUCT, lw=3, zorder=1)
# Barra horizontal superior
ax.plot([1.5, 8.5], [8.5, 8.5], color=C_STRUCT, lw=3, zorder=1)

# ── Bicos oscilantes ──
nozzle_xs = [3.0, 5.0, 7.0]
for nx in nozzle_xs:
    # corpo do bico
    ax.add_patch(Rectangle((nx - 0.2, 8.0), 0.4, 0.5, facecolor="#777",
                            edgecolor=C_STRUCT, lw=1.2, zorder=3))
    # cone de spray
    xs_spray = np.array([nx - 1.2, nx, nx + 1.2])
    ys_spray = np.array([5.5, 8.0, 5.5])
    ax.fill(xs_spray, ys_spray, alpha=0.10, color=C_WATER, zorder=1)
    # gotas (simplificadas)
    for gx in np.linspace(nx - 0.8, nx + 0.8, 5):
        for gy in np.linspace(5.8, 7.5, 4):
            gy_jit = gy + np.random.uniform(-0.15, 0.15)
            gx_jit = gx + np.random.uniform(-0.1, 0.1)
            ax.plot(gx_jit, gy_jit, "o", color=C_WATER, markersize=1.8, alpha=0.5)

# ── Cota: 3 m ──
ax.annotate("", xy=(9.3, 8.5), xytext=(9.3, 5.3),
            arrowprops=dict(arrowstyle="<->", color=C_TEXT, lw=1.2))
ax.text(9.5, 6.9, "3 m", fontsize=8, color=C_TEXT, rotation=90, ha="left", va="center")

# ── Label bicos ──
ax.text(5.0, 8.9, "Oscillating nozzles", ha="center", fontsize=7.5,
        color=C_STRUCT, style="italic")

# ── Bandeja com amostra natural ──
bx, by, bw, bh = 3.0, 4.5, 2.5, 1.2
ax.add_patch(Rectangle((bx - bw/2, by - bh/2), bw, bh,
                        facecolor=C_SOIL_N, edgecolor=C_STRUCT, lw=1.5, zorder=2))
# camada de ferro (linha vermelha)
ax.plot([bx - bw/2 + 0.1, bx + bw/2 - 0.1], [by - 0.1, by - 0.1],
        color=C_IRON, lw=2.5, zorder=3)
ax.text(bx, by + 0.25, "Natural\nsample", ha="center", va="center",
        fontsize=7, color="white", fontweight="bold", zorder=3)
ax.text(bx, by - 0.35, "Fe₂O₃ cement", ha="center", va="center",
        fontsize=6, color=C_IRON, fontweight="bold", zorder=3)

# ── Bandeja com amostra desferrificada ──
bx2 = 7.0
ax.add_patch(Rectangle((bx2 - bw/2, by - bh/2), bw, bh,
                        facecolor=C_SOIL_D, edgecolor=C_STRUCT, lw=1.5, zorder=2))
ax.text(bx2, by + 0.15, "DCB-treated\nsample", ha="center", va="center",
        fontsize=7, color=C_TEXT, fontweight="bold", zorder=3)
ax.text(bx2, by - 0.4, "(Fe removed)", ha="center", va="center",
        fontsize=6, color=C_TEXT, style="italic", zorder=3)

# ── Calhas de coleta ──
for bxi in [bx, bx2]:
    # calha inclinada
    ax.plot([bxi + bw/2, bxi + bw/2 + 0.4], [by - bh/2, by - bh/2 - 0.5],
            color=C_STRUCT, lw=2, zorder=2)
    # recipiente de coleta
    rx = bxi + bw/2 + 0.4
    ry = by - bh/2 - 0.5 - 0.6
    ax.add_patch(Rectangle((rx - 0.3, ry), 0.6, 0.6,
                            facecolor="#FDE8D0", edgecolor=C_SED, lw=1.5, zorder=2))
    # nível de sedimento
    ax.add_patch(Rectangle((rx - 0.25, ry + 0.05), 0.5, 0.25,
                            facecolor=C_SED, edgecolor="none", alpha=0.6, zorder=3))

# Labels coleta
ax.text(3.0 + bw/2 + 0.4, by - bh/2 - 1.5, "Runoff +\nsediment", ha="center",
        fontsize=6.5, color=C_SED, fontweight="bold")
ax.text(7.0 + bw/2 + 0.4, by - bh/2 - 1.5, "Runoff +\nsediment", ha="center",
        fontsize=6.5, color=C_SED, fontweight="bold")

# ── Intensidades ──
rbox(ax, 5.0, 1.5, 6.0, 0.9,
     "Intensities: 30, 60, 90, 120 mm/h\n"
     "Duration: 30 min per intensity  ·  Drop KE ≈ natural tropical rain",
     fc=C_LIGHT, tc=C_WATER, fs=7.5, fw="bold")

# ── Seta comparação ──
ax.annotate("", xy=(6.8, 4.5), xytext=(4.3, 4.5),
            arrowprops=dict(arrowstyle="<->", color=C_MECH, lw=2))
ax.text(5.55, 5.25, "Compare\n$\\Delta$ erosion", ha="center", fontsize=8,
        color=C_MECH, fontweight="bold")

# ═══════════════════════════════════════════════════════
# PAINEL (b) — Cadeia de interpretação
# ═══════════════════════════════════════════════════════
ax = ax_right
ax.text(5, 9.7, "(b) Calibration chain from simulated rainfall",
        ha="center", fontsize=11, fontweight="bold", color=C_TEXT)

# ── Etapa 1: Input ──
rbox(ax, 5, 8.7, 7.5, 0.7,
     "Erosion measurement under controlled intensity\n"
     "Natural sample → $A_{nat}$     |     DCB-treated sample → $A_{dcb}$",
     fc=C_LIGHT, tc=C_TEXT, fs=7.5, fw="bold")

arrow(ax, 5, 8.34, 5, 7.72)

# ── Etapa 2: fd ──
rbox(ax, 5, 7.3, 7.5, 0.75,
     "Dispersible fraction\n"
     "$f_d = f_{tex} / [1 + a_1 \\cdot Fe_d^{a_2} \\cdot \\rho_b^{a_3} \\cdot R_{WDPT}^{a_4}]$\n"
     "Calibrate $a_1$–$a_4$ from ratio $A_{nat}/A_{dcb}$ across intensities",
     fc="#E8DAEF", tc=C_MECH, fs=7.5, fw="bold")

arrow(ax, 5, 6.92, 5, 6.3)

# ── Etapa 3: Ed ──
rbox(ax, 5, 5.9, 7.5, 0.7,
     "Disaggregation energy\n"
     "$E_d = E_0 \\cdot (f_{tex}/f_d)^{n_d}$\n"
     "$E_0$ calibrated from DCB-treated samples (reference)",
     fc="#E8DAEF", tc=C_MECH, fs=7.5, fw="bold")

arrow(ax, 5, 5.54, 5, 4.92)

# ── Etapa 4: JET ──
rbox(ax, 5, 4.5, 7.5, 0.75,
     "Independent validation of $\\tau_c$ and $k_d$\n"
     "JET (Jet Erosion Test) in situ → Ap, BAc, Bf horizons\n"
     "Consistency check: $\\tau_c$ from JET ≈ $E_d$ ranking from model",
     fc="#FCE4EC", tc=C_IRON, fs=7.5, fw="bold")

arrow(ax, 5, 4.12, 5, 3.5)

# ── Etapa 5: Micro-CT ──
rbox(ax, 5, 3.1, 7.5, 0.7,
     "Failure mode identification (micro-CT)\n"
     "5 wetting-drying cycles → 3D pore network evolution\n"
     "Piping (internal channels) vs. delamination (surface crust)",
     fc="#FCE4EC", tc=C_IRON, fs=7.5, fw="bold")

arrow(ax, 5, 2.74, 5, 2.12)

# ── Output final ──
rbox(ax, 5, 1.7, 7.5, 0.75,
     "Outputs for field model\n"
     "$f_d$ per pedological class  ·  $E_d$ per horizon  ·  Failure mode\n"
     "→ feed into $K_{plint}$ calibration (field plots)",
     fc="#D5F5E3", tc="#1A6B3C", fs=7.5, fw="bold", lw=1.5, ec="#1A6B3C")


fig.tight_layout(pad=1.2)
out = r"c:\Users\vidal\OneDrive\Documentos\13 - CLONEGIT\artigo-posdoc\3-EROSIBIDADE\1-MANUSCRITOS\7-PROPOSTA_K_PLINTOSSOLO\figuras\fig_esquema_chuva_simulada.png"
fig.savefig(out, dpi=300, bbox_inches="tight", facecolor=C_BG)
print(f"Salvo em: {out}")
plt.close()
