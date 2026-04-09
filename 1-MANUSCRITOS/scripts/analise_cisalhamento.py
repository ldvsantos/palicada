#!/usr/bin/env python3
"""Análise dos dados de cisalhamento direto para integração nos manuscritos."""
import numpy as np

# === DADOS DO ENSAIO DE CISALHAMENTO DIRETO ===
c = 13.02      # kPa, coesao inundada
phi = 34.93    # graus, angulo de atrito
phi_rad = np.radians(phi)
gamma_g = 2.654  # g/cm3

# Dados dos CPs
sigma_n = [20, 40, 80, 200]
tau_p   = [22.61, 45.70, 69.19, 152.07]
gamma_d = [1.531, 1.491, 1.294, 1.320]
e_i     = [0.734, 0.780, 1.051, 1.011]
e_f     = [0.666, 0.620, 0.642, 0.487]
S_f     = [118.3, 109.9, 117.6, 138.9]

# === 1. PESO ESPECIFICO SATURADO ===
e_f_medio = np.mean(e_f)
gamma_sat = ((gamma_g + e_f_medio) / (1 + e_f_medio)) * 9.81  # kN/m3
gamma_sub = gamma_sat - 9.81
print("=== PARAMETROS DERIVADOS ===")
print(f"e_f medio = {e_f_medio:.3f}")
print(f"gamma_sat = {gamma_sat:.2f} kN/m3")
print(f"gamma_sub = {gamma_sub:.2f} kN/m3")

# === 2. ALTURA CRITICA DE CORTE VERTICAL (Rankine) ===
Ka = np.tan(np.radians(45 - phi/2))**2
sqrt_Ka = np.sqrt(Ka)
print(f"\nKa = {Ka:.4f}, sqrt(Ka) = {sqrt_Ka:.4f}")

# Hc teorico (sem fissura de tracao)
Hc = 4 * c / (gamma_sat * sqrt_Ka)
z_c = 2 * c / (gamma_sat * sqrt_Ka)
# Hc com fissura inundada (reducao ~2/3)
Hc_crack = 2.67 * c / (gamma_sat * sqrt_Ka)

print(f"\n=== ALTURA CRITICA (Hc) ===")
print(f"Hc teorico (sem fissura) = {Hc:.2f} m")
print(f"Profundidade fissura (z_c) = {z_c:.2f} m")
print(f"Hc com fissura inundada = {Hc_crack:.2f} m")

# === 3. FOS POR FEICAO ===
feicoes = {
    "F1": {"prof": 1.10, "decl_pct": 12.0},
    "F2": {"prof": 0.40, "decl_pct": 8.0},
    "F3": {"prof": 0.60, "decl_pct": 9.0},
    "F4": {"prof": 1.40, "decl_pct": 15.0},
    "F5": {"prof": 1.50, "decl_pct": 17.0},
    "F6": {"prof": 0.60, "decl_pct": 10.0},
}

print(f"\n=== FOS POR FEICAO (corte vertical, condicao inundada) ===")
print(f"  Ref: Hc_crack = {Hc_crack:.2f} m")
header = f"{'Feicao':>7} | {'Prof':>6} | {'H/Hc':>6} | {'FOS':>6} | {'Status'}"
print(header)
print("-" * 65)
for f, d in feicoes.items():
    ratio = d["prof"] / Hc_crack
    fos = Hc_crack / d["prof"]
    if fos < 1.0:
        status = "INSTAVEL"
    elif fos < 1.5:
        status = "MARGINALMENTE ESTAVEL"
    elif fos < 2.0:
        status = "CONDICIONALMENTE ESTAVEL"
    else:
        status = "ESTAVEL"
    print(f"{f:>7} | {d['prof']:>6.2f} | {ratio:>6.2f} | {fos:>6.2f} | {status}")

# === 4. TENSAO CISALHANTE: FLUXO vs RESISTENCIA ===
gamma_w = 9.81
print(f"\n=== TENSAO CISALHANTE: FLUXO vs RESISTENCIA ===")
print(f"c (sigma_n=0) = {c:.2f} kPa = {c*1000:.0f} Pa")
for f, d in feicoes.items():
    S_slope = d["decl_pct"] / 100.0
    theta = np.arctan(S_slope)
    Rh = d["prof"] * 0.3
    tau_flow = gamma_w * Rh * S_slope
    sigma_n_base = gamma_sat * d["prof"] * np.cos(theta)**2
    tau_resist = c + sigma_n_base * np.tan(phi_rad)
    ratio_tau = tau_flow / tau_resist
    print(f"  {f}: tau_flow={tau_flow:.3f} kPa, tau_resist={tau_resist:.1f} kPa, ratio={ratio_tau:.4f}")

# === 5. LIMIAR PARA O ABACO ===
limiar_67 = 0.67 * Hc_crack
print(f"\n=== LIMIARES PARA O ABACO ===")
print(f"Prof > {limiar_67:.2f} m -> FOS < 1.5 (marginalmente estavel)")
print(f"Prof > {Hc_crack:.2f} m -> FOS < 1.0 (instavel)")
print(f"F acima de {limiar_67:.2f} m: F1(1.10), F4(1.40), F5(1.50)")
print(f"F abaixo: F2(0.40), F3(0.60), F6(0.60)")

# === 6. COMPORTAMENTO VOLUMETRICO ===
print(f"\n=== COMPORTAMENTO VOLUMETRICO ===")
for i in range(4):
    delta = e_f[i] - e_i[i]
    tipo = "contratil (NC)" if delta < 0 else "dilatante (OC)"
    print(f"  CP{i+1}: e_i={e_i[i]:.3f} -> e_f={e_f[i]:.3f}, De={delta:.3f} ({tipo})")

# === 7. VERIFICACAO ENVOLTORIA MOHR-COULOMB ===
print(f"\n=== VERIFICACAO ENVOLTORIA ===")
print(f"tau = {c:.2f} + sigma_n * tan({phi:.2f} deg)")
print(f"tan(phi) = {np.tan(phi_rad):.4f}")
for sn, tp in zip(sigma_n, tau_p):
    tau_pred = c + sn * np.tan(phi_rad)
    erro = tp - tau_pred
    print(f"  sigma_n={sn:>5} kPa: tau_pred={tau_pred:.2f}, tau_obs={tp:.2f}, erro={erro:+.2f} kPa")
