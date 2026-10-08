# Hillstrom Email Experiment: Analysis and Decision Memo

## 1. Summary and Decision

**Question.** Did a Mens or Womens merchandise email increase purchases among 64,000 recent customers, compared with sending nothing? Customers were randomly split into three equal arms, and outcomes were tracked for two weeks.

**Answer.** Yes for both emails, and the Mens email did better. Primary metric: conversion rate. All differences are against the No E-Mail arm, with 95% intervals.

| Metric | No email | Mens email | Womens email |
| --- | --- | --- | --- |
| Conversion (primary) | 0.57% | 1.25%, +0.68 pp \[0.50, 0.86\] | 0.88%, +0.31 pp \[0.15, 0.47\] |
| Site visit | 10.6% | 18.3%, +7.66 pp \[7.00, 8.32\] | 15.1%, +4.52 pp \[3.89, 5.16\] |
| Spend per customer | $0.65 | $1.42, +$0.77 \[0.48, 1.05\] | $1.08, +$0.42 \[0.17, 0.69\] |
| Incremental revenue per 1,000 emails |  | $770 \[$479, $1,049\] | $424 \[$166, $694\] |

**Decision.** Send both; the Mens email is stronger. Whether each is worth sending depends on email cost and margin, which the data does not contain. On revenue alone, break-even is about $0.77 (Mens) and $0.42 (Womens) per email. A targeting model found no gain over sending the Mens email to everyone.

## 2. Success Metrics

A good success metric is **measurable** (we can observe it), **attributable** (the change can be traced to the treatment), **sensitive** (low variability, so real effects show up), and **timely** (visible in the test window). Metrics trade off against each other, so one is chosen as primary and the others are secondary.

| Metric | Role | Sensitive? | Timely? | Trade-off |
| --- | --- | --- | --- | --- |
| Site visit | Secondary, proxy | High (coefficient of variation 2.4) | Yes | Visits don't pay the bills |
| Conversion | **Primary** | Medium (10.5) | Yes | Ignores order size |
| Spend per customer | Secondary, revenue | Low (14.3) | Yes | Closest to value, but 99.1% of values are zero |
| Profit per customer (spend minus email cost) | Hybrid decision metric | Low | Yes | Needs a cost and margin assumption |

**Proxy metrics.** Visit is a proxy for conversion, and conversion is a proxy for spend. Proxies are more sensitive and faster, but a proxy can move without revenue moving, so they should support the revenue conclusion and not replace it.

**Hybrid (holistic) metric.** Profit per customer combines engagement and money in one number: revenue per customer minus the cost of the email. It is the metric the send-or-don't-send decision actually rests on.

**User-to-purchase journey.** Email sent, delivered, opened, clicked, site visit, purchase, spend. Only the last three are in the data. The analysis is by assignment (intent-to-treat), not by who opened, so it doesn't depend on a post-treatment behavior.

**Edge cases.** Spend per buyer and visit-to-purchase rate look informative but condition on an outcome that the email itself changed, so they are descriptive only. Unsubscribes and complaints are important guardrails and are not in this data.

## 3. Experiment Design

**Hypotheses.** Null: the email does not change the conversion rate. Alternative: it does. Tested separately for the Mens and Womens emails, each against no email.

**Significance and power.** 5% overall significance, with a Holm correction because two emails are tested against the same control. Power set at 80% (a 20% chance of missing a real effect of the minimum detectable size).

| Design element | Choice |
| --- | --- |
| Randomization unit | The customer |
| Target population | Customers who purchased within the last 12 months (not new prospects or lapsed customers) |
| Sample size | 64,000, about 21,300 per arm |
| Duration | Two weeks of outcomes after the send, fixed in advance |

**Sample size and practical significance.** At 21,306 customers per arm, the smallest effect the test could reliably detect is 0.23 pp on conversion (39% relative), 0.92 pp on visits (8.7% relative), and $0.35 on spend per customer (53% relative). The Womens email's conversion lift (+0.31 pp) is above that threshold but not by much. Detecting +0.2 pp would need about 31,700 customers per arm. Statistical significance only says an effect is unlikely to be zero. Practical significance asks whether it is large enough to matter, here whether incremental revenue exceeds the cost of sending.

## 4. Validity Checks

Results are only trustworthy if the experiment itself was sound. Checks were run before looking at any outcomes.

| Check | Result |
| --- | --- |
| **No sample ratio mismatch** (chi-square test of arm sizes against an equal split) | Arms of 21,306 / 21,307 / 21,387; p = 0.90. Pass |
| **Sanity checks** (pre-experiment columns balanced across arms) | Eight covariates compared; all differences under 0.01 standard deviations, p from 0.36 to 0.93. Pass |
| **Instrumentation** | Cannot be verified from the data. Risk: if visits or purchases are logged differently in email arms than in the control, the lift would be partly measurement |
| **External factors** | One campaign in one window. Seasonality and concurrent promotions are unknown |
| **Selection bias** | Population is recent purchasers, so results don't transfer to new or lapsed customers. Analysis is by assignment, not by who opened the email |
| **Novelty effect** | One send, two weeks. Novelty and repeat-send fatigue can't be separated from the real effect |

**Avoiding peeking at p-values.** Checking results repeatedly and stopping at the first significant one inflates false positives. In an A/A simulation with no true effect and 10 interim looks, 18.9% of runs stopped on a false "win", compared with 4.2% with one pre-planned look at the end. The fix is to fix the sample size and duration in advance, or use a sequential method designed for repeated looks.

## 5. Descriptive Statistics

| Variable | Mean | Median | Std. dev. | Skew | Reading |
| --- | --- | --- | --- | --- | --- |
| Recency (months since last purchase) | 5.76 | 6 | 3.51 | 0.1 | Roughly symmetric |
| History (past spend, $) | 242 | 158 | 256 | 2.4 | Right-skewed; log transform makes it symmetric |
| Spend (two-week, $) | 1.05 | 0 | 15.04 | 20.6 | Extremely skewed: 99.1% of customers spent nothing |

**Central tendency.** For spend, the mean ($1.05) and median ($0) tell different stories. The median hides the buyers and the mean is driven by a few, so both are reported with the share of zeros.

**Dispersion.** Spend has a standard deviation about 14 times its mean, which is why revenue is the least sensitive metric and needs a bootstrap interval. Among the 578 buyers, spend averages $116 (median $81, maximum $499), and the top 1% of buyers account for 3.7% of all spend, so the result is not driven by a few large orders.

**Correlation.** Past spend is only weakly related to two-week spend (Spearman 0.025), and recency is only weakly related to conversion (-0.025). The covariates barely predict purchase, which is part of why regression adjustment adds little here.

**Normal distribution.** Spend and history are far from normal. The tests don't need them to be: the difference in means between arms of about 21,000 is approximately normal by the central limit theorem. A bootstrap on spend serves as a cross-check, and agrees with the standard test.

## 6. Results

Conversion and visit use a two-proportion z-test; spend uses a Welch test with a 5,000-resample bootstrap interval. P-values are adjusted with Holm for the two comparisons against the control.

| Comparison with no email | Metric | Difference | 95% interval | Adjusted p |
| --- | --- | --- | --- | --- |
| Mens | Conversion | +0.68 pp | \[0.50, 0.86\] | 3e-13 |
| Womens | Conversion | +0.31 pp | \[0.15, 0.47\] | 0.00016 |
| Mens | Visit | +7.66 pp | \[7.00, 8.32\] | below 0.0001 |
| Womens | Visit | +4.52 pp | \[3.89, 5.16\] | below 0.0001 |
| Mens | Spend per customer | +$0.77 | \[0.48, 1.05\] | 2e-07 |
| Womens | Spend per customer | +$0.42 | \[0.17, 0.69\] | 0.0011 |

**Mens vs. Womens (secondary).** Mens beats Womens on conversion by 0.37 pp \[0.17, 0.56\], p = 0.0002. On spend the gap is $0.35 with an unadjusted p of 0.03, which I would treat as suggestive and not settled.

**Segments (exploratory).** Four pre-specified variables (new vs. existing customer, channel, past spend band, and prior Mens or Womens purchase) were checked for conversion lift. The Mens email had a positive point estimate in every segment. The Womens email's lift was concentrated among customers who had previously bought women's merchandise (+0.51 pp vs. +0.06 pp for those who hadn't) and among new customers, and near zero for some higher-spend bands. These are 32 subgroup comparisons: 23 were nominally significant and 15 survived correction, so treat them as hypotheses to test, not conclusions. Section 10 checks whether they hold up out of sample, and they do not.

## 7. Interpretation and Recommendation

**In business terms.** Both emails raise purchases beyond what would have happened anyway, since the control group is the baseline. The Mens email roughly doubles conversion (0.57% to 1.25%), and the Womens email raises it by about half. The hybrid decision metric turns this into a send-or-don't-send rule: send if incremental revenue per email, times the margin, exceeds the cost of the email.

| Illustrative cost per email | Mens profit per 1,000 emails | Womens profit per 1,000 emails |
| --- | --- | --- |
| $0.01 | $760 \[469, 1,039\] | $414 \[156, 684\] |
| $0.05 | $720 \[429, 999\] | $374 \[116, 644\] |
| $0.10 | $670 \[379, 949\] | $324 \[66, 594\] |

These costs are examples, not data, and the table counts revenue as profit. With an illustrative 30% margin, the revenue break-even drops to roughly $0.23 per email for Mens and $0.13 for Womens. The lower end of the Womens interval is the number to watch.

**Recommendation.**

1. Send the Mens email to the full recent-customer base.
2. Send the Womens email as a second option. Don't build targeting on these features: out-of-sample uplift models did not beat sending the Mens email to everyone (section 10).
3. Before scaling, measure unsubscribe and complaint rates, which this data lacks.
4. Run a follow-up with a longer window to see whether the effect lasts or reflects novelty.

**Limits.** Two weeks, one campaign, one customer group, and data from 2008. No cost or margin data. Subgroup patterns are exploratory. Revenue is noisy, so its intervals are wide (the Womens email's spend interval runs from $0.17 to $0.69).

## 8. Product-Experiment Notes Beyond This Dataset

These points come up in real product experiments but can't be shown with this data, so they are explained here, not measured.

- **Latency and rendering flaws.** A new feature can be slower to render, so the treatment group loses engagement because of load time and not because of the feature's content. Add latency and error rate as guardrail metrics, compare them across arms, and check that logging fires the same way in both. A slower treatment can also change how events are recorded, which is an instrumentation effect.
- **Same reward, different delivery.** A $10 store credit and a $10 gift card have the same face value but different redemption friction, expiry, and spending behavior. Treat each delivery method as its own arm, and measure redemption and downstream spend, not the nominal reward value.
- **Interim looks.** I read "interim groups" as interim analyses, meaning looking at results before the planned end. As the simulation in section 4 shows, doing this carelessly inflates false positives from about 4% to 19%. Use a fixed horizon, or a group-sequential method that spends the significance level across planned looks.
- **Hybrid metrics.** A single overall evaluation criterion (here, profit per customer) keeps teams from optimizing a proxy such as clicks or visits at the expense of revenue.

## 9. Upgrade: Covariate Adjustment (Variance Reduction)

**Idea.** In a randomized test, adding pre-experiment covariates to the regression can shrink the standard error of the treatment effect without changing what it estimates. The size of the gain depends on how well the covariates predict the outcome. Covariates used: recency, log of past spend, prior Mens and Womens purchase, new-customer flag, channel, and zip type, with robust standard errors.

| Outcome | Treatment effect (unadjusted vs. adjusted) | Standard error ratio | Variance reduction |
| --- | --- | --- | --- |
| Conversion, Mens | +0.681 pp vs. +0.679 pp | 0.999 | 0.2% |
| Conversion, Womens | +0.311 pp vs. +0.313 pp | 0.999 | 0.1% |
| Visit, Mens | +7.66 pp vs. +7.62 pp | 0.986 | 2.8% |
| Visit, Womens | +4.52 pp vs. +4.55 pp | 0.987 | 2.5% |
| Spend, Mens | +$0.770 vs. +$0.769 | 0.999 | 0.2% |
| Spend, Womens | +$0.424 vs. +$0.428 | 1.001 | none |

**Finding.** The adjustment barely helps. The covariates explain only 0.2% of the variation in conversion, 0.1% in spend, and 3% in visits among control customers, so there is almost nothing to remove. The point estimates also don't move, which is the expected result in a clean randomization and a useful extra check on the balance tests.

**Why it matters.** Variance reduction is worth the effort when a strong pre-period version of the outcome exists (for example, last month's spend predicting this month's). Here the only history is total past spend, a weak predictor of a two-week purchase. The unadjusted analysis in section 6 stands.

## 10. Upgrade: Can We Target Better Than "Send Mens to Everyone"?

**Question.** The segment tables in section 6 hinted that some customers respond more. Could a model pick the right email for each customer and beat the simple rule?

**Method.** A two-model uplift approach: for each arm, a model predicts the chance of converting from the covariates, and a customer's predicted uplift is the difference between an email arm and the control arm. Two model types were used, logistic regression and gradient boosting. Scores were **cross-fitted** with 5 folds, so every customer's score comes from a model that never saw them. Because assignment was random, the scores can be checked honestly in two ways.

**Check 1: does the ranking find responders?** Compare actual uplift among the top 30% by predicted uplift with the rest.

| Model and email | Top 30% | Rest | Top minus rest \[95% interval\] | Permutation p |
| --- | --- | --- | --- | --- |
| Logistic, Mens | +0.75 pp | +0.65 pp | +0.09 pp \[-0.34, +0.53\] | 0.30 |
| Logistic, Womens | +0.31 pp | +0.31 pp | -0.01 pp \[-0.41, +0.37\] | 0.53 |
| Gradient boosting, Mens | +0.59 pp | +0.72 pp | -0.14 pp \[-0.56, +0.31\] | 0.74 |
| Gradient boosting, Womens | +0.43 pp | +0.26 pp | +0.17 pp \[-0.21, +0.52\] | 0.19 |

No model separates responders from non-responders. Actual uplift by predicted-uplift quintile (logistic) is flat for the Mens email (0.40 to 0.83 pp across quintiles, with overlapping intervals) and non-monotonic for the Womens email.

**Check 2: policy value.** Because each customer had a 1 in 3 chance of each arm, the value of any rule can be estimated by inverse propensity weighting, using only customers whose random email matched what the rule would have sent.

| Policy | Conversion | Spend per customer |
| --- | --- | --- |
| Send nothing | 0.57% | $0.65 |
| Mens to everyone | 1.25% | $1.42 |
| Womens to everyone | 0.89% | $1.08 |
| Logistic model picks the email | 1.26% | $1.46 |
| Gradient boosting model picks the email | 1.24% | $1.42 |

Model minus Mens-to-everyone: logistic +0.006 pp \[-0.084, +0.084\] on conversion and +$0.04 \[-0.07, +0.15\] on spend; gradient boosting -0.012 pp \[-0.103, +0.075\] and -$0.00 \[-0.14, +0.12\]. Neither is distinguishable from zero.

**Finding.** With these covariates, targeting adds nothing measurable over sending the Mens email to everyone. The Womens-buyer pattern from the segment tables did not become an out-of-sample gain, which is what the warning about subgroup fishing predicted.

**Caveats.** This is a null result, not proof that all customers respond alike. The control arm has only about 120 conversions, so the test has little power to detect modest differences in response. The policy estimates use only a third of customers each, so they are noisy. A larger experiment, or stronger pre-period data, could change the answer.

**Decision.** Don't build a targeting system on these features. Send the Mens email to everyone, and treat the Womens email as a second option to test further.
