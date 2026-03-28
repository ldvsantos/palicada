"""
Gera:
  1) Fig_cronograma_gantt.png  — Gantt profissional (estilo revista Q1)
  2) Fig_equipamentos.png      — Painel com fotos CC-0 / CC-BY-SA dos equipamentos

Todas as imagens são obtidas do Wikimedia Commons sob licenças abertas.
"""

import io, urllib.request
from pathlib import Path

import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import matplotlib.patheffects as pe
import numpy as np
from PIL import Image

OUT = Path(__file__).parent

# ══════════════════════════════════════════════════════════════════════
# 1. GRÁFICO DE GANTT — ESTILO MODERNO
# ══════════════════════════════════════════════════════════════════════

def gantt():
    """Gera cronograma de Gantt elegante, agrupado por fase."""

    phases = [
        ("PREPARAÇÃO", [
            ("Revisão bibliográfica",               [(1,2)]),
            ("Colheita e preparo dos CP",            [(1,2)]),
        ]),
        ("ENSAIOS LABORATORIAIS", [
            ("Cisalhamento interlaminar (5.1)",      [(2,1)]),
            ("Flexão estática (5.3)",                [(2,1)]),
            ("Extensometria SCF (5.7)",              [(3,1)]),
        ]),
        ("ENSAIOS DE CAMPO", [
            ("Degradação in situ (5.2)",             [(2,10)]),
            ("Rigidez da conexão (5.4)",             [(3,1)]),
            ("Prova de carga lateral (5.5)",         [(4,1)]),
            ("Monitoramento deslocamento (5.6)",     [(4,2)]),
        ]),
        ("ANÁLISE E MODELAGEM", [
            ("Análise parcial (k semestral)",        [(6,1),(9,1)]),
            ("Recalibração do modelo FEM",           [(10,2)]),
            ("Simulação — parâmetros atualizados",   [(11,1)]),
        ]),
        ("ENTREGÁVEIS", [
            ("Redação do relatório e artigo",        [(11,2)]),
        ]),
    ]

    phase_colors = {
        "PREPARAÇÃO":            "#64748B",
        "ENSAIOS LABORATORIAIS": "#2563EB",
        "ENSAIOS DE CAMPO":      "#059669",
        "ANÁLISE E MODELAGEM":   "#7C3AED",
        "ENTREGÁVEIS":           "#DC2626",
    }

    rows = []
    phase_spans = []
    for ph_name, items in phases:
        y0 = len(rows)
        for label, segs in items:
            rows.append((label, segs, phase_colors[ph_name]))
        y1 = len(rows) - 1
        phase_spans.append((ph_name, y0, y1))

    n = len(rows)
    bar_h = 0.52
    fig_w, fig_h = 11.5, 0.48 * n + 2.4

    fig, ax = plt.subplots(figsize=(fig_w, fig_h), dpi=150)
    fig.patch.set_facecolor("white")
    ax.set_facecolor("#FAFBFC")

    # faixas alternadas
    for ph_name, y0, y1 in phase_spans:
        idx = list(phase_colors.keys()).index(ph_name)
        if idx % 2 == 0:
            ax.axhspan(n - 1 - y1 - 0.45, n - 1 - y0 + 0.45,
                        color="#F1F5F9", zorder=0)

    # barras (FancyBboxPatch arredondado)
    for i, (label, segs, cor) in enumerate(rows):
        y = n - 1 - i
        for (inicio, dur) in segs:
            bar = mpatches.FancyBboxPatch(
                (inicio - 0.42, y - bar_h / 2), dur - 0.16, bar_h,
                boxstyle=mpatches.BoxStyle.Round(pad=0.06),
                facecolor=cor, edgecolor="white", linewidth=0.8, zorder=5,
            )
            ax.add_patch(bar)
            meses = dur * 2
            if dur >= 2:
                ax.text(inicio - 0.42 + (dur - 0.16) / 2, y,
                        f"{meses} m", ha="center", va="center",
                        fontsize=6.5, color="white", fontweight="bold",
                        zorder=6)

    # milestones
    milestones = [(6, "1.ª recalibração"), (12, "Entrega final")]
    for bim, tip in milestones:
        ax.plot(bim, -0.9, marker="D", markersize=8,
                color="#F59E0B", markeredgecolor="#92400E",
                markeredgewidth=1, zorder=7, clip_on=False)
        ax.text(bim, -1.45, tip, ha="center", va="top",
                fontsize=6.5, color="#92400E", fontstyle="italic",
                zorder=7, clip_on=False)

    # eixos
    bimestres = np.arange(1, 13)
    labels_bim = [f"M{2*b-1}–M{2*b}" for b in bimestres]
    ax.set_xticks(bimestres)
    ax.set_xticklabels(labels_bim, fontsize=7, rotation=45, ha="right",
                       color="#374151")
    ax.set_xlim(0.2, 12.8)

    ylabels = [r[0] for r in reversed(rows)]
    ax.set_yticks(range(n))
    ax.set_yticklabels(ylabels, fontsize=7.5, color="#1F2937")
    ax.set_ylim(-1.8, n - 0.3)

    for b in np.arange(0.5, 13.5, 1):
        ax.axvline(b, color="#E5E7EB", linewidth=0.4, zorder=1)

    # rótulos de fase (lateral)
    for ph_name, y0, y1 in phase_spans:
        yc = n - 1 - (y0 + y1) / 2
        ax.text(13.05, yc, ph_name, ha="left", va="center",
                fontsize=6, fontweight="bold", color=phase_colors[ph_name],
                clip_on=False,
                path_effects=[pe.withStroke(linewidth=2, foreground="white")])

    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.spines["left"].set_visible(False)
    ax.spines["bottom"].set_color("#9CA3AF")
    ax.tick_params(axis="y", length=0)
    ax.tick_params(axis="x", colors="#6B7280", length=3)

    leg = [mpatches.Patch(color=c, label=n) for n, c in phase_colors.items()]
    leg.append(plt.Line2D([0], [0], marker="D", color="w",
               markerfacecolor="#F59E0B", markeredgecolor="#92400E",
               markersize=7, label="Marco"))
    ax.legend(handles=leg, loc="lower left", fontsize=6.5,
              frameon=True, fancybox=False, edgecolor="#D1D5DB",
              ncol=3, bbox_to_anchor=(0.0, -0.28))

    plt.tight_layout()
    out = OUT / "Fig_cronograma_gantt.png"
    fig.savefig(out, dpi=300, bbox_inches="tight", facecolor="white")
    plt.close()
    print(f"[OK] Gantt: {out}")


# ══════════════════════════════════════════════════════════════════════
# 2. PAINEL DE EQUIPAMENTOS (Wikimedia Commons — CC0 / CC-BY-SA)
# ══════════════════════════════════════════════════════════════════════

EQUIP = [
    (
        "https://upload.wikimedia.org/wikipedia/commons/thumb/2/22/"
        "Tensile_testing_on_a_coir_composite.jpg/"
        "600px-Tensile_testing_on_a_coir_composite.jpg",
        "(a) Máquina universal\nde ensaios (Instron)",
        "Kerina yin · CC0"
    ),
    (
        "https://upload.wikimedia.org/wikipedia/commons/thumb/4/44/"
        "Strain_gauge.jpg/600px-Strain_gauge.jpg",
        "(b) Extensômetro de\nresistência elétrica",
        "B. Tong Minh · CC BY-SA 3.0"
    ),
    (
        "https://upload.wikimedia.org/wikipedia/commons/thumb/f/f3/"
        "Nalepeny_tenzometr.jpg/600px-Nalepeny_tenzometr.jpg",
        "(c) Extensômetro colado\nem corpo de prova",
        "J. Běťák · CC BY-SA 3.0"
    ),
    (
        "https://upload.wikimedia.org/wikipedia/commons/thumb/a/a7/"
        "LoadCell_Waegezelle.jpg/600px-LoadCell_Waegezelle.jpg",
        "(d) Célula de carga\n(load cell)",
        "MakeMagazinDE · CC BY-SA 4.0"
    ),
    (
        "https://upload.wikimedia.org/wikipedia/commons/thumb/3/3f/"
        "Comparateur0.jpg/400px-Comparateur0.jpg",
        "(e) Comparador mecânico\n(dial gauge)",
        "Wikimedia · CC BY-SA 3.0"
    ),
    (
        "https://upload.wikimedia.org/wikipedia/commons/thumb/5/59/"
        "Monojack01.png/500px-Monojack01.png",
        "(f) Macaco hidráulico\npara prova de carga",
        "SRG Limited · CC BY-SA 4.0"
    ),
]


def _download(url: str) -> Image.Image:
    req = urllib.request.Request(
        url,
        headers={
            "User-Agent":
            "ProjetoIC-UEFS/1.0 (academic; ldvsantos@uefs.br)"
        },
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        return Image.open(io.BytesIO(resp.read())).convert("RGB")


def equipamentos():
    """Baixa imagens e monta painel 2×3 com bordas e rótulos."""
    ncols, nrows = 3, 2
    cell_w, cell_h = 3.3, 3.5
    fig, axes = plt.subplots(nrows, ncols,
                             figsize=(cell_w * ncols, cell_h * nrows),
                             dpi=150)
    fig.patch.set_facecolor("white")
    fig.suptitle("Equipamentos e instrumentos principais",
                 fontsize=11, fontweight="bold", color="#1F2937", y=0.99)

    for idx, (url, label, credit) in enumerate(EQUIP):
        r, c = divmod(idx, ncols)
        ax = axes[r][c]
        try:
            img = _download(url)
            ax.imshow(img, aspect="auto")
            print(f"  ✓ {label.split(chr(10))[0]}")
        except Exception as e:
            ax.text(0.5, 0.5, "[imagem\nindisponível]",
                    ha="center", va="center", fontsize=8, color="#9CA3AF",
                    transform=ax.transAxes)
            print(f"  ⚠ Falha: {e}")
        ax.set_xticks([])
        ax.set_yticks([])
        for spine in ax.spines.values():
            spine.set_color("#D1D5DB")
            spine.set_linewidth(0.6)
        ax.set_title(label, fontsize=8, fontweight="bold",
                     color="#1F2937", pad=6, loc="center")
        ax.text(0.99, 0.02, credit, transform=ax.transAxes,
                fontsize=4.5, color="#9CA3AF", ha="right", va="bottom",
                fontstyle="italic",
                bbox=dict(facecolor="white", alpha=0.7, edgecolor="none",
                          pad=1))

    plt.tight_layout(pad=1.5)
    out = OUT / "Fig_equipamentos.png"
    fig.savefig(out, dpi=300, bbox_inches="tight", facecolor="white")
    plt.close()
    print(f"[OK] Equipamentos: {out}")


# ══════════════════════════════════════════════════════════════════════
if __name__ == "__main__":
    gantt()
    equipamentos()
