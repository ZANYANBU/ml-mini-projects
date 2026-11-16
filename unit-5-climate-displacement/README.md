# Predicting climate-driven population displacement

**Unit 5 – Combining models.** A hybrid of Bayesian Model Averaging and Gradient Boosting. Team Cash Guard: V. Anbu Chelvan, S. Roopesh, B. Charith Reddy, Y. Rupesh Reddy.

## Problem statement

Develop a hybrid model combining Bayesian Model Averaging and Gradient Boosting to predict population displacement caused by extreme climate events, and support local authorities in urban planning and emergency aid distribution.

Displacement figures are usually known only after an event. A reliable estimate, with a range showing how sure it is, at the moment a flood warning or cyclone forecast is issued would let authorities pre-position tents, food and water and plan shelters.

## Data

| Source | Content |
|---|---|
| [IDMC – internal displacements associated with disasters](https://data.humdata.org/dataset/idmc-internal-displacements-new-displacements-associated-with-disasters) (via HDX, CC BY-IGO) | 29,698 disaster events, 2008–2025: country, dates, hazard type, people displaced |
| [World Bank Open Data API](https://data.worldbank.org) | Population, urban share, GDP per capita, population density by country and year |

Weather-related events with at least one person displaced: 28,112 events in 214 countries and territories; 28,000 with complete country data. Floods are 52.8% of events; floods and storms cause 96% of all displacement.

Inputs: event duration, season (month as sine and cosine), named storm, multi-country, monthly-report flag, year trend, population, urban share, density, GDP per capita, the country's displacement history (past years only), hazard type. Target: log(1 + people displaced).

## Method

1. **Bayesian Model Averaging.** Fit all 2¹³ = 8,192 subsets of the 13 numeric features by least squares, weight each by exp(−BIC/2), and average. This gives the posterior inclusion probability of each feature and an honest predictive standard deviation.
2. **Gradient Boosting on BMA's residuals.** 500 trees (depth 4, learning rate 0.05, 80% subsampling, at least 40 events per leaf) learn the non-linear patterns BMA leaves behind.
3. **Hybrid prediction** = BMA prediction + boosted residual, with a 90% interval from BMA (± 1.645 σ).

Train/test: random 80/20 split (22,400 / 5,600 events).

## Results

On 5,600 unseen events:

| Model | RMSE (log) | MAE (log) | R² | Typical error |
|---|---|---|---|---|
| BMA (averaged linear models) | 2.187 | 1.740 | 0.361 | ×4.3 |
| Gradient Boosting | 1.902 | 1.482 | 0.517 | ×3.4 |
| **Hybrid BMA + Gradient Boosting** | **1.897** | **1.481** | **0.520** | ×3.4 |

- The hybrid is the most accurate of the three. Boosting adds about 16 points of explained variance over BMA.
- BMA contributes the uncertainty: **94% of real outcomes fell inside the 90% interval**, so the ranges can be trusted (slightly conservative).
- Nine features have inclusion probability close to 1: duration, season, named storm, the reporting trend, population, urban share, density and the country's history. The single best model has posterior probability 0.78, so averaging still matters for the remaining 22%.

**For local authorities:** `plan_aid()` turns a forecast into supplies using the Sphere humanitarian standards (15 L of water per person per day, 3.5 m² of covered space per person, one family tent per five people). Example, a named typhoon in the Philippines in November lasting 3 days: expected 48,810 people displaced, 9,762 tents, 170,835 m² of shelter and 5.1 million litres of water for a week; the 95% case is 1.77 million people.

## Run it in Google Colab

Open [the notebook in Colab](https://colab.research.google.com/github/ZANYANBU/ml-mini-projects/blob/main/unit-5-climate-displacement/Climate_Displacement_BMA_GradientBoosting.ipynb), then **Runtime → Run all** (about one minute). It downloads the data itself; nothing to upload.

## Files

| Path | What it is |
|---|---|
| `Climate_Displacement_BMA_GradientBoosting.ipynb` | The code, already run, with every graph |
| `figures/` | The graphs as PNG |
| `presentation/Climate_Displacement_Presentation.pptx` | Review 5 slides |
| `report/Climate_Displacement_Report.docx` | The unit's written report |
