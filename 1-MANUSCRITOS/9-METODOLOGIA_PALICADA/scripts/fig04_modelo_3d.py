"""Fig. 04 — Modelo 3D fiel de palicada de bambu em ravina (Plintossolo).

Calibrado pelo protocolo do manuscrito (Metodologia_Palicadas_Bambu.qmd):
  Feicao-tipo F1: D=1.10 m, largura media=1.37 m, secao em U.
  H = D/3 = 0.37 m. Estacas D=8 cm espacadas ~40 cm.
  Varas D=4 cm entrelacadas alternadamente. Ancoragem lateral 0.50 m.
  Deposito em cunha, espessura maxima ~0.45 m junto a palicada.

Geometria da cena:
  z=0 = fundo da ravina junto a palicada.
  Paredes sobem ate z~1.10 m (nivel do pasto).
  Palicada atravessa o talvegue de parede a parede.
  Terreno plano (pasto) no topo das margens.

Saida: media/modelagem_3d/04_modelo_3d_pyvista.png
"""

from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import pyvista as pv
from pykrige.ok import OrdinaryKriging
from pykrige.ok3d import OrdinaryKriging3D
from scipy.interpolate import RBFInterpolator, RegularGridInterpolator

# ===========================================================================
# 0. CONFIGURACAO — dimensoes REAIS da feicao-tipo F1
# ===========================================================================
SEED = 42
rng = np.random.default_rng(SEED)

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "media" / "modelagem_3d"
OUT.mkdir(parents=True, exist_ok=True)

# --- Ravina F1 (Tabuleiros Costeiros, Plintossolo) ------------------------
D_PROFUNDIDADE = 1.10    # profundidade maxima da ravina (m)
W_LARGURA_TOPO = 1.80    # largura no topo (m)
W_LARGURA_FUNDO = 0.55   # largura plana no fundo (m)
L_COMPRIMENTO = 6.0      # extensao a montante modelada (m)
EIXO_X = W_LARGURA_TOPO / 2  # centro da ravina no eixo x

# --- Palicada (conforme protocolo) ----------------------------------------
H_EFETIVA = 0.37          # altura efetiva acima do fundo (H = D/3)
PROJECAO_PONTA = 0.15     # projecao da estaca acima da vara mais alta
D_ESTACA = 0.08           # diametro das estacas (colmos 6-10 cm)
D_VARA = 0.04             # diametro das varas (colmos 3-5 cm)
ESP_ESTACAS = 0.40        # espacamento entre estacas (30-50 cm)
PENETRACAO_ESTACA = 0.40  # profundidade enterrada abaixo do fundo (m)
N_VARAS = 6               # numero de varas horizontais

# --- Deposito -------------------------------------------------------------
ESP_DEPOSITO_MAX = 0.45   # espessura maxima do sedimento junto a palicada

# --- Dominio da cena ------------------------------------------------------
MARGEM_LAT = 1.2   # pasto visivel alem da ravina
DOMINIO_X = (-MARGEM_LAT, W_LARGURA_TOPO + MARGEM_LAT)
DOMINIO_Y = (-0.5, L_COMPRIMENTO + 0.4)

# ===========================================================================
# 1. TERRENO — pasto plano com ravina entalhada
# ===========================================================================
def z_ravina(x: np.ndarray, y: np.ndarray) -> np.ndarray:
    """Cota do terreno natural.

    z = D_PROFUNDIDADE no pasto plano.
    Dentro da ravina, z desce ate 0 no fundo.
    Perfil U suave com talude curvo (cosseno).
    """
    d = np.abs(x - EIXO_X)
    meia_fundo = W_LARGURA_FUNDO / 2
    meia_talude = (W_LARGURA_TOPO - W_LARGURA_FUNDO) / 2

    z = np.full_like(d, D_PROFUNDIDADE, dtype=float)
    no_talude = (d > meia_fundo) & (d <= meia_fundo + meia_talude)
    frac = np.clip((d - meia_fundo) / meia_talude, 0, 1)
    z_talude = D_PROFUNDIDADE * 0.5 * (1 + np.cos(np.pi * frac))
    z = np.where(no_talude, z_talude, z)
    no_fundo = d <= meia_fundo
    z = np.where(no_fundo, 0.0, z)

    # Entalhe um pouco mais fundo perto da palicada
    aprof = -0.06 * np.exp(-np.maximum(y, 0) / 3.0) * no_fundo.astype(float)
    return z + aprof


def fator_dentro_ravina(x: np.ndarray) -> np.ndarray:
    """1 no fundo/talude inferior, 0 no pasto. Limita o deposito."""
    d = np.abs(x - EIXO_X)
    meia = W_LARGURA_FUNDO / 2 + (W_LARGURA_TOPO - W_LARGURA_FUNDO) / 4
    return np.where(
        d <= meia, 1.0,
        np.where(d <= meia + 0.10,
                 0.5 * (1 + np.cos(np.pi * (d - meia) / 0.10)),
                 0.0),
    )


# ===========================================================================
# 2. SONDAGENS SINTETICAS + KRIGAGENS
# ===========================================================================
def gerar_sondagens(n_pontos: int = 15) -> pd.DataFrame:
    nx, ny = 3, 5
    xs = np.linspace(EIXO_X - 0.18, EIXO_X + 0.18, nx)
    ys = np.linspace(0.25, L_COMPRIMENTO - 0.25, ny)
    XX, YY = np.meshgrid(xs, ys)
    pts = np.column_stack([XX.ravel(), YY.ravel()])
    pts += rng.normal(0, 0.05, size=pts.shape)
    if len(pts) > n_pontos:
        pts = pts[rng.choice(len(pts), n_pontos, replace=False)]

    registros = []
    for i, (x, y) in enumerate(pts, start=1):
        h = ESP_DEPOSITO_MAX * np.exp(-y / 2.0)
        h = max(0.04, h + rng.normal(0, 0.03))
        nz = rng.integers(4, 6)
        zs = np.linspace(0.03, h - 0.01, nz)
        for z in zs:
            rp = 22.0 + 90.0 * (z / ESP_DEPOSITO_MAX) + 14.0 * np.exp(-y / 2.5)
            rp += rng.normal(0, 5.0)
            registros.append(dict(
                borehole=f"S{i:02d}", x=x, y=y, z=z,
                h_local=h, RP_kPa=max(15.0, rp),
            ))
    return pd.DataFrame(registros)


def krigar_espessura(df: pd.DataFrame, nx: int = 60, ny: int = 80):
    pts = df.groupby("borehole").agg(
        x=("x", "mean"), y=("y", "mean"), h=("h_local", "mean")
    ).reset_index()
    gx = np.linspace(0, W_LARGURA_TOPO, nx)
    gy = np.linspace(0, L_COMPRIMENTO, ny)
    ok = OrdinaryKriging(
        pts["x"].values, pts["y"].values, pts["h"].values,
        variogram_model="exponential", verbose=False, enable_plotting=False,
    )
    z, _ = ok.execute("grid", gx, gy)
    return gx, gy, np.array(z)


def krigar_rp_3d(df: pd.DataFrame, nx: int = 25, ny: int = 35, nz: int = 12):
    gx = np.linspace(0, W_LARGURA_TOPO, nx)
    gy = np.linspace(0, L_COMPRIMENTO, ny)
    gz = np.linspace(0.02, ESP_DEPOSITO_MAX + 0.02, nz)
    ok3d = OrdinaryKriging3D(
        df["x"].values, df["y"].values, df["z"].values, df["RP_kPa"].values,
        variogram_model="exponential", verbose=False, enable_plotting=False,
    )
    rp, _ = ok3d.execute("grid", gx, gy, gz)
    return gx, gy, gz, np.array(rp)


# ===========================================================================
# 3. CONSTRUTORES DE MALHA
# ===========================================================================
def build_terreno(resol: float = 0.08) -> pv.StructuredGrid:
    xx = np.arange(DOMINIO_X[0], DOMINIO_X[1] + resol, resol)
    yy = np.arange(DOMINIO_Y[0], DOMINIO_Y[1] + resol, resol)
    GX, GY = np.meshgrid(xx, yy)
    GZ = z_ravina(GX, GY)
    return pv.StructuredGrid(GX, GY, GZ)


def build_deposito(gx_esp, gy_esp, esp_grid, gx3, gy3, gz3, rp3,
                   fine_xy: int = 60, nz: int = 16) -> pv.StructuredGrid:
    GX_c, GY_c = np.meshgrid(gx_esp, gy_esp)
    rbf = RBFInterpolator(
        np.column_stack([GX_c.ravel(), GY_c.ravel()]),
        esp_grid.ravel(), kernel="thin_plate_spline", smoothing=0.20,
    )
    gx_f = np.linspace(0, W_LARGURA_TOPO, fine_xy)
    gy_f = np.linspace(0, L_COMPRIMENTO, fine_xy)
    GX_f, GY_f = np.meshgrid(gx_f, gy_f)
    H = rbf(np.column_stack([GX_f.ravel(), GY_f.ravel()])).reshape(GX_f.shape)
    H = np.clip(H, 0.0, ESP_DEPOSITO_MAX * 1.05)
    H *= fator_dentro_ravina(GX_f)
    H = np.maximum(H, 0.0)
    Z_base = z_ravina(GX_f, GY_f)

    rp_xyz = np.transpose(rp3, (2, 1, 0))
    rp_interp = RegularGridInterpolator(
        (gx3, gy3, gz3), rp_xyz, bounds_error=False, fill_value=None,
    )

    nx_f, ny_f = fine_xy, fine_xy
    XX = np.zeros((nx_f, ny_f, nz))
    YY = np.zeros_like(XX)
    ZZ = np.zeros_like(XX)
    for i in range(nx_f):
        for j in range(ny_f):
            XX[i, j, :] = gx_f[i]
            YY[i, j, :] = gy_f[j]
            z_base_col = Z_base[j, i]
            z_topo_col = z_base_col + H[j, i]
            ZZ[i, j, :] = np.linspace(z_base_col, z_topo_col, nz)

    grid = pv.StructuredGrid(XX, YY, ZZ)
    pts = grid.points
    z_local = pts[:, 2] - z_ravina(pts[:, 0], pts[:, 1])
    z_local = np.clip(z_local, gz3.min(), gz3.max())
    rp_pts = rp_interp(np.column_stack([pts[:, 0], pts[:, 1], z_local]))
    z_norm = z_local / max(ESP_DEPOSITO_MAX, 0.01)
    rp_final = 0.55 * rp_pts + 0.45 * (25.0 + 90.0 * z_norm)
    grid["RP_kPa"] = np.clip(rp_final, 15.0, 140.0)
    return grid


def build_palicada_estacas() -> tuple[pv.PolyData, np.ndarray]:
    meia_fundo = W_LARGURA_FUNDO / 2
    x_min = EIXO_X - meia_fundo - 0.05
    x_max = EIXO_X + meia_fundo + 0.05
    n = max(3, int(round((x_max - x_min) / ESP_ESTACAS)) + 1)
    xs = np.linspace(x_min, x_max, n)
    estacas = []
    for x in xs:
        z_b = z_ravina(np.array([x]), np.array([0.0]))[0]
        z_topo = z_b + H_EFETIVA + PROJECAO_PONTA
        z_enterrada = z_b - PENETRACAO_ESTACA
        cyl = pv.Cylinder(
            center=(x, 0.0, (z_enterrada + z_topo) / 2),
            direction=(0, 0, 1),
            radius=D_ESTACA / 2,
            height=z_topo - z_enterrada,
            resolution=24,
        )
        estacas.append(cyl)
    merged = estacas[0]
    for e in estacas[1:]:
        merged = merged.merge(e)
    return merged, xs


def build_palicada_varas(xs_estacas: np.ndarray) -> pv.PolyData:
    eixo_xs = np.linspace(EIXO_X - 0.4, EIXO_X + 0.4, 60)
    z_min = z_ravina(eixo_xs, np.zeros_like(eixo_xs)).min()
    cotas = np.linspace(z_min + 0.05, z_min + H_EFETIVA - 0.03, N_VARAS)
    offset = D_ESTACA * 0.50   # ~4 cm de afastamento da linha central
    extens = 0.10
    x_inicio = xs_estacas[0] - extens
    x_fim = xs_estacas[-1] + extens
    pontos_x = np.concatenate(([x_inicio], xs_estacas, [x_fim]))
    n_pontos = len(pontos_x)

    tubos = []
    for k, z in enumerate(cotas):
        sinal_inicial = 1 if k % 2 == 0 else -1
        sinais = np.array([
            sinal_inicial * (1 if (i % 2 == 0) else -1)
            for i in range(n_pontos)
        ])
        polyline_pts = []
        for j in range(n_pontos - 1):
            x_a, x_b = pontos_x[j], pontos_x[j + 1]
            y_a = sinais[j] * offset
            y_b = sinais[j + 1] * offset
            n_sub = 10
            for t_idx in range(n_sub):
                t = t_idx / n_sub
                t_s = 0.5 * (1 - np.cos(np.pi * t))
                xx = x_a + (x_b - x_a) * t
                yy = y_a + (y_b - y_a) * t_s
                polyline_pts.append([xx, yy, z])
        pts_arr = np.array(polyline_pts)
        line = pv.lines_from_points(pts_arr)
        tube = line.tube(radius=D_VARA / 2, n_sides=14)
        tubos.append(tube)
    merged = tubos[0]
    for t in tubos[1:]:
        merged = merged.merge(t)
    return merged


def build_sondagens_tubos(df: pd.DataFrame) -> pv.PolyData:
    boreholes = df.groupby("borehole")
    tubos = []
    for _, grp in boreholes:
        x0, y0 = grp["x"].iloc[0], grp["y"].iloc[0]
        h0 = grp["h_local"].iloc[0]
        if fator_dentro_ravina(np.array([x0]))[0] < 0.15:
            continue
        z_b = z_ravina(np.array([x0]), np.array([y0]))[0]
        line = pv.Line((x0, y0, z_b + 0.003),
                       (x0, y0, z_b + max(h0, 0.04)), resolution=8)
        tube = line.tube(radius=0.030, n_sides=10)
        tubos.append(tube)
    if not tubos:
        return pv.PolyData()
    merged = tubos[0]
    for t in tubos[1:]:
        merged = merged.merge(t)
    return merged


# ===========================================================================
# 4. RENDERIZACAO
# ===========================================================================
def render_fig04(gx_esp, gy_esp, esp_grid, gx3, gy3, gz3, rp3, df_sond) -> None:
    terreno = build_terreno()
    deposito = build_deposito(gx_esp, gy_esp, esp_grid, gx3, gy3, gz3, rp3)
    estacas, xs_est = build_palicada_estacas()
    varas = build_palicada_varas(xs_est)
    tubos = build_sondagens_tubos(df_sond)

    pv.set_plot_theme("document")
    p = pv.Plotter(window_size=(1700, 1200), off_screen=True, border=False)
    p.set_background("white")

    # Iluminacao
    p.remove_all_lights()
    p.add_light(pv.Light(
        position=(EIXO_X + 3.0, -2.0, D_PROFUNDIDADE + 3.5),
        focal_point=(EIXO_X, L_COMPRIMENTO / 2, D_PROFUNDIDADE / 2),
        color="white", intensity=0.90,
    ))
    p.add_light(pv.Light(
        position=(EIXO_X - 2.0, L_COMPRIMENTO + 2.5, D_PROFUNDIDADE + 2.5),
        focal_point=(EIXO_X, L_COMPRIMENTO / 2, D_PROFUNDIDADE / 2),
        color="white", intensity=0.45,
    ))

    # Terreno completo (cor de solo)
    p.add_mesh(
        terreno, color="#c2b280", opacity=1.0,
        lighting=True, specular=0.05, smooth_shading=True,
    )

    # Deposito
    p.add_mesh(
        deposito, scalars="RP_kPa", cmap="YlOrBr",
        clim=(15, 130), opacity=0.97, lighting=True,
        specular=0.15, smooth_shading=True,
        scalar_bar_args=dict(
            title="RP (kPa)", vertical=True,
            position_x=0.91, position_y=0.15,
            width=0.030, height=0.50,
            label_font_size=13, title_font_size=15, color="black", n_labels=5,
        ),
    )

    # Palicada
    p.add_mesh(
        estacas, color="#d4a76a", lighting=True, specular=0.40,
        smooth_shading=True, pbr=True, roughness=0.48, metallic=0.04,
    )
    p.add_mesh(
        varas, color="#8b5a2b", lighting=True, specular=0.35,
        smooth_shading=True, pbr=True, roughness=0.55, metallic=0.04,
    )

    # Sondagens
    if tubos.n_cells > 0:
        p.add_mesh(
            tubos, color="#2a3478", lighting=True,
            specular=0.30, smooth_shading=True,
        )

    p.add_axes(xlabel="x", ylabel="y", zlabel="z",
               line_width=2, color="dimgray", labels_off=False)

    # Camera: isometrica com a palicada visivel no primeiro plano
    p.camera.position = (EIXO_X + 2.8, -2.2, D_PROFUNDIDADE + 1.8)
    p.camera.focal_point = (EIXO_X, L_COMPRIMENTO / 2.5, D_PROFUNDIDADE / 3)
    p.camera.up = (0, 0, 1)
    p.camera.zoom(1.10)

    p.enable_anti_aliasing("ssaa", multi_samples=3)

    img = p.screenshot(return_img=True, transparent_background=False)
    p.close()

    fig, ax = plt.subplots(figsize=(13.5, 9.5), facecolor="white")
    ax.imshow(img); ax.axis("off")
    ax.set_title(
        "Modelo 3D — deposito retido pela palicada de bambu na ravina F1",
        fontsize=15, pad=10,
    )
    fig.tight_layout()
    fig.savefig(OUT / "04_modelo_3d_pyvista.png",
                dpi=300, facecolor="white", bbox_inches="tight")
    plt.close(fig)
    print("      [OK] 04_modelo_3d_pyvista.png renderizado")


def main() -> None:
    print("[fig04] Gerando sondagens...")
    df = gerar_sondagens()
    print("[fig04] Krigando espessura 2D...")
    gx, gy, esp = krigar_espessura(df)
    print("[fig04] Krigando RP 3D...")
    gx3, gy3, gz3, rp3 = krigar_rp_3d(df)
    print("[fig04] Renderizando...")
    render_fig04(gx, gy, esp, gx3, gy3, gz3, rp3, df)


if __name__ == "__main__":
    main()
