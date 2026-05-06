"""
Simulação 06 -- Âncora Empírica: Talude LIMPO (solo descoberto) x PEDRA (paliçadas baixas)
========================================================================================

Integra os dados reais de 15 coletas de sedimento do talude experimental
(Plintossolo Háplico, 22 deg, rampa 2,40 x 0,50 m) ao artigo ECZ como âncora
empírica que complementa os 5 testes computacionais.

Tratamentos:
  - LIMPO  = solo descoberto (controle Wischmeier reduzido, C=P=1)
  - PEDRA  = paliçadas baixas (~20 cm, barreira permeável fixa)

Gera 3 figuras + 1 tabela para o manuscrito:
  Fig. 09 -- Bracketing triplo de delta (campo x sintético x modelo)
  Fig. 10 -- Razão LIMPO/PEDRA vs intensidade de chuva (eficiência das paliçadas)
  Fig. 11 -- Sedimento acumulado + precipitação acumulada ao longo da estação
  Tabela -- Comparativo sintético vs campo (delta, K_obs, C.P empírico)
"""

from __future__ import annotations

import sys
from pathlib import Path

# Aponta para o diretório de scripts do ECZ para importar config_simulacao
_SCRIPT_DIR = Path(__file__).resolve().parent
_ECZ_SCRIPTS = Path(
    r"c:\Users\vidal\OneDrive\Documentos\13 - CLONEGIT\artigo-posdoc\3-EROSIBIDADE"
    r"\1-MANUSCRITOS\8-SIMULACAO_K_PLINTOSSOLO\scripts"
)
sys.path.insert(0, str(_ECZ_SCRIPTS))

import pandas as pd
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import math

from config_simulacao import (
    PLINTOSSOLO, LATOSSOLO, ARGISSOLO, SOLOS, K_RUSLE,
    TRUE_PARAMS, delta_model, alpha, beta, gamma,
    VIB_REF, FIG_DIR, DISPLAY_NAME, calc_Hc,
)

# ── Diretórios ──────────────────────────────────────────────────────
BASE_DADOS = Path(
    r"c:\Users\vidal\OneDrive\Documentos\13 - CLONEGIT\artigo-posdoc\3-EROSIBIDADE\2-DADOS"
)
FIG_DIR_ECZ = _ECZ_SCRIPTS.parent / "figuras"
FIG_DIR_ECZ.mkdir(exist_ok=True)

# ── Parâmetros do talude (confirmados em campo) ─────────────────────
LAMBDA_M = 2.40
LARGURA_M = 0.50
A_PARC_M2 = LAMBDA_M * LARGURA_M  # 1.20 m²
INCLIN_GRAUS = 22.0
sin_t = math.sin(math.radians(INCLIN_GRAUS))
S_factor = 16.8 * sin_t - 0.50
L_factor = (LAMBDA_M / 22.13) ** 0.5
LS_TALUDE = L_factor * S_factor  # ~ 1.91

# ── Tratamentos (terminologia de campo) ─────────────────────────────
# LIMPO = solo descoberto (bare soil, C=P=1)
# PEDRA = paliçadas baixas (~20 cm, barreira permeável fixa)
TRAT_LABEL = {"LIMPO": "Bare soil (LIMPO)", "PEDRA": "Low palisades (PEDRA)"}
TRAT_COLOR = {"LIMPO": "#C0392B", "PEDRA": "#27AE60"}
TRAT_MARKER = {"LIMPO": "o", "PEDRA": "s"}

# ── Parâmetros do modelo K_plint para referência ────────────────────
TRUE = TRUE_PARAMS
VIB_PLINT_MED = np.mean(list(PLINTOSSOLO["VIB"].values()))  # ~ 2.08 cm/h
M_AL_PLINT_BAc = PLINTOSSOLO["m_Al"]["BAc"]  # 99.2%
H_HC_PLINT_MED = np.mean([f["H_Hc"] for f in PLINTOSSOLO["feicoes"].values()])  # ~ 0.28

DELTA_MOD = float(
    delta_model(VIB_PLINT_MED, M_AL_PLINT_BAc, H_HC_PLINT_MED, **TRUE)
)
DELTA_OBS_SINTETICO = 2.71  # do Test 5 (I30 >= 40 mm/h)


# ══════════════════════════════════════════════════════════════════════
# 1. CARREGAR DADOS DO TALUDE
# ══════════════════════════════════════════════════════════════════════
sed = pd.read_csv(BASE_DADOS / "Sedimentos_talude_LIMPO_PEDRA_dados_longos.csv")
sed["data"] = pd.to_datetime(sed["data"])

ppt = pd.read_csv(
    BASE_DADOS / "CLIMATOLOGIA_20ANOS" / "dados" / "serie_precipitacao_20anos.csv"
)
ppt["Data"] = pd.to_datetime(ppt["Data"])
ppt = ppt.sort_values("Data").reset_index(drop=True)

inicio_exp = pd.Timestamp("2025-04-01")
fim_exp = pd.Timestamp("2025-11-30")
ppt_exp = ppt[(ppt["Data"] >= inicio_exp) & (ppt["Data"] <= fim_exp)].copy()

# Pareamento chuva entre coletas
datas_coleta = sorted(sed["data"].unique())
intervalos = []
data_anterior = inicio_exp
for d in datas_coleta:
    mask = (ppt_exp["Data"] > data_anterior) & (ppt_exp["Data"] <= pd.Timestamp(d))
    p_int = ppt_exp.loc[mask, "Precipitacao_mm"].sum()
    n_dias = (pd.Timestamp(d) - data_anterior).days
    p_max_dia = ppt_exp.loc[mask, "Precipitacao_mm"].max()
    intervalos.append({
        "data_coleta": d,
        "n_dias_intervalo": n_dias,
        "P_intervalo_mm": float(p_int),
        "P_max_dia_mm": float(p_max_dia) if pd.notna(p_max_dia) else 0.0,
    })
    data_anterior = pd.Timestamp(d)

intervalos_df = pd.DataFrame(intervalos)

# Agregação por tratamento x coleta
agreg = (
    sed.groupby(["data", "tratamento"])
    .agg(
        sedimento_medio_g=("sedimento_g", "mean"),
        sedimento_total_g=("sedimento_g", "sum"),
        n_parcelas=("codigo_parcela", "nunique"),
        cv_pct=(
            "sedimento_g",
            lambda x: 100 * x.std(ddof=1) / x.mean() if len(x) > 1 else np.nan,
        ),
    )
    .reset_index()
)

pivot_med = (
    agreg.pivot(index="data", columns="tratamento", values="sedimento_medio_g")
    .reset_index()
)
pivot_med.columns.name = None
pivot_med = pivot_med.rename(
    columns={"LIMPO": "med_LIMPO_g", "PEDRA": "med_PEDRA_g"}
)
pivot_med["data"] = pd.to_datetime(pivot_med["data"])

intervalos_df["data_coleta"] = pd.to_datetime(intervalos_df["data_coleta"])
tabela = intervalos_df.merge(
    pivot_med, left_on="data_coleta", right_on="data"
).drop(columns=["data"])
tabela["razao_LIMPO_PEDRA"] = tabela["med_LIMPO_g"] / tabela["med_PEDRA_g"]

# Totais acumulados
A_total_LIMPO = (
    sed[sed["tratamento"] == "LIMPO"]
    .groupby("codigo_parcela")["sedimento_g"]
    .sum()
    .mean()
)
A_total_PEDRA = (
    sed[sed["tratamento"] == "PEDRA"]
    .groupby("codigo_parcela")["sedimento_g"]
    .sum()
    .mean()
)
conv = 0.01 / A_PARC_M2
A_LIMPO_t_ha = A_total_LIMPO * conv
A_PEDRA_t_ha = A_total_PEDRA * conv

# EI30 e R
ei30 = pd.read_csv(
    BASE_DADOS / "CLIMATOLOGIA_20ANOS" / "dados" / "ei30_anual.csv"
)
ei30["ano"] = pd.to_datetime(ei30["Data"]).dt.year
R_anual_med = ei30[(ei30["ano"] >= 2006) & (ei30["ano"] <= 2024)][
    "precipitacao"
].mean()
P_anual_med = ppt.groupby("Ano")["Precipitacao_mm"].sum().mean()
P_total_exp = tabela["P_intervalo_mm"].sum()
R_exp_estim = R_anual_med * (P_total_exp / P_anual_med)

K_obs_LIMPO = A_LIMPO_t_ha / (R_exp_estim * LS_TALUDE * 1.0 * 1.0)
DELTA_FIELD = K_obs_LIMPO / K_RUSLE["plintossolo"]

# C.P empírico das paliçadas baixas
CP_EMPIRICO = A_PEDRA_t_ha / A_LIMPO_t_ha  # ~ 0.43

# Sedimento acumulado ao longo do tempo
sed_acum = (
    sed.groupby(["data", "tratamento"])["sedimento_g"]
    .mean()
    .groupby(level="tratamento")
    .cumsum()
    .reset_index()
)
sed_acum.columns = ["data", "tratamento", "sed_acum_g"]
sed_acum["data"] = pd.to_datetime(sed_acum["data"])

# Precipitação acumulada
ppt_acum = ppt_exp.set_index("Data")["Precipitacao_mm"].cumsum().reset_index()
ppt_acum.columns = ["data", "P_acum_mm"]


# ══════════════════════════════════════════════════════════════════════
# 2. FIGURA 09 -- BRACKETING TRIPLO DE delta
# ══════════════════════════════════════════════════════════════════════
def fig_09_bracketing_delta():
    """Painel triplo: delta_field (talude) x delta_obs (Test 5 sintético) x delta_mod (K_plint)."""
    fig, axes = plt.subplots(1, 3, figsize=(16, 5.5))

    # ── (a) delta_field por coleta ──
    ax = axes[0]
    # K_obs por coleta (aproximado)
    k_obs_por_coleta = []
    for _, row in tabela.iterrows():
        if row["P_intervalo_mm"] > 0:
            r_frac = R_anual_med * (row["P_intervalo_mm"] / P_anual_med)
            a_limpo = row["med_LIMPO_g"] * conv
            k = a_limpo / (r_frac * LS_TALUDE)
        else:
            k = np.nan
        k_obs_por_coleta.append(k)
    delta_por_coleta = np.array(k_obs_por_coleta) / K_RUSLE["plintossolo"]

    datas = tabela["data_coleta"]
    valid = ~np.isnan(delta_por_coleta)
    ax.bar(
        datas[valid],
        delta_por_coleta[valid],
        width=4,
        color="#E67E22",
        alpha=0.75,
        label=r"$\delta_{\mathrm{field}}$ (bare soil, 2.40 m ramp)",
    )
    ax.axhline(
        DELTA_FIELD,
        color="#E67E22",
        ls="--",
        lw=1.5,
        label=f"Mean delta_field = {DELTA_FIELD:.3f}",
    )
    ax.axhline(1.0, color="k", ls=":", lw=0.8, label=r"$\delta = 1$ (nomograph)")
    ax.set_ylabel(r"$\delta = K_{\mathrm{obs}} / K_{\mathrm{RUSLE}}$")
    ax.set_xlabel("Collection date")
    ax.set_title(
        "Empirical anchor\n(bare soil, short ramp, no runoff gauging)",
        fontsize=11,
    )
    ax.tick_params(axis="x", rotation=30)
    ax.legend(fontsize=7.5, loc="upper left")
    ax.text(-0.05, 1.12, "(a)", transform=ax.transAxes, fontsize=14, fontweight="bold")

    # ── (b) delta_obs sintético (Test 5) ──
    ax = axes[1]
    i30_vals = [30, 40, 50, 60, 75, 90, 100]
    delta_sint = [0.0, 1.80, 2.30, 2.71, 3.10, 3.50, 3.80]
    ax.plot(
        i30_vals,
        delta_sint,
        "s-",
        color="#8E44AD",
        lw=2,
        markersize=8,
        label=r"$\delta_{\mathrm{obs}}$ (WEPP-type, Test 5)",
    )
    ax.axhline(
        DELTA_OBS_SINTETICO,
        color="#8E44AD",
        ls="--",
        lw=1.5,
        label=f"Mean delta_obs = {DELTA_OBS_SINTETICO:.2f}",
    )
    ax.axhline(1.0, color="k", ls=":", lw=0.8)
    ax.set_ylabel(r"$\delta = K_{\mathrm{obs}} / K_{\mathrm{RUSLE}}$")
    ax.set_xlabel(r"$I_{30}$ (mm/h)")
    ax.set_title(
        "Synthetic erosion (Test 5)\n(WEPP-type detachment, 22.13 m plot)",
        fontsize=11,
    )
    ax.legend(fontsize=7.5, loc="upper left")
    ax.text(-0.05, 1.12, "(b)", transform=ax.transAxes, fontsize=14, fontweight="bold")

    # ── (c) Bracketing completo ──
    ax = axes[2]
    categorias = [
        "Field\n(short ramp,\nbare soil)",
        "Synthetic\n(WEPP-type,\n22.13 m plot)",
        "Model\n(K_plint,\nuncalibrated)",
    ]
    valores = [DELTA_FIELD, DELTA_OBS_SINTETICO, DELTA_MOD]
    cores = ["#E67E22", "#8E44AD", "#2C3E50"]
    bars = ax.bar(categorias, valores, color=cores, alpha=0.8, width=0.5)
    ax.axhline(1.0, color="k", ls=":", lw=0.8, label=r"$\delta = 1$ (nomograph)")

    # Anotar valores
    for bar, val in zip(bars, valores):
        ax.text(
            bar.get_x() + bar.get_width() / 2,
            bar.get_height() + 0.15,
            f"{val:.2f}",
            ha="center",
            va="bottom",
            fontweight="bold",
            fontsize=11,
        )

    # Zona de calibração Wischmeier
    ax.axhspan(0.5, 4.0, alpha=0.08, color="green")
    ax.text(
        1.0,
        2.2,
        "Target calibration\nzone (Wischmeier\ninstrumentation)",
        ha="center",
        fontsize=8,
        color="green",
        fontstyle="italic",
    )

    ax.set_ylabel(r"$\delta = K_{\mathrm{obs}} / K_{\mathrm{RUSLE}}$")
    ax.set_title(
        "Triple bracketing of delta\n(field anchor ↔ synthetic ↔ model)",
        fontsize=11,
    )
    ax.legend(fontsize=7.5, loc="upper left")
    ax.text(-0.05, 1.12, "(c)", transform=ax.transAxes, fontsize=14, fontweight="bold")

    fig.suptitle(
        "Convergence of empirical and computational delta estimates\n"
        "toward the Wischmeier calibration target",
        fontsize=13,
        fontweight="bold",
    )
    fig.tight_layout()
    path = FIG_DIR_ECZ / "fig_09_bracketing_delta.png"
    fig.savefig(path, dpi=180, bbox_inches="tight")
    plt.close(fig)
    print(f"  [OK] Fig. 09 → {path.name}")


# ══════════════════════════════════════════════════════════════════════
# 3. FIGURA 10 -- EFICIÊNCIA DAS PALIÇADAS BAIXAS vs INTENSIDADE
# ══════════════════════════════════════════════════════════════════════
def fig_10_eficiencia_palicadas():
    """Razão LIMPO/PEDRA e C.P empírico em função de P_max_dia (proxy de I30)."""
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5.5))

    # ── (a) Razão LIMPO/PEDRA vs P_max ──
    ax1.scatter(
        tabela["P_max_dia_mm"],
        tabela["razao_LIMPO_PEDRA"],
        c=tabela["P_intervalo_mm"],
        cmap="YlOrRd",
        s=120,
        edgecolors="k",
        linewidths=0.5,
        zorder=3,
    )
    ax1.axhline(1.0, color="k", ls="--", lw=0.8, label="No reduction (ratio = 1)")
    ax1.axhline(
        2.34,
        color="#C0392B",
        ls="--",
        lw=1.2,
        label=f"Mean ratio = 2.34",
    )
    ax1.set_xlabel("Maximum daily rainfall in interval, $P_{\\mathrm{max}}$ (mm)")
    ax1.set_ylabel("LIMPO / PEDRA sediment ratio")
    ax1.set_title(
        "Efficiency of low palisades (PEDRA) vs bare soil (LIMPO)\n"
        "as a function of rainfall intensity proxy",
        fontsize=11,
    )
    ax1.legend(fontsize=8)
    ax1.grid(True, alpha=0.3)
    cbar = plt.colorbar(
        ax1.collections[0], ax=ax1, label="Cumulative rainfall\nin interval (mm)"
    )
    ax1.text(-0.05, 1.12, "(a)", transform=ax1.transAxes, fontsize=14, fontweight="bold")

    # ── (b) C.P empírico por coleta ──
    cp_por_coleta = 1.0 / tabela["razao_LIMPO_PEDRA"]
    ax2.bar(
        tabela["data_coleta"],
        cp_por_coleta,
        width=4,
        color="#27AE60",
        alpha=0.7,
        label=r"Empirical $C \cdot P$ (PEDRA / LIMPO)",
    )
    ax2.axhline(
        CP_EMPIRICO,
        color="#1E8449",
        ls="--",
        lw=1.5,
        label=f"Mean C.P = {CP_EMPIRICO:.3f}",
    )
    ax2.axhline(1.0, color="k", ls=":", lw=0.8, label="C.P = 1 (bare soil)")
    ax2.set_ylabel(r"Empirical $C \cdot P$ factor")
    ax2.set_xlabel("Collection date")
    ax2.set_title(
        "Cover-management factor of low palisades\n"
        "(inferred from sediment reduction ratio)",
        fontsize=11,
    )
    ax2.tick_params(axis="x", rotation=30)
    ax2.legend(fontsize=8)
    ax2.set_ylim(0, 1.1)
    ax2.text(-0.05, 1.12, "(b)", transform=ax2.transAxes, fontsize=14, fontweight="bold")

    fig.suptitle(
        "Hydrosedimentological performance of low palisades\n"
        "on a 22 deg Plinthosol slope (Coastal Tablelands, Sergipe)",
        fontsize=13,
        fontweight="bold",
    )
    fig.tight_layout()
    path = FIG_DIR_ECZ / "fig_10_eficiencia_palicadas.png"
    fig.savefig(path, dpi=180, bbox_inches="tight")
    plt.close(fig)
    print(f"  [OK] Fig. 10 → {path.name}")


# ══════════════════════════════════════════════════════════════════════
# 4. FIGURA 11 -- SEDIMENTO ACUMULADO + PRECIPITAÇÃO ACUMULADA
# ══════════════════════════════════════════════════════════════════════
def fig_11_acumulado():
    """Sedimento acumulado LIMPO vs PEDRA + precipitação acumulada."""
    fig, ax1 = plt.subplots(figsize=(12, 5.5))
    ax2 = ax1.twinx()

    # Precipitação acumulada (área)
    ax2.fill_between(
        ppt_acum["data"],
        ppt_acum["P_acum_mm"],
        alpha=0.12,
        color="#4F9DDE",
        label="Cumulative rainfall (mm)",
    )
    ax2.plot(
        ppt_acum["data"],
        ppt_acum["P_acum_mm"],
        color="#4F9DDE",
        lw=1.5,
        alpha=0.7,
    )
    ax2.set_ylabel("Cumulative rainfall (mm)", color="#2C5780")

    # Sedimento acumulado por tratamento
    for trt in ["LIMPO", "PEDRA"]:
        df = sed_acum[sed_acum["tratamento"] == trt]
        ax1.plot(
            df["data"],
            df["sed_acum_g"],
            marker=TRAT_MARKER[trt],
            color=TRAT_COLOR[trt],
            lw=2.2,
            markersize=7,
            label=TRAT_LABEL[trt],
        )

    # Anotar valores finais
    for trt, y, color in [
        ("LIMPO", A_total_LIMPO, TRAT_COLOR["LIMPO"]),
        ("PEDRA", A_total_PEDRA, TRAT_COLOR["PEDRA"]),
    ]:
        ax1.annotate(
            f"{y:.0f} g",
            xy=(sed_acum["data"].max(), y),
            xytext=(15, 0),
            textcoords="offset points",
            fontsize=9,
            fontweight="bold",
            color=color,
            va="center",
        )

    ax1.set_ylabel("Cumulative mean sediment per ramp (g)")
    ax1.set_xlabel("Date")
    ax1.set_title(
        "Cumulative sediment yield and rainfall\n"
        "Bare soil (LIMPO) vs low palisades (PEDRA) -- 22 deg Plinthosol slope",
        fontsize=12,
        fontweight="bold",
    )

    # Legenda combinada
    lines1, labels1 = ax1.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    ax1.legend(
        lines1 + lines2,
        labels1 + labels2,
        loc="upper left",
        fontsize=9,
    )
    ax1.tick_params(axis="x", rotation=30)
    ax1.grid(True, alpha=0.3)

    fig.tight_layout()
    path = FIG_DIR_ECZ / "fig_11_sedimento_acumulado.png"
    fig.savefig(path, dpi=180, bbox_inches="tight")
    plt.close(fig)
    print(f"  [OK] Fig. 11 → {path.name}")


# ══════════════════════════════════════════════════════════════════════
# 5. TABELA COMPARATIVA SINTÉTICO vs CAMPO
# ══════════════════════════════════════════════════════════════════════
def tabela_comparativa():
    """Gera tabela LaTeX para o manuscrito."""
    rows = [
        (r"$\delta$ (amplification factor)",
         f"{DELTA_FIELD:.3f}",
         f"{DELTA_OBS_SINTETICO:.2f}",
         f"{DELTA_MOD:.2f}"),
        (r"$K_{\mathrm{obs}}$ (t\,h\,MJ$^{-1}$\,mm$^{-1}$)",
         f"{K_obs_LIMPO:.4f}",
         "0.058--0.116",
         "--"),
        (r"$K_{\mathrm{RUSLE}}$ (t\,h\,MJ$^{-1}$\,mm$^{-1}$)",
         f"{K_RUSLE['plintossolo']:.3f}",
         f"{K_RUSLE['plintossolo']:.3f}",
         f"{K_RUSLE['plintossolo']:.3f}"),
        (r"$C \cdot P$ (cover-management)",
         f"{CP_EMPIRICO:.3f}",
         "1.0 (assumed)",
         "1.0 (assumed)"),
        ("Ramp / plot length (m)", f"{LAMBDA_M:.2f}", "22.13", "22.13"),
        (r"$LS$ factor", f"{LS_TALUDE:.2f}", "1.0 (standard)", "1.0 (standard)"),
        ("Runoff gauging", "No", "No (synthetic)", "No (synthetic)"),
        (r"$EI_{30}$ source", "Scaled by interval P", "Synthetic $I_{30}$", "Synthetic $I_{30}$"),
        ("Replicates", "7 (bare), 2 (palisades)", "42 virtual plots", "--"),
        ("Monitoring period", "May--Nov 2025", "Synthetic events", "--"),
    ]

    print("\n" + "=" * 90)
    print("TABELA COMPARATIVA: Field (talude) x Synthetic (Test 5) x Model (K_plint)")
    print("=" * 90)
    header = f"{'Metric':<40} {'Field':>15} {'Synthetic':>15} {'Model':>15}"
    print(header)
    print("-" * 90)
    for metric, field, synth, model in rows:
        print(f"{metric:<40} {field:>15} {synth:>15} {model:>15}")

    # Salvar como CSV para referência
    df = pd.DataFrame(rows, columns=["Metric", "Field (talude)", "Synthetic (Test 5)", "Model (K_plint)"])
    csv_path = FIG_DIR_ECZ / "tabela_comparativa_campo_sintetico.csv"
    df.to_csv(csv_path, index=False)
    print(f"\n  [OK] Tabela → {csv_path.name}")

    return rows


# ══════════════════════════════════════════════════════════════════════
# MAIN
# ══════════════════════════════════════════════════════════════════════
def main():
    print("=" * 70)
    print("SIMULAÇÃO 06 -- ÂNCORA EMPÍRICA (TALUDE LIMPO x PALIÇADAS BAIXAS)")
    print("=" * 70)
    print(f"  Geometria: {LAMBDA_M} x {LARGURA_M} m  |  Área: {A_PARC_M2:.2f} m²")
    print(f"  Inclinação: {INCLIN_GRAUS} deg  |  LS: {LS_TALUDE:.3f}")
    print(f"  Tratamentos: LIMPO = solo descoberto  |  PEDRA = paliçadas baixas (~20 cm)")
    print(f"  Perda LIMPO: {A_LIMPO_t_ha:.2f} t/ha  |  Perda PEDRA: {A_PEDRA_t_ha:.2f} t/ha")
    print(f"  Razão LIMPO/PEDRA: {A_total_LIMPO/A_total_PEDRA:.2f}")
    print(f"  C.P empírico (paliçadas): {CP_EMPIRICO:.3f}")
    print(f"  K_obs LIMPO: {K_obs_LIMPO:.6f} t h MJ⁻¹ mm⁻¹")
    print(f"  delta_field: {DELTA_FIELD:.4f}")
    print(f"  delta_obs (Test 5): {DELTA_OBS_SINTETICO:.2f}")
    print(f"  delta_mod (K_plint): {DELTA_MOD:.2f}")
    print()

    fig_09_bracketing_delta()
    fig_10_eficiencia_palicadas()
    fig_11_acumulado()
    tabela_comparativa()

    print(f"\n  Todas as figuras salvas em: {FIG_DIR_ECZ}")


if __name__ == "__main__":
    main()
