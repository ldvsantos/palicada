"""Extrai todos os valores numéricos necessários para atualizar o manuscrito
após a inclusão dos pinos de talude (Option B).
"""
import pandas as pd
import numpy as np
from scipy.optimize import curve_fit
from scipy.stats import f

BASE = ('c:/Users/vidal/OneDrive/Documentos/13 - CLONEGIT/artigo-posdoc/'
        '3-EROSIBIDADE/1-MANUSCRITOS/5-SIMULACAO_FEM_BAMBU/resultados/')

df = pd.read_csv(BASE + 'fem3d_full.csv')
ds = pd.read_csv(BASE + 'fem3d_summary.csv')

# Excluir stub elements
df_s = df[df['type'] != 'colmo_embed']

print('COLUNAS:', df_s.columns.tolist())
print()

# ── 1. FI máximo global ───────────────────────────
worst = df_s.loc[df_s['FI'].idxmax()]
print('=== 1. FI MAX GLOBAL ===')
print(worst[['segment','hydro','degradation','time_yr','type','FI','safety_factor',
             'sigma_b_MPa','tau_s_MPa']].to_string())
print()

# ── 2. MED pessimistic t=10 ─────────────────────
med_p10 = df_s[(df_s.segment=='MED') & (df_s.degradation=='pessimistic') & (df_s.time_yr==10.0)]
st = med_p10[med_p10.type=='stake']
co = med_p10[med_p10.type=='colmo']
fi_st = st['FI'].max(); fi_co = co['FI'].max()
row_crit = st.loc[st['FI'].idxmax()]
print('=== 2. MED pessimistic t=10 stake crítica ===')
print(row_crit[['FI','safety_factor','sigma_b_MPa','tau_s_MPa']].to_string())
print(f'FI stake: {fi_st:.4f}   FI colmo: {fi_co:.4f}   Ratio: {fi_st/fi_co:.0f}x')
# componentes contributions to Tsai-Hill (sigma^2/sigmaUlt^2 + tau^2/tauUlt^2)
# Need to look for component columns
print()

# ── 3. INF / SUP máximo ─────────────────────────
for seg in ['INF', 'SUP']:
    sub = df_s[(df_s.segment==seg) & (df_s.degradation=='pessimistic') & (df_s.type=='stake')]
    r = sub.loc[sub['FI'].idxmax()]
    print(f'{seg} pessimistic: FI={r["FI"]:.4f}  FS={r["safety_factor"]:.0f}  t={r["time_yr"]}  '
          f'sig={r["sigma_b_MPa"]:.3f}MPa  tau={r["tau_s_MPa"]:.3f}MPa')
print()

# ── 4. Ratio MED vs INF/SUP ──────────────────────
fi_inf = df_s[(df_s.segment=='INF') & (df_s.degradation=='pessimistic') & (df_s.type=='stake')]['FI'].max()
fi_sup = df_s[(df_s.segment=='SUP') & (df_s.degradation=='pessimistic') & (df_s.type=='stake')]['FI'].max()
fi_med = df_s[(df_s.segment=='MED') & (df_s.degradation=='pessimistic') & (df_s.type=='stake')]['FI'].max()
print(f'Ratio MED/INF: {fi_med/fi_inf:.0f}x   MED/SUP: {fi_med/fi_sup:.0f}x')
fs_inf = df_s[(df_s.segment=='INF') & (df_s.degradation=='pessimistic') & (df_s.type=='stake')]['safety_factor'].max()
fs_sup = df_s[(df_s.segment=='SUP') & (df_s.degradation=='pessimistic') & (df_s.type=='stake')]['safety_factor'].max()
print(f'FS INF max: {fs_inf:.0f}   FS SUP max: {fs_sup:.0f}')
print()

# ── 5. FI evolution MED by scenario (median) ─────
print('=== 5. FI evolution MED stake median ===')
for deg in ['optimistic', 'baseline', 'pessimistic']:
    sub = df_s[(df_s.segment=='MED') & (df_s.degradation==deg) & (df_s.hydro=='median') & (df_s.type=='stake')]
    t8  = sub[sub.time_yr==8.0]['FI'].max()
    t10 = sub[sub.time_yr==10.0]['FI'].max()
    print(f'  {deg}: FI(t=8)={t8:.3f}  FI(t=10)={t10:.3f}')
print()

# ── 6. FS min baseline ────────────────────────────
print('=== 6. FS summary ===')
ref = ds[ds.degradation=='baseline']
print(f'FS min baseline: {ref["safety_factor"].min():.2f}')
opt = ds[ds.degradation=='optimistic']
print(f'FS min optimistic MED t=10: {opt[(opt.segment=="MED") & (opt.time_yr==10.0)]["safety_factor"].min():.2f}')
print()

# ── 7. Deslocamentos ──────────────────────────────
print('=== 7. Deslocamentos laterais max (mm) ===')
for seg in ['INF','MED','SUP']:
    for deg in ['pessimistic','baseline']:
        sub = df_s[(df_s.segment==seg) & (df_s.degradation==deg) & (df_s.time_yr==10.0)]
        d = sub['disp_lat_mm'].max()
        print(f'  {seg} {deg} t=10: {d:.1f} mm')
print()

# ── 8. FS regression MED / SUP ───────────────────
print('=== 8. FS trajectories ===')
for seg, deg in [('MED','pessimistic'), ('SUP','pessimistic'), ('INF','pessimistic')]:
    sub = ds[(ds.segment==seg) & (ds.degradation==deg) & (ds.hydro=='P95')].sort_values('time_yr')
    t = sub['time_yr'].values
    fs = sub['safety_factor'].values
    # Quadratic fit
    try:
        coeffs = np.polyfit(t, fs, 2)
        p = np.poly1d(coeffs)
        r2 = 1 - np.sum((fs - p(t))**2) / np.sum((fs - fs.mean())**2)
        print(f'  {seg} {deg}: FS = {coeffs[2]:.2f} + {coeffs[1]:+.2f}t + {coeffs[0]:+.3f}t² (R²={r2:.3f})')
    except Exception as e:
        print(f'  {seg}: {e}')

# ── 9. Shear fraction (FI_cis / FI_total) ─────────
print()
print('=== 9. Shear fraction at critical element ===')
row = row_crit
sig = row['sigma_b_MPa']
tau = row['tau_s_MPa']
# From postprocess: sigma_ult residual ~ sigma_tL * factor; need factor
# factor = e^(-k*t) with k=0.10, t=10 → 0.3679
factor = np.exp(-0.10 * 10.0)
# Wall thinning: wall = max(min_wall, initial_wall - 0.001*t)
# BAMBOO props from fem_palicada_3d.py: sigma_tL=180MPa, tau_LR=10MPa
# Approximate from FS = 1/FI: sigma_ult_res = sigma_tL*factor, tau_ult_res = tau_LR*factor
# FI_bending = (sigma/sigma_ult)^2
# FI_shear = (tau/tau_ult)^2
# FI_total = FI_bending + FI_shear (Tsai-Hill simplified)
sigma_tL = 180.0  # MPa - consistent with fem_palicada_3d.py and manuscript
tau_LR   = 10.0   # MPa - consistent with fem_palicada_3d.py and manuscript
sig_ult_r = sigma_tL * factor
tau_ult_r = tau_LR  * factor * 0.65  # SCF on nodal zone
fi_bend = (sig / sig_ult_r)**2
fi_shear = (tau / tau_ult_r)**2
fi_total_calc = fi_bend + fi_shear
print(f'  sigma_b={sig:.3f} MPa  tau_s={tau:.3f} MPa')
print(f'  sig_ult_r={sig_ult_r:.2f} MPa  tau_ult_r={tau_ult_r:.3f} MPa (after SCF degradation)')
print(f'  FI_bend (calc) = {fi_bend:.4f}  FI_shear (calc) = {fi_shear:.4f}')
print(f'  FI_total_calc = {fi_total_calc:.4f}  (vs CSV FI = {row["FI"]:.4f})')
if fi_total_calc > 0:
    print(f'  Shear fraction = {fi_shear/fi_total_calc*100:.1f}%')
print()

# ── 10. Node vs internode ─────────────────────────
print('=== 10. Node vs Internode FI (MED pessimistic P95) ===')
med_p95 = df_s[(df_s.segment=='MED') & (df_s.degradation=='pessimistic') & (df_s.hydro=='P95') & (df_s.type=='stake')]
for t_val in [0.0, 5.0, 10.0]:
    sub_t = med_p95[med_p95.time_yr==t_val]
    if sub_t.empty:
        continue
    nz_max   = sub_t[sub_t.is_node_zone==True]['FI'].max()
    nz_other = sub_t[sub_t.is_node_zone==False]['FI'].dropna()
    nz_other_max = nz_other.max() if len(nz_other) else float('nan')
    ratio = nz_max/nz_other_max if nz_other_max > 0 else float('nan')
    print(f'  t={t_val}: FI_nodal={nz_max:.4f}  FI_internodal={nz_other_max:.4f}  ratio={ratio:.2f}')

print()
print('=== 11. FI_bend e FI_shear do elemento critico ===')
row2 = df_s.loc[df_s['FI'].idxmax()]
print(f'  FI_bend={row2["FI_bend"]:.4f}  FI_shear={row2["FI_shear"]:.4f}  FI_total={row2["FI"]:.4f}')
print(f'  shear frac = {row2["FI_shear"]/row2["FI"]*100:.1f}%')
print(f'  sigma_b={row2["sigma_b_MPa"]:.3f} MPa  tau_s={row2["tau_s_MPa"]:.3f} MPa')
print(f'  tau_ult={row2["tau_ult_MPa"]:.3f} MPa  sigma_ult={row2["sigma_ult_MPa"]:.3f} MPa')
print()

print('=== 12. Node ratio evolution MED pessimistic P95 ===')
med_p95_all = df_s[(df_s.segment=='MED') & (df_s.degradation=='pessimistic') & (df_s.hydro=='P95') & (df_s.type=='stake')]
t_vals = sorted(med_p95_all.time_yr.unique())
ratios = []
for t_val in t_vals:
    sub_t = med_p95_all[med_p95_all.time_yr==t_val]
    nz_max   = sub_t[sub_t.is_node_zone==True]['FI'].max()
    nz_other = sub_t[sub_t.is_node_zone==False]['FI'].max()
    if nz_other > 0:
        ratios.append((t_val, nz_max, nz_other, nz_max/nz_other))
if ratios:
    t0_r = ratios[0][3]; tmax_r = ratios[-1][3]
    print(f'  t=0: ratio={t0_r:.2f}   t=max: ratio={tmax_r:.2f}')
    t_arr = np.array([r[0] for r in ratios])
    ratio_arr = np.array([r[3] for r in ratios])
    c = np.polyfit(t_arr, ratio_arr, 1)
    r2 = 1 - np.sum((ratio_arr - np.poly1d(c)(t_arr))**2)/np.sum((ratio_arr-ratio_arr.mean())**2)
    print(f'  Razao = {c[1]:.3f} + {c[0]:.3f}*t  R2={r2:.3f}')
    
# nodal FI exponential fit
print()
print('=== 13. Exponential fits nodal vs internodal MED pessimistic P95 ===')
for nz_val, label in [(True,'nodal'),(False,'internodal')]:
    sub = med_p95_all[med_p95_all.is_node_zone==nz_val].groupby('time_yr')['FI'].max().reset_index()
    sub = sub[sub['FI']>0]
    if len(sub) < 4:
        continue
    t = sub['time_yr'].values
    fi = sub['FI'].values
    def exp_func(t, a, b): return a * np.exp(b * t)
    try:
        popt, _ = curve_fit(exp_func, t, fi, p0=[0.001, 0.4], maxfev=5000)
        fi_pred = exp_func(t, *popt)
        r2 = 1 - np.sum((fi - fi_pred)**2)/np.sum((fi - fi.mean())**2)
        print(f'  {label}: FI = {popt[0]:.4f} * exp({popt[1]:.3f} * t)  R2={r2:.3f}')
    except Exception as e:
        print(f'  {label}: {e}')
