"""
CashGuard - ATM cash-out prediction
===================================
Problem statement #21: predict when an ATM will run out of cash and needs
replenishment, using withdrawal patterns, ATM location, weekends, holidays,
salary periods and historical withdrawal data.

What this script does, in order:

    1. loads the CSV and reports basic statistics       (Review 1)
    2. engineers the features named in the statement    (Review 2)
    3. fits a multiple linear regression by hand        (Review 2)
    4. scores it against two baselines                  (Review 3)
    5. turns the forecast into a days-to-empty alert    (the actual goal)

The regression is written from first principles - normal equations solved with
Gaussian elimination. No pandas, no numpy, no scikit-learn, so it runs on a
plain Python install and satisfies the "avoid python libraries" rule.

Run:  python3 atm_cash_analysis.py
"""

import csv
import os
from datetime import date

TARGET = "Cash_Demand_Next_Day"
LEAD_TIME_DAYS = 2.0        # how long a cash-in-transit refill takes to arrive

# Try the real Kaggle file first, then fall back to the generated sample.
DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data")          # the CSVs live in ../data
CANDIDATES = [os.path.join(DATA_DIR, "atm_cash_management_dataset.csv"),
              os.path.join(DATA_DIR, "atm_cash_management_dataset_sample.csv")]

NUMERIC = ["Total_Withdrawals", "Total_Deposits", "Previous_Day_Cash_Level",
           "Nearby_Competitor_ATMs", "Holiday_Flag", "Special_Event_Flag"]
CATEGORICAL = ["Day_of_Week", "Time_of_Day", "Location_Type",
               "Weather_Condition"]


# ===================================================================== 1. load
def find_csv():
    for name in CANDIDATES:
        if os.path.exists(name):
            return name
    raise SystemExit(
        "No dataset found. Run 'python3 make_sample_data.py' first, or put "
        "the real atm_cash_management_dataset.csv next to this script.")


def load(path):
    with open(path, newline="") as f:
        rows = list(csv.DictReader(f))
    for r in rows:
        for k in NUMERIC + [TARGET]:
            r[k] = float(r[k])
        y, m, d = (int(x) for x in r["Date"].split("-"))
        r["_date"] = date(y, m, d)
    return rows


# ================================================================ 2. statistics
def describe(values):
    """min, max, mean, median, standard deviation and skewness."""
    n = len(values)
    s = sorted(values)
    mean = sum(values) / n
    med = s[n // 2] if n % 2 else (s[n // 2 - 1] + s[n // 2]) / 2
    var = sum((v - mean) ** 2 for v in values) / n
    sd = var ** 0.5
    skew = (sum((v - mean) ** 3 for v in values) / n / sd ** 3) if sd else 0.0
    return dict(n=n, lo=min(values), hi=max(values), mean=mean, med=med,
                sd=sd, skew=skew)


def histogram(values, bins=10, width=40):
    lo, hi = min(values), max(values)
    step = (hi - lo) / bins
    counts = [0] * bins
    for v in values:
        i = min(bins - 1, int((v - lo) / step)) if step else 0
        counts[i] += 1
    top = max(counts)
    for i, c in enumerate(counts):
        bar = "#" * int(c / top * width)
        print(f"    {lo + i*step:>9,.0f} - {lo + (i+1)*step:>9,.0f} "
              f"| {bar:<{width}} {c:>5,d}")


def section(title):
    print()
    print("=" * 74)
    print(title)
    print("=" * 74)


def explore(rows):
    section("1. DATASET AND STATISTICAL ANALYSIS")
    print(f"  rows: {len(rows):,}    columns: {len(rows[0]) - 1}")
    dates = [r["_date"] for r in rows]
    print(f"  period: {min(dates)}  to  {max(dates)}")
    print(f"  ATMs:   {len(set(r['ATM_ID'] for r in rows))}")

    missing = sum(1 for r in rows for k, v in r.items() if v == "")
    print(f"  missing values: {missing}")

    print("\n  Numeric summary")
    print(f"    {'column':<26}{'min':>10}{'max':>11}{'mean':>11}"
          f"{'median':>11}{'sd':>10}{'skew':>8}")
    for col in ["Total_Withdrawals", "Total_Deposits",
                "Previous_Day_Cash_Level", TARGET]:
        d = describe([r[col] for r in rows])
        print(f"    {col:<26}{d['lo']:>10,.0f}{d['hi']:>11,.0f}"
              f"{d['mean']:>11,.0f}{d['med']:>11,.0f}{d['sd']:>10,.0f}"
              f"{d['skew']:>8.2f}")

    print("\n  Categorical frequencies")
    for col in CATEGORICAL:
        counts = {}
        for r in rows:
            counts[r[col]] = counts.get(r[col], 0) + 1
        parts = ", ".join(f"{k} {v/len(rows)*100:.0f}%" for k, v in
                          sorted(counts.items(), key=lambda kv: -kv[1]))
        print(f"    {col:<20} {len(counts)} levels: {parts}")

    for col in ["Holiday_Flag", "Special_Event_Flag"]:
        ones = sum(r[col] for r in rows)
        print(f"    {col:<20} {ones:,.0f} rows set to 1 "
              f"({ones/len(rows)*100:.2f}%)")

    print(f"\n  Distribution of {TARGET}")
    histogram([r[TARGET] for r in rows])

    # average demand by weekday - the weekend effect the statement asks about
    print("\n  Mean next-day demand by day of week")
    order = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday",
             "Saturday", "Sunday"]
    for day in order:
        vals = [r[TARGET] for r in rows if r["Day_of_Week"] == day]
        if vals:
            print(f"    {day:<12} {sum(vals)/len(vals):>10,.0f}   "
                  f"({len(vals):,} rows)")
    print("    Note: the target is NEXT day's demand, so this effect reads")
    print("    shifted by one day - a Thursday row carries Friday's demand.")


# ========================================================= 3. feature building
def is_salary_window(d):
    """Salary and pension period: the first five days, or the 25th onwards."""
    return d.day <= 5 or d.day >= 25


def build_features(rows):
    """Turn each row into a plain list of numbers, plus the feature names."""
    # one-hot: drop the first level of each category to avoid collinearity
    levels = {c: sorted(set(r[c] for r in rows))[1:] for c in CATEGORICAL}

    names = (["Total_Withdrawals", "Total_Deposits", "Previous_Day_Cash_Level",
              "Nearby_Competitor_ATMs", "Holiday_Flag", "Special_Event_Flag",
              "is_weekend", "is_salary_window", "day_of_month"]
             + [f"{c}={v}" for c in CATEGORICAL for v in levels[c]])

    X, y = [], []
    for r in rows:
        d = r["_date"]
        row = [r["Total_Withdrawals"], r["Total_Deposits"],
               r["Previous_Day_Cash_Level"], r["Nearby_Competitor_ATMs"],
               r["Holiday_Flag"], r["Special_Event_Flag"],
               1.0 if d.weekday() >= 5 else 0.0,
               1.0 if is_salary_window(d) else 0.0,
               float(d.day)]
        for c in CATEGORICAL:
            row += [1.0 if r[c] == v else 0.0 for v in levels[c]]
        X.append(row)
        y.append(r[TARGET])
    return X, y, names


# =============================================================== 4. regression
def solve(A, b):
    """Solve A w = b by Gaussian elimination with partial pivoting."""
    n = len(A)
    M = [list(A[i]) + [b[i]] for i in range(n)]
    for c in range(n):
        pivot = max(range(c, n), key=lambda r: abs(M[r][c]))
        M[c], M[pivot] = M[pivot], M[c]
        if abs(M[c][c]) < 1e-12:
            continue
        for r in range(c + 1, n):
            f = M[r][c] / M[c][c]
            if f:
                for k in range(c, n + 1):
                    M[r][k] -= f * M[c][k]
    w = [0.0] * n
    for c in range(n - 1, -1, -1):
        acc = M[c][n] - sum(M[c][k] * w[k] for k in range(c + 1, n))
        w[c] = acc / M[c][c] if abs(M[c][c]) > 1e-12 else 0.0
    return w


class LinearModel:
    """Multiple linear regression, fitted with the normal equations.

        minimise  sum (y - Xw - b)^2  +  ridge * |w|^2
        solution  (X'X + ridge*I) w = X'y      with X and y centred

    Features are standardised first, so the coefficients are comparable and
    the matrix stays well conditioned.
    """

    def __init__(self, ridge=1e-6):
        self.ridge = ridge

    def fit(self, X, y):
        n, p = len(X), len(X[0])
        self.mean = [sum(r[j] for r in X) / n for j in range(p)]
        self.sd = []
        for j in range(p):
            var = sum((r[j] - self.mean[j]) ** 2 for r in X) / n
            self.sd.append(var ** 0.5 or 1.0)      # constant column -> 1.0
        Z = [[(r[j] - self.mean[j]) / self.sd[j] for j in range(p)] for r in X]

        self.y_mean = sum(y) / n
        yc = [v - self.y_mean for v in y]

        # normal equations
        A = [[sum(Z[i][a] * Z[i][b] for i in range(n)) for b in range(p)]
             for a in range(p)]
        for j in range(p):
            A[j][j] += self.ridge * n
        rhs = [sum(Z[i][j] * yc[i] for i in range(n)) for j in range(p)]
        self.w = solve(A, rhs)
        return self

    def predict_one(self, row):
        z = [(row[j] - self.mean[j]) / self.sd[j] for j in range(len(row))]
        return self.y_mean + sum(self.w[j] * z[j] for j in range(len(z)))

    def predict(self, X):
        return [self.predict_one(r) for r in X]


# ================================================================== 5. scoring
def score(y_true, y_pred):
    n = len(y_true)
    mae = sum(abs(a - b) for a, b in zip(y_true, y_pred)) / n
    mse = sum((a - b) ** 2 for a, b in zip(y_true, y_pred)) / n
    mean = sum(y_true) / n
    ss_tot = sum((a - mean) ** 2 for a in y_true)
    ss_res = sum((a - b) ** 2 for a, b in zip(y_true, y_pred))
    mape = sum(abs(a - b) / a for a, b in zip(y_true, y_pred) if a) / n * 100
    under = sum(1 for a, b in zip(y_true, y_pred) if b < a) / n * 100
    return dict(mae=mae, rmse=mse ** 0.5, r2=1 - ss_res / ss_tot if ss_tot
                else 0.0, mape=mape, under=under)


def report(name, s):
    print(f"    {name:<28} MAE {s['mae']:>9,.0f}   RMSE {s['rmse']:>9,.0f}   "
          f"R2 {s['r2']:>6.3f}   MAPE {s['mape']:>5.1f}%")


def model_and_evaluate(rows):
    section("2. FEATURE ENGINEERING AND MODEL")

    # Time-aware split: learn from the earlier period, test on the later one.
    # A random split would let the model see the future.
    rows = sorted(rows, key=lambda r: r["_date"])
    cut = int(len(rows) * 0.7)
    split_date = rows[cut]["_date"]
    train_rows, test_rows = rows[:cut], rows[cut:]

    X, y, names = build_features(rows)
    Xtr, ytr = X[:cut], y[:cut]
    Xte, yte = X[cut:], y[cut:]

    print(f"  features built: {len(names)}")
    print("    " + ", ".join(names[:9]))
    print("    plus one-hot columns for "
          + ", ".join(CATEGORICAL))
    print(f"\n  train: {len(Xtr):,} rows  (up to {split_date})")
    print(f"  test:  {len(Xte):,} rows  (from {split_date} onwards)")

    model = LinearModel().fit(Xtr, ytr)

    print("\n  Results on the unseen test period")
    report("CashGuard regression", score(yte, model.predict(Xte)))
    # baseline 1: always predict the training mean
    mean_pred = [sum(ytr) / len(ytr)] * len(yte)
    report("baseline: training mean", score(yte, mean_pred))
    # baseline 2: assume tomorrow equals today
    today_pred = [r["Total_Withdrawals"] for r in test_rows]
    report("baseline: same as today", score(yte, today_pred))

    s = score(yte, model.predict(Xte))
    print(f"\n  Under-prediction rate: {s['under']:.1f}% of test days "
          f"(these are the ones that cause a stock-out)")

    print("\n  Which features matter most (standardised coefficients)")
    ranked = sorted(zip(names, model.w), key=lambda kv: -abs(kv[1]))
    for nm, w in ranked[:10]:
        bar = "#" * int(abs(w) / abs(ranked[0][1]) * 30)
        print(f"    {nm:<26} {w:>+10,.0f}  {bar}")

    return model, names


# ================================================= 6. the replenishment alert
def replenishment_alert(rows, model):
    """Convert the forecast into 'how many days until this ATM is empty'."""
    section("3. REPLENISHMENT ALERT  (the answer the problem statement wants)")

    # most recent record for each ATM
    latest = {}
    for r in rows:
        if r["ATM_ID"] not in latest or r["_date"] > latest[r["ATM_ID"]]["_date"]:
            latest[r["ATM_ID"]] = r

    # typical deposits per ATM - cash put back in offsets what is taken out
    deposits = {}
    for r in rows:
        deposits.setdefault(r["ATM_ID"], []).append(r["Total_Deposits"])

    X, _, _ = build_features(list(latest.values()))
    alerts = []
    for (atm, r), features in zip(latest.items(), X):
        demand = model.predict_one(features)
        dep = sum(deposits[atm]) / len(deposits[atm])
        net_drain = max(demand - dep, 1.0)          # never divide by zero
        balance = r["Previous_Day_Cash_Level"]
        alerts.append((balance / net_drain, atm, r["_date"], balance,
                       demand, net_drain))

    alerts.sort()
    print(f"  Refill lead time assumed: {LEAD_TIME_DAYS:.0f} days\n")
    print(f"    {'ATM':<10}{'last seen':<13}{'cash held':>11}"
          f"{'forecast':>11}{'net drain':>11}{'days left':>11}  status")
    for days, atm, d, bal, dem, drain in alerts[:12]:
        status = "REFILL NOW" if days <= LEAD_TIME_DAYS else "ok"
        print(f"    {atm:<10}{str(d):<13}{bal:>11,.0f}{dem:>11,.0f}"
              f"{drain:>11,.0f}{days:>11.2f}  {status}")

    urgent = [a for a in alerts if a[0] <= LEAD_TIME_DAYS]
    print(f"\n  {len(urgent)} of {len(alerts)} ATMs need a refill within the "
          f"{LEAD_TIME_DAYS:.0f}-day lead time.")
    print("  Ranking by days-left is the schedule a cash-in-transit team "
          "would drive.")


# ===================================================================== main
def main():
    path = find_csv()
    print(f"Reading {path}")
    rows = load(path)

    explore(rows)
    model, _ = model_and_evaluate(rows)
    replenishment_alert(rows, model)

    section("DONE")
    print("  Statistics above cover Review 1; the hand-coded regression and")
    print("  engineered features cover Review 2; the baseline comparison and")
    print("  the alert table are the starting point for Review 3.")


if __name__ == "__main__":
    main()
