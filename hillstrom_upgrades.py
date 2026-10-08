import sys, warnings
import numpy as np, pandas as pd
from scipy import stats
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import GradientBoostingClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import make_pipeline
from sklearn.model_selection import StratifiedKFold
warnings.filterwarnings("ignore")

SEED = 42
rng = np.random.default_rng(SEED)
path = "data/hillstrom.csv"
df = pd.read_csv(path)
CONTROL, MENS, WOMENS = "No E-Mail", "Mens E-Mail", "Womens E-Mail"



# ---- covariates ----

X = pd.DataFrame({
    "recency": df.recency,
    "log_history": np.log1p(df.history),
    "mens": df.mens, "womens": df.womens, "newbie": df.newbie,
    "ch_phone": (df.channel == "Phone").astype(int),
    "ch_web": (df.channel == "Web").astype(int),
    "zip_suburban": (df.zip_code == "Surburban").astype(int),
    "zip_urban": (df.zip_code == "Urban").astype(int),
})
T = df.segment.values
Tm = (T == MENS).astype(float); Tw = (T == WOMENS).astype(float)

def pr(t): print(f"\n=== {t} ===")


# ---------------------- REGRESSION ADJUSTMENT ----------------------


def ols_hc1(y, M):
    """OLS with HC1 robust standard errors."""
    n, k = M.shape
    XtX_inv = np.linalg.inv(M.T @ M)
    beta = XtX_inv @ M.T @ y
    resid = y - M @ beta
    meat = (M * resid[:, None]).T @ (M * resid[:, None])
    cov = XtX_inv @ meat @ XtX_inv * n / (n - k)
    return beta, np.sqrt(np.diag(cov))

pr("A. REGRESSION ADJUSTMENT: effect vs control, unadjusted vs covariate-adjusted (HC1 SEs)")
Xc = (X - X.mean()).values
base = np.column_stack([np.ones(len(df)), Tm, Tw])
adj = np.column_stack([base, Xc])
for outcome in ["conversion", "visit", "spend"]:
    y = df[outcome].values.astype(float)
    b0, s0 = ols_hc1(y, base)
    b1, s1 = ols_hc1(y, adj)
    for j, arm in [(1, "Mens"), (2, "Womens")]:
        vr = 1 - (s1[j] / s0[j]) ** 2
        print(f"{outcome:10s} {arm:6s} unadj={b0[j]:+.5f} (se {s0[j]:.5f})  adj={b1[j]:+.5f} (se {s1[j]:.5f})  "
              f"SE ratio={s1[j]/s0[j]:.3f}  variance reduction={vr*100:.1f}%")
        
# how much do covariates explain the outcome among controls?
ctl = (T == CONTROL)
for outcome in ["conversion", "visit", "spend"]:
    y = df.loc[ctl, outcome].values.astype(float)
    M = np.column_stack([np.ones(ctl.sum()), Xc[ctl]])
    beta = np.linalg.lstsq(M, y, rcond=None)[0]
    r2 = 1 - ((y - M @ beta) ** 2).sum() / ((y - y.mean()) ** 2).sum()
    print(f"R^2 of covariates on {outcome} (control group) = {r2:.4f}")

# ---------------------- B. UPLIFT TARGETING ----------------------
def make_models():
    return {
        "logistic": lambda: make_pipeline(StandardScaler(), LogisticRegression(C=0.1, max_iter=1000)),
        "gbm": lambda: GradientBoostingClassifier(n_estimators=100, max_depth=3, learning_rate=0.05,
                                                   subsample=0.8, random_state=SEED),
    }
y_conv = df.conversion.values
scores = {m: {"mens": np.zeros(len(df)), "womens": np.zeros(len(df))} for m in make_models()}
skf = StratifiedKFold(n_splits=5, shuffle=True, random_state=SEED)
for tr, te in skf.split(X, T):
    for mname, mk in make_models().items():
        p = {}
        for arm_name, arm in [("ctrl", CONTROL), ("mens", MENS), ("womens", WOMENS)]:
            idx = tr[T[tr] == arm]
            mdl = mk().fit(X.iloc[idx], y_conv[idx])
            p[arm_name] = mdl.predict_proba(X.iloc[te])[:, 1]
        scores[mname]["mens"][te] = p["mens"] - p["ctrl"]
        scores[mname]["womens"][te] = p["womens"] - p["ctrl"]

def top_vs_rest(s, treated, y, frac=0.3):
    thr = np.quantile(s, 1 - frac)
    top = s >= thr
    def up(mask):
        t = y[mask & treated]; c = y[mask & ~treated]
        return t.mean() - c.mean()
    return up(top), up(~top), up(np.ones_like(top, dtype=bool))

pr("B1. RANKING QUALITY: does the model find customers who respond more? (out-of-fold scores, top 30% vs rest)")
print("uplift = conversion rate (email) - conversion rate (control), in percentage points")
perm_n, boot_n = 300, 500
for mname in scores:
    for arm_key, arm in [("mens", MENS), ("womens", WOMENS)]:
        mask = (T == arm) | (T == CONTROL)
        s = scores[mname][arm_key][mask]; treated = (T[mask] == arm); y = y_conv[mask]
        top, rest, overall = top_vs_rest(s, treated, y)
        obs = top - rest
        # permutation null: shuffle scores, recompute top-minus-rest
        null = []
        for _ in range(perm_n):
            sp = rng.permutation(s)
            a, b, _ = top_vs_rest(sp, treated, y); null.append(a - b)
        p = (np.sum(np.array(null) >= obs) + 1) / (perm_n + 1)
        n = len(s); bs = []
        for _ in range(boot_n):
            ii = rng.integers(0, n, n)
            a, b, _ = top_vs_rest(s[ii], treated[ii], y[ii]); bs.append(a - b)
        lo, hi = np.percentile(bs, [2.5, 97.5])
        print(f"{mname:8s} {arm[:6]:6s} top30%={top*100:+.2f}pp rest={rest*100:+.2f}pp overall={overall*100:+.2f}pp "
              f"| top-minus-rest={obs*100:+.2f}pp [{lo*100:+.2f},{hi*100:+.2f}] permutation p={p:.3f}")

pr("B2. QUINTILES of predicted uplift (logistic), actual uplift in pp [95% bootstrap CI]")
for arm_key, arm in [("mens", MENS), ("womens", WOMENS)]:
    mask = (T == arm) | (T == CONTROL)
    s = scores["logistic"][arm_key][mask]; treated = (T[mask] == arm); y = y_conv[mask]
    q = pd.qcut(s, 5, labels=False, duplicates="drop")
    for k in sorted(np.unique(q)):
        m = q == k
        d = y[m & treated].mean() - y[m & ~treated].mean()
        bs = []
        idx = np.where(m)[0]
        for _ in range(500):
            ii = rng.choice(idx, len(idx))
            bs.append(y[ii][treated[ii]].mean() - y[ii][~treated[ii]].mean())
        lo, hi = np.percentile(bs, [2.5, 97.5])
        print(f"{arm[:6]:6s} quintile {k+1} (1=lowest predicted): n={m.sum():5d} actual uplift={d*100:+.2f}pp [{lo*100:+.2f},{hi*100:+.2f}]")

# ---- policy value via inverse propensity weighting (propensity 1/3 by design) ----
def policy_value(assign, y):
    match = (T == assign)
    return 3.0 * np.mean(match * y)

def assign_best(um, uw, allow_none):
    a = np.where(um >= uw, MENS, WOMENS).astype(object)
    if allow_none:
        best = np.maximum(um, uw)
        a = np.where(best > 0, a, CONTROL).astype(object)
    return a

pr("B3. POLICY VALUE (inverse propensity weighting; per customer, two-week outcome)")
outcomes = {"conversion": df.conversion.values.astype(float), "spend": df.spend.values.astype(float)}
policies = {
    "send nothing": np.full(len(df), CONTROL, dtype=object),
    "Mens to everyone": np.full(len(df), MENS, dtype=object),
    "Womens to everyone": np.full(len(df), WOMENS, dtype=object),
}
for mname in scores:
    um, uw = scores[mname]["mens"], scores[mname]["womens"]
    policies[f"{mname} model: better email, always send"] = assign_best(um, uw, False)
for oname, y in outcomes.items():
    print(f"-- outcome: {oname}")
    vals = {}
    for pname, a in policies.items():
        v = 3.0 * np.mean((T == a) * y); vals[pname] = v
        bs = []
        n = len(df)
        for _ in range(500):
            ii = rng.integers(0, n, n)
            bs.append(3.0 * np.mean((T[ii] == a[ii]) * y[ii]))
        lo, hi = np.percentile(bs, [2.5, 97.5])
        unit = 100 if oname == "conversion" else 1
        suffix = "%" if oname == "conversion" else ""
        pre = "" if oname == "conversion" else "$"
        print(f"   {pname:46s} {pre}{v*unit:.3f}{suffix} [{lo*unit:.3f},{hi*unit:.3f}]  share assigned Mens/Womens: "
              f"{(a==MENS).mean()*100:.0f}%/{(a==WOMENS).mean()*100:.0f}%")
        
    # paired bootstrap: model vs Mens-to-everyone
    for pname in [k for k in policies if "model" in k]:
        a = policies[pname]; b = policies["Mens to everyone"]
        diffs = []
        for _ in range(1000):
            ii = rng.integers(0, len(df), len(df))
            diffs.append(3.0 * np.mean(((T[ii] == a[ii]).astype(float) - (T[ii] == b[ii]).astype(float)) * y[ii]))
        lo, hi = np.percentile(diffs, [2.5, 97.5])
        unit = 100 if oname == "conversion" else 1
        print(f"   {pname} minus Mens-to-everyone = {np.mean(diffs)*unit:+.3f} [{lo*unit:+.3f},{hi*unit:+.3f}]")