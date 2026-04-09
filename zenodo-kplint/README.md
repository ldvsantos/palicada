# Zenodo deposit — K_plint correction factor for Plinthosol erodibility

[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.19483403.svg)](https://doi.org/10.5281/zenodo.19483403)

## Description

Supplementary data, simulation scripts and manuscript files for the article:

> **da Silva, E.G.** A field-parameterised multiplicative correction factor $K_{\text{plint}}$ for USLE erodibility of tropical Plinthosols: formulation, sensitivity analysis and computational validation.

## Repository structure

```
zenodo-kplint/
├── manuscripts/
│   ├── Simulacao_Kplint_USLE_Springer.tex      # English manuscript (LaTeX)
│   ├── Simulacao_Kplint_USLE_Springer.pdf       # English manuscript (PDF)
│   ├── Simulacao_Kplint_USLE_Springer_PTBR.tex  # Portuguese manuscript (LaTeX)
│   ├── Simulacao_Kplint_USLE_Springer_PTBR.pdf  # Portuguese manuscript (PDF)
│   └── referencias_artigos.bib                  # BibTeX references
├── figures/
│   ├── fig_00a_area_estudo_aerea.png             # Aerial view of the study site
│   ├── fig_00b_feicoes_drone_campo.jpeg          # UAV orthomosaic and field measurements
│   ├── fig_01_calibracao_sintetica.png           # Synthetic calibration — parameter bias
│   ├── fig_02_boxplot_parametros.png             # Parameter distribution boxplots
│   ├── fig_03_sensibilidade_sobol.png            # Sobol sensitivity indices
│   ├── fig_04_interacoes_s2.png                  # Second-order interaction matrix
│   ├── fig_05_estabilidade_taludes.png           # Slope stability and gamma validation
│   ├── fig_06_infiltracao_escoamento.png         # Green–Ampt infiltration and runoff
│   ├── fig_07_hidrograma_i60.png                 # Runoff hydrograph (I30 = 60 mm/h)
│   ├── fig_08_erosao_virtual.png                 # Virtual erosion simulation results
│   └── fig_09_sitio_experimental.png             # Experimental site elements
└── scripts/
    ├── config_simulacao.py                       # Shared configuration and soil profiles
    ├── sim_01_calibracao_sintetica.py            # Test 1 — Synthetic calibration
    ├── sim_02_sensibilidade_sobol.py             # Test 2 — Sobol sensitivity analysis
    ├── sim_03_estabilidade_taludes.py            # Test 3 — Slope stability
    ├── sim_04_infiltracao_escoamento.py          # Test 4 — Green–Ampt infiltration
    └── sim_05_erosao_virtual.py                  # Test 5 — Virtual erosion (WEPP-type)
```

## How to reproduce the simulations

```bash
pip install numpy scipy matplotlib SALib
cd scripts
python sim_01_calibracao_sintetica.py
python sim_02_sensibilidade_sobol.py
python sim_03_estabilidade_taludes.py
python sim_04_infiltracao_escoamento.py
python sim_05_erosao_virtual.py
```

## License

CC BY 4.0
