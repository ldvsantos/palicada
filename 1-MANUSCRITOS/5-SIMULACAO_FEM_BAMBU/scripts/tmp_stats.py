import pandas as pd
import json

base = r"C:\Users\vidal\OneDrive\Documentos\13 - CLONEGIT\artigo-posdoc\3-EROSIBIDADE\1-MANUSCRITOS\5-SIMULACAO_FEM_BAMBU\resultados"

df = pd.read_csv(f"{base}/fem_results_full.csv")
ds = pd.read_csv(f"{base}/fem_summary_failure.csv")
sens = pd.read_csv(f"{base}/sensitivity_span_velocity.csv")
sf = pd.read_csv(f"{base}/safety_factor_evolution.csv")

print("="*60)
print("RESULTADOS COMPLETOS DA SIMULAÇÃO FEM")
print("="*60)

print(f"\nTotal registros full: {len(df)}")
print(f"FI max global: {df['failure_index'].max():.6f}")
print(f"FI min global: {df['failure_index'].min():.6f}")
print(f"FI mean global: {df['failure_index'].mean():.6f}")

print("\n--- FI MAX por degradação ---")
for k in sorted(df['degradation_scenario'].unique()):
    sub = df[df['degradation_scenario']==k]
    print(f"  {k}: FI_max={sub['failure_index'].max():.6f}")

print("\n--- FI MAX por segmento ---")
for seg in df['segment'].unique():
    sub = df[df['segment']==seg]
    print(f"  {seg}: FI_max={sub['failure_index'].max():.6f}")

print("\n--- FI MAX por cenário hidrológico ---")
for h in df['hydro_scenario'].unique():
    sub = df[df['hydro_scenario']==h]
    print(f"  {h}: FI_max={sub['failure_index'].max():.6f}")

# Pior combo
idx = df['failure_index'].idxmax()
row = df.loc[idx]
print("\n--- PIOR COMBINAÇÃO (FI máximo) ---")
for c in ['segment','hydro_scenario','degradation_scenario','time_yr','element',
          'is_node_zone','failure_index','failure_mode','sigma_bending_MPa',
          'tau_shear_MPa','deflection_mm','sed_fill_pct','veg_factor','deg_factor',
          'wall_thickness_mm','E_L_GPa','sigma_t_ult_MPa','tau_ult_MPa']:
    print(f"  {c}: {row[c]}")

# Top 10 FI
print("\n--- TOP 10 FI ---")
top = df.nlargest(10, 'failure_index')
for _, r in top.iterrows():
    print(f"  seg={r['segment']} hydro={r['hydro_scenario']} deg={r['degradation_scenario']} "
          f"t={r['time_yr']} elem={r['element']} zone={r['is_node_zone']} "
          f"FI={r['failure_index']:.6f} mode={r['failure_mode']}")

# Deflection stats
print("\n--- DEFLEXÃO ---")
print(f"  Max deflexão (mm): {df['deflection_mm'].max():.4f}")
idx_d = df['deflection_mm'].idxmax()
rd = df.loc[idx_d]
print(f"  @seg={rd['segment']} hydro={rd['hydro_scenario']} deg={rd['degradation_scenario']} t={rd['time_yr']}")

# Defl t=0 vs t=5 no cenário referência MED P90
ref = df[(df['segment']=='MED') & (df['hydro_scenario']=='P90') & (df['degradation_scenario']=='reference')]
d0 = ref[ref['time_yr']==0]['deflection_mm'].max()
d5 = ref[ref['time_yr']==5]['deflection_mm'].max()
d10 = ref[ref['time_yr']==10]['deflection_mm'].max()
print(f"\n  MED/P90/reference: defl_max t=0={d0:.4f} t=5={d5:.4f} t=10={d10:.4f}")
if d0 > 0:
    print(f"  Incremento 0→5: {(d5/d0-1)*100:.0f}%")
    print(f"  Incremento 0→10: {(d10/d0-1)*100:.0f}%")

# FI em zonas nodais vs internodais
print("\n--- FI: ZONAS NODAIS vs INTERNODAIS ---")
nodes = df[df['is_node_zone']==True]
inter = df[df['is_node_zone']==False]
print(f"  Nodal: FI_max={nodes['failure_index'].max():.6f}, FI_mean={nodes['failure_index'].mean():.6f}")
print(f"  Internodal: FI_max={inter['failure_index'].max():.6f}, FI_mean={inter['failure_index'].mean():.6f}")
if inter['failure_index'].max() > 0:
    ratio = nodes['failure_index'].max() / inter['failure_index'].max()
    print(f"  Razão nodal/internodal (max): {ratio:.2f}x")

# Fator de segurança = 1/FI
fi_max = df['failure_index'].max()
print(f"\n--- FATOR DE SEGURANÇA MÍNIMO: {1/fi_max:.1f} ---")

# Sensitivity analysis
print("\n" + "="*60)
print("ANÁLISE DE SENSIBILIDADE")
print("="*60)
print("Total combinações:", len(sens))
failures = sens[sens['max_FI'] >= 1.0]
print("Combinações com falha (FI>=1):", len(failures))
if len(failures) > 0:
    print("Vão mínimo para falha:", failures['span_m'].min(), "m")
    print("Velocidade mínima para falha:", failures['v_flow_ms'].min(), "m/s")
    print("\n--- Top 15 falhas ---")
    for _, r in failures.nlargest(15, 'max_FI').iterrows():
        print("  span=%.1fm vel=%.1fm/s t=%.0fyr FI=%.3f SF=%.2f mode=%s" % (
            r['span_m'], r['v_flow_ms'], r['time_yr'], r['max_FI'], r['safety_factor'], r['failure_mode']))

# Config atual 1.5m
actual = sens[sens['span_m'] == 1.5]
print("\nConfig 1.5m: SF min=%.1f, FI max=%.6f" % (actual['safety_factor'].min(), actual['max_FI'].max()))

# Safety factor evolution
print("\n--- EVOLUÇÃO DO FATOR DE SEGURANÇA ---")
# Pior cenário MED/P95/pessimistic
worst = sf[(sf['segment']=='MED') & (sf['hydro_scenario']=='P95') & (sf['degradation_scenario']=='pessimistic')]
print("\nMED/P95/pessimistic:")
for _, r in worst.iterrows():
    print("  t=%.1f SF=%.1f FI=%.6f defl=%.3fmm sigma=%.3fMPa tau=%.3fMPa" % (
        r['time_yr'], r['safety_factor'], r['max_FI'], r['max_defl_mm'],
        r['max_sigma_MPa'], r['max_tau_MPa']))

# Melhor cenário: SUP/median/optimistic
best = sf[(sf['segment']=='SUP') & (sf['hydro_scenario']=='median') & (sf['degradation_scenario']=='optimistic')]
print("\nSUP/median/optimistic:")
for _, r in best.iterrows():
    print("  t=%.1f SF=%.1f FI=%.6f defl=%.3fmm" % (
        r['time_yr'], r['safety_factor'], r['max_FI'], r['max_defl_mm']))

# Cenário referência MED/P90/baseline
ref = sf[(sf['segment']=='MED') & (sf['hydro_scenario']=='P90') & (sf['degradation_scenario']=='baseline')]
print("\nMED/P90/baseline:")
for _, r in ref.iterrows():
    print("  t=%.1f SF=%.1f FI=%.6f defl=%.3fmm sigma=%.3fMPa tau=%.3fMPa" % (
        r['time_yr'], r['safety_factor'], r['max_FI'], r['max_defl_mm'],
        r['max_sigma_MPa'], r['max_tau_MPa']))
