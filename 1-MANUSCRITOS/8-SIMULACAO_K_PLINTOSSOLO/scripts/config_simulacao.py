"""
Configuração centralizada para simulações do fator K_plint.
Dados reais (Plintossolo) + faixas da literatura (Latossolo, Argissolo).
"""
import numpy as np
from pathlib import Path

# ── Diretórios ──────────────────────────────────────────────────────
BASE_DIR = Path(__file__).resolve().parent.parent
FIG_DIR = BASE_DIR / "figuras"
FIG_DIR.mkdir(exist_ok=True)

# ── Parâmetros fixos do modelo K_plint ──────────────────────────────
VIB_REF = 6.0       # cm/h  (limiar infiltração-dominante)
M0 = 50.0           # %     (ponto de inflexão da sigmoide β)

# ── Parâmetros "verdadeiros" para calibração sintética ──────────────
TRUE_PARAMS = dict(n1=1.0, beta_max=2.5, k2=0.10, k3=3.0, n3=2.0)

# ── K_RUSLE nominal por classe (t h MJ⁻¹ mm⁻¹) ────────────────────
K_RUSLE = dict(plintossolo=0.035, latossolo=0.015, argissolo=0.025)

# ── Dados reais — Plintossolo Argilúvico Distrófico (Sergipe) ──────
PLINTOSSOLO = dict(
    VIB=dict(superior=3.13, intermediario=1.53, inferior=1.59),
    m_Al=dict(Ap=15.2, BAc=99.2, Bt=84.0),
    c_kPa=13.02,
    phi_deg=34.93,
    gamma_sat=19.93,   # kN/m³
    Hc=3.35,           # m  (Rankine, saturado)
    feicoes=dict(
        F1=dict(prof=1.10, H_Hc=0.33),
        F2=dict(prof=0.40, H_Hc=0.12),
        F3=dict(prof=0.60, H_Hc=0.18),
        F4=dict(prof=1.40, H_Hc=0.42),
        F5=dict(prof=1.50, H_Hc=0.45),
        F6=dict(prof=0.60, H_Hc=0.18),
    ),
    Ksat_cm_h=dict(Ap=3.13, BAc=0.50, Bt=1.53),
    n_solo_nu=12, n_exposto=4, n_cobertura=6,
)

# ── Dados da literatura — Latossolo Vermelho-Amarelo (controle −) ──
LATOSSOLO = dict(
    VIB=dict(superior=12.0, intermediario=9.0, inferior=7.0),
    m_Al=dict(Ap=10.0, Bw=20.0),
    c_kPa=30.0,
    phi_deg=30.0,
    gamma_sat=18.0,
    Hc=None,  # calculado pela função Hc()
    feicoes={},
    Ksat_cm_h=dict(Ap=12.0, Bw=8.0),
    n_solo_nu=12, n_cobertura=4,
)

# ── Dados da literatura — Argissolo Vermelho-Amarelo (controle ±) ──
ARGISSOLO = dict(
    VIB=dict(superior=4.5, intermediario=2.5, inferior=2.8),
    m_Al=dict(Ap=20.0, Bt=45.0),
    c_kPa=18.0,
    phi_deg=32.0,
    gamma_sat=19.0,
    Hc=None,
    feicoes=dict(F1=dict(prof=0.30, H_Hc=0.08)),
    Ksat_cm_h=dict(Ap=4.5, Bt=1.0),
    n_solo_nu=12, n_exposto=2, n_cobertura=4,
)

SOLOS = dict(plintossolo=PLINTOSSOLO, latossolo=LATOSSOLO, argissolo=ARGISSOLO)

# ── Display names (English, for figures) ────────────────────────────
DISPLAY_NAME = dict(plintossolo='Plinthosol', latossolo='Ferralsol', argissolo='Acrisol')


# ── Funções do modelo K_plint ───────────────────────────────────────
def calc_Hc(c_kPa, phi_deg, gamma_sat):
    """Altura crítica de Rankine (Eq. 7)."""
    phi_rad = np.radians(phi_deg)
    tan_term = np.tan(np.pi / 4 + phi_rad / 2)
    return (2 * c_kPa / gamma_sat) * tan_term + (2 * c_kPa) / (gamma_sat * tan_term)


def alpha(vib_local, n1, vib_ref=VIB_REF):
    """Fator de amplificação por regime hidráulico (Eq. 4)."""
    vib_local = np.asarray(vib_local, dtype=float)
    return np.where(vib_local >= vib_ref, 1.0, (vib_ref / vib_local) ** n1)


def beta(m_al, beta_max, k2, m0=M0):
    """Fator de penalização por toxicidade edáfica (Eq. 5)."""
    m_al = np.asarray(m_al, dtype=float)
    return 1.0 + (beta_max - 1.0) / (1.0 + np.exp(-k2 * (m_al - m0)))


def gamma(H_Hc, k3, n3):
    """Fator de vulnerabilidade geotécnica (Eq. 6)."""
    H_Hc = np.asarray(H_Hc, dtype=float)
    return 1.0 + k3 * H_Hc ** n3


def K_plint(K_rusle, vib_local, m_al, H_Hc, n1, beta_max, k2, k3, n3):
    """Equação 8 completa."""
    return (K_rusle
            * alpha(vib_local, n1)
            * beta(m_al, beta_max, k2)
            * gamma(H_Hc, k3, n3))


def delta_model(vib_local, m_al, H_Hc, n1, beta_max, k2, k3, n3):
    """Razão δ = K_plint / K_RUSLE (independe de K_RUSLE)."""
    return (alpha(vib_local, n1)
            * beta(m_al, beta_max, k2)
            * gamma(H_Hc, k3, n3))


# ── Gerar vetor de parcelas sintéticas para os 3 sítios ────────────
def gerar_parcelas(rng=None):
    """Retorna arrays (vib, m, H_Hc, classe, K_rusle) para 56 parcelas."""
    if rng is None:
        rng = np.random.default_rng(42)

    records = []

    def _add(solo_dict, nome, K_r):
        vibs = list(solo_dict['VIB'].values())
        m_vals = list(solo_dict['m_Al'].values())
        n_pos = len(vibs)
        rep = solo_dict['n_solo_nu'] // n_pos

        for i, v in enumerate(vibs):
            m_horiz = m_vals[min(i, len(m_vals) - 1)]
            feicoes = list(solo_dict['feicoes'].values())
            if feicoes:
                h_hc_mean = np.mean([f['H_Hc'] for f in feicoes])
                # Posição superior: feições menores; inferior: maiores
                h_hc = h_hc_mean * (0.5 + i * 0.5)
            else:
                h_hc = 0.0
            for _ in range(rep):
                records.append((v, m_horiz, h_hc, nome, K_r))

        # Parcelas com horizonte exposto (alto m)
        n_exp = solo_dict.get('n_exposto', 0)
        if n_exp > 0:
            m_max = max(m_vals)
            v_med = vibs[len(vibs) // 2]
            h_hc = np.mean([f['H_Hc'] for f in feicoes]) if feicoes else 0.0
            for _ in range(n_exp):
                records.append((v_med, m_max, h_hc, nome, K_r))

        # Parcelas com cobertura (não entram na calibração de K, mas geram dados)
        # Omitidas da calibração (C ≠ 1)

    _add(PLINTOSSOLO, 'plintossolo', K_RUSLE['plintossolo'])
    _add(LATOSSOLO, 'latossolo', K_RUSLE['latossolo'])
    _add(ARGISSOLO, 'argissolo', K_RUSLE['argissolo'])

    vib = np.array([r[0] for r in records])
    m = np.array([r[1] for r in records])
    h_hc = np.array([r[2] for r in records])
    classe = np.array([r[3] for r in records])
    k_r = np.array([r[4] for r in records])

    return vib, m, h_hc, classe, k_r


# ── Preencher Hc para Latossolo e Argissolo ─────────────────────────
for _s in [LATOSSOLO, ARGISSOLO]:
    _s['Hc'] = calc_Hc(_s['c_kPa'], _s['phi_deg'], _s['gamma_sat'])
