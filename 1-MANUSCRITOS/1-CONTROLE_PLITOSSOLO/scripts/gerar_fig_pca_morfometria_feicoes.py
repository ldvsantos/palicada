from __future__ import annotations

import re
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.decomposition import PCA
from sklearn.preprocessing import StandardScaler

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt


ROOT = Path(r"C:\Users\vidal\OneDrive\Documentos\13 - CLONEGIT\artigo-posdoc\3-EROSIBIDADE")

MORF_XLSX = ROOT / r"2-DADOS\PLANILHA DE COLETA DE DADOS DE RAVINAS E VOÇOROCAS (1).xlsx"
SHEET = "Table 2"

OUT_PNG = (
    ROOT
    / r"1-MANUSCRITOS\2-CARACTERIZACAO_FEICAO\media\fig_S1_pca_morfometria.png"
)


# ── Depth class styles (matching Jussimara biplot conventions) ──
DEPTH_CLASSES = {
    'Rasa': {
        'feicoes': [2, 3],
        'color': '#c0392b',
        'marker': 's',
        'label': 'Rasa (< 0,5 m)',
        'size': 80,
    },
    'Mod. profunda': {
        'feicoes': [1, 4],
        'color': '#27ae60',
        'marker': '^',
        'label': 'Mod. profunda (0,5–1,5 m)',
        'size': 90,
    },
    'Profunda': {
        'feicoes': [5],
        'color': '#2980b9',
        'marker': 'o',
        'label': 'Profunda (≥ 1,5 m)',
        'size': 80,
    },
}

# reverse lookup: feicao -> class key
_feicao_to_class = {}
for cls_key, cls_info in DEPTH_CLASSES.items():
    for f in cls_info['feicoes']:
        _feicao_to_class[f] = cls_key


def _to_float(value: object) -> float:
    s = str(value).strip()
    if s == "" or s.lower() == "nan":
        return float("nan")
    # fix common typos
    s = s.replace("O", "0").replace("o", "0").replace("l", "1").replace("I", "1")
    s = s.replace(",", ".")
    # remove replicate prefixes like 1-0.75, 2-1.10
    s = re.sub(r"\b\d\s*-\s*(?=\d)", "", s)
    nums = [float(m.group(1)) for m in re.finditer(r"(\d+(?:\.\d+)?)", s)]
    return float(np.mean(nums)) if nums else float("nan")


def _extract_morfometria() -> pd.DataFrame:
    df = pd.read_excel(MORF_XLSX, sheet_name=SHEET, dtype=str)
    df = df.iloc[1:].copy()  # drop header-description row

    # known layout for this sheet
    col_feicao = "Ravina (Num)"
    col_comp = "Comprimento (montante/ Jusante) (m)"

    # segment columns by position (from earlier inspection)
    col_larg_med_sup = df.columns[5]
    col_alt_sup = df.columns[7]

    col_larg_med_med = df.columns[9]
    col_alt_med = df.columns[11]

    col_larg_med_inf = df.columns[13]
    col_alt_inf = df.columns[15]

    rows: list[dict[str, float]] = []
    for _, r in df.iterrows():
        feicao = _to_float(r.get(col_feicao))
        if np.isnan(feicao):
            continue

        comprimento = _to_float(r.get(col_comp))

        largura_media = np.nanmean(
            [
                _to_float(r.get(col_larg_med_sup)),
                _to_float(r.get(col_larg_med_med)),
                _to_float(r.get(col_larg_med_inf)),
            ]
        )

        prof_max = np.nanmax(
            [
                _to_float(r.get(col_alt_sup)),
                _to_float(r.get(col_alt_med)),
                _to_float(r.get(col_alt_inf)),
            ]
        )

        rows.append(
            {
                "feicao": int(round(feicao)),
                "comprimento_m": comprimento,
                "largura_media_m": largura_media,
                "prof_max_m": prof_max,
            }
        )

    out = pd.DataFrame(rows).drop_duplicates(subset=["feicao"]).set_index("feicao")
    return out


def main() -> None:
    out = _extract_morfometria()

    # PCA requires complete rows
    cols = ["comprimento_m", "largura_media_m", "prof_max_m"]
    complete = out.dropna(subset=cols).copy()

    if len(complete) < 3:
        raise SystemExit(f"Poucas feições completas para PCA (n={len(complete)}).")

    X = complete[cols].to_numpy(dtype=float)
    Xz = StandardScaler().fit_transform(X)

    pca = PCA(n_components=2, random_state=0)
    scores = pca.fit_transform(Xz)
    loadings = pca.components_.T  # (n_features, 2)
    explained = pca.explained_variance_ratio_

    print(f"PC1: {explained[0]*100:.1f}%")
    print(f"PC2: {explained[1]*100:.1f}%")
    print(f"Cumulative: {sum(explained)*100:.1f}%")

    # ── Scale factor for loading arrows ──
    scale_factor = (
        max(np.abs(scores).max(axis=0))
        / max(np.abs(loadings).max(axis=0))
        * 0.75
    )

    # ── Compute axis limits from data (scores + scaled loading tips) ──
    tips = loadings * scale_factor  # (n_features, 2)
    all_x = np.concatenate([scores[:, 0], tips[:, 0], [0.0]])
    all_y = np.concatenate([scores[:, 1], tips[:, 1], [0.0]])
    margin_x = (all_x.max() - all_x.min()) * 0.30  # 30% margin for labels
    margin_y = (all_y.max() - all_y.min()) * 0.30
    xlim = (all_x.min() - margin_x, all_x.max() + margin_x)
    ylim = (all_y.min() - margin_y, all_y.max() + margin_y)

    # ── Create figure (Jussimara style) ──
    fig, ax = plt.subplots(figsize=(8, 6), dpi=300)

    ax.set_xlim(xlim)
    ax.set_ylim(ylim)

    # Reference lines
    ax.axhline(0, color='#aaaaaa', linewidth=0.6, linestyle='--', zorder=1)
    ax.axvline(0, color='#aaaaaa', linewidth=0.6, linestyle='--', zorder=1)

    # ── Plot scatter by depth class ──
    feicao_list = complete.index.tolist()
    for cls_key, sty in DEPTH_CLASSES.items():
        mask = [f in sty['feicoes'] for f in feicao_list]
        if not any(mask):
            continue
        idx = [i for i, m in enumerate(mask) if m]
        ax.scatter(
            scores[idx, 0], scores[idx, 1],
            c=sty['color'], marker=sty['marker'], s=sty['size'],
            alpha=0.85, edgecolors='k', linewidths=0.5,
            label=sty['label'], zorder=3,
        )

    # ── Label points with feição numbers ──
    try:
        from adjustText import adjust_text
        _has_adjust = True
    except ImportError:
        _has_adjust = False

    texts = []
    for i, feicao in enumerate(feicao_list):
        cls_key = _feicao_to_class.get(feicao, list(DEPTH_CLASSES.keys())[0])
        color = DEPTH_CLASSES[cls_key]['color']
        texts.append(ax.text(
            scores[i, 0], scores[i, 1], f"F{feicao}",
            fontsize=10, color=color, fontweight='bold',
            ha='center', va='bottom', zorder=4,
        ))

    if _has_adjust:
        adjust_text(
            texts, ax=ax,
            arrowprops=dict(arrowstyle='-', color='gray', lw=0.3, alpha=0.4),
            expand=(1.4, 1.6),
            force_text=(0.35, 0.45),
            force_points=(0.25, 0.35),
            lim=200,
        )

    # ── Loading vectors with bbox labels ──
    var_labels = {
        "comprimento_m": "Comprimento",
        "largura_media_m": "Largura média",
        "prof_max_m": "Prof. máxima",
    }

    for i, var in enumerate(cols):
        tx = loadings[i, 0] * scale_factor
        ty = loadings[i, 1] * scale_factor

        ax.annotate(
            '', xy=(tx, ty), xytext=(0, 0),
            arrowprops=dict(
                arrowstyle='->', color='black', lw=1.6,
                shrinkA=0, shrinkB=2,
            ),
            zorder=5,
        )

        # offset label away from origin
        norm = np.sqrt(tx**2 + ty**2)
        ox = tx / norm * 0.15 if norm > 0 else 0.15
        oy = ty / norm * 0.15 if norm > 0 else 0.15

        ax.text(
            tx + ox, ty + oy, var_labels.get(var, var),
            fontsize=9, fontweight='bold',
            ha='left' if tx >= 0 else 'right',
            va='bottom' if ty >= 0 else 'top',
            color='black',
            bbox=dict(
                boxstyle='round,pad=0.25', facecolor='#fffde7',
                edgecolor='#666666', alpha=0.92, linewidth=0.6,
            ),
            zorder=6,
        )

    # ── Axis labels with variance ──
    ax.set_xlabel(
        f'PC1 ({explained[0]*100:.1f}%)',
        fontsize=13, fontweight='bold', labelpad=8,
    )
    ax.set_ylabel(
        f'PC2 ({explained[1]*100:.1f}%)',
        fontsize=13, fontweight='bold', labelpad=8,
    )

    # Legend
    ax.legend(
        loc='best', fontsize=9, framealpha=0.92,
        edgecolor='gray', fancybox=True, borderpad=0.8,
    )

    ax.tick_params(labelsize=10)
    ax.grid(True, alpha=0.15, linewidth=0.4)

    plt.tight_layout()

    OUT_PNG.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(OUT_PNG, dpi=300, bbox_inches='tight', facecolor='white')
    plt.close(fig)

    print(f"\nOK: {OUT_PNG}")


if __name__ == "__main__":
    main()
