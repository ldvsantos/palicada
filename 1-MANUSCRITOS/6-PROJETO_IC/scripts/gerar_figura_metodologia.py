"""
Gera duas figuras metodológicas do projeto de IC:

  Fig_metodologia_4a.png — dois painéis lado a lado:
    (a) Foto real da ravina com paliçadas em série (image9.jpeg)
    (b) Perfil longitudinal esquemático (P1–P4)

  Fig_metodologia_4b.png — dois painéis lado a lado:
    (a) Detalhe da paliçada MED com pontos de ensaio de campo
    (b) Disposição dos corpos de prova no ensaio de degradação in situ
"""

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import matplotlib.patheffects as pe
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch, Arc
from matplotlib.image import imread
import numpy as np

BASE = r"c:\Users\vidal\OneDrive\Documentos\13 - CLONEGIT\artigo-posdoc\3-EROSIBIDADE\1-MANUSCRITOS\6-PROJETO_IC"

# ── cores ──────────────────────────────────────────────────────────────────
C_SOLO   = "#c8a96e"
C_SOLO2  = "#8B6914"
C_BAMBU  = "#6a9f3c"
C_BAMBU2 = "#2d5a16"
C_SED    = "#b5956a"
C_AGUA   = "#4a90d9"
C_ARAME  = "#888888"
C_LABEL  = "#1a1a2e"
C_STRAIN = "#e63946"
C_DISP   = "#f4a261"
C_LOAD   = "#457b9d"
C_MESH   = "#6b4226"
C_BG     = "#f8f6f0"

# ═══════════════════════════════════════════════════════════════════════════
# FIGURA 4A — Foto real (a) + Perfil longitudinal (b)
# ═══════════════════════════════════════════════════════════════════════════
fig_4a, (ax_foto, ax_a) = plt.subplots(1, 2, figsize=(17, 8),
                                        facecolor=C_BG,
                                        gridspec_kw={"width_ratios": [1, 1.6]})
fig_4a.subplots_adjust(left=0.03, right=0.97, top=0.90, bottom=0.07, wspace=0.06)

# ── painel (a): foto real ───────────────────────────────────────────────────
foto = imread(BASE + r"\image9.jpeg")
ax_foto.imshow(foto)
ax_foto.set_xticks([]); ax_foto.set_yticks([])
for spine in ax_foto.spines.values():
    spine.set_linewidth(1.2); spine.set_edgecolor("#888")
ax_foto.set_title("(a)  Vista geral da ravina \u2014 pali\u00e7adas P1 a P4 em s\u00e9rie",
                  fontsize=10, loc="left", color=C_LABEL, pad=6)

# ── painel (b): perfil longitudinal — configura eixo ───────────────────────
ax = ax_a
ax.set_aspect("equal")
ax.set_facecolor(C_BG)
for spine in ax.spines.values():
    spine.set_visible(False)
ax.set_xticks([]); ax.set_yticks([])
ax.set_xlim(0, 22)
ax.set_ylim(-1.5, 5.5)

# ── renomeia eixo para título correto ──────────────────────────────────────

# Talude esquerdo e direito
xs_left  = [0,  0,  2,  4,  6,  8, 10, 12, 14, 16, 18, 20, 22]
ys_left  = [4.5,4.5,4.0,3.5,3.0,2.5,2.0,1.5,1.0,0.8,0.6,0.5,0.5]
xs_right = [0, 22]
ys_bot   = [-0.5, -0.5]

# Fundo da ravina (gradiente de declividade)
xb = np.array([0, 22])
yb = np.array([2.5, -0.5])
ax.fill_between([0, 22], [-1.5, -1.5], yb, color=C_SOLO, alpha=0.6, zorder=1)
ax.plot(xb, yb, color=C_SOLO2, lw=1.5, zorder=2)

# Talude superior
ax.fill_between(xs_left, ys_left, [5.5]*len(xs_left), color=C_SOLO, alpha=0.5, zorder=1)
ax.plot(xs_left, ys_left, color=C_SOLO2, lw=1.5, zorder=2)

# ── Funções de geometria do perfil ─────────────────────────────────────────
def _y_floor(x):
    """Cota do fundo da ravina no perfil longitudinal."""
    return 2.5 - (3.0 / 22.0) * x

_xs_surf = [0, 2, 4, 6, 8, 10, 12, 14, 16, 18, 20, 22]
_ys_surf = [4.5, 4.0, 3.5, 3.0, 2.5, 2.0, 1.5, 1.0, 0.8, 0.6, 0.5, 0.5]
def _y_surface(x):
    """Cota da borda do talude por interpolação linear."""
    return float(np.interp(x, _xs_surf, _ys_surf))

# Paliçadas P1-P4 — posições calculadas a partir da geometria real
_pal_xs     = [4.5, 8.5, 12.5, 17.0]
_pal_labels = ["P1", "P2", "P3", "P4"]
_pal_tags   = ["INF", "INF", "MED", "SUP"]
_fill_ratio = 0.90   # paliçadas ocupam 90 % do vão de escoamento

palisades = []
for _xp, _lab, _tag in zip(_pal_xs, _pal_labels, _pal_tags):
    _base = _y_floor(_xp)
    _gap  = _y_surface(_xp) - _base
    palisades.append({"x": _xp, "h_base": _base,
                       "h_bar": _gap * _fill_ratio,
                       "label": _lab, "tag": _tag})

sed_offsets = {"P1": 2.5, "P2": 2.8, "P3": 3.5, "P4": 1.8}

for p in palisades:
    xp, yb_p, ht = p["x"], p["h_base"], p["h_bar"]
    # Sedimento a montante de cada paliçada
    sed_w = sed_offsets.get(p["label"], 2.5)
    ax.fill_betweenx([yb_p, yb_p + ht * 0.85],
                     [xp - sed_w, xp - sed_w], [xp - 0.1, xp - 0.1],
                     color=C_SED, alpha=0.45, zorder=3)
    # Barreira (colmos horizontais)
    for dy in np.arange(0, ht, 0.18):
        y0 = yb_p + dy
        ax.plot([xp - 0.08, xp + 0.08], [y0, y0],
                color=C_BAMBU, lw=3.5, solid_capstyle="round", zorder=5)
    # Estaca vertical (penetra 0.35 no solo)
    ax.plot([xp, xp], [yb_p - 0.35, yb_p + ht],
            color=C_BAMBU2, lw=4, solid_capstyle="round", zorder=4)
    # Rótulo acima da barreira
    ax.text(xp, yb_p + ht + 0.15, p["label"],
            ha="center", va="bottom", fontsize=9, fontweight="bold",
            color=C_BAMBU2, zorder=6)
    # Tag de posição (abaixo do fundo)
    ax.text(xp, yb_p - 0.45, p["tag"],
            ha="center", va="top", fontsize=7.5, color="#555",
            style="italic", zorder=6)

# Destaque MED com caixa — calculado a partir da geometria de P3
_p3_base = _y_floor(12.5)
_p3_top  = _p3_base + (_y_surface(12.5) - _p3_base) * _fill_ratio
ax.add_patch(FancyBboxPatch((10.8, _p3_base - 0.8),
                             3.5, (_p3_top - _p3_base) + 1.6,
                             boxstyle="round,pad=0.15",
                             linewidth=1.5, edgecolor=C_STRAIN,
                             facecolor="none", linestyle="--", zorder=7))
ax.text(14.5, _p3_top + 0.3, "segmento MED\n(ensaios de campo)",
        ha="left", va="center", fontsize=8, color=C_STRAIN,
        bbox=dict(fc=C_BG, ec="none", pad=2))

# Seta de fluxo — centralizada no vão de escoamento
_arrow_x0, _arrow_x1 = 1.5, 4.0
_arrow_y0 = (_y_floor(_arrow_x0) + _y_surface(_arrow_x0)) / 2.0
_arrow_y1 = (_y_floor(_arrow_x1) + _y_surface(_arrow_x1)) / 2.0
_arrow_rot = np.degrees(np.arctan2(_arrow_y1 - _arrow_y0, _arrow_x1 - _arrow_x0))
ax.annotate("", xy=(_arrow_x1, _arrow_y1), xytext=(_arrow_x0, _arrow_y0),
            arrowprops=dict(arrowstyle="-|>", color=C_AGUA, lw=2), zorder=8)
ax.text((_arrow_x0 + _arrow_x1) / 2.0, (_arrow_y0 + _arrow_y1) / 2.0 + 0.25,
        "Escoamento", fontsize=8, color=C_AGUA, rotation=_arrow_rot,
        ha="center", va="bottom",
        bbox=dict(fc=C_BG, ec="none", pad=1, alpha=0.85), zorder=8)

# Escala de referência — calibrada por GPS (P1_SUP→P3_INF ≈ 132 m em 12,5 u → 1 u ≈ 10,6 m)
_scale_units = 2.0          # comprimento da barra em unidades do eixo
_scale_m     = 20.0         # metros reais correspondentes
ax.plot([18.5, 18.5 + _scale_units], [-1.0, -1.0], color="k", lw=1.5)
ax.plot([18.5, 18.5], [-0.9, -1.1], color="k", lw=1.5)
ax.plot([18.5 + _scale_units, 18.5 + _scale_units], [-0.9, -1.1], color="k", lw=1.5)
ax.text(18.5 + _scale_units / 2, -1.3, f"~{_scale_m:.0f} m",
        ha="center", va="top", fontsize=7.5, color="k")

ax.set_title("(b)  Perfil longitudinal esquem\u00e1tico \u2014 pali\u00e7adas P1 a P4 em s\u00e9rie",
             fontsize=10, loc="left", color=C_LABEL, pad=6)

# ── save fig_4a ─────────────────────────────────────────────────────────────
out_4a = BASE + r"\Fig_metodologia_4a.png"
fig_4a.savefig(out_4a, dpi=180, bbox_inches="tight", facecolor=C_BG)
print(f"Figura 4a salva em:\n{out_4a}")
plt.close(fig_4a)

# ═══════════════════════════════════════════════════════════════════════════
# FIGURA 5 — Esquema dos ensaios de campo (dois painéis empilhados)
#   (a) Seção transversal da paliçada MED — instrumentação de campo
#   (b) Disposição dos corpos de prova — degradação in situ (Ensaio 5.2)
# ═══════════════════════════════════════════════════════════════════════════

fig_5 = plt.figure(figsize=(16, 16), facecolor=C_BG)
gs5 = fig_5.add_gridspec(2, 1, height_ratios=[1, 1], hspace=0.28)
ax_a5 = fig_5.add_subplot(gs5[0])
ax_b5 = fig_5.add_subplot(gs5[1])

for ax in (ax_a5, ax_b5):
    ax.set_facecolor(C_BG)
    for spine in ax.spines.values():
        spine.set_visible(False)
    ax.set_xticks([]); ax.set_yticks([])

# ───────────────────────────────────────────────────────────────────────────
# PAINEL (a) — Seção transversal frontal da paliçada MED
# ───────────────────────────────────────────────────────────────────────────
# Escala: 1 unidade ≈ 0,30 m → H = 0,76 m ≈ 2,53 u; L = 3,00 m = 10 u
# Espaçamento estacas: 1,50 m = 5 u
# ───────────────────────────────────────────────────────────────────────────
ax = ax_a5
ax.set_xlim(-5.5, 22.0)
ax.set_ylim(-2.5, 7.5)

# ── Geometria da ravina (seção trapezoidal) ────────────────────────────────
# Fundo da ravina: y = 0, entre x_bot_L = 1.0 e x_bot_R = 15.0  (≈ 4,2 m)
# Talude inclinado: 1V:0,7H → a cada 1 u de subida, recua 0,7 u
# Topo dos taludes: y = 5.5  → deslocamento horizontal = 5.5 × 0.7 = 3.85
x_bot_L = 1.0      # pé do talude esquerdo
x_bot_R = 15.0     # pé do talude direito
slope = 0.70       # recuo horizontal por unidade de altura (1V:0,7H)
y_top_tal = 5.5    # topo visível dos taludes
dx_top = y_top_tal * slope  # 3.85

x_top_L = x_bot_L - dx_top   # ≈ -2.85
x_top_R = x_bot_R + dx_top   # ≈ 18.85

def face_x_left(y):
    """Coordenada x da face interna do talude esquerdo na altura y."""
    return x_bot_L - y * slope

def face_x_right(y):
    """Coordenada x da face interna do talude direito na altura y."""
    return x_bot_R + y * slope

# Talude esquerdo (polígono preenchido)
ax.fill([x_bot_L, x_top_L, -5.5, -5.5, x_bot_L],
        [0,        y_top_tal, y_top_tal, -2.5, -2.5],
        color=C_SOLO, alpha=0.50, zorder=1)
ax.plot([x_bot_L, x_top_L], [0, y_top_tal],
        color=C_SOLO2, lw=2.5, zorder=2)          # face do talude

# Talude direito
ax.fill([x_bot_R, x_top_R, 22.0, 22.0, x_bot_R],
        [0,        y_top_tal, y_top_tal, -2.5, -2.5],
        color=C_SOLO, alpha=0.50, zorder=1)
ax.plot([x_bot_R, x_top_R], [0, y_top_tal],
        color=C_SOLO2, lw=2.5, zorder=2)

# Fundo da ravina
ax.fill_between([x_bot_L, x_bot_R], [-2.5, -2.5], [0, 0],
                color=C_SOLO, alpha=0.60, zorder=2)
ax.plot([x_bot_L, x_bot_R], [0, 0], color=C_SOLO2, lw=2, zorder=3)

# Sedimento retido (~55% da altura da paliçada)
sed_top = 1.40
ax.fill_between([x_bot_L, x_bot_R], [0, 0], [sed_top, sed_top],
                color=C_SED, alpha=0.35, zorder=2)
ax.text(8.0, sed_top * 0.48, "sedimento retido", ha="center", va="center",
        fontsize=9, color="#7a5230", style="italic")

# ── Estacas verticais ──────────────────────────────────────────────────────
# 3 estacas: E1, E2 (central), E3 — espaçamento 5 u = 1,50 m
stake_xs = [3.0, 8.0, 13.0]
stake_names = ["E1", "E2", "E3"]
stake_bottom = -1.6
stake_top = 3.4         # afloram um pouco acima do colmo superior
for sx in stake_xs:
    ax.add_patch(plt.Rectangle((sx - 0.22, stake_bottom), 0.44, stake_top - stake_bottom,
                                color=C_BAMBU2, zorder=4, lw=0))

# ── Colmos horizontais — ancorados nos taludes ─────────────────────────────
# 6 colmos distribuídos em H ≈ 2,53 u  (0,76 m)
# Alturas relativas: colmo 1 (base) até colmo 6 (topo)
colmo_ys = [0.30, 0.74, 1.18, 1.62, 2.06, 2.50]
embed = 1.0   # comprimento de embutimento nos taludes

for cy in colmo_ys:
    xl_face = face_x_left(cy)    # x da face do talude esquerdo nesta altura
    xr_face = face_x_right(cy)   # x da face do talude direito nesta altura
    xl_embed = xl_face - embed    # extremidade embutida esquerda
    xr_embed = xr_face + embed   # extremidade embutida direita
    colmo_h = 0.28               # espessura visual do colmo

    # Trecho embutido esquerdo (mais escuro, dentro do talude)
    ax.add_patch(plt.Rectangle((xl_embed, cy - colmo_h/2), embed, colmo_h,
                                color=C_BAMBU2, alpha=0.50, zorder=5, lw=0))
    # Trecho visível (entre faces dos taludes)
    ax.add_patch(plt.Rectangle((xl_face, cy - colmo_h/2),
                                xr_face - xl_face, colmo_h,
                                color=C_BAMBU, zorder=5, lw=0))
    # Trecho embutido direito
    ax.add_patch(plt.Rectangle((xr_face, cy - colmo_h/2), embed, colmo_h,
                                color=C_BAMBU2, alpha=0.50, zorder=5, lw=0))
    # Amarrações de arame nas estacas
    for sx in stake_xs:
        ax.plot(sx, cy, "o", color=C_ARAME, ms=5, zorder=6)

# ── Instrumentação ─────────────────────────────────────────────────────────

# (5.7) Extensômetros — 3 colmos inferiores, estaca central E2
for cy in colmo_ys[:3]:
    ax.plot([8.25, 8.85], [cy, cy], color=C_STRAIN, lw=2, zorder=8)
    ax.plot(8.85, cy, "s", color=C_STRAIN, ms=7, zorder=8)
ax.annotate("Extensômetros\n(Ensaio 5.7 — SCF)",
            xy=(8.85, colmo_ys[1]), xytext=(8.0, -1.8),
            arrowprops=dict(arrowstyle="-|>", color=C_STRAIN, lw=1.4),
            fontsize=9, color=C_STRAIN, va="center", ha="center",
            bbox=dict(fc="white", ec="none", pad=2, alpha=0.92),
            zorder=10)

# (5.6) Comparador de deslocamento — acima do topo da estaca central
comp_bot = colmo_ys[-1] + 0.50
comp_top = comp_bot + 1.8
ax.annotate("", xy=(8.0, comp_bot), xytext=(8.0, comp_top),
            arrowprops=dict(arrowstyle="<->", color=C_DISP, lw=2.5))
ax.text(8.5, (comp_bot + comp_top)/2, "Comparador\n(Ensaio 5.6)",
        fontsize=9, color=C_DISP, va="center")

# (5.5) Prova de carga lateral — macaco posicionado fora do talude esquerdo
load_y = colmo_ys[3]   # meia-altura da paliçada
face_at_load = face_x_left(load_y)
ax.annotate("", xy=(stake_xs[0] - 0.22, load_y),
            xytext=(face_at_load - 0.15, load_y),
            arrowprops=dict(arrowstyle="-|>", color=C_LOAD, lw=3))
box_w, box_h = 2.2, 1.2
box_x = face_at_load - 0.15 - box_w
ax.add_patch(FancyBboxPatch((box_x, load_y - box_h/2), box_w, box_h,
                             boxstyle="round,pad=0.08",
                             facecolor=C_LOAD, edgecolor="none", zorder=7))
ax.text(box_x + box_w/2, load_y, "F", ha="center", va="center",
        fontsize=13, fontweight="bold", color="white", zorder=8)
ax.text(box_x + box_w/2, load_y - box_h/2 - 0.25,
        "Prova de carga (Ensaio 5.5)", ha="center", va="top",
        fontsize=9, color=C_LOAD,
        bbox=dict(fc="white", ec="none", pad=2, alpha=0.92),
        zorder=10)

# (5.4) Inclinômetro — junção colmo-estaca E3
incl_y = colmo_ys[2]
ax.plot(stake_xs[2], incl_y, "D", color="#9b2226", ms=9, zorder=8)
ax.annotate("Inclinômetro\n(Ensaio 5.4 — $k_θ$)",
            xy=(stake_xs[2] + 0.3, incl_y),
            xytext=(face_x_right(incl_y) + 1.8, incl_y + 1.8),
            arrowprops=dict(arrowstyle="-|>", color="#9b2226", lw=1.4),
            fontsize=9, color="#9b2226", va="center",
            bbox=dict(fc="white", ec="none", pad=2, alpha=0.92),
            zorder=10)

# ── Cotas dimensionais ─────────────────────────────────────────────────────
# H = 0,76 m (entre colmo inferior e superior) — posicionado mais para a direita
cota_x = face_x_right(colmo_ys[-1]) + 2.5
ax.annotate("", xy=(cota_x, colmo_ys[0]), xytext=(cota_x, colmo_ys[-1]),
            arrowprops=dict(arrowstyle="<->", color="k", lw=1.2),
            zorder=10)
ax.text(cota_x + 0.35, (colmo_ys[0] + colmo_ys[-1])/2,
        "H = 0,76 m", fontsize=9, va="center", rotation=90,
        bbox=dict(fc="white", ec="none", pad=2, alpha=0.92),
        zorder=10)

# L = 3,00 m (entre estacas externas)
cota_y = -2.0
ax.annotate("", xy=(stake_xs[0], cota_y), xytext=(stake_xs[2], cota_y),
            arrowprops=dict(arrowstyle="<->", color="k", lw=1.2))
ax.text(8.0, cota_y - 0.3, "L = 3,00 m", ha="center", va="top", fontsize=9)

# Nomes das estacas
for sx, nm in zip(stake_xs, stake_names):
    ax.text(sx, stake_top + 0.15, nm, ha="center", va="bottom",
            fontsize=8, fontweight="bold", color=C_BAMBU2)

# ── Legenda ────────────────────────────────────────────────────────────────
legend_a = [
    mpatches.Patch(color=C_STRAIN, label="Extensômetros — SCF (Ensaio 5.7)"),
    mpatches.Patch(color=C_DISP,   label="Comparador de deslocamento (Ensaio 5.6)"),
    mpatches.Patch(color=C_LOAD,   label="Prova de carga lateral (Ensaio 5.5)"),
    mpatches.Patch(color="#9b2226", label="Inclinômetro — $k_θ$ (Ensaio 5.4)"),
]
ax.legend(handles=legend_a, loc="upper right", fontsize=8,
          framealpha=0.95, edgecolor="#bbb", frameon=True,
          bbox_to_anchor=(1.0, 1.0))

ax.set_title("(a)  Seção transversal da paliçada MED — localização dos ensaios de campo",
             fontsize=11, fontweight="bold", loc="left", color=C_LABEL, pad=8)

# ───────────────────────────────────────────────────────────────────────────
# PAINEL (b) — Disposição dos corpos de prova — degradação in situ
# ───────────────────────────────────────────────────────────────────────────
ax = ax_b5
ax.set_xlim(-1.5, 12.5)
ax.set_ylim(-5.0, 3.5)

# Solo
ax.fill_between([-1.0, 11.5], [-4.5, -4.5], [0, 0],
                color=C_SOLO, alpha=0.50, zorder=1)
ax.plot([-1.0, 11.5], [0, 0], color=C_SOLO2, lw=2.5, zorder=2)
ax.text(0.0, 0.25, "Superfície do solo", fontsize=9, color=C_SOLO2)

# Linha de 15 cm de profundidade
ax.plot([-1.0, 11.5], [-1.8, -1.8], color=C_SOLO2, lw=1.2,
        linestyle="--", alpha=0.6, zorder=3)
ax.annotate("", xy=(-0.6, -1.8), xytext=(-0.6, 0),
            arrowprops=dict(arrowstyle="<->", color=C_SOLO2, lw=1.2))
ax.text(-0.85, -0.9, "15 cm", fontsize=8.5, ha="right", va="center",
        color=C_SOLO2)

# ── Corpos de prova (6 sacos de tela) ──────────────────────────────────────
colors_cp = {
    "Cisalhamento\nnodal":     "#d62828",
    "Cisalhamento\ninternodal":"#f77f00",
    "Flexão":                  "#4cc9f0",
}
positions = [
    (1.2,  "Cisalhamento\nnodal"),
    (3.0,  "Cisalhamento\nnodal"),
    (4.8,  "Cisalhamento\ninternodal"),
    (6.6,  "Cisalhamento\ninternodal"),
    (8.4,  "Flexão"),
    (10.2, "Flexão"),
]

cp_y = -1.8
cp_w, cp_h = 1.3, 1.6
# Dimensões de cada mini-cilindro (5 CPs empilhados por saco)
_n_cp = 5
_cyl_w = 0.80           # largura do cilindro
_gap = 0.04             # espaço entre cilindros
_usable_h = cp_h - 0.30 # altura útil dentro do saco (descontando padding)
_cyl_h = (_usable_h - (_n_cp - 1) * _gap) / _n_cp   # altura de cada cilindro
_ell_ry = 0.06          # semi-eixo vertical das elipses (perspectiva)

for (xcp, tipo) in positions:
    col = colors_cp[tipo]
    # Saco de tela (envelope externo)
    ax.add_patch(mpatches.FancyBboxPatch(
        (xcp - cp_w/2, cp_y - cp_h/2), cp_w, cp_h,
        boxstyle="round,pad=0.10",
        facecolor=col, edgecolor=C_MESH, linewidth=1.8,
        alpha=0.75, zorder=4))

    # ── 5 corpos de prova cilíndricos empilhados ──
    _stack_bot = cp_y - _usable_h / 2
    for i in range(_n_cp):
        _bot_i = _stack_bot + i * (_cyl_h + _gap)
        _top_i = _bot_i + _cyl_h

        # Corpo lateral (retângulo)
        ax.add_patch(plt.Rectangle(
            (xcp - _cyl_w / 2, _bot_i), _cyl_w, _cyl_h,
            facecolor="white", edgecolor="none", alpha=0.65, zorder=5))
        # Bordas laterais
        ax.plot([xcp - _cyl_w / 2] * 2, [_bot_i, _top_i],
                color=col, lw=0.9, alpha=0.85, zorder=6)
        ax.plot([xcp + _cyl_w / 2] * 2, [_bot_i, _top_i],
                color=col, lw=0.9, alpha=0.85, zorder=6)

        # Elipse inferior (base, tracejada)
        ax.add_patch(mpatches.Ellipse(
            (xcp, _bot_i), _cyl_w, 2 * _ell_ry,
            facecolor="white", edgecolor=col, linewidth=0.7,
            linestyle="--", alpha=0.45, zorder=6))

        # Elipse superior (topo, opaca)
        ax.add_patch(mpatches.Ellipse(
            (xcp, _top_i), _cyl_w, 2 * _ell_ry,
            facecolor="white", edgecolor=col, linewidth=0.9,
            alpha=0.75, zorder=7))

        # Linha central de fibra (textura do bambu)
        _mid_i = (_bot_i + _top_i) / 2
        ax.plot([xcp - _cyl_w / 2 + 0.05, xcp + _cyl_w / 2 - 0.05],
                [_mid_i] * 2, color=col, lw=0.5, alpha=0.40, zorder=6)

    # Plaqueta de identificação
    ax.plot(xcp + 0.42, cp_y + 0.55, "s", color="silver",
            ms=5, markeredgecolor="gray", zorder=7)

# ── Sensor T/UR ────────────────────────────────────────────────────────────
sensor_x, sensor_y = 0.3, -3.6
ax.add_patch(FancyBboxPatch((sensor_x - 0.6, sensor_y - 0.5), 1.2, 1.0,
                             boxstyle="round,pad=0.10",
                             facecolor="#023e8a", edgecolor="#0096c7",
                             linewidth=2, zorder=4))
ax.text(sensor_x, sensor_y, "T / UR", ha="center", va="center",
        fontsize=9, color="white", fontweight="bold", zorder=5)
ax.plot([sensor_x, sensor_x], [sensor_y + 0.5, cp_y - cp_h/2],
        color="#0096c7", lw=1.2, linestyle=":", zorder=3)
ax.text(sensor_x + 0.75, sensor_y,
        "  Datalogger\n  (registro horário)",
        fontsize=8, color="#0096c7", va="center")

# ── Setas de retirada semestral ────────────────────────────────────────────
for (xcp, _) in positions:
    ax.annotate("", xy=(xcp, 0.7), xytext=(xcp, 0.15),
                arrowprops=dict(arrowstyle="-|>", color="#505050", lw=1.2))

ax.text(5.7, 1.3, "Retirada semestral  (t = 0, 6, 12, 18, 24, 30 meses)",
        ha="center", va="bottom", fontsize=9, color="#444",
        bbox=dict(fc=C_BG, ec="#ccc", pad=3, boxstyle="round,pad=0.3"))

# ── Legenda de cores ───────────────────────────────────────────────────────
legend_b = [
    mpatches.Patch(color="#d62828", label="CP cisalhamento nodal (5 × 2)"),
    mpatches.Patch(color="#f77f00", label="CP cisalhamento internodal (5 × 2)"),
    mpatches.Patch(color="#4cc9f0", label="CP flexão (5 × 2)"),
    mpatches.Patch(color="#023e8a", label="Sensor T/UR (registro contínuo)"),
]
ax.legend(handles=legend_b, loc="upper right", fontsize=8,
          framealpha=0.95, edgecolor="#ccc", frameon=True,
          bbox_to_anchor=(1.0, 1.0))

# Nota de total de CPs
ax.text(5.7, -4.5,
        "Total por retirada: 10 CP cisalhamento + 10 CP flexão + controles laboratoriais",
        ha="center", va="top", fontsize=8.5, color="#333", style="italic",
        bbox=dict(fc="white", ec="#ccc", pad=3, boxstyle="round,pad=0.3"))

ax.set_title("(b)  Disposição dos corpos de prova — ensaio de degradação in situ (Ensaio 5.2)",
             fontsize=11, fontweight="bold", loc="left", color=C_LABEL, pad=8)

# ── Salvar ─────────────────────────────────────────────────────────────────
out_5 = BASE + r"\Fig_metodologia_4b.png"
fig_5.savefig(out_5, dpi=180, bbox_inches="tight", facecolor=C_BG)
print(f"Figura 5 salva em:\n{out_5}")
plt.close(fig_5)
