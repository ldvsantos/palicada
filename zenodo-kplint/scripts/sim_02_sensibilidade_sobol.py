"""
Simulação 02 — Análise de Sensibilidade Global (Sobol).
Quantifica a contribuição de cada parâmetro livre à variância de δ
para cada classe de solo e para o conjunto.
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))

import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from SALib.sample import saltelli
from SALib.analyze import sobol

from config_simulacao import (
    delta_model, gerar_parcelas, FIG_DIR, PLINTOSSOLO, LATOSSOLO, ARGISSOLO,
)

np.random.seed(2026)


def main():
    # ── Definição do problema Sobol ─────────────────────────────────
    problem = {
        'num_vars': 5,
        'names': ['n1', 'beta_max', 'k2', 'k3', 'n3'],
        'bounds': [
            [0.1, 3.0],     # n1
            [1.1, 5.0],     # beta_max
            [0.01, 0.50],   # k2
            [0.5, 10.0],    # k3
            [1.0, 4.0],     # n3
        ],
    }

    N = 1024
    param_samples = saltelli.sample(problem, N, calc_second_order=True)
    print(f"Amostras Saltelli geradas: {param_samples.shape[0]}")

    # ── Avaliar δ para condições representativas de cada classe ─────
    cenarios = {
        'Plintossolo\n(VIB=1,53 cm/h, m$_{Al}$=84%, H/H$_c$=0,33)': (1.53, 84.0, 0.33),
        'Plintossolo\n(VIB=3,13 cm/h, m$_{Al}$=15%, H/H$_c$=0,12)': (3.13, 15.2, 0.12),
        'Argissolo\n(VIB=2,5 cm/h, m$_{Al}$=45%, H/H$_c$=0,08)':    (2.50, 45.0, 0.08),
        'Latossolo\n(VIB=9,0 cm/h, m$_{Al}$=20%, H/H$_c$=0)':     (9.00, 20.0, 0.00),
    }

    resultados_sobol = {}
    for nome, (vib, m_al, h_hc) in cenarios.items():
        # Vetorizado: passa arrays inteiros para delta_model
        Y = delta_model(
            vib, m_al, h_hc,
            param_samples[:, 0], param_samples[:, 1],
            param_samples[:, 2], param_samples[:, 3],
            param_samples[:, 4]
        ).ravel()
        Si = sobol.analyze(problem, Y, calc_second_order=True,
                           print_to_console=False)
        resultados_sobol[nome] = Si
        print(f"\n{'='*60}")
        print(f"Cenário: {nome.replace(chr(10), ' ')}")
        print(f"{'='*60}")
        print(f"{'Parâmetro':>12}  {'S1':>8}  {'ST':>8}  {'S1_conf':>10}")
        for i, p in enumerate(problem['names']):
            print(f"{p:>12}  {Si['S1'][i]:>8.4f}  {Si['ST'][i]:>8.4f}  "
                  f"±{Si['S1_conf'][i]:.4f}")

    # ── Figura: barras S1 e ST por cenário ──────────────────────────
    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
    colors_s1 = '#4C72B0'
    colors_st = '#DD8452'
    bar_width = 0.35

    # Labels descritivos para eixos x das barras
    param_labels_sobol = [
        '$n_1$\n(expoente\nhidráulico)',
        r'$\beta_{max}$' + '\n(amplif. máx.\ntoxicidade)',
        '$k_2$\n(taxa transição\nsigmoide)',
        '$k_3$\n(escala amplif.\ntalude)',
        '$n_3$\n(curvatura\nresp. talude)',
    ]

    panel_labels = ['(a)', '(b)', '(c)', '(d)']
    for idx, (ax, (nome, Si)) in enumerate(zip(axes.flat, resultados_sobol.items())):
        x = np.arange(len(problem['names']))
        bars1 = ax.bar(x - bar_width/2, Si['S1'], bar_width,
                       label='$S_1$ (1ª ordem)', color=colors_s1, alpha=0.8,
                       yerr=Si['S1_conf'], capsize=3)
        bars2 = ax.bar(x + bar_width/2, Si['ST'], bar_width,
                       label='$S_T$ (total)', color=colors_st, alpha=0.8,
                       yerr=Si['ST_conf'], capsize=3)
        ax.set_xticks(x)
        ax.set_xticklabels(param_labels_sobol, fontsize=8)
        ax.set_title(nome, fontsize=10, fontweight='bold')
        ax.text(-0.05, 1.12, panel_labels[idx], transform=ax.transAxes,
                fontsize=14, fontweight='bold', va='top')
        ax.set_ylim(0, 1.1)
        ax.axhline(0.1, color='gray', linestyle=':', alpha=0.5)
        ax.legend(fontsize=9)
        ax.grid(True, alpha=0.2, axis='y')

    fig.suptitle('Análise de sensibilidade global (Sobol) — Índices $S_1$ (1ª ordem) e $S_T$ (total)',
                 fontsize=14, fontweight='bold')
    fig.tight_layout()
    fig.savefig(FIG_DIR / 'fig_03_sensibilidade_sobol.png', dpi=300)
    print(f"\nFigura salva: {FIG_DIR / 'fig_03_sensibilidade_sobol.png'}")

    # ── Figura: heatmap de interações S2 (Plintossolo intermediário) ─
    nome_plint = list(cenarios.keys())[0]
    Si_plint = resultados_sobol[nome_plint]
    s2_matrix = np.zeros((5, 5))
    for i in range(5):
        for j in range(5):
            if i != j:
                s2_matrix[i, j] = Si_plint['S2'][i, j]

    # Labels descritivos para heatmap
    param_labels_s2 = [
        '$n_1$\n(hidráulico)',
        r'$\beta_{max}$' + '\n(toxicidade)',
        '$k_2$\n(sigmoide)',
        '$k_3$\n(talude)',
        '$n_3$\n(curvatura)',
    ]

    fig3, ax3 = plt.subplots(figsize=(7, 6))
    im = ax3.imshow(s2_matrix, cmap='YlOrRd', vmin=0)
    ax3.set_xticks(range(5))
    ax3.set_yticks(range(5))
    ax3.set_xticklabels(param_labels_s2, fontsize=9)
    ax3.set_yticklabels(param_labels_s2, fontsize=9)
    for i in range(5):
        for j in range(5):
            if i != j:
                ax3.text(j, i, f'{s2_matrix[i,j]:.3f}',
                         ha='center', va='center', fontsize=10)
    plt.colorbar(im, ax=ax3, label='Índice $S_2$ (interação de 2ª ordem)')
    ax3.set_title('Interações entre parâmetros — Plintossolo intermediário\n'
                  '(VIB = 1,53 cm/h, m$_{Al}$ = 84%, H/H$_c$ = 0,33)',
                  fontsize=12, fontweight='bold')
    fig3.tight_layout()
    fig3.savefig(FIG_DIR / 'fig_04_interacoes_s2.png', dpi=300)
    print(f"Figura salva: {FIG_DIR / 'fig_04_interacoes_s2.png'}")

    plt.close('all')


if __name__ == '__main__':
    main()
