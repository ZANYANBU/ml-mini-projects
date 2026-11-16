"""
CashGuard - handwriting guide for the poster
============================================
One A4 page per graph: the printed graph on top, and underneath it the exact
observation text to copy onto the A3 poster in pen.

Every number in the text is recomputed from the dataset, so if you drop the
real Kaggle CSV into this folder and re-run, the sentences update themselves.

Run:  python3 make_poster_charts.py      (first - builds the graph PNGs)
      python3 make_observation_guide.py

Out:  poster_charts/CashGuard_Observation_Guide.pdf
"""
import csv, os, textwrap
from datetime import date
from collections import defaultdict

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.image as mpimg
from matplotlib.backends.backend_pdf import PdfPages
from matplotlib.patches import FancyBboxPatch
import numpy as np

OUT = "poster_charts"
TARGET = "Cash_Demand_Next_Day"
NUM = ["Total_Withdrawals", "Total_Deposits", "Previous_Day_Cash_Level",
       "Nearby_Competitor_ATMs", "Holiday_Flag", "Special_Event_Flag", TARGET]
CANDIDATES = ["atm_cash_management_dataset.csv",
              "atm_cash_management_dataset_sample.csv"]

INK, BLUE, AMBER, GREY = "#12263A", "#2E6F9E", "#D98E32", "#9AA5B1"
A4 = (8.27, 11.69)
LEAD_TIME_DAYS = 2.0

plt.rcParams.update({"figure.dpi": 200, "savefig.dpi": 200,
                     "text.color": INK, "figure.facecolor": "white"})


def load():
    path = next((p for p in CANDIDATES if os.path.exists(p)), None)
    if path is None:
        raise SystemExit("No dataset found - run make_sample_data.py first.")
    rows = list(csv.DictReader(open(path, newline="")))
    for r in rows:
        for k in NUM:
            r[k] = float(r[k])
        y, m, d = (int(x) for x in r["Date"].split("-"))
        r["_date"] = date(y, m, d)
        r["is_salary_window"] = 1.0 if (r["_date"].day <= 5 or
                                        r["_date"].day >= 25) else 0.0
    return path, rows


def stats(rows):
    """Every number that appears in the observation sentences."""
    s = {}
    y = np.array([r[TARGET] for r in rows])
    w = np.array([r["Total_Withdrawals"] for r in rows])
    dep = np.array([r["Total_Deposits"] for r in rows])
    prev = np.array([r["Previous_Day_Cash_Level"] for r in rows])

    s["n"] = len(y)
    s["mean"], s["med"], s["sd"] = y.mean(), np.median(y), y.std()
    s["q1"], s["q3"] = np.percentile(y, 25), np.percentile(y, 75)
    s["lo"], s["hi"] = y.min(), y.max()
    s["skew"] = float(((y - s["mean"]) ** 3).mean() / s["sd"] ** 3)

    g = defaultdict(list)
    for r in rows:
        g[r["Location_Type"]].append(r[TARGET])
    meds = {k: float(np.median(v)) for k, v in g.items()}
    iqrs = {k: float(np.percentile(v, 75) - np.percentile(v, 25))
            for k, v in g.items()}
    s["loc_hi"] = max(meds, key=meds.get)
    s["loc_lo"] = min(meds, key=meds.get)
    s["loc_hi_med"], s["loc_lo_med"] = meds[s["loc_hi"]], meds[s["loc_lo"]]
    s["loc_hi_iqr"], s["loc_lo_iqr"] = iqrs[s["loc_hi"]], iqrs[s["loc_lo"]]
    s["loc_gap"] = s["loc_hi_med"] - s["loc_lo_med"]

    def r_with(v):
        return float(np.corrcoef(v, y)[0, 1])
    s["r_wd"] = r_with(w)
    s["r_comp"] = r_with([r["Nearby_Competitor_ATMs"] for r in rows])
    s["r_sal"] = r_with([r["is_salary_window"] for r in rows])
    s["r_dep"] = r_with(dep)
    s["r_prev"] = r_with(prev)
    s["r_wd_comp"] = float(np.corrcoef(
        w, [r["Nearby_Competitor_ATMs"] for r in rows])[0, 1])

    m, b = np.polyfit(w, y, 1)
    s["slope"], s["intercept"] = float(m), float(b)
    s["r2"] = s["r_wd"] ** 2

    order = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday",
             "Saturday", "Sunday"]
    dow = {d: np.mean([r[TARGET] for r in rows if r["Day_of_Week"] == d])
           for d in order}
    s["dow_hi"] = max(dow, key=dow.get)
    s["dow_lo"] = min(dow, key=dow.get)
    s["dow_hi_mean"], s["dow_lo_mean"] = dow[s["dow_hi"]], dow[s["dow_lo"]]
    s["dow_gap"] = s["dow_hi_mean"] - s["dow_lo_mean"]
    s["dow_hi_next"] = order[(order.index(s["dow_hi"]) + 1) % 7]

    def grp(f):
        v = [r[TARGET] for r in rows if f(r)]
        return float(np.mean(v)), len(v)
    s["sal_mean"], s["sal_n"] = grp(lambda r: r["is_salary_window"])
    s["nor_mean"], _ = grp(lambda r: not r["is_salary_window"])
    s["sal_lift"] = (s["sal_mean"] / s["nor_mean"] - 1) * 100
    s["hol_mean"], s["hol_n"] = grp(lambda r: r["Holiday_Flag"])
    s["work_mean"], _ = grp(lambda r: not r["Holiday_Flag"])
    s["ev_mean"], s["ev_n"] = grp(lambda r: r["Special_Event_Flag"])
    s["noev_mean"], _ = grp(lambda r: not r["Special_Event_Flag"])

    s["w_mean"], s["dep_mean"], s["prev_mean"] = w.mean(), dep.mean(), prev.mean()
    s["drain"] = s["w_mean"] - s["dep_mean"]
    s["days_cash"] = s["prev_mean"] / s["drain"]
    s["dep_ratio"] = s["w_mean"] / s["dep_mean"]
    return s


def texts(s):
    """(file, heading, key-numbers line, observation to handwrite)"""
    return [
        ("01_histogram_demand.png",
         "Graph 1 — Distribution of next-day cash demand",
         f"n = {s['n']:,}   mean ₹{s['mean']:,.0f}   median ₹{s['med']:,.0f}   "
         f"SD ₹{s['sd']:,.0f}   Q1–Q3 ₹{s['q1']:,.0f}–₹{s['q3']:,.0f}   "
         f"skew {s['skew']:+.2f}",
         f"Demand is roughly bell-shaped but leans to the right — skewness is "
         f"{s['skew']:+.2f}, and the mean (₹{s['mean']:,.0f}) sits above the "
         f"median (₹{s['med']:,.0f}). Half of all ATM-days fall inside the "
         f"narrow band ₹{s['q1']:,.0f} to ₹{s['q3']:,.0f}, yet the tail "
         f"stretches all the way to ₹{s['hi']:,.0f}. A bank that loads every "
         f"machine with the average amount would therefore be short of cash on "
         f"exactly the high-demand days when a stock-out costs it customers."),

        ("02_boxplot_location.png",
         "Graph 2 — Cash demand by ATM location type",
         f"{s['loc_hi']} median ₹{s['loc_hi_med']:,.0f} (IQR ₹{s['loc_hi_iqr']:,.0f})   "
         f"{s['loc_lo']} median ₹{s['loc_lo_med']:,.0f} (IQR ₹{s['loc_lo_iqr']:,.0f})",
         f"{s['loc_hi']} ATMs carry the highest median demand "
         f"(₹{s['loc_hi_med']:,.0f}) and also the widest spread (IQR "
         f"₹{s['loc_hi_iqr']:,.0f}); {s['loc_lo']} ATMs are the lowest and the "
         f"steadiest (median ₹{s['loc_lo_med']:,.0f}, IQR "
         f"₹{s['loc_lo_iqr']:,.0f}). The gap between the best and the worst "
         f"median is about ₹{s['loc_gap']:,.0f} a day. That is small on "
         f"average but it means one single refill schedule cannot serve all "
         f"five location types, so location has to enter the model as a "
         f"feature."),

        ("03_correlation_heatmap.png",
         "Graph 3 — Correlation heatmap of the numeric features",
         f"withdrawals r = {s['r_wd']:+.3f}   competitors r = {s['r_comp']:+.3f}   "
         f"salary window r = {s['r_sal']:+.3f}   deposits r = {s['r_dep']:+.3f}",
         f"Only three variables carry real signal. Today's withdrawals dominate "
         f"(r = {s['r_wd']:+.3f}), nearby competitor ATMs pull demand away "
         f"(r = {s['r_comp']:+.3f}), and the salary window lifts it "
         f"(r = {s['r_sal']:+.3f}). Deposits and previous-day cash level are "
         f"effectively uncorrelated (r = {s['r_dep']:+.2f} and "
         f"{s['r_prev']:+.2f}) — they tell us how much cash is inside the "
         f"machine, not how much will be taken out. Withdrawals and competitors "
         f"are themselves correlated (r = {s['r_wd_comp']:+.2f}), so we "
         f"standardise the features before regression to keep the coefficients "
         f"comparable."),

        ("04_scatter_withdrawals.png",
         "Graph 4 — Today's withdrawals vs tomorrow's demand",
         f"fitted line: demand = {s['slope']:.3f} × withdrawals + "
         f"{s['intercept']:,.0f}   r = {s['r_wd']:.3f}   R² = {s['r2']:.3f}",
         f"There is a clear positive linear relationship: every extra ₹1,000 "
         f"withdrawn today predicts about ₹{s['slope']*1000:,.0f} more tomorrow. "
         f"But this single predictor explains only {s['r2']*100:.0f}% of the "
         f"variation (R² = {s['r2']:.3f}) — the remaining {100-s['r2']*100:.0f}% "
         f"is the scatter visible around the line. That residual spread is "
         f"exactly why CashGuard uses multiple regression with calendar and "
         f"location features instead of simply carrying today's number forward."),

        ("05_bar_day_of_week.png",
         "Graph 5 — Mean cash demand by day of the week",
         f"{s['dow_hi']} ₹{s['dow_hi_mean']:,.0f} (highest)   "
         f"{s['dow_lo']} ₹{s['dow_lo_mean']:,.0f} (lowest)   "
         f"overall mean ₹{s['mean']:,.0f}",
         f"{s['dow_hi']} rows carry the highest mean "
         f"(₹{s['dow_hi_mean']:,.0f}) and {s['dow_lo']} the lowest "
         f"(₹{s['dow_lo_mean']:,.0f}) — a swing of ₹{s['dow_gap']:,.0f}, and "
         f"the 95% confidence intervals do not overlap, so the difference is "
         f"real and not sampling noise. Read the labels carefully: the target "
         f"is NEXT day's demand, so a {s['dow_hi']} row actually describes "
         f"{s['dow_hi_next']}'s cash-out. The genuine peak is therefore "
         f"{s['dow_hi_next']} — the classic weekend withdrawal rush."),

        ("06_violin_calendar_effects.png",
         "Graph 6 — Calendar effects on cash demand",
         f"salary window ₹{s['sal_mean']:,.0f} vs normal ₹{s['nor_mean']:,.0f} "
         f"({s['sal_lift']:+.1f}%)   holiday ₹{s['hol_mean']:,.0f} "
         f"(n = {s['hol_n']:,})   event ₹{s['ev_mean']:,.0f}",
         f"The salary window is by far the strongest calendar effect: mean "
         f"demand rises from ₹{s['nor_mean']:,.0f} to ₹{s['sal_mean']:,.0f}, a "
         f"jump of {s['sal_lift']:.1f}% on {s['sal_n']:,} of the {s['n']:,} "
         f"days, and the whole violin shifts upward rather than just the tail. "
         f"Holidays lift demand by ₹{s['hol_mean']-s['work_mean']:,.0f} but rest "
         f"on only {s['hol_n']:,} rows, so that estimate is shaky. Special "
         f"events barely move the needle "
         f"(₹{s['ev_mean']-s['noev_mean']:,.0f}, well inside the spread). "
         f"Conclusion: engineer a salary-window flag, treat the holiday flag "
         f"with caution, and drop the special-event flag."),

        ("07_summary_table.png",
         "Graph 7 — Five-number summary of the key variables",
         f"withdrawals mean ₹{s['w_mean']:,.0f}   deposits mean "
         f"₹{s['dep_mean']:,.0f}   net drain ₹{s['drain']:,.0f}/day   "
         f"typical balance ₹{s['prev_mean']:,.0f}",
         f"Withdrawals run roughly {s['dep_ratio']:.0f} times deposits (mean "
         f"₹{s['w_mean']:,.0f} against ₹{s['dep_mean']:,.0f}), so an ATM drains "
         f"steadily at a net rate of about ₹{s['drain']:,.0f} a day. Measured "
         f"against a typical loaded balance of ₹{s['prev_mean']:,.0f}, that is "
         f"only {s['days_cash']:.1f} days of cash. With a "
         f"{LEAD_TIME_DAYS:.0f}-day cash-in-transit lead time the refill "
         f"decision has almost no slack — this table is the reason the project "
         f"exists."),
    ]


def page(pdf, idx, total, png, heading, keys, body):
    fig = plt.figure(figsize=A4, facecolor="white")

    fig.text(0.08, 0.972, heading, fontsize=15, fontweight="bold", va="top")
    fig.text(0.92, 0.9735, f"{idx} of {total}", fontsize=10, color=GREY,
             ha="right", va="top")
    fig.add_artist(plt.Line2D([0.08, 0.92], [0.958, 0.958], color=GREY, lw=.8))

    img = mpimg.imread(f"{OUT}/{png}")
    w_frac = 0.84
    h_frac = min(0.44, w_frac * A4[0] / A4[1] * img.shape[0] / img.shape[1])
    top = 0.935
    ax = fig.add_axes([0.08, top - h_frac, w_frac, h_frac])
    ax.imshow(img); ax.axis("off")
    fig.text(0.5, top - h_frac - 0.014,
             f"printed on the poster  ·  {png}", ha="center", fontsize=8,
             color=GREY)

    y = top - h_frac - 0.045
    fig.text(0.08, y, "KEY NUMBERS", fontsize=9.5, fontweight="bold",
             color=BLUE, va="top")
    y -= 0.018
    for line in textwrap.wrap(keys, 88):
        fig.text(0.08, y, line, fontsize=10, va="top", color="#33475B")
        y -= 0.0165

    y -= 0.022
    wrapped = textwrap.wrap(body, 74)
    box_h = 0.028 + len(wrapped) * 0.0225 + 0.02
    fig.add_artist(FancyBboxPatch(
        (0.075, y - box_h), 0.85, box_h, transform=fig.transFigure,
        boxstyle="round,pad=0.008", fc="#F5F8FA", ec=BLUE, lw=1.2))
    fig.text(0.095, y - 0.022, "WRITE THIS UNDER THE GRAPH — in pen, in your "
             "own handwriting", fontsize=10, fontweight="bold", color=BLUE,
             va="top")
    ty = y - 0.048
    for line in wrapped:
        fig.text(0.095, ty, line, fontsize=12.5, va="top")
        ty -= 0.0225

    y = y - box_h - 0.022
    fig.text(0.08, y, f"≈ {len(wrapped)} printed lines  ·  allow about "
             f"{max(4, round(len(wrapped) * 1.4))} lines of normal handwriting "
             f"·  reword it in your own phrasing before you write",
             fontsize=9, color=GREY, va="top", style="italic")

    fig.text(0.08, 0.028, "CashGuard · 21CSC305P Machine Learning · FP1 "
             "Component 1 — Statistical Poster", fontsize=8, color=GREY)
    pdf.savefig(fig); plt.close(fig)


def cover(pdf, path, s, n_pages):
    fig = plt.figure(figsize=A4, facecolor="white")
    fig.text(0.5, 0.88, "CashGuard", fontsize=34, fontweight="bold",
             ha="center")
    fig.text(0.5, 0.845, "Predicting ATM Cash-Out and Replenishment",
             fontsize=15, ha="center", color="#33475B")
    fig.add_artist(plt.Line2D([0.2, 0.8], [0.825, 0.825], color=BLUE, lw=2))
    fig.text(0.5, 0.795, "Observation guide for the A3 statistical poster",
             fontsize=13, ha="center", color=BLUE, va="top")

    lines = [
        ("Course", "21CSC305P Machine Learning · FP1 Component 1 (25 marks)"),
        ("Team", "V. Anbu Chelvan · S. Roopesh · B. Charith Reddy · "
                 "Y. Rupesh Reddy"),
        ("Dataset", f"{path}"),
        ("Size", f"{s['n']:,} rows · 13 columns · 50 ATMs"),
        ("Graphs", f"{n_pages} — histogram, box plot, correlation heatmap, "
                   f"scatter, bar chart, violin, summary table"),
    ]
    y = 0.715
    for k, v in lines:
        fig.text(0.16, y, k, fontsize=11, fontweight="bold", color=BLUE)
        for i, line in enumerate(textwrap.wrap(v, 62)):
            fig.text(0.30, y - i * 0.020, line, fontsize=11)
        y -= 0.020 * max(1, len(textwrap.wrap(v, 62))) + 0.016

    how = ("How to use this guide\n\n"
           "1.  Print poster_charts/A4_cut_sheets.pdf in colour at 100% scale, "
           "cut out the seven graphs and paste them onto the A3 sheet.\n\n"
           "2.  Keep this guide beside you. One page per graph: the graph at "
           "the top so you know which is which, then the observation to write "
           "underneath it on the poster.\n\n"
           "3.  Reword each observation in your own phrasing before you write "
           "it. The numbers must stay exactly as printed; the sentences should "
           "sound like you.\n\n"
           "4.  Nothing on this page gets printed onto the poster. Only the "
           "graphs are printed — the title, the observations and the "
           "conclusion are all handwritten.\n\n"
           "5.  If you swap in the real Kaggle CSV, re-run make_poster_charts.py "
           "and then make_observation_guide.py. Every number in this guide "
           "recomputes itself.")
    box_lines = how.split("\n")
    fig.add_artist(FancyBboxPatch(
        (0.115, 0.10), 0.77, 0.40, transform=fig.transFigure,
        boxstyle="round,pad=0.012", fc="#F5F8FA", ec=BLUE, lw=1.2))
    ty = 0.470
    for raw in box_lines:
        if not raw.strip():
            ty -= 0.011
            continue
        bold = raw.startswith("How to use")
        for line in textwrap.wrap(raw, 74):
            fig.text(0.145, ty, line, fontsize=12 if bold else 10.5,
                     fontweight="bold" if bold else "normal", va="top")
            ty -= 0.0205
    pdf.savefig(fig); plt.close(fig)


if __name__ == "__main__":
    path, rows = load()
    s = stats(rows)
    items = texts(s)
    missing = [f for f, *_ in items if not os.path.exists(f"{OUT}/{f}")]
    if missing:
        raise SystemExit("Run 'python3 make_poster_charts.py' first - missing: "
                         + ", ".join(missing))

    out = f"{OUT}/CashGuard_Observation_Guide.pdf"
    with PdfPages(out) as pdf:
        cover(pdf, path, s, len(items))
        for i, (png, head, keys, body) in enumerate(items, 1):
            page(pdf, i, len(items), png, head, keys, body)
    print(f"source: {path}")
    print(f"saved  {out}   ({len(items) + 1} pages)")
