"""
Figura 1 — Estilo ANSYS / ParaView (renderização sólida 3D)
============================================================

Apresentação dos resultados de elementos finitos no formato consagrado
pela literatura técnica de mecânica computacional (ANSYS Mechanical,
Abaqus/CAE, COMSOL, Ansys Workbench):

    Painel (a) "Geometria + Condições de Contorno"
        - Estacas e colmos renderizados como tubos sólidos com a seção
          tubular real do bambu (D_ext = 100 mm)
        - Iluminação Phong (sombreamento suave)
        - Solo em corte semitransparente (faixa de embutimento)
        - Glifos de engaste (▲ cones) na base das estacas
        - Glifos de pino (♦) nos nós embutidos no talude
        - Setas de carregamento (empuxo lateral de Rankine)
        - Triad de orientação canto inferior

    Painel (b) "Resultados — Tsai-Hill Failure Index"
        - Malha deformada amplificada (×N) com mapa contínuo de FI
          (per-element) usando colormap engenharia ("jet")
        - Wireframe da malha indeformada como referência fantasma
        - Barra de escalares horizontal (estilo ANSYS) com FI_max e SF
        - Anotações: amplificação, segmento, cenário

Dependências: pyvista, numpy, matplotlib (compositor final).
Saída: figuras/versao_EN/Fig_1_wireframe_3d.{png,pdf}
    figuras/versao_EN/Fig_4_failure_states.{png,pdf}
    figuras/versao_EN/Fig_9_collapse_envelope.{png,pdf}
    equivalentes em figuras/versao_PT/
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pyvista as pv
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import image as mpimg

# Imports do solver FEM (mesma pasta)
sys.path.insert(0, str(Path(__file__).resolve().parent))
from fem_palicada_3d import generate_mesh, SEGMENTS, MESH, BAMBOO  # noqa: E402
from gerar_figuras_fem3d import _solve_single  # noqa: E402

# ================================================================
# CONFIGURAÇÕES
# ================================================================
BASE = Path(__file__).resolve().parent.parent
FIG_EN = BASE / "figuras" / "versao_EN"
FIG_PT = BASE / "figuras" / "versao_PT"
FIG_EN.mkdir(parents=True, exist_ok=True)
FIG_PT.mkdir(parents=True, exist_ok=True)

SEG_NAME = "MED"
HYDRO = "median"
DEG = "pessimistic"

# Trio de estágios de degradação (cenário crítico MED-mediana-pessimista)
# escolhidos a partir da curva FI(t) varrida por solver:
#   t = 5 a   → FI ≈ 0.04  (vida útil de serviço, ~4 % esforço)
#   t = 10 a  → FI ≈ 0.36  (fim do projeto declarado, ~36 % esforço)
#   t = 11.5 a→ FI ≈ 0.97  (ruptura iminente, SF ≈ 1.0)
STAGES = [
    dict(label="b", t_yr=5.0,  pct="~4%",  desc="early service"),
    dict(label="c", t_yr=10.0, pct="36%",  desc="design end-of-life"),
    dict(label="d", t_yr=11.5, pct="97%",  desc="incipient rupture"),
]
# Painel (e): colapso progressivo — multiplicador da carga à ruptura
# (λ = 2.5 → +150 % de carga; ruína perceptível da fileira inferior de estacas)
LAM_COLLAPSE = 2.5
# Escala compartilhada de FI (Tsai-Hill: 0 = intacto, 1 = ruptura)
FI_CLIM = (0.0, 1.0)
AMP_FRAC = 0.09           # alvo: amp ≈ max(W,H)*0.09 ≈ 27 cm visual

# Renderização
WINDOW = (1800, 1100)     # px (cada subplot) — proporcional ao bbox
DPI_OUT = 350
# Câmera: vista isométrica padrão de FEM (ANSYS-like)
# (X→largura, Y→profundidade lateral, Z→altura). Olhamos do octante +X,-Y,+Z.
CAMERA_VIEW = dict(
    azimuth_deg=-65,        # rotação em torno de Z
    elevation_deg=22,       # tilt acima do horizonte
    distance_factor=2.6,    # múltiplo do diagonal da bbox
    parallel_scale_factor=0.32,  # fração da diagonal (zoom)
)

# Cores (paleta ANSYS-like)
CLR_STAKE = "#1f5fa8"       # azul aço
CLR_CULM = "#c45a3a"        # cobre/terracota
CLR_EMBED = "#7a7a7a"       # cinza
CLR_SOIL = "#c2a473"        # bege talude
CLR_FIXED = "#2b2b2b"       # quase preto
CLR_PIN = "#444444"
CLR_LOAD = "#b81e1e"
CLR_GHOST = "#bbbbbb"
BG = "white"

# Diâmetros visuais
R_BEAM = BAMBOO["D_ext"] / 2.0          # 0.05 m → 100 mm tubo real
R_GHOST = R_BEAM * 0.20                  # wireframe finito de referência

LABEL = {
    "EN": dict(
        a_title="(a)",
        stage_title="({lab})",
        info_a="Section: {seg}  |  L = {L:.2f} m  |  H = {H:.2f} m  |  embed. = {emb:.2f} m\n"
               "Beam elements (Euler-Bernoulli, 12 DOF): {ne}  |  Nodes: {nn}\n"
               "Tubular section: D$_{{ext}}$ = 100 mm, t = 15 mm",
        info_stage="t = {t:.1f} yr  |  FI$_{{max}}$ = {fimax:.3f}  |  SF = {sf:.2f}\n"
                   "$\\sigma_{{max}}$ = {sigma:.1f} MPa  |  u$_{{max}}$ = {umax:.1f} mm\n"
                   "deformation $\\times${amp:.0f}",
        info_collapse="$\\lambda$ = {lam:.2f} (+{pctl:.0f}% load over rupture)\n"
                      "broken: {nbr}/{ntot} elem ({pcb:.1f}%)\n"
                      "deformation $\\times${amp:.0f}",
        curve_title="Progressive collapse envelope (linear-elastic FEM)",
        curve_xlabel="load multiplier  $\\lambda$  (1.0 = current rupture load)",
        curve_ylabel="% of beam elements with FI $\\geq$ 1",
        curve_legend=["stakes (vertical)", "culms (horizontal)",
                      "culm embedments", "all elements",
                      "$\\lambda$ = 2.5"],
        cb_label="Tsai-Hill FI [-]  (1.0 = rupture)",
    ),
    "PT": dict(
        a_title="(a)",
        stage_title="({lab})",
        info_a="Trecho: {seg}  |  L = {L:.2f} m  |  H = {H:.2f} m  |  emb. = {emb:.2f} m\n"
               "Elementos de viga (Euler-Bernoulli, 12 DOF): {ne}  |  Nós: {nn}\n"
               "Seção tubular: D$_{{ext}}$ = 100 mm, t = 15 mm",
        info_stage="t = {t:.1f} a  |  FI$_{{max}}$ = {fimax:.3f}  |  FS = {sf:.2f}\n"
                   "$\\sigma_{{máx}}$ = {sigma:.1f} MPa  |  u$_{{máx}}$ = {umax:.1f} mm\n"
                   "deformação $\\times${amp:.0f}",
        info_collapse="$\\lambda$ = {lam:.2f} (+{pctl:.0f}% carga além da ruptura)\n"
                      "rompidos: {nbr}/{ntot} elem ({pcb:.1f}%)\n"
                      "deformação $\\times${amp:.0f}",
        curve_title="Envelope de colapso progressivo (FEM linear-elástica)",
        curve_xlabel="multiplicador de carga  $\\lambda$  (1.0 = carga atual de ruptura)",
        curve_ylabel="% de elementos de viga com FI $\\geq$ 1",
        curve_legend=["estacas (verticais)", "colmos (horizontais)",
                      "embutimentos", "todos os elementos",
                      "$\\lambda$ = 2,5"],
        cb_label="FI Tsai-Hill [-]  (1.0 = ruptura)",
    ),
}


# ================================================================
# UTIL — construir um tubo (cilindro orientado) entre dois pontos
# ================================================================
def beam_tube(p1: np.ndarray, p2: np.ndarray, radius: float,
              n_sides: int = 18) -> pv.PolyData:
    """Cilindro entre p1 e p2 com tampa nas extremidades."""
    p1 = np.asarray(p1, float)
    p2 = np.asarray(p2, float)
    vec = p2 - p1
    L = float(np.linalg.norm(vec))
    if L < 1e-9:
        return pv.PolyData()
    center = (p1 + p2) / 2.0
    return pv.Cylinder(center=center, direction=vec, radius=radius,
                       height=L, resolution=n_sides, capping=True)


def setup_isometric_camera(pl: pv.Plotter, bounds, parallel: bool = True):
    """Posiciona a câmera em vista isométrica reprodutível (estilo ANSYS).

    bounds: (xmin, xmax, ymin, ymax, zmin, zmax)
    """
    xmin, xmax, ymin, ymax, zmin, zmax = bounds
    cx = (xmin + xmax) / 2
    cy = (ymin + ymax) / 2
    cz = (zmin + zmax) / 2
    diag = float(np.linalg.norm([xmax - xmin, ymax - ymin, zmax - zmin]))

    az = np.deg2rad(CAMERA_VIEW["azimuth_deg"])
    el = np.deg2rad(CAMERA_VIEW["elevation_deg"])
    R = diag * CAMERA_VIEW["distance_factor"]
    # Posição da câmera em coordenadas esféricas (origem no centro do bbox)
    px = cx + R * np.cos(el) * np.cos(az)
    py = cy + R * np.cos(el) * np.sin(az)
    pz = cz + R * np.sin(el)

    pl.camera_position = [(px, py, pz),     # posição
                          (cx, cy, cz),     # foco
                          (0, 0, 1)]        # up = Z (vertical)
    if parallel:
        pl.enable_parallel_projection()
        pl.camera.parallel_scale = diag * CAMERA_VIEW["parallel_scale_factor"]
    pl.reset_camera_clipping_range()


# ================================================================
# PAINEL (a) — geometria + condições de contorno + cargas
# ================================================================
def render_panel_a(seg_name: str = SEG_NAME) -> tuple[np.ndarray, dict]:
    sp = SEGMENTS[seg_name]
    W, H = sp["width"], sp["height"]
    EMBED = MESH["stake_embed"]
    EMB_C = MESH["colmo_embed"]

    nodes, elems, x_stakes, z_layers, talude_ids = generate_mesh(W, H)

    pl = pv.Plotter(off_screen=True, window_size=WINDOW)
    pl.set_background(BG)

    # --- Solo (caixa semi-transparente) ---
    soil = pv.Box(bounds=(-EMB_C - 0.10, W + EMB_C + 0.10,
                          -0.18, 0.18,
                          -EMBED - 0.05, 0.0))
    pl.add_mesh(soil, color=CLR_SOIL, opacity=0.30,
                show_edges=False, smooth_shading=True)
    # Linha cota do nível do solo
    ground_line = pv.Line((-EMB_C - 0.12, 0, 0),
                          (W + EMB_C + 0.12, 0, 0))
    pl.add_mesh(ground_line.tube(radius=0.012),
                color="#5a4014", show_scalar_bar=False)

    # --- Tubos (estacas, colmos, embutimentos) ---
    color_by_type = {"stake": CLR_STAKE, "colmo": CLR_CULM,
                     "colmo_embed": CLR_EMBED}
    for e in elems:
        p1 = nodes[e["n1"]]
        p2 = nodes[e["n2"]]
        col = color_by_type[e["type"]]
        opa = 0.55 if e["type"] == "colmo_embed" else 1.0
        # Trechos enterrados: tom desbotado
        if p1[2] < -1e-3 and p2[2] < -1e-3:
            opa *= 0.55
        tube = beam_tube(p1, p2, R_BEAM)
        pl.add_mesh(tube, color=col, opacity=opa,
                    smooth_shading=True, specular=0.35,
                    specular_power=20, ambient=0.25)

    # --- Glifos de engaste (cones nas bases enterradas) ---
    for ni, nd in enumerate(nodes):
        if nd[2] < -EMBED + 1e-3:    # nós no fundo do engaste
            cone = pv.Cone(center=(nd[0], nd[1], nd[2] - 0.06),
                           direction=(0, 0, 1),
                           height=0.12, radius=0.07, resolution=24)
            pl.add_mesh(cone, color=CLR_FIXED, smooth_shading=True)
            # 3 hachuras de engaste
            for k, dx in enumerate([-0.06, 0, 0.06]):
                hatch = pv.Line((nd[0] + dx - 0.03, nd[1], nd[2] - 0.14),
                                (nd[0] + dx + 0.03, nd[1], nd[2] - 0.18))
                pl.add_mesh(hatch.tube(radius=0.006), color=CLR_FIXED)

    # --- Glífos de pino no talude (esferas) ---
    for tid in talude_ids:
        nd = nodes[tid]
        sph = pv.Sphere(center=nd, radius=0.04, theta_resolution=24,
                        phi_resolution=24)
        pl.add_mesh(sph, color=CLR_PIN, smooth_shading=True)

    # Câmera (vista isométrica fixa)
    bounds = (-EMB_C - 0.20, W + EMB_C + 0.20,
              -0.50, 0.50,
              -EMBED - 0.20, H + 0.20)
    setup_isometric_camera(pl, bounds, parallel=True)

    # Triad de orientação
    pl.add_axes(line_width=3, labels_off=False,
                xlabel="X (Width)", ylabel="Y (Lateral)", zlabel="Z (Height)",
                color="black")

    img = pl.screenshot(transparent_background=False, return_img=True)
    pl.close()

    info = dict(W=W, H=H, EMBED=EMBED, n_nodes=len(nodes),
                n_elems=len(elems))
    return img, info


# ================================================================
# PAINEL DE ESTÁGIO (b/c/d) — deformada amplificada + Tsai-Hill FI
# ================================================================
def render_stage(seg_name: str, t_yr: float) -> tuple[np.ndarray, dict]:
    sp = SEGMENTS[seg_name]
    W, H = sp["width"], sp["height"]

    nodes, elems, U, fi_list = _solve_single(seg_name, HYDRO, DEG, t_yr)

    # Amplificação (alvo visual fixo — todos os estágios mesmo deslocamento aparente)
    max_disp = 0.0
    for ni in range(len(nodes)):
        d = np.sqrt(U[ni*6]**2 + U[ni*6+1]**2 + U[ni*6+2]**2)
        max_disp = max(max_disp, d)
    amp = (max(W, H) * AMP_FRAC) / max_disp if max_disp > 1e-12 else 1.0

    nodes_def = nodes.copy()
    for ni in range(len(nodes)):
        nodes_def[ni, 0] += U[ni * 6]     * amp
        nodes_def[ni, 1] += U[ni * 6 + 1] * amp
        nodes_def[ni, 2] += U[ni * 6 + 2] * amp

    fi_arr = np.array(fi_list, dtype=float)
    fi_max = float(np.nanmax(fi_arr))
    sf = 1.0 / fi_max if fi_max > 1e-9 else 999.0
    # Tensão de flexão máxima (recalculada no solver — reaproveitamos do summary)
    sigma_max = float(np.sqrt(fi_max) * BAMBOO["sigma_tL"] * 1e-6) \
        if fi_max > 0 else 0.0

    pl = pv.Plotter(off_screen=True, window_size=WINDOW)
    pl.set_background(BG)

    # Solo (referência)
    EMB_C = MESH["colmo_embed"]
    soil = pv.Box(bounds=(-EMB_C - 0.10, W + EMB_C + 0.10,
                          -0.45, 0.45,
                          -MESH["stake_embed"] - 0.05, 0.0))
    pl.add_mesh(soil, color=CLR_SOIL, opacity=0.18,
                show_edges=False)
    ground_line = pv.Line((-EMB_C - 0.12, 0, 0),
                          (W + EMB_C + 0.12, 0, 0))
    pl.add_mesh(ground_line.tube(radius=0.010),
                color="#5a4014")

    # Wireframe da malha indeformada (fantasma)
    for e in elems:
        p1, p2 = nodes[e["n1"]], nodes[e["n2"]]
        ghost = beam_tube(p1, p2, R_GHOST)
        pl.add_mesh(ghost, color=CLR_GHOST, opacity=0.55,
                    smooth_shading=True, ambient=0.4)

    # Deformada colorida por FI (escala compartilhada 0–1)
    for e, fi in zip(elems, fi_arr):
        p1, p2 = nodes_def[e["n1"]], nodes_def[e["n2"]]
        tube = beam_tube(p1, p2, R_BEAM)
        # Clip visual: FI > 1 satura no topo da escala
        fi_clip = float(min(fi, FI_CLIM[1]))
        tube["FI"] = np.full(tube.n_points, fi_clip)
        pl.add_mesh(tube, scalars="FI", cmap="jet", clim=FI_CLIM,
                    show_scalar_bar=False, smooth_shading=True,
                    specular=0.30, specular_power=18, ambient=0.22)

    # Câmera idêntica ao painel A
    bounds = (-EMB_C - 0.20, W + EMB_C + 0.20,
              -0.50, 0.50,
              -MESH["stake_embed"] - 0.20, H + 0.20)
    setup_isometric_camera(pl, bounds, parallel=True)

    pl.add_axes(line_width=3, labels_off=False,
                xlabel="X", ylabel="Y", zlabel="Z",
                color="black")

    img = pl.screenshot(transparent_background=False, return_img=True)
    pl.close()

    info = dict(amp=amp, fi_max=fi_max, sf=sf,
                u_max_mm=max_disp * 1e3,
                sigma_max_MPa=sigma_max,
                t_yr=t_yr)
    return img, info


# ================================================================
# PAINEL (e) — colapso pós-ruptura para multiplicador λ da carga
# ================================================================
def render_collapse(seg_name: str, lam: float,
                    t_ref: float = 11.5) -> tuple[np.ndarray, dict]:
    """Estado pós-ruptura sob carga λ × carga atual.

    Aproveita a linearidade do FEM:
        u(λ)  = λ · u(1)
        FI(λ) = λ² · FI(1)
    Elementos com FI(λ) ≥ 1 são desenhados em vermelho escuro semi-fragmentado
    (visualização do colapso); demais seguem o jet [0,1].
    """
    sp = SEGMENTS[seg_name]
    W, H = sp["width"], sp["height"]

    nodes, elems, U, fi_list = _solve_single(seg_name, HYDRO, DEG, t_ref)
    U = np.asarray(U) * lam
    fi_arr = np.asarray(fi_list, dtype=float) * (lam ** 2)

    # Amplificação visual fixa (mesmo alvo dos demais painéis)
    max_disp = 0.0
    for ni in range(len(nodes)):
        d = np.sqrt(U[ni*6]**2 + U[ni*6+1]**2 + U[ni*6+2]**2)
        max_disp = max(max_disp, d)
    amp = (max(W, H) * AMP_FRAC) / max_disp if max_disp > 1e-12 else 1.0

    nodes_def = nodes.copy()
    for ni in range(len(nodes)):
        nodes_def[ni, 0] += U[ni * 6]     * amp
        nodes_def[ni, 1] += U[ni * 6 + 1] * amp
        nodes_def[ni, 2] += U[ni * 6 + 2] * amp

    pl = pv.Plotter(off_screen=True, window_size=WINDOW)
    pl.set_background(BG)

    EMB_C = MESH["colmo_embed"]
    soil = pv.Box(bounds=(-EMB_C - 0.10, W + EMB_C + 0.10,
                          -0.45, 0.45,
                          -MESH["stake_embed"] - 0.05, 0.0))
    pl.add_mesh(soil, color=CLR_SOIL, opacity=0.18, show_edges=False)
    ground_line = pv.Line((-EMB_C - 0.12, 0, 0),
                          (W + EMB_C + 0.12, 0, 0))
    pl.add_mesh(ground_line.tube(radius=0.010), color="#5a4014")

    # Wireframe indeformado
    for e in elems:
        p1, p2 = nodes[e["n1"]], nodes[e["n2"]]
        ghost = beam_tube(p1, p2, R_GHOST)
        pl.add_mesh(ghost, color=CLR_GHOST, opacity=0.55,
                    smooth_shading=True, ambient=0.4)

    # Deformada: cores conforme estado
    n_broken = 0
    for e, fi in zip(elems, fi_arr):
        p1, p2 = nodes_def[e["n1"]], nodes_def[e["n2"]]
        tube = beam_tube(p1, p2, R_BEAM)
        if fi >= 1.0:
            # Elemento rompido — cor crítica + edges destacados
            n_broken += 1
            pl.add_mesh(tube, color=CLR_LOAD, opacity=0.95,
                        smooth_shading=True, specular=0.10,
                        ambient=0.30, show_edges=True,
                        edge_color="#3a0000", line_width=1.2)
        else:
            tube["FI"] = np.full(tube.n_points, float(min(fi, FI_CLIM[1])))
            pl.add_mesh(tube, scalars="FI", cmap="jet", clim=FI_CLIM,
                        show_scalar_bar=False, smooth_shading=True,
                        specular=0.30, specular_power=18, ambient=0.22)

    bounds = (-EMB_C - 0.20, W + EMB_C + 0.20,
              -0.50, 0.50,
              -MESH["stake_embed"] - 0.20, H + 0.20)
    setup_isometric_camera(pl, bounds, parallel=True)
    pl.add_axes(line_width=3, labels_off=False,
                xlabel="X", ylabel="Y", zlabel="Z", color="black")

    img = pl.screenshot(transparent_background=False, return_img=True)
    pl.close()

    info = dict(amp=amp, lam=lam,
                pct_load=(lam - 1.0) * 100.0,
                n_broken=n_broken, n_total=len(elems),
                pct_broken=n_broken / len(elems) * 100.0,
                u_max_mm=max_disp * 1e3)
    return img, info


# ================================================================
# CURVA (f) — λ vs % de elementos rompidos
# ================================================================
def compute_collapse_curve(seg_name: str, t_ref: float = 11.5,
                           n_pts: int = 600) -> dict:
    """λ_failure por elemento + por tipo. FI(λ)=λ²·FI(1) ⇒ λ_i = 1/√FI_i."""
    _, elems, _, fi_list = _solve_single(seg_name, HYDRO, DEG, t_ref)
    fi = np.asarray(fi_list, dtype=float)
    lam_fail = np.where(fi > 1e-9, 1.0 / np.sqrt(fi), np.inf)

    types = np.array([e["type"] for e in elems])
    lam_grid = np.geomspace(0.5, 50.0, n_pts)
    out = {"lam": lam_grid}
    out["all_pct"] = np.array([(lam_fail <= L).mean() * 100 for L in lam_grid])
    for t in ("stake", "colmo", "colmo_embed"):
        sub = lam_fail[types == t]
        out[f"{t}_pct"] = np.array([(sub <= L).mean() * 100 for L in lam_grid])
        out[f"{t}_first"] = float(sub.min())
    out["lam_25"] = float(np.percentile(lam_fail[np.isfinite(lam_fail)], 25))
    out["lam_50"] = float(np.percentile(lam_fail[np.isfinite(lam_fail)], 50))
    out["lam_75"] = float(np.percentile(lam_fail[np.isfinite(lam_fail)], 75))
    out["lam_max"] = float(lam_fail[np.isfinite(lam_fail)].max())
    out["frac_broken_at_lam_collapse"] = float(
        (lam_fail <= LAM_COLLAPSE).mean() * 100)
    return out


# ================================================================
# COMPOSITOR FINAL — matplotlib monta a figura editorial
# ================================================================
def compose_figure(img_a: np.ndarray, info_a: dict,
                   stages: list[tuple[str, np.ndarray, dict]],
                   img_e: np.ndarray, info_e: dict,
                   lang: str, out_dir: Path):
    """Composições principais.

    A primeira figura contém geometria, serviço inicial e fim de vida de
    projeto. A segunda separa ruptura incipiente e pós-ruptura, reduzindo a
    densidade visual no manuscrito.
    """
    L = LABEL[lang]
    seg = SEG_NAME

    plt.rcParams.update({
        "font.family": "serif",
        "font.size": 10,
        "axes.titlesize": 11,
        "savefig.bbox": "tight",
    })

    import matplotlib.colors as mcolors

    def add_colorbar(fig, cax):
        cmap = plt.get_cmap("jet")
        norm = mcolors.Normalize(vmin=FI_CLIM[0], vmax=FI_CLIM[1])
        sm = plt.cm.ScalarMappable(cmap=cmap, norm=norm)
        sm.set_array([])
        cb = fig.colorbar(sm, cax=cax, orientation="vertical")
        cb.set_label(L["cb_label"], fontsize=9.5, labelpad=10)
        cb.set_ticks(np.linspace(FI_CLIM[0], FI_CLIM[1], 11))
        cb.ax.tick_params(labelsize=8)
        cb.ax.axhline(1.0, color="#000", lw=1.0)

    fig = plt.figure(figsize=(12.4, 4.2), dpi=DPI_OUT)
    gs = fig.add_gridspec(
        nrows=1, ncols=4,
        width_ratios=[1.0, 1.0, 1.0, 0.045],
        wspace=0.04,
        left=0.012, right=0.94, top=0.97, bottom=0.02,
    )

    # ---- (a) ----
    ax_a = fig.add_subplot(gs[0, 0])
    ax_a.imshow(img_a, aspect="auto")
    ax_a.set_axis_off()
    ax_a.set_title(L["a_title"], pad=4, fontsize=12, loc="left")
    ax_a.text(
        0.02, 0.02,
        L["info_a"].format(seg=seg, L=info_a["W"], H=info_a["H"],
                           emb=info_a["EMBED"],
                           ne=info_a["n_elems"], nn=info_a["n_nodes"]),
        transform=ax_a.transAxes, ha="left", va="bottom",
        fontsize=8.0,
        bbox=dict(boxstyle="round,pad=0.42", fc="white",
                  ec="#888", lw=0.6, alpha=0.92),
    )

    # ---- (b) (c) ----
    for (lab, img_s, info_s), c in zip(stages[:2], [1, 2]):
        ax = fig.add_subplot(gs[0, c])
        ax.imshow(img_s, aspect="auto")
        ax.set_axis_off()
        ax.set_title(L["stage_title"].format(lab=lab),
                     pad=4, fontsize=12, loc="left")
        ax.text(
            0.02, 0.02,
            L["info_stage"].format(
                t=info_s["t_yr"],
                fimax=info_s["fi_max"], sf=info_s["sf"],
                sigma=info_s["sigma_max_MPa"],
                umax=info_s["u_max_mm"], amp=info_s["amp"],
            ),
            transform=ax.transAxes, ha="left", va="bottom",
            fontsize=8.0,
            bbox=dict(boxstyle="round,pad=0.42", fc="white",
                      ec="#888", lw=0.6, alpha=0.92),
        )

    # ---- Colorbar vertical ----
    cax = fig.add_subplot(gs[0, 3])
    add_colorbar(fig, cax)

    out_png = out_dir / "Fig_1_wireframe_3d.png"
    out_pdf = out_dir / "Fig_1_wireframe_3d.pdf"
    fig.savefig(out_png, dpi=DPI_OUT)
    fig.savefig(out_pdf)
    plt.close(fig)
    print(f"  ✓ {out_png}")
    print(f"  ✓ {out_pdf}")

    # ---- Figura separada: ruptura incipiente + pós-ruptura ----
    fig = plt.figure(figsize=(8.6, 4.2), dpi=DPI_OUT)
    gs = fig.add_gridspec(
        nrows=1, ncols=3,
        width_ratios=[1.0, 1.0, 0.05],
        wspace=0.04,
        left=0.012, right=0.92, top=0.97, bottom=0.02,
    )

    lab, img_s, info_s = stages[2]
    ax = fig.add_subplot(gs[0, 0])
    ax.imshow(img_s, aspect="auto")
    ax.set_axis_off()
    ax.set_title(L["stage_title"].format(lab="a"),
                 pad=4, fontsize=12, loc="left")
    ax.text(
        0.02, 0.02,
        L["info_stage"].format(
            t=info_s["t_yr"],
            fimax=info_s["fi_max"], sf=info_s["sf"],
            sigma=info_s["sigma_max_MPa"],
            umax=info_s["u_max_mm"], amp=info_s["amp"],
        ),
        transform=ax.transAxes, ha="left", va="bottom",
        fontsize=8.0,
        bbox=dict(boxstyle="round,pad=0.42", fc="white",
                  ec="#888", lw=0.6, alpha=0.92),
    )

    ax_e = fig.add_subplot(gs[0, 1])
    ax_e.imshow(img_e, aspect="auto")
    ax_e.set_axis_off()
    ax_e.set_title(L["stage_title"].format(lab="b"),
                   pad=4, fontsize=12, loc="left")
    ax_e.text(
        0.02, 0.02,
        L["info_collapse"].format(
            lam=info_e["lam"], pctl=info_e["pct_load"],
            nbr=info_e["n_broken"], ntot=info_e["n_total"],
            pcb=info_e["pct_broken"], amp=info_e["amp"],
        ),
        transform=ax_e.transAxes, ha="left", va="bottom",
        fontsize=8.0,
        bbox=dict(boxstyle="round,pad=0.42", fc="white",
                  ec="#888", lw=0.6, alpha=0.92),
    )

    cax = fig.add_subplot(gs[0, 2])
    add_colorbar(fig, cax)

    out_png = out_dir / "Fig_4_failure_states.png"
    out_pdf = out_dir / "Fig_4_failure_states.pdf"
    fig.savefig(out_png, dpi=DPI_OUT)
    fig.savefig(out_pdf)
    plt.close(fig)
    print(f"  ✓ {out_png}")
    print(f"  ✓ {out_pdf}")


def compose_curve_figure(curve: dict, lang: str, out_dir: Path):
    """Figura separada — envelope de colapso progressivo λ vs % rompidos.
    Sem caption interno (vai no manuscrito).
    """
    L = LABEL[lang]
    plt.rcParams.update({
        "font.family": "serif",
        "font.size": 10,
        "savefig.bbox": "tight",
    })

    fig, ax = plt.subplots(figsize=(7.2, 4.8), dpi=DPI_OUT)
    lam = curve["lam"]

    ax.semilogx(lam, curve["stake_pct"], color=CLR_STAKE, lw=1.6,
                label=L["curve_legend"][0])
    ax.semilogx(lam, curve["colmo_pct"], color=CLR_CULM, lw=1.6,
                label=L["curve_legend"][1])
    ax.semilogx(lam, curve["colmo_embed_pct"], color=CLR_EMBED, lw=1.4,
                ls="--", label=L["curve_legend"][2])
    ax.semilogx(lam, curve["all_pct"], color="#222", lw=2.2,
                label=L["curve_legend"][3], zorder=5)

    # Marcador λ=2.5
    ax.axvline(LAM_COLLAPSE, color="#b81e1e", lw=1.2, ls=":",
               label=L["curve_legend"][4])
    pct_e = curve["frac_broken_at_lam_collapse"]
    ax.scatter([LAM_COLLAPSE], [pct_e], s=70, color="#b81e1e",
               zorder=10, edgecolor="black", lw=0.8)
    ax.annotate(f"$\\lambda$ = {LAM_COLLAPSE}\n{pct_e:.1f}%",
                xy=(LAM_COLLAPSE, pct_e),
                xytext=(LAM_COLLAPSE * 1.6, pct_e + 14),
                fontsize=9, color="#b81e1e",
                arrowprops=dict(arrowstyle="-", color="#b81e1e", lw=0.8))

    # Linhas-guia de % típicas
    for y, lbl in [(25, "25%"), (50, "50%"), (75, "75%")]:
        ax.axhline(y, color="#aaa", lw=0.5, ls=":")

    ax.set_xlim(0.9, 30)
    ax.set_ylim(-3, 105)
    ax.set_xlabel(L["curve_xlabel"], fontsize=10.5)
    ax.set_ylabel(L["curve_ylabel"], fontsize=10.5)
    ax.grid(True, which="both", ls=":", lw=0.4, alpha=0.7)
    ax.legend(loc="lower right", fontsize=8.5, framealpha=0.95)
    ax.tick_params(labelsize=9)

    out_png = out_dir / "Fig_9_collapse_envelope.png"
    out_pdf = out_dir / "Fig_9_collapse_envelope.pdf"
    fig.savefig(out_png, dpi=DPI_OUT)
    fig.savefig(out_pdf)
    plt.close(fig)
    print(f"  ✓ {out_png}")
    print(f"  ✓ {out_pdf}")


# ================================================================
# MAIN
# ================================================================
def main():
    print("Renderizando painel (a) — geometria + BCs ...")
    img_a, info_a = render_panel_a(SEG_NAME)

    stages = []
    for st in STAGES:
        print(f"Renderizando painel ({st['label']}) — t = {st['t_yr']:.1f} a "
              f"({st['desc']}) ...")
        img_s, info_s = render_stage(SEG_NAME, st["t_yr"])
        stages.append((st["label"], img_s, info_s))

    print(f"Renderizando painel (e) — colapso pós-ruptura λ = {LAM_COLLAPSE} ...")
    img_e, info_e = render_collapse(SEG_NAME, LAM_COLLAPSE)

    print("Computando curva (f) — λ vs % rompidos ...")
    curve = compute_collapse_curve(SEG_NAME)

    print("Compondo versão EN ...")
    compose_figure(img_a, info_a, stages, img_e, info_e, "EN", FIG_EN)
    compose_curve_figure(curve, "EN", FIG_EN)
    print("Compondo versão PT ...")
    compose_figure(img_a, info_a, stages, img_e, info_e, "PT", FIG_PT)
    compose_curve_figure(curve, "PT", FIG_PT)

    print("\nOK — figura ANSYS-style gerada.")
    for (lab, _, info_s) in stages:
        print(f"  ({lab}) t = {info_s['t_yr']:5.1f} a  |  "
              f"FI_max = {info_s['fi_max']:.3f}  |  SF = {info_s['sf']:5.2f}  |  "
              f"u_max = {info_s['u_max_mm']:5.1f} mm  |  amp ×{info_s['amp']:.1f}")
    print(f"  (e) λ = {info_e['lam']:.2f} (+{info_e['pct_load']:.0f}% load)  |  "
          f"broken = {info_e['n_broken']}/{info_e['n_total']} "
          f"({info_e['pct_broken']:.1f}%)  |  amp ×{info_e['amp']:.1f}")
    print(f"  (f) curve: 25%@λ={curve['lam_25']:.2f}  50%@λ={curve['lam_50']:.2f}  "
          f"75%@λ={curve['lam_75']:.2f}  100%@λ={curve['lam_max']:.1f}")


if __name__ == "__main__":
    main()
