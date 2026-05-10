"""Fig. 03 — Superficie krigada da espessura do deposito.

Standalone: roda sozinho, regerando sondagens e krigagem.
Saida: media/modelagem_3d/03_superficie_krigada.png

Vista 3D classica (elev=28, azim=-130) + mapa de isolinhas em planta.
"""

from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from pykrige.ok import OrdinaryKriging

# ----- Configuracao ---------------------------------------------------------
SEED = 42
rng = np.random.default_rng(SEED)

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "media" / "modelagem_3d"
OUT.mkdir(parents=True, exist_ok=True)

LARGURA_X = 4.0
COMPRIMENTO_Y = 6.0
ESP_MAX = 0.55


def gerar_sondagens(n_pontos: int = 24) -> pd.DataFrame:
    nx, ny = 4, 6
    xs = np.linspace(0.4, LARGURA_X - 0.4, nx)
    ys = np.linspace(0.3, COMPRIMENTO_Y - 0.3, ny)
    XX, YY = np.meshgrid(xs, ys)
    pts = np.column_stack([XX.ravel(), YY.ravel()])
    pts += rng.normal(0, 0.12, size=pts.shape)
    if len(pts) > n_pontos:
        pts = pts[rng.choice(len(pts), n_pontos, replace=False)]

    registros = []
    for i, (x, y) in enumerate(pts, start=1):
        h = ESP_MAX * np.exp(-y / 2.6) * (
            1.0 - 0.18 * abs(x - LARGURA_X / 2) / (LARGURA_X / 2)
        )
        h = max(0.08, h + rng.normal(0, 0.04))
        registros.append(dict(borehole=f"S{i:02d}", x=x, y=y, h_local=h))
    return pd.DataFrame(registros)


def krigar(df: pd.DataFrame, nx: int = 80, ny: int = 100):
    pts = df.groupby("borehole").agg(
        x=("x", "mean"), y=("y", "mean"), h=("h_local", "mean")
    ).reset_index()
    gx = np.linspace(0, LARGURA_X, nx)
    gy = np.linspace(0, COMPRIMENTO_Y, ny)
    ok = OrdinaryKriging(
        pts["x"].values, pts["y"].values, pts["h"].values,
        variogram_model="spherical", verbose=False, enable_plotting=False,
    )
    z, _ = ok.execute("grid", gx, gy)
    return gx, gy, np.array(z), pts


def render_fig03(gx, gy, z, pts) -> None:
    GX, GY = np.meshgrid(gx, gy)
    Y_CORTE = COMPRIMENTO_Y - GY
    pts_y_corte = COMPRIMENTO_Y - pts["y"]
    Z_m = z

    fig = plt.figure(figsize=(14.8, 5.8))
    gs = fig.add_gridspec(1, 2, width_ratios=(1.05, 1.0), wspace=0.02,
                          left=0.055, right=0.975, top=0.92, bottom=0.14)

    # ---- (a) superficie 3D em planta obliqua (quase top-down) -------------
    ax1 = fig.add_subplot(gs[0, 0], projection="3d")
    surf = ax1.plot_surface(
        GX, Y_CORTE, Z_m, cmap="YlOrBr", linewidth=0,
        antialiased=True, alpha=0.94, rcount=70, ccount=70,
        edgecolor="none", shade=True, vmin=Z_m.min(), vmax=Z_m.max(),
    )
    # Isolinhas projetadas na parede dos x maximos (fundo da cena lateral)
    ax1.contour(
        GX, Y_CORTE, Z_m, zdir="x", offset=LARGURA_X,
        levels=np.arange(0.05, 0.55, 0.10), colors="0.40", linewidths=0.5, alpha=0.55,
    )
    # Pontos de sondagem
    ax1.scatter(
        pts["x"], pts_y_corte, pts["h"],
        c="k", s=30, depthshade=False, zorder=10, edgecolors="white",
        linewidths=0.7,
    )
    # Linha da palicada no fim do corte visual, apos o trecho a montante.
    ax1.plot([0, LARGURA_X], [COMPRIMENTO_Y, COMPRIMENTO_Y], [0, 0],
             color="saddlebrown", lw=6, solid_capstyle="butt", zorder=11)

    ax1.set_xlabel("transversal (m)", fontsize=11, labelpad=-2)
    ax1.set_ylabel("longitudinal (m)", fontsize=11, labelpad=2)
    ax1.set_zlabel("Espessura (m)", fontsize=11, labelpad=-2)
    ax1.set_xlim(0, LARGURA_X)
    ax1.set_ylim(0, COMPRIMENTO_Y)
    ax1.set_zlim(0, max(Z_m.max() * 1.08, 0.50))
    ax1.set_xticks([0, 2, 4])
    ax1.set_yticks([0, 2, 4, 6])
    ax1.set_zticks([0.0, 0.1, 0.2, 0.3, 0.4, 0.5])
    ax1.zaxis.set_major_formatter(plt.FuncFormatter(lambda v, _: f"{v:.1f}"))
    ax1.tick_params(axis="both", which="major", labelsize=10, pad=-1)
    ax1.zaxis.set_tick_params(labelsize=10, pad=-1)
    # Corte longitudinal calibrado: y_corte=6-y inverte apenas a leitura visual,
    # mantendo o deposito fisico acumulado junto da palicada. O azimute de -22
    # graus aumenta a contribuicao visual de x, mas preserva y como eixo longo.
    ax1.view_init(elev=18, azim=-22)
    ax1.set_box_aspect((1.15, 3.0, 1.05), zoom=1.42)
    ax1.set_title("(a) Superficie krigada — corte longitudinal", pad=10, fontsize=13)

    # ---- (b) mapa de isolinhas em planta pura -----------------------------
    ax2 = fig.add_subplot(gs[0, 1])
    cf = ax2.contourf(GX, GY, Z_m, levels=12, cmap="YlOrBr")
    cs = ax2.contour(GX, GY, Z_m, levels=8, colors="k", linewidths=0.5)
    ax2.clabel(cs, fontsize=7, fmt="%.2f")
    ax2.scatter(pts["x"], pts["y"], c="k", s=24, marker="x", linewidths=1.2)
    # Paliçada
    ax2.axhline(0, color="saddlebrown", lw=4)
    ax2.text(LARGURA_X / 2, 0.25, "Paliçada",
             ha="center", va="bottom", color="saddlebrown", fontsize=11,
             fontweight="bold",
             bbox=dict(boxstyle="round,pad=0.25", fc="white", ec="saddlebrown",
                       lw=0.6, alpha=0.92))
    # Seta de fluxo: a montante (y alto) escoa em direcao a palicada (y=0).
    ax2.annotate(
        "fluxo", xy=(LARGURA_X * 0.88, 4.0),
        xytext=(LARGURA_X * 0.88, 5.5),
        ha="center", va="center", fontsize=8, color="0.22",
        arrowprops=dict(arrowstyle="-|>", color="0.22", lw=1.2),
        bbox=dict(boxstyle="round,pad=0.3", fc="white", ec="0.55",
                  lw=0.5, alpha=0.88),
    )
    ax2.set_xlabel("transversal (m)", fontsize=11, labelpad=6)
    ax2.set_ylabel("longitudinal a montante (m)", fontsize=11, labelpad=6)
    ax2.tick_params(axis="both", labelsize=10)
    ax2.set_aspect("equal")
    ax2.set_xlim(0, LARGURA_X)
    ax2.set_ylim(-0.5, COMPRIMENTO_Y)
    ax2.set_title("(b) Mapa de isolinhas de espessura (m)", pad=10, fontsize=13)
    cb2 = fig.colorbar(cf, ax=ax2, shrink=0.82, pad=0.035, aspect=24,
                       fraction=0.045)
    cb2.set_label("Espessura (m)", fontsize=11, labelpad=7)
    cb2.ax.yaxis.set_label_position("right")
    cb2.ax.tick_params(labelsize=10)
    cb2.formatter = plt.FuncFormatter(lambda v, _: f"{v:.2f}")
    cb2.update_ticks()

    out = OUT / "03_superficie_krigada.png"
    fig.savefig(out, dpi=300, facecolor="white")
    plt.close(fig)
    print(f"      [OK] {out.name} renderizado")


def main() -> None:
    print("[fig03] Gerando sondagens sinteticas...")
    df = gerar_sondagens()
    print("[fig03] Krigando espessura...")
    gx, gy, z, pts = krigar(df)
    print("[fig03] Renderizando figura...")
    render_fig03(gx, gy, z, pts)


if __name__ == "__main__":
    main()
