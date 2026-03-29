# Data Availability Statement

**Journal:** International Journal of River Basin Management  
**Manuscript title:** Biodegradation rate rather than hydrological regime as the dominant control on structural safety of bamboo palisades in gully erosion management

---

## Statement (to be inserted in the manuscript)

**Data availability**

The Python source code implementing the three-dimensional finite element model (Euler-Bernoulli beam framework, Tsai-Hill failure criterion, degradation and loading routines) and all processed input data used to reproduce the results reported in this study are publicly available in the GitHub repository: https://github.com/ldvsantos/palicada. Raw field monitoring data (pin measurements, pluviometric series 2005–2025) are available from the corresponding author upon reasonable request.

---

## Checklist for data deposit (Taylor & Francis Basic Data Sharing Policy)

Authors are encouraged to share or make open the data supporting the results or analyses presented in their paper. The following actions are needed before final submission:

| Action | Status | Notes |
|---|---|---|
| Deposit code and processed data in a persistent repository | ⬜ To do | Archive the GitHub repository as a versioned release on **Zenodo** (https://zenodo.org) to obtain a DOI; this is more suitable than GitHub alone as it provides a permanent, citable identifier |
| Cite the dataset in the reference list | ⬜ To do | Add a [dataset] reference following Elsevier format (see example below) |
| Add dataset DOI to the journal submission form | ⬜ To do | Paste the Zenodo DOI when prompted in ScholarOne |
| State unavailability of any sensitive raw data | ⬜ To do | If pluviometric raw data from third-party stations cannot be shared, state: "Raw pluviometric data are owned by [INMET/SEMARH-SE] and are available from the corresponding institution upon request." |

---

## Example dataset reference (add to the References section)

```
Santos, L.D.V., [year]. FEM model and field data for bamboo palisade structural
analysis (Version 1.0) [dataset]. Zenodo. https://doi.org/10.5281/zenodo.XXXXXXX
```

Replace `XXXXXXX` with the actual Zenodo record number after deposit.

---

## Recommended Zenodo deposit contents

- `scripts/fem_palicada_3d.py` — core FEM solver
- `scripts/` — all analysis and figure-generation scripts
- `resultados/` — model output CSVs
- `README.md` — description of files, dependencies, and reproduction instructions
- Input parameter tables (Table 1 and Table 2 of the manuscript) as CSV

**Dependencies to document:** Python ≥ 3.10, NumPy, SciPy, Pandas, Matplotlib (with versions); R 4.5.1 for regression analyses.
