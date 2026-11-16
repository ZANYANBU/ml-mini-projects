import json, warnings
import numpy as np, pandas as pd
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
from sklearn.linear_model import LinearRegression, HuberRegressor
from sklearn.preprocessing import PolynomialFeatures, RobustScaler
from sklearn.pipeline import make_pipeline
from sklearn.model_selection import train_test_split
warnings.filterwarnings("ignore")

R = json.load(open("results.json"))
NAVY, CREAM, RED, GREEN, TEAL, GOLD = "#254A5D", "#F7EAD9", "#C0392B", "#2C7A4B", "#1C7293", "#C8901B"
plt.rcParams.update({"font.family": "DejaVu Sans", "axes.edgecolor": "#8A8A8A",
                     "axes.labelcolor": "#2B2B2B", "text.color": "#2B2B2B",
                     "xtick.color": "#4A4A4A", "ytick.color": "#4A4A4A",
                     "axes.grid": True, "grid.color": "#DDDDDD", "grid.linewidth": .6,
                     "figure.facecolor": "white", "axes.facecolor": "white"})

PATH = ("data/CalCOFI_Database_194903-202105_csv_16October2023/"
        "CalCOFI_Database_194903-202105_csv_16October2023/194903-202105_Bottle.csv")
df = pd.read_csv(PATH, usecols=lambda c: c in ["Depthm","T_degC","Salnty","T_qual","S_qual"],
                 low_memory=False, encoding="latin-1").rename(
                 columns={"T_degC":"temp","Salnty":"sal","Depthm":"depth"}).dropna(subset=["temp","sal"])
flag = df.T_qual.notna() | df.S_qual.notna()
gate = ~(df.sal.between(30,37) & df.temp.between(-2,35))
clean = df[~flag & ~gate]

# ---------------------------------------------------------------- FIG 1 -----
fig, ax = plt.subplots(1, 2, figsize=(11, 4.1))
s = clean.sample(25000, random_state=0)
ax[0].scatter(s.sal, s.temp, s=2, c=TEAL, alpha=.25, lw=0, rasterized=True)
ax[0].set(xlabel="Salinity (PSU)", ylabel="Temperature (°C)",
          title=f"Clean archive  ·  {R['n_clean']:,} casts  ·  r = {R['corr_sal_temp']}")
bad = df[flag | gate].sample(4000, random_state=0)
ax[1].scatter(s.sal, s.temp, s=2, c="#C8CFD4", alpha=.35, lw=0, rasterized=True, label="accepted")
ax[1].scatter(bad.sal, bad.temp, s=8, c=RED, alpha=.55, lw=0, label="rejected by QC")
ax[1].set(xlabel="Salinity (PSU)", ylabel="Temperature (°C)",
          title=f"{R['n_quality_flagged']:,} QC-flagged + {R['n_gate_fail']:,} impossible")
ax[1].legend(frameon=False, fontsize=8, markerscale=2, loc="lower left")
for a in ax: a.title.set_fontsize(9.5)
fig.tight_layout(); fig.savefig("fig_data.png", dpi=190); plt.close(fig)

# ---------------------------------------------------------------- FIG 2 -----
# Loss shapes + what a 10% warm-biased fault does to each fitted curve
work = clean.sample(80000, random_state=42)
X, y = work[["sal"]].to_numpy(), work.temp.to_numpy()
X_tr, X_te, y_tr, y_te = train_test_split(X, y, test_size=.25, random_state=42)
rng = np.random.default_rng(2026); yb = y_tr.copy()
idx = rng.choice(len(yb), int(.1*len(yb)), replace=False); md = rng.integers(0,3,len(idx))
for i,m in zip(idx, md):
    if m==0: yb[i] = min(yb[i]+rng.uniform(5,14), 35)
    elif m==1: yb[i] = rng.uniform(18,26)
    else: yb[i] = min(yb[i]+rng.uniform(8,20), 35)

fig, ax = plt.subplots(1, 2, figsize=(11, 4.1))
e = np.linspace(-4, 4, 400); d = 1.35
ax[0].plot(e, e**2, color=RED, lw=2.4, label="Squared  L2  → $e^2$")
ax[0].plot(e, np.abs(e), color=TEAL, lw=2.2, ls="--", label="Absolute  L1  → $|e|$")
hub = np.where(np.abs(e)<=d, .5*e**2, d*(np.abs(e)-.5*d))
ax[0].plot(e, hub, color=GREEN, lw=2.8, label=f"Huber  δ={d}")
for v in (-d, d): ax[0].axvline(v, color="#999", ls=":", lw=1)
ax[0].set(xlabel="residual  e = t − y(x,w)", ylabel="loss", ylim=(-.3, 9),
          title="Why Huber resists outliers: linear beyond δ")
ax[0].legend(frameon=False, fontsize=8.5); ax[0].title.set_fontsize(9.5)

g = np.linspace(clean.sal.quantile(.002), clean.sal.quantile(.998), 300).reshape(-1,1)
sm = work.sample(9000, random_state=3)
ax[1].scatter(sm.sal, sm.temp, s=2.5, c="#C8CFD4", alpha=.5, lw=0, rasterized=True, label="true (clean) data")
ax[1].scatter(X_tr[idx][:1200,0], yb[idx][:1200], s=9, c=RED, alpha=.45, lw=0, label="faulty sensor rows")
for est, col, lab, ls in [(LinearRegression(), NAVY, "OLS on clean data", ":"),
                          (LinearRegression(), RED, "OLS on faulty data", "-"),
                          (HuberRegressor(epsilon=1.35, max_iter=800), GREEN, "Huber on faulty data", "-")]:
    p = make_pipeline(PolynomialFeatures(5, include_bias=False), RobustScaler(), est)
    p.fit(X_tr, y_tr if lab.endswith("clean data") else yb)
    ax[1].plot(g, p.predict(g), color=col, lw=2.6, ls=ls, label=lab)
ax[1].set(xlabel="Salinity (PSU)", ylabel="Temperature (°C)", ylim=(0, 26),
          title="10% faulty sensors drag OLS up; Huber holds the truth")
ax[1].legend(frameon=False, fontsize=7.6, markerscale=2, loc="upper right"); ax[1].title.set_fontsize(9.5)
fig.tight_layout(); fig.savefig("fig_huber.png", dpi=190); plt.close(fig)

# ---------------------------------------------------------------- FIG 3 -----
rates = np.array(R["sweep_rates"])*100
style = {"OLS  (MLE / least squares)": (RED,"-","o"), "Ridge  (MAP, Gaussian prior)": (GOLD,"--","s"),
         "Bayesian linear regression": (NAVY,"-.","^"), "RANSAC  (consensus)": (TEAL,":","d"),
         "Huber  (robust, delta=1.35)": (GREEN,"-","o")}
fig, ax = plt.subplots(1, 2, figsize=(11, 4.1))
for k,(c,ls,mk) in style.items():
    lw = 3.0 if "Huber" in k else 1.8
    ax[0].plot(rates, R["sweep_rmse"][k], color=c, ls=ls, marker=mk, ms=4.5, lw=lw, label=k.split("  ")[0])
    ax[1].plot(rates, R["sweep_bias"][k], color=c, ls=ls, marker=mk, ms=4.5, lw=lw, label=k.split("  ")[0])
ax[0].set(xlabel="% of training rows with faulty sensors", ylabel="Test RMSE (°C)",
          title="Prediction error on the clean held-out test set")
ax[1].axhline(0, color="#777", lw=1)
ax[1].set(xlabel="% of training rows with faulty sensors", ylabel="Mean prediction bias (°C)",
          title="Systematic warm bias injected into the model")
for a in ax: a.legend(frameon=False, fontsize=8, ncol=2); a.title.set_fontsize(9.5)
fig.tight_layout(); fig.savefig("fig_sweep.png", dpi=190); plt.close(fig)
print("figures written")
