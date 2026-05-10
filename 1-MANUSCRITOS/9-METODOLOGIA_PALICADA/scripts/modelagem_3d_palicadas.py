"""Modelagem 3D profissional do deposito sedimentar a montante de palicadas
permeaveis de bambu — Ravina 1, Plintossolo, Tabuleiros Costeiros (SE).

Inspirada na rotina de caracterizacao geotecnica de barragens de rejeito
(krigagem ordinaria 3D de NSPT -> modelo de blocos). O analogo e a
resistencia a penetracao de bolso (RP, kPa) do prisma sedimentar retido,
calibrado pelos dados de campo LIMPO (parcelas 4.1-4.5) de 13/05/2025 a
24/11/2025.

Motor 3D: PyVista + VTK (StructuredGrid terrain-following + smooth shading).
Motor 2D: Matplotlib.

ABORDAGEM (revisada 2026-05-09)
-------------------------------
A versao anterior usava clip_surface sobre voxels (bordas serrilhadas). Esta
versao constroi o solido como StructuredGrid terrain-following (cada coluna
XY tem Z indo de 0 ate a superficie), produzindo um corpo continuo sem
artefatos de voxel — analogo ao visual de modelos geotecnicos profissionais
de barragens de rejeito.

Saidas (300 dpi) em ../media/modelagem_3d/:
  01_planta_amostragem.png        — mapa de sondagens com espessura
  02_variograma.png               — semivariograma experimental + modelo
  03_superficie_krigada.png       — wireframe 3D + isolinhas 2D
  04_modelo_3d_pyvista.png        — modelo profissional (2 views)
  05_secoes_xz_yz.png             — cortes longitudinal e transversal (RP)
  06_curva_enchimento.png         — volume acumulado vs. tempo
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
from scipy.ndimage import gaussian_filter

# ---------------------------------------------------------------------------
# 0. Configuracao
# ---------------------------------------------------------------------------
SEED = 42
rng = np.random.default_rng(SEED)

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "media" / "modelagem_3d"
OUT.mkdir(parents=True, exist_ok=True)

DATA_CSV = (
    ROOT.parents[1] / "2-DADOS" / "Sedimentos_talude_LIMPO_PEDRA_dados_longos.csv"
)
COORDS_TXT = ROOT.parents[1] / "2-DADOS" / "DADOS" / "coordenadas ravinas.txt"

LARGURA_X = 4.0
COMPRIMENTO_Y = 6.0
ESP_MAX = 0.55
ALTURA_PALICADA = 0.80

RES_Z = 28  # numero de camadas verticais no solido terrain-following


# ===========================================================================
# 1. Calibracao com dados de campo
# ===========================================================================
def calibrar_volume_campo() -> tuple[float, pd.DataFrame]:
    df = pd.read_csv(DATA_CSV)
    limpo = df[df["tratamento"] == "LIMPO"].copy()
    limpo["data"] = pd.to_datetime(limpo["data"])
    acum = (
        limpo.sort_values("data")
        .groupby(["codigo_parcela", "data"], as_index=False)["sedimento_g"]
        .sum()
    )
    acum["acum_g"] = acum.groupby("codigo_parcela")["sedimento_g"].cumsum()
    massa_media_g = acum.groupby("codigo_parcela")["acum_g"].max().mean()
    rho_b = 1.40e6
    area_parcela = 1.0
    area_bacia = 250.0
    vol_especifico = massa_media_g / (rho_b * area_parcela)
    vol_palicada = vol_especifico * area_bacia
    return vol_palicada, acum


# ===========================================================================
# 2. Sondagens sinteticas
# ===========================================================================
def gerar_sondagens(n_pontos: int = 24) -> pd.DataFrame:
    nx, ny = 4, 6
    xs = np.linspace(0.4, LARGURA_X - 0.4, nx)
    ys = np.linspace(0.3, COMPRIMENTO_Y - 0.3, ny)
    XX, YY = np.meshgrid(xs, ys)
    pts = np.column_stack([XX.ravel(), YY.ravel()])
    pts += rng.normal(0, 0.12, size=pts.shape)
    if len(pts) > n_pontos:
        pts = pts[rng.choice(len(pts), n_pontos, replace=False)]

    registros = []
    for i, (x, y) in enumerate(pts, start=1):
        h = ESP_MAX * np.exp(-y / 2.6) * (
            1.0 - 0.18 * abs(x - LARGURA_X / 2) / (LARGURA_X / 2)
        )
        h = max(0.08, h + rng.normal(0, 0.04))
        nz = rng.integers(4, 7)
        zs = np.linspace(0.05, h - 0.02, nz)
        for z in zs:
            rp = (
                28.0
                + 95.0 * (z / ESP_MAX)
                + 18.0 * np.exp(-y / 3.0)
                - 6.0 * abs(x - LARGURA_X / 2) / (LARGURA_X / 2)
                + rng.normal(0, 6.5)
            )
            registros.append(
                dict(
                    borehole=f"S{i:02d}",
                    x=x, y=y, z=z, h_local=h,
                    RP_kPa=max(15.0, rp),
                )
            )
    return pd.DataFrame(registros)


# ===========================================================================
# 3. Krigagens
# ===========================================================================
def krigar_espessura(df: pd.DataFrame, nx: int = 80, ny: int = 100):
    pts = (
        df.groupby("borehole")
        .agg(x=("x", "mean"), y=("y", "mean"), h=("h_local", "mean"))
        .reset_index()
    )
    gx = np.linspace(0, LARGURA_X, nx)
    gy = np.linspace(0, COMPRIMENTO_Y, ny)
    ok = OrdinaryKriging(
        pts["x"].values, pts["y"].values, pts["h"].values,
        variogram_model="spherical", verbose=False, enable_plotting=False,
    )
    z, ss = ok.execute("grid", gx, gy)
    return gx, gy, np.array(z), np.array(ss), pts, ok


def krigar_rp_3d(df: pd.DataFrame, nx: int = 40, ny: int = 50, nz: int = 18):
    gx = np.linspace(0, LARGURA_X, nx)
    gy = np.linspace(0, COMPRIMENTO_Y, ny)
    gz = np.linspace(0.02, ESP_MAX, nz)
    ok3d = OrdinaryKriging3D(
        df["x"].values, df["y"].values, df["z"].values, df["RP_kPa"].values,
        variogram_model="exponential", verbose=False, enable_plotting=False,
    )
    rp, ss = ok3d.execute("grid", gx, gy, gz)
    return gx, gy, gz, np.array(rp), np.array(ss), ok3d


# ===========================================================================
# 4. Topografia
# ===========================================================================
def gerar_topografia_ravina(resol: float = 0.10) -> pv.StructuredGrid:
    coords = np.loadtxt(COORDS_TXT)
    x_utm, y_utm, z_utm = coords[:, 1], coords[:, 2], coords[:, 3]
    x_rel = x_utm - x_utm.mean()
    y_rel = y_utm - y_utm.mean()
    escala = 10.0 / (x_rel.max() - x_rel.min())
    x_loc = x_rel * escala
    y_loc = y_rel * escala
    z_loc = (z_utm - z_utm.min()) * 0.15

    rbf = RBFInterpolator(
        np.column_stack([x_loc, y_loc]), z_loc,
        kernel="thin_plate_spline", smoothing=0.5,
    )

    pad = 1.8
    xx = np.linspace(-pad, LARGURA_X + pad, int((LARGURA_X + 2 * pad) / resol))
    yy = np.linspace(-1.2, COMPRIMENTO_Y + 1.8, int((COMPRIMENTO_Y + 3.0) / resol))
    GX, GY = np.meshgrid(xx, yy)
    pts_grid = np.column_stack([GX.ravel(), GY.ravel()])
    Z_topo = rbf(pts_grid).reshape(GX.shape)

    centro_x = LARGURA_X / 2
    dist_centro = np.abs(GX - centro_x)
    meia_largura = LARGURA_X / 2 + 0.6
    canal = np.where(
        dist_centro < meia_largura,
        -0.40 * (1 - (dist_centro / meia_largura) ** 2) * np.exp(-GY / 8.0),
        0.0,
    )
    Z_final = gaussian_filter(Z_topo + canal, sigma=1.5)
    return pv.StructuredGrid(GX, GY, Z_final)


# ===========================================================================
# 5. Figuras 2D
# ===========================================================================
def fig01_planta(df_sond: pd.DataFrame) -> None:
    pts = (
        df_sond.groupby("borehole")
        .agg(x=("x", "mean"), y=("y", "mean"), h=("h_local", "mean"))
        .reset_index()
    )
    fig, ax = plt.subplots(figsize=(6.5, 6.0))
    sc = ax.scatter(
        pts["x"], pts["y"], c=pts["h"] * 100, s=120,
        cmap="YlOrBr", edgecolor="k", linewidth=0.6,
    )
    for _, r in pts.iterrows():
        ax.text(r["x"] + 0.06, r["y"] + 0.06, r["borehole"], fontsize=7)
    ax.axhline(0, color="saddlebrown", lw=4, label="Palicada (y = 0)")
    ax.set_xlim(-0.2, LARGURA_X + 0.2)
    ax.set_ylim(-0.4, COMPRIMENTO_Y + 0.2)
    ax.set_xlabel("x — transversal (m)")
    ax.set_ylabel("y — longitudinal a montante (m)")
    ax.set_aspect("equal")
    cb = fig.colorbar(sc, ax=ax, shrink=0.85)
    cb.set_label("Espessura amostrada (cm)")
    ax.set_title(f"Planta de sondagens (n = {pts.shape[0]})")
    ax.legend(loc="upper right", fontsize=8)
    fig.tight_layout()
    fig.savefig(OUT / "01_planta_amostragem.png", dpi=300)
    plt.close(fig)


def fig02_variograma(ok3d: OrdinaryKriging3D) -> None:
    lags = ok3d.lags
    semi = ok3d.semivariance
    psill, rng_, nug = ok3d.variogram_model_parameters
    h = np.linspace(0, lags.max() * 1.05, 200)
    gamma = nug + psill * (1.0 - np.exp(-3.0 * h / rng_))
    fig, ax = plt.subplots(figsize=(6.5, 4.5))
    ax.plot(lags, semi, "ko", label="Semivariancia experimental")
    ax.plot(
        h, gamma, "r-", lw=2,
        label=f"Modelo exponencial: nugget={nug:.1f}, "
              f"sill={psill+nug:.1f}, range={rng_:.2f} m",
    )
    ax.set_xlabel("Distancia h (m)")
    ax.set_ylabel(r"$\gamma(h)$  (kPa$^2$)")
    ax.set_title("Variograma 3D — RP (analogo NSPT)")
    ax.grid(alpha=0.3)
    ax.legend(fontsize=8)
    fig.tight_layout()
    fig.savefig(OUT / "02_variograma.png", dpi=300)
    plt.close(fig)


def fig03_superficie(gx, gy, z, pts) -> None:
    GX, GY = np.meshgrid(gx, gy)
    fig = plt.figure(figsize=(12.5, 5.8))
    gs = fig.add_gridspec(1, 2, width_ratios=(1.18, 1.0), wspace=0.18)
    ax1 = fig.add_subplot(gs[0, 0], projection="3d")
    surf = ax1.plot_surface(
        GX, GY, z * 100, cmap="YlOrBr", linewidth=0.15,
        edgecolor=(0.62, 0.42, 0.20, 0.18), antialiased=True, alpha=0.96,
    )
    ax1.contour(
        GX, GY, z * 100, zdir="z", offset=0,
        levels=np.arange(10, 55, 5), colors="0.28", linewidths=0.55,
        alpha=0.70,
    )
    ax1.plot([0, LARGURA_X], [0, 0], [0, 0], color="saddlebrown", lw=6)
    ax1.scatter(
        pts["x"], pts["y"], pts["h"] * 100,
        c="k", s=22, depthshade=False, zorder=5,
    )
    ax1.set_xlabel("x (m)")
    ax1.set_ylabel("y (m)")
    ax1.set_zlabel("Espessura (cm)")
    ax1.set_xlim(0, LARGURA_X)
    ax1.set_ylim(0, COMPRIMENTO_Y)
    ax1.set_zlim(0, 55)
    ax1.set_box_aspect((LARGURA_X, COMPRIMENTO_Y, 1.35))
    ax1.view_init(elev=64, azim=-92)
    ax1.text(LARGURA_X * 0.05, -0.18, 1.5, "paliçada", color="saddlebrown", fontsize=9)
    ax1.text(LARGURA_X * 0.68, COMPRIMENTO_Y * 0.82, 7, "montante", color="0.25", fontsize=9)
    ax1.grid(False)
    ax1.set_title("(a) Superficie krigada em planta obliqua")
    fig.colorbar(surf, ax=ax1, shrink=0.68, pad=0.02, label="cm")

    ax2 = fig.add_subplot(gs[0, 1])
    cf = ax2.contourf(GX, GY, z * 100, levels=12, cmap="YlOrBr")
    cs = ax2.contour(GX, GY, z * 100, levels=8, colors="k", linewidths=0.5)
    ax2.clabel(cs, fontsize=7, fmt="%d")
    ax2.scatter(pts["x"], pts["y"], c="k", s=20, marker="x")
    ax2.axhline(0, color="saddlebrown", lw=3)
    ax2.annotate(
        "montante", xy=(3.55, 5.35), xytext=(3.55, 4.35),
        ha="center", va="center", fontsize=8, color="0.2",
        arrowprops=dict(arrowstyle="-|>", color="0.2", lw=1.0),
    )
    ax2.text(0.10, 0.12, "paliçada", color="saddlebrown", fontsize=8,
             va="bottom")
    ax2.set_xlabel("x (m)")
    ax2.set_ylabel("y (m)")
    ax2.set_aspect("equal")
    ax2.set_xlim(0, LARGURA_X)
    ax2.set_ylim(0, COMPRIMENTO_Y)
    ax2.set_title("(b) Mapa de isolinhas de espessura (cm)")
    fig.colorbar(cf, ax=ax2, shrink=0.85, label="cm")
    fig.savefig(OUT / "03_superficie_krigada.png", dpi=300)
    plt.close(fig)


# ===========================================================================
# 6. CONSTRUTORES DO MODELO 3D PROFISSIONAL
# ===========================================================================
def _build_terrain_following_solid(
    gx_esp: np.ndarray,
    gy_esp: np.ndarray,
    esp_grid: np.ndarray,
    rp_xyz: np.ndarray,
    gx3: np.ndarray,
    gy3: np.ndarray,
    gz3: np.ndarray,
    nz: int = RES_Z,
    fine_xy: int = 90,
) -> pv.StructuredGrid:
    """Solido terrain-following do deposito.

    Constroi StructuredGrid (nx_f, ny_f, nz) onde para cada coluna XY o eixo Z
    vai de 0 ate a espessura local krigada. RP e amostrado nos pontos.
    Resultado: superficies suaves, sem voxels visiveis.
    """
    # Refina a superficie com RBF
    GX_c, GY_c = np.meshgrid(gx_esp, gy_esp)
    pts_in = np.column_stack([GX_c.ravel(), GY_c.ravel()])
    rbf = RBFInterpolator(pts_in, esp_grid.ravel(),
                          kernel="thin_plate_spline", smoothing=0.15)
    gx_f = np.linspace(0, LARGURA_X, fine_xy)
    gy_f = np.linspace(0, COMPRIMENTO_Y, fine_xy)
    GX_f, GY_f = np.meshgrid(gx_f, gy_f)
    Z_surf = rbf(np.column_stack([GX_f.ravel(), GY_f.ravel()])).reshape(GX_f.shape)
    Z_surf = np.maximum(Z_surf, 0.005)

    # Interpolador 3D de RP (em x, y, z)
    rp_interp = RegularGridInterpolator(
        (gx3, gy3, gz3), rp_xyz,
        bounds_error=False, fill_value=None,
    )

    nx_f, ny_f = fine_xy, fine_xy
    XX = np.zeros((nx_f, ny_f, nz))
    YY = np.zeros_like(XX)
    ZZ = np.zeros_like(XX)
    for i in range(nx_f):
        for j in range(ny_f):
            XX[i, j, :] = gx_f[i]
            YY[i, j, :] = gy_f[j]
            ZZ[i, j, :] = np.linspace(0.0, Z_surf[j, i], nz)

    grid = pv.StructuredGrid(XX, YY, ZZ)

    # Atribui RP nos pontos (ponto, nao celula -> sombreamento mais suave)
    pts = grid.points
    # Recorta z dentro do dominio krigado
    z_clip = np.clip(pts[:, 2], gz3.min(), gz3.max())
    rp_pts = rp_interp(np.column_stack([pts[:, 0], pts[:, 1], z_clip]))
    # Reforco da estratificacao por compactacao em profundidade
    z_norm = pts[:, 2] / max(Z_surf.max(), 0.05)
    rp_final = 0.55 * rp_pts + 0.45 * (25.0 + 95.0 * z_norm)
    rp_final = np.clip(rp_final, 15.0, 140.0)
    grid["RP_kPa"] = rp_final
    return grid


def _build_palicada_3d() -> pv.PolyData:
    """Palicada como caixa 3D fechada com espessura."""
    espessura = 0.10
    box = pv.Box(
        bounds=(
            -0.10, LARGURA_X + 0.10,
            -espessura / 2, espessura / 2,
            -0.08, ALTURA_PALICADA,
        )
    )
    return box.triangulate()


def _build_estacas_verticais(n: int = 9) -> pv.PolyData:
    """Estacas verticais que sustentam a palicada (visual de bambu)."""
    xs = np.linspace(0.0, LARGURA_X, n)
    estacas = []
    for x in xs:
        cyl = pv.Cylinder(
            center=(x, 0.0, ALTURA_PALICADA / 2 - 0.04),
            direction=(0, 0, 1),
            radius=0.035,
            height=ALTURA_PALICADA + 0.30,
            resolution=24,
        )
        estacas.append(cyl)
    if not estacas:
        return pv.PolyData()
    merged = estacas[0]
    for e in estacas[1:]:
        merged = merged.merge(e)
    return merged


def _build_varas_horizontais(n: int = 6) -> pv.PolyData:
    """Varas horizontais entrelacadas (visual de palicada)."""
    zs = np.linspace(-0.05, ALTURA_PALICADA - 0.05, n)
    varas = []
    for k, z in enumerate(zs):
        y_off = 0.025 if k % 2 == 0 else -0.025
        cyl = pv.Cylinder(
            center=(LARGURA_X / 2, y_off, z),
            direction=(1, 0, 0),
            radius=0.025,
            height=LARGURA_X + 0.15,
            resolution=18,
        )
        varas.append(cyl)
    if not varas:
        return pv.PolyData()
    merged = varas[0]
    for v in varas[1:]:
        merged = merged.merge(v)
    return merged


def _build_sondagens_tubos(df_sond: pd.DataFrame) -> pv.PolyData:
    """Tubos verticais coloridos pelo RP medio."""
    boreholes = df_sond.groupby("borehole")
    tubos = []
    for name, grp in boreholes:
        x0 = grp["x"].iloc[0]
        y0 = grp["y"].iloc[0]
        h0 = grp["h_local"].iloc[0]
        rp_med = grp["RP_kPa"].mean()
        line_pts = np.array([[x0, y0, 0.005], [x0, y0, max(h0, 0.06)]])
        line = pv.Line(line_pts[0], line_pts[1], resolution=10)
        tube = line.tube(radius=0.04, n_sides=10)
        tube["RP_kPa"] = np.full(tube.n_points, rp_med)
        tubos.append(tube)
    if not tubos:
        return pv.PolyData()
    merged = tubos[0]
    for t in tubos[1:]:
        merged = merged.merge(t)
    return merged


# ===========================================================================
# 7. FIGURA 4 — Modelo 3D profissional
# ===========================================================================
def fig04_modelo_3d_pyvista(
    gx_esp, gy_esp, esp_grid,
    gx3, gy3, gz3, rp3,
    topo, df_sond,
) -> None:
    rp_xyz = np.transpose(rp3, (2, 1, 0))  # (nx, ny, nz)
    deposit = _build_terrain_following_solid(
        gx_esp, gy_esp, esp_grid, rp_xyz, gx3, gy3, gz3,
    )
    palicada = _build_palicada_3d()
    estacas = _build_estacas_verticais(n=9)
    varas = _build_varas_horizontais(n=6)
    sond_tubos = _build_sondagens_tubos(df_sond)

    clim = (15, 140)
    cmap_name = "YlOrBr"

    def _build_plotter(view_label: str, cam_pos, cam_focal, scalar_x: float):
        pv.set_plot_theme("document")
        p = pv.Plotter(window_size=(1300, 1150), off_screen=True, border=False)
        # Iluminacao de tres pontos
        p.remove_all_lights()
        light_key = pv.Light(position=(LARGURA_X * 1.5, -COMPRIMENTO_Y * 0.5, ESP_MAX * 8),
                             focal_point=(LARGURA_X / 2, COMPRIMENTO_Y / 2, 0),
                             color="white", intensity=0.85)
        light_fill = pv.Light(position=(-LARGURA_X * 0.5, COMPRIMENTO_Y * 1.5, ESP_MAX * 5),
                              focal_point=(LARGURA_X / 2, COMPRIMENTO_Y / 2, 0),
                              color="white", intensity=0.45)
        light_back = pv.Light(position=(LARGURA_X * 0.5, COMPRIMENTO_Y * 2.5, ESP_MAX * 3),
                              focal_point=(LARGURA_X / 2, COMPRIMENTO_Y / 2, 0),
                              color="#cce0ff", intensity=0.30)
        p.add_light(light_key); p.add_light(light_fill); p.add_light(light_back)

        # Topografia
        p.add_mesh(topo, color="#9bb88a", opacity=0.32,
                   lighting=True, specular=0.04, smooth_shading=True)
        # Solido do deposito (smooth shading => sem voxels)
        p.add_mesh(
            deposit, scalars="RP_kPa", cmap=cmap_name,
            opacity=0.95, lighting=True, specular=0.20,
            smooth_shading=True, clim=clim, show_edges=False,
            scalar_bar_args=dict(
                title="RP (kPa)", vertical=True,
                position_x=scalar_x, position_y=0.20,
                width=0.035, height=0.40,
                label_font_size=14, title_font_size=16, color="black",
            ),
        )
        # Palicada
        p.add_mesh(palicada, color="#5b3a1d", opacity=0.85,
                   lighting=True, specular=0.18, smooth_shading=True)
        p.add_mesh(estacas, color="#c9a66b", opacity=1.0,
                   lighting=True, specular=0.45, smooth_shading=True,
                   pbr=True, roughness=0.45, metallic=0.05)
        p.add_mesh(varas, color="#7a5a2e", opacity=1.0,
                   lighting=True, specular=0.40, smooth_shading=True,
                   pbr=True, roughness=0.50, metallic=0.05)
        # Sondagens
        if sond_tubos.n_cells > 0:
            p.add_mesh(sond_tubos, scalars="RP_kPa", cmap="plasma",
                       opacity=1.0, lighting=True, specular=0.35,
                       smooth_shading=True, clim=clim, show_scalar_bar=False)

        p.add_axes(xlabel="x (m)", ylabel="y (m)", zlabel="z (m)",
                   line_width=2, labels_off=False, color="dimgray")
        p.camera.position = cam_pos
        p.camera.focal_point = cam_focal
        p.camera.up = (0, 0, 1)
        p.set_background("white")
        p.enable_anti_aliasing("ssaa", multi_samples=3)
        return p

    # ----- Vista (a): isometrica de JUSANTE (paliçada + depósito atrás) ----
    pa = _build_plotter(
        "iso_jusante",
        cam_pos=(LARGURA_X * 1.8, -COMPRIMENTO_Y * 0.9, ESP_MAX * 5.5),
        cam_focal=(LARGURA_X / 2, COMPRIMENTO_Y / 2.5, ESP_MAX / 4),
        scalar_x=0.04,
    )
    img_a = pa.screenshot(return_img=True, transparent_background=False)
    pa.close()

    # ----- Vista (b): isometrica de MONTANTE (vê a face cheia do depósito) -
    pb = _build_plotter(
        "iso_montante",
        cam_pos=(-LARGURA_X * 0.6, COMPRIMENTO_Y * 1.8, ESP_MAX * 5.5),
        cam_focal=(LARGURA_X / 2, COMPRIMENTO_Y / 2.5, ESP_MAX / 4),
        scalar_x=0.93,
    )
    img_b = pb.screenshot(return_img=True, transparent_background=False)
    pb.close()

    # ----- Composicao final em matplotlib ---------------------------------
    fig, axes = plt.subplots(1, 2, figsize=(18, 8), facecolor="white")
    axes[0].imshow(img_a); axes[0].axis("off")
    axes[0].set_title("(a) Vista isometrica de jusante (paliçada em primeiro plano)",
                      fontsize=15, pad=8)
    axes[1].imshow(img_b); axes[1].axis("off")
    axes[1].set_title("(b) Vista isometrica de montante (face do deposito)",
                      fontsize=15, pad=8)
    fig.tight_layout()
    fig.savefig(OUT / "04_modelo_3d_pyvista.png", dpi=300, facecolor="white",
                bbox_inches="tight")
    plt.close(fig)
    print("      [OK] 04_modelo_3d_pyvista.png renderizado")


# ===========================================================================
# 8. Cortes
# ===========================================================================
def fig05_secoes(gx, gy, gz, rp) -> None:
    rp_xyz = np.transpose(rp, (2, 1, 0))
    ix = rp_xyz.shape[0] // 2
    sec_yz = rp_xyz[ix, :, :]
    iy = int(np.argmin(np.abs(gy - 1.0)))
    sec_xz = rp_xyz[:, iy, :]

    fig, axes = plt.subplots(1, 2, figsize=(12, 4.5))
    YY, ZZ = np.meshgrid(gy, gz, indexing="ij")
    cf1 = axes[0].contourf(YY, ZZ, sec_yz, levels=14, cmap="YlOrBr")
    axes[0].invert_yaxis()
    axes[0].set_xlabel("y (m) — distancia a montante da palicada")
    axes[0].set_ylabel("z (m) — profundidade no deposito")
    axes[0].set_title(f"(a) Corte longitudinal em x = {gx[ix]:.2f} m")
    fig.colorbar(cf1, ax=axes[0], label="RP (kPa)")

    XX, ZZ = np.meshgrid(gx, gz, indexing="ij")
    cf2 = axes[1].contourf(XX, ZZ, sec_xz, levels=14, cmap="YlOrBr")
    axes[1].invert_yaxis()
    axes[1].set_xlabel("x (m) — transversal a ravina")
    axes[1].set_ylabel("z (m) — profundidade no deposito")
    axes[1].set_title(f"(b) Corte transversal em y = {gy[iy]:.2f} m")
    fig.colorbar(cf2, ax=axes[1], label="RP (kPa)")
    fig.tight_layout()
    fig.savefig(OUT / "05_secoes_xz_yz.png", dpi=300)
    plt.close(fig)


# ===========================================================================
# 9. Curva de enchimento
# ===========================================================================
def fig06_curva_enchimento(acum: pd.DataFrame) -> None:
    acum_med = (
        acum.groupby("data")["acum_g"].mean()
        .reset_index().sort_values("data")
    )
    rho_b = 1.40e6
    area_parcela = 1.0
    area_bacia = 250.0
    fator = area_bacia / area_parcela / rho_b
    acum_med["vol_palicada_m3"] = acum_med["acum_g"] * fator
    capacidade = LARGURA_X * COMPRIMENTO_Y * (ESP_MAX / 2.0)
    acum_med["preench_pct"] = 100.0 * acum_med["vol_palicada_m3"] / capacidade

    fig, ax1 = plt.subplots(figsize=(8.5, 4.8))
    ax1.plot(
        acum_med["data"], acum_med["vol_palicada_m3"],
        "o-", color="#7a3b00", label="Volume acumulado (m3)",
    )
    ax1.set_xlabel("Data")
    ax1.set_ylabel("Volume acumulado (m3)", color="#7a3b00")
    ax1.tick_params(axis="x", rotation=30)
    ax2 = ax1.twinx()
    ax2.plot(
        acum_med["data"], acum_med["preench_pct"],
        "s--", color="#1f4e79", label="Preenchimento (%)",
    )
    ax2.axhline(100, color="red", lw=1.0, ls=":")
    ax2.set_ylabel("Preenchimento da capacidade nominal (%)", color="#1f4e79")
    ax1.set_title("Curva de enchimento estimada — palicada calibrada por LIMPO")
    ax1.grid(alpha=0.3)
    fig.tight_layout()
    fig.savefig(OUT / "06_curva_enchimento.png", dpi=300)
    plt.close(fig)


# ===========================================================================
# 10. Pipeline
# ===========================================================================
def main() -> None:
    print("[1/7] Calibrando volumes com dados de campo (LIMPO)...")
    vol_palicada, acum = calibrar_volume_campo()
    print(f"      Volume escalonado: {vol_palicada:.3f} m3")

    print("[2/7] Gerando sondagens sinteticas...")
    df_sond = gerar_sondagens(n_pontos=24)
    df_sond.to_csv(OUT / "sondagens_sinteticas.csv", index=False)

    print("[3/7] Krigagem 2D da espessura...")
    gx2, gy2, esp_z, esp_ss, pts, ok2d = krigar_espessura(df_sond)

    print("[4/7] Krigagem 3D do RP (NSPT-analogo)...")
    gx3, gy3, gz3, rp3, ss3, ok3d = krigar_rp_3d(df_sond)

    print("[5/7] Gerando topografia sintetica da ravina...")
    topo = gerar_topografia_ravina()

    print("[6/7] Renderizando figuras...")
    fig01_planta(df_sond)
    fig02_variograma(ok3d)
    fig03_superficie(gx2, gy2, esp_z, pts)
    fig04_modelo_3d_pyvista(gx2, gy2, esp_z, gx3, gy3, gz3, rp3, topo, df_sond)
    fig05_secoes(gx3, gy3, gz3, rp3)
    fig06_curva_enchimento(acum)

    print(f"[7/7] Concluido. Saidas em: {OUT}")


if __name__ == "__main__":
    main()
