"""
CashGuard - poster chart generator
==================================
Builds the printable statistical visualisations for the ML FP1 poster
(21CSC305P, Component 1).

Reads the real Kaggle file if present, otherwise the generated sample.

Out:  poster_charts/*.png   (300 dpi, one file per graph)
      poster_charts/CashGuard_Poster_Charts.pdf   (print this)
      poster_charts/real_numbers.txt (every number that appears on a chart)

Run:  python3 make_poster_charts.py
"""
import csv, os, math
from datetime import date
from collections import defaultdict

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
import numpy as np

DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data")          # the CSVs live in ../data
CANDIDATES = [os.path.join(DATA_DIR, "atm_cash_management_dataset.csv"),
              os.path.join(DATA_DIR, "atm_cash_management_dataset_sample.csv")]
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "figures")
TARGET = "Cash_Demand_Next_Day"
NUM = ["Total_Withdrawals", "Total_Deposits", "Previous_Day_Cash_Level",
       "Nearby_Competitor_ATMs", "Holiday_Flag", "Special_Event_Flag", TARGET]

INK   = "#12263A"      # dark slate for text / axes
BLUE  = "#2E6F9E"
TEAL  = "#3F9C8F"
AMBER = "#D98E32"
RED   = "#B4453C"
GREY  = "#9AA5B1"

plt.rcParams.update({
    "figure.dpi": 300, "savefig.dpi": 300,
    "font.size": 12, "axes.titlesize": 16, "axes.labelsize": 13,
    "axes.titleweight": "bold", "axes.edgecolor": INK, "axes.labelcolor": INK,
    "text.color": INK, "xtick.color": INK, "ytick.color": INK,
    "axes.spines.top": False, "axes.spines.right": False,
    "figure.facecolor": "white", "savefig.bbox": "tight",
})

log_lines = []
def log(s=""):
    print(s); log_lines.append(s)


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
        r["is_weekend"] = 1.0 if r["_date"].weekday() >= 5 else 0.0
        r["is_salary_window"] = 1.0 if (r["_date"].day <= 5 or
                                        r["_date"].day >= 25) else 0.0
    return path, rows


def pct(v, p):
    return float(np.percentile(np.asarray(v, float), p))


def money(x, _=None):
    return f"{x/1000:,.0f}k"


def finish(fig, ax_or_axes, name, title, sub):
    fig.tight_layout(rect=[0, 0, 1, 0.90])
    fig.suptitle(title, fontsize=19, fontweight="bold", color=INK, y=1.035)
    fig.text(0.5, 0.955, sub, ha="center", va="top", fontsize=11.5,
             color="#4A5A6A")
    fig.savefig(f"{OUT}/{name}.png")
    pdf.savefig(fig)
    plt.close(fig)
    log(f"  saved {OUT}/{name}.png")


# ------------------------------------------------------------------ 1. hist
def chart1(rows):
    v = np.array([r[TARGET] for r in rows])
    mean, med = v.mean(), np.median(v)
    q1, q3 = pct(v, 25), pct(v, 75)
    sd = v.std()
    skew = float(((v - mean) ** 3).mean() / sd ** 3)

    fig, ax = plt.subplots(figsize=(9, 6.2))
    n, bins, patches = ax.hist(v, bins=30, color=BLUE, edgecolor="white",
                               alpha=.88)
    ax.axvspan(q1, q3, color=TEAL, alpha=.13, zorder=0,
               label=f"IQR  {q1:,.0f} – {q3:,.0f}")
    ax.axvline(mean, color=RED, lw=2.4, label=f"Mean  ₹{mean:,.0f}")
    ax.axvline(med, color=AMBER, lw=2.4, ls="--", label=f"Median  ₹{med:,.0f}")
    ax.set_xlabel("Cash demand next day  (₹)")
    ax.set_ylabel("Number of ATM-days")
    ax.xaxis.set_major_formatter(money)
    ax.legend(frameon=False, loc="upper right")
    ax.text(.02, .96, f"n = {len(v):,}\nSD = ₹{sd:,.0f}\nSkewness = {skew:+.2f}",
            transform=ax.transAxes, va="top", fontsize=11.5,
            bbox=dict(fc="#F2F5F8", ec=GREY, boxstyle="round,pad=0.5"))
    finish(fig, ax, "01_histogram_demand",
           "1 · Distribution of Next-Day Cash Demand",
           "Histogram with mean, median and inter-quartile range")

    log(f"    mean={mean:,.0f} median={med:,.0f} sd={sd:,.0f} "
        f"Q1={q1:,.0f} Q3={q3:,.0f} IQR={q3-q1:,.0f} skew={skew:+.3f} "
        f"min={v.min():,.0f} max={v.max():,.0f}")


# --------------------------------------------------------------- 2. box plot
def chart2(rows):
    groups = defaultdict(list)
    for r in rows:
        groups[r["Location_Type"]].append(r[TARGET])
    keys = sorted(groups, key=lambda k: -np.median(groups[k]))
    data = [groups[k] for k in keys]

    fig, ax = plt.subplots(figsize=(9, 6.2))
    bp = ax.boxplot(data, tick_labels=keys, patch_artist=True, widths=.55,
                    showmeans=True,
                    meanprops=dict(marker="D", mfc=RED, mec=RED, ms=6),
                    medianprops=dict(color=INK, lw=2.2),
                    flierprops=dict(marker="o", ms=4, mfc=GREY, mec=GREY,
                                    alpha=.5))
    for p, c in zip(bp["boxes"], [BLUE, TEAL, AMBER, "#7C6BAD", "#4E8C6A"]):
        p.set(facecolor=c, alpha=.55, edgecolor=INK)
    ax.set_ylabel("Cash demand next day  (₹)")
    ax.set_xlabel("ATM location type")
    ax.yaxis.set_major_formatter(money)
    ax.grid(axis="y", ls=":", color=GREY, alpha=.6)
    ax.plot([], [], "D", color=RED, label="mean")
    ax.legend(frameon=False, loc="upper right")
    finish(fig, ax, "02_boxplot_location",
           "2 · Cash Demand by ATM Location Type",
           "Box plot — median, quartiles, whiskers and outliers")

    for k in keys:
        g = np.array(groups[k])
        log(f"    {k:<14} n={len(g):>5,}  Q1={pct(g,25):>8,.0f}  "
            f"med={np.median(g):>8,.0f}  Q3={pct(g,75):>8,.0f}  "
            f"IQR={pct(g,75)-pct(g,25):>8,.0f}  mean={g.mean():>8,.0f}")


# ---------------------------------------------------------------- 3. heatmap
def chart3(rows):
    cols = ["Total_Withdrawals", "Total_Deposits", "Previous_Day_Cash_Level",
            "Nearby_Competitor_ATMs", "Holiday_Flag", "Special_Event_Flag",
            "is_weekend", "is_salary_window", TARGET]
    short = ["Withdrawals", "Deposits", "Prev. cash", "Competitors",
             "Holiday", "Sp. event", "Weekend", "Salary win.", "DEMAND(next)"]
    M = np.array([[r[c] for c in cols] for r in rows], float)
    C = np.corrcoef(M, rowvar=False)

    fig, ax = plt.subplots(figsize=(9.2, 7.6))
    im = ax.imshow(C, cmap="RdBu_r", vmin=-1, vmax=1)
    ax.set_xticks(range(len(short)), short, rotation=45, ha="right")
    ax.set_yticks(range(len(short)), short)
    for i in range(len(short)):
        for j in range(len(short)):
            ax.text(j, i, f"{C[i,j]:.2f}", ha="center", va="center",
                    fontsize=9.5,
                    color="white" if abs(C[i, j]) > .55 else INK)
    fig.colorbar(im, ax=ax, shrink=.82, label="Pearson r")
    finish(fig, ax, "03_correlation_heatmap",
           "3 · Correlation Heatmap of Numeric Features",
           "Pearson correlation coefficient between every pair of variables")

    tgt = C[-1][:-1]
    order = np.argsort(-np.abs(tgt))
    for i in order:
        log(f"    r({short[i]}, demand) = {tgt[i]:+.3f}")


# ---------------------------------------------------------------- 4. scatter
def chart4(rows):
    x = np.array([r["Total_Withdrawals"] for r in rows])
    y = np.array([r[TARGET] for r in rows])
    m, b = np.polyfit(x, y, 1)
    r = float(np.corrcoef(x, y)[0, 1])

    fig, ax = plt.subplots(figsize=(9, 6.2))
    ax.scatter(x, y, s=9, alpha=.28, color=BLUE, edgecolors="none")
    xs = np.linspace(x.min(), x.max(), 100)
    ax.plot(xs, m * xs + b, color=RED, lw=2.6,
            label=f"y = {m:.2f}x + {b:,.0f}")
    ax.set_xlabel("Today's total withdrawals  (₹)")
    ax.set_ylabel("Next day's cash demand  (₹)")
    ax.xaxis.set_major_formatter(money)
    ax.yaxis.set_major_formatter(money)
    ax.legend(frameon=False, loc="upper left")
    ax.text(.98, .04, f"r = {r:.3f}\nR² = {r**2:.3f}\nn = {len(x):,}",
            transform=ax.transAxes, ha="right", fontsize=12,
            bbox=dict(fc="#F2F5F8", ec=GREY, boxstyle="round,pad=0.5"))
    ax.grid(ls=":", color=GREY, alpha=.5)
    finish(fig, ax, "04_scatter_withdrawals",
           "4 · Today's Withdrawals vs Tomorrow's Demand",
           "Scatter plot with least-squares regression line")

    log(f"    slope={m:.4f} intercept={b:,.0f} r={r:.4f} R2={r**2:.4f}")


# ------------------------------------------------------------- 5. weekday bar
def chart5(rows):
    order = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday",
             "Saturday", "Sunday"]
    g = defaultdict(list)
    for r in rows:
        g[r["Day_of_Week"]].append(r[TARGET])
    means = [np.mean(g[d]) for d in order]
    errs = [1.96 * np.std(g[d]) / math.sqrt(len(g[d])) for d in order]
    grand = np.mean([r[TARGET] for r in rows])

    fig, ax = plt.subplots(figsize=(9.4, 6.2))
    cols = [BLUE] * 5 + [AMBER] * 2
    bars = ax.bar(order, means, yerr=errs, capsize=5, color=cols, alpha=.9,
                  edgecolor=INK, lw=.6)
    ax.axhline(grand, color=RED, ls="--", lw=2,
               label=f"overall mean ₹{grand:,.0f}")
    for bar, mv, e in zip(bars, means, errs):
        ax.text(bar.get_x() + bar.get_width() / 2, mv + e + 900, f"{mv:,.0f}",
                ha="center", fontsize=10.5)
    ax.set_ylabel("Mean next-day cash demand  (₹)")
    ax.set_ylim(0, max(means) * 1.18)
    ax.yaxis.set_major_formatter(money)
    ax.legend(frameon=False, loc="lower right")
    ax.grid(axis="y", ls=":", color=GREY, alpha=.6)
    finish(fig, ax, "05_bar_day_of_week",
           "5 · Mean Cash Demand by Day of the Week",
           "Bar chart with 95% confidence intervals (weekend bars in amber)")

    for d, mv, e in zip(order, means, errs):
        log(f"    {d:<10} n={len(g[d]):>5,}  mean={mv:>9,.0f}  ±{e:,.0f}")


# --------------------------------------------------- 6. salary / event effect
def chart6(rows):
    pairs = [("Normal days", [r[TARGET] for r in rows
                              if not r["is_salary_window"]]),
             ("Salary window\n(1–5 & 25–31)", [r[TARGET] for r in rows
                                               if r["is_salary_window"]]),
             ("No event", [r[TARGET] for r in rows
                           if not r["Special_Event_Flag"]]),
             ("Special event", [r[TARGET] for r in rows
                                if r["Special_Event_Flag"]]),
             ("Working day", [r[TARGET] for r in rows
                              if not r["Holiday_Flag"]]),
             ("Holiday", [r[TARGET] for r in rows if r["Holiday_Flag"]])]
    labels = [p[0] for p in pairs]
    data = [p[1] for p in pairs]

    fig, ax = plt.subplots(figsize=(10, 6.2))
    parts = ax.violinplot(data, showmeans=True, showextrema=False, widths=.8)
    for i, b in enumerate(parts["bodies"]):
        b.set_facecolor([GREY, TEAL, GREY, AMBER, GREY, RED][i])
        b.set_alpha(.6); b.set_edgecolor(INK)
    parts["cmeans"].set_color(INK); parts["cmeans"].set_linewidth(2)
    bp = ax.boxplot(data, widths=.12, patch_artist=True, showfliers=False,
                    medianprops=dict(color="white", lw=1.6),
                    boxprops=dict(facecolor=INK, ec=INK))
    ax.set_xticks(range(1, len(labels) + 1), labels, fontsize=10.5)
    ax.set_ylabel("Cash demand next day  (₹)")
    ax.yaxis.set_major_formatter(money)
    ax.grid(axis="y", ls=":", color=GREY, alpha=.6)
    top = max(max(x) for x in data)
    ax.set_ylim(top=top * 1.14)
    for i, d in enumerate(data, 1):
        ax.text(i, top * 1.07, f"n={len(d):,}", ha="center", fontsize=9.5,
                color="#4A5A6A")
    finish(fig, ax, "06_violin_calendar_effects",
           "6 · Calendar Effects on Cash Demand",
           "Violin + box plots — salary window, special events and holidays")

    for name, d in pairs:
        d = np.array(d)
        log(f"    {name.replace(chr(10),' '):<28} n={len(d):>5,}  "
            f"mean={d.mean():>9,.0f}  med={np.median(d):>9,.0f}")


# ------------------------------------------------------- 7. summary stat card
def chart7(rows):
    cols = [("Total_Withdrawals", "Total withdrawals (₹)"),
            ("Total_Deposits", "Total deposits (₹)"),
            ("Previous_Day_Cash_Level", "Previous day cash level (₹)"),
            (TARGET, "Cash demand next day (₹)")]
    head = ["Variable", "Min", "Q1", "Median", "Mean", "Q3", "P90", "Max",
            "SD"]
    body = []
    for key, label in cols:
        v = np.array([r[key] for r in rows])
        body.append([label] + [f"{x:,.0f}" for x in
                               [v.min(), pct(v, 25), np.median(v), v.mean(),
                                pct(v, 75), pct(v, 90), v.max(), v.std()]])

    fig, ax = plt.subplots(figsize=(12.5, 3.0))
    ax.axis("off")
    widths = [0.26] + [0.0925] * (len(head) - 1)
    t = ax.table(cellText=body, colLabels=head, loc="center",
                 cellLoc="right", colLoc="center", colWidths=widths)
    t.auto_set_font_size(False); t.set_fontsize(11); t.scale(1, 2.1)
    for (r_, c_), cell in t.get_celld().items():
        cell.set_edgecolor(GREY)
        if r_ == 0:
            cell.set_facecolor(INK); cell.set_text_props(color="white",
                                                         weight="bold")
        elif r_ % 2 == 0:
            cell.set_facecolor("#F2F5F8")
        if c_ == 0:
            cell.set_text_props(ha="left", weight="bold")
    finish(fig, ax, "07_summary_table",
           "Five-Number Summary of the Key Variables",
           "Minimum · quartiles · median · mean · 90th percentile · maximum "
           "· standard deviation")


def cut_sheets():
    """Lay the finished PNGs onto A4 pages at the exact size they should be
    pasted onto the A3 poster: 125 mm wide, two graphs per page."""
    import matplotlib.image as mpimg
    A4 = (8.27, 11.69)                     # inches
    W = 125 / 25.4                         # 125 mm printed width
    files = sorted(f for f in os.listdir(OUT) if f.endswith(".png"))
    pdf2 = PdfPages(f"{OUT}/A4_cut_sheets.pdf")
    slots, page = [], None
    for i, f in enumerate(files):
        if i % 2 == 0:
            page = plt.figure(figsize=A4, facecolor="white")
        img = mpimg.imread(f"{OUT}/{f}")
        h_in = W * img.shape[0] / img.shape[1]
        y = 0.955 - (i % 2) * 0.485 - h_in / A4[1]
        ax = page.add_axes([(A4[0] - W) / 2 / A4[0], y, W / A4[0],
                            h_in / A4[1]])
        ax.imshow(img); ax.axis("off")
        for sp in ("top", "bottom", "left", "right"):
            ax.spines[sp].set_visible(True)
            ax.spines[sp].set_color("#C8D0D8")
            ax.spines[sp].set_linestyle((0, (4, 4)))
        ax.set_axis_on(); ax.set_xticks([]); ax.set_yticks([])
        page.text(0.5, y - 0.018, "cut along the dashed border  ·  "
                  f"{f}", ha="center", fontsize=7, color="#9AA5B1")
        if i % 2 == 1 or i == len(files) - 1:
            pdf2.savefig(page); plt.close(page)
    pdf2.close()
    log(f"  saved {OUT}/A4_cut_sheets.pdf  "
        f"({len(files)} graphs, 125 mm wide each)")


if __name__ == "__main__":
    os.makedirs(OUT, exist_ok=True)
    path, rows = load()
    log(f"CashGuard poster charts — source file: {path}")
    log(f"rows: {len(rows):,}   ATMs: {len(set(r['ATM_ID'] for r in rows))}   "
        f"period: {min(r['_date'] for r in rows)} to "
        f"{max(r['_date'] for r in rows)}")
    log()

    pdf = PdfPages(f"{OUT}/CashGuard_Poster_Charts.pdf")
    for fn in (chart1, chart2, chart3, chart4, chart5, chart6, chart7):
        fn(rows)
        log()
    pdf.close()
    log(f"  saved {OUT}/CashGuard_Poster_Charts.pdf")
    cut_sheets()

    open(f"{OUT}/real_numbers.txt", "w").write("\n".join(log_lines) + "\n")
