# Robust ocean temperature from salinity

**Unit 2 – Linear models for regression.** Team Cash Guard: V. Anbu Chelvan, S. Roopesh, B. Charith Reddy, Y. Rupesh Reddy.

## Problem statement

Predict ocean water temperatures from salinity measurements taken over 60+ years, using outlier-proof regression (Huber) so that faulty sensor readings do not corrupt the predictions.

What makes it hard: a 72-year archive is stitched together from many ships, crews and instrument generations. Thermistors drift, sensors foul, bottles sit in the sun, and a faulty reading is usually still a **physically plausible number**, so a range check cannot remove it.

## Data

The **CalCOFI Bottle Database**, March 1949 to May 2021: real seawater samples off California.

| Step | Rows |
|---|---|
| Bottle records read | 895,371 |
| With both temperature and salinity | 844,748 |
| Flagged by CalCOFI's own quality codes | 38,593 (4.57%) |
| Physically impossible (e.g. a 99 °C reading) | 934 |
| Clean rows after screening | 806,108 |
| Modelled (random sample) | 80,000: 60,000 train, 20,000 test |

Salinity and temperature correlate at −0.505, and the relationship is curved, so the models use polynomial basis functions (degree 5).

Download: https://calcofi.org/data/oceanographic-data/bottle-database/ (the file `194903-202105_Bottle.csv`). The problem statement also points to https://calcofi.io/datasets/calcofi_ctd-cast/.

## Method

Two lines of defence:

1. **A physical quality gate** removes impossible readings (salinity outside 30–37 PSU, temperature outside −2 to 35 °C) and rows CalCOFI itself flagged.
2. **Robust regression** handles the faults the gate cannot see: plausible but wrong values.

Every Unit 2 concept is used and compared:

| Concept | Model |
|---|---|
| Maximum likelihood = least squares | OLS on the basis functions |
| Basis functions φ(x) | degree-5 polynomial of salinity |
| Robust regression | **Huber loss, δ = 1.35** (the main deliverable), and RANSAC |
| MAP with a Gaussian prior | Ridge (α chosen by cross-validation: 0.001) |
| Bayesian linear regression | BayesianRidge, which also gives a predictive uncertainty |

The honest test: every model is **trained on contaminated data** and scored on the same **clean** held-out test set. Faults are injected at controlled rates (0–30%) as warm-biased readings that stay inside the physical range, the hard case.

## Results

At 10% faulty training readings (6,000 of 60,000), on the clean test set:

| Model | RMSE (°C) | MAE (°C) | R² | Bias (°C) |
|---|---|---|---|---|
| OLS (MLE / least squares) | 3.505 | 2.867 | 0.322 | +1.109 |
| Ridge (MAP, Gaussian prior) | 3.579 | 2.918 | 0.293 | +1.113 |
| Bayesian linear regression | 3.441 | 2.758 | 0.346 | +1.109 |
| RANSAC | 3.675 | 2.320 | 0.254 | −0.494 |
| **Huber (δ = 1.35)** | **3.322** | 2.304 | **0.390** | **−0.141** |

- **Huber's bias is 7.5× smaller than OLS's** (0.14 °C against 1.11 °C): faulty sensors no longer drag the predictions warm.
- Huber's fault mask catches **99.4%** of the injected faults.
- At 30% contamination, Huber's RMSE is about **17% lower** than OLS's (3.96 °C against 4.79 °C).
- Ridge does not help here: a Gaussian prior shrinks weights but does nothing about a corrupted target. The key point is that regularisation and robustness solve different problems.
- R² stays near 0.4 because salinity alone is ambiguous (the same salinity occurs at different temperatures in different water masses). Adding depth would raise it; the task was robustness.

Graphs: `figures/fig_data.png` (the data and the gate), `figures/fig_huber.png` (fits on contaminated data), `figures/fig_sweep.png` (error and bias as contamination rises). All numbers: `code/results.json`.

## Run it

```bash
pip install numpy pandas scikit-learn matplotlib
```

Put the CalCOFI download under `data/` (the path is at the top of `code/analysis.py`), then:

```bash
python3 code/analysis.py
```

```bash
python3 code/figures.py
```

## Files

| Path | What it is |
|---|---|
| `code/analysis.py` | Data audit, quality gate, contamination, the five models, the sweep |
| `code/figures.py` | Draws the three figures |
| `code/results.json` | Every number in this README |
| `presentation/` | Review 2 slides (PowerPoint and PDF) and the presentation script |
