"""
Simulação 05 — Modelo de Erosão Virtual (WEPP/USLE-M simplificado).
Gera escoamento (Green-Ampt) → tensão cisalhante → destacamento →
inversão de K_obs → comparação δ_obs com δ_model(K_plint).

Valida a Eq. 8 como preditor integrado de perda de solo entre classes.
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))

import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

from config_simulacao import (
    PLINTOSSOLO, LATOSSOLO, ARGISSOLO, SOLOS, K_RUSLE,
    TRUE_PARAMS, delta_model, alpha, beta, gamma,
    VIB_REF, FIG_DIR, DISPLAY_NAME,
)

# ── Parâmetros físicos gerais ───────────────────────────────────────
RHO_W = 1000.0       # kg/m³
G = 9.81             # m/s²
SLOPE_M_M = 0.12     # m/m (declividade ~12%, típica das parcelas Wischmeier)
LARGURA_PARCELA = 3.5  # m  (parcela padrão)
COMPRIMENTO = 22.13   # m  (parcela Wischmeier)
MANNING_N = 0.03      # s/m^(1/3)  solo exposto

# Parâmetros de erodibilidade intrínseca do solo (k_r, τ_c)
# Estimativas baseadas em literatura para solos tropicais
SOLOS_EROD = dict(
    plintossolo=dict(k_r=0.008, tau_c=1.5),   # menos coeso, baixa VIB
    latossolo=dict(k_r=0.003, tau_c=3.5),      # agregação óxidos Fe/Al
    argissolo=dict(k_r=0.005, tau_c=2.0),      # intermediário
)


def green_ampt_runoff(I_mm_h, Ksat_eff_cm_h, duracao_min=60.0, dt_min=1.0,
                      psi_cm=20.0, theta_s=0.45, theta_i=0.20):
    """Retorna lâmina de escoamento acumulado (mm) para evento constante."""
    Ksat_mm = Ksat_eff_cm_h * 10.0
    psi_mm = psi_cm * 10.0
    dtheta = theta_s - theta_i
    dt_h = dt_min / 60.0
    n_steps = int(duracao_min / dt_min)

    F = 0.0
    R = 0.0
    for _ in range(n_steps):
        if F > 0:
            f_cap = Ksat_mm * (1.0 + psi_mm * dtheta / F)
        else:
            f_cap = I_mm_h
        f_inst = min(I_mm_h, f_cap)
        runoff = max(0, I_mm_h - f_inst)
        F += f_inst * dt_h
        R += runoff * dt_h
    return R  # mm


def calcular_erosao(I_mm_h, Ksat_eff, k_r, tau_c, duracao_min=60.0):
    """
    Modelo simplificado de destacamento por escoamento.
    Retorna perda de solo (t/ha) para um evento.

    Cadeia: chuva → escoamento (Green-Ampt) → profundidade de lâmina →
    tensão cisalhante → destacamento → transporte.
    """
    R_mm = green_ampt_runoff(I_mm_h, Ksat_eff, duracao_min)
    if R_mm <= 0:
        return 0.0, R_mm, 0.0

    # Lâmina de escoamento (m) — regime uniforme em parcela
    R_m = R_mm / 1000.0  # depth (m)
    q = R_m / (duracao_min * 60.0) * COMPRIMENTO  # m³/s/m (vazão unitária estabilizada)

    # Profundidade normal (Manning): h = (n*q / S^0.5)^(3/5)
    h_flow = (MANNING_N * q / SLOPE_M_M ** 0.5) ** 0.6  # m

    # Tensão cisalhante: τ = ρ g h S
    tau = RHO_W * G * h_flow * SLOPE_M_M  # Pa

    # Destacamento (kg/m²/s) — modelo WEPP simplificado
    if tau > tau_c:
        D = k_r * (tau - tau_c)
    else:
        D = 0.0

    # Perda total na parcela (t/ha)
    A_parcela = LARGURA_PARCELA * COMPRIMENTO  # m²
    perda_kg = D * A_parcela * (duracao_min * 60.0)  # kg
    perda_t_ha = perda_kg / A_parcela * 10000 / 1000  # t/ha

    return perda_t_ha, R_mm, tau


def inverter_K_obs(perda_t_ha, R_mm, I_mm_h, duracao_min=60.0):
    """
    Inverte K_obs pela USLE-M simplificada.
    K_obs = A / (R_factor * LS * C * P)
    Assumindo LS, C=1, P=1 para solo exposto em parcela padrão.

    R_factor ~ EI30: produto da energia cinética pela I30 (MJ mm / ha h)
    Usamos a relação de Wischmeier: E = 0.119 + 0.0873 * log10(I), unidades SI.
    """
    if perda_t_ha <= 0:
        return 0.0

    # E unitária (MJ / ha / mm) — Wischmeier & Smith 1978
    I_val = max(I_mm_h, 0.1)
    e_unit = 0.119 + 0.0873 * np.log10(I_val)  # MJ/(ha·mm)

    # Chuva total (mm) e EI30
    P_mm = I_mm_h * duracao_min / 60.0
    EI30 = e_unit * P_mm * I_mm_h  # MJ mm / (ha h)

    # LS fator para parcela Wischmeier (22.13 m, ~12%)
    LS = 1.0  # Parcela padrão = LS = 1 por definição

    K_obs = perda_t_ha / (EI30 * LS)  # t h / (MJ mm)
    return K_obs


def main():
    I_range = np.arange(10, 105, 5)  # mm/h
    duracao = 60.0  # min

    solos_nomes = ['plintossolo', 'latossolo', 'argissolo']
    cores = ['#C44E52', '#4C72B0', '#55A868']
    markers = ['o', 's', '^']

    # ── Simulação por classe ────────────────────────────────────────
    resultados = {n: [] for n in solos_nomes}
    for nome in solos_nomes:
        solo = SOLOS[nome]
        Ksat_eff = min(solo['Ksat_cm_h'].values())
        k_r = SOLOS_EROD[nome]['k_r']
        tau_c = SOLOS_EROD[nome]['tau_c']

        for I in I_range:
            perda, R_mm, tau = calcular_erosao(I, Ksat_eff, k_r, tau_c, duracao)
            K_obs = inverter_K_obs(perda, R_mm, I, duracao)
            delta_obs = K_obs / K_RUSLE[nome] if K_RUSLE[nome] > 0 else 1.0

            # δ modelo (com parâmetros verdadeiros)
            vibs = list(solo['VIB'].values())
            vib_med = np.mean(vibs)
            m_vals = list(solo['m_Al'].values())
            m_med = np.mean(m_vals)
            feicoes = list(solo['feicoes'].values())
            h_hc = np.mean([f['H_Hc'] for f in feicoes]) if feicoes else 0.0

            d_mod = float(delta_model(
                vib_med, m_med, h_hc,
                **TRUE_PARAMS
            ))

            resultados[nome].append(dict(
                I=I, perda=perda, R_mm=R_mm, tau=tau,
                K_obs=K_obs, delta_obs=delta_obs, delta_mod=d_mod,
            ))

    # ── Tabela resumo ───────────────────────────────────────────────
    print("=" * 80)
    print("EROSÃO VIRTUAL (WEPP-like) — RESULTADOS POR CLASSE E INTENSIDADE")
    print("=" * 80)
    print(f"{'Solo':>15} {'I30':>5} {'Perda':>10} {'R_mm':>8} {'τ(Pa)':>8} "
          f"{'K_obs':>8} {'δ_obs':>8} {'δ_mod':>8}")

    for nome in solos_nomes:
        for r in resultados[nome]:
            if r['I'] in [20, 40, 60, 80, 100]:
                print(f"{nome:>15} {r['I']:>5.0f} {r['perda']:>10.4f} "
                      f"{r['R_mm']:>8.1f} {r['tau']:>8.2f} "
                      f"{r['K_obs']:>8.5f} {r['delta_obs']:>8.2f} "
                      f"{r['delta_mod']:>8.2f}")
        print()

    # ── Comparação δ médio por classe ───────────────────────────────
    print("=" * 80)
    print("COMPARAÇÃO δ MÉDIO (I30 ≥ 40 mm/h) POR CLASSE")
    print("=" * 80)
    for nome in solos_nomes:
        deltas_obs = [r['delta_obs'] for r in resultados[nome]
                      if r['I'] >= 40 and r['perda'] > 0]
        d_mod = resultados[nome][0]['delta_mod']
        if deltas_obs:
            d_mean = np.mean(deltas_obs)
            d_std = np.std(deltas_obs)
            erro_rel = abs(d_mean - d_mod) / d_mod * 100
            print(f"  {nome:>15}: δ_obs = {d_mean:.2f} ± {d_std:.2f}, "
                  f"δ_mod = {d_mod:.2f}, erro relativo = {erro_rel:.1f}%")
        else:
            print(f"  {nome:>15}: sem erosão observada para I30 ≥ 40 mm/h")

    # ── Figura 1: Perda de solo vs I30 ──────────────────────────────
    fig, axes = plt.subplots(2, 2, figsize=(14, 12))

    # (a) Perda de solo
    ax = axes[0, 0]
    for nome, cor, mk in zip(solos_nomes, cores, markers):
        I_vals = [r['I'] for r in resultados[nome]]
        perdas = [r['perda'] for r in resultados[nome]]
        ax.plot(I_vals, perdas, f'{mk}-', color=cor, linewidth=2, markersize=5,
                label=DISPLAY_NAME[nome])
    ax.set_xlabel('Maximum 30-min intensity, $I_{30}$ (mm/h)', fontsize=11)
    ax.set_ylabel('Soil loss (t/ha)', fontsize=11)
    ax.set_title('Simulated soil loss by pedological class', fontsize=12)
    ax.text(-0.05, 1.12, '(a)', transform=ax.transAxes,
            fontsize=14, fontweight='bold', va='top')
    ax.legend(fontsize=10)
    ax.grid(True, alpha=0.3)

    # (b) K_obs vs I30
    ax = axes[0, 1]
    for nome, cor, mk in zip(solos_nomes, cores, markers):
        I_vals = [r['I'] for r in resultados[nome] if r['K_obs'] > 0]
        K_vals = [r['K_obs'] for r in resultados[nome] if r['K_obs'] > 0]
        ax.plot(I_vals, K_vals, f'{mk}-', color=cor, linewidth=2, markersize=5,
                label=DISPLAY_NAME[nome])
        ax.axhline(K_RUSLE[nome], color=cor, linestyle=':', alpha=0.5)
    ax.set_xlabel('Maximum 30-min intensity, $I_{30}$ (mm/h)', fontsize=11)
    ax.set_ylabel('Observed erodibility, $K_{obs}$ (t h MJ$^{-1}$ mm$^{-1}$)', fontsize=11)
    ax.set_title('Inverted $K_{obs}$ vs nomograph $K_{RUSLE}$', fontsize=12)
    ax.text(-0.05, 1.12, '(b)', transform=ax.transAxes,
            fontsize=14, fontweight='bold', va='top')
    ax.legend(fontsize=10)
    ax.grid(True, alpha=0.3)

    # (c) δ_obs vs I30 com δ_mod como referência
    ax = axes[1, 0]
    for nome, cor, mk in zip(solos_nomes, cores, markers):
        I_vals = [r['I'] for r in resultados[nome] if r['perda'] > 0]
        d_vals = [r['delta_obs'] for r in resultados[nome] if r['perda'] > 0]
        d_mod = resultados[nome][0]['delta_mod']
        ax.plot(I_vals, d_vals, f'{mk}-', color=cor, linewidth=2, markersize=5,
                label=f'{DISPLAY_NAME[nome]} ($\\delta_{{mod}}$={d_mod:.1f})')
        ax.axhline(d_mod, color=cor, linestyle='--', alpha=0.6)
    ax.axhline(1.0, color='gray', linestyle=':', alpha=0.4, label='$\\delta$ = 1 (no correction)')
    ax.set_xlabel('Maximum 30-min intensity, $I_{30}$ (mm/h)', fontsize=11)
    ax.set_ylabel('Amplification factor, $\\delta$ = $K_{obs}$ / $K_{RUSLE}$', fontsize=11)
    ax.set_title('Observed vs modeled amplification factor $\\delta$', fontsize=12)
    ax.text(-0.05, 1.12, '(c)', transform=ax.transAxes,
            fontsize=14, fontweight='bold', va='top')
    ax.legend(fontsize=9)
    ax.grid(True, alpha=0.3)

    # (d) δ_obs vs δ_mod (1:1)
    ax = axes[1, 1]
    for nome, cor, mk in zip(solos_nomes, cores, markers):
        d_vals = [r['delta_obs'] for r in resultados[nome]
                  if r['perda'] > 0 and r['I'] >= 40]
        d_mod = resultados[nome][0]['delta_mod']
        if d_vals:
            ax.scatter([d_mod] * len(d_vals), d_vals, color=cor, marker=mk,
                       s=80, alpha=0.6, label=DISPLAY_NAME[nome], edgecolors='k',
                       linewidths=0.5)

    # Linha 1:1
    lims = ax.get_xlim()
    all_vals = []
    for nome in solos_nomes:
        d_mod = resultados[nome][0]['delta_mod']
        all_vals.append(d_mod)
        all_vals.extend([r['delta_obs'] for r in resultados[nome] if r['perda'] > 0])
    if all_vals:
        v_min, v_max = min(all_vals) * 0.8, max(all_vals) * 1.2
        ax.plot([v_min, v_max], [v_min, v_max], 'k--', alpha=0.5, label='1:1')
        ax.set_xlim(v_min, v_max)
        ax.set_ylim(v_min, v_max)
    ax.set_xlabel('$\\delta_{model}$ (predicted by $K_{plint}$)', fontsize=11)
    ax.set_ylabel('$\\delta_{obs}$ (inverted from erosion model)', fontsize=11)
    ax.set_title('$\\delta$ validation \u2014 model vs simulated process', fontsize=12)
    ax.text(-0.05, 1.12, '(d)', transform=ax.transAxes,
            fontsize=14, fontweight='bold', va='top')
    ax.legend(fontsize=10)
    ax.grid(True, alpha=0.3)

    fig.tight_layout()
    fig.savefig(FIG_DIR / 'fig_08_erosao_virtual.png', dpi=300)
    print(f"\nFigura salva: {FIG_DIR / 'fig_08_erosao_virtual.png'}")
    plt.close('all')


if __name__ == '__main__':
    main()
