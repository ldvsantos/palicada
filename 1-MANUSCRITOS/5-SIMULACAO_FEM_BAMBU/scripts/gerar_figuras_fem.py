"""
Figure generation for FEM bamboo check dam failure analysis.

Produces publication-quality figures from fem_palicada_bambu.py outputs:
  - Fig 1: Mesh schematic with internode zones (article methodology)
  - Fig 2: Spatial failure index map (heatmap over culm length × time)
  - Fig 3: Temporal evolution of max failure index per scenario
  - Fig 4: Failure mode competition (bending vs shear vs buckling)
  - Fig 5: Integrated panel — structural failure vs sediment saturation timeline

Author: Diego Vidal
Date: 2026-03-27
"""

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
from matplotlib.patches import FancyBboxPatch, Rectangle
from matplotlib.collections import PatchCollection
from pathlib import Path
import json

# Style
plt.rcParams.update({
    "font.family": "serif",
    "font.size": 11,
    "axes.labelsize": 12,
    "axes.titlesize": 13,
    "legend.fontsize": 9,
    "figure.dpi": 300,
    "savefig.dpi": 300,
    "savefig.bbox": "tight",
    "axes.spines.top": False,
    "axes.spines.right": False,
})

COLORS = {
    "optimistic": "#2196F3",
    "baseline": "#FF9800",
    "pessimistic": "#F44336",
    "shear": "#E91E63",
    "bending": "#3F51B5",
    "buckling": "#4CAF50",
    "sediment": "#8D6E63",
    "water": "#42A5F5",
    "vegetation": "#66BB6A",
    "node_zone": "#FFCDD2",
    "internode": "#E3F2FD",
}


def load_data(results_dir):
    results_dir = Path(results_dir)
    df_full = pd.read_csv(results_dir / "fem_results_full.csv")
    df_summary = pd.read_csv(results_dir / "fem_summary_failure.csv")
    with open(results_dir / "simulation_parameters.json") as f:
        params = json.load(f)
    return df_full, df_summary, params


# ============================================================
# FIGURE 1: Mesh schematic with internode zones
# ============================================================

def fig1_mesh_schematic(params, output_dir):
    """Schematic of FEM mesh showing internode and node zones."""
    fig, ax = plt.subplots(1, 1, figsize=(10, 3.5))

    L = params["geometry"]["L_culm_m"]
    D = params["geometry"]["D_ext_m"]
    n_inter = params["geometry"]["n_internode"]
    L_node = params["geometry"]["L_node_m"]
    L_internode = L / n_inter

    # Draw culm as rectangle
    y_base = 0
    culm_h = D * 3  # visual scaling

    x = 0
    for seg in range(n_inter):
        # Internode
        L_main = L_internode - L_node if seg < n_inter - 1 else L_internode
        rect = Rectangle((x, y_base), L_main, culm_h, linewidth=0.5,
                          edgecolor="gray", facecolor=COLORS["internode"], alpha=0.7)
        ax.add_patch(rect)
        # Element divisions
        n_elem_vis = 4
        for j in range(1, n_elem_vis):
            xx = x + j * L_main / n_elem_vis
            ax.plot([xx, xx], [y_base, y_base + culm_h], ":", color="gray", lw=0.5)
        x += L_main

        # Node zone
        if seg < n_inter - 1:
            rect_n = Rectangle((x, y_base), L_node, culm_h, linewidth=0.5,
                                edgecolor="gray", facecolor=COLORS["node_zone"], alpha=0.9)
            ax.add_patch(rect_n)
            ax.plot([x + L_node/2], [y_base + culm_h + 0.005], "v",
                    color=COLORS["shear"], markersize=6)
            x += L_node

    # Supports
    ax.plot([0], [y_base - 0.005], "^", color="k", markersize=12)
    ax.plot([L], [y_base - 0.005], "^", color="k", markersize=12)

    # Load arrows
    n_arrows = 15
    for i in range(n_arrows):
        xa = L * (i + 0.5) / n_arrows
        ax.annotate("", xy=(xa, y_base + culm_h),
                     xytext=(xa, y_base + culm_h + 0.04),
                     arrowprops=dict(arrowstyle="->", color=COLORS["water"], lw=1.2))

    # Labels
    ax.text(L/2, y_base + culm_h + 0.05, r"$q(t) = p_{sed}(t) + p_{hydro}(t)$",
            ha="center", fontsize=11, color=COLORS["water"])
    ax.text(L/2, y_base - 0.025, f"L = {L} m", ha="center", fontsize=10)

    # Legend patches
    from matplotlib.patches import Patch
    legend_elements = [
        Patch(facecolor=COLORS["internode"], edgecolor="gray", label="Região intermodal"),
        Patch(facecolor=COLORS["node_zone"], edgecolor="gray", label="Zona do nó (diafragma)"),
    ]
    ax.legend(handles=legend_elements, loc="upper right", frameon=True, fontsize=9)

    ax.set_xlim(-0.05, L + 0.05)
    ax.set_ylim(-0.05, y_base + culm_h + 0.08)
    ax.set_aspect("equal")
    ax.axis("off")
    ax.set_title("Discretização da tora de bambu em elementos finitos", pad=15)

    fig.savefig(output_dir / "Fig_1_malha_FEM.png")
    fig.savefig(output_dir / "Fig_1_malha_FEM.pdf")
    plt.close(fig)
    print("[Fig 1] Malha FEM salva.")


# ============================================================
# FIGURE 2: Spatial-temporal failure index heatmap
# ============================================================

def fig2_failure_heatmap(df, output_dir, segment="MED", hydro="P90"):
    """Heatmap of Tsai-Hill failure index: x-position (culm) vs time."""
    fig, axes = plt.subplots(1, 3, figsize=(14, 5), sharey=True)

    for ax, scen in zip(axes, ["optimistic", "baseline", "pessimistic"]):
        sub = df[(df["segment"] == segment) &
                 (df["hydro_scenario"] == hydro) &
                 (df["degradation_scenario"] == scen)]

        pivot = sub.pivot_table(index="time_yr", columns="x_mid_m",
                                values="failure_index", aggfunc="mean")

        X = pivot.columns.values
        Y = pivot.index.values
        Z = pivot.values

        # Custom colormap: green -> yellow -> red
        cmap = mcolors.LinearSegmentedColormap.from_list(
            "safe_fail", ["#4CAF50", "#FFEB3B", "#FF9800", "#F44336", "#B71C1C"])
        norm = mcolors.Normalize(vmin=0, vmax=max(1.5, Z.max()))

        im = ax.pcolormesh(X, Y, Z, cmap=cmap, norm=norm, shading="nearest")

        # Mark FI=1.0 contour
        try:
            cs = ax.contour(X, Y, Z, levels=[1.0], colors=["white"], linewidths=2, linestyles="--")
            ax.clabel(cs, fmt="FI=1.0", fontsize=8, colors="white")
        except Exception:
            pass

        # Mark node zones
        node_x = sub[sub["is_node_zone"]]["x_mid_m"].unique()
        for nx in node_x:
            ax.axvline(nx, color="white", lw=0.5, alpha=0.4)

        k_label = {"optimistic": "k=0,03", "baseline": "k=0,06", "pessimistic": "k=0,10"}
        ax.set_title(f"Cenário {scen}\n({k_label[scen]} ano$^{{-1}}$)", fontsize=11)
        ax.set_xlabel("Posição na tora (m)")

    axes[0].set_ylabel("Tempo (anos)")

    fig.subplots_adjust(right=0.88)
    cbar_ax = fig.add_axes([0.90, 0.15, 0.02, 0.70])
    fig.colorbar(im, cax=cbar_ax, label="Índice de Tsai-Hill")

    fig.suptitle(f"Mapa de vulnerabilidade estrutural — Segmento {segment}, cenário {hydro}",
                 fontsize=13, y=1.02)

    fig.savefig(output_dir / "Fig_2_heatmap_falha.png")
    fig.savefig(output_dir / "Fig_2_heatmap_falha.pdf")
    plt.close(fig)
    print("[Fig 2] Heatmap de falha salvo.")


# ============================================================
# FIGURE 3: Temporal evolution of max failure index
# ============================================================

def fig3_failure_evolution(df, output_dir, segment="MED"):
    """Max failure index over time, per scenario and hydrological condition."""
    fig, axes = plt.subplots(1, 3, figsize=(14, 4.5), sharey=True)

    for ax, hydro in zip(axes, ["median", "P90", "P95"]):
        for scen in ["optimistic", "baseline", "pessimistic"]:
            sub = df[(df["segment"] == segment) &
                     (df["hydro_scenario"] == hydro) &
                     (df["degradation_scenario"] == scen)]
            max_fi = sub.groupby("time_yr")["failure_index"].max()
            ax.plot(max_fi.index, max_fi.values, "-o", color=COLORS[scen],
                    markersize=3, label=scen, lw=1.5)

        ax.axhline(1.0, color="red", ls="--", lw=1, alpha=0.7, label="Limiar de falha")
        ax.set_xlabel("Tempo (anos)")
        ax.set_title(f"Cenário hidrológico: {hydro}", fontsize=11)
        ax.set_xlim(0, 10)
        ax.grid(True, alpha=0.3)

    axes[0].set_ylabel("Índice de Tsai-Hill (máximo)")
    axes[0].legend(loc="upper left", fontsize=8, frameon=True)

    fig.suptitle(f"Evolução temporal do índice de falha — Segmento {segment}", fontsize=13, y=1.02)
    fig.tight_layout()
    fig.savefig(output_dir / "Fig_3_evolucao_falha.png")
    fig.savefig(output_dir / "Fig_3_evolucao_falha.pdf")
    plt.close(fig)
    print("[Fig 3] Evolução temporal salva.")


# ============================================================
# FIGURE 4: Failure mode competition (stacked area)
# ============================================================

def fig4_failure_modes(df, output_dir, segment="MED", hydro="P90"):
    """Contribution of bending vs shear to total failure index over time."""
    fig, axes = plt.subplots(1, 3, figsize=(14, 4.5), sharey=True)

    for ax, scen in zip(axes, ["optimistic", "baseline", "pessimistic"]):
        sub = df[(df["segment"] == segment) &
                 (df["hydro_scenario"] == hydro) &
                 (df["degradation_scenario"] == scen)]

        # For each time step, count fraction of elements dominated by each mode
        mode_counts = sub.groupby(["time_yr", "failure_mode"]).size().unstack(fill_value=0)
        mode_frac = mode_counts.div(mode_counts.sum(axis=1), axis=0)

        times = mode_frac.index.values
        bending_frac = mode_frac.get("bending", pd.Series(0, index=times)).values
        shear_frac = mode_frac.get("shear", pd.Series(0, index=times)).values

        ax.fill_between(times, 0, bending_frac, alpha=0.6, color=COLORS["bending"], label="Flexão")
        ax.fill_between(times, bending_frac, bending_frac + shear_frac, alpha=0.6,
                         color=COLORS["shear"], label="Cisalhamento")

        # Overlay: max FI on secondary axis
        ax2 = ax.twinx()
        max_fi = sub.groupby("time_yr")["failure_index"].max()
        ax2.plot(max_fi.index, max_fi.values, "k-", lw=1.5, alpha=0.7, label="FI máx.")
        ax2.axhline(1.0, color="red", ls=":", lw=0.8)
        if ax == axes[-1]:
            ax2.set_ylabel("Índice de Tsai-Hill")
        ax2.set_ylim(0, max(2, max_fi.max() * 1.1))

        k_label = {"optimistic": "k=0,03", "baseline": "k=0,06", "pessimistic": "k=0,10"}
        ax.set_title(f"{scen} ({k_label[scen]})", fontsize=11)
        ax.set_xlabel("Tempo (anos)")
        ax.set_ylim(0, 1.05)

    axes[0].set_ylabel("Fração de elementos por modo")
    axes[0].legend(loc="upper left", fontsize=8)

    fig.suptitle(f"Competição de modos de falha — Segmento {segment}, {hydro}", fontsize=13, y=1.02)
    fig.tight_layout()
    fig.savefig(output_dir / "Fig_4_modos_falha.png")
    fig.savefig(output_dir / "Fig_4_modos_falha.pdf")
    plt.close(fig)
    print("[Fig 4] Modos de falha salvo.")


# ============================================================
# FIGURE 5: Safety factor evolution over time
# ============================================================

def fig5_safety_factor(output_dir):
    """Safety factor vs time for each segment/hydro, pessimistic degradation."""
    results_dir = output_dir.parent / "resultados"
    df_sf = pd.read_csv(results_dir / "safety_factor_evolution.csv")

    fig, axes = plt.subplots(1, 3, figsize=(14, 5), sharey=True)
    segments_order = ["SUP", "MED", "INF"]
    hydro_colors = {"median": "#66BB6A", "P90": "#FF9800", "P95": "#F44336"}

    for ax, seg in zip(axes, segments_order):
        for hydro_name, color in hydro_colors.items():
            for scen in ["optimistic", "baseline", "pessimistic"]:
                sub = df_sf[(df_sf["segment"] == seg) &
                            (df_sf["hydro_scenario"] == hydro_name) &
                            (df_sf["degradation_scenario"] == scen)]
                ls = {"optimistic": ":", "baseline": "-", "pessimistic": "--"}[scen]
                lw = 1.5 if scen == "baseline" else 1.0
                label = f"{hydro_name}, {scen}" if seg == "SUP" else ""
                sf_vals = sub["safety_factor"].clip(upper=500)
                ax.plot(sub["time_yr"], sf_vals, ls=ls, color=color, lw=lw, label=label)

        ax.axhline(1.0, color="red", ls="-", lw=2, alpha=0.5, label="Limiar de falha" if seg == "SUP" else "")
        ax.set_xlabel("Tempo (anos)")
        seg_h = {'SUP': 50, 'MED': 76, 'INF': 36}[seg]
        ax.set_title(f"Segmento {seg} (H = {seg_h} cm)", fontsize=11)
        ax.set_yscale("log")
        ax.set_ylim(1, 1500)
        ax.grid(True, alpha=0.3, which="both")

    axes[0].set_ylabel("Fator de segurança (1/FI)")
    axes[0].legend(loc="upper right", fontsize=6, frameon=True, ncol=1)

    fig.suptitle("Evolução do fator de segurança estrutural por segmento e cenário", fontsize=13, y=1.02)
    fig.tight_layout()
    fig.savefig(output_dir / "Fig_5_fator_seguranca.png")
    fig.savefig(output_dir / "Fig_5_fator_seguranca.pdf")
    plt.close(fig)
    print("[Fig 5] Fator de segurança salvo.")


# ============================================================
# FIGURE 7: Sensitivity heatmap — span × velocity
# ============================================================

def fig7_sensitivity_heatmap(output_dir):
    """Heatmap of max FI for span × velocity, at selected time steps."""
    results_dir = output_dir.parent / "resultados"
    df = pd.read_csv(results_dir / "sensitivity_span_velocity.csv")

    fig, axes = plt.subplots(1, 3, figsize=(14, 5))
    time_steps = [0, 5, 10]
    cmap = mcolors.LinearSegmentedColormap.from_list(
        "safe_fail", ["#4CAF50", "#FFEB3B", "#FF9800", "#F44336", "#B71C1C"])

    for ax, t_yr in zip(axes, time_steps):
        sub = df[df["time_yr"] == t_yr]
        pivot = sub.pivot_table(index="v_flow_ms", columns="span_m",
                                values="max_FI", aggfunc="max")
        X = pivot.columns.values
        Y = pivot.index.values
        Z = pivot.values

        vmax = max(1.5, Z.max())
        norm = mcolors.Normalize(vmin=0, vmax=vmax)
        im = ax.pcolormesh(X, Y, Z, cmap=cmap, norm=norm, shading="nearest")

        try:
            cs = ax.contour(X, Y, Z, levels=[1.0], colors=["white"], linewidths=2, linestyles="--")
            ax.clabel(cs, fmt="FI=1.0", fontsize=8, colors="white")
        except Exception:
            pass

        # Mark current configuration
        ax.plot(1.5, 2.0, "w*", markersize=15, markeredgecolor="k", markeredgewidth=1.0)

        ax.set_xlabel("Vão da tora (m)")
        ax.set_title(f"t = {t_yr} anos", fontsize=11)

    axes[0].set_ylabel("Velocidade do escoamento (m/s)")

    fig.subplots_adjust(right=0.88)
    cbar_ax = fig.add_axes([0.90, 0.15, 0.02, 0.70])
    fig.colorbar(im, cax=cbar_ax, label="Índice de Tsai-Hill (máximo)")

    fig.suptitle("Análise de sensibilidade — Vão × Velocidade (cenário baseline, segmento MED)",
                 fontsize=13, y=1.02)
    fig.savefig(output_dir / "Fig_7_sensibilidade_vao_vel.png")
    fig.savefig(output_dir / "Fig_7_sensibilidade_vao_vel.pdf")
    plt.close(fig)
    print("[Fig 7] Sensibilidade vão × velocidade salva.")


# ============================================================
# FIGURE 8: Critical span for failure as function of time
# ============================================================

def fig8_critical_span(output_dir):
    """Critical span length (FI=1.0) as function of time for various velocities."""
    results_dir = output_dir.parent / "resultados"
    df = pd.read_csv(results_dir / "sensitivity_span_velocity.csv")

    fig, ax = plt.subplots(figsize=(8, 5))
    vel_targets = [2.0, 3.0, 4.0, 5.0, 6.0]
    cmap = plt.cm.RdYlBu_r

    for j, v in enumerate(vel_targets):
        sub = df[df["v_flow_ms"] == v]
        times = sorted(sub["time_yr"].unique())
        crit_spans = []
        for t in times:
            tt = sub[sub["time_yr"] == t].sort_values("span_m")
            # Find span where FI crosses 1.0 (linear interpolation)
            spans = tt["span_m"].values
            fis = tt["max_FI"].values
            cross = np.where(fis >= 1.0)[0]
            if len(cross) > 0:
                idx = cross[0]
                if idx > 0:
                    # Linear interpolation
                    s0, s1 = spans[idx-1], spans[idx]
                    f0, f1 = fis[idx-1], fis[idx]
                    if f1 != f0:
                        s_crit = s0 + (1.0 - f0) * (s1 - s0) / (f1 - f0)
                    else:
                        s_crit = s0
                else:
                    s_crit = spans[0]
                crit_spans.append((t, s_crit))

        if crit_spans:
            ts, ss = zip(*crit_spans)
            color = cmap(j / (len(vel_targets) - 1))
            ax.plot(ts, ss, "o-", color=color, lw=1.5, markersize=5,
                    label=f"v = {v:.1f} m/s")

    ax.axhline(1.5, color="gray", ls="--", lw=1, alpha=0.7, label="Vão atual (1,5 m)")
    ax.set_xlabel("Tempo (anos)")
    ax.set_ylabel("Vão crítico para falha (m)")
    ax.set_title("Vão crítico (FI = 1,0) em função do tempo e velocidade de escoamento", fontsize=12)
    ax.legend(loc="upper right", fontsize=9)
    ax.grid(True, alpha=0.3)
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 7)

    fig.tight_layout()
    fig.savefig(output_dir / "Fig_8_vao_critico.png")
    fig.savefig(output_dir / "Fig_8_vao_critico.pdf")
    plt.close(fig)
    print("[Fig 8] Vão crítico salvo.")


# ============================================================
# FIGURE 6: Deflection profile along culm
# ============================================================

def fig6_deflection_profiles(df, output_dir, segment="MED", hydro="P90"):
    """Deflection profiles along the culm at selected time steps."""
    fig, axes = plt.subplots(1, 3, figsize=(14, 4.5), sharey=True)
    time_snapshots = [0, 2, 5, 8, 10]
    cmap_t = plt.cm.viridis

    for ax, scen in zip(axes, ["optimistic", "baseline", "pessimistic"]):
        sub = df[(df["segment"] == segment) &
                 (df["hydro_scenario"] == hydro) &
                 (df["degradation_scenario"] == scen)]

        for j, t in enumerate(time_snapshots):
            t_sub = sub[sub["time_yr"] == t].sort_values("x_mid_m")
            if len(t_sub) == 0:
                continue
            color = cmap_t(j / (len(time_snapshots) - 1))
            ax.plot(t_sub["x_mid_m"], t_sub["deflection_mm"], "-", color=color,
                    lw=1.5, label=f"t = {t} anos")

        # Mark node zones
        node_x = sub[sub["is_node_zone"]]["x_mid_m"].unique()
        for nx in node_x:
            ax.axvline(nx, color=COLORS["node_zone"], lw=3, alpha=0.3)

        k_label = {"optimistic": "k=0,03", "baseline": "k=0,06", "pessimistic": "k=0,10"}
        ax.set_title(f"{scen} ({k_label[scen]})", fontsize=11)
        ax.set_xlabel("Posição na tora (m)")
        ax.grid(True, alpha=0.3)

    axes[0].set_ylabel("Deflexão (mm)")
    axes[0].legend(loc="lower right", fontsize=8)

    fig.suptitle(f"Perfil de deflexão da tora — Segmento {segment}, {hydro}", fontsize=13, y=1.02)
    fig.tight_layout()
    fig.savefig(output_dir / "Fig_6_deflexao.png")
    fig.savefig(output_dir / "Fig_6_deflexao.pdf")
    plt.close(fig)
    print("[Fig 6] Perfis de deflexão salvos.")


# ============================================================
# ENTRY POINT
# ============================================================

def main():
    base = Path(__file__).parent.parent
    results_dir = base / "resultados"
    figures_dir = base / "figuras"
    figures_dir.mkdir(parents=True, exist_ok=True)

    df_full, df_summary, params = load_data(results_dir)

    fig1_mesh_schematic(params, figures_dir)
    fig2_failure_heatmap(df_full, figures_dir, segment="MED", hydro="P90")
    fig3_failure_evolution(df_full, figures_dir, segment="MED")
    fig4_failure_modes(df_full, figures_dir, segment="MED", hydro="P90")
    fig5_safety_factor(figures_dir)
    fig6_deflection_profiles(df_full, figures_dir, segment="MED", hydro="P90")
    fig7_sensitivity_heatmap(figures_dir)
    fig8_critical_span(figures_dir)

    print("\n[OK] Todas as figuras geradas em:", figures_dir)


if __name__ == "__main__":
    main()
