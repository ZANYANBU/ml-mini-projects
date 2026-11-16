"""
Unit 2 Mini Project -- Ocean temperature from salinity with outlier-proof regression.
Dataset: CalCOFI Bottle Database (REAL), 1949-03 .. 2021-05  (72 years).

Two-stage defence:
  Stage 1  physical QC gate   -> removes gross input faults (leverage points)
  Stage 2  robust regression  -> removes target-side faults the gate cannot see

Unit 2 concepts applied: MLE/least squares, basis functions phi(x), robust linear
regression (Huber), ridge = MAP with Gaussian prior, Bayesian linear regression.
"""
import json, warnings
import numpy as np
import pandas as pd
from sklearn.linear_model import (LinearRegression, Ridge, HuberRegressor,
                                  RANSACRegressor, BayesianRidge)
from sklearn.preprocessing import PolynomialFeatures, RobustScaler
from sklearn.pipeline import make_pipeline
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score
from sklearn.model_selection import train_test_split, GridSearchCV

warnings.filterwarnings("ignore")
OUT = {}
DEG = 5
PATH = ("data/CalCOFI_Database_194903-202105_csv_16October2023/"
        "CalCOFI_Database_194903-202105_csv_16October2023/194903-202105_Bottle.csv")

# ---------------------------------------------------------------- 1. LOAD ----
df = pd.read_csv(PATH, usecols=lambda c: c in
                 ["Depthm", "T_degC", "Salnty", "T_qual", "S_qual"],
                 low_memory=False, encoding="latin-1")
OUT["n_raw_rows"] = int(len(df))
df = df.rename(columns={"T_degC": "temp", "Salnty": "sal", "Depthm": "depth"})

# ------------------------------------------------- 2. DATA-QUALITY AUDIT ----
paired = df.dropna(subset=["temp", "sal"])
OUT["n_paired"] = int(len(paired))
OUT["pct_pairs_missing"] = round(100 * (1 - len(paired) / len(df)), 1)

flagged = paired["T_qual"].notna() | paired["S_qual"].notna()
OUT["n_quality_flagged"] = int(flagged.sum())
OUT["pct_quality_flagged"] = round(100 * flagged.mean(), 2)

SAL_LO, SAL_HI, T_LO, T_HI = 30.0, 37.0, -2.0, 35.0     # Stage-1 QC gate
gate_fail = ~(paired["sal"].between(SAL_LO, SAL_HI) & paired["temp"].between(T_LO, T_HI))
OUT["n_gate_fail"] = int(gate_fail.sum())
OUT["sal_raw_range"] = [round(float(paired.sal.min()), 2), round(float(paired.sal.max()), 2)]
OUT["temp_raw_range"] = [round(float(paired.temp.min()), 2), round(float(paired.temp.max()), 2)]
OUT["n_discarded_total"] = int((flagged | gate_fail).sum())

# --------------------------------------------------- 3. CLEAN REFERENCE ----
clean = paired[(~flagged) & (~gate_fail)]
OUT["n_clean"] = int(len(clean))
OUT["corr_sal_temp"] = round(float(clean.sal.corr(clean.temp)), 3)
OUT["clean_sal_mean"] = round(float(clean.sal.mean()), 2)
OUT["clean_temp_mean"] = round(float(clean.temp.mean()), 2)
OUT["clean_temp_std"] = round(float(clean.temp.std()), 2)

SUB = 80_000
work = clean.sample(SUB, random_state=42) if len(clean) > SUB else clean
X = work[["sal"]].to_numpy(); y = work["temp"].to_numpy()
X_tr, X_te, y_tr, y_te = train_test_split(X, y, test_size=0.25, random_state=42)
OUT["n_modelled"] = int(len(work)); OUT["n_train"] = len(X_tr); OUT["n_test"] = len(X_te)
OUT["basis_degree"] = DEG

# ------------------------------------------ 4. SENSOR-FAULT INJECTION -------
# Faults that SURVIVE the Stage-1 gate: every corrupted temperature is still a
# physically plausible number, so no range check can catch it. This is exactly
# the regime robust loss functions exist for.
def inject(y_in, rate, seed):
    """Real thermistor faults are WARM-BIASED (self-heating, biofouling, deck
    solar heating), not symmetric noise -- and every value stays inside the
    physical gate, so no range check can catch them."""
    rng = np.random.default_rng(seed)
    y2 = y_in.copy(); n = len(y2); k = int(round(rate * n))
    if k == 0:
        return y2, np.zeros(n, bool)
    idx = rng.choice(n, k, replace=False)
    mode = rng.integers(0, 3, k)
    for i, m in zip(idx, mode):
        if m == 0:        # self-heating drift: reads several degrees too warm
            y2[i] = min(y2[i] + rng.uniform(5, 14), T_HI)
        elif m == 1:      # biofouled sensor latched to a warm plateau
            y2[i] = rng.uniform(18, 26)
        else:             # bottle sat on deck in the sun before reading
            y2[i] = min(y2[i] + rng.uniform(8, 20), T_HI)
    mask = np.zeros(n, bool); mask[idx] = True
    return y2, mask

# --------------------------------------------------------- 5. MODELS -------
def basis():                       # phi(x): polynomial basis + robust scaling
    return [PolynomialFeatures(DEG, include_bias=False), RobustScaler()]

def models(alpha):
    return {
        "OLS  (MLE / least squares)":    make_pipeline(*basis(), LinearRegression()),
        "Ridge  (MAP, Gaussian prior)":  make_pipeline(*basis(), Ridge(alpha=alpha)),
        "Bayesian linear regression":    make_pipeline(*basis(), BayesianRidge()),
        "RANSAC  (consensus)":           make_pipeline(*basis(), RANSACRegressor(random_state=0)),
        "Huber  (robust, delta=1.35)":   make_pipeline(*basis(), HuberRegressor(epsilon=1.35, max_iter=800)),
    }

def evaluate(ms, ytr, Xtr=X_tr):
    out = {}
    for name, m in ms.items():
        m.fit(Xtr, ytr); p = m.predict(X_te)
        out[name] = {"rmse": float(np.sqrt(mean_squared_error(y_te, p))),
                     "mae":  float(mean_absolute_error(y_te, p)),
                     "r2":   float(r2_score(y_te, p)),
                     "bias": float(np.mean(p - y_te))}
    return out

gs = GridSearchCV(make_pipeline(*basis(), Ridge()),
                  {"ridge__alpha": np.logspace(-3, 4, 15)}, cv=5,
                  scoring="neg_root_mean_squared_error").fit(X_tr, y_tr)
ALPHA = float(gs.best_params_["ridge__alpha"]); OUT["ridge_alpha_cv"] = ALPHA

OUT["baseline_clean"] = evaluate(models(ALPHA), y_tr)

RATE = 0.10
y_bad, mask = inject(y_tr, RATE, 2026)
OUT["headline_rate"] = RATE; OUT["n_corrupted"] = int(mask.sum())
OUT["contaminated"] = evaluate(models(ALPHA), y_bad)

# ------------------------------------------------ 6. DEGRADATION SWEEP ------
rates = [0.0, 0.05, 0.10, 0.15, 0.20, 0.30]
sweep = {k: [] for k in models(ALPHA)}
sweep_bias = {k: [] for k in models(ALPHA)}
for r in rates:
    yb, _ = inject(y_tr, r, 7)
    for n_, m_ in evaluate(models(ALPHA), yb).items():
        sweep[n_].append(round(m_["rmse"], 4)); sweep_bias[n_].append(round(m_["bias"], 4))
OUT["sweep_rates"] = rates; OUT["sweep_rmse"] = sweep; OUT["sweep_bias"] = sweep_bias

# ------------------------------------- 7. HUBER AS AN OUTLIER DETECTOR ------
hub = make_pipeline(*basis(), HuberRegressor(epsilon=1.35, max_iter=800)).fit(X_tr, y_bad)
fl = hub[-1].outliers_
OUT["huber_flagged"] = int(fl.sum())
OUT["huber_recall"] = round(float((fl & mask).sum() / max(mask.sum(), 1)), 3)
OUT["huber_precision"] = round(float((fl & mask).sum() / max(fl.sum(), 1)), 3)

# ------------------------------------------- 8. BAYESIAN UNCERTAINTY --------
bl = make_pipeline(*basis(), BayesianRidge()).fit(X_tr, y_bad)
_, sd = bl[-1].predict(bl[:-1].transform(X_te), return_std=True)
OUT["bayes_pred_sd"] = round(float(sd.mean()), 3)
OUT["bayes_noise_var"] = round(float(1 / bl[-1].alpha_), 3)

json.dump(OUT, open("results.json", "w"), indent=2)

# ------------------------------------------------------------- REPORT -------
b, c = OUT["baseline_clean"], OUT["contaminated"]
W = 30
print("=" * 86)
print(f"CalCOFI bottle records read     : {OUT['n_raw_rows']:,}")
print(f"Rows with paired T and S        : {OUT['n_paired']:,}")
print(f"Flagged by CalCOFI QC codes     : {OUT['n_quality_flagged']:,}  ({OUT['pct_quality_flagged']}%)")
print(f"Rejected by physical gate       : {OUT['n_gate_fail']:,}")
print(f"Raw salinity range              : {OUT['sal_raw_range'][0]} .. {OUT['sal_raw_range'][1]} PSU")
print(f"Raw temperature range           : {OUT['temp_raw_range'][0]} .. {OUT['temp_raw_range'][1]} C")
print(f"Clean set after both stages     : {OUT['n_clean']:,}")
print(f"corr(salinity, temperature)     : {OUT['corr_sal_temp']}")
print(f"Modelled  train/test            : {OUT['n_train']:,} / {OUT['n_test']:,}   basis degree {DEG}")
print(f"Ridge alpha (5-fold CV)         : {ALPHA:g}")
print("=" * 86)
print(f"\n{'model':<{W}}{'CLEAN RMSE':>11}{'DIRTY RMSE':>11}{'penalty':>9}{'dirty R2':>9}{'warm bias C':>12}")
print("-" * 86)
for n_ in b:
    pen = c[n_]['rmse'] - b[n_]['rmse']
    print(f"{n_:<{W}}{b[n_]['rmse']:>11.3f}{c[n_]['rmse']:>11.3f}{pen:>+9.3f}{c[n_]['r2']:>9.3f}{c[n_]['bias']:>+12.3f}")
print(f"\n({int(RATE*100)}% of {OUT['n_train']:,} training rows = {OUT['n_corrupted']:,} faulty sensors;"
      f" all models scored on the SAME clean held-out test set)")
print("\nRMSE vs contamination rate")
print(f"{'model':<{W}}" + "".join(f"{int(r*100):>8}%" for r in rates))
for n_, v in sweep.items():
    print(f"{n_:<{W}}" + "".join(f"{x:>9.3f}" for x in v))
print("\nPrediction warm-bias (C) vs contamination rate")
print(f"{'model':<{W}}" + "".join(f"{int(r*100):>8}%" for r in rates))
for n_, v in sweep_bias.items():
    print(f"{n_:<{W}}" + "".join(f"{x:>+9.3f}" for x in v))
print(f"\nHuber outlier detector : flagged {OUT['huber_flagged']:,} | "
      f"recall {OUT['huber_recall']} | precision {OUT['huber_precision']}")
print(f"Bayesian                : noise var {OUT['bayes_noise_var']} | mean predictive sd {OUT['bayes_pred_sd']} C")
print("=" * 86)
