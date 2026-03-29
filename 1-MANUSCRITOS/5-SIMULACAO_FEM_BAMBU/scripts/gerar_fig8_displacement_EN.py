"""
Figure 8 — Maximum lateral displacement over time (EN version).
3 segments (INF, MED, SUP) / P95 / pessimistic.
"""
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from pathlib import Path
import json

plt.rcParams.update({
    "font.family": "serif",
    "font.size": 11,
    "axes.labelsize": 12,
    "axes.titlesize": 13,
    "legend.fontsize": 9,
    "figure.dpi": 150,
    "savefig.dpi": 300,
    "savefig.bbox": "tight",
})

BASE = Path(__file__).resolve().parent.parent
RES = BASE / 'resultados'
FIG = BASE / 'figuras' / 'versao_EN'
FIG.mkdir(parents=True, exist_ok=True)


def main():
    ds = pd.read_csv(RES / 'fem3d_summary.csv')

    fig, ax = plt.subplots(figsize=(8, 5))
    colors_s = {'INF': '#2ca02c', 'MED': '#d62728', 'SUP': '#1f77b4'}

    for seg in ['INF', 'MED', 'SUP']:
        sub = ds[(ds['segment']==seg) & (ds['hydro']=='P95') &
                 (ds['degradation']=='pessimistic')].sort_values('time_yr')
        ax.plot(sub['time_yr'], sub['max_disp_lat_mm'],
                'o-', color=colors_s[seg], lw=1.8, ms=3,
                label=f'{seg} (L={sub["width_m"].iloc[0]:.1f} m)')

    ax.set_xlabel('Time (years)')
    ax.set_ylabel('Maximum lateral displacement (mm)')
    ax.set_title('Lateral deflection — P95 pessimistic')
    ax.legend(fontsize=9)
    ax.grid(True, alpha=0.3)
    ax.set_xlim(0, 10)
    fig.tight_layout()

    for ext in ['png', 'pdf']:
        fig.savefig(FIG / f'Fig_8_displacement.{ext}')
    plt.close(fig)
    print(f'  Fig_8_displacement (EN) saved to: {FIG}')


if __name__ == '__main__':
    main()
