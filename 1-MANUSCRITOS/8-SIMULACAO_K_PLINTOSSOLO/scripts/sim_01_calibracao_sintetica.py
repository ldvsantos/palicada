"""
Simulação 01 -- Calibração Sintética.
Testa se o protocolo sequencial de 4 etapas recupera parâmetros conhecidos
a partir de dados ruidosos (56 parcelas, 3 classes de solo).
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))

import numpy as np
from scipy.optimize import least_squares
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

from config_simulacao import (
    TRUE_PARAMS, VIB_REF, M0,
    alpha, beta, gamma, delta_model,
    gerar_parcelas, FIG_DIR,
)

np.random.seed(2026)


def gerar_delta_obs(vib, m, h_hc, cv, params):
    """Gera delta_obs = delta_true x (1 + ruído), com ruído ~ N(0, cv)."""
    d_true = delta_model(vib, m, h_hc, **params)
    ruido = 1.0 + np.random.normal(0, cv, size=d_true.shape)
    return d_true * np.clip(ruido, 0.3, 3.0), d_true


def calibrar_sequencial(vib, m, h_hc, classe, d_obs):
    """Protocolo sequencial de 4 etapas (§4.5 do manuscrito)."""

    # Etapa 1: verificação controle negativo (Latossolo delta ~ 1)
    mask_lat = classe == 'latossolo'
    delta_lat_mean = np.mean(d_obs[mask_lat])

    # Etapa 2: calibração marginal de alpha via Argissolo
    mask_arg = classe == 'argissolo'
    vib_arg = vib[mask_arg]
    d_arg = d_obs[mask_arg]
    # delta_arg ~ alpha(VIB) x beta(m_arg~30-45) x gamma(H/Hc~0)
    # Como beta e gamma são ~1 no Argissolo, delta_arg ~ alpha
    def res_alpha(p):
        n1 = p[0]
        return alpha(vib_arg, n1) - d_arg
    sol_a = least_squares(res_alpha, [0.5], bounds=([0.01], [5.0]))
    n1_est = sol_a.x[0]

    # Etapa 3: calibração de beta via Plintossolo (Ap vs BAc exposto)
    mask_plint = classe == 'plintossolo'
    vib_p = vib[mask_plint]
    m_p = m[mask_plint]
    h_hc_p = h_hc[mask_plint]
    d_p = d_obs[mask_plint]
    # Remover efeito de alpha já calibrado
    d_corr_alpha = d_p / alpha(vib_p, n1_est)
    # E gamma ~ 1 + k3*(H/Hc)^n3, mas estimar beta antes de gamma
    # Aproximar gamma ~ 1 para esta etapa (H/Hc baixo em muitas parcelas)
    def res_beta(p):
        bmax, k2_ = p
        return beta(m_p, bmax, k2_) - d_corr_alpha
    sol_b = least_squares(res_beta, [2.0, 0.05],
                          bounds=([1.01, 0.001], [10.0, 1.0]))
    bmax_est, k2_est = sol_b.x

    # Etapa 4: calibração de gamma via Plintossolo (resíduo)
    d_residual = d_corr_alpha / beta(m_p, bmax_est, k2_est)
    def res_gamma(p):
        k3_, n3_ = p
        return gamma(h_hc_p, k3_, n3_) - d_residual
    sol_g = least_squares(res_gamma, [2.0, 2.0],
                          bounds=([0.1, 0.5], [20.0, 5.0]))
    k3_est, n3_est = sol_g.x

    # Calibração simultânea final (Levenberg-Marquardt, todos os sítios)
    def res_total(p):
        n1_, bmax_, k2__, k3__, n3__ = p
        d_pred = delta_model(vib, m, h_hc, n1_, bmax_, k2__, k3__, n3__)
        return d_pred - d_obs

    x0 = [n1_est, bmax_est, k2_est, k3_est, n3_est]
    sol_final = least_squares(res_total, x0,
                              bounds=([0.01, 1.01, 0.001, 0.1, 0.5],
                                      [5.0, 10.0, 1.0, 20.0, 5.0]))

    return dict(
        n1=sol_final.x[0],
        beta_max=sol_final.x[1],
        k2=sol_final.x[2],
        k3=sol_final.x[3],
        n3=sol_final.x[4],
        delta_lat_mean=delta_lat_mean,
        etapas=dict(n1_seq=n1_est, bmax_seq=bmax_est,
                    k2_seq=k2_est, k3_seq=k3_est, n3_seq=n3_est),
    )


def main():
    vib, m, h_hc, classe, k_r = gerar_parcelas()
    n_parcelas = len(vib)
    print(f"Parcelas geradas: {n_parcelas}")

    cvs = [0.10, 0.15, 0.20, 0.25, 0.30]
    n_rep = 30
    resultados = {cv: [] for cv in cvs}

    for cv in cvs:
        for _ in range(n_rep):
            d_obs, _ = gerar_delta_obs(vib, m, h_hc, cv, TRUE_PARAMS)
            est = calibrar_sequencial(vib, m, h_hc, classe, d_obs)
            resultados[cv].append(est)

    # ── Tabela de resultados ────────────────────────────────────────
    print("\n" + "=" * 80)
    print(f"CALIBRAÇÃO SINTÉTICA -- RECUPERAÇÃO DE PARÂMETROS ({n_rep} repetições)")
    print("=" * 80)
    params_nomes = ['n1', 'beta_max', 'k2', 'k3', 'n3']
    true_vals = [TRUE_PARAMS[p] for p in params_nomes]

    print(f"{'CV':>6} | ", end='')
    for p in params_nomes:
        print(f"  {p:>10} (true={TRUE_PARAMS[p]:.2f})", end='')
    print(f"  |  delta_Lat (~1.0)")
    print("-" * 100)

    tabela_bias = {}
    for cv in cvs:
        ests = resultados[cv]
        medians = {p: np.median([e[p] for e in ests]) for p in params_nomes}
        iqr25 = {p: np.percentile([e[p] for e in ests], 25) for p in params_nomes}
        iqr75 = {p: np.percentile([e[p] for e in ests], 75) for p in params_nomes}
        d_lat = np.median([e['delta_lat_mean'] for e in ests])

        print(f"{cv:>6.0%} | ", end='')
        for p in params_nomes:
            print(f"  {medians[p]:>6.3f} [{iqr25[p]:.2f}-{iqr75[p]:.2f}]", end='')
        print(f"  |  {d_lat:.3f}")

        tabela_bias[cv] = {p: abs(medians[p] - TRUE_PARAMS[p]) / TRUE_PARAMS[p]
                           for p in params_nomes}

    # ── Figura: viés relativo vs CV ─────────────────────────────────
    # Nomes descritivos para legenda
    param_labels = {
        'n1': '$n_1$ (hydraulic exponent)',
        'beta_max': r'$\beta_{max}$ (max. toxicity amplification)',
        'k2': '$k_2$ (sigmoid transition rate)',
        'k3': '$k_3$ (slope amplification scale)',
        'n3': '$n_3$ (slope response curvature)',
    }

    fig, ax = plt.subplots(figsize=(8, 5))
    for p in params_nomes:
        biases = [tabela_bias[cv][p] * 100 for cv in cvs]
        ax.plot([cv * 100 for cv in cvs], biases, 'o-',
                label=param_labels[p], linewidth=2)

    ax.set_xlabel('Coefficient of variation of noise (%)', fontsize=12)
    ax.set_ylabel('Median relative bias (%)', fontsize=12)
    ax.set_title('Parameter recovery -- Synthetic calibration of K$_{plint}$',
                 fontsize=13)
    ax.legend(fontsize=9)
    ax.grid(True, alpha=0.3)
    ax.set_ylim(bottom=0)
    fig.tight_layout()
    fig.savefig(FIG_DIR / 'fig_01_calibracao_sintetica.png', dpi=300)
    print(f"\nFigura salva: {FIG_DIR / 'fig_01_calibracao_sintetica.png'}")

    # ── Figura: boxplot por CV para cada parâmetro ──────────────────
    # Títulos descritivos para cada subplot do boxplot
    param_titulos_box = {
        'n1': '$n_1$ -- hydraulic exponent',
        'beta_max': r'$\beta_{max}$ -- max. toxicity amplification',
        'k2': '$k_2$ -- sigmoid transition rate',
        'k3': '$k_3$ -- slope amplification scale',
        'n3': '$n_3$ -- slope response curvature',
    }

    fig2, axes = plt.subplots(1, 5, figsize=(18, 5), sharey=False)
    for i, p in enumerate(params_nomes):
        data = [[e[p] for e in resultados[cv]] for cv in cvs]
        bp = axes[i].boxplot(data, tick_labels=[f'{cv:.0%}' for cv in cvs],
                             patch_artist=True)
        for patch in bp['boxes']:
            patch.set_facecolor('#4C72B0')
            patch.set_alpha(0.6)
        axes[i].axhline(TRUE_PARAMS[p], color='red', linestyle='--',
                        linewidth=1.5, label=f'True = {TRUE_PARAMS[p]:.2f}')
        axes[i].set_title(param_titulos_box[p], fontsize=11, fontweight='bold')
        axes[i].set_xlabel('Noise CV')
        axes[i].legend(fontsize=8)
        axes[i].grid(True, alpha=0.3)

    fig2.suptitle('Distribution of estimated parameters by noise level',
                  fontsize=14, fontweight='bold')
    fig2.tight_layout()
    fig2.savefig(FIG_DIR / 'fig_02_boxplot_parametros.png', dpi=300)
    print(f"Figura salva: {FIG_DIR / 'fig_02_boxplot_parametros.png'}")

    plt.close('all')


if __name__ == '__main__':
    main()
