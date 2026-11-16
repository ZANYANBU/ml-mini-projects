# CashGuard — ATM cash-out prediction

**Unit 1 – Regression.** Problem statement 17 (team Cash Guard). Predict when an ATM will run out of cash and needs
replenishment, using withdrawal patterns, ATM location, weekends, holidays,
salary periods and historical withdrawal data.

Team: V. Anbu Chelvan (lead), S. Roopesh, B. Charith Reddy, Y. Rupesh Reddy.

## How to run in VS Code

1. Open this folder (`unit-1-cashguard-atm`) in VS Code (`File → Open Folder…`).
2. Open a terminal (`` Ctrl+` ``) and run:

```bash
python3 code/make_sample_data.py
```

```bash
python3 code/atm_cash_analysis.py
```

Nothing to install. Both scripts use only the Python standard library — no
pandas, no numpy, no scikit-learn. That keeps them runnable anywhere and
satisfies the Review 2 rule of avoiding Python libraries for the model.

## Files

| File | What it does |
|---|---|
| `code/make_sample_data.py` | Generates `atm_cash_management_dataset_sample.csv` — 5,658 rows × 13 columns matching the Kaggle schema and published statistics |
| `code/atm_cash_analysis.py` | Statistics → feature engineering → hand-coded regression → baselines → refill alert |
| `data/atm_cash_management_dataset_sample.csv` | The generated sample data |

## Using the real Kaggle data instead

Download `atm_cash_management_dataset.csv` from
<https://www.kaggle.com/datasets/zoya77/atm-cash-demand-forecasting-and-management>
(a free Kaggle login is required) and drop it into `data/`.
`atm_cash_analysis.py` looks for that filename first and only falls back to
the sample, so no code changes are needed.

## What the sample data is calibrated to

The generator reproduces the statistics published on the Kaggle data card:
5,658 rows, 13 columns, 50 ATMs, 2022-01-01 to 2024-01-01,
`Total_Withdrawals` mean ≈49,812 sd ≈15,218, `Total_Deposits` mean ≈10,157,
`Previous_Day_Cash_Level` mean ≈100,392, `Holiday_Flag` ≈2%,
`Special_Event_Flag` ≈9.6%, and near-uniform categorical levels.

Two columns are **assumptions**, because the data card does not publish their
distributions: `Weather_Condition` (Sunny/Cloudy/Rainy/Stormy) and
`Nearby_Competitor_ATMs` (0–5).

One deliberate improvement over the real file: each ATM keeps a **fixed**
`Location_Type`. In the real dataset the same ATM_ID appears at different
location types on different rows, which cannot happen physically.

## The model

`Cash_Demand_Next_Day` is continuous, so this is **regression**, not
classification. Multiple linear regression fitted with the normal equations
`(XᵀX + λI)w = Xᵀy`, solved by Gaussian elimination with partial pivoting.
Features are standardised first, so the printed coefficients are directly
comparable.

Validation is **time-aware** — the first 70% of the calendar trains, the rest
tests. A random split would let the model see the future.

The "will it run out?" answer is derived after forecasting:

```
net drain    = predicted next-day demand − average deposits
days to empty = cash held in machine ÷ net drain
alert         when days to empty ≤ refill lead time (2 days)
```

## Results on the sample data

Trained on 3,960 rows up to 25 May 2023, tested on the 1,698 rows after it.

| Model | MAE | RMSE | R² | MAPE |
|---|---|---|---|---|
| **CashGuard regression** | **7,065** | **9,067** | **0.666** | **15.3%** |
| Baseline: training mean | 12,399 | 15,688 | −0.001 | 27.5% |
| Baseline: same as today | 8,563 | 11,279 | 0.483 | 18.1% |

Beating "same as today" is the bar that matters: it is what a bank without a model would do. CashGuard cuts its error by 20% (RMSE) and explains 18 points more of the variance.

Strongest standardised coefficients: today's withdrawals (+9,911), nearby competitor ATMs (−2,632), Thursday (+2,168), Saturday (−1,921), the salary window (+1,540).

**The refill alert** (2-day refill lead time): on the last day of data, 21 of the 50 ATMs have under 2 days of cash left and are flagged REFILL NOW, ranked by days left, which is the route a cash-in-transit team would drive. The full output is in [`results/run_output.txt`](results/run_output.txt).

## What the data shows (graphs in `figures/`)

| Finding | Number |
|---|---|
| Next-day demand | mean 49,894, median 48,222, sd 15,377 (right-skewed, +0.61) |
| Strongest driver | today's withdrawals, r = +0.744 (R² 0.553 on its own) |
| Nearby competitor ATMs | r = −0.396: more competitors, less demand |
| Salary window (days 1–5 and 25–31) | mean demand 56,035 against 46,122 on other days (+21%) |
| Busiest weekdays | Thursday 55,038 and Friday 53,006; quietest Saturday 45,794 |
| Holidays | 53,489 against 49,827 on working days |

## Other files

| Path | What it is |
|---|---|
| `code/make_poster_charts.py` | Draws the seven graphs in `figures/` and the poster PDF |
| `code/make_observation_guide.py` | Writes `figures/CashGuard_Observation_Guide.pdf`, what each graph shows |
| `code/build_review1_deck.py` | Generated the Review 1 slides |
| `presentation/` | Review 1 slides (PowerPoint and PDF) |
