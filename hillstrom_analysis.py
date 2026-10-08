import sys
import numpy as np, pandas as pd
from scipy import stats

rng = np.random.default_rng(42)
path = "data/hillstrom.csv"
df = pd.read_csv(path)
CONTROL, ARMS = "No E-Mail", ["Mens E-Mail", "Womens E-Mail"]
ctrl = df[df.segment == CONTROL]

def pr(title): print(f"\n=== {title} ===")

# ---------- 1. Descriptives ----------


pr("DESCRIPTIVES (all customers)")
for c in ["recency", "history", "spend"]:
    s = df[c]
    print(f"{c}: mean={s.mean():.3f} median={s.median():.3f} sd={s.std():.3f} "
          f"iqr={s.quantile(.75)-s.quantile(.25):.3f} min={s.min():.2f} max={s.max():.2f} "
          f"skew={stats.skew(s):.2f} excess_kurt={stats.kurtosis(s):.2f}")
print(f"visit rate={df.visit.mean():.4f}  conversion rate={df.conversion.mean():.4f}  "
      f"zero-spend share={(df.spend==0).mean():.4f}")
buyers = df[df.conversion == 1]
print(f"buyers: n={len(buyers)} mean spend={buyers.spend.mean():.2f} median={buyers.spend.median():.2f} "
      f"max={buyers.spend.max():.2f}; top 1% of buyers' share of spend={buyers.spend.nlargest(max(1,len(buyers)//100)).sum()/df.spend.sum():.3f}")
print("\nspend vs history: spearman=%.3f pearson=%.3f" % (stats.spearmanr(df.history, df.spend)[0], df.history.corr(df.spend)))
print("recency vs conversion: spearman=%.3f" % stats.spearmanr(df.recency, df.conversion)[0])
print("history vs conversion: spearman=%.3f" % stats.spearmanr(df.history, df.conversion)[0])
print("history skew raw=%.2f, log1p=%.2f" % (stats.skew(df.history), stats.skew(np.log1p(df.history))))

# ---------- 2. Journey funnel (descriptive only) ----------


pr("FUNNEL (descriptive, by arm)")
g = df.groupby("segment").agg(n=("visit","size"), visit=("visit","mean"), conv=("conversion","mean"), spend=("spend","mean"))
g["conv_given_visit"] = df[df.visit==1].groupby("segment").conversion.mean()
print(g.round(4))

# ---------- 3. Tests vs control ----------


def prop_test(a, b):
    p1, p2, n1, n2 = a.mean(), b.mean(), len(a), len(b)
    d = p1 - p2
    se = np.sqrt(p1*(1-p1)/n1 + p2*(1-p2)/n2)
    pool = (a.sum()+b.sum())/(n1+n2)
    se0 = np.sqrt(pool*(1-pool)*(1/n1+1/n2))
    z = d/se0
    p = 2*(1-stats.norm.cdf(abs(z)))
    return d, d-1.96*se, d+1.96*se, p

def holm(ps):
    order = np.argsort(ps); m = len(ps); adj = np.empty(m); run = 0
    for rank, i in enumerate(order):
        run = max(run, (m-rank)*ps[i]); adj[i] = min(1, run)
    return adj

pr("CONVERSION and VISIT vs No E-Mail (absolute differences, 95% CI, Holm-adjusted p)")
for metric in ["conversion", "visit"]:
    rows = []
    for arm in ARMS:
        t = df[df.segment == arm][metric]
        d, lo, hi, p = prop_test(t, ctrl[metric])
        rows.append((arm, t.mean(), ctrl[metric].mean(), d, lo, hi, p))
    adj = holm(np.array([r[-1] for r in rows]))
    for r, a in zip(rows, adj):
        rel = r[3]/r[2]
        print(f"{metric:10s} {r[0]:14s} arm={r[1]:.4f} ctrl={r[2]:.4f} diff={r[3]*100:+.2f}pp "
              f"[{r[4]*100:+.2f},{r[5]*100:+.2f}] rel_lift={rel*100:+.1f}% p={r[6]:.2g} holm_p={a:.2g}")

pr("SPEND per customer vs No E-Mail (Welch p, bootstrap 95% CI, 5000 resamples)")
B = 5000
spend_res = {}
for arm in ARMS:
    t = df[df.segment == arm].spend.values; c = ctrl.spend.values
    d = t.mean() - c.mean()
    boots = np.array([rng.choice(t, len(t)).mean() - rng.choice(c, len(c)).mean() for _ in range(B)])
    lo, hi = np.percentile(boots, [2.5, 97.5])
    p = stats.ttest_ind(t, c, equal_var=False).pvalue
    spend_res[arm] = (d, lo, hi, p)
adjs = holm(np.array([v[3] for v in spend_res.values()]))
for (arm, (d, lo, hi, p)), a in zip(spend_res.items(), adjs):
    print(f"{arm:14s} mean={df[df.segment==arm].spend.mean():.3f} ctrl={ctrl.spend.mean():.3f} "
          f"diff=${d:+.3f} [{lo:+.3f},{hi:+.3f}] welch_p={p:.2g} holm_p={a:.2g}  "
          f"=> incremental revenue per 1,000 emails = ${d*1000:,.0f} [{lo*1000:,.0f},{hi*1000:,.0f}]")

pr("MENS vs WOMENS (secondary)")
a = df[df.segment=="Mens E-Mail"]; b = df[df.segment=="Womens E-Mail"]
d, lo, hi, p = prop_test(a.conversion, b.conversion)
print(f"conversion diff={d*100:+.2f}pp [{lo*100:+.2f},{hi*100:+.2f}] p={p:.2g}")
print(f"spend diff=${a.spend.mean()-b.spend.mean():+.3f} welch_p={stats.ttest_ind(a.spend,b.spend,equal_var=False).pvalue:.2g}")

# ---------- 4. Power / MDE ----------


pr("POWER / MINIMUM DETECTABLE EFFECT (alpha=0.025 two-sided per comparison, power=0.8)")
za, zb = stats.norm.ppf(1-0.025/2), stats.norm.ppf(0.8)
n = len(ctrl)
for metric in ["visit", "conversion"]:
    p0 = ctrl[metric].mean()
    mde = (za+zb)*np.sqrt(2*p0*(1-p0)/n)
    print(f"{metric}: control rate={p0:.4f}  MDE={mde*100:.2f}pp absolute ({mde/p0*100:.1f}% relative) at n={n} per arm")
sd = ctrl.spend.std()
mde_s = (za+zb)*sd*np.sqrt(2/n)
print(f"spend: control mean={ctrl.spend.mean():.3f} sd={sd:.2f}  MDE=${mde_s:.3f} ({mde_s/ctrl.spend.mean()*100:.1f}% relative)")
print("coefficient of variation: spend=%.1f, conversion=%.1f, visit=%.1f" % (
    df.spend.std()/df.spend.mean(),
    np.sqrt(df.conversion.mean()*(1-df.conversion.mean()))/df.conversion.mean(),
    np.sqrt(df.visit.mean()*(1-df.visit.mean()))/df.visit.mean()))


# sample size needed to detect a practically meaningful +0.3pp conversion lift
for lift in [0.002, 0.003, 0.005]:
    p0 = ctrl.conversion.mean(); p1 = p0 + lift
    need = ((za+zb)**2 * (p0*(1-p0)+p1*(1-p1))) / lift**2
    print(f"n per arm needed to detect +{lift*100:.1f}pp conversion: {need:,.0f}")

# ---------- 5. Hybrid metric: profit per 1,000 emails at illustrative costs ----------


pr("HYBRID: PROFIT PER 1,000 EMAILS = incremental revenue - email cost (illustrative costs; margin ignored)")
for arm in ARMS:
    d, lo, hi, _ = spend_res[arm]
    for cost in [0.01, 0.05, 0.10]:
        print(f"{arm:14s} cost=${cost:.2f}/email: profit/1000 = ${(d-cost)*1000:,.0f} [{(lo-cost)*1000:,.0f},{(hi-cost)*1000:,.0f}]")
    print(f"{arm:14s} break-even email cost (point estimate) = ${d:.3f} per email")

# ---------- 6. Pre-specified segments (exploratory) ----------


pr("SEGMENTS (pre-specified, EXPLORATORY): conversion lift vs control, pp [95% CI]")
def seg_table(col):
    out = []
    for lvl, sub in df.groupby(col):
        c = sub[sub.segment == CONTROL].conversion
        for arm in ARMS:
            t = sub[sub.segment == arm].conversion
            d, lo, hi, p = prop_test(t, c)
            out.append((col, lvl, arm.split()[0], len(t), d*100, lo*100, hi*100, p))
    return out
rows = []
for col in ["newbie", "channel", "history_segment", "mens", "womens"]:
    rows += seg_table(col)
seg = pd.DataFrame(rows, columns=["var","level","arm","n","lift_pp","lo","hi","p"])
seg["holm_p"] = holm(seg.p.values)
print(seg.round(3).to_string(index=False))
print(f"\nsegment comparisons run: {len(seg)}; nominal p<0.05: {(seg.p<0.05).sum()}; after Holm: {(seg.holm_p<0.05).sum()}")

# ---------- 7. Peeking: A/A simulation ----------


pr("PEEKING: A/A simulation (no true effect), 10 interim looks, 2000 simulations")
p0 = ctrl.conversion.mean(); N = 20000; looks = np.linspace(N/10, N, 10).astype(int)
fp_peek = 0; fp_final = 0; sims = 2000
for _ in range(sims):
    a = rng.random(N) < p0; b = rng.random(N) < p0
    sig_any = False
    for k in looks:
        pa, pb = a[:k].mean(), b[:k].mean(); pool = (a[:k].sum()+b[:k].sum())/(2*k)
        se = np.sqrt(pool*(1-pool)*2/k)
        if se > 0 and abs(pa-pb)/se > 1.96: sig_any = True
        if k == N: fp_final += (se > 0 and abs(pa-pb)/se > 1.96)
    fp_peek += sig_any
print(f"false positive rate if you stop at the first 'significant' look: {fp_peek/sims*100:.1f}%")
print(f"false positive rate with one pre-planned look at the end: {fp_final/sims*100:.1f}%")
