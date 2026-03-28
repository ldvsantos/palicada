import pandas as pd
ds = pd.read_csv('1-MANUSCRITOS/5-SIMULACAO_FEM_BAMBU/resultados/fem3d_summary.csv')

print("=== WORST PER HYDRO ===")
for h in ['median','P90','P95']:
    sub = ds[ds['hydro']==h]
    w = sub.loc[sub['max_FI'].idxmax()]
    print(f"  {h}: {w['segment']}/{w['degradation']} t={w['time_yr']:.1f} "
          f"FI={w['max_FI']:.6f} FS={w['safety_factor']:.1f}")

print("\n=== ALL SEGMENTS t=10 pessimistic ===")
for s in ['INF','MED','SUP']:
    for h in ['median','P90','P95']:
        sub = ds[(ds['segment']==s)&(ds['hydro']==h)
                 &(ds['degradation']=='pessimistic')&(ds['time_yr']==10)]
        if len(sub)>0:
            r = sub.iloc[0]
            print(f"  {s}/{h}: FI={r['max_FI']:.6f} FS={r['safety_factor']:.1f}")

print("\n=== MED/P95/pessimistic evolution ===")
sub = ds[(ds['segment']=='MED')&(ds['hydro']=='P95')&(ds['degradation']=='pessimistic')]
for _,r in sub.iterrows():
    if r['max_FI']>0.01:
        print(f"  t={r['time_yr']:5.1f} FI={r['max_FI']:.6f} FS={r['safety_factor']:6.1f} d={r['max_disp_lat_mm']:.2f}")

print("\n=== MED/P95/baseline evolution ===")
sub = ds[(ds['segment']=='MED')&(ds['hydro']=='P95')&(ds['degradation']=='baseline')]
for _,r in sub.iterrows():
    if r['max_FI']>0.01:
        print(f"  t={r['time_yr']:5.1f} FI={r['max_FI']:.6f} FS={r['safety_factor']:6.1f} d={r['max_disp_lat_mm']:.2f}")
