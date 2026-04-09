"""
Simulação 03 — Estabilidade de Taludes e Validação de γ(H/Hc).
Modela fator de segurança (FS) por Bishop simplificado para cortes em
Plintossolo sob saturação progressiva, e verifica se a forma funcional
γ = 1 + k3*(H/Hc)^n3 captura a transição para colapso.
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
    PLINTOSSOLO, calc_Hc, gamma, FIG_DIR,
)


def fator_seguranca_rankine(H, c, phi_deg, gamma_sat, gamma_w=9.81, ru=0.0):
    """
    Fator de segurança para corte vertical (Rankine modificado).
    ru = pressão de poros normalizada (u / γ_sat * H), 0 a ~0.5.
    FS = Hc_efetivo / H
    """
    phi_rad = np.radians(phi_deg)
    # Coesão efetiva reduzida por pressão de poros
    c_eff = c * (1.0 - ru * 0.3)  # simplificação: c reduz com ru
    tan_term = np.tan(np.pi / 4 + phi_rad / 2)
    Hc_eff = (2 * c_eff / gamma_sat) * tan_term + \
             (2 * c_eff) / (gamma_sat * tan_term)
    return Hc_eff / H


def volume_ruptura(H, phi_deg, largura=1.0):
    """
    Volume de cunha de ruptura planar por metro de comprimento.
    V = 0.5 * H² / tan(45 - φ/2) * largura
    """
    phi_rad = np.radians(phi_deg)
    ang_ruptura = np.pi / 4 - phi_rad / 2
    return 0.5 * H ** 2 / np.tan(ang_ruptura) * largura


def gamma_func(h_hc, k3, n3):
    """Forma funcional de γ para ajuste."""
    return 1.0 + k3 * h_hc ** n3


def main():
    c = PLINTOSSOLO['c_kPa']
    phi = PLINTOSSOLO['phi_deg']
    g_sat = PLINTOSSOLO['gamma_sat']
    Hc = PLINTOSSOLO['Hc']

    H_Hc_range = np.linspace(0.05, 0.95, 50)
    H_range = H_Hc_range * Hc

    # ── FS para diferentes níveis de saturação (ru) ─────────────────
    ru_values = [0.0, 0.1, 0.2, 0.3, 0.4, 0.5]
    FS_matrix = np.zeros((len(ru_values), len(H_range)))

    for i, ru in enumerate(ru_values):
        FS_matrix[i, :] = fator_seguranca_rankine(H_range, c, phi, g_sat, ru=ru)

    # ── Volume de ruptura normalizado ───────────────────────────────
    V = volume_ruptura(H_range, phi)
    V_norm = V / volume_ruptura(Hc, phi)  # normalizado por V(Hc)

    # ── δ_geotécnico como proxy: contribuição relativa ──────────────
    # A contribuição geotécnica cresce com V e com 1/FS
    # Proxy: δ_geo ∝ V_norm / FS (mais volume mobilizado quando FS baixo)
    delta_geo = np.zeros_like(H_Hc_range)
    for i, h_hc in enumerate(H_Hc_range):
        # Usar FS médio entre ru=0 e ru=0.3 (condição sazonal)
        fs_mean = np.mean([FS_matrix[j, i] for j in range(4)])
        # Proxy: amplificação relativa = V_norm * (2/FS - 1) quando FS < 2
        if fs_mean < 2.0:
            delta_geo[i] = V_norm[i] * (2.0 / fs_mean - 1.0)
        else:
            delta_geo[i] = 0.0

    # Normalizar para que γ(0) = 1
    gamma_sim = 1.0 + delta_geo / max(delta_geo.max(), 1e-10) * 5.0

    # ── Ajustar γ = 1 + k3*(H/Hc)^n3 aos dados simulados ──────────
    mask = H_Hc_range > 0.05
    popt, pcov = curve_fit(gamma_func, H_Hc_range[mask], gamma_sim[mask],
                           p0=[3.0, 2.0], bounds=([0.1, 0.5], [20.0, 5.0]))
    k3_fit, n3_fit = popt
    perr = np.sqrt(np.diag(pcov))

    print("=" * 60)
    print("ESTABILIDADE DE TALUDES — VALIDAÇÃO DE γ(H/Hc)")
    print("=" * 60)
    print(f"Parâmetros geotécnicos: c={c} kPa, φ={phi}°, γ_sat={g_sat} kN/m³")
    print(f"Hc (Rankine, saturado) = {Hc:.2f} m")
    print(f"\nAjuste γ = 1 + k3·(H/Hc)^n3:")
    print(f"  k3 = {k3_fit:.3f} ± {perr[0]:.3f}")
    print(f"  n3 = {n3_fit:.3f} ± {perr[1]:.3f}")
    print(f"  (Valor inicial proposto: k3=3.0, n3=2.0)")

    # ── Verificar FS para feições reais ─────────────────────────────
    print(f"\n{'Feição':>8}  {'H(m)':>6}  {'H/Hc':>6}  {'FS(ru=0)':>8}  "
          f"{'FS(ru=0.3)':>10}  {'γ_ajust':>8}")
    for fn, fd in PLINTOSSOLO['feicoes'].items():
        H = fd['prof']
        h_hc = fd['H_Hc']
        fs0 = fator_seguranca_rankine(H, c, phi, g_sat, ru=0.0)
        fs3 = fator_seguranca_rankine(H, c, phi, g_sat, ru=0.3)
        g_fit = gamma_func(h_hc, k3_fit, n3_fit)
        print(f"{fn:>8}  {H:>6.2f}  {h_hc:>6.2f}  {fs0:>8.2f}  "
              f"{fs3:>10.2f}  {g_fit:>8.3f}")

    # ── Figura 1: FS vs H/Hc para diferentes ru ────────────────────
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))

    colors_ru = plt.cm.RdYlBu_r(np.linspace(0.2, 0.9, len(ru_values)))
    for i, ru in enumerate(ru_values):
        ax1.plot(H_Hc_range, FS_matrix[i, :], color=colors_ru[i],
                 linewidth=2, label=f'$r_u$ = {ru:.1f}')
    ax1.axhline(1.0, color='red', linestyle='--', linewidth=1.5,
                label='FS = 1 (limiar de ruptura)')
    ax1.axhline(1.5, color='orange', linestyle=':', linewidth=1,
                label='FS = 1,5 (margem mínima convencional)')

    # Marcar feições reais
    for fn, fd in PLINTOSSOLO['feicoes'].items():
        h_hc = fd['H_Hc']
        fs0 = fator_seguranca_rankine(fd['prof'], c, phi, g_sat, ru=0.0)
        ax1.plot(h_hc, fs0, 'ko', markersize=8)
        ax1.annotate(fn, (h_hc, fs0), textcoords="offset points",
                     xytext=(5, 5), fontsize=9)

    ax1.set_xlabel('Profundidade normalizada da feição (H / H$_c$)', fontsize=12)
    ax1.set_ylabel('Fator de segurança (FS)', fontsize=12)
    ax1.set_title('Estabilidade de corte vertical — Plintossolo\n'
                  r'($c$ = 13,02 kPa, $\phi$ = 34,93°, H$_c$ = 3,35 m)',
                  fontsize=12)
    ax1.text(-0.05, 1.12, '(a)', transform=ax1.transAxes,
             fontsize=14, fontweight='bold', va='top')
    ax1.legend(fontsize=9, loc='upper right')
    ax1.grid(True, alpha=0.3)
    ax1.set_xlim(0, 1)
    ax1.set_ylim(0, 8)

    # ── Figura 2: γ simulado vs ajustado ────────────────────────────
    ax2.plot(H_Hc_range, gamma_sim, 'ko', markersize=4, alpha=0.5,
             label='$\\gamma$ simulado (proxy FS-volume)')
    h_fit = np.linspace(0, 0.95, 100)
    ax2.plot(h_fit, gamma_func(h_fit, k3_fit, n3_fit), 'r-', linewidth=2.5,
             label=f'Ajuste: $k_3$={k3_fit:.2f}, $n_3$={n3_fit:.2f}')
    ax2.plot(h_fit, gamma_func(h_fit, 3.0, 2.0), 'b--', linewidth=1.5,
             label='Proposta inicial: $k_3$=3,0, $n_3$=2,0')

    # Marcar feições reais
    for fn, fd in PLINTOSSOLO['feicoes'].items():
        h_hc = fd['H_Hc']
        g_val = gamma_func(h_hc, k3_fit, n3_fit)
        ax2.plot(h_hc, g_val, 'rs', markersize=10)
        ax2.annotate(fn, (h_hc, g_val), textcoords="offset points",
                     xytext=(5, 5), fontsize=9)

    ax2.set_xlabel('Profundidade normalizada da feição (H / H$_c$)', fontsize=12)
    ax2.set_ylabel('Fator de vulnerabilidade geotécnica ($\\gamma$)', fontsize=12)
    ax2.set_title('Validação da forma funcional $\\gamma$(H/H$_c$)', fontsize=12)
    ax2.text(-0.05, 1.08, '(b)', transform=ax2.transAxes,
             fontsize=14, fontweight='bold', va='top')
    ax2.legend(fontsize=10)
    ax2.grid(True, alpha=0.3)
    ax2.set_xlim(0, 1)

    fig.tight_layout()
    fig.savefig(FIG_DIR / 'fig_05_estabilidade_taludes.png', dpi=300)
    print(f"\nFigura salva: {FIG_DIR / 'fig_05_estabilidade_taludes.png'}")

    plt.close('all')


if __name__ == '__main__':
    main()
