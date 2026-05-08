# -*- coding: utf-8 -*-
"""Apply LDD Round 2 condensation to EN .qmd, mirroring PT structure."""
from pathlib import Path

path = Path(r"1-MANUSCRITOS/5-SIMULACAO_FEM_BAMBU/Simulacao_FEM_Bambu_EN.qmd")
t = path.read_text(encoding="utf-8")

new_23_to_26 = r"""## 2.3 Geometric model and finite element discretisation

The palisade was represented as a space frame composed of stacked horizontal culms connected to vertical stakes driven into the soil. Each element was modelled as a three-dimensional Euler-Bernoulli beam with 12 degrees of freedom per element, hollow tubular cross-section (outer diameter 100 mm, inner diameter 70 mm, initial wall thickness 15 mm) and orthotropic properties of *Bambusa vulgaris* (Table 1). The parametric geometry represents three segments with widths from 1.50 to 3.00 m and effective heights from 0.36 to 0.76 m, with 2 to 3 stakes per segment spaced up to 1.50 m apart and 3 to 6 horizontal culm layers with vertical spacing of 0.12 m. Lateral embedment of the culms into the slopes (15 cm per end) was represented by pin nodes, and culm-stake connections as rigid joints. Each culm span was subdivided into four elements, yielding 25 to 72 nodes and 26 to 81 elements per segment (150 to 432 DOF). Boundary conditions adopted full fixity at the lower stake tips (0.70 m below the surface), a conservative assumption relative to the actual driving depth of 30 cm. A mesh convergence study on the MED segment confirmed that the maximum FI remained unchanged (FI$_{\text{max}} = 0.364$) between 57 and 225 elements. The complete formulation of the stiffness, transformation and mesh validation procedures is detailed in the Supplementary Material (Section S1).

## 2.4 Material properties and degradation model

*Bambusa vulgaris* was treated as an orthotropic material, with initial mechanical properties obtained from the literature (Table 1) [@ghavami_marinho_2005; @iwasaki_et_al_2022]. Temporal degradation was modelled by exponential decay $P(t) = P_0 \cdot e^{-k \cdot t}$ (Equation 1), with three scenarios: optimistic ($k = 0.03$ yr$^{-1}$), reference ($k = 0.06$ yr$^{-1}$, half-life of 11.5 yr) and pessimistic ($k = 0.10$ yr$^{-1}$), spanning the durability range reported for untreated bamboo in tropical environments [@ghimire_et_al_2013; @romano_et_al_2016]. Wall thickness was reduced linearly at 1 mm yr$^{-1}$. At nodal zones, a reduction factor of 0.65 on interlaminar shear strength was adopted [@meng_et_al_2023]. The justification for the uniform decay rate and a sensitivity analysis with differential degradation ($k_{\tau} \approx 1.3 \cdot k_{\sigma}$) are presented in the Supplementary Material (Section S4).

## 2.5 Loading model and hydrological scenarios

Loading combines three lateral components and one gravitational component, all time-varying. On the upstream face, below the sediment level, the active earth pressure acts ($p_{sed}(z,t) = \gamma_s \cdot K_a \cdot (h_{sed}(t) - z)$, with $K_a = 0.333$ and $\gamma_s = 15\,000$ N/m^3 [@rankine_1857]). Exposed culms above the sediment level are subjected to hydrodynamic drag ($q_d = \tfrac{1}{2} C_d \rho_w v^2 D_{ext}$, $C_d = 1.2$) and debris impact (400 N for P95). Three hydrological scenarios were defined from the 20-year rainfall series: median, P90 (168.1 mm month$^{-1}$) and P95 (181.8 mm month$^{-1}$), with flow velocities of 0.5, 1.5 and 2.0 m/s, respectively. Drag and impact loads were scaled by a logistic vegetation factor (Equation 2) that models the progressive colonisation of the upstream face, anchored to two photographic inspection rounds processed by the Excess Green Index ($t \approx 0$ and $t \approx 2$ yr, Fig. 3). The saturation time ($T_{sat}$) was derived from empirical retention efficiencies and monthly deposition rates (Table 2). The complete loading model formulation, including the rationale for the non-concurrence of hydrostatic and hydrodynamic loads, is provided in the Supplementary Material (Section S2).

| $\displaystyle f_{veg}(t) = 1 - V_{max} \cdot \frac{1}{1 + e^{-r\,(t - t_m)}}$ | (2) |
| --- | --- |

In Equation 2, $V_{max} = 0.30$ is the maximum load reduction, $r = 2.0$ yr$^{-1}$ is the logistic growth rate, and $t_m = 2.0$ yr is the inflection point of the sigmoid curve, such that the factor progressively reduces up to 30\% of the effective drag and impact load from the second year onward. The reference value of $V_{max} = 0.30$ was anchored to a digital phenology assessment of the standardised photographic records spanning installation and the second-year inspection (Fig. 3), processed through the Excess Green Index [@richardson_et_al_2007; @woebbecke_et_al_1995]. The installation-day frame ($t \approx 0$) returned a vegetation cover of 3.5\% on the upstream face, dominated by exposed Plinthosol surfaces immediately after trench excavation, whereas the April 2025 inspection ($t \approx 2$ yr, $n = 5$ frames) yielded a mean cover of 11.9\%, ranging from 2.9\% to 17.5\%.

The increase from 3.5\% to 11.9\% over two years is consistent with the early-to-intermediate colonisation phase described in vegetation dynamics models for disturbed surfaces [@prentice_van_der_maarel_1987] and remains coherent with reviews on vegetation development over freshly exposed surfaces of hydraulic works [@corcoran_et_al_2010]. At $t = t_m$, the logistic function predicts $f_{veg}(t_m) = 1 - 0.5 V_{max}$, so that $V_{max} = 0.30$ implies a 15\% load reduction at the inflection point and an asymptotic 30\% reduction in the colonised state, a formulation coherent with the use of vegetation indices to represent temporal cover dynamics [@cano_carmona_et_al_2022]. A sensitivity analysis with $V_{max}$ ranging from 0.15 to 0.45 indicated changes of less than 3\% in the maximum FI at $t = 10$ yr, suggesting that moderate uncertainty in vegetation cover exerts a secondary effect on the global mechanical response, as expected in systems where vegetation acts as a modulator of surface processes rather than as a dominant mechanical forcing [@briske_2017].

![**Figure 3.** Photographic anchoring of the vegetation factor on the upstream face of the MED palisade. Panel (a) shows the structure on the installation day, with exposed Plinthosol surfaces and a baseline Excess Green Index cover of 3.5\%; panel (b) shows the same face at the second-year inspection ($t \approx 2$ yr, April 2025), with herbaceous and woody recolonisation reaching an Excess Green Index cover of 17.5\% in the most colonised frame. Pixels classified as vegetation are highlighted in green over the original imagery.](figuras/versao_EN/Fig_vegetation_panel.png){width="6.5in"}

Saturation time ($T_{sat}$) was treated as a continuous projection derived from empirical retention efficiencies and monthly deposition rates, under continuous recurrence of each hydrological scenario, onto the remaining effective height of each segment. Filling progression was parameterised as linear between 0% at $t = 0$ and 100% at $T_{sat}$, with the percentage at any instant given by $\min(100,\; t/T_{sat} \times 100)$. Because the FEM evaluates structural response at discrete 0.5-yr time steps, fractional $T_{sat}$ values, such as 0.8 yr, were linearly interpolated between adjacent steps (0.5 and 1.0 yr). The resulting saturation times are reported in Table 2.

**Table 2.** Estimated time to full (100%) storage capacity filling by segment and hydrological scenario, derived from empirical retention efficiencies ($1.12$ to $1.97 \times 10^{-4}$ cm/mm) and the 20-year rainfall series (2005–2025).

| **Segment** | **$H$ (cm)** | **Median (yr)** | **P90 (yr)** | **P95 (yr)** |
|----------|----------:|---------------:|-----------:|-----------:|
| SUP      |        50 |            4.8 |        2.4 |        2.2 |
| MED      |        76 |            2.2 |        1.1 |        1.0 |
| INF      |        36 |            1.7 |        0.8 |        0.8 |

## 2.6 Failure criterion and simulation design

The Tsai-Hill criterion for orthotropic materials [@hill_1948] was adopted in its reduced form for beam elements (Equation 3). A stress concentration factor (SCF = 1.8) was applied to culm-stake junctions [@pilkey_1997], and nodal zones additionally received a 0.65 reduction factor on interlaminar shear strength [@meng_et_al_2023]. Euler buckling was checked separately, yielding a safety factor exceeding 240 across all combinations. The simulation totalled 567 combinations (3 segments $\times$ 3 hydrological scenarios $\times$ 3 degradation rates $\times$ 21 time steps from 0 to 10 yr at 0.5-yr intervals), with global system solution by direct inversion. The complete derivation of the criterion, the buckling analysis and the parametric sensitivity tests are detailed in the Supplementary Material (Section S3).


"""

new_31 = r"""## 3.1 Sediment filling dynamics and hydrological regime transition

Field monitoring over 24 months yielded segment-specific retention efficiencies of $1.12$ to $1.97 \times 10^{-4}$ cm/mm, which parameterised the sediment accumulation rates used in the model (Fig. 2). Individual segments contributed 37.7% (SUP), 22.6% (MED) and 39.7% (INF) of the total retained mass, while the mean incremental deposition rate did not differ among segments (ANOVA, $F = 0.27$, $p = 0.77$), indicating that the series arrangement distributes the sediment load uniformly. After two years the residual storage capacity remained above 98% in all segments, confirming that the system operated in the pre-saturation phase throughout the monitoring period.

Sediment storage reached full capacity between 1.0 and 4.8 yr (Table 2), always before any risk of mechanical failure across the 567 combinations evaluated. The MED segment under P95 saturated first ($T_{sat} = 1.0$ yr), followed by INF ($T_{sat} = 0.8$ yr) and SUP ($T_{sat} = 2.2$ yr). This rapid clogging resulted from the sediment transport peak during high-energy storms, as four months with incremental deposition above the 95th percentile accounted for 40.6% of the total retained mass during the 2023–2025 period, with segment-specific contributions of 44.6% (INF), 39.6% (SUP) and 37.4% (MED). The concentration of 42% of the annual sediment input in the first wet trimester is consistent with the joint control of antecedent soil moisture and early-season erosivity over event sediment concentration documented by @defersha_melesse_2012, and with the seasonal EI30 distribution reported for the Cerrado biome [@castagna_et_al_2022], reflecting the typical concentrated-runoff dynamics of Plinthosols with slow internal drainage [@medeiros_araujo_2014].

After sediment filling reached 100%, the three hydrological scenarios (median, P90, P95) converged to the same failure index in each segment, remaining virtually identical up to $t = 10$ yr. This convergence reflects the operational phase transition described for open sediment traps [@piton_recking_2016], in which the height of the exposed face approaches zero, drag and debris impact loads vanish, and the active pressure of the retained material becomes the only lateral load, rendering structural demand independent of the hydrological regime. Empirical evidence from the same experimental system corroborates this transition: field monitoring revealed that mean monthly deposition under "High" rainfall (P75–P90) exceeded that under "Extreme" events (> P95), with mean incremental rates of 0.066 and 0.053 cm month$^{-1}$, respectively. This inversion suggests fine-sediment bypass under high-energy flow conditions and a non-monotonic relationship between rainfall magnitude and retention, consistent with the scour and bypass mechanisms described by @frankl_et_al_2021 and with clogging patterns of permeable barriers documented in semiarid basins [@hassanli_et_al_2009].

A variation of $T_{sat}$ by $\pm 30\%$ relative to the values in Table 2 supports this interpretation. Under the accelerated filling scenario ($T_{sat} \times 0.7$), the maximum FI at $t = 10$ yr remained virtually unchanged, while under the delayed scenario ($T_{sat} \times 1.3$) the increase in maximum FI under P95 was less than 4%. Reasonable uncertainty in the deposition rate, therefore, appears unlikely to alter the structural safety trajectory. This response reproduces the functional saturation pattern reported for permeable barriers in gullies [@wang_et_al_2021; @ramos_diez_et_al_2017], although in those systems saturation is generally not coupled with the progressive degradation of the construction material.

"""

# Replace §2.3..§2.6 (anchors at indices 13669..33461 from prior mapping)
start_23 = t.index("## 2.3 Geometric model and finite element discretisation")
end_26 = t.index("## 2.7 Statistical analysis")
t2 = t[:start_23] + new_23_to_26 + t[end_26:]

# Replace §3.1
start_31 = t2.index("## 3.1 Field-derived parameterisation and global mechanical response")
end_31 = t2.index("## 3.2 Stakes as critical elements")
t3 = t2[:start_31] + new_31 + t2[end_31:]

path.write_text(t3, encoding="utf-8", newline="\n")
print("OK new len =", len(t3))
