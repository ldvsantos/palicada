"""
Simulação 04 — Modelo de Infiltração e Geração de Escoamento (Green-Ampt).
Valida α(VIB) modelando perfis de solo em camadas sob eventos de chuva
com diferentes intensidades (I30). Quantifica excedente hortoniano e
correlaciona com o fator α proposto.
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))

import numpy as np
from scipy.optimize import curve_fit
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

from config_simulacao import (
    PLINTOSSOLO, LATOSSOLO, ARGISSOLO, SOLOS,
    alpha, VIB_REF, FIG_DIR, DISPLAY_NAME,
)


def green_ampt_infiltracao(I_mm_h, Ksat_cm_h, psi_cm=20.0,
                           theta_s=0.45, theta_i=0.20, dt_min=5.0,
                           duracao_min=60.0):
    """
    Modelo Green-Ampt simplificado para evento único.
    Retorna: infiltração acumulada (mm) e escoamento acumulado (mm).

    Parameters
    ----------
    I_mm_h : float  — intensidade de chuva constante (mm/h)
    Ksat_cm_h : float — condutividade hidráulica saturada (cm/h)
    psi_cm : float — sucção na frente de umedecimento (cm)
    theta_s, theta_i : float — umidade saturada e inicial
    dt_min : float — passo de tempo (min)
    duracao_min : float — duração do evento (min)
    """
    Ksat_mm_h = Ksat_cm_h * 10.0  # cm/h → mm/h
    psi_mm = psi_cm * 10.0
    delta_theta = theta_s - theta_i

    n_steps = int(duracao_min / dt_min)
    dt_h = dt_min / 60.0

    F_cum = 0.0  # infiltração acumulada (mm)
    R_cum = 0.0  # escoamento acumulado (mm)
    f_series = []
    r_series = []
    t_series = []

    # Tempo de alagamento (ponding time)
    tp = Ksat_mm_h * psi_mm * delta_theta / (I_mm_h * (I_mm_h - Ksat_mm_h)) \
        if I_mm_h > Ksat_mm_h else np.inf

    for step in range(n_steps):
        t = step * dt_h
        t_series.append(t * 60)

        if t < tp / 60.0 * dt_min:  # Antes do alagamento
            f_inst = I_mm_h
            runoff = 0.0
        else:
            # Capacidade de infiltração Green-Ampt
            if F_cum > 0:
                f_cap = Ksat_mm_h * (1.0 + psi_mm * delta_theta / F_cum)
            else:
                f_cap = I_mm_h
            f_inst = min(I_mm_h, f_cap)
            runoff = max(0, I_mm_h - f_inst)

        F_cum += f_inst * dt_h
        R_cum += runoff * dt_h
        f_series.append(f_inst)
        r_series.append(runoff)

    return F_cum, R_cum, np.array(t_series), np.array(f_series), np.array(r_series)


def simular_perfil(solo_dict, I_range, duracao=60.0):
    """
    Simula escoamento para um perfil de solo com Ksat efetivo.
    O Ksat efetivo é o mínimo entre horizontes (impedância governa).
    """
    Ksat_horizons = list(solo_dict['Ksat_cm_h'].values())
    Ksat_eff = min(Ksat_horizons)  # horizonte limitante
    VIB_vals = list(solo_dict['VIB'].values())
    VIB_mean = np.mean(VIB_vals)

    resultados = []
    for I in I_range:
        F, R, t, f, r = green_ampt_infiltracao(
            I_mm_h=I, Ksat_cm_h=Ksat_eff,
            duracao_min=duracao
        )
        resultados.append(dict(
            I_mm_h=I, F_mm=F, R_mm=R,
            coef_esc=R / (I * duracao / 60.0) if I > 0 else 0,
            Ksat_eff=Ksat_eff, VIB_mean=VIB_mean,
        ))
    return resultados


def main():
    I_range = np.arange(5, 105, 5)  # mm/h (I30 de 5 a 100)
    duracao = 60.0  # min

    solos_nomes = ['plintossolo', 'latossolo', 'argissolo']
    solos_dicts = [PLINTOSSOLO, LATOSSOLO, ARGISSOLO]
    cores = ['#C44E52', '#4C72B0', '#55A868']

    resultados_por_solo = {}
    for nome, solo_d in zip(solos_nomes, solos_dicts):
        resultados_por_solo[nome] = simular_perfil(solo_d, I_range, duracao)

    # ── Tabela resumo ───────────────────────────────────────────────
    print("=" * 70)
    print("INFILTRAÇÃO E ESCOAMENTO (Green-Ampt) — RESUMO POR CLASSE")
    print("=" * 70)
    print(f"{'Solo':>15}  {'Ksat_eff':>8}  {'VIB_med':>7}  "
          f"{'CE(I30=30)':>10}  {'CE(I30=60)':>10}  {'CE(I30=90)':>10}")
    for nome in solos_nomes:
        res = resultados_por_solo[nome]
        Ksat = res[0]['Ksat_eff']
        VIB = res[0]['VIB_mean']
        ce30 = next(r['coef_esc'] for r in res if r['I_mm_h'] == 30)
        ce60 = next(r['coef_esc'] for r in res if r['I_mm_h'] == 60)
        ce90 = next(r['coef_esc'] for r in res if r['I_mm_h'] == 90)
        print(f"{nome:>15}  {Ksat:>8.2f}  {VIB:>7.2f}  "
              f"{ce30:>10.3f}  {ce60:>10.3f}  {ce90:>10.3f}")

    # ── Correlação CE com α(VIB) ────────────────────────────────────
    print(f"\n{'='*70}")
    print("CORRELAÇÃO: Coeficiente de Escoamento vs α(VIB)")
    print(f"{'='*70}")

    # Para I30 = 60 mm/h (evento moderado-alto)
    ce_60 = {}
    vib_medios = {}
    for nome in solos_nomes:
        res = resultados_por_solo[nome]
        ce_60[nome] = next(r['coef_esc'] for r in res if r['I_mm_h'] == 60)
        vib_medios[nome] = res[0]['VIB_mean']

    # α com diferentes n1
    for n1_test in [0.5, 1.0, 1.5, 2.0]:
        print(f"\n  n1 = {n1_test}:")
        for nome in solos_nomes:
            a_val = float(alpha(vib_medios[nome], n1_test))
            print(f"    {nome:>15}: α = {a_val:.3f}, CE = {ce_60[nome]:.3f}, "
                  f"razão CE/CE_lat = {ce_60[nome]/max(ce_60['latossolo'],1e-6):.2f}")

    # ── Figura 1: Coeficiente de escoamento vs I30 ──────────────────
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))

    for nome, cor in zip(solos_nomes, cores):
        res = resultados_por_solo[nome]
        I_vals = [r['I_mm_h'] for r in res]
        CE_vals = [r['coef_esc'] for r in res]
        Ksat = res[0]['Ksat_eff']
        ax1.plot(I_vals, CE_vals, 'o-', color=cor, linewidth=2, markersize=4,
                 label=f'{DISPLAY_NAME[nome]} (K$_{{sat,eff}}$={Ksat:.2f} cm/h)')

    ax1.set_xlabel('Maximum 30-min intensity, $I_{30}$ (mm/h)', fontsize=12)
    ax1.set_ylabel('Runoff coefficient (RC)', fontsize=12)
    ax1.set_title('Surface runoff generation\n(Green\u2013Ampt, 60-min event)',
                  fontsize=12)
    ax1.text(-0.05, 1.12, '(a)', transform=ax1.transAxes,
             fontsize=14, fontweight='bold', va='top')
    ax1.legend(fontsize=10)
    ax1.grid(True, alpha=0.3)
    ax1.set_ylim(0, 1)

    # ── Figura 2: α teórico vs razão CE observada ───────────────────
    # Para cada solo e I30, calcular razão de CE relativa ao Latossolo
    I_plot = [30, 45, 60, 75, 90]
    for nome, cor in zip(['plintossolo', 'argissolo'], cores[:2]):
        vibs = list(SOLOS[nome]['VIB'].values())
        vib_med = np.mean(vibs)
        razoes = []
        for I in I_plot:
            ce_solo = next(r['coef_esc'] for r in resultados_por_solo[nome]
                           if r['I_mm_h'] == I)
            ce_lat = next(r['coef_esc'] for r in resultados_por_solo['latossolo']
                          if r['I_mm_h'] == I)
            razoes.append(ce_solo / max(ce_lat, 0.001))
        ax2.plot(I_plot, razoes, 's-', color=cor, linewidth=2, markersize=8,
                 label=f'{DISPLAY_NAME[nome]} (mean BIR = {vib_med:.1f} cm/h)')

    # α teórico para referência
    for n1_t, ls in [(0.5, ':'), (1.0, '--'), (1.5, '-.')]:
        for nome, cor in zip(['plintossolo', 'argissolo'], cores[:2]):
            vib_med = np.mean(list(SOLOS[nome]['VIB'].values()))
            a_val = float(alpha(vib_med, n1_t))
            ax2.axhline(a_val, color=cor, linestyle=ls, alpha=0.4)
        ax2.plot([], [], 'k' + ls, label=f'$\\alpha$ teórico ($n_1$={n1_t})')

    ax2.set_xlabel('Maximum 30-min intensity, $I_{30}$ (mm/h)', fontsize=12)
    ax2.set_ylabel('RC$_{soil}$ / RC$_{Ferralsol}$ ratio', fontsize=12)
    ax2.set_title('Validation of hydraulic amplification factor\n'
                  '$\\alpha$(BIR) by hydrological modeling', fontsize=12)
    ax2.text(-0.05, 1.12, '(b)', transform=ax2.transAxes,
             fontsize=14, fontweight='bold', va='top')
    ax2.legend(fontsize=9, ncol=2)
    ax2.grid(True, alpha=0.3)

    fig.tight_layout()
    fig.savefig(FIG_DIR / 'fig_06_infiltracao_escoamento.png', dpi=300)
    print(f"\nFigura salva: {FIG_DIR / 'fig_06_infiltracao_escoamento.png'}")

    # ── Figura 3: Hidrograma para I30 = 60 mm/h ────────────────────
    fig3, ax3 = plt.subplots(figsize=(8, 5))
    for nome, cor in zip(solos_nomes, cores):
        solo_d = SOLOS[nome]
        Ksat_eff = min(solo_d['Ksat_cm_h'].values())
        _, _, t, f, r = green_ampt_infiltracao(
            I_mm_h=60, Ksat_cm_h=Ksat_eff, duracao_min=duracao
        )
        ax3.plot(t, r, '-', color=cor, linewidth=2,
                 label=f'{DISPLAY_NAME[nome]} (K$_{{sat,eff}}$={Ksat_eff:.2f} cm/h)')
        ax3.fill_between(t, 0, r, color=cor, alpha=0.15)

    ax3.axhline(60, color='gray', linestyle=':', label='$I_{30}$ = 60 mm/h (applied intensity)')
    ax3.set_xlabel('Time (min)', fontsize=12)
    ax3.set_ylabel('Surface runoff intensity (mm/h)', fontsize=12)
    ax3.set_title('Surface runoff hydrograph \u2014 $I_{30}$ = 60 mm/h',
                  fontsize=12)
    ax3.legend(fontsize=10)
    ax3.grid(True, alpha=0.3)
    fig3.tight_layout()
    fig3.savefig(FIG_DIR / 'fig_07_hidrograma_i60.png', dpi=600)
    print(f"Figura salva: {FIG_DIR / 'fig_07_hidrograma_i60.png'}")

    plt.close('all')


if __name__ == '__main__':
    main()
