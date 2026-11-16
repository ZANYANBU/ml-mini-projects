#!/usr/bin/env python3
"""CashGuard - Project Review 1 deck generator (stdlib only -> real .pptx)."""
import zipfile, os

# ---------------------------------------------------------------- statistics
# Real published distributions from the Kaggle data card (5,658 records).
N = 5658
HIST = {
    "Total_Withdrawals": [
        (1380, 12021, 37), (12021, 22662, 165), (22662, 33303, 557),
        (33303, 43944, 1204), (43944, 54585, 1575), (54585, 65226, 1234),
        (65226, 75867, 673), (75867, 86508, 182), (86508, 97149, 29),
        (97149, 107790, 2)],
    "Total_Deposits": [
        (0, 3239.5, 469), (3239.5, 6479, 859), (6479, 9718.5, 1343),
        (9718.5, 12958, 1406), (12958, 16197.5, 972), (16197.5, 19437, 430),
        (19437, 22676.5, 149), (22676.5, 25916, 26), (25916, 29155.5, 3),
        (29155.5, 32395, 1)],
    "Previous_Day_Cash_Level": [
        (23266, 38162.1, 8), (38162.1, 53058.2, 50), (53058.2, 67954.3, 222),
        (67954.3, 82850.4, 801), (82850.4, 97746.5, 1476),
        (97746.5, 112642.6, 1552), (112642.6, 127538.7, 1047),
        (127538.7, 142434.8, 405), (142434.8, 157330.9, 85),
        (157330.9, 172227, 12)],
}

def stats(bins):
    tot = sum(c for *_, c in bins)
    mids = [((lo + hi) / 2.0, c) for lo, hi, c in bins]
    mean = sum(m * c for m, c in mids) / tot
    m2 = sum(c * (m - mean) ** 2 for m, c in mids) / tot
    m3 = sum(c * (m - mean) ** 3 for m, c in mids) / tot
    sd = m2 ** 0.5
    skew = m3 / (sd ** 3) if sd else 0.0
    # median by linear interpolation inside the containing bin
    half, run = tot / 2.0, 0
    med = None
    for lo, hi, c in bins:
        if run + c >= half:
            med = lo + (half - run) / c * (hi - lo)
            break
        run += c
    return dict(n=tot, lo=bins[0][0], hi=bins[-1][1], mean=mean,
                med=med, sd=sd, skew=skew, cv=sd / mean * 100)

S = {k: stats(v) for k, v in HIST.items()}

def f0(x):  return f"{x:,.0f}"
def f2(x):  return f"{x:,.2f}"

# ---------------------------------------------------------------- palette
INK, NAVY, TEAL, AMBER, RED = "0B1F3A", "17406E", "00B3A4", "F5A524", "E5484D"
GREY, LIGHT, WHITE, PANEL = "5A6B85", "EEF3F9", "FFFFFF", "F7FAFD"
W, H = 12192000, 6858000          # 16:9 slide, EMU
def IN(v): return int(v * 914400)

_id = [1]
def nid():
    _id[0] += 1
    return _id[0]

def esc(t):
    return (t.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;"))

def run(t, sz=1400, b=0, col=INK, i=0, font="Calibri"):
    return (f'<a:r><a:rPr lang="en-US" sz="{sz}" b="{b}" i="{i}" dirty="0">'
            f'<a:solidFill><a:srgbClr val="{col}"/></a:solidFill>'
            f'<a:latin typeface="{font}"/></a:rPr>'
            f'<a:t>{esc(t)}</a:t></a:r>')

def mline(text, sz=800, col=None, b=0):
    """Multi-line label: real <a:br/> breaks, not literal newlines."""
    col = col or GREY
    out = []
    for i, part in enumerate(text.split("\n")):
        if i:
            out.append("<a:br/>")
        out.append(run(part, sz, b, col))
    return out

def para(runs, align="l", space=0, bullet=None, indent=0):
    mar = f' marL="{IN(indent)}" indent="{IN(-0.18) if bullet else 0}"' if bullet or indent else ''
    bu = ('<a:buFont typeface="Arial"/><a:buChar char="▪"/>' if bullet == "sq"
          else '<a:buFont typeface="Arial"/><a:buChar char="•"/>' if bullet
          else '<a:buNone/>')
    sp = f'<a:spcBef><a:spcPts val="{space}"/></a:spcBef>' if space else ''
    return (f'<a:p><a:pPr{mar} algn="{align}">{sp}{bu}</a:pPr>'
            f'{"".join(runs)}</a:p>')

def box(x, y, w, h, paras, fill=None, line=None, lw=12700, anchor="t",
        ins=(0.10, 0.06), rot=None, shape="rect"):
    f = (f'<a:solidFill><a:srgbClr val="{fill}"/></a:solidFill>' if fill
         else '<a:noFill/>')
    l = (f'<a:ln w="{lw}"><a:solidFill><a:srgbClr val="{line}"/></a:solidFill></a:ln>'
         if line else '<a:ln><a:noFill/></a:ln>')
    r = f' rot="{rot}"' if rot else ''
    return (f'<p:sp><p:nvSpPr><p:cNvPr id="{nid()}" name="s{_id[0]}"/>'
            f'<p:cNvSpPr/><p:nvPr/></p:nvSpPr>'
            f'<p:spPr><a:xfrm{r}><a:off x="{IN(x)}" y="{IN(y)}"/>'
            f'<a:ext cx="{IN(w)}" cy="{IN(h)}"/></a:xfrm>'
            f'<a:prstGeom prst="{shape}"><a:avLst/></a:prstGeom>{f}{l}</p:spPr>'
            f'<p:txBody><a:bodyPr wrap="square" anchor="{anchor}" '
            f'lIns="{IN(ins[0])}" rIns="{IN(ins[0])}" '
            f'tIns="{IN(ins[1])}" bIns="{IN(ins[1])}"><a:normAutofit/></a:bodyPr>'
            f'<a:lstStyle/>{"".join(paras) or "<a:p/>"}</p:txBody></p:sp>')

def tbl(x, y, w, rows, colw, hdr_fill=NAVY, sz=1050, rh=0.30, hrh=0.34):
    """rows[0] = header. cells are plain strings."""
    grid = "".join(f'<a:gridCol w="{IN(c)}"/>' for c in colw)
    out = []
    for ri, r in enumerate(rows):
        cells = []
        for ci, c in enumerate(r):
            head = ri == 0
            fill = hdr_fill if head else (PANEL if ri % 2 else WHITE)
            col = WHITE if head else INK
            al = "l" if ci == 0 else "ctr"
            cells.append(
                f'<a:tc><a:txBody><a:bodyPr/><a:lstStyle/>'
                f'{para([run(c, sz, 1 if head else 0, col)], al)}'
                f'</a:txBody><a:tcPr marL="{IN(0.07)}" marR="{IN(0.07)}" '
                f'marT="{IN(0.03)}" marB="{IN(0.03)}" anchor="ctr">'
                f'<a:lnB w="6350"><a:solidFill><a:srgbClr val="D5DEEA"/>'
                f'</a:solidFill></a:lnB>'
                f'<a:solidFill><a:srgbClr val="{fill}"/></a:solidFill></a:tcPr></a:tc>')
        out.append(f'<a:tr h="{IN(hrh if ri == 0 else rh)}">{"".join(cells)}</a:tr>')
    return (f'<p:graphicFrame><p:nvGraphicFramePr>'
            f'<p:cNvPr id="{nid()}" name="t{_id[0]}"/><p:cNvGraphicFramePr/>'
            f'<p:nvPr/></p:nvGraphicFramePr>'
            f'<p:xfrm><a:off x="{IN(x)}" y="{IN(y)}"/>'
            f'<a:ext cx="{IN(w)}" cy="{IN(hrh + rh * (len(rows) - 1))}"/></p:xfrm>'
            f'<a:graphic><a:graphicData uri="http://schemas.openxmlformats.org/'
            f'drawingml/2006/table"><a:tbl><a:tblPr/><a:tblGrid>{grid}'
            f'</a:tblGrid>{"".join(out)}</a:tbl></a:graphicData></a:graphic>'
            f'</p:graphicFrame>')

# ------------------------------------------------------------ slide chrome
def chrome(num, title, kicker):
    s = [box(0, 0, 13.333, 0.90, [], fill=INK),
         box(0, 0.90, 13.333, 0.045, [], fill=TEAL),
         box(0.45, 0.10, 9.6, 0.34,
             [para([run(kicker.upper(), 900, 1, TEAL)])]),
         box(0.45, 0.38, 11.0, 0.48,
             [para([run(title, 2000, 1, WHITE)])]),
         box(11.55, 0.20, 1.4, 0.45,
             [para([run(f"{num} / 10", 1100, 1, "8FA6C4")], "r")]),
         box(0.45, 6.98, 8.0, 0.32,
             [para([run("CashGuard  ·  PS #21  ·  Project Review 1  ·  11.08.2026",
                        850, 0, "93A3B8")])])]
    return s

def bars(x, y, w, h, labels, vals, col=TEAL, fmt=f0, sz=800, hi=None):
    """Horizontal-baseline column chart from plain rectangles."""
    out = [box(x, y + h, w, 0.02, [], fill="C9D5E4")]
    mx = max(vals) or 1
    n = len(vals)
    slot = w / n
    bw = slot * 0.62
    for i, (lb, v) in enumerate(zip(labels, vals)):
        bh = (v / mx) * h
        cx = x + i * slot + (slot - bw) / 2
        c = AMBER if (hi and i in hi) else col
        out.append(box(cx, y + h - bh, bw, max(bh, 0.015), [], fill=c))
        out.append(box(x + i * slot, y + h - bh - 0.26, slot, 0.24,
                       [para([run(fmt(v), sz, 1, INK)], "ctr")]))
        out.append(box(x + i * slot, y + h + 0.05, slot, 0.50,
                       [para(mline(lb, sz), "ctr")]))
    return out

def tile(x, y, w, h, big, cap, col=TEAL):
    return [box(x, y, w, h, [], fill=WHITE, line="D9E2EE"),
            box(x, y, 0.05, h, [], fill=col),
            box(x + 0.16, y + 0.14, w - 0.3, 0.55,
                [para([run(big, 2400, 1, INK)])]),
            box(x + 0.16, y + 0.70, w - 0.3, 0.6,
                [para([run(cap, 950, 0, GREY)])])]

# ------------------------------------------------------------------ slides
SL = []

# 1 ---- title
SL.append([
    box(0, 0, 13.333, 7.5, [], fill=INK),
    box(0, 0, 13.333, 0.14, [], fill=TEAL),
    box(8.55, 1.05, 4.3, 5.4, [], fill="112C4E"),
    box(0.85, 1.30, 7.6, 0.42,
        [para([run("PROBLEM STATEMENT #21  ·  PROJECT REVIEW 1", 1100, 1, TEAL)])]),
    box(0.85, 1.80, 7.7, 1.5,
        [para([run("CashGuard", 5400, 1, WHITE)])]),
    box(0.85, 3.20, 7.5, 1.0,
        [para([run("Predicting ATM cash-out and optimising "
                   "cash replenishment with machine learning", 1700, 0, "C7D6E8")])]),
    box(0.85, 4.35, 0.9, 0.045, [], fill=TEAL),
    box(0.85, 4.60, 7.6, 0.35,
        [para([run("TEAM", 900, 1, TEAL)])]),
    box(0.85, 4.92, 7.6, 1.15, [
        para([run("V. Anbu Chelvan", 1300, 1, WHITE),
              run("   (Team Lead)", 1150, 0, "9DB2CC")]),
        para([run("S. Roopesh", 1300, 0, WHITE)], space=200),
        para([run("B. Charith Reddy", 1300, 0, WHITE)], space=200),
        para([run("Y. Rupesh Reddy", 1300, 0, WHITE)], space=200)]),
    box(8.85, 1.45, 3.7, 0.4,
        [para([run("REVIEW 1 SCOPE", 900, 1, TEAL)])]),
    box(8.85, 1.90, 3.7, 2.2, [
        para([run("Understanding the problem", 1250, 1, WHITE)]),
        para([run("statement — 2.5 marks", 1250, 1, WHITE)]),
        para([run("Statistical analysis of the", 1250, 1, WHITE)], space=600),
        para([run("dataset — 2.5 marks", 1250, 1, WHITE)])]),
    box(8.85, 4.35, 3.7, 0.045, [], fill="2A4A73"),
    box(8.85, 4.60, 3.7, 1.5, [
        para([run("Dataset", 950, 1, TEAL)]),
        para([run("Kaggle · zoya77", 1100, 0, WHITE)], space=150),
        para([run("ATM Cash Demand Forecasting", 1050, 0, "C7D6E8")], space=150),
        para([run("5,658 records · 13 columns · CC0", 1050, 0, "C7D6E8")], space=150)]),
    box(0.85, 6.55, 11.6, 0.4,
        [para([run("Date of review: 11.08.2026", 1000, 0, "7E93AD")])]),
])

# 2 ---- problem statement
SL.append(chrome(2, "The Problem", "Understanding the problem statement") + [
    box(0.45, 1.20, 12.45, 1.25, [], fill=LIGHT, line="D9E2EE"),
    box(0.45, 1.20, 0.06, 1.25, [], fill=TEAL),
    box(0.70, 1.34, 12.0, 1.0, [
        para([run("“Develop an ML model that predicts when an ATM will run out of cash "
                  "and require replenishment.", 1350, 1, INK)]),
        para([run("The model can use withdrawal patterns, ATM location, weekends, holidays, "
                  "salary periods, and historical cash withdrawal data.”", 1350, 1, INK)])]),

    box(0.45, 2.70, 6.05, 0.42,
        [para([run("WHY IT MATTERS — THE TWO-SIDED COST", 950, 1, NAVY)])]),
    box(0.45, 3.12, 2.9, 1.55, [], fill=WHITE, line="F2C9CA"),
    box(0.45, 3.12, 2.9, 0.05, [], fill=RED),
    box(0.62, 3.28, 2.6, 1.3, [
        para([run("Too little cash", 1250, 1, RED)]),
        para([run("Stock-out. Customer is turned away, "
                  "trust and fee income are lost, and an "
                  "emergency van is dispatched.", 1000, 0, GREY)], space=200)]),
    box(3.60, 3.12, 2.9, 1.55, [], fill=WHITE, line="F7DFB4"),
    box(3.60, 3.12, 2.9, 0.05, [], fill=AMBER),
    box(3.77, 3.28, 2.6, 1.3, [
        para([run("Too much cash", 1250, 1, "B4761A")]),
        para([run("Idle currency earns nothing, raises "
                  "insurance and audit cost, and inflates "
                  "cash-in-transit trips.", 1000, 0, GREY)], space=200)]),
    box(0.45, 4.85, 6.05, 1.05, [], fill=INK),
    box(0.65, 4.98, 5.7, 0.85, [
        para([run("Our goal", 1000, 1, TEAL)]),
        para([run("Forecast tomorrow's demand accurately enough to "
                  "refill just before the machine empties — not sooner.",
                  1150, 0, WHITE)], space=150)]),

    box(6.85, 2.70, 6.05, 0.42,
        [para([run("WHAT THE STATEMENT ASKS US TO USE", 950, 1, NAVY)])]),
    box(6.85, 3.12, 6.05, 2.78, [], fill=PANEL, line="D9E2EE"),
    box(7.05, 3.24, 5.7, 2.6, [
        para([run("Withdrawal patterns", 1150, 1, INK),
              run("  — per-ATM history and volatility", 1100, 0, GREY)], bullet="sq", indent=0.22),
        para([run("ATM location", 1150, 1, INK),
              run("  — mall, bank, gas station, etc.", 1100, 0, GREY)], bullet="sq", indent=0.22, space=350),
        para([run("Weekends", 1150, 1, INK),
              run("  — day-of-week seasonality", 1100, 0, GREY)], bullet="sq", indent=0.22, space=350),
        para([run("Holidays", 1150, 1, INK),
              run("  — festival and public-holiday spikes", 1100, 0, GREY)], bullet="sq", indent=0.22, space=350),
        para([run("Salary periods", 1150, 1, INK),
              run("  — month-start / month-end surge", 1100, 0, GREY)], bullet="sq", indent=0.22, space=350),
        para([run("Historical cash data", 1150, 1, INK),
              run("  — lagged demand and balance", 1100, 0, GREY)], bullet="sq", indent=0.22, space=350)]),
])

# 3 ---- how we read it / objectives
SL.append(chrome(3, "How We Interpret It", "Problem framing · Objectives") + [
    box(0.45, 1.15, 12.45, 0.40,
        [para([run("A “run-out” date is not a column in any dataset — it is a "
                   "quantity we must derive. We therefore split the statement into a "
                   "forecast step and a decision step.", 1200, 0, GREY)])]),
    # pipeline
    box(0.45, 1.70, 3.85, 1.5, [], fill=WHITE, line="D9E2EE"),
    box(0.45, 1.70, 3.85, 0.05, [], fill=TEAL),
    box(0.62, 1.86, 3.5, 1.25, [
        para([run("STEP 1 · FORECAST", 900, 1, TEAL)]),
        para([run("Predict cash demand for the next day", 1250, 1, INK)], space=150),
        para([run("Supervised regression on "
                  "Cash_Demand_Next_Day", 1000, 0, GREY)], space=150)]),
    box(4.55, 2.25, 0.55, 0.4, [para([run("→", 1800, 1, "B9C7D8")], "ctr")]),
    box(5.20, 1.70, 3.85, 1.5, [], fill=WHITE, line="D9E2EE"),
    box(5.20, 1.70, 3.85, 0.05, [], fill=AMBER),
    box(5.37, 1.86, 3.5, 1.25, [
        para([run("STEP 2 · DEPLETION", 900, 1, "B4761A")]),
        para([run("Convert demand into days-to-empty", 1250, 1, INK)], space=150),
        para([run("Balance ÷ predicted daily demand, "
                  "rolled forward day by day", 1000, 0, GREY)], space=150)]),
    box(9.30, 2.25, 0.55, 0.4, [para([run("→", 1800, 1, "B9C7D8")], "ctr")]),
    box(9.95, 1.70, 2.95, 1.5, [], fill=INK),
    box(10.12, 1.86, 2.6, 1.25, [
        para([run("STEP 3 · ACTION", 900, 1, TEAL)]),
        para([run("Refill alert", 1250, 1, WHITE)], space=150),
        para([run("Flag an ATM when days-to-empty "
                  "falls below the service lead time", 1000, 0, "AFC2D8")], space=150)]),

    box(0.45, 3.45, 5.9, 0.42,
        [para([run("OBJECTIVES", 950, 1, NAVY)])]),
    box(0.45, 3.85, 5.9, 2.9, [], fill=PANEL, line="D9E2EE"),
    box(0.62, 3.98, 5.55, 2.7, [
        para([run("O1  ", 1150, 1, TEAL), run("Analyse and clean the ATM dataset; "
              "establish baseline statistics.", 1150, 0, INK)]),
        para([run("O2  ", 1150, 1, TEAL), run("Engineer the drivers named in the "
              "statement — weekend, holiday, salary window, lags.", 1150, 0, INK)], space=300),
        para([run("O3  ", 1150, 1, TEAL), run("Build a mathematical model and code it "
              "in Python from first principles.", 1150, 0, INK)], space=300),
        para([run("O4  ", 1150, 1, TEAL), run("Compare against standard regression and "
              "ensemble algorithms.", 1150, 0, INK)], space=300),
        para([run("O5  ", 1150, 1, TEAL), run("Convert the forecast into a "
              "replenishment schedule and quantify cash saved.", 1150, 0, INK)], space=300)]),

    box(6.65, 3.45, 6.25, 0.42,
        [para([run("SCOPE OF THIS REVIEW", 950, 1, NAVY)])]),
    box(6.65, 3.85, 6.25, 2.9, [], fill=WHITE, line="D9E2EE"),
    box(6.85, 3.98, 5.9, 2.7, [
        para([run("In scope today", 1150, 1, INK)]),
        para([run("Problem definition, dataset selection, data dictionary, "
                  "univariate and categorical statistics, data-quality findings.",
                  1100, 0, GREY)], space=150),
        para([run("Deferred to Review 2  (10.09.2026)", 1150, 1, INK)], space=400),
        para([run("Mathematical formulation of the model and the Python script "
                  "written without ML libraries.", 1100, 0, GREY)], space=150),
        para([run("Deferred to Review 3  (04.11.2026)", 1150, 1, INK)], space=400),
        para([run("Live demo and comparative analysis against Unit 4–5 algorithms, "
                  "with the GitHub link submitted for plagiarism check.",
                  1100, 0, GREY)], space=150)]),
])

# 4 ---- dataset overview
SL.append(chrome(4, "The Dataset", "Statistical analysis · Overview") + [
    box(0.45, 1.15, 12.45, 0.42, [
        para([run("ATM Cash Demand Forecasting and Management", 1300, 1, INK),
              run("   ·   Kaggle, author zoya77   ·   "
                  "atm_cash_management_dataset.csv", 1150, 0, GREY)])]),
    ] + tile(0.45, 1.70, 3.0, 1.35, "5,658", "records (rows)") \
      + tile(3.62, 1.70, 3.0, 1.35, "13", "columns", AMBER) \
      + tile(6.79, 1.70, 3.0, 1.35, "50", "distinct ATMs (ATM_0001–ATM_0050)", NAVY) \
      + tile(9.96, 1.70, 2.94, 1.35, "731", "days covered", RED) + [

    box(0.45, 3.30, 6.05, 0.42, [para([run("PROVENANCE", 950, 1, NAVY)])]),
    ] + [tbl(0.45, 3.72, 6.05, [
            ["Attribute", "Value"],
            ["File", "atm_cash_management_dataset.csv"],
            ["Size", "473.94 kB  (single file)"],
            ["Period covered", "2022-01-01  →  2024-01-01"],
            ["Licence", "CC0: Public Domain"],
            ["Kaggle usability", "6.47"],
            ["Task type", "Supervised regression"],
            ["Target variable", "Cash_Demand_Next_Day"]], [2.35, 3.70], rh=0.285)] + [

    box(6.85, 3.30, 6.05, 0.42, [para([run("RECORDS PER CALENDAR WINDOW", 950, 1, NAVY)])]),
    box(6.85, 3.72, 6.05, 2.35, [], fill=WHITE, line="D9E2EE"),
    ] + bars(7.10, 4.02, 5.55, 1.08,
             ["H1\n2022", "H2\n2022", "H1\n2023", "H2\n2023"],
             [1127, 1117, 1168, 1096], col=NAVY) + [
    box(7.05, 5.70, 5.7, 0.34, [
        para([run("Coverage is even across both years — no seasonal gap in "
                  "collection.", 950, 0, GREY)], "ctr")]),
    box(0.45, 6.28, 12.45, 0.45, [], fill=LIGHT),
    box(0.62, 6.33, 12.1, 0.38, [
        para([run("Read: ", 1000, 1, TEAL),
              run("a two-year, multi-ATM panel with ~113 observations per machine "
                  "— wide enough for cross-sectional learning, sparse for "
                  "per-ATM daily time series.", 1000, 0, INK)])]),
])

# 5 ---- data dictionary
DD = [
    ["#", "Column", "Type", "Role in our model"],
    ["1", "ATM_ID", "Categorical", "Entity key · per-ATM grouping"],
    ["2", "Date", "Date", "Time index · source of engineered features"],
    ["3", "Day_of_Week", "Categorical", "Weekend / weekday effect"],
    ["4", "Time_of_Day", "Categorical", "Intra-day usage pattern"],
    ["5", "Total_Withdrawals", "Numeric", "Core withdrawal pattern"],
    ["6", "Total_Deposits", "Numeric", "Cash recycled back into the machine"],
    ["7", "Location_Type", "Categorical", "ATM location driver"],
    ["8", "Holiday_Flag", "Binary 0/1", "Holiday effect"],
    ["9", "Special_Event_Flag", "Binary 0/1", "Local-event surge"],
    ["10", "Previous_Day_Cash_Level", "Numeric", "Opening balance · depletion base"],
    ["11", "Weather_Condition", "Categorical", "Footfall modifier"],
    ["12", "Nearby_Competitor_ATMs", "Numeric", "Demand diverted to rivals"],
    ["13", "Cash_Demand_Next_Day", "Numeric", "TARGET — what we predict"],
]
SL.append(chrome(5, "Data Dictionary", "Statistical analysis · Variables") + [
    box(0.45, 1.12, 8.0, 0.38, [
        para([run("All 13 columns, and how each one serves the problem statement.",
                  1150, 0, GREY)])]),
    ] + [tbl(0.45, 1.55, 8.35, DD, [0.45, 3.05, 1.55, 3.30], sz=1000, rh=0.345)] + [

    box(9.05, 1.55, 3.85, 0.42, [para([run("COVERAGE CHECK", 950, 1, NAVY)])]),
    box(9.05, 1.97, 3.85, 2.55, [], fill=PANEL, line="D9E2EE"),
    box(9.22, 2.08, 3.5, 2.4, [
        para([run("Directly available", 1050, 1, "0E7C5A")]),
        para([run("Withdrawal patterns ✓", 1000, 0, INK)], space=120),
        para([run("ATM location ✓", 1000, 0, INK)], space=100),
        para([run("Weekends ✓", 1000, 0, INK)], space=100),
        para([run("Holidays ✓", 1000, 0, INK)], space=100),
        para([run("Historical cash data ✓", 1000, 0, INK)], space=100),
        para([run("Must be engineered", 1050, 1, RED)], space=280),
        para([run("Salary periods — derived from Date "
                  "(1st–5th and 25th–last)", 1000, 0, INK)], space=120)]),
    box(9.05, 4.72, 3.85, 2.0, [], fill=INK),
    box(9.22, 4.85, 3.5, 1.8, [
        para([run("THE TARGET", 900, 1, TEAL)]),
        para([run("Cash_Demand_Next_Day", 1200, 1, WHITE)], space=180),
        para([run("A continuous rupee amount — so the core task is "
                  "regression, not classification. The “will it run out?” "
                  "answer is produced afterwards by comparing the forecast "
                  "against the cash loaded in the machine.", 950, 0, "AFC2D8")], space=180)]),
])

# 6 ---- numeric statistics
def srow(name, k):
    s = S[k]
    return [name, f0(s["lo"]), f0(s["hi"]), f0(s["mean"]), f0(s["med"]),
            f0(s["sd"]), f"{s['cv']:.1f}%", f"{s['skew']:+.2f}"]

SL.append(chrome(6, "Numeric Summary", "Statistical analysis · Univariate") + [
    box(0.45, 1.12, 12.45, 0.38, [
        para([run("Descriptive statistics for the three numeric predictors, "
                  "computed over all 5,658 records.", 1150, 0, GREY)])]),
    ] + [tbl(0.45, 1.55, 12.45, [
            ["Variable", "Min", "Max", "Mean", "Median", "Std dev", "CV", "Skew"],
            srow("Total_Withdrawals", "Total_Withdrawals"),
            srow("Total_Deposits", "Total_Deposits"),
            srow("Previous_Day_Cash_Level", "Previous_Day_Cash_Level")],
            [3.35, 1.20, 1.30, 1.30, 1.30, 1.30, 1.15, 1.55], sz=1050, rh=0.44)] + [

    box(0.45, 3.35, 4.0, 0.42, [para([run("WHAT THE NUMBERS SAY", 950, 1, NAVY)])]),
    box(0.45, 3.77, 4.0, 2.95, [], fill=PANEL, line="D9E2EE"),
    box(0.62, 3.90, 3.7, 2.8, [
        para([run("Withdrawals are the volatile term.", 1100, 1, INK)]),
        para([run(f"Spread of {S['Total_Withdrawals']['cv']:.0f}% around the mean, "
                  f"and the largest day ({f0(S['Total_Withdrawals']['hi'])}) is "
                  f"{S['Total_Withdrawals']['hi']/S['Total_Withdrawals']['mean']:.1f}× "
                  f"the average. This is the variable that causes stock-outs.",
                  1000, 0, GREY)], space=120),
        para([run("Deposits are small but not negligible.", 1100, 1, INK)], space=320),
        para([run(f"Averaging {f0(S['Total_Deposits']['mean'])}, they offset roughly "
                  f"{S['Total_Deposits']['mean']/S['Total_Withdrawals']['mean']*100:.0f}% "
                  f"of gross withdrawals, so net drain — not withdrawals alone "
                  f"— drives depletion.", 1000, 0, GREY)], space=120)]),

    box(4.65, 3.35, 4.0, 0.42, [para([run("DISTRIBUTION SHAPE", 950, 1, NAVY)])]),
    box(4.65, 3.77, 4.0, 2.95, [], fill=PANEL, line="D9E2EE"),
    box(4.82, 3.90, 3.7, 2.8, [
        para([run("All three are near-symmetric.", 1100, 1, INK)]),
        para([run("Skew stays inside ±0.5 and each mean sits close to its "
                  "median, so no log transform is required before modelling.",
                  1000, 0, GREY)], space=120),
        para([run("Tails are thin but real.", 1100, 1, INK)], space=320),
        para([run("Only 31 of 5,658 withdrawal days exceed 86,508 — about "
                  "0.5%. These rare heavy days are exactly the ones a "
                  "replenishment model must not miss.", 1000, 0, GREY)], space=120)]),

    box(8.85, 3.35, 4.05, 0.42, [para([run("OPENING BALANCE vs DEMAND", 950, 1, NAVY)])]),
    box(8.85, 3.77, 4.05, 2.95, [], fill=INK),
    box(9.02, 3.90, 3.7, 2.8, [
        para([run(f"Mean cash loaded", 1000, 0, "AFC2D8")]),
        para([run(f0(S['Previous_Day_Cash_Level']['mean']), 2000, 1, WHITE)]),
        para([run("Mean daily net drain", 1000, 0, "AFC2D8")], space=250),
        para([run(f0(S['Total_Withdrawals']['mean'] - S['Total_Deposits']['mean']),
                  2000, 1, TEAL)]),
        para([run(f"≈ "
                  f"{S['Previous_Day_Cash_Level']['mean']/(S['Total_Withdrawals']['mean']-S['Total_Deposits']['mean']):.1f} "
                  f"days of autonomy on average — but only "
                  f"{S['Previous_Day_Cash_Level']['lo']/S['Total_Withdrawals']['hi']:.1f} "
                  f"days in the worst case. That gap is the risk we are modelling.",
                  1000, 0, "AFC2D8")], space=250)]),
])

# 7 ---- distributions
tw = HIST["Total_Withdrawals"]
SL.append(chrome(7, "Distributions", "Statistical analysis · Histograms") + [
    box(0.45, 1.10, 7.9, 0.40, [
        para([run("Total_Withdrawals", 1250, 1, INK),
              run("   ·   frequency across 10 equal bins", 1100, 0, GREY)])]),
    box(0.45, 1.52, 7.9, 3.05, [], fill=WHITE, line="D9E2EE"),
    ] + bars(0.70, 1.80, 7.4, 2.05,
             ["1.4k\n–12k", "12k\n–23k", "23k\n–33k", "33k\n–44k",
              "44k\n–55k", "55k\n–65k", "65k\n–76k", "76k\n–87k",
              "87k\n–97k", "97k\n–108k"],
             [c for *_, c in tw], col=TEAL, sz=750, hi={4}) + [

    box(0.45, 4.72, 7.9, 0.40, [
        para([run("Previous_Day_Cash_Level", 1250, 1, INK),
              run("   ·   opening balance held in the machine", 1100, 0, GREY)])]),
    box(0.45, 5.14, 7.9, 1.65, [], fill=WHITE, line="D9E2EE"),
    ] + bars(0.70, 5.34, 7.4, 0.95,
             ["23k", "38k", "53k", "68k", "83k", "98k", "113k", "128k", "142k", "157k"],
             [c for *_, c in HIST["Previous_Day_Cash_Level"]], col=NAVY, sz=700) + [

    box(8.60, 1.10, 4.3, 0.40, [para([run("READING THE SHAPE", 950, 1, NAVY)])]),
    box(8.60, 1.52, 4.3, 2.35, [], fill=PANEL, line="D9E2EE"),
    box(8.77, 1.64, 3.95, 2.2, [
        para([run("A single clear peak.", 1100, 1, INK)]),
        para([run(f"The 44k–55k bin holds {f0(1575)} of 5,658 days "
                  f"({1575/N*100:.0f}%). Demand is unimodal and centred — "
                  f"there is a stable “normal day” to learn from.",
                  1000, 0, GREY)], space=140),
        para([run("Both tails are thin.", 1100, 1, INK)], space=260),
        para([run("37 very quiet days at the bottom, 31 very heavy days at "
                  "the top. Rare, but they set the safety buffer.",
                  1000, 0, GREY)], space=140)]),

    box(8.60, 4.05, 4.3, 0.40, [para([run("TOTAL_DEPOSITS", 950, 1, NAVY)])]),
    box(8.60, 4.47, 4.3, 2.32, [], fill=WHITE, line="D9E2EE"),
    box(8.77, 4.60, 3.95, 2.15, [
        para([run(f"Range   ", 1000, 0, GREY),
              run(f"{f0(S['Total_Deposits']['lo'])} – "
                  f"{f0(S['Total_Deposits']['hi'])}", 1100, 1, INK)]),
        para([run(f"Mean   ", 1000, 0, GREY),
              run(f0(S['Total_Deposits']['mean']), 1100, 1, INK)], space=140),
        para([run(f"Median   ", 1000, 0, GREY),
              run(f0(S['Total_Deposits']['med']), 1100, 1, INK)], space=140),
        para([run(f"Skew   ", 1000, 0, GREY),
              run(f"{S['Total_Deposits']['skew']:+.2f}", 1100, 1, INK)], space=140),
        para([run("Mildly right-skewed: most days see modest deposits, a few "
                  "see large ones. 469 records sit in the lowest bin, "
                  "including genuine zero-deposit days.", 1000, 0, GREY)], space=200)]),
])

# 8 ---- categorical
SL.append(chrome(8, "Categorical & Temporal", "Statistical analysis · Frequencies") + [
    box(0.45, 1.10, 12.45, 0.38, [
        para([run("How the four categorical fields and the two event flags are "
                  "distributed — this decides how we encode and how we "
                  "validate.", 1150, 0, GREY)])]),

    box(0.45, 1.55, 4.0, 0.40, [para([run("DAY_OF_WEEK  ·  7 levels", 950, 1, NAVY)])]),
    box(0.45, 1.95, 4.0, 1.55, [], fill=WHITE, line="D9E2EE"),
    box(0.62, 2.06, 3.7, 1.4, [
        para([run("Monday   ", 1050, 0, GREY), run("15%", 1200, 1, INK),
              run("   most frequent", 950, 0, GREY)]),
        para([run("Friday   ", 1050, 0, GREY), run("14%", 1200, 1, INK)], space=140),
        para([run("Remaining 5 days share 71% — close to the 14.3% a "
                  "perfectly even split would give.", 950, 0, GREY)], space=180)]),

    box(4.65, 1.55, 4.0, 0.40, [para([run("TIME_OF_DAY  ·  4 levels", 950, 1, NAVY)])]),
    box(4.65, 1.95, 4.0, 1.55, [], fill=WHITE, line="D9E2EE"),
    box(4.82, 2.06, 3.7, 1.4, [
        para([run("Afternoon   ", 1050, 0, GREY), run("26%", 1200, 1, INK)]),
        para([run("Evening   ", 1050, 0, GREY), run("25%", 1200, 1, INK)], space=140),
        para([run("Morning and Night together make up the other 49% — "
                  "again near-uniform at about 25% each.", 950, 0, GREY)], space=180)]),

    box(8.85, 1.55, 4.05, 0.40, [para([run("LOCATION_TYPE  ·  5 levels", 950, 1, NAVY)])]),
    box(8.85, 1.95, 4.05, 1.55, [], fill=WHITE, line="D9E2EE"),
    box(9.02, 2.06, 3.75, 1.4, [
        para([run("Gas Station 20%  ·  Standalone 20%", 1100, 1, INK)]),
        para([run("Supermarket, Mall and Bank Branch share the remaining "
                  "60% — an even 20% each.", 950, 0, GREY)], space=180),
        para([run("Balanced by design, so location effects can be compared "
                  "without re-weighting.", 950, 0, GREY)], space=140)]),

    box(0.45, 3.70, 6.05, 0.40, [para([run("THE TWO EVENT FLAGS ARE RARE", 950, 1, NAVY)])]),
    box(0.45, 4.10, 6.05, 2.6, [], fill=WHITE, line="D9E2EE"),
    ] + bars(0.95, 4.42, 5.05, 1.20,
             ["Holiday_Flag = 1\n125 records", "Special_Event_Flag = 1\n546 records"],
             [125, 546], col=RED, sz=900) + [
    box(0.62, 6.28, 5.7, 0.34, [
        para([run("2.21%", 1100, 1, RED), run("  of days are holidays  ·  ", 1000, 0, GREY),
              run("9.65%", 1100, 1, RED), run("  carry a special event", 1000, 0, GREY)], "ctr")]),

    box(6.85, 3.70, 6.05, 0.40, [para([run("WHY THIS MATTERS FOR MODELLING", 950, 1, NAVY)])]),
    box(6.85, 4.10, 6.05, 2.6, [], fill=PANEL, line="D9E2EE"),
    box(7.05, 4.22, 5.7, 2.45, [
        para([run("Encoding is cheap.", 1100, 1, INK),
              run("  Every categorical field has ≤ 7 levels, so one-hot "
                  "encoding adds only 16 columns — no high-cardinality "
                  "problem to solve.", 1050, 0, GREY)]),
        para([run("Holidays need care.", 1100, 1, INK),
              run("  With 125 positive cases, a random split can leave a fold "
                  "with almost none. We will stratify on Holiday_Flag and report "
                  "error on holidays separately.", 1050, 0, GREY)], space=280),
        para([run("Balance is a warning too.", 1100, 1, INK),
              run("  Near-perfect uniformity confirms the data is simulated, so "
                  "we will state that limitation rather than claim real-world "
                  "generalisation.", 1050, 0, GREY)], space=280)]),
])

# 9 ---- insights & gaps
SL.append(chrome(9, "Key Findings", "Insights · Data quality · Gaps") + [
    box(0.45, 1.10, 12.45, 0.38, [
        para([run("Six conclusions from Review 1, and what each one forces us to "
                  "do next.", 1150, 0, GREY)])]),

    box(0.45, 1.52, 6.05, 0.40, [para([run("STRENGTHS OF THIS DATASET", 950, 1, "0E7C5A")])]),
    box(0.45, 1.92, 6.05, 2.35, [], fill=WHITE, line="C8E6D8"),
    box(0.62, 2.04, 5.7, 2.2, [
        para([run("Complete and clean.", 1100, 1, INK),
              run("  5,658 × 13 with no missing values reported and a usability "
                  "score of 6.47 — modelling can start immediately.",
                  1050, 0, GREY)]),
        para([run("Four of six drivers are native.", 1100, 1, INK),
              run("  Withdrawal patterns, location, weekday and holidays are "
                  "already columns; historical cash is available as "
                  "Previous_Day_Cash_Level.", 1050, 0, GREY)], space=260),
        para([run("Two useful extras.", 1100, 1, INK),
              run("  Weather_Condition and Nearby_Competitor_ATMs go beyond the "
                  "statement and may lift accuracy.", 1050, 0, GREY)], space=260)]),

    box(6.85, 1.52, 6.05, 0.40, [para([run("GAPS WE MUST CLOSE", 950, 1, RED)])]),
    box(6.85, 1.92, 6.05, 2.35, [], fill=WHITE, line="F2C9CA"),
    box(7.05, 2.04, 5.7, 2.2, [
        para([run("No salary-period column.", 1100, 1, INK),
              run("  The statement names it, the data lacks it. We will derive a "
                  "salary window from Date (1st–5th, 25th–month end).",
                  1050, 0, GREY)]),
        para([run("No run-out label.", 1100, 1, INK),
              run("  Nothing marks an empty ATM. We define depletion ourselves "
                  "from balance and predicted demand, then validate the rule.",
                  1050, 0, GREY)], space=260),
        para([run("Sparse per-ATM history.", 1100, 1, INK),
              run("  About 113 records per ATM across 731 days, so the panel is "
                  "not a continuous daily series — lag features must be built "
                  "per ATM with gaps handled explicitly.", 1050, 0, GREY)], space=260)]),

    box(0.45, 4.45, 12.45, 0.40, [para([run("DECISIONS TAKEN", 950, 1, NAVY)])]),
    box(0.45, 4.85, 4.0, 1.85, [], fill=INK),
    box(0.62, 4.98, 3.7, 1.7, [
        para([run("01", 1400, 1, TEAL)]),
        para([run("Regression first, alert second", 1150, 1, WHITE)], space=140),
        para([run("Predict Cash_Demand_Next_Day, then turn the forecast into a "
                  "days-to-empty countdown.", 1000, 0, "AFC2D8")], space=140)]),
    box(4.65, 4.85, 4.0, 1.85, [], fill=INK),
    box(4.82, 4.98, 3.7, 1.7, [
        para([run("02", 1400, 1, TEAL)]),
        para([run("Time-aware validation", 1150, 1, WHITE)], space=140),
        para([run("Train on 2022, test on 2023. A random split would let the "
                  "model see the future.", 1000, 0, "AFC2D8")], space=140)]),
    box(8.85, 4.85, 4.05, 1.85, [], fill=INK),
    box(9.02, 4.98, 3.75, 1.7, [
        para([run("03", 1400, 1, TEAL)]),
        para([run("Cost-aware error metric", 1150, 1, WHITE)], space=140),
        para([run("Under-prediction causes stock-outs, so we weight it more "
                  "heavily than over-prediction.", 1000, 0, "AFC2D8")], space=140)]),
])

# 10 ---- roadmap
SL.append(chrome(10, "Roadmap", "Next steps · Review 2 plan") + [
    box(0.45, 1.10, 12.45, 0.38, [
        para([run("What we build between now and each remaining review date.",
                  1150, 0, GREY)])]),

    box(0.45, 1.55, 12.45, 0.05, [], fill="D9E2EE"),
    ] + sum([[
    box(0.45 + i * 3.15, 1.42, 0.28, 0.28, [], fill=c, shape="ellipse"),
    box(0.45 + i * 3.15, 1.80, 2.95, 0.34,
        [para([run(d, 1050, 1, c)])]),
    box(0.45 + i * 3.15, 2.14, 2.95, 0.38,
        [para([run(t, 1250, 1, INK)])]),
    box(0.45 + i * 3.15, 2.55, 2.95, 1.05,
        [para([run(b, 1000, 0, GREY)])]),
    ] for i, (d, t, b, c) in enumerate([
        ("11.08.2026  ·  DONE", "Review 1",
         "Problem understanding and statistical analysis of the dataset — "
         "this deck.", TEAL),
        ("10.09.2026", "Review 2",
         "Mathematical model of the algorithm, then a Python script implementing "
         "it from first principles, without ML libraries.", AMBER),
        ("04.11.2026", "Review 3",
         "Working demo plus comparative analysis against the Unit 4–5 "
         "algorithms. GitHub link submitted for plagiarism check.", NAVY),
        ("11.11.2026", "Report & Viva",
         "Full project report covering statement, objectives, model, script and "
         "results — 10 marks, plus a 5-mark viva.", RED),
    ])], []) + [

    box(0.45, 3.75, 6.05, 0.40, [para([run("IMMEDIATE NEXT ACTIONS", 950, 1, NAVY)])]),
    box(0.45, 4.15, 6.05, 2.55, [], fill=PANEL, line="D9E2EE"),
    box(0.62, 4.30, 5.7, 2.35, [
        para([run("Engineer the missing drivers", 1100, 1, INK),
              run("  — is_weekend, salary window, month-end, per-ATM lag and "
                  "rolling mean.", 1050, 0, GREY)], bullet="sq", indent=0.22),
        para([run("Derive the depletion label", 1100, 1, INK),
              run("  — days-to-empty from balance and net drain.",
                  1050, 0, GREY)], bullet="sq", indent=0.22, space=200),
        para([run("Write the mathematical model", 1100, 1, INK),
              run("  — regression formulation with gradient descent derived "
                  "by hand.", 1050, 0, GREY)], bullet="sq", indent=0.22, space=200),
        para([run("Set up the GitHub repository", 1100, 1, INK),
              run("  — code, notebooks and this deck, ready for the "
                  "Review 3 submission.", 1050, 0, GREY)], bullet="sq", indent=0.22, space=200)]),

    box(6.85, 3.75, 6.05, 0.40, [para([run("HOW WE WILL JUDGE SUCCESS", 950, 1, NAVY)])]),
    box(6.85, 4.15, 6.05, 2.55, [], fill=WHITE, line="D9E2EE"),
    box(7.05, 4.30, 5.7, 2.35, [
        para([run("Forecast accuracy", 1100, 1, INK),
              run("  — MAE and RMSE on Cash_Demand_Next_Day, with "
                  "R² for fit.", 1050, 0, GREY)], bullet="sq", indent=0.22),
        para([run("Stock-out recall", 1100, 1, INK),
              run("  — share of true run-out events flagged before they "
                  "happen.", 1050, 0, GREY)], bullet="sq", indent=0.22, space=200),
        para([run("Idle cash reduction", 1100, 1, INK),
              run("  — average balance held versus the current "
                  "fixed-schedule baseline.", 1050, 0, GREY)], bullet="sq", indent=0.22, space=200),
        para([run("Trip count", 1100, 1, INK),
              run("  — replenishment visits needed per ATM per month.",
                  1050, 0, GREY)], bullet="sq", indent=0.22, space=200)]),
])

# ------------------------------------------------------------------ package
def slide_xml(shapes):
    return ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
            '<p:sld xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" '
            'xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships" '
            'xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main">'
            '<p:cSld><p:spTree><p:nvGrpSpPr><p:cNvPr id="1" name=""/>'
            '<p:cNvGrpSpPr/><p:nvPr/></p:nvGrpSpPr><p:grpSpPr><a:xfrm>'
            '<a:off x="0" y="0"/><a:ext cx="0" cy="0"/><a:chOff x="0" y="0"/>'
            '<a:chExt cx="0" cy="0"/></a:xfrm></p:grpSpPr>'
            f'{"".join(shapes)}</p:spTree></p:cSld>'
            '<p:clrMapOvr><a:masterClrMapping/></p:clrMapOvr></p:sld>')

NS_A = 'xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main"'
NS_P = 'xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main"'
NS_R = 'xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"'
REL = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
PKG = "http://schemas.openxmlformats.org/package/2006/relationships"

def theme():
    def sc(v): return f'<a:srgbClr val="{v}"/>'
    scheme = "".join(
        f'<a:{k}>{sc(v)}</a:{k}>' for k, v in
        [("dk1", "000000"), ("lt1", "FFFFFF"), ("dk2", INK), ("lt2", LIGHT),
         ("accent1", TEAL), ("accent2", NAVY), ("accent3", AMBER),
         ("accent4", RED), ("accent5", "5A9BD5"), ("accent6", "70AD47"),
         ("hlink", TEAL), ("folHlink", NAVY)])
    font = ('<a:latin typeface="Calibri"/><a:ea typeface=""/><a:cs typeface=""/>')
    fmt = ('<a:fmtScheme name="Office"><a:fillStyleLst>'
           '<a:solidFill><a:schemeClr val="phClr"/></a:solidFill>'
           '<a:solidFill><a:schemeClr val="phClr"/></a:solidFill>'
           '<a:solidFill><a:schemeClr val="phClr"/></a:solidFill>'
           '</a:fillStyleLst><a:lnStyleLst>'
           '<a:ln w="6350"><a:solidFill><a:schemeClr val="phClr"/></a:solidFill></a:ln>'
           '<a:ln w="12700"><a:solidFill><a:schemeClr val="phClr"/></a:solidFill></a:ln>'
           '<a:ln w="19050"><a:solidFill><a:schemeClr val="phClr"/></a:solidFill></a:ln>'
           '</a:lnStyleLst><a:effectStyleLst>'
           '<a:effectStyle><a:effectLst/></a:effectStyle>'
           '<a:effectStyle><a:effectLst/></a:effectStyle>'
           '<a:effectStyle><a:effectLst/></a:effectStyle>'
           '</a:effectStyleLst><a:bgFillStyleLst>'
           '<a:solidFill><a:schemeClr val="phClr"/></a:solidFill>'
           '<a:solidFill><a:schemeClr val="phClr"/></a:solidFill>'
           '<a:solidFill><a:schemeClr val="phClr"/></a:solidFill>'
           '</a:bgFillStyleLst></a:fmtScheme>')
    return ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
            f'<a:theme {NS_A} name="CashGuard"><a:themeElements>'
            f'<a:clrScheme name="CashGuard">{scheme}</a:clrScheme>'
            f'<a:fontScheme name="CashGuard"><a:majorFont>{font}</a:majorFont>'
            f'<a:minorFont>{font}</a:minorFont></a:fontScheme>{fmt}'
            '</a:themeElements></a:theme>')

def master():
    return ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
            f'<p:sldMaster {NS_A} {NS_R} {NS_P}><p:cSld><p:bg><p:bgPr>'
            '<a:solidFill><a:srgbClr val="FFFFFF"/></a:solidFill>'
            '<a:effectLst/></p:bgPr></p:bg><p:spTree><p:nvGrpSpPr>'
            '<p:cNvPr id="1" name=""/><p:cNvGrpSpPr/><p:nvPr/></p:nvGrpSpPr>'
            '<p:grpSpPr><a:xfrm><a:off x="0" y="0"/><a:ext cx="0" cy="0"/>'
            '<a:chOff x="0" y="0"/><a:chExt cx="0" cy="0"/></a:xfrm>'
            '</p:grpSpPr></p:spTree></p:cSld>'
            '<p:clrMap bg1="lt1" tx1="dk1" bg2="lt2" tx2="dk2" accent1="accent1" '
            'accent2="accent2" accent3="accent3" accent4="accent4" '
            'accent5="accent5" accent6="accent6" hlink="hlink" '
            'folHlink="folHlink"/><p:sldLayoutIdLst>'
            '<p:sldLayoutId id="2147483649" r:id="rId1"/></p:sldLayoutIdLst>'
            '</p:sldMaster>')

def layout():
    return ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
            f'<p:sldLayout {NS_A} {NS_R} {NS_P} type="blank" preserve="1">'
            '<p:cSld name="Blank"><p:spTree><p:nvGrpSpPr>'
            '<p:cNvPr id="1" name=""/><p:cNvGrpSpPr/><p:nvPr/></p:nvGrpSpPr>'
            '<p:grpSpPr><a:xfrm><a:off x="0" y="0"/><a:ext cx="0" cy="0"/>'
            '<a:chOff x="0" y="0"/><a:chExt cx="0" cy="0"/></a:xfrm>'
            '</p:grpSpPr></p:spTree></p:cSld>'
            '<p:clrMapOvr><a:masterClrMapping/></p:clrMapOvr></p:sldLayout>')

n = len(SL)
sld_ids = "".join(
    f'<p:sldId id="{256+i}" r:id="rId{i+2}"/>' for i in range(n))
presentation = ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
    f'<p:presentation {NS_A} {NS_R} {NS_P} saveSubsetFonts="1">'
    '<p:sldMasterIdLst><p:sldMasterId id="2147483648" r:id="rId1"/>'
    '</p:sldMasterIdLst>'
    f'<p:sldIdLst>{sld_ids}</p:sldIdLst>'
    f'<p:sldSz cx="{W}" cy="{H}"/><p:notesSz cx="{H}" cy="{W}"/>'
    '</p:presentation>')

pres_rels = ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
    f'<Relationships xmlns="{PKG}">'
    f'<Relationship Id="rId1" Type="{REL}/slideMaster" Target="slideMasters/slideMaster1.xml"/>'
    + "".join(f'<Relationship Id="rId{i+2}" Type="{REL}/slide" '
              f'Target="slides/slide{i+1}.xml"/>' for i in range(n))
    + f'<Relationship Id="rId{n+2}" Type="{REL}/theme" Target="theme/theme1.xml"/>'
    f'<Relationship Id="rId{n+3}" Type="{REL}/tableStyles" Target="tableStyles.xml"/>'
    '</Relationships>')

ct = ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
    '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
    '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
    '<Default Extension="xml" ContentType="application/xml"/>'
    '<Override PartName="/ppt/presentation.xml" ContentType="application/vnd.openxmlformats-officedocument.presentationml.presentation.main+xml"/>'
    '<Override PartName="/ppt/slideMasters/slideMaster1.xml" ContentType="application/vnd.openxmlformats-officedocument.presentationml.slideMaster+xml"/>'
    '<Override PartName="/ppt/slideLayouts/slideLayout1.xml" ContentType="application/vnd.openxmlformats-officedocument.presentationml.slideLayout+xml"/>'
    '<Override PartName="/ppt/theme/theme1.xml" ContentType="application/vnd.openxmlformats-officedocument.theme+xml"/>'
    '<Override PartName="/ppt/tableStyles.xml" ContentType="application/vnd.openxmlformats-officedocument.presentationml.tableStyles+xml"/>'
    '<Override PartName="/docProps/core.xml" ContentType="application/vnd.openxmlformats-package.core-properties+xml"/>'
    '<Override PartName="/docProps/app.xml" ContentType="application/vnd.openxmlformats-officedocument.extended-properties+xml"/>'
    + "".join(f'<Override PartName="/ppt/slides/slide{i+1}.xml" '
              'ContentType="application/vnd.openxmlformats-officedocument.presentationml.slide+xml"/>'
              for i in range(n))
    + '</Types>')

root_rels = ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
    f'<Relationships xmlns="{PKG}">'
    f'<Relationship Id="rId1" Type="{REL}/officeDocument" Target="ppt/presentation.xml"/>'
    f'<Relationship Id="rId2" Type="{PKG}/metadata/core-properties" Target="docProps/core.xml"/>'
    f'<Relationship Id="rId3" Type="{REL}/extended-properties" Target="docProps/app.xml"/>'
    '</Relationships>')

core = ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
    '<cp:coreProperties xmlns:cp="http://schemas.openxmlformats.org/package/2006/metadata/core-properties" '
    'xmlns:dc="http://purl.org/dc/elements/1.1/" xmlns:dcterms="http://purl.org/dc/terms/" '
    'xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">'
    '<dc:title>CashGuard - ATM Cash-Out Prediction (Project Review 1)</dc:title>'
    '<dc:creator>V. Anbu Chelvan; S. Roopesh; B. Charith Reddy; Y. Rupesh Reddy</dc:creator>'
    '<cp:lastModifiedBy>CashGuard</cp:lastModifiedBy>'
    '<dcterms:created xsi:type="dcterms:W3CDTF">2026-08-11T00:00:00Z</dcterms:created>'
    '</cp:coreProperties>')

app = ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
    '<Properties xmlns="http://schemas.openxmlformats.org/officeDocument/2006/extended-properties" '
    'xmlns:vt="http://schemas.openxmlformats.org/officeDocument/2006/docPropsVTypes">'
    f'<Slides>{n}</Slides><Company/></Properties>')

tblstyles = ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
    f'<a:tblStyleLst {NS_A} def="{{5C22544A-7EE6-4342-B048-85BDC9FD1C3A}}"/>')

OUT = os.path.expanduser("~/Desktop/CashGuard_Review1.pptx")
with zipfile.ZipFile(OUT, "w", zipfile.ZIP_DEFLATED) as z:
    z.writestr("[Content_Types].xml", ct)
    z.writestr("_rels/.rels", root_rels)
    z.writestr("docProps/core.xml", core)
    z.writestr("docProps/app.xml", app)
    z.writestr("ppt/presentation.xml", presentation)
    z.writestr("ppt/_rels/presentation.xml.rels", pres_rels)
    z.writestr("ppt/theme/theme1.xml", theme())
    z.writestr("ppt/tableStyles.xml", tblstyles)
    z.writestr("ppt/slideMasters/slideMaster1.xml", master())
    z.writestr("ppt/slideMasters/_rels/slideMaster1.xml.rels",
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        f'<Relationships xmlns="{PKG}">'
        f'<Relationship Id="rId1" Type="{REL}/slideLayout" Target="../slideLayouts/slideLayout1.xml"/>'
        f'<Relationship Id="rId2" Type="{REL}/theme" Target="../theme/theme1.xml"/>'
        '</Relationships>')
    z.writestr("ppt/slideLayouts/slideLayout1.xml", layout())
    z.writestr("ppt/slideLayouts/_rels/slideLayout1.xml.rels",
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        f'<Relationships xmlns="{PKG}">'
        f'<Relationship Id="rId1" Type="{REL}/slideMaster" Target="../slideMasters/slideMaster1.xml"/>'
        '</Relationships>')
    for i, shapes in enumerate(SL):
        z.writestr(f"ppt/slides/slide{i+1}.xml", slide_xml(shapes))
        z.writestr(f"ppt/slides/_rels/slide{i+1}.xml.rels",
            '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
            f'<Relationships xmlns="{PKG}">'
            f'<Relationship Id="rId1" Type="{REL}/slideLayout" '
            'Target="../slideLayouts/slideLayout1.xml"/></Relationships>')

print(f"WROTE {OUT}  ({os.path.getsize(OUT):,} bytes, {n} slides)")
print("\nDerived statistics used in the deck:")
for k, s in S.items():
    print(f"  {k:26s} mean={f0(s['mean']):>9s} med={f0(s['med']):>9s} "
          f"sd={f0(s['sd']):>8s} cv={s['cv']:5.1f}% skew={s['skew']:+.2f}")
