"""
Gera figura esquemática do experimento de erosão — v2.
  (a) Parcela individual Wischmeier com divisor Geib e tanques
      — proporção ESQUEMÁTICA (não em escala real 1:12)
  (b) Distribuição das 28 parcelas nos 3 sítios
"""
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyBboxPatch

fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(17, 9),
                                gridspec_kw={'width_ratios': [1, 1], 'wspace': 0.05})

# ============================================================
# (a) PARCELA INDIVIDUAL — vista em planta (ESQUEMÁTICA)
# ============================================================
ax1.set_xlim(-5, 19)
ax1.set_ylim(-7, 20)
ax1.set_aspect('equal')
ax1.axis('off')
ax1.set_title('(a) Parcela padrão Wischmeier (esquemático, fora de escala)',
              fontsize=11, fontweight='bold', pad=10)

# Dimensões esquemáticas (proporção visual ~1:2.5)
pw = 6.0    # largura visual
ph = 15.0   # altura visual
px0, py0 = 2.0, 1.5

# --- Solo nu (preenchimento) ---
ax1.add_patch(plt.Rectangle((px0, py0), pw, ph,
              facecolor='#F5DEB3', edgecolor='none', zorder=1))

# --- Chapas galvanizadas (3 lados: esq, dir, topo) ---
ct = 0.35
for rx, ry, rw, rh in [
    (px0 - ct, py0 - 0.5, ct, ph + 1.0),    # esquerda
    (px0 + pw, py0 - 0.5, ct, ph + 1.0),     # direita
    (px0 - ct, py0 + ph, pw + 2*ct, ct),      # topo
]:
    ax1.add_patch(plt.Rectangle((rx, ry), rw, rh,
                  facecolor='#909090', edgecolor='#505050', linewidth=1.2, zorder=3))

# Label chapas
ax1.annotate('Chapas galvanizadas\n(enterradas 15 cm)',
             xy=(px0 - ct, py0 + ph * 0.65),
             xytext=(-4.0, py0 + ph * 0.75),
             fontsize=8.5, ha='center', va='center',
             arrowprops=dict(arrowstyle='->', color='#505050', lw=1.3),
             bbox=dict(boxstyle='round,pad=0.3', facecolor='#E0E0E0', edgecolor='#505050'))

# --- Cotagens ---
# Comprimento (vertical)
cx = px0 + pw + ct + 1.2
ax1.annotate('', xy=(cx, py0), xytext=(cx, py0 + ph),
             arrowprops=dict(arrowstyle='<->', color='k', lw=1.3))
ax1.text(cx + 0.4, py0 + ph/2, '22,13 m', fontsize=10,
         rotation=90, ha='left', va='center', fontweight='bold')
# Largura (horizontal)
cy = py0 + ph + ct + 0.8
ax1.annotate('', xy=(px0, cy), xytext=(px0 + pw, cy),
             arrowprops=dict(arrowstyle='<->', color='k', lw=1.3))
ax1.text(px0 + pw/2, cy + 0.5, '1,83 m', fontsize=10,
         ha='center', va='bottom', fontweight='bold')

# --- Seta de declive ---
ax1.annotate('', xy=(px0 + pw/2, py0 + 1.5),
             xytext=(px0 + pw/2, py0 + ph - 1.5),
             arrowprops=dict(arrowstyle='->', color='#2E86C1', lw=3.0))
ax1.text(px0 + pw/2 + 0.8, py0 + ph * 0.6, 'Declive',
         fontsize=10, ha='left', va='center', color='#2E86C1',
         fontweight='bold', rotation=90)

# --- Texto central ---
ax1.text(px0 + pw/2, py0 + ph/2,
         'Solo nu\n(C = P = 1,0)\n\nA = 40,5 m²',
         fontsize=10, ha='center', va='center', style='italic',
         bbox=dict(boxstyle='round,pad=0.5', facecolor='#F5DEB3',
                   edgecolor='#8B7355', alpha=0.95))

# --- Divisor Geib (base da parcela) ---
geib_h = 1.0
geib_y = py0 - geib_h
ax1.add_patch(plt.Rectangle((px0 - 0.2, geib_y), pw + 0.4, geib_h,
              facecolor='#3B6E8C', edgecolor='#1A3A4A', linewidth=1.5, zorder=4))
n_slots = 11
for i in range(1, n_slots):
    sx = px0 - 0.2 + i * (pw + 0.4) / n_slots
    ax1.plot([sx, sx], [geib_y, geib_y + geib_h],
             color='#1A3A4A', lw=0.9, zorder=5)
ax1.text(px0 + pw/2, geib_y + geib_h/2, 'Divisor Geib',
         fontsize=9.5, ha='center', va='center', color='white',
         fontweight='bold', zorder=6)

# Label Geib
ax1.annotate('Divisor Geib: fendas de largura\nconhecida separam a fração\namostrada (1/n) do escoamento total',
             xy=(px0 - 0.2, geib_y + geib_h/2),
             xytext=(-4.0, geib_y + 0.5),
             fontsize=7.5, ha='center', va='top',
             arrowprops=dict(arrowstyle='->', color='#3B6E8C', lw=1.2),
             bbox=dict(boxstyle='round,pad=0.3', facecolor='#D6EAF8', edgecolor='#3B6E8C'))

# --- Tubulação Geib → Tanque 1 ---
mid_x = px0 + pw/2
ax1.plot([mid_x, mid_x], [geib_y, geib_y - 1.2],
         color='#2F4F4F', lw=3.5, zorder=3)
ax1.plot([mid_x, mid_x + 3.5], [geib_y - 1.2, geib_y - 1.2],
         color='#2F4F4F', lw=3.5, zorder=3)
ax1.plot([mid_x + 3.5, mid_x + 3.5], [geib_y - 1.2, geib_y - 1.8],
         color='#2F4F4F', lw=3.5, zorder=3)

# --- Tanque 1 ---
t1w, t1h = 3.0, 2.5
t1x = mid_x + 3.5 - t1w/2
t1y = geib_y - 1.8 - t1h
ax1.add_patch(plt.Rectangle((t1x, t1y), t1w, t1h,
              facecolor='#AED6F1', edgecolor='#2F4F4F', linewidth=1.5, zorder=4))
ax1.add_patch(plt.Rectangle((t1x + 0.08, t1y + 0.08), t1w - 0.16, 0.7,
              facecolor='#C4A35A', edgecolor='none', zorder=5, alpha=0.7))
ax1.text(t1x + t1w/2, t1y + t1h/2 + 0.3, 'Tanque 1\n(coleta 1/n)',
         fontsize=8.5, ha='center', va='center', fontweight='bold', zorder=6)

# Overflow → Tanque 2
t2x = t1x + t1w + 1.5
t2y = t1y
ax1.plot([t1x + t1w, t2x], [t1y + t1h - 0.5, t1y + t1h - 0.5],
         color='#2F4F4F', lw=2.5, zorder=3)
ax1.plot([t2x, t2x], [t1y + t1h - 0.5, t1y + t1h - 0.9],
         color='#2F4F4F', lw=2.5, zorder=3)
ax1.text((t1x + t1w + t2x)/2, t1y + t1h - 0.1, 'overflow',
         fontsize=7.5, ha='center', va='bottom', color='#2F4F4F', style='italic')

# --- Tanque 2 ---
ax1.add_patch(plt.Rectangle((t2x, t2y), t1w, t1h,
              facecolor='#D4E6F1', edgecolor='#2F4F4F', linewidth=1.5, zorder=4))
ax1.add_patch(plt.Rectangle((t2x + 0.08, t2y + 0.08), t1w - 0.16, 0.4,
              facecolor='#C4A35A', edgecolor='none', zorder=5, alpha=0.5))
ax1.text(t2x + t1w/2, t2y + t1h/2 + 0.3, 'Tanque 2\n(armazenamento)',
         fontsize=8.5, ha='center', va='center', fontweight='bold', zorder=6)

# Label tanques
ax1.text((t1x + t2x + t1w) / 2, t1y - 0.6,
         'Tanques de armazenamento de sedimentos',
         fontsize=8.5, ha='center', va='top',
         bbox=dict(boxstyle='round,pad=0.3', facecolor='#D6EAF8', edgecolor='#2E86C1'))

# ============================================================
# (b) DISTRIBUIÇÃO DAS 28 PARCELAS NOS 3 SÍTIOS
# ============================================================
ax2.set_xlim(-0.5, 14)
ax2.set_ylim(-2.5, 29)
ax2.set_aspect('equal')
ax2.axis('off')
ax2.set_title('(b) Distribuição das 28 parcelas nos 3 sítios',
              fontsize=11, fontweight='bold', pad=10)

C_NU  = '#F5DEB3'
C_BAC = '#E74C3C'
C_BT  = '#E67E22'
C_VEG = '#27AE60'

def draw_site(ax, y0, label, bg_color, parcels, subtitle):
    """
    Layout vertical calculado (de baixo para cima, dentro da caixa):
       y0 + 0.50  ─── base da 1ª fileira de parcelas
       y0 + 4.80  ─── topo da 3ª fileira  (3 × 1.3 + 2 × 0.2)
       y0 + 5.35  ─── rótulo do grupo (0.55 acima das parcelas)
       y0 + 7.30  ─── subtítulo          (box_h - 1.20)
       y0 + 8.15  ─── título             (box_h - 0.35)
       y0 + 8.50  ─── topo da caixa
    """
    box_w, box_h = 13.0, 8.5
    x0 = 0.3
    ax.add_patch(FancyBboxPatch((x0, y0), box_w, box_h,
                 boxstyle='round,pad=0.25', facecolor=bg_color,
                 edgecolor='#333', linewidth=1.5, alpha=0.12, zorder=1))
    # Título e subtítulo no topo da caixa, bem acima dos rótulos de grupo
    ax.text(x0 + 0.3, y0 + box_h - 0.35, label, fontsize=10,
            fontweight='bold', va='top', color='#333', zorder=10)
    ax.text(x0 + 0.3, y0 + box_h - 1.20, subtitle, fontsize=7.5,
            va='top', color='#555', style='italic', zorder=10)

    pw_mini, ph_mini = 0.7, 1.3
    gap = 0.2
    group_gap = 1.6
    parcel_base = y0 + 0.5
    # Rótulos de grupo: topo das parcelas (y0+5.0) + 0.35 de folga
    label_y = parcel_base + 3 * (ph_mini + gap) + 0.35

    cx = x0 + 0.5
    for n, color, lbl in parcels:
        for i in range(n):
            col = i // 3
            row = i % 3
            mx = cx + col * (pw_mini + gap)
            my = parcel_base + row * (ph_mini + gap)
            ax.add_patch(plt.Rectangle((mx, my), pw_mini, ph_mini,
                        facecolor=color, edgecolor='#333', linewidth=0.9, zorder=3))
        n_cols = max(1, (n - 1) // 3 + 1)
        center_x = cx + (n_cols * (pw_mini + gap) - gap) / 2
        ax.text(center_x, label_y,
                f'{lbl}\n({n})', fontsize=7.5, ha='center', va='bottom',
                fontweight='bold', color='#333', zorder=10)
        cx += n_cols * (pw_mini + gap) + group_gap

# Espaçamento entre caixas = 0.5 u
draw_site(ax2, 18.5, 'S1 — Plintossolo (alvo)', '#E74C3C',
          [(3, C_NU, 'Solo nu'), (1, C_BAC, 'BAc exposto'), (1, C_VEG, 'Cobertura')],
          '3 posições × 1 rep  +  1 BAc  +  1 veg  =  5 parcelas')

draw_site(ax2, 9.5, 'S2 — Latossolo (controle negativo)', '#3498DB',
          [(3, C_NU, 'Solo nu'), (1, C_VEG, 'Cobertura')],
          '1 posição × 3 rep  +  1 veg  =  4 parcelas')

draw_site(ax2, 0.5, 'S3 — Argissolo (controle parcial)', '#F39C12',
          [(3, C_NU, 'Solo nu'), (1, C_BT, 'Bt exposto'), (1, C_VEG, 'Cobertura')],
          '1 posição × 3 rep  +  1 Bt  +  1 veg  =  5 parcelas')

legend_elements = [
    mpatches.Patch(facecolor=C_NU,  edgecolor='#333', label='Solo nu (C = P = 1,0)'),
    mpatches.Patch(facecolor=C_BAC, edgecolor='#333', label='BAc exposto (escav. controlada)'),
    mpatches.Patch(facecolor=C_BT,  edgecolor='#333', label='Bt exposto'),
    mpatches.Patch(facecolor=C_VEG, edgecolor='#333', label='Cobertura vegetal natural'),
]
ax2.legend(handles=legend_elements, loc='lower center',
           bbox_to_anchor=(0.5, -0.06), ncol=2, fontsize=8.5,
           frameon=True, fancybox=True, shadow=False)

ax2.text(6.8, -1.5, 'Total geral = 14 parcelas', fontsize=11,
         ha='center', fontweight='bold', color='#333',
         bbox=dict(boxstyle='round,pad=0.4', facecolor='#FDEBD0', edgecolor='#E67E22'))

# --- Salvar ---
out = (r'c:\Users\vidal\OneDrive\Documentos\13 - CLONEGIT\artigo-posdoc'
       r'\3-EROSIBIDADE\1-MANUSCRITOS\7-PROPOSTA_K_PLINTOSSOLO'
       r'\figuras\fig_esquema_parcela_experimento.png')
fig.savefig(out, dpi=300, bbox_inches='tight', facecolor='white')
print(f'OK: {out}')
plt.close()
