import pandas as pd, numpy as np

base = 'c:/Users/vidal/OneDrive/Documentos/13 - CLONEGIT/artigo-posdoc/3-EROSIBIDADE/1-MANUSCRITOS/5-SIMULACAO_FEM_BAMBU/resultados/'
df = pd.read_csv(base + 'fem3d_full.csv')
ds = pd.read_csv(base + 'fem3d_summary.csv')

df_s = df[df['type'] != 'colmo_embed']

print('=== FI MAX global (sem colmo_embed) ===')
worst = df_s.loc[df_s['FI'].idxmax()]
fi = worst['FI']
fs = worst['safety_factor']
seg = worst['segment']
hydro = worst['hydro']
deg = worst['degradation']
t = worst['time_yr']
print(f'FI_max={fi:.4f}  FS={fs:.2f}  seg={seg}  hydro={hydro}  deg={deg}  t={t}')
print()

med_p10 = df_s[(df_s['segment']=='MED') & (df_s['degradation']=='pessimistic') & (df_s['time_yr']==10.0)]
fi_st = med_p10[med_p10['type']=='stake']['FI'].max()
fi_co = med_p10[med_p10['type']=='colmo']['FI'].max()
fs_st = med_p10[med_p10['type']=='stake']['safety_factor'].min()
print(f'=== MED pessimistic t=10 ===')
print(f'  FI_max stake: {fi_st:.4f}  FS={fs_st:.2f}')
print(f'  FI_max colmo: {fi_co:.4f}')
print(f'  Ratio: {fi_st/fi_co:.0f}x')
print()

inf_p = df_s[(df_s['segment']=='INF') & (df_s['degradation']=='pessimistic') & (df_s['type']=='stake')]
r = inf_p.loc[inf_p['FI'].idxmax()]
print(f'INF pessimistic: FI={r["FI"]:.4f} FS={r["safety_factor"]:.0f} t={r["time_yr"]}')

sup_p = df_s[(df_s['segment']=='SUP') & (df_s['degradation']=='pessimistic') & (df_s['type']=='stake')]
r2 = sup_p.loc[sup_p['FI'].idxmax()]
print(f'SUP pessimistic: FI={r2["FI"]:.4f} FS={r2["safety_factor"]:.0f} t={r2["time_yr"]}')
print()

for deg2 in ['optimistic', 'baseline', 'pessimistic']:
    sub = df_s[(df_s['segment']=='MED') & (df_s['degradation']==deg2) & (df_s['hydro']=='median') & (df_s['type']=='stake')]
    t8  = sub[sub['time_yr']==8.0]['FI'].max()
    t10 = sub[sub['time_yr']==10.0]['FI'].max()
    print(f'MED {deg2} median: FI(t=8)={t8:.3f}  FI(t=10)={t10:.3f}')
print()

ref = ds[ds['degradation']=='baseline']
print(f'FS min (baseline all segs): {ref["safety_factor"].min():.1f}')

# Percentual stake capacity (FI_max = % da capacidade residual)
print(f'Percentual capacidade residual: {fi_st*100:.0f}%')
