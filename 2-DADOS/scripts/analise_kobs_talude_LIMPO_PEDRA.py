"""
Analise integrada talude LIMPO/PEDRA × precipitação climatologica × K_obs preliminar
=====================================================================================

Objetivo
--------
Pareamento das 15 coletas de sedimento (parcelas LIMPO e PEDRA, talude 22 graus,
Plintossolo Haplico) com a precipitacao acumulada entre coletas extraida da serie
diaria 2005-2025 (estacao climatologica do projeto, distancia < 500 m das parcelas).
Producao de:
  (a) tabela de eventos com P_intervalo (mm), sedimento medio por tratamento (g),
      perda relativa LIMPO:PEDRA;
  (b) estimativa preliminar de K_obs no padrao USLE assumindo dimensoes Wischmeier
      (22,13 m x 1,83 m = 40,5 m^2) como cenario declarado, sob ressalva explicita
      de que dimensoes reais devem ser confirmadas em caderneta de campo;
  (c) figuras de suporte (chuva-sedimento, razao LIMPO:PEDRA por evento).

Limitacoes declaradas
---------------------
1. P_intervalo e a precipitacao total entre coletas, nao a precipitacao por evento
   erosivo isolado (intervalo seco minimo de 6 h nao foi reconstruido aqui).
2. R-factor (EI30) por intervalo nao foi recalculado; usa-se erosividade unitaria
   media regional (R_anual aproximado) como cenario para estimar K_obs ordem de
   grandeza, nao para inferencia formal.
3. Volume de escoamento superficial nao foi monitorado; impossivel calcular C-factor
   real ou aplicar a forma rigorosa K = A / (R . LS . C . P). Adota-se C=P=1
   (parcela nua padrao Wischmeier) como hipotese.
4. Dimensoes da parcela assumidas como padrao Wischmeier 22,13 x 1,83 m. Caso
   medicao de campo difira, todas as taxas devem ser reescaladas pelo fator
   A_real / 40,5.
"""

from __future__ import annotations

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path

BASE = Path(r"c:\Users\vidal\OneDrive\Documentos\13 - CLONEGIT\artigo-posdoc\3-EROSIBIDADE\2-DADOS")
OUT = BASE / "RELATORIO_PARALELO_SEDIMENTOS_media"
OUT.mkdir(parents=True, exist_ok=True)
FIG = BASE / "scripts" / "figuras_kobs_talude"
FIG.mkdir(parents=True, exist_ok=True)


# ---------------------------------------------------------------------------
# 1. Dados de sedimento
# ---------------------------------------------------------------------------
sed = pd.read_csv(BASE / "Sedimentos_talude_LIMPO_PEDRA_dados_longos.csv")
sed["data"] = pd.to_datetime(sed["data"])
sed = sed.sort_values(["tratamento", "codigo_parcela", "data"]).reset_index(drop=True)

# ---------------------------------------------------------------------------
# 2. Serie diaria de precipitacao (2005-2025)
# ---------------------------------------------------------------------------
ppt = pd.read_csv(BASE / "CLIMATOLOGIA_20ANOS" / "dados" / "serie_precipitacao_20anos.csv")
ppt["Data"] = pd.to_datetime(ppt["Data"])
ppt = ppt.sort_values("Data").reset_index(drop=True)

# Janela experimental
inicio_exp = pd.Timestamp("2025-04-01")  # antes da primeira coleta (13/05/2025)
fim_exp = pd.Timestamp("2025-11-30")
ppt_exp = ppt[(ppt["Data"] >= inicio_exp) & (ppt["Data"] <= fim_exp)].copy()

# ---------------------------------------------------------------------------
# 3. Pareamento: precipitacao acumulada entre coletas consecutivas
# ---------------------------------------------------------------------------
datas_coleta = sorted(sed["data"].unique())
intervalos = []
data_anterior = inicio_exp
for d in datas_coleta:
    p_int = ppt_exp[(ppt_exp["Data"] > data_anterior) & (ppt_exp["Data"] <= d)]["Precipitacao_mm"].sum()
    n_dias = (pd.Timestamp(d) - data_anterior).days
    n_dias_chuvosos = (ppt_exp[(ppt_exp["Data"] > data_anterior) & (ppt_exp["Data"] <= d)]["Precipitacao_mm"] > 0).sum()
    p_max_dia = ppt_exp[(ppt_exp["Data"] > data_anterior) & (ppt_exp["Data"] <= d)]["Precipitacao_mm"].max()
    intervalos.append({
        "data_coleta": d,
        "data_inicio_intervalo": data_anterior,
        "n_dias_intervalo": n_dias,
        "n_dias_chuvosos": int(n_dias_chuvosos),
        "P_intervalo_mm": float(p_int),
        "P_max_dia_mm": float(p_max_dia) if pd.notna(p_max_dia) else 0.0,
    })
    data_anterior = pd.Timestamp(d)

intervalos_df = pd.DataFrame(intervalos)

# ---------------------------------------------------------------------------
# 4. Sedimento medio por tratamento por coleta
# ---------------------------------------------------------------------------
agreg = (
    sed.groupby(["data", "tratamento"])
    .agg(
        sedimento_medio_g=("sedimento_g", "mean"),
        sedimento_total_g=("sedimento_g", "sum"),
        n_parcelas=("codigo_parcela", "nunique"),
        cv_pct=("sedimento_g", lambda x: 100 * x.std(ddof=1) / x.mean() if len(x) > 1 else np.nan),
    )
    .reset_index()
)

pivot_med = agreg.pivot(index="data", columns="tratamento", values="sedimento_medio_g").reset_index()
pivot_med.columns.name = None
pivot_med = pivot_med.rename(columns={"LIMPO": "med_LIMPO_g", "PEDRA": "med_PEDRA_g"})
pivot_med["data"] = pd.to_datetime(pivot_med["data"])

intervalos_df["data_coleta"] = pd.to_datetime(intervalos_df["data_coleta"])
tabela = intervalos_df.merge(pivot_med, left_on="data_coleta", right_on="data").drop(columns=["data"])

# Razao LIMPO/PEDRA
tabela["razao_LIMPO_PEDRA"] = tabela["med_LIMPO_g"] / tabela["med_PEDRA_g"]

# ---------------------------------------------------------------------------
# 5. Estimativa preliminar de K_obs (dimensoes reais confirmadas em campo)
# ---------------------------------------------------------------------------
# Hipoteses confirmadas pela equipe de campo:
#   - rampa de 2,40 m de comprimento na direcao do declive
#   - largura de 0,50 m
#   - inclinacao de 22 graus
#   - PEDRA: rampa coberta por fragmentos rochosos (~20 cm de espessura)
#   - LIMPO: rampa em solo nu (controle Wischmeier reduzido)
import math
LAMBDA_M = 2.40           # comprimento de rampa (m)
LARGURA_M = 0.50          # largura (m)
A_PARC_M2 = LAMBDA_M * LARGURA_M  # 1.20 m^2
INCLIN_GRAUS = 22.0
sin_t = math.sin(math.radians(INCLIN_GRAUS))
# S = 16.8 sin(theta) - 0.50 (McCool et al., 1989, para slope > 9%)
S_factor = 16.8 * sin_t - 0.50
# L = (lambda/22.13)^m, m = 0.5 para slope > 5% (Renard et al., 1997)
M_EXP = 0.5
L_factor = (LAMBDA_M / 22.13) ** M_EXP
LS = L_factor * S_factor

# Erosividade R: serie 20 anos da estacao indica R anual; usa-se EI30 anual estimado
# do relatorio (consultar ei30_anual.csv para valor regional)
ei30 = pd.read_csv(BASE / "CLIMATOLOGIA_20ANOS" / "dados" / "ei30_anual.csv")
# A coluna 'precipitacao' do arquivo ei30_anual armazena EI30 anual (MJ.mm/(ha.h.ano));
# excluem-se 2005 (ano parcial) e 2025 (ano em curso) para a media climatologica.
ei30["ano"] = pd.to_datetime(ei30["Data"]).dt.year
R_anual_med = ei30[(ei30["ano"] >= 2006) & (ei30["ano"] <= 2024)]["precipitacao"].mean()

# Para o intervalo experimental, R proporcional a fracao da chuva anual
P_anual_med = ppt.groupby("Ano")["Precipitacao_mm"].sum().mean()
P_total_exp = tabela["P_intervalo_mm"].sum()
R_exp_estim = R_anual_med * (P_total_exp / P_anual_med) if (P_anual_med and not np.isnan(R_anual_med)) else np.nan

# Perda de solo total no experimento por tratamento (g/parcela -> t/ha)
A_total_LIMPO = sed[sed["tratamento"] == "LIMPO"].groupby("codigo_parcela")["sedimento_g"].sum().mean()
A_total_PEDRA = sed[sed["tratamento"] == "PEDRA"].groupby("codigo_parcela")["sedimento_g"].sum().mean()

# Conversao g/parcela -> t/ha:  (g / A_m2) * 10^4 m2/ha * 10^-6 t/g = g / A_m2 * 0.01
conv = 0.01 / A_PARC_M2  # (t/ha) / g
A_LIMPO_t_ha = A_total_LIMPO * conv
A_PEDRA_t_ha = A_total_PEDRA * conv

# K_obs preliminar (C=P=1 para LIMPO; PEDRA tem C reduzido nao quantificado)
K_obs_LIMPO = (A_LIMPO_t_ha / (R_exp_estim * LS * 1.0 * 1.0)) if (R_exp_estim and not np.isnan(R_exp_estim)) else np.nan

# ---------------------------------------------------------------------------
# 6. Salvar tabelas
# ---------------------------------------------------------------------------
tabela.to_csv(OUT / "tabela_eventos_chuva_sedimento.csv", index=False, float_format="%.3f")

resumo = pd.DataFrame({
    "metrica": [
        "Comprimento de rampa lambda (m)",
        "Largura da parcela (m)",
        "Area da parcela (m2)",
        "Inclinacao (graus)",
        "Precipitacao total experimento (mm)",
        "Precipitacao anual media historica (mm)",
        "Fracao da chuva anual coberta",
        "EI30 anual medio historico (MJ mm ha-1 h-1 ano-1)",
        "R estimado para o intervalo experimental",
        "L (lambda/22,13)^0,5",
        "S (McCool 22 graus)",
        "LS (talude 22 graus, lambda=2,40 m)",
        "Perda media por parcela LIMPO (g)",
        "Perda media por parcela PEDRA (g)",
        "Perda media LIMPO (t/ha)",
        "Perda media PEDRA (t/ha)",
        "Razao perdas LIMPO:PEDRA",
        "K_obs preliminar LIMPO (t h MJ-1 mm-1)",
        "K_RUSLE nominal Plintossolo (t h MJ-1 mm-1)",
        "Razao K_obs / K_RUSLE (delta aparente)",
    ],
    "valor": [
        LAMBDA_M,
        LARGURA_M,
        round(A_PARC_M2, 3),
        INCLIN_GRAUS,
        round(P_total_exp, 1),
        round(P_anual_med, 1),
        round(P_total_exp / P_anual_med, 3),
        round(R_anual_med, 1) if not np.isnan(R_anual_med) else np.nan,
        round(R_exp_estim, 1) if not np.isnan(R_exp_estim) else np.nan,
        round(L_factor, 3),
        round(S_factor, 3),
        round(LS, 3),
        round(A_total_LIMPO, 1),
        round(A_total_PEDRA, 1),
        round(A_LIMPO_t_ha, 3),
        round(A_PEDRA_t_ha, 3),
        round(A_LIMPO_t_ha / A_PEDRA_t_ha, 2),
        round(K_obs_LIMPO, 6) if not np.isnan(K_obs_LIMPO) else np.nan,
        round(0.035, 4),  # K_RUSLE nominal Plintossolo (Tabuleiros Costeiros)
        round(K_obs_LIMPO / 0.035, 3) if not np.isnan(K_obs_LIMPO) else np.nan,
    ],
})
resumo.to_csv(OUT / "resumo_kobs_preliminar.csv", index=False)

print("="*70)
print("RESUMO INTEGRADO LIMPO/PEDRA × PRECIPITACAO × K_obs PRELIMINAR")
print("="*70)
print(resumo.to_string(index=False))
print()
print("Tabela coletas (chuva entre coletas e sedimento medio):")
print(tabela[["data_coleta", "n_dias_intervalo", "P_intervalo_mm", "P_max_dia_mm",
              "med_LIMPO_g", "med_PEDRA_g", "razao_LIMPO_PEDRA"]].to_string(index=False))

# ---------------------------------------------------------------------------
# 7. Figuras
# ---------------------------------------------------------------------------
plt.rcParams.update({"font.size": 10, "figure.dpi": 110})

# Fig 1. Chuva acumulada entre coletas vs sedimento medio
fig, ax1 = plt.subplots(figsize=(10, 4.5))
ax2 = ax1.twinx()
x = tabela["data_coleta"]
ax1.bar(x, tabela["P_intervalo_mm"], width=4, color="#4F9DDE", alpha=0.55, label="Precipitação no intervalo (mm)")
ax2.plot(x, tabela["med_LIMPO_g"], "o-", color="#C0392B", label="LIMPO (g/parcela)", lw=2)
ax2.plot(x, tabela["med_PEDRA_g"], "s-", color="#27AE60", label="PEDRA (g/parcela)", lw=2)
ax1.set_ylabel("Precipitação acumulada entre coletas (mm)", color="#2C5780")
ax2.set_ylabel("Sedimento médio por parcela (g)")
ax1.set_xlabel("Data da coleta")
ax1.tick_params(axis="x", rotation=30)
fig.suptitle("Resposta hidrossedimentológica do talude (Plintossolo, 22°)\nPrecipitação entre coletas vs perda de solo média por tratamento")
lines, labels = ax2.get_legend_handles_labels()
bars, blab = ax1.get_legend_handles_labels()
ax1.legend(bars + lines, blab + labels, loc="upper right", fontsize=8)
fig.tight_layout()
fig.savefig(FIG / "fig_chuva_sedimento_LIMPO_PEDRA.png", dpi=180, bbox_inches="tight")
plt.close(fig)

# Fig 2. Razao LIMPO:PEDRA
fig, ax = plt.subplots(figsize=(10, 4))
ax.bar(tabela["data_coleta"], tabela["razao_LIMPO_PEDRA"], width=4, color="#7D3C98", alpha=0.75)
ax.axhline(1, color="k", ls="--", lw=0.8)
ax.set_ylabel("Razão LIMPO/PEDRA (g/g)")
ax.set_xlabel("Data da coleta")
ax.set_title("Eficiência relativa da cobertura granular (PEDRA) vs solo nu (LIMPO)\nRazões > 1 indicam que a cobertura granular reduziu a perda de solo")
ax.tick_params(axis="x", rotation=30)
fig.tight_layout()
fig.savefig(FIG / "fig_razao_LIMPO_PEDRA.png", dpi=180, bbox_inches="tight")
plt.close(fig)

print()
print(f"Figuras salvas em: {FIG}")
print(f"Tabelas salvas em: {OUT}")
