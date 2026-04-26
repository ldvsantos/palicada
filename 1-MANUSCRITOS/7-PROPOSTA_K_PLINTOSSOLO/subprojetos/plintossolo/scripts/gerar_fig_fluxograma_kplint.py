"""
Gera fluxograma conceitual do modelo K_plint:
  (a) Estrutura do modelo multiplicativo + modelo mecanístico de dispersão
  (b) Protocolo de calibração sequencial em 4 etapas + bayesiana + validação
"""

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch

# ── cores ──
C_USLE   = "#2C3E50"   # azul escuro (modelo base)
C_ALPHA  = "#2980B9"   # azul (hidráulico)
C_BETA   = "#27AE60"   # verde (toxicidade)
C_GAMMA  = "#E74C3C"   # vermelho (geotécnico)
C_MECH   = "#8E44AD"   # roxo (modelo mecanístico)
C_CALIB  = "#F39C12"   # laranja (calibração)
C_VALID  = "#1ABC9C"   # teal (validação)
C_BG     = "#FAFAFA"
C_TEXT   = "#1A1A1A"
C_LIGHT  = "#ECF0F1"


def rounded_box(ax, x, y, w, h, text, fc, tc=C_TEXT, fs=8.5, fw="normal", lw=1.0, ec="#555555"):
    """Caixa arredondada com texto centralizado."""
    box = FancyBboxPatch(
        (x - w / 2, y - h / 2), w, h,
        boxstyle="round,pad=0.12", facecolor=fc, edgecolor=ec,
        linewidth=lw, zorder=2
    )
    ax.add_patch(box)
    ax.text(x, y, text, ha="center", va="center", fontsize=fs,
            color=tc, fontweight=fw, zorder=3, linespacing=1.3)
    return box


def arrow(ax, x0, y0, x1, y1, color="#555555", style="-|>", lw=1.2, ls="-"):
    """Seta entre dois pontos."""
    arr = FancyArrowPatch(
        (x0, y0), (x1, y1),
        arrowstyle=style, color=color, linewidth=lw,
        mutation_scale=12, zorder=1, linestyle=ls,
        connectionstyle="arc3,rad=0"
    )
    ax.add_patch(arr)


# ═══════════════════════════════════════════════════════════════════
# PAINEL (a) — Estrutura conceitual do modelo
# ═══════════════════════════════════════════════════════════════════
fig, (ax_a, ax_b) = plt.subplots(1, 2, figsize=(16, 9.5), facecolor=C_BG)

for ax in (ax_a, ax_b):
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 10)
    ax.set_aspect("equal")
    ax.axis("off")
    ax.set_facecolor(C_BG)

# ── Título do painel ──
ax_a.text(5, 9.7, "(a) Conceptual framework of the $K_{plint}$ correction model",
          ha="center", va="center", fontsize=11, fontweight="bold", color=C_TEXT)

# ── K_RUSLE (topo) ──
rounded_box(ax_a, 5, 8.8, 4.0, 0.65,
            "$K_{RUSLE}$  (Wischmeier nomogram)\nTexture · OM · Structure · Permeability",
            fc=C_LIGHT, tc=C_USLE, fs=8, fw="bold")

arrow(ax_a, 5, 8.47, 5, 7.85, color=C_USLE)

# ── Caixa central: modelo multiplicativo ──
rounded_box(ax_a, 5, 7.5, 5.5, 0.55,
            "$K_{plint}  =  K_{RUSLE}  \\times  \\alpha(VIB)  \\times  \\beta(m_{Al})  \\times  \\gamma(H/H_c)$",
            fc="#D5E8F0", tc=C_USLE, fs=10, fw="bold", lw=1.8, ec=C_USLE)

# ── Três fatores amplificadores ──
y_fac = 6.2
bw, bh = 2.8, 1.0

# alpha
rounded_box(ax_a, 1.8, y_fac, bw, bh,
            "$\\alpha = (VIB_{ref}/VIB)^{n_1}$\n\nHydraulic\nimpedance",
            fc="#D6EAF8", tc=C_ALPHA, fs=7.5, fw="bold")
arrow(ax_a, 1.8, y_fac + bh/2 + 0.05, 3.2, 7.22, color=C_ALPHA, lw=1.0)

# beta
rounded_box(ax_a, 5.0, y_fac, bw, bh,
            "$\\beta = 1 + \\beta_{max}/(1+e^{-k_2(m-m_0)})$\n\nEdaphic\ntoxicity ($m_{Al}$)",
            fc="#D5F5E3", tc=C_BETA, fs=7.5, fw="bold")
arrow(ax_a, 5.0, y_fac + bh/2 + 0.05, 5.0, 7.22, color=C_BETA, lw=1.0)

# gamma
rounded_box(ax_a, 8.2, y_fac, bw, bh,
            "$\\gamma = 1 + k_3 (H/H_c)^{n_3}$\n\nGeotechnical\nvulnerability",
            fc="#FADBD8", tc=C_GAMMA, fs=7.5, fw="bold")
arrow(ax_a, 8.2, y_fac + bh/2 + 0.05, 6.8, 7.22, color=C_GAMMA, lw=1.0)

# ── Modelo mecanístico de dispersão (fd, Ed) ──
y_mech = 4.3
rounded_box(ax_a, 5.0, y_mech, 7.0, 1.15,
            "Mechanistic dispersion model\n"
            "$f_d = f_{tex} / [1 + a_1 \\cdot Fe_d^{a_2} \\cdot \\rho_b^{a_3} \\cdot R_{WDPT}^{a_4}]$\n"
            "$E_d = E_0 \\cdot (f_{tex}/f_d)^{n_d}$",
            fc="#E8DAEF", tc=C_MECH, fs=8, fw="bold", lw=1.5, ec=C_MECH)

# seta do modelo mecanístico para alpha
arrow(ax_a, 3.0, y_mech + 0.6, 1.8, y_fac - bh/2 - 0.08, color=C_MECH, lw=1.0, ls="--")
ax_a.text(1.55, 5.1, "calibrates\n$E_d$ threshold", ha="center", fontsize=6.5, color=C_MECH, style="italic")

# ── Inputs do modelo mecanístico ──
y_inp = 2.8
inputs = [
    (1.5, "$Fe_d$\n(free iron\noxide)", "#E8DAEF"),
    (3.5, "$\\rho_b$\n(bulk\ndensity)", "#E8DAEF"),
    (5.0, "$R_{WDPT}$\n(hydro-\nphobicity)", "#E8DAEF"),
    (6.5, "Simulated\nrainfall\n(30–120 mm/h)", "#F5EEF8"),
    (8.5, "JET\n($k_d$, $\\tau_c$)", "#F5EEF8"),
]
for xi, txt, fc in inputs:
    rounded_box(ax_a, xi, y_inp, 1.6, 0.85, txt, fc=fc, tc=C_MECH, fs=6.5)
    arrow(ax_a, xi, y_inp + 0.43 + 0.05, xi if xi <= 6.5 else 7.5, y_mech - 0.58 - 0.05, color=C_MECH, lw=0.8)

# ── Micro-CT ──
rounded_box(ax_a, 8.5, 1.5, 1.6, 0.7,
            "Micro-CT\n(failure mode)", fc="#F5EEF8", tc=C_MECH, fs=6.5)
arrow(ax_a, 8.5, 1.85 + 0.05, 8.5, y_inp - 0.43 - 0.05, color=C_MECH, lw=0.8, ls="--")

# ── Parcelas de campo ──
rounded_box(ax_a, 3.0, 1.5, 2.8, 0.7,
            "Field plots (Wischmeier + microparcels)\n$K_{obs} = A_{obs} / (R \\times L \\times S)$",
            fc=C_LIGHT, tc=C_USLE, fs=7)
arrow(ax_a, 3.0, 1.85 + 0.05, 1.8, y_fac - bh/2 - 0.08, color=C_USLE, lw=0.8)
arrow(ax_a, 4.1, 1.85 + 0.05, 5.0, y_fac - bh/2 - 0.08, color=C_USLE, lw=0.8)
arrow(ax_a, 4.4, 1.85 + 0.05, 8.2, y_fac - bh/2 - 0.08, color=C_USLE, lw=0.8)

# ── δ = Kobs/KRUSLE ──
rounded_box(ax_a, 5.0, 0.55, 3.5, 0.55,
            "$\\delta = K_{obs}/K_{RUSLE}$   (amplification ratio)",
            fc="#FDEBD0", tc=C_CALIB, fs=8, fw="bold")
arrow(ax_a, 3.0, 1.15, 4.2, 0.83, color=C_CALIB, lw=1.0)


# ═══════════════════════════════════════════════════════════════════
# PAINEL (b) — Protocolo de calibração e validação
# ═══════════════════════════════════════════════════════════════════
ax_b.text(5, 9.7, "(b) Sequential calibration protocol and validation",
          ha="center", va="center", fontsize=11, fontweight="bold", color=C_TEXT)

# ── Etapa 0: Controle negativo ──
rounded_box(ax_b, 5, 9.0, 7.5, 0.65,
            "Step 0 — Negative control verification\n"
            "S2 (Latossolo): $\\delta_{S2} \\approx 1.0$ → USLE adequate (one-sided t-test, α = 0.05)",
            fc="#D6EAF8", tc=C_ALPHA, fs=7.5, fw="bold")

arrow(ax_b, 5, 8.67, 5, 8.15, color="#555555")

# ── Etapa 1: α ──
rounded_box(ax_b, 5, 7.8, 7.5, 0.6,
            "Step 1 — Marginal calibration of $\\alpha$  ($n_1$)\n"
            "S3 (Argissolo) vs S2: $\\delta_{S3}/\\delta_{S2} \\sim (VIB_{ref}/VIB)^{n_1}$ → nonlinear regression",
            fc="#D6EAF8", tc=C_ALPHA, fs=7.5, fw="bold")

arrow(ax_b, 5, 7.49, 5, 6.97, color="#555555")

# ── Etapa 2: β ──
rounded_box(ax_b, 5, 6.6, 7.5, 0.65,
            "Step 2 — Calibration of $\\beta$  ($\\beta_{max}$, $k_2$)\n"
            "S1 (Plintossolo): Ap ($m$=15%) vs BAc ($m$=99%) at same slope position → sigmoid fit",
            fc="#D5F5E3", tc=C_BETA, fs=7.5, fw="bold")

arrow(ax_b, 5, 6.27, 5, 5.75, color="#555555")

# ── Etapa 3: γ ──
rounded_box(ax_b, 5, 5.4, 7.5, 0.6,
            "Step 3 — Calibration of $\\gamma$  ($k_3$, $n_3$)\n"
            "S1: F2 ($H/H_c$=0.12) vs F5 ($H/H_c$=0.45) → $\\delta_{res} = \\delta/(\\alpha \\cdot \\beta)$",
            fc="#FADBD8", tc=C_GAMMA, fs=7.5, fw="bold")

arrow(ax_b, 5, 5.09, 5, 4.57, color="#555555")

# ── Etapa 4: Calibração simultânea ──
rounded_box(ax_b, 5, 4.2, 7.5, 0.65,
            "Step 4 — Simultaneous calibration (Levenberg-Marquardt)\n"
            "56 plots × 3 sites → $K_{plint}$ full model → bootstrap CI (1000 resamples)",
            fc="#FDEBD0", tc=C_CALIB, fs=7.5, fw="bold")

# ── Braço bayesiano ──
rounded_box(ax_b, 2.0, 3.1, 3.2, 0.75,
            "Hierarchical Bayesian\nStan/PyMC · MCMC\n$\\hat{R}$ < 1.01 · WAIC comparison",
            fc="#FDEBD0", tc=C_CALIB, fs=7, fw="bold")
arrow(ax_b, 2.0, 3.48, 2.0, 3.87, color=C_CALIB, lw=1.0)
# seta lateral de Step 4 para Bayesiano
arrow(ax_b, 3.0, 3.87, 3.6, 3.48, color=C_CALIB, lw=1.0, ls="--")

# ── Braço frequentista → validação ──
arrow(ax_b, 5, 3.87, 5, 2.55, color="#555555")

# ── Bayesiano → validação ──
arrow(ax_b, 2.0, 2.72, 2.0, 2.55, color=C_CALIB, lw=1.0, ls="--")

# ── Validação ──
rounded_box(ax_b, 5, 2.1, 7.5, 0.8,
            "Validation\n"
            "Internal: LOOCV (56 obs. combined)  |  Cross-site: calibrate 2 sites, test on 3rd\n"
            "Metrics: $R^2$, RMSE, NSE, PBIAS  |  Model comparison: AICc (4 candidates)",
            fc="#D1F2EB", tc=C_VALID, fs=7.5, fw="bold")

arrow(ax_b, 5, 1.69, 5, 1.17, color="#555555")

# ── Resultado final ──
rounded_box(ax_b, 5, 0.8, 7.5, 0.65,
            "Output:  $K_{plint}$  with CI per pedological class\n"
            "Transferable protocol for tropical Plinthosols",
            fc=C_LIGHT, tc=C_USLE, fs=8.5, fw="bold", lw=1.8, ec=C_USLE)

# ── Legenda lateral: sítios ──
y_leg = 0.25
for lbl, clr in [("S1 Plintossolo (calibration)", C_GAMMA),
                 ("S2 Latossolo (negative control)", C_ALPHA),
                 ("S3 Argissolo (partial control)", C_BETA)]:
    ax_b.plot(1.2, y_leg, "s", color=clr, markersize=7)
    ax_b.text(1.5, y_leg, lbl, fontsize=6.5, va="center", color=C_TEXT)
    y_leg -= 0.28


fig.tight_layout(pad=1.2)
out = r"c:\Users\vidal\OneDrive\Documentos\13 - CLONEGIT\artigo-posdoc\3-EROSIBIDADE\1-MANUSCRITOS\7-PROPOSTA_K_PLINTOSSOLO\figuras\fig_fluxograma_kplint.png"
fig.savefig(out, dpi=300, bbox_inches="tight", facecolor=C_BG)
print(f"Salvo em: {out}")
plt.close()
