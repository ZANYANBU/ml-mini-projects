"""
CashGuard - sample data generator
=================================
Problem statement #21: predict when an ATM will run out of cash.

Builds a sample CSV with exactly the same 13 columns as the Kaggle dataset
"ATM Cash Demand Forecasting and Management" (zoya77), calibrated to the
statistics published on that dataset's data card:

    rows                     5,658          columns    13
    period                   2022-01-01 to 2024-01-01
    ATMs                     50  (ATM_0001 .. ATM_0050)
    Total_Withdrawals        1,380 .. 107,790   mean ~49,812  sd ~15,218
    Total_Deposits           0 .. 32,395        mean ~10,157  sd ~4,874
    Previous_Day_Cash_Level  23,266 .. 172,227  mean ~100,392 sd ~20,498
    Holiday_Flag = 1         125 rows (2.21%)
    Special_Event_Flag = 1   546 rows (9.65%)

Only the Python standard library is used - no pandas, no numpy, no pip install.

Run:  python3 make_sample_data.py
Out:  atm_cash_management_dataset_sample.csv
"""

import csv
import os
import random
from datetime import date, timedelta

random.seed(42)          # same file every run, so results are reproducible

# ----------------------------------------------------------------- settings
N_ROWS = 5658
N_ATMS = 50
START = date(2022, 1, 1)
END = date(2024, 1, 1)
OUTFILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data", "atm_cash_management_dataset_sample.csv")

DAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday",
        "Saturday", "Sunday"]
TIMES = ["Morning", "Afternoon", "Evening", "Night"]
LOCATIONS = ["Mall", "Supermarket", "Bank Branch", "Gas Station", "Standalone"]
WEATHER = ["Sunny", "Cloudy", "Rainy", "Stormy"]

# Public holidays (month, day). 8 dates x 2 years / 731 days = 2.2% of rows,
# which matches the Holiday_Flag rate published for the real dataset.
HOLIDAYS = {(1, 1), (1, 26), (3, 29), (5, 1),
            (8, 15), (10, 2), (11, 12), (12, 25)}

# How much each condition lifts or lowers cash demand.
# These are the real-world effects named in the problem statement.
DOW_FACTOR = {"Monday": 1.08, "Tuesday": 0.96, "Wednesday": 0.95,
              "Thursday": 0.98, "Friday": 1.12, "Saturday": 1.06,
              "Sunday": 0.92}
TIME_FACTOR = {"Morning": 0.98, "Afternoon": 1.06, "Evening": 1.04,
               "Night": 0.88}
LOC_FACTOR = {"Mall": 1.10, "Supermarket": 1.05, "Bank Branch": 0.95,
              "Gas Station": 1.00, "Standalone": 0.92}
WEATHER_FACTOR = {"Sunny": 1.02, "Cloudy": 1.00, "Rainy": 0.94, "Stormy": 0.85}

SALARY_LIFT = 1.22       # 1st-5th and 25th-month end: salary / pension week
HOLIDAY_LIFT = 1.18
EVENT_LIFT = 1.12


# ----------------------------------------------------------------- helpers
def is_salary_window(d):
    """True during the salary / pension period: 1st-5th or 25th onwards."""
    return d.day <= 5 or d.day >= 25


def is_holiday(d):
    return (d.month, d.day) in HOLIDAYS


def rescale(values, target_mean, target_sd, lo, hi):
    """Shift and stretch a list to the published mean/sd, then clip to range.

    An affine transform, so any relationship between columns is preserved.
    """
    n = len(values)
    mean = sum(values) / n
    sd = (sum((v - mean) ** 2 for v in values) / n) ** 0.5
    out = []
    for v in values:
        z = (v - mean) / sd
        out.append(min(hi, max(lo, round(target_mean + z * target_sd))))
    return out


def demand_signal(atm_base, d, time_of_day, location, weather, competitors,
                  holiday, event):
    """Expected cash demand for one ATM on one day, before random noise.

    This is the ground truth the model in atm_cash_analysis.py has to learn.
    """
    x = atm_base
    x *= DOW_FACTOR[DAYS[d.weekday()]]
    x *= TIME_FACTOR[time_of_day]
    x *= LOC_FACTOR[location]
    x *= WEATHER_FACTOR[weather]
    x *= 1.0 - 0.03 * competitors          # rivals nearby divert some demand
    if is_salary_window(d):
        x *= SALARY_LIFT
    if holiday:
        x *= HOLIDAY_LIFT
    if event:
        x *= EVENT_LIFT
    return x


# ----------------------------------------------------------------- build it
def build_rows():
    # Each ATM has a fixed home location, a fixed number of rivals nearby and
    # its own popularity. A real ATM does not move, so these stay constant.
    atm_ids = [f"ATM_{i:04d}" for i in range(1, N_ATMS + 1)]
    # 10 ATMs per location type, so each type is 20% of the rows - the same
    # balanced split the real dataset has.
    atm_location = {a: LOCATIONS[i % len(LOCATIONS)]
                    for i, a in enumerate(atm_ids)}
    atm_rivals = {a: random.randint(0, 5) for a in atm_ids}
    atm_base = {a: random.gauss(50000, 9000) for a in atm_ids}

    span = (END - START).days
    raw_withdrawals, raw_deposits, raw_balance, raw_target = [], [], [], []
    rows = []

    for _ in range(N_ROWS):
        atm = random.choice(atm_ids)
        d = START + timedelta(days=random.randint(0, span))
        time_of_day = random.choice(TIMES)
        weather = random.choices(WEATHER, weights=[40, 30, 25, 5])[0]
        location = atm_location[atm]
        rivals = atm_rivals[atm]

        holiday = is_holiday(d)
        event = random.random() < 0.0965          # 9.65% of rows

        # today's withdrawals
        today = demand_signal(atm_base[atm], d, time_of_day, location,
                              weather, rivals, holiday, event)
        # A few very quiet days - machine out of service, road closed, and so
        # on. The real dataset has the same thin lower tail (37 rows in its
        # lowest bin), and these rare days are what a refill model must survive.
        if random.random() < 0.012:
            today *= random.uniform(0.20, 0.50)
        raw_withdrawals.append(today * random.gauss(1.0, 0.13))

        # tomorrow's demand - this is the column we are trying to predict.
        # It uses tomorrow's calendar, so weekends, holidays and the salary
        # window all matter, plus a little carry-over from today.
        nxt = d + timedelta(days=1)
        tomorrow = demand_signal(atm_base[atm], nxt, time_of_day, location,
                                 weather, rivals, is_holiday(nxt),
                                 random.random() < 0.0965)
        raw_target.append(0.85 * tomorrow + 0.15 * today
                          + random.gauss(0, 4200))

        raw_deposits.append(random.gauss(10157, 4874))
        raw_balance.append(random.gauss(100392, 20498))

        rows.append({
            "ATM_ID": atm,
            "Date": d.isoformat(),
            "Day_of_Week": DAYS[d.weekday()],
            "Time_of_Day": time_of_day,
            "Location_Type": location,
            "Holiday_Flag": 1 if holiday else 0,
            "Special_Event_Flag": 1 if event else 0,
            "Weather_Condition": weather,
            "Nearby_Competitor_ATMs": rivals,
        })

    # Match the published mean / sd / min / max of the real dataset.
    withdrawals = rescale(raw_withdrawals, 49812, 15218, 1380, 107790)
    deposits = rescale(raw_deposits, 10157, 4874, 0, 32395)
    balance = rescale(raw_balance, 100392, 20498, 23266, 172227)
    target = rescale(raw_target, 49900, 15400, 1400, 108000)

    for i, r in enumerate(rows):
        r["Total_Withdrawals"] = withdrawals[i]
        r["Total_Deposits"] = deposits[i]
        r["Previous_Day_Cash_Level"] = balance[i]
        r["Cash_Demand_Next_Day"] = target[i]

    return rows


# The 13 columns, in the same order as the Kaggle file.
COLUMNS = ["ATM_ID", "Date", "Day_of_Week", "Time_of_Day",
           "Total_Withdrawals", "Total_Deposits", "Location_Type",
           "Holiday_Flag", "Special_Event_Flag", "Previous_Day_Cash_Level",
           "Weather_Condition", "Nearby_Competitor_ATMs",
           "Cash_Demand_Next_Day"]


def main():
    rows = build_rows()
    with open(OUTFILE, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=COLUMNS)
        w.writeheader()
        for r in rows:
            w.writerow({c: r[c] for c in COLUMNS})

    print(f"Wrote {OUTFILE}")
    print(f"  {len(rows)} rows x {len(COLUMNS)} columns")

    # quick confirmation that we hit the published numbers
    def col(name):
        return [r[name] for r in rows]

    for name in ("Total_Withdrawals", "Total_Deposits",
                 "Previous_Day_Cash_Level", "Cash_Demand_Next_Day"):
        v = col(name)
        m = sum(v) / len(v)
        sd = (sum((x - m) ** 2 for x in v) / len(v)) ** 0.5
        print(f"  {name:24s} min={min(v):>7,d}  max={max(v):>7,d}  "
              f"mean={m:>9,.0f}  sd={sd:>8,.0f}")

    hol = sum(col("Holiday_Flag"))
    evt = sum(col("Special_Event_Flag"))
    print(f"  Holiday_Flag = 1         {hol} rows ({hol/len(rows)*100:.2f}%)")
    print(f"  Special_Event_Flag = 1   {evt} rows ({evt/len(rows)*100:.2f}%)")


if __name__ == "__main__":
    main()
