#!/usr/bin/env python3
"""
Classificação Processo-Funcional de Feições Erosivas em Plintossolos Tropicais
==============================================================================
Material Suplementar — Proposta 1 (Chave Determinística) + Proposta 2 (Lógica Fuzzy)
+ Clustering Exploratório (Ward + k-means)

Gera figuras para o material suplementar do artigo:
  - Fig. S1: Árvore de decisão determinística (fluxograma)
  - Fig. S2: Funções de pertinência fuzzy por variável
  - Fig. S3: Graus de pertinência fuzzy por feição (barras empilhadas)
  - Fig. S4: Dendrograma (Ward) + silhouette
  - Fig. S5: Radar comparativo: EGC vs. Classificação Processo-Funcional

Autores: Santos, L.D.V. et al.
Data: Abril 2026
"""

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyBboxPatch
import skfuzzy as fuzz
from skfuzzy import control as ctrl
from scipy.cluster.hierarchy import dendrogram, linkage, fcluster
from scipy.spatial.distance import pdist
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score, silhouette_samples
from sklearn.preprocessing import StandardScaler
import warnings
import os

warnings.filterwarnings("ignore")

# ── Diretório de saída ────────────────────────────────────────────────────────
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
OUT_DIR = os.path.join(SCRIPT_DIR, "..", "2-CARACTERIZACAO_FEICAO", "media")
os.makedirs(OUT_DIR, exist_ok=True)

# ── Configuração global de figuras ────────────────────────────────────────────
plt.rcParams.update({
    "font.family": "serif",
    "font.size": 10,
    "axes.labelsize": 11,
    "axes.titlesize": 12,
    "figure.dpi": 300,
    "savefig.dpi": 300,
})

# =============================================================================
# 1. DADOS DAS FEIÇÕES (do manuscrito, Tab. 1 e Tab. 2)
# =============================================================================
feicoes = pd.DataFrame({
    "Feicao":          ["F1",   "F2",   "F3",   "F4",   "F5",   "F6"],
    "Comprimento_m":   [35.0,    8.0,    9.0,   20.2,   24.8,    np.nan],
    "Largura_media_m": [1.37,   1.87,   1.30,   1.39,   1.38,   2.37],
    "Prof_max_m":      [1.10,   0.40,   0.60,   1.40,   1.50,   0.60],
    "Secao":           ["U",    "V",    "V",    "V",    "V",    "V"],
    "Cabeca":          ["escarpada", "suave", "suave", "vertical", "escarpada", "suave"],
    "Declividade_pct": [12.0,    8.0,    9.0,   15.0,   17.0,   10.0],  # estimada do MDE
})

# Dados edáficos e hidrológicos (constantes para o sítio, Tab. 2 + VIB)
ARGILA_B_PCT = 51.4       # % argila horizonte Bt
M_AL_PCT = 99.2           # saturação por Al no BAc (pior caso)
P95_MM = 181.8            # P95 mensal (mm), série 2005–2025
VIB_INTERMEDIARIO = 1.53  # cm/h, terço intermediário

# VIB por posição (usada na chave — assume-se terço intermediário como referência
# para todas as feições, pois todas estão em topo de vale com convergência)
feicoes["VIB_cmh"] = VIB_INTERMEDIARIO
feicoes["Argila_B"] = ARGILA_B_PCT
feicoes["m_Al"] = M_AL_PCT
feicoes["P95_mm"] = P95_MM


# =============================================================================
# 2. PROPOSTA 1 — CHAVE DETERMINÍSTICA PROCESSO-FUNCIONAL
# =============================================================================
def classificar_nivel1(prof):
    """Nível 1: classificação morfométrica por profundidade."""
    if prof < 0.3:
        return "Sulco"
    elif prof <= 3.0:
        return "Ravina"
    else:
        return "Voçoroca"


def classificar_mecanismo(row):
    """Nível 2: mecanismo dominante."""
    mecanismos = []
    if row["VIB_cmh"] < 2.0 and row["Argila_B"] > 45:
        mecanismos.append("Saturação-dominante")
    if row["VIB_cmh"] >= 2.0 and row["Declividade_pct"] > 12:
        mecanismos.append("Incisão-dominante")
    if row["Cabeca"] in ("vertical", "escarpada") and row["Prof_max_m"] > 0.8:
        mecanismos.append("Regressão-dominante")
    if not mecanismos:
        mecanismos.append("Incisão moderada")
    return " + ".join(mecanismos)


def contar_indicadores_criticos(row):
    """Nível 3: contagem de indicadores críticos (Tab. 3 do manuscrito)."""
    n = 0
    if row["VIB_cmh"] < 2.0:
        n += 1
    if row["Argila_B"] > 45:
        n += 1
    if row["m_Al"] > 80:
        n += 1
    if row["P95_mm"] > 150:
        n += 1
    if row["Prof_max_m"] > 1.0 and row["Cabeca"] in ("vertical", "escarpada"):
        n += 1
    return n


def classificar_vulnerabilidade(n_crit):
    """Nível 3: classe de vulnerabilidade."""
    if n_crit >= 4:
        return "Crítica"
    elif n_crit >= 2:
        return "Moderada"
    else:
        return "Baixa"


# Aplicar a chave
feicoes["Nivel1"] = feicoes["Prof_max_m"].apply(classificar_nivel1)
feicoes["Mecanismo"] = feicoes.apply(classificar_mecanismo, axis=1)
feicoes["N_criticos"] = feicoes.apply(contar_indicadores_criticos, axis=1)
feicoes["Vulnerabilidade"] = feicoes["N_criticos"].apply(classificar_vulnerabilidade)

print("=" * 80)
print("PROPOSTA 1 — CHAVE DETERMINÍSTICA PROCESSO-FUNCIONAL")
print("=" * 80)
print(feicoes[["Feicao", "Prof_max_m", "Nivel1", "Mecanismo",
               "N_criticos", "Vulnerabilidade"]].to_string(index=False))
print()


# =============================================================================
# 3. PROPOSTA 2 — LÓGICA FUZZY (Mamdani)
# =============================================================================

# ── Variáveis de entrada ──────────────────────────────────────────────────────
profundidade = ctrl.Antecedent(np.arange(0, 3.1, 0.01), "profundidade")
vib = ctrl.Antecedent(np.arange(0, 10.1, 0.1), "vib")
m_al = ctrl.Antecedent(np.arange(0, 101, 1), "m_al")
p95 = ctrl.Antecedent(np.arange(0, 301, 1), "p95")
decliv = ctrl.Antecedent(np.arange(0, 31, 0.5), "declividade")

# ── Variável de saída: grau de severidade erosiva ────────────────────────────
severidade = ctrl.Consequent(np.arange(0, 101, 1), "severidade")

# ── Funções de pertinência — Profundidade (m) ────────────────────────────────
profundidade["rasa"] = fuzz.trapmf(profundidade.universe, [0, 0, 0.3, 0.6])
profundidade["moderada"] = fuzz.trapmf(profundidade.universe, [0.3, 0.6, 1.0, 1.5])
profundidade["profunda"] = fuzz.trapmf(profundidade.universe, [1.0, 1.5, 3.0, 3.0])

# ── Funções de pertinência — VIB (cm/h) ──────────────────────────────────────
vib["baixa"] = fuzz.trapmf(vib.universe, [0, 0, 1.5, 2.5])
vib["media"] = fuzz.trapmf(vib.universe, [1.5, 2.5, 4.0, 6.0])
vib["alta"] = fuzz.trapmf(vib.universe, [4.0, 6.0, 10.0, 10.0])

# ── Funções de pertinência — Saturação por Al (%) ────────────────────────────
m_al["baixa"] = fuzz.trapmf(m_al.universe, [0, 0, 30, 50])
m_al["moderada"] = fuzz.trapmf(m_al.universe, [30, 50, 70, 85])
m_al["alta"] = fuzz.trapmf(m_al.universe, [70, 85, 100, 100])

# ── Funções de pertinência — P95 mensal (mm) ─────────────────────────────────
p95["baixa"] = fuzz.trapmf(p95.universe, [0, 0, 80, 120])
p95["moderada"] = fuzz.trapmf(p95.universe, [80, 120, 150, 180])
p95["alta"] = fuzz.trapmf(p95.universe, [150, 180, 300, 300])

# ── Funções de pertinência — Declividade (%) ─────────────────────────────────
decliv["suave"] = fuzz.trapmf(decliv.universe, [0, 0, 5, 8])
decliv["moderada"] = fuzz.trapmf(decliv.universe, [5, 8, 15, 20])
decliv["forte"] = fuzz.trapmf(decliv.universe, [15, 20, 30, 30])

# ── Variável de saída — Severidade (0–100) ───────────────────────────────────
severidade["sulco"] = fuzz.trapmf(severidade.universe, [0, 0, 15, 30])
severidade["ravina_estavel"] = fuzz.trapmf(severidade.universe, [15, 30, 45, 55])
severidade["ravina_transicional"] = fuzz.trapmf(severidade.universe, [40, 55, 70, 80])
severidade["vocoroca_incipiente"] = fuzz.trapmf(severidade.universe, [65, 80, 100, 100])

# ── Regras de inferência (Mamdani) ───────────────────────────────────────────
regras = [
    # Regras de profundidade rasa
    ctrl.Rule(profundidade["rasa"] & vib["alta"], severidade["sulco"]),
    ctrl.Rule(profundidade["rasa"] & vib["media"], severidade["sulco"]),
    ctrl.Rule(profundidade["rasa"] & vib["baixa"] & m_al["baixa"], severidade["sulco"]),
    ctrl.Rule(profundidade["rasa"] & vib["baixa"] & m_al["moderada"], severidade["ravina_estavel"]),
    ctrl.Rule(profundidade["rasa"] & vib["baixa"] & m_al["alta"], severidade["ravina_estavel"]),

    # Regras de profundidade moderada
    ctrl.Rule(profundidade["moderada"] & vib["alta"], severidade["ravina_estavel"]),
    ctrl.Rule(profundidade["moderada"] & vib["media"] & decliv["suave"], severidade["ravina_estavel"]),
    ctrl.Rule(profundidade["moderada"] & vib["media"] & decliv["moderada"], severidade["ravina_transicional"]),
    ctrl.Rule(profundidade["moderada"] & vib["media"] & decliv["forte"], severidade["ravina_transicional"]),
    ctrl.Rule(profundidade["moderada"] & vib["baixa"] & m_al["alta"], severidade["ravina_transicional"]),
    ctrl.Rule(profundidade["moderada"] & vib["baixa"] & p95["alta"], severidade["ravina_transicional"]),
    ctrl.Rule(profundidade["moderada"] & vib["baixa"] & m_al["alta"] & p95["alta"],
              severidade["vocoroca_incipiente"]),

    # Regras de profundidade profunda
    ctrl.Rule(profundidade["profunda"] & vib["alta"], severidade["ravina_transicional"]),
    ctrl.Rule(profundidade["profunda"] & vib["media"], severidade["ravina_transicional"]),
    ctrl.Rule(profundidade["profunda"] & vib["baixa"], severidade["vocoroca_incipiente"]),
    ctrl.Rule(profundidade["profunda"] & decliv["forte"], severidade["vocoroca_incipiente"]),
    ctrl.Rule(profundidade["profunda"] & m_al["alta"] & p95["alta"],
              severidade["vocoroca_incipiente"]),
    ctrl.Rule(profundidade["profunda"] & vib["baixa"] & m_al["alta"] & p95["alta"] & decliv["moderada"],
              severidade["vocoroca_incipiente"]),
]

sistema_ctrl = ctrl.ControlSystem(regras)
sistema = ctrl.ControlSystemSimulation(sistema_ctrl)

# ── Simulação para cada feição ────────────────────────────────────────────────
resultados_fuzzy = []
for _, row in feicoes.iterrows():
    sistema.input["profundidade"] = row["Prof_max_m"]
    sistema.input["vib"] = row["VIB_cmh"]
    sistema.input["m_al"] = row["m_Al"]
    sistema.input["p95"] = row["P95_mm"]
    sistema.input["declividade"] = row["Declividade_pct"]
    sistema.compute()

    sev_val = sistema.output["severidade"]

    # Calcular grau de pertinência a cada classe de saída
    mu_sulco = fuzz.interp_membership(severidade.universe,
                                       severidade["sulco"].mf, sev_val)
    mu_rav_est = fuzz.interp_membership(severidade.universe,
                                         severidade["ravina_estavel"].mf, sev_val)
    mu_rav_trans = fuzz.interp_membership(severidade.universe,
                                           severidade["ravina_transicional"].mf, sev_val)
    mu_voc = fuzz.interp_membership(severidade.universe,
                                     severidade["vocoroca_incipiente"].mf, sev_val)

    resultados_fuzzy.append({
        "Feicao": row["Feicao"],
        "Severidade": round(sev_val, 1),
        "mu_Sulco": round(mu_sulco, 3),
        "mu_Ravina_Estavel": round(mu_rav_est, 3),
        "mu_Ravina_Transicional": round(mu_rav_trans, 3),
        "mu_Vocoroca_Incipiente": round(mu_voc, 3),
    })

df_fuzzy = pd.DataFrame(resultados_fuzzy)

# Classe dominante por maior pertinência
cols_mu = ["mu_Sulco", "mu_Ravina_Estavel", "mu_Ravina_Transicional", "mu_Vocoroca_Incipiente"]
labels_mu = ["Sulco", "Ravina estável", "Ravina transicional", "Voçoroca incipiente"]
df_fuzzy["Classe_dominante"] = df_fuzzy[cols_mu].apply(
    lambda r: labels_mu[np.argmax(r.values)], axis=1
)

print("=" * 80)
print("PROPOSTA 2 — CLASSIFICAÇÃO POR LÓGICA FUZZY (Mamdani)")
print("=" * 80)
print(df_fuzzy.to_string(index=False))
print()


# =============================================================================
# 4. CLUSTERING EXPLORATÓRIO
# =============================================================================
# Usar feições com dados completos (excluir F6 sem comprimento)
feicoes_completas = feicoes.dropna(subset=["Comprimento_m"]).copy()
vars_cluster = ["Prof_max_m", "Largura_media_m", "Comprimento_m", "Declividade_pct"]

X = feicoes_completas[vars_cluster].values
scaler = StandardScaler()
X_scaled = scaler.fit_transform(X)
labels_feicoes = feicoes_completas["Feicao"].values

# Ward linkage
Z = linkage(X_scaled, method="ward")

# k-means k=2 e k=3
km2 = KMeans(n_clusters=2, random_state=42, n_init=10).fit(X_scaled)
km3 = KMeans(n_clusters=3, random_state=42, n_init=10).fit(X_scaled)

if len(X_scaled) >= 3:
    sil2 = silhouette_score(X_scaled, km2.labels_)
    sil3 = silhouette_score(X_scaled, km3.labels_)
else:
    sil2 = sil3 = np.nan

print("=" * 80)
print("CLUSTERING EXPLORATÓRIO")
print("=" * 80)
print(f"Silhouette (k=2): {sil2:.3f}")
print(f"Silhouette (k=3): {sil3:.3f}")
for f, c2, c3 in zip(labels_feicoes, km2.labels_, km3.labels_):
    print(f"  {f}: cluster_k2={c2}, cluster_k3={c3}")
print()


# =============================================================================
# 5. GERAÇÃO DE FIGURAS
# =============================================================================

# ── Fig. S1 / Fig. 6: Fluxograma da chave determinística ─────────────────────
def fig_fluxograma():
    """Chave de classificação processo-funcional — estilo monocromático.

    Design baseado em convenções de chaves taxonômicas hierárquicas e
    diagramas ISO 5807:  losango para decisão, retângulos para processos
    e terminais, paleta monocromática (grayscale-safe), 300 DPI.
    """

    fig, ax = plt.subplots(figsize=(8, 14))
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 17)
    ax.axis("off")
    ax.set_aspect("equal")

    # ── Paleta monocromática ──────────────────────────────────────────────
    BK  = "#333333"           # bordas e texto principal
    GY  = "#777777"           # texto secundário / anotações
    LG  = "#F0F0F0"           # cinza claro (decisões, entrada)
    MG  = "#E0E0E0"           # cinza médio (terminais)

    LW  = 0.8                 # espessura padrão
    LWT = 1.2                 # espessura terminais

    # ── Helpers ───────────────────────────────────────────────────────────
    def rbox(cx, cy, w, h, txt, fs=8.5, fc="white", lw=LW, bold=False):
        ax.add_patch(FancyBboxPatch(
            (cx - w/2, cy - h/2), w, h,
            boxstyle="round,pad=0.06", fc=fc, ec=BK, lw=lw, zorder=2))
        ax.text(cx, cy, txt, ha="center", va="center", fontsize=fs,
                fontweight="bold" if bold else "normal", color=BK,
                zorder=3, linespacing=1.3, multialignment="center")

    def tbox(cx, cy, w, h, txt, fs=9, fc=MG):
        """Caixa terminal (borda mais espessa)."""
        ax.add_patch(FancyBboxPatch(
            (cx - w/2, cy - h/2), w, h,
            boxstyle="round,pad=0.06", fc=fc, ec=BK, lw=LWT, zorder=2))
        ax.text(cx, cy, txt, ha="center", va="center", fontsize=fs,
                fontweight="bold", color=BK, zorder=3, linespacing=1.3)

    def diam(cx, cy, w, h, txt, fs=8.5):
        """Losango de decisão ISO 5807."""
        pts = [(cx, cy + h/2), (cx + w/2, cy),
               (cx, cy - h/2), (cx - w/2, cy)]
        ax.add_patch(plt.Polygon(pts, closed=True, fc=LG, ec=BK,
                                  lw=LW, zorder=2))
        ax.text(cx, cy, txt, ha="center", va="center", fontsize=fs,
                color=BK, zorder=3, linespacing=1.2)

    def arr(x1, y1, x2, y2, lbl="", side="right"):
        ax.annotate("", xy=(x2, y2), xytext=(x1, y1),
                    arrowprops=dict(arrowstyle="-|>", color=BK, lw=0.6,
                                    mutation_scale=8), zorder=1)
        if lbl:
            mx, my = (x1 + x2) / 2, (y1 + y2) / 2
            if abs(x1 - x2) < 0.05:          # seta vertical
                dx = 0.12 if side == "right" else -0.12
                ha_t = "left" if dx > 0 else "right"
                ax.text(mx + dx, my, lbl, fontsize=7, color=GY,
                        fontstyle="italic", ha=ha_t, va="center", zorder=3)
            else:                               # seta horizontal
                ax.text(mx, my + 0.12, lbl, fontsize=7, color=GY,
                        fontstyle="italic", ha="center", va="bottom",
                        zorder=3)

    def sep(y, label):
        """Linha separadora horizontal tracejada com rótulo de nível."""
        ax.plot([0.3, 9.7], [y, y], color=GY, lw=0.4,
                linestyle=(0, (8, 4)), zorder=0, clip_on=False)
        ax.text(0.35, y + 0.08, label, fontsize=7.5, color=GY,
                fontweight="bold", va="bottom", zorder=1)

    # ═══════════════════════════════════════════════════════════════════════
    #  BLOCO EGC — Classificação morfológica prévia
    # ═══════════════════════════════════════════════════════════════════════
    ax.add_patch(FancyBboxPatch(
        (1.2, 15.15), 7.6, 1.5,
        boxstyle="round,pad=0.10", fc="white", ec=GY, lw=0.8,
        linestyle=(0, (4, 3)), zorder=2))
    ax.text(5, 16.3, "CLASSIFICAÇÃO MORFOLÓGICA — EGC",
            ha="center", va="center", fontsize=9.5,
            fontweight="bold", color=BK, zorder=3)
    ax.text(5, 15.65,
            "(1) Tipo   (2) Família   (3) Persistência   "
            "(4) Posição na paisagem\n"
            "(5) Forma   (6) Continuidade da forma   "
            "(7) Forma da seção transversal",
            ha="center", va="center", fontsize=8, color=GY,
            zorder=3, linespacing=1.5, multialignment="center")

    # Seta EGC → Extensão
    arr(5, 15.15, 5, 14.7)

    # Rótulo de extensão
    rbox(5, 14.4, 5.0, 0.45,
         "EXTENSÃO PROCESSO-FUNCIONAL",
         fs=9.5, fc=LG, bold=True)

    arr(5, 14.17, 5, 13.75)

    # ── Separadores de nível ──────────────────────────────────────────────
    sep(13.6, "NÍVEL 1 — Profundidade")
    sep(10.0, "NÍVEL 2 — Mecanismo dominante")
    sep(5.6, "NÍVEL 3 — Vulnerabilidade funcional")

    # ═══════════════════════════════════════════════════════════════════════
    #  NÍVEL 1 — PROFUNDIDADE
    # ═══════════════════════════════════════════════════════════════════════
    rbox(5, 13.2, 4.0, 0.5,
         "Feição erosiva classificada pela EGC",
         fs=9, fc=LG, bold=True)

    arr(5, 12.95, 5, 12.55)

    diam(5, 11.9, 3.2, 1.2, "Profundidade\nmáxima (m)?", fs=9)

    # Esquerda → SULCO
    arr(3.4, 11.9, 2.1, 11.9, "< 0,3")
    tbox(1.2, 11.9, 1.5, 0.4, "SULCO", fs=9)

    # Direita → VOÇOROCA
    arr(6.6, 11.9, 8.0, 11.9, "> 3,0")
    tbox(8.8, 11.9, 1.8, 0.4, "VOÇOROCA", fs=9)

    # Centro → RAVINA
    arr(5, 11.3, 5, 10.75, "0,3 – 3,0")
    rbox(5, 10.5, 2.0, 0.4, "RAVINA", fs=10, bold=True, fc=LG)

    # ═══════════════════════════════════════════════════════════════════════
    #  NÍVEL 2 — MECANISMO DOMINANTE
    # ═══════════════════════════════════════════════════════════════════════
    arr(5, 10.3, 5, 9.75)

    ax.text(5, 9.55, "Avaliar mecanismos (podem coexistir):",
            ha="center", va="center", fontsize=8, color=GY,
            fontstyle="italic", zorder=3)

    # Barra de bifurcação
    ax.plot([1.8, 8.2], [9.25, 9.25], color=BK, lw=LW, zorder=2)
    ax.plot([5, 5], [9.4, 9.25], color=BK, lw=0.6, zorder=2)
    for xp in [1.8, 5.0, 8.2]:
        arr(xp, 9.25, xp, 8.85)

    # Três losangos de avaliação (paralelos)
    diam(1.8, 8.2, 2.7, 1.2,
         "VIB < 2 cm h⁻¹\nArgila (B) > 45%?", fs=7.5)
    diam(5.0, 8.2, 2.7, 1.2,
         "Cabeça escarpada\nProf. > 0,8 m?", fs=7.5)
    diam(8.2, 8.2, 2.7, 1.2,
         "VIB ≥ 2 cm h⁻¹\nDecliv. > 12%?", fs=7.5)

    # Setas "Sim"
    arr(1.8, 7.6, 1.8, 7.1, "Sim")
    arr(5.0, 7.6, 5.0, 7.1, "Sim")
    arr(8.2, 7.6, 8.2, 7.1, "Sim")

    # Caixas de mecanismo (terminais)
    tbox(1.8, 6.75, 2.3, 0.5, "Saturação-\ndominante", fs=8.5, fc=MG)
    tbox(5.0, 6.75, 2.3, 0.5, "Regressão-\ndominante", fs=8.5, fc=MG)
    tbox(8.2, 6.75, 2.3, 0.5, "Incisão-\ndominante", fs=8.5, fc=MG)

    # Barra de convergência
    ax.plot([1.8, 8.2], [6.2, 6.2], color=BK, lw=LW, zorder=2)
    for xp in [1.8, 5.0, 8.2]:
        ax.plot([xp, xp], [6.5, 6.2], color=BK, lw=0.6, zorder=2)
    arr(5, 6.2, 5, 5.7)

    # ═══════════════════════════════════════════════════════════════════════
    #  NÍVEL 3 — VULNERABILIDADE FUNCIONAL
    # ═══════════════════════════════════════════════════════════════════════
    rbox(5, 4.6, 7.0, 1.6,
         "CONTAGEM DE INDICADORES CRÍTICOS (0–5)\n\n"
         "(1) VIB < 2 cm h⁻¹           (2) Argila (B) > 45%\n"
         "(3) m(Al) > 80%                (4) P95 > 150 mm mês⁻¹\n"
         "(5) Prof. > 1,0 m + cabeça escarpada",
         fs=8, fc=LG)

    # Três saídas de vulnerabilidade
    arr(3.0, 3.8, 2.0, 2.95, "0–1")
    arr(5.0, 3.8, 5.0, 2.95, "2–3")
    arr(7.0, 3.8, 8.0, 2.95, "≥ 4")

    # Gradiente de cinza: Baixa (claro) → Moderada → Crítica (escuro)
    tbox(2.0, 2.6, 1.8, 0.5, "BAIXA", fs=10, fc="#E8E8E8")
    tbox(5.0, 2.6, 2.2, 0.5, "MODERADA", fs=10, fc="#D0D0D0")
    tbox(8.0, 2.6, 1.8, 0.5, "CRÍTICA", fs=10, fc="#B8B8B8")

    # Nota interpretativa
    rbox(5, 1.4, 7.5, 0.65,
         "≥ 4 indicadores → equivalente funcional a voçoroca incipiente\n"
         "→ intervenção prioritária de controle",
         fs=8, lw=0.5)

    fig.savefig(os.path.join(OUT_DIR, "fig_S1_chave_deterministica.png"),
                bbox_inches="tight", pad_inches=0.3, dpi=300)
    plt.close()
    print("  → fig_S1_chave_deterministica.png")


# ── Fig. S2: Funções de pertinência fuzzy ─────────────────────────────────────
def fig_pertinencia():
    fig, axes = plt.subplots(2, 3, figsize=(12, 7))

    def plot_var(ax, universe, mfs, names, title, xlabel, colors=None):
        if colors is None:
            colors = ["#3498DB", "#F39C12", "#E74C3C"]
        for name, color in zip(names, colors):
            ax.plot(universe, mfs[name].mf, linewidth=2, label=name, color=color)
            ax.fill_between(universe, mfs[name].mf, alpha=0.15, color=color)
        ax.set_title(title, fontweight="bold")
        ax.set_xlabel(xlabel)
        ax.set_ylabel("μ")
        ax.legend(fontsize=8, loc="best")
        ax.set_ylim(-0.05, 1.1)
        ax.grid(alpha=0.3)

    plot_var(axes[0, 0], profundidade.universe, profundidade.terms,
             ["rasa", "moderada", "profunda"], "Profundidade", "m")
    plot_var(axes[0, 1], vib.universe, vib.terms,
             ["baixa", "media", "alta"], "VIB", "cm/h")
    plot_var(axes[0, 2], m_al.universe, m_al.terms,
             ["baixa", "moderada", "alta"], "Saturação por Al (m)", "%")
    plot_var(axes[1, 0], p95.universe, p95.terms,
             ["baixa", "moderada", "alta"], "P95 mensal", "mm")
    plot_var(axes[1, 1], decliv.universe, decliv.terms,
             ["suave", "moderada", "forte"], "Declividade", "%")

    # Saída
    ax_out = axes[1, 2]
    colors_out = ["#2ECC71", "#3498DB", "#F39C12", "#E74C3C"]
    names_out = ["sulco", "ravina_estavel", "ravina_transicional", "vocoroca_incipiente"]
    labels_out = ["Sulco", "Ravina estável", "Ravina transicional", "Voçoroca incipiente"]
    for name, label, color in zip(names_out, labels_out, colors_out):
        ax_out.plot(severidade.universe, severidade[name].mf, linewidth=2,
                     label=label, color=color)
        ax_out.fill_between(severidade.universe, severidade[name].mf,
                             alpha=0.15, color=color)
    ax_out.set_title("Severidade (saída)", fontweight="bold")
    ax_out.set_xlabel("Índice de severidade")
    ax_out.set_ylabel("μ")
    ax_out.legend(fontsize=7, loc="upper right")
    ax_out.set_ylim(-0.05, 1.1)
    ax_out.grid(alpha=0.3)

    fig.suptitle("Funções de pertinência do sistema fuzzy Mamdani", fontsize=13,
                  fontweight="bold", y=1.01)
    fig.tight_layout()
    fig.savefig(os.path.join(OUT_DIR, "fig_S2_funcoes_pertinencia_fuzzy.png"))
    plt.close()
    print("  → fig_S2_funcoes_pertinencia_fuzzy.png")


# ── Fig. S3: Graus de pertinência por feição (barras horizontais) ─────────────
def fig_pertinencia_feicoes():
    fig, ax = plt.subplots(figsize=(8, 4.5))

    feicoes_labels = df_fuzzy["Feicao"].values
    y_pos = np.arange(len(feicoes_labels))

    colors = ["#2ECC71", "#3498DB", "#F39C12", "#E74C3C"]
    bottom = np.zeros(len(feicoes_labels))

    for col, label, color in zip(cols_mu, labels_mu, colors):
        vals = df_fuzzy[col].values
        ax.barh(y_pos, vals, left=bottom, height=0.6, label=label, color=color,
                edgecolor="white", linewidth=0.5)
        # Mostrar valor se > 0.05
        for i, v in enumerate(vals):
            if v > 0.05:
                ax.text(bottom[i] + v/2, y_pos[i], f"{v:.2f}",
                        ha="center", va="center", fontsize=7, color="white",
                        fontweight="bold")
        bottom += vals

    ax.set_yticks(y_pos)
    ax.set_yticklabels(feicoes_labels)
    ax.set_xlabel("Grau de pertinência (μ)")
    ax.set_title("Classificação fuzzy: graus de pertinência por feição", fontweight="bold")
    ax.legend(loc="lower right", fontsize=8)
    ax.set_xlim(0, max(bottom) * 1.05 if max(bottom) > 1 else 1.05)
    ax.invert_yaxis()
    ax.grid(axis="x", alpha=0.3)

    # Adicionar severidade numérica à direita
    for i, sev in enumerate(df_fuzzy["Severidade"].values):
        ax.text(bottom[i] + 0.02, y_pos[i], f"S = {sev}",
                ha="left", va="center", fontsize=8, color="#555")

    fig.tight_layout()
    fig.savefig(os.path.join(OUT_DIR, "fig_S3_pertinencia_feicoes.png"))
    plt.close()
    print("  → fig_S3_pertinencia_feicoes.png")


# ── Fig. S4: Dendrograma + silhouette ─────────────────────────────────────────
def fig_dendrograma():
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(11, 4.5))

    # Dendrograma
    dendrogram(Z, labels=labels_feicoes, ax=ax1, leaf_font_size=10,
               color_threshold=Z[-2, 2] * 0.7,
               above_threshold_color="#888")
    ax1.set_title("Dendrograma (Ward)", fontweight="bold")
    ax1.set_ylabel("Distância euclidiana")
    ax1.set_xlabel("Feição erosiva")

    # Silhouette k=2
    if len(X_scaled) >= 3:
        sil_vals = silhouette_samples(X_scaled, km2.labels_)
        colors_k2 = ["#3498DB", "#E74C3C"]
        y_lower = 0
        for i in range(2):
            cluster_sil = np.sort(sil_vals[km2.labels_ == i])
            size = cluster_sil.shape[0]
            y_upper = y_lower + size
            ax2.fill_betweenx(np.arange(y_lower, y_upper), 0, cluster_sil,
                               facecolor=colors_k2[i], alpha=0.7,
                               edgecolor=colors_k2[i])
            ax2.text(-0.05, y_lower + 0.5 * size,
                      f"C{i+1}", fontsize=9, fontweight="bold")
            y_lower = y_upper + 1

        ax2.axvline(x=sil2, color="#E74C3C", linestyle="--", linewidth=1.2,
                     label=f"Média = {sil2:.3f}")
        ax2.set_xlabel("Coeficiente de silhouette")
        ax2.set_ylabel("Feições")
        ax2.set_title(f"Silhouette (k = 2, média = {sil2:.3f})", fontweight="bold")
        ax2.legend(fontsize=8)
        ax2.set_yticks([])
    else:
        ax2.text(0.5, 0.5, "n insuficiente\npara silhouette",
                  ha="center", va="center", transform=ax2.transAxes)

    fig.tight_layout()
    fig.savefig(os.path.join(OUT_DIR, "fig_S4_dendrograma_silhouette.png"))
    plt.close()
    print("  → fig_S4_dendrograma_silhouette.png")


# ── Fig. S5: Radar comparativo EGC vs. Processo-Funcional ─────────────────────
def fig_radar():
    # Comparar EGC (binária: ravina sim/não, 3 profundidades) vs. Processo-Funcional
    # para 3 feições representativas: F2 (rasa), F4 (intermediária), F5 (profunda)
    feicoes_radar = ["F2", "F4", "F5"]
    categorias = ["Profundidade\n(normalizada)", "Mecanismo\n(nível)", "Vulnerabilidade\n(índice)",
                   "Severidade\nfuzzy", "Indicadores\ncríticos"]

    # Normalizar valores para radar [0, 1]
    dados_radar = {}
    for f in feicoes_radar:
        row_f = feicoes[feicoes["Feicao"] == f].iloc[0]
        row_fz = df_fuzzy[df_fuzzy["Feicao"] == f].iloc[0]
        dados_radar[f] = [
            row_f["Prof_max_m"] / 3.0,                          # prof normalizada 0–3m
            {"Incisão moderada": 0.25, "Saturação-dominante": 0.5,
             "Saturação-dominante + Regressão-dominante": 0.85,
             "Regressão-dominante": 0.7}.get(row_f["Mecanismo"], 0.5),
            {"Baixa": 0.2, "Moderada": 0.5, "Crítica": 0.9}[row_f["Vulnerabilidade"]],
            row_fz["Severidade"] / 100.0,
            row_f["N_criticos"] / 5.0,
        ]

    N = len(categorias)
    angles = np.linspace(0, 2 * np.pi, N, endpoint=False).tolist()
    angles += angles[:1]

    fig, ax = plt.subplots(figsize=(7, 7), subplot_kw=dict(polar=True))
    colors_radar = {"F2": "#3498DB", "F4": "#F39C12", "F5": "#E74C3C"}

    for f in feicoes_radar:
        vals = dados_radar[f] + dados_radar[f][:1]
        ax.plot(angles, vals, "o-", linewidth=2, label=f, color=colors_radar[f])
        ax.fill(angles, vals, alpha=0.12, color=colors_radar[f])

    ax.set_xticks(angles[:-1])
    ax.set_xticklabels(categorias, fontsize=9)
    ax.set_ylim(0, 1)
    ax.set_yticks([0.2, 0.4, 0.6, 0.8, 1.0])
    ax.set_yticklabels(["0.2", "0.4", "0.6", "0.8", "1.0"], fontsize=7, color="#888")
    ax.set_title("Perfil multidimensional: EGC vs. Classificação Processo-Funcional",
                  fontweight="bold", pad=20)
    ax.legend(loc="upper right", bbox_to_anchor=(1.25, 1.1), fontsize=9)

    fig.tight_layout()
    fig.savefig(os.path.join(OUT_DIR, "fig_S5_radar_comparativo.png"))
    plt.close()
    print("  → fig_S5_radar_comparativo.png")


# ── Executar geração de figuras ───────────────────────────────────────────────

# ── Fig. 7: Ábaco de classificação processo-funcional (hachuras) ─────────────
def fig_abaco_classificacao():
    """Ábaco bidimensional com hachuras profissionais (grayscale-safe).

    Zonas delimitadas por contornos S = 30, 55, 80 do sistema fuzzy Mamdani,
    diferenciadas por hachuras progressivas (vazio → pontos → diagonais →
    cruzado) em vez de cor, garantindo legibilidade em escala de cinza.
    """
    import matplotlib.ticker as mticker
    from matplotlib.patches import Patch
    from collections import defaultdict

    # ── Estilo de hachura ─────────────────────────────────────────────────
    _prev_hw = plt.rcParams.get("hatch.linewidth", 1.0)
    _prev_hc = plt.rcParams.get("hatch.color", "black")
    plt.rcParams["hatch.linewidth"] = 0.5
    plt.rcParams["hatch.color"] = "#444444"

    # ── Grid 2-D ──────────────────────────────────────────────────────────
    n = 80
    prof_arr = np.linspace(0.01, 3.0, n)
    vib_arr  = np.linspace(0.01, 10.0, n)
    PP, VV   = np.meshgrid(prof_arr, vib_arr)

    m_al_fix   = 99.2
    p95_fix    = 181.8
    decliv_fix = 12.0

    Z = np.full_like(PP, np.nan)
    for i in range(n):
        for j in range(n):
            try:
                sim = ctrl.ControlSystemSimulation(sistema_ctrl)
                sim.input["profundidade"] = PP[i, j]
                sim.input["vib"]          = VV[i, j]
                sim.input["m_al"]         = m_al_fix
                sim.input["p95"]          = p95_fix
                sim.input["declividade"]  = decliv_fix
                sim.compute()
                Z[i, j] = sim.output["severidade"]
            except Exception:
                Z[i, j] = np.nan

    # ── Figura ────────────────────────────────────────────────────────────
    fig, ax = plt.subplots(figsize=(9, 6.5))

    # 4 zonas discretas: preenchimento cinza claro + hachura progressiva
    zone_levels  = [0, 30, 55, 80, 100]
    zone_fills   = ["white", "#F2F2F2", "#E5E5E5", "#D5D5D5"]
    zone_hatches = ["", "..", "///", "xxx"]
    zone_names   = [
        "Sulco (S < 30)",
        "Ravina estável (30 ≤ S < 55)",
        "Ravina transicional (55 ≤ S < 80)",
        "Voçoroca incipiente (S ≥ 80)",
    ]

    ax.contourf(PP, VV, Z, levels=zone_levels, colors=zone_fills,
                hatches=zone_hatches)

    # Limites entre zonas — linhas pretas contínuas
    cs = ax.contour(PP, VV, Z, levels=[30, 55, 80],
                     colors="black", linewidths=1.4, linestyles="-")
    ax.clabel(cs, inline=True, fontsize=8,
              fmt={30: " S = 30 ", 55: " S = 55 ", 80: " S = 80 "})

    # Rótulos das zonas
    for zx, zy, ztxt, zfs in [
        (0.15, 8.5,  "SULCO",                10),
        (0.55, 5.0,  "RAVINA\nESTÁVEL",       9),
        (1.40, 3.5,  "RAVINA\nTRANSICIONAL",   9),
        (2.40, 1.0,  "VOÇOROCA\nINCIPIENTE",   9),
    ]:
        ax.text(zx, zy, ztxt, fontsize=zfs, fontweight="bold", color="black",
                ha="center", va="center",
                bbox=dict(boxstyle="round,pad=0.3", fc="white", ec="black",
                          alpha=0.9, lw=0.5))

    # ── Feições do inventário ─────────────────────────────────────────────
    markers_map = {"F1": "D", "F2": "o", "F3": "s",
                   "F4": "^", "F5": "v", "F6": "p"}

    # Agrupar feições em posições coincidentes (F3 e F6 se sobrepõem)
    groups = defaultdict(list)
    for _, row in feicoes.iterrows():
        f = row["Feicao"]
        sev = df_fuzzy[df_fuzzy["Feicao"] == f]["Severidade"].values[0]
        key = (round(row["Prof_max_m"], 2), round(row["VIB_cmh"], 2))
        groups[key].append((f, sev, row))

    # Plotar marcadores (preto/branco)
    for _, row in feicoes.iterrows():
        f = row["Feicao"]
        ax.scatter(row["Prof_max_m"], row["VIB_cmh"],
                   s=90, marker=markers_map[f], facecolors="white",
                   edgecolors="black", linewidths=1.3, zorder=5)

    # Anotações com offsets alternados (acima/abaixo) para evitar sobreposição
    stagger_above = True
    for key in sorted(groups.keys()):
        items = groups[key]
        x_pos, y_pos = key
        if len(items) == 1:
            label = f"{items[0][0]} (S = {items[0][1]:.0f})"
        else:
            names = ", ".join(it[0] for it in items)
            label = f"{names} (S = {items[0][1]:.0f})"

        offset_y = 20 if stagger_above else -20
        ax.annotate(label, xy=(x_pos, y_pos),
                    xytext=(0, offset_y), textcoords="offset points",
                    fontsize=7.5, fontweight="bold", ha="center",
                    arrowprops=dict(arrowstyle="->", color="black", lw=0.7))
        stagger_above = not stagger_above

    # ── Legenda com amostras de hachura ───────────────────────────────────
    legend_patches = [
        Patch(facecolor=f, hatch=h, edgecolor="black", lw=0.5, label=n)
        for f, h, n in zip(zone_fills, zone_hatches, zone_names)
    ]
    ax.legend(handles=legend_patches, loc="upper right", fontsize=8,
              framealpha=0.95, edgecolor="black", fancybox=False,
              title="Zona diagnóstica", title_fontsize=9)

    # ── Eixos ─────────────────────────────────────────────────────────────
    ax.set_xlabel("Profundidade máxima (m)", fontsize=11, fontweight="bold")
    ax.set_ylabel("VIB (cm h$^{-1}$)", fontsize=11, fontweight="bold")
    ax.set_xlim(0, 3.0)
    ax.set_ylim(0, 10.0)
    ax.xaxis.set_minor_locator(mticker.AutoMinorLocator(2))
    ax.yaxis.set_minor_locator(mticker.AutoMinorLocator(2))
    ax.tick_params(which="both", direction="in", top=True, right=True)
    ax.grid(which="major", alpha=0.2, linestyle=":", color="gray")

    # Referência EGC (limiar 3 m)
    ax.axvline(x=3.0, color="#888", linestyle=":", lw=1.0, alpha=0.5)
    ax.text(2.85, 9.5, "Limiar EGC\n(3 m)", fontsize=7, color="#888",
            ha="right", va="top", fontstyle="italic")

    # Nota de rodapé
    ax.text(0.01, -0.09,
            f"Variáveis fixadas: m(Al) = {m_al_fix}%, "
            f"P95 = {p95_fix} mm/mês, declividade = {decliv_fix}%\n"
            "Contornos: limiares de transição entre classes fuzzy Mamdani "
            "(centróide)",
            transform=ax.transAxes, fontsize=7.5, color="#555", va="top")

    fig.tight_layout()
    fig.savefig(os.path.join(OUT_DIR, "fig_abaco_classificacao.png"),
                bbox_inches="tight", pad_inches=0.3, dpi=300)
    plt.close()

    # restaurar rcParams
    plt.rcParams["hatch.linewidth"] = _prev_hw
    plt.rcParams["hatch.color"] = _prev_hc
    print("  → fig_abaco_classificacao.png")


print("Gerando figuras do Material Suplementar...")
fig_fluxograma()
fig_pertinencia()
fig_pertinencia_feicoes()
fig_dendrograma()
fig_radar()
fig_abaco_classificacao()
print("\nTodas as figuras salvas em:", OUT_DIR)


# =============================================================================
# 6. TABELA RESUMO COMPARATIVA (para o texto suplementar)
# =============================================================================
print("\n" + "=" * 80)
print("TABELA COMPARATIVA — EGC vs. CLASSIFICAÇÃO PROCESSO-FUNCIONAL")
print("=" * 80)

tabela_comp = feicoes[["Feicao", "Prof_max_m", "Nivel1", "Vulnerabilidade"]].merge(
    df_fuzzy[["Feicao", "Severidade", "Classe_dominante"]], on="Feicao"
)
# EGC original (do manuscrito Tab. 1)
egc_classes = {
    "F1": "Ravina mod. profunda",
    "F2": "Ravina rasa",
    "F3": "Ravina rasa",
    "F4": "Ravina mod. profunda",
    "F5": "Ravina profunda",
    "F6": "Ravina rasa",
}
tabela_comp["EGC_original"] = tabela_comp["Feicao"].map(egc_classes)
tabela_comp = tabela_comp[["Feicao", "Prof_max_m", "EGC_original",
                            "Nivel1", "Vulnerabilidade", "Severidade", "Classe_dominante"]]
tabela_comp.columns = ["Feição", "Prof. (m)", "EGC original",
                         "Nível 1", "Vulnerabilidade", "Severidade fuzzy", "Classe fuzzy"]
print(tabela_comp.to_string(index=False))
