// Builds the final project report (21CSC305P Machine Learning) from this repository's results.
//   node build_report.js            (needs the npm package "docx"; run from this folder)
// Names, registration numbers and the faculty are in team.json beside this file.
const fs = require("fs");
const path = require("path");
const {
  Document, Packer, Paragraph, TextRun, ImageRun, Table, TableRow, TableCell, AlignmentType, HeadingLevel,
  WidthType, ShadingType, BorderStyle, PageBreak, Footer, PageNumber, TableOfContents, LevelFormat,
  TabStopType, LeaderType, Tab,
} = require("docx");

const HERE = __dirname;
const REPO = path.join(HERE, "..", "..");
const team = JSON.parse(fs.readFileSync(path.join(HERE, "team.json"), "utf8"));
const FONT = "Times New Roman";
const REPO_URL = team.repo_url;

// ---------------------------------------------------------------- helpers
const run = (text, o = {}) => new TextRun({ text, font: FONT, size: o.size || 24, bold: o.bold, italics: o.italics, color: o.color });
function P(content, o = {}) {
  const runs = (Array.isArray(content) ? content : [content]).map((c) => (typeof c === "string" ? run(c, o) : c));
  return new Paragraph({
    children: runs,
    alignment: o.align || AlignmentType.JUSTIFIED,
    spacing: { line: o.line || 360, before: o.before || 0, after: o.after === undefined ? 160 : o.after },
    indent: o.indent,
    keepNext: o.keepNext,
  });
}
const C = (text, o = {}) => P(text, { align: AlignmentType.CENTER, after: o.after === undefined ? 60 : o.after, line: o.line || 276, ...o });
const B = (text, o = {}) => run(text, { bold: true, ...o });
const I = (text, o = {}) => run(text, { italics: true, ...o });
const HEADINGS = [];
const H1 = (text) => { HEADINGS.push([1, text]); return new Paragraph({ heading: HeadingLevel.HEADING_1, children: [new TextRun({ text, font: FONT })], pageBreakBefore: true }); };
const H2 = (text) => { HEADINGS.push([2, text]); return new Paragraph({ heading: HeadingLevel.HEADING_2, children: [new TextRun({ text, font: FONT })] }); };
// Page numbers for the contents list: TOC_PAGES points to a JSON {heading: page} measured from a first render.
const TOC_PAGES = process.env.TOC_PAGES ? JSON.parse(fs.readFileSync(process.env.TOC_PAGES, "utf8")) : null;
const H3 = (text) => new Paragraph({ heading: HeadingLevel.HEADING_3, children: [new TextRun({ text, font: FONT })] });
const bullet = (content, level = 0) => new Paragraph({
  numbering: { reference: "bullets", level },
  children: (Array.isArray(content) ? content : [content]).map((c) => (typeof c === "string" ? run(c) : c)),
  spacing: { line: 336, after: 80 }, alignment: AlignmentType.LEFT,
});
const numbered = (content, ref = "steps") => new Paragraph({
  numbering: { reference: ref, level: 0 },
  children: (Array.isArray(content) ? content : [content]).map((c) => (typeof c === "string" ? run(c) : c)),
  spacing: { line: 336, after: 80 }, alignment: AlignmentType.LEFT,
});
const eq = (text) => P([I(text)], { align: AlignmentType.CENTER, after: 160 });
const PB = () => new Paragraph({ children: [new PageBreak()] });

const BORDER = { style: BorderStyle.SINGLE, size: 4, color: "808080" };
const BORDERS = { top: BORDER, bottom: BORDER, left: BORDER, right: BORDER };
function table(rows, widths, o = {}) {
  const total = widths.reduce((a, b) => a + b, 0);
  return new Table({
    width: { size: total, type: WidthType.DXA },
    columnWidths: widths,
    rows: rows.map((r, ri) => new TableRow({
      tableHeader: ri === 0,
      children: r.map((cell, ci) => new TableCell({
        width: { size: widths[ci], type: WidthType.DXA },
        borders: BORDERS,
        shading: ri === 0 ? { fill: "D9E2F3", type: ShadingType.CLEAR, color: "auto" } : (o.bold && o.bold.includes(ri) ? { fill: "F2F2F2", type: ShadingType.CLEAR, color: "auto" } : undefined),
        margins: { top: 60, bottom: 60, left: 100, right: 100 },
        children: [new Paragraph({
          alignment: ci === 0 || o.left ? AlignmentType.LEFT : AlignmentType.CENTER,
          spacing: { line: 264, after: 0 },
          children: [new TextRun({ text: String(cell), font: FONT, size: 21, bold: ri === 0 || (o.bold && o.bold.includes(ri)) })],
        })],
      })),
    })),
  });
}
let tableNo = {};
let figNo = {};
function caption(kind, chapter, text) {
  const store = kind === "Table" ? tableNo : figNo;
  store[chapter] = (store[chapter] || 0) + 1;
  return P([B(`${kind} ${chapter}.${store[chapter]}: `, { size: 22 }), run(text, { size: 22 })],
    { align: AlignmentType.CENTER, after: 200, before: kind === "Figure" ? 60 : 0, keepNext: kind === "Table" });
}
function tbl(chapter, title, rows, widths, o) {
  return [caption("Table", chapter, title), table(rows, widths, o), P("", { after: 120 })];
}
function fig(chapter, rel, widthIn, text) {
  const file = path.join(REPO, rel);
  const buf = fs.readFileSync(file);
  // PNG size from the IHDR chunk
  const w = buf.readUInt32BE(16), h = buf.readUInt32BE(20);
  const wpx = Math.round(widthIn * 96);
  return [
    new Paragraph({ alignment: AlignmentType.CENTER, keepNext: true, spacing: { before: 120, after: 0 },
      children: [new ImageRun({ type: "png", data: buf, transformation: { width: wpx, height: Math.round(wpx * h / w) },
        altText: { title: text, description: text, name: path.basename(file) } })] }),
    caption("Figure", chapter, text),
  ];
}
const TW = 9026; // text width in DXA: A4 (11906) minus 1440 margins each side

// ---------------------------------------------------------------- front matter
const names = team.members.map((m) => `${m.name.toUpperCase()} [${m.reg}]`);
const logoBig = fs.readFileSync(path.join(HERE, "srm_logo.jpeg"));
const logoSmall = fs.readFileSync(path.join(HERE, "srm_logo_small.jpeg"));

const cover = [
  C([B("A PROJECT REPORT", { size: 28 })], { before: 200, after: 360 }),
  C([B("21CSC305P – MACHINE LEARNING", { size: 28 })], { after: 80 }),
  C([B("(2021 Regulation)", { size: 24 })], { after: 80 }),
  C([B("III Year / V Semester", { size: 24 })], { after: 80 }),
  C([B("Academic Year: 2026 – 2027", { size: 24 })], { after: 360 }),
  C([I("Submitted by", { size: 28 })], { after: 80 }),
  ...names.map((n) => C([run(n, { size: 28 })], { after: 40 })),
  C([B(`Team: ${team.team_name}`, { size: 24 })], { before: 120, after: 360 }),
  C([I("Under the Guidance of", { size: 28 })], { after: 80 }),
  C([run(team.faculty.name, { size: 28 })], { after: 40 }),
  C([run(team.faculty.designation, { size: 24 })], { after: 40 }),
  C([run("Department of Computing Technologies", { size: 24 })], { after: 360 }),
  C([I("in partial fulfillment of the requirements for the degree of", { size: 28 })], { after: 240 }),
  C([run("BACHELOR OF TECHNOLOGY", { size: 28 })], { after: 40 }),
  C([run("in", { size: 28 })], { after: 40 }),
  C([run("COMPUTER SCIENCE AND ENGINEERING", { size: 28 })], { after: 240 }),
  new Paragraph({ alignment: AlignmentType.CENTER, spacing: { after: 120 },
    children: [new ImageRun({ type: "jpg", data: logoBig, transformation: { width: 200, height: 67 },
      altText: { title: "SRM logo", description: "SRM Institute of Science and Technology logo", name: "srm_logo" } })] }),
  C([run("SCHOOL OF COMPUTING", { size: 28 })], { after: 20 }),
  C([run("COLLEGE OF ENGINEERING AND TECHNOLOGY", { size: 28 })], { after: 20 }),
  C([run("SRM INSTITUTE OF SCIENCE AND TECHNOLOGY", { size: 28 })], { after: 20 }),
  C([run("KATTANKULATHUR – 603 203", { size: 28 })], { after: 240 }),
  C([run("NOVEMBER 2026", { size: 28 })], { after: 0 }),
];

const sigCell = (lines) => new TableCell({
  width: { size: TW / 2, type: WidthType.DXA },
  borders: { top: { style: BorderStyle.NONE, size: 0, color: "FFFFFF" }, bottom: { style: BorderStyle.NONE, size: 0, color: "FFFFFF" },
    left: { style: BorderStyle.NONE, size: 0, color: "FFFFFF" }, right: { style: BorderStyle.NONE, size: 0, color: "FFFFFF" } },
  children: lines.map(([t, bold]) => new Paragraph({ spacing: { after: 20 }, children: [run(t, { size: 24, bold })] })),
});
const bonafide = [
  new Paragraph({ alignment: AlignmentType.CENTER, spacing: { after: 120 },
    children: [new ImageRun({ type: "jpg", data: logoSmall, transformation: { width: 120, height: 51 },
      altText: { title: "SRM logo", description: "SRM Institute of Science and Technology logo", name: "srm_logo_small" } })] }),
  C([run("SRM INSTITUTE OF SCIENCE AND TECHNOLOGY", { size: 32 })], { after: 40 }),
  C([run("KATTANKULATHUR – 603 203", { size: 32 })], { after: 480 }),
  C([B("BONAFIDE CERTIFICATE", { size: 36 })], { after: 600 }),
  P([run("Certified that "), B("21CSC305P – MACHINE LEARNING"), run(" project report is the bonafide work of “"),
    B(team.members.map((m) => `${m.name.toUpperCase()} [${m.reg}]`).join(", ")),
    run("” who carried out the task of completing the project within the allotted time.")], { line: 480, after: 1800 }),
  new Table({
    width: { size: TW, type: WidthType.DXA }, columnWidths: [TW / 2, TW / 2],
    rows: [new TableRow({ children: [
      sigCell([["SIGNATURE", true], ["", false], [team.faculty.name, false], ["Course Faculty", true], [team.faculty.designation, false],
        ["Department of Computing Technologies", false], ["SRM Institute of Science and Technology", false], ["Kattankulathur", false]]),
      sigCell([["SIGNATURE", true], ["", false], ["Dr. G. Niranjana", false], ["Head of the Department", true], ["Professor", false],
        ["Department of Computing Technologies", false], ["SRM Institute of Science and Technology", false], ["Kattankulathur", false]]),
    ] })],
  }),
];

// ---------------------------------------------------------------- body
const body = [];
const push = (...xs) => xs.flat().forEach((x) => body.push(x));

// Acknowledgement
HEADINGS.push([1, "ACKNOWLEDGEMENT"]);
push(new Paragraph({ heading: HeadingLevel.HEADING_1, children: [new TextRun({ text: "ACKNOWLEDGEMENT", font: FONT })] }));
push(P("We express our sincere gratitude to the management of SRM Institute of Science and Technology, Kattankulathur, for providing the facilities and the academic environment that made this work possible."),
  P(`We thank Dr. G. Niranjana, Professor and Head, Department of Computing Technologies, for her support, and our course faculty, ${team.faculty.name}, ${team.faculty.designation}, for guidance and feedback at every project review of 21CSC305P – Machine Learning.`),
  P("We also thank the organisations whose open data made these projects possible: Kaggle and its contributors, the CalCOFI programme, Olist, the PX4 project and Open-Meteo, the Internal Displacement Monitoring Centre (IDMC) and the World Bank."),
  P("Finally, we thank our families and friends for their encouragement throughout the semester."),
  P(""), P(team.members.map((m) => m.name).join(", "), { align: AlignmentType.RIGHT }));

// Abstract
push(H1("ABSTRACT"));
push(P("This report presents five machine-learning mini projects completed by Team Cash Guard for 21CSC305P – Machine Learning, one for each unit of the course. Each project starts from a real problem statement, uses real public data, applies the methods of its unit, and is evaluated honestly on held-out data against a simple baseline."),
  P([B("Unit 1 (regression): "), run("CashGuard predicts next-day ATM cash demand with a multiple linear regression written from first principles and turns the forecast into a refill alert. It reaches R² = 0.666 on unseen days, against 0.483 for the naive “same as today” forecast, and flags 21 of 50 ATMs for refill.")]),
  P([B("Unit 2 (linear models): "), run("ocean temperature is predicted from salinity over 72 years of CalCOFI data (895,371 records). With 10% faulty sensor readings in training, Huber robust regression keeps its bias to 0.14 °C against 1.11 °C for least squares, and its fault mask catches 99.4% of the faults.")]),
  P([B("Unit 3 (clustering): "), run("K-Means groups 383 real warehouse products from the Olist dataset into four storage zones by pick frequency, seasonality, volume and weight; in a simple aisle model, walking per pick falls by 27%.")]),
  P([B("Unit 4 (sequential data): "), run("a Linear Dynamical System with Kalman filtering, RTS smoothing and EM estimates a drone’s 3-D position and velocity in turbulent wind from noisy IMU, altimeter and optical-flow readings. Position error falls from 103.4 m (IMU alone) to 0.43 m, a 238-fold improvement, and the unmeasured wind is recovered to 2.1 m/s.")]),
  P([B("Unit 5 (combining models): "), run("a hybrid of Bayesian Model Averaging and Gradient Boosting predicts how many people an extreme weather event will displace, using 28,000 IDMC events. It reaches R² = 0.520 on 5,600 unseen events, and 94% of outcomes fall inside its 90% prediction interval; a planning function converts each forecast into tents, shelter area and water.")]),
  P([run("All code, data samples, figures and presentations are in one public repository: "), B(REPO_URL), run(".")]));
push(P([B("Keywords: "), run("linear regression, Huber loss, Bayesian linear regression, K-Means clustering, Kalman filter, linear dynamical systems, EM algorithm, Bayesian model averaging, gradient boosting.")]));

// TOC
push(new Paragraph({ pageBreakBefore: true, alignment: AlignmentType.CENTER, spacing: { after: 360 },
  children: [new TextRun({ text: "TABLE OF CONTENTS", font: FONT, size: 32, bold: true })] }));
const TOC_AT = body.length;      // the contents list is inserted here once all headings are known

// ---------------- Chapter 1
push(H1("1. INTRODUCTION"));
push(H2("1.1 About the course projects"),
  P("21CSC305P – Machine Learning is organised in five units. For each unit, every team receives a problem statement, studies it, chooses a method from that unit, implements it, and presents it at a project review. This report collects all five projects of Team Cash Guard in one place, with the problem statement, data, method, implementation, results and conclusion of each."),
  H2("1.2 The five projects"));
push(tbl(1, "The five projects at a glance", [
  ["Unit", "Project", "Method", "Main result"],
  ["1", "CashGuard: ATM cash-out prediction", "Multiple linear regression from first principles", "R² 0.666 (baseline 0.483)"],
  ["2", "Robust ocean temperature", "Basis functions; OLS, ridge, Bayesian, RANSAC, Huber", "Bias 0.14 °C vs 1.11 °C (OLS)"],
  ["3", "Warehouse SKU clustering", "K-Means (elbow, silhouette)", "4 zones; 27% less walking"],
  ["4", "Drone state estimation", "LDS + Kalman filter, RTS smoother, EM", "0.43 m vs 103.4 m (238×)"],
  ["5", "Climate displacement forecast", "Bayesian Model Averaging + Gradient Boosting", "R² 0.520; 94% in 90% band"],
], [700, 2600, 3126, 2600]));
push(H2("1.3 Team"));
push(tbl(1, "Team Cash Guard", [
  ["Member", "Registration number", "Main contributions"],
  ...team.members.map((m) => [m.name + (m.head ? " (team head)" : ""), m.reg, m.role]),
], [2400, 2200, 4426]));
push(H2("1.4 Tools"),
  P("All projects are written in Python. Unit 1 deliberately uses only the Python standard library for the model (the normal equations are solved by hand). The other units use NumPy, pandas, scikit-learn and matplotlib, and Unit 4 adds pyulog and SQLite. Units 3, 4 and 5 run end to end in Google Colab and download their own data."),
  P([run("Repository: "), B(REPO_URL), run(". Each unit has its own folder with a README (problem statement, data, how to run, results), the code or notebook, the figures and the review presentation.")]));

// ---------------- Chapter 2: Unit 1
push(H1("2. UNIT 1 – CASHGUARD: ATM CASH-OUT PREDICTION"));
push(H2("2.1 Problem statement"),
  P([I("Develop an ML model that predicts when an ATM will run out of cash and require replenishment. The model can use withdrawal patterns, ATM location, weekends, holidays, salary periods, and historical cash withdrawal data.")]),
  P("An ATM that runs dry loses customers and fees; one that is refilled too often wastes money on cash-in-transit trips and idle cash. The useful answer is not a demand figure but a decision: which ATMs need a refill before the next truck can arrive."),
  H2("2.2 Dataset"),
  P("The problem statement points to the Kaggle dataset ATM Cash Demand Forecasting and Management (5,658 rows, 13 columns, 50 ATMs, 1 January 2022 to 1 January 2024). Because Kaggle requires a login, the repository includes a generator that reproduces the published statistics of the data card exactly (withdrawals mean ≈ 49,812, sd ≈ 15,218; 2% holidays; 9.6% special events); the analysis reads the real file first if it is present. Each ATM keeps a fixed location type, which the real file does not always do."));
push(tbl(2, "Main columns", [
  ["Column", "Meaning"],
  ["Total_Withdrawals, Total_Deposits", "Cash taken out and paid in on the day"],
  ["Previous_Day_Cash_Level", "Cash in the machine at the start of the day"],
  ["Day_of_Week, Time_of_Day, Holiday_Flag, Special_Event_Flag", "Calendar effects"],
  ["Location_Type, Nearby_Competitor_ATMs, Weather_Condition", "Where the ATM is and what is around it"],
  ["Cash_Demand_Next_Day (target)", "Cash that will be withdrawn the next day"],
], [4200, 4826], { left: true }));
push(H2("2.3 Exploratory analysis"),
  P("Next-day demand has mean 49,894 and median 48,222 (sd 15,377), slightly right-skewed. Today’s withdrawals are by far the strongest single signal (r = +0.744), nearby competitor ATMs lower demand (r = −0.396), and the salary window (days 1–5 and 25–31 of the month) raises it by about 21% (56,035 against 46,122)."));
push(fig(2, "unit-1-cashguard-atm/figures/03_correlation_heatmap.png", 4.3, "Correlation of each feature with next-day demand"));
push(fig(2, "unit-1-cashguard-atm/figures/06_violin_calendar_effects.png", 5.6, "Calendar effects: salary window, special events and holidays"));
push(H2("2.4 Method"),
  P("The target is continuous, so this is regression. CashGuard is a multiple linear regression on 25 engineered features: the numeric columns, weekend and salary-window flags, day of month, and one-hot columns for day of week, time of day, location type and weather. Features are standardised, and the weights solve the regularised normal equations"),
  eq("(XᵀX + λI) w = Xᵀy"),
  P("solved by Gaussian elimination with partial pivoting, written from scratch without NumPy or scikit-learn. Validation is time-aware: the first 70% of the calendar trains (3,960 rows, to 25 May 2023) and the rest tests (1,698 rows). A random split would let the model see the future."),
  P("The forecast becomes the decision the problem asks for:"),
  eq("net drain = predicted demand − average deposits;   days to empty = cash held ÷ net drain"),
  P("An ATM is flagged REFILL NOW when its days to empty are at most the refill lead time, assumed to be 2 days."));
push(H2("2.5 Results"));
push(tbl(2, "Results on the unseen test period", [
  ["Model", "MAE", "RMSE", "R²", "MAPE"],
  ["CashGuard regression", "7,065", "9,067", "0.666", "15.3%"],
  ["Baseline: training mean", "12,399", "15,688", "−0.001", "27.5%"],
  ["Baseline: same as today", "8,563", "11,279", "0.483", "18.1%"],
], [3426, 1400, 1400, 1400, 1400], { bold: [1] }));
push(P("“Same as today” is what a bank without a model would do, so it is the bar that matters. CashGuard lowers its RMSE by 20% and explains 18 percentage points more of the variance. The largest standardised coefficients are today’s withdrawals (+9,911), nearby competitors (−2,632), Thursday (+2,168), Saturday (−1,921) and the salary window (+1,540), which match the exploratory analysis."),
  P("On the last day of data, 21 of the 50 ATMs have less than two days of cash left. Ranked by days left (the first, ATM_0005, has 1.36 days), the list is the route a cash-in-transit team would drive."));
push(H2("2.6 Conclusion"),
  P("A transparent linear model, built without libraries, beats the naive forecast clearly and turns demand into a refill schedule. Its main limitation is that it under-predicts on 46.8% of test days, which is when stock-outs happen; an asymmetric loss or a safety margin would trade a few extra trips for fewer empty machines."));

// ---------------- Chapter 3: Unit 2
push(H1("3. UNIT 2 – ROBUST OCEAN TEMPERATURE FROM SALINITY"));
push(H2("3.1 Problem statement"),
  P([I("Predict ocean water temperatures based on salinity measurements taken over 60+ years, using outlier-proof regression models (Huber) so that faulty sensor readings don’t corrupt the predictions.")]),
  P("A 72-year archive is stitched together from many ships, crews and instrument generations. Thermistors drift and sensors foul, and a faulty reading is usually still a physically plausible number, so a simple range check cannot remove it."),
  H2("3.2 Dataset"),
  P("The CalCOFI Bottle Database, March 1949 to May 2021: real seawater samples off the coast of California."));
push(tbl(3, "Data audit", [
  ["Step", "Rows"],
  ["Bottle records read", "895,371"],
  ["With both temperature and salinity", "844,748"],
  ["Flagged by CalCOFI quality codes", "38,593 (4.57%)"],
  ["Physically impossible (e.g. a 99 °C reading)", "934"],
  ["Clean rows after screening", "806,108"],
  ["Modelled sample: train / test", "60,000 / 20,000"],
], [5526, 3500]));
push(P("Salinity and temperature correlate at −0.505, and the relationship is clearly curved."));
push(fig(3, "unit-2-ocean-temperature-huber/figures/fig_data.png", 6.0, "The CalCOFI data and the physical quality gate"));
push(H2("3.3 Unit 2 concepts applied"),
  bullet([B("Maximum likelihood: "), run("with Gaussian noise, maximising the likelihood is the same as minimising squared error (ordinary least squares).")]),
  bullet([B("Basis functions: "), run("y = wᵀφ(x) with φ a degree-5 polynomial of salinity, so a linear model fits the curve.")]),
  bullet([B("Robust regression: "), run("the Huber loss is quadratic for small residuals and linear beyond δ, so one wild reading cannot pull the fit far. δ = 1.35 keeps about 95% of least squares’ efficiency on clean data. RANSAC is the consensus-based alternative.")]),
  bullet([B("MAP with a Gaussian prior: "), run("ridge regression, with α = 0.001 chosen by cross-validation.")]),
  bullet([B("Bayesian linear regression: "), run("a full posterior over weights, which also gives a predictive standard deviation.")]),
  eq("L_δ(r) = ½ r²  if |r| ≤ δ;   δ(|r| − ½ δ)  otherwise"));
push(H2("3.4 Method"),
  P("Two lines of defence. First, a physical gate removes impossible values (salinity outside 30–37 PSU or temperature outside −2 to 35 °C) and rows CalCOFI itself flagged. Second, robust regression handles faults the gate cannot see. To measure this honestly, every model is trained on contaminated data and scored on the same clean test set; faults are injected at rates from 0 to 30% as warm-biased readings that stay inside the physical range."));
push(H2("3.5 Results"));
push(tbl(3, "Clean test set, models trained with 10% faulty readings", [
  ["Model", "RMSE (°C)", "MAE (°C)", "R²", "Bias (°C)"],
  ["OLS (MLE / least squares)", "3.505", "2.867", "0.322", "+1.109"],
  ["Ridge (MAP, Gaussian prior)", "3.579", "2.918", "0.293", "+1.113"],
  ["Bayesian linear regression", "3.441", "2.758", "0.346", "+1.109"],
  ["RANSAC", "3.675", "2.320", "0.254", "−0.494"],
  ["Huber (δ = 1.35)", "3.322", "2.304", "0.390", "−0.141"],
], [3426, 1400, 1400, 1400, 1400], { bold: [5] }));
push(fig(3, "unit-2-ocean-temperature-huber/figures/fig_huber.png", 6.0, "Fits on contaminated training data: least squares is pulled warm, Huber is not"));
push(fig(3, "unit-2-ocean-temperature-huber/figures/fig_sweep.png", 6.0, "Test error and bias as the share of faulty readings rises from 0 to 30%"));
push(bullet("Huber’s bias is 7.5 times smaller than least squares’ (0.14 °C against 1.11 °C)."),
  bullet("Its fault mask flags 99.4% of the injected faults."),
  bullet("At 30% contamination, Huber’s RMSE is 17% lower than least squares’ (3.96 °C against 4.79 °C)."),
  bullet("Ridge and the Bayesian model do not fix the bias: a prior on the weights does nothing about a corrupted target. Regularisation and robustness solve different problems."),
  bullet("R² stays near 0.4 because salinity alone is ambiguous (the same salinity occurs at different temperatures in different water masses). The task was robustness, not R²; adding depth would raise it."));
push(H2("3.6 Conclusion"),
  P("A physical gate plus Huber regression predicts ocean temperature across 72 years of real survey data and stays essentially unbiased even when one training reading in ten comes from a faulty sensor. Faulty readings no longer corrupt the predictions."));

// ---------------- Chapter 4: Unit 3
push(H1("4. UNIT 3 – WAREHOUSE SKU CLUSTERING WITH K-MEANS"));
push(H2("4.1 Problem statement"),
  P([I("Partition warehouse product SKUs based on order pick frequency, seasonal demand velocity, physical dimensions, and handling requirements. Logistical managers can use these operational clusters to optimize inventory placement and minimize worker travel time during order fulfillment.")]),
  H2("4.2 Choice of method"),
  P("From the Unit 3 methods (K-Means, mixtures of Gaussians, hierarchical clustering, PCA and factor analysis) we chose K-Means. The task is a partition: every SKU needs exactly one storage zone. K-Means is simple, fast for thousands of SKUs, and its cluster centres read directly as zone profiles. Hierarchical clustering, mixtures of Gaussians and PCA are compared in the demo."),
  H2("4.3 Dataset and features"),
  P("The Brazilian E-Commerce Public Dataset by Olist (MIT licence): 99,441 orders and 112,650 order lines placed from September 2016 to October 2018, covering 32,951 products. For the 383 products ordered at least 30 times, four features are built:"),
  bullet([B("Pick frequency: "), run("number of orders.")]),
  bullet([B("Seasonal velocity: "), run("a season index, the peak month’s orders relative to the product’s average month.")]),
  bullet([B("Physical dimensions: "), run("volume in litres from length × width × height.")]),
  bullet([B("Handling requirements: "), run("weight in kilograms (the dataset has no handling field, so weight stands in for it).")]),
  P("The features are scaled before clustering so that no single unit dominates the distance."));
push(H2("4.4 Algorithm"),
  P("K-Means minimises the within-cluster sum of squared distances J = Σₖ Σ_{x∈Cₖ} ‖x − μₖ‖² by alternating two steps until nothing changes: assign every SKU to its nearest centre, then move each centre to the mean of its SKUs. The number of clusters is chosen with the elbow of J and the silhouette score."));
push(fig(4, "unit-3-warehouse-sku-kmeans/docs/img/elbow.png", 4.4, "Elbow: within-cluster error for k = 1 to 8; the bend is at k = 4"));
push(P("The silhouette score is also highest at k = 4 (0.367, against 0.359 for k = 2 and 0.342 for k = 3), so both criteria agree."));
push(H2("4.5 Results"));
push(tbl(4, "The four clusters on real Olist data", [
  ["Zone", "Cluster", "SKUs", "Avg orders", "Season index", "Volume (L)", "Weight (kg)"],
  ["A", "Fast movers", "76", "160", "2.6", "9.2", "1.1"],
  ["B", "Bulky / heavy", "84", "52", "3.5", "47.1", "7.6"],
  ["C", "Seasonal", "25", "48", "7.4", "12.9", "1.1"],
  ["D", "Regular small items", "198", "45", "3.2", "5.1", "0.6"],
], [800, 2226, 900, 1300, 1300, 1250, 1250]));
push(fig(4, "unit-3-warehouse-sku-kmeans/docs/img/clusters_pca.png", 5.2, "The 383 SKUs coloured by cluster, projected onto two principal components"));
push(P("Each cluster becomes a storage zone, the most-picked nearest to packing. In a simple one-aisle model where each group takes as much aisle as it has products, the average walk per pick falls from 63.8 m with no grouping to 46.5 m with the K-Means zones, 27% less. This is a model, not a measurement."));
push(fig(4, "unit-3-warehouse-sku-kmeans/docs/img/walk_per_pick.png", 5.6, "Modelled walk per pick: no grouping against K-Means zones"));
push(H2("4.6 Conclusion"),
  P("K-Means turns raw order history into four zones a warehouse manager can act on: fast movers near packing, bulky items on low racks, seasonal items moved in and out by season, and the long tail of small items further back. An interactive demo (one HTML file) lets the reader run K-Means step by step and watch the products move on the shelves."));

// ---------------- Chapter 5: Unit 4
push(H1("5. UNIT 4 – DRONE STATE ESTIMATION IN TURBULENT WIND"));
push(H2("5.1 Problem statement"),
  P([I("Estimate the true 3D position and velocity of an autonomous drone under turbulent wind conditions by combining noisy sensor readings (IMU, altimeter, optical flow) using Linear Dynamical Systems and Kalman filtering.")]));
push(tbl(5, "The three sensors, each inadequate on its own", [
  ["Sensor", "Rate", "Measures", "Weakness"],
  ["IMU", "100 Hz", "Acceleration", "Integrating twice turns a small bias into a huge error: drifts 103 m in 60 s"],
  ["Altimeter", "10 Hz", "Height", "σ = 0.60 m; says nothing about horizontal position"],
  ["Optical flow", "30 Hz", "Horizontal velocity", "σ ≈ 0.12 m/s, and degrades with altitude"],
], [1500, 1000, 1900, 4626]));
push(P("Turbulent wind pushes the aircraft around, and gusts are correlated in time, not white noise. No sensor measures the wind."));
push(H2("5.2 Why this is a Unit 4 problem"),
  P("A Linear Dynamical System is a hidden Markov model whose hidden state is continuous. The forward pass becomes the Kalman filter, forward–backward becomes the Rauch–Tung–Striebel (RTS) smoother, Baum–Welch becomes EM with the smoother in the E-step, and because everything is linear and Gaussian the posterior stays Gaussian: a mean and a covariance are the whole answer."),
  H2("5.3 Model"),
  P("The state is 9-dimensional: position, velocity and wind on each of the three axes. Per axis, with time step Δt:"),
  eq("p(t+1) = p(t) + v(t)·Δt"),
  eq("v(t+1) = v(t) + (a − k·(v(t) − w(t)))·Δt"),
  eq("w(t+1) = φ·w(t) + ε(t),   φ = exp(−Δt/τ)"),
  bullet([B("Drag acts on airspeed (v − w), "), run("not ground speed. This couples the wind into the dynamics and makes it observable: the gust is inferred from how the drone is pushed off course.")]),
  bullet([B("Gusts follow an Ornstein–Uhlenbeck process, "), run("so a gust now predicts a gust a second later. This is still linear, so the Kalman filter remains exactly optimal; no extended or unscented filter is needed.")]),
  P("The Kalman filter alternates predict (move the estimate with the physics; uncertainty grows) and update (correct it with a sensor reading, weighted by the Kalman gain; uncertainty shrinks). Sensors at different rates simply update when they report."));
push(H2("5.4 Real data"),
  bullet([B("Real IMU noise: "), run("a PX4 flight log from a real quadrotor (248 Hz over 69 s, 17,070 samples) is parsed with pyulog; the accelerometer noise σ = 0.289 m/s² and bias are measured from it, not assumed.")]),
  bullet([B("Real turbulence: "), run("168 hourly wind observations from the Open-Meteo archive near Kallakurichi; the flight uses the gustiest hour (21 Oct 2026, 14:00: mean 2.44 m/s, gusts 9.69 m/s), giving a gust intensity of 2.90 m/s.")]),
  bullet([B("Database: "), run("every sensor reading, the ground truth and all estimates are stored in SQLite (36,000+ rows), and accuracy is computed by an SQL JOIN against the ground truth.")]));
push(H2("5.5 Results"));
push(tbl(5, "Accuracy, computed in SQL against the ground truth", [
  ["Method", "Position RMSE (m)", "Velocity RMSE (m/s)"],
  ["Integrating the IMU (dead reckoning)", "103.394", "4.601"],
  ["Kalman filter", "0.434", "0.683"],
  ["RTS smoother", "0.318", "0.200"],
], [4226, 2400, 2400], { bold: [2, 3] }));
push(fig(5, "unit-4-drone-state-estimation/slides/figures/deck_traj.png", 3.4, "True path, IMU-only path and Kalman estimate in 3-D"));
push(fig(5, "unit-4-drone-state-estimation/slides/figures/deck_rmse.png", 5.6, "Position and velocity error: IMU alone, Kalman filter, RTS smoother (log scale)"));
push(bullet("The Kalman filter is 238 times more accurate than integrating the IMU, and the smoother improves velocity a further 3.4 times."),
  bullet("The wind, which no sensor measures, is recovered to 2.14 m/s."),
  bullet("EM learns the sensor noise from the data alone: starting from a wrong guess, the altimeter σ converges to 0.593 m (true 0.600 m) and the log-likelihood rises monotonically from −2,220 to −1,649."),
  bullet("Consistency tests (NIS) caught a model mismatch that RMSE hid: with a constant optical-flow noise the filter was as accurate but claimed three times too much confidence (NIS 10.15 against the ideal 2); an altitude-scaled noise fixed it (NIS 1.95)."),
  bullet("Adding GPS made short flights worse (+73% error at 60 s) and only helped after about five minutes (−57% at 300 s)."));
push(fig(5, "unit-4-drone-state-estimation/slides/figures/deck_em.png", 5.8, "EM: log-likelihood per iteration, and the measured wind against the filter’s estimate"));
push(H2("5.6 Conclusion"),
  P("Three weak sensors together beat any one of them by more than two orders of magnitude, and modelling the wind as part of the state recovers a quantity nothing measures. The main lesson is that being accurate and knowing you are accurate are different things: only a consistency test tells you which you have. Limits: the flight is gentle (aerobatics would need an extended filter) and the trajectory is simulated, although the noise and wind driving it are measured."));

// ---------------- Chapter 6: Unit 5
push(H1("6. UNIT 5 – PREDICTING CLIMATE-DRIVEN DISPLACEMENT"));
push(H2("6.1 Problem statement"),
  P([I("Develop a hybrid model combining Bayesian Model Averaging and Gradient Boosting to predict population displacement caused by extreme climate events and support local authorities in urban planning and emergency aid distribution.")]),
  P("Displacement figures are usually known only after an event. An estimate with an honest range, available when a flood warning or cyclone forecast is issued, would let authorities pre-position tents, food and water and plan shelters."),
  H2("6.2 Dataset"));
push(tbl(6, "Data sources", [
  ["Source", "Content"],
  ["IDMC internal displacements associated with disasters (HDX, CC BY-IGO)", "29,698 disaster events, 2008–2025: country, dates, hazard type, people displaced"],
  ["World Bank Open Data API", "Population, urban share, GDP per capita, population density by country and year"],
], [4200, 4826], { left: true }));
push(P("Keeping weather-related events with at least one person displaced leaves 28,112 events in 214 countries and territories, 28,000 with complete country data. Floods are 52.8% of events, and floods and storms together cause 96% of all displacement. The target is log(1 + people displaced); inputs are event duration, season, named storm, multi-country and reporting flags, a year trend, country population, urban share, density, GDP per capita, the country’s past displacement, and hazard type."));
push(fig(6, "unit-5-climate-displacement/figures/fig1_eda_hazards.png", 6.0, "Events by hazard type and people displaced per year"));
push(H2("6.3 Unit 5 concepts"),
  bullet([B("Bayesian Model Averaging (BMA): "), run("instead of choosing one model, average all candidate models weighted by their posterior probability. With equal priors this is approximated by the BIC:")]),
  eq("p(y | x, D) = Σₖ p(y | x, Mₖ) p(Mₖ | D),   p(Mₖ | D) ∝ exp(−BICₖ / 2)"),
  bullet([B("Gradient Boosting: "), run("trees are added one at a time, each fitted to the current residuals and added with a small learning rate η:")]),
  eq("Fₘ(x) = Fₘ₋₁(x) + η · hₘ(x)"),
  bullet([B("Why combine them: "), run("BMA is interpretable and gives honest uncertainty but is limited to linear models; boosting captures non-linear patterns but has no built-in uncertainty.")]));
push(H2("6.4 The hybrid model"),
  numbered("Random 80/20 split: 22,400 training and 5,600 test events; numeric inputs standardised."),
  numbered("BMA: fit all 2¹³ = 8,192 subsets of the 13 numeric features by least squares (hazard type always in), weight each by exp(−BIC/2), and compute the averaged prediction and its standard deviation."),
  numbered("Gradient Boosting on BMA’s training residuals: 500 trees, depth 4, learning rate 0.05, 80% subsampling, at least 40 events per leaf."),
  numbered("Hybrid prediction = BMA prediction + boosted residual, with a 90% interval of ± 1.645 σ from BMA."));
push(H2("6.5 Results"));
push(tbl(6, "Performance on 5,600 unseen events", [
  ["Model", "RMSE (log)", "MAE (log)", "R²", "Typical error"],
  ["BMA (averaged linear models)", "2.187", "1.740", "0.361", "×4.3"],
  ["Gradient Boosting", "1.902", "1.482", "0.517", "×3.4"],
  ["Hybrid BMA + Gradient Boosting", "1.897", "1.481", "0.520", "×3.4"],
], [3426, 1400, 1400, 1400, 1400], { bold: [3] }));
push(fig(6, "unit-5-climate-displacement/figures/fig4_bma_pip.png", 5.0, "BMA posterior inclusion probability of each feature"));
push(fig(6, "unit-5-climate-displacement/figures/fig7_intervals.png", 6.0, "Hybrid predictions with 90% BMA intervals for 40 test events"));
push(bullet("The hybrid is the most accurate of the three; boosting adds about 16 points of explained variance over BMA."),
  bullet("94% of real outcomes fall inside the nominal 90% interval, so the ranges can be trusted (slightly conservative)."),
  bullet("Nine features have inclusion probability close to 1 (duration, season, named storm, reporting trend, population, urban share, density and the country’s history); the single best model has posterior probability 0.78, so averaging still matters for the remaining 22%."));
push(H2("6.6 Supporting local authorities"),
  P("A plan_aid() function converts a forecast into supplies using the Sphere humanitarian standards: 15 litres of water per person per day, 3.5 m² of covered space per person and one family tent per five people."));
push(tbl(6, "Example: a named typhoon in the Philippines in November, lasting 3 days", [
  ["Scenario", "People displaced", "Family tents", "Shelter (m²)", "Water, 7 days (L)"],
  ["Low (5%)", "1,346", "270", "4,711", "141,330"],
  ["Expected", "48,810", "9,762", "170,835", "5,125,050"],
  ["High (95%)", "1,769,056", "353,812", "6,191,696", "185,750,880"],
], [1826, 1800, 1700, 1700, 2000]));
push(H2("6.7 Conclusion"),
  P("Combining models works: BMA explains which factors drive displacement and how certain the forecast is, and Gradient Boosting adds the accuracy a linear model lacks. Limits: the data has no physical intensity (rainfall, wind speed, flood depth), predictions are at country level, and IDMC’s reporting changed after 2023, which makes a strict past-to-future test harder (R² ≈ 0.18)."));

// ---------------- Chapter 7
push(H1("7. CONCLUSION AND FUTURE WORK"));
push(P("Across the five units, the same discipline held: start from the real problem, use real data, test on data the model has not seen, and compare against what someone without a model would do. Each project beat its baseline by a clear margin, and each produced something a user can act on: a refill route, an unbiased temperature model, storage zones, a position fix with honest uncertainty, and an aid plan with a range."));
push(tbl(7, "Future work", [
  ["Unit", "Next step"],
  ["1", "An asymmetric loss or safety margin to reduce under-prediction; train on the real Kaggle file"],
  ["2", "Add depth as an input; tune δ; replace polynomials with kernels (SVR)"],
  ["3", "A real handling field and multi-aisle travel measured in a warehouse"],
  ["4", "An extended Kalman filter for aggressive flight; real flight trajectories"],
  ["5", "Weather-forecast intensity inputs and sub-national data; BMA over tree models"],
], [900, 8126], { left: true }));

// ---------------- References
push(H1("REFERENCES"));
[
  "C. M. Bishop, Pattern Recognition and Machine Learning. Springer, 2006.",
  "K. P. Murphy, Machine Learning: A Probabilistic Perspective. MIT Press, 2012.",
  "P. J. Huber, “Robust estimation of a location parameter,” Annals of Mathematical Statistics, 35(1), 73–101, 1964.",
  "R. E. Kalman, “A new approach to linear filtering and prediction problems,” Journal of Basic Engineering, 82(1), 35–45, 1960.",
  "H. E. Rauch, F. Tung and C. T. Striebel, “Maximum likelihood estimates of linear dynamic systems,” AIAA Journal, 3(8), 1445–1450, 1965.",
  "J. A. Hoeting, D. Madigan, A. E. Raftery and C. T. Volinsky, “Bayesian model averaging: a tutorial,” Statistical Science, 14(4), 382–417, 1999.",
  "J. H. Friedman, “Greedy function approximation: a gradient boosting machine,” Annals of Statistics, 29(5), 1189–1232, 2001.",
  "S. Lloyd, “Least squares quantization in PCM,” IEEE Transactions on Information Theory, 28(2), 129–137, 1982.",
  "F. Pedregosa et al., “Scikit-learn: machine learning in Python,” Journal of Machine Learning Research, 12, 2825–2830, 2011.",
  "Kaggle, “ATM Cash Demand Forecasting and Management.” https://www.kaggle.com/datasets/zoya77/atm-cash-demand-forecasting-and-management",
  "CalCOFI, “Bottle Database, 1949–2021.” https://calcofi.org/data/oceanographic-data/bottle-database/",
  "Olist, “Brazilian E-Commerce Public Dataset.” https://github.com/olist/work-at-olist-data",
  "PX4 Autopilot, pyulog sample flight log. https://github.com/PX4/pyulog",
  "Open-Meteo, historical weather API. https://open-meteo.com",
  "Internal Displacement Monitoring Centre, “Internal displacements associated with disasters.” https://data.humdata.org/dataset/idmc-internal-displacements-new-displacements-associated-with-disasters",
  "World Bank Open Data. https://data.worldbank.org",
  "The Sphere Handbook: Humanitarian Charter and Minimum Standards in Humanitarian Response, 2018.",
].forEach((r) => push(numbered(r, "refs")));

// ---------------- Appendix
push(H1("APPENDIX A – IMPLEMENTATION LINKS"));
push(tbl("A", "Code, notebooks and presentations", [
  ["Unit", "Folder in the repository", "Presentation (review)"],
  ["1", "unit-1-cashguard-atm/", "Review 1: CashGuard_Review1"],
  ["2", "unit-2-ocean-temperature-huber/", "Review 2: Unit2_ML_Robust_Ocean_Temperature"],
  ["3", "unit-3-warehouse-sku-kmeans/", "Review 3: kmeans-sku-clustering"],
  ["4", "unit-4-drone-state-estimation/", "Review 4: Drone_Kalman_Unit4_Presentation"],
  ["5", "unit-5-climate-displacement/", "Review 5: Climate_Displacement_Presentation"],
], [800, 3800, 4426], { left: true }));
push(P([run("Repository: "), B(REPO_URL)]),
  P("Units 3, 4 and 5 open directly in Google Colab from the links in the repository README and run end to end with Runtime → Run all; they download their own data. Units 1 and 2 are Python scripts; their READMEs give the commands."));

// the contents list: static lines with dot leaders, page numbers from the first render
body.splice(TOC_AT, 0, ...HEADINGS.map(([lvl, text]) => new Paragraph({
  spacing: { after: lvl === 1 ? 80 : 40, before: lvl === 1 ? 120 : 0 },
  indent: { left: lvl === 1 ? 0 : 440 },
  tabStops: [{ type: TabStopType.RIGHT, position: TW, leader: LeaderType.DOT }],
  children: [
    new TextRun({ text, font: FONT, size: lvl === 1 ? 24 : 22, bold: lvl === 1 }),
    new TextRun({ font: FONT, size: lvl === 1 ? 24 : 22, bold: lvl === 1,
      children: [new Tab(), String(TOC_PAGES && TOC_PAGES[text] !== undefined ? TOC_PAGES[text] : "")] }),
  ],
})));
fs.writeFileSync(path.join(HERE, ".headings.json"), JSON.stringify(HEADINGS));

// ---------------------------------------------------------------- document
const doc = new Document({
  creator: team.members[0].name,
  title: "21CSC305P Machine Learning – Project Report – Team " + team.team_name,
  features: { updateFields: true },
  styles: {
    default: { document: { run: { font: FONT, size: 24 } } },
    paragraphStyles: [
      { id: "Heading1", name: "Heading 1", basedOn: "Normal", next: "Normal", quickFormat: true,
        run: { font: FONT, size: 32, bold: true }, paragraph: { spacing: { before: 0, after: 360 }, alignment: AlignmentType.CENTER, keepNext: true, outlineLevel: 0 } },
      { id: "Heading2", name: "Heading 2", basedOn: "Normal", next: "Normal", quickFormat: true,
        run: { font: FONT, size: 28, bold: true }, paragraph: { spacing: { before: 280, after: 140 }, keepNext: true, outlineLevel: 1 } },
      { id: "Heading3", name: "Heading 3", basedOn: "Normal", next: "Normal", quickFormat: true,
        run: { font: FONT, size: 24, bold: true }, paragraph: { spacing: { before: 200, after: 100 }, keepNext: true, outlineLevel: 2 } },
    ],
  },
  numbering: {
    config: [
      { reference: "bullets", levels: [{ level: 0, format: LevelFormat.BULLET, text: "•", alignment: AlignmentType.LEFT,
        style: { paragraph: { indent: { left: 720, hanging: 360 } } } }] },
      { reference: "steps", levels: [{ level: 0, format: LevelFormat.DECIMAL, text: "%1.", alignment: AlignmentType.LEFT,
        style: { paragraph: { indent: { left: 720, hanging: 360 } } } }] },
      { reference: "refs", levels: [{ level: 0, format: LevelFormat.DECIMAL, text: "[%1]", alignment: AlignmentType.LEFT,
        style: { paragraph: { indent: { left: 720, hanging: 720 } } } }] },
    ],
  },
  sections: [
    { properties: { page: { size: { width: 11906, height: 16838 }, margin: { top: 1440, bottom: 1440, left: 1440, right: 1440 } } },
      children: [...cover, PB(), ...bonafide] },
    { properties: { page: { size: { width: 11906, height: 16838 }, margin: { top: 1440, bottom: 1440, left: 1440, right: 1440 },
        pageNumbers: { start: 1 } } },
      footers: { default: new Footer({ children: [new Paragraph({ alignment: AlignmentType.CENTER,
        children: [new TextRun({ children: [PageNumber.CURRENT], font: FONT, size: 22 })] })] }) },
      children: body },
  ],
});

const out = path.join(HERE, "..", "ML_Project_Report_Team_Cash_Guard.docx");
Packer.toBuffer(doc).then((buf) => { fs.writeFileSync(out, buf); console.log("wrote", out, Math.round(buf.length / 1024), "KB"); });
