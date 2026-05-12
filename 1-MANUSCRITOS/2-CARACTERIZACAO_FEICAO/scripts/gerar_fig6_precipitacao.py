"""
Figura 6 do manuscrito Caracterizacao_Feicao_Erosiva_Plintossolo.qmd

Série de precipitação diária e acumulado móvel de 30 dias para São Cristóvão, SE
(2005-2025), com marcação dos limiares P90 e P95 mensais.

A paleta foi deliberadamente alterada em relação à figura equivalente usada no
manuscrito Controle_Ravinas_Paliçadas (azul + vermelho tracejado) para evitar
duplicação visual entre os dois artigos.
"""

from __future__ import annotations

from pathlib import Path

import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

# ──────────────────────────────────────────────────────────────────────────────
# Caminhos
# ──────────────────────────────────────────────────────────────────────────────
SCRIPT_DIR = Path(__file__).resolve().parent
ARTIGO_DIR = SCRIPT_DIR.parent
REPO_DIR = ARTIGO_DIR.parents[1]
DATA_CSV = (
    REPO_DIR
    / "2-DADOS"
    / "CLIMATOLOGIA_20ANOS"
    / "dados"
    / "serie_precipitacao_20anos.csv"
)
OUTPUT_PNG = ARTIGO_DIR / "media" / "fig_precipitacao_serie_2005_2025.png"

# ──────────────────────────────────────────────────────────────────────────────
# Estilo (paleta diferente da usada no artigo de controle de ravinas)
# ──────────────────────────────────────────────────────────────────────────────
plt.rcParams.update(
    {
        "font.family": "DejaVu Sans",
        "font.size": 10,
        "axes.labelsize": 11,
        "axes.titlesize": 12,
        "xtick.labelsize": 9,
        "ytick.labelsize": 9,
        "legend.fontsize": 9,
        "figure.dpi": 300,
    }
)

# Paleta distinta da figura equivalente do artigo de paliçadas (azul + vermelho).
# Aqui usa-se verde-musgo para a chuva diária e laranja queimado para o
# acumulado móvel, com limiares em ocre e marrom escuro.
COR_DIARIA = "#3E7C59"          # verde-musgo para barras diárias
COR_ACUMULADO = "#D97706"       # laranja queimado para o acumulado móvel
COR_P90 = "#B7950B"             # ocre para limiar P90
COR_P95 = "#5D4037"             # marrom escuro para limiar P95


def carregar_serie(csv_path: Path) -> pd.DataFrame:
    df = pd.read_csv(csv_path, parse_dates=["Data"])
    df = df.sort_values("Data").reset_index(drop=True)
    df["Precip_Movel_30d"] = (
        df["Precipitacao_mm"].rolling(window=30, min_periods=1).sum()
    )
    return df


def calcular_limiares_mensais(df: pd.DataFrame) -> tuple[float, float]:
    mensal = df.groupby(["Ano", "Mes"], as_index=False)["Precipitacao_mm"].sum()
    p90 = float(np.percentile(mensal["Precipitacao_mm"], 90))
    p95 = float(np.percentile(mensal["Precipitacao_mm"], 95))
    return p90, p95


def plotar_figura(df: pd.DataFrame, p90: float, p95: float, output: Path) -> None:
    fig, ax = plt.subplots(figsize=(13, 5.2))

    # Precipitação diária como barras finas (estilo distinto do artigo de paliçadas)
    ax.bar(
        df["Data"],
        df["Precipitacao_mm"],
        width=1.0,
        color=COR_DIARIA,
        alpha=0.55,
        linewidth=0,
        label="Precipitação diária (mm)",
    )

    # Acumulado móvel de 30 dias como linha sólida
    ax.plot(
        df["Data"],
        df["Precip_Movel_30d"],
        color=COR_ACUMULADO,
        linewidth=1.3,
        alpha=0.95,
        label="Acumulado móvel de 30 dias (mm)",
    )

    # Limiares P90 e P95 (mensais) como referências horizontais
    ax.axhline(
        p90,
        color=COR_P90,
        linewidth=1.0,
        linestyle="--",
        alpha=0.85,
        label=f"P90 mensal = {p90:.1f} mm",
    )
    ax.axhline(
        p95,
        color=COR_P95,
        linewidth=1.0,
        linestyle=":",
        alpha=0.9,
        label=f"P95 mensal = {p95:.1f} mm",
    )

    ax.set_xlabel("Ano", fontweight="bold")
    ax.set_ylabel("Precipitação (mm)", fontweight="bold")
    ax.set_xlim(df["Data"].min(), df["Data"].max())
    ax.set_ylim(bottom=0)
    ax.xaxis.set_major_locator(mdates.YearLocator(2))
    ax.xaxis.set_minor_locator(mdates.YearLocator(1))
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y"))
    ax.tick_params(axis="x", rotation=0)
    ax.grid(axis="y", linestyle="--", alpha=0.35, linewidth=0.5)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.legend(loc="upper right", framealpha=0.92, ncol=2)

    fig.tight_layout()
    output.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output, dpi=300, bbox_inches="tight", facecolor="white")
    plt.close(fig)


def main() -> None:
    if not DATA_CSV.exists():
        raise FileNotFoundError(f"Série de precipitação não encontrada: {DATA_CSV}")

    df = carregar_serie(DATA_CSV)
    p90, p95 = calcular_limiares_mensais(df)

    plotar_figura(df, p90, p95, OUTPUT_PNG)

    n_dias = len(df)
    total = df["Precipitacao_mm"].sum()
    media_anual = total / (n_dias / 365.25)
    print(f"Figura salva em: {OUTPUT_PNG}")
    print(f"Período: {df['Data'].min():%Y-%m-%d} a {df['Data'].max():%Y-%m-%d}")
    print(f"n = {n_dias} dias | total = {total:.1f} mm | média anual = {media_anual:.1f} mm")
    print(f"P90 mensal = {p90:.1f} mm | P95 mensal = {p95:.1f} mm")


if __name__ == "__main__":
    main()
