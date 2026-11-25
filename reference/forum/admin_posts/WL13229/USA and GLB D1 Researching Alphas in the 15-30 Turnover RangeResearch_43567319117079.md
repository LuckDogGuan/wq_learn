# USA and GLB D1: Researching Alphas in the 15-30% Turnover RangeResearch

- **链接**: https://support.worldquantbrain.com/hc/zh-cn/community/posts/43567319117079
- **作者**: WL13229
- **发布时间/热度**: 13天前, 得票: 60

## 帖子正文

**Working on the USA/D1 or GLB/D1 turnover-gap theme?**  Start with a question about information, not a decay setting:  **what changes in your data, why might that change predict returns, and how long should the effect last?**

**The aim**

Research useful signals in the theme's  **15–30% turnover range**  without adding unnecessary trading. This range is a research target — not a claim that every Alpha inside it is profitable, or that Alphas outside it are inferior. Check your current theme details for eligible settings and the platform's exact matching rules.

Below are dataset starting points, two illustrative expressions, and a practical workflow for evaluating them.  *The expressions have not been backtested for this article and are not submission-ready recommendations.*

## 01 | Separate turnover from signal horizon

Turnover describes trading activity;  **PnL Realization Horizon**  describes how quickly positions capture predictive returns. They are related, but not interchangeable. A frequently changing signal can still earn most of its returns over a longer horizon — or trade without adding useful information.

For example, a news-driven hypothesis might predict a brief reaction after new information arrives. An estimate-revision hypothesis might predict a more persistent adjustment. Use the available horizon diagnostics to ask whether the results  *fit the hypothesis* , rather than assuming that a shorter lookback creates a shorter-lived opportunity.

**Important:**  The turnover-gap theme and the High Turnover classifications are different. Do not import a classification's turnover or horizon conditions into your cohort's eligibility rules unless the active theme explicitly requires them.

## 02 | Choose data with a reason to change

In  [Data Explorer](https://platform.worldquantbrain.com/data) , set the region, Delay 1, and your intended universe before searching a dataset ID. Check the field description, type, coverage, and availability in your account. A dataset with frequent source updates does not necessarily provide new information for every stock every day, and intraday source data does not remove the simulation's D1 timing requirements.

The following BRAIN datasets and example fields were returned in USA/D1/TOP3000 or GLB/D1/TOPDIV3000 searches. These are research contexts, not additional theme restrictions. Availability and fields can differ when you change context.

Region checked
Search in Data Explorer
Example fields
Research question

USA

 `news18`  — Ravenpack News Data

 `rp_ess_earnings` ,  `rp_css_earnings` 

Does the tone of earnings news contain information beyond its recent history?

USA

 `news54`  — Key Developments Data
 `daily_event_announcement_time_utc` 
Does a recently announced corporate event change how a separate directional signal behaves?

USA

 `socialmedia12`  — Sentiment Data for Equity

 `scl12_sentiment` ,  `scl12_buzz` 

Are changes in sentiment more informative when attention is unusually high?

GLB

 `analyst4`  — Analyst Estimate Data for Equity
 `anl4_fs_detail_estimates_basic_qf_v4_nd_eps_median` 
Do changes in EPS estimates predict returns after accounting for their forecast period and timing?

GLB

 `insider_agg_matrix`  — Smart Insider Transaction Aggregates

 `total_top_buy_shares` ,  `total_top_sell_shares` 

Does newly disclosed executive buying or selling add information relative to a company's usual activity?

**News and corporate events:**  Distinguish a new announcement from a repeated story or an updated record. The  `news54`  timestamp example is a  **VECTOR**  field, not a directional sentiment score. Understand timestamp units and event alignment before aggregating it; averaging unrelated event times is not a meaningful signal.

**Sentiment and attention:**  The sentiment and buzz examples are MATRIX fields. Treat buzz as an attention measure, not a bullish signal by itself. Higher attention can accompany either continuation or reversal; those are different hypotheses, not interchangeable signs to choose after seeing results.

**Analyst estimates:**  Keep the forecast period consistent. A jump caused by rolling from one fiscal period to another is not necessarily an analyst revision. Check currency, accounting basis, and publication timing before comparing estimates. Adding estimate dispersion may help test an agreement hypothesis, but it also changes coverage and requires its own validation.

**Disclosed insider transactions:**  Check disclosure availability rather than assuming the trade date was observable. Determine whether the field is a daily flow or a rolling aggregate, and what missing values mean. A change in a rolling total can reflect old trades leaving the window, not new trades arriving. Sparse activity can also leave too few instruments with useful signals.

## 03 | Start with a simple, explainable baseline

The numeric windows below illustrate a construction, not an optimized setting. Inspect missing values and field semantics first. Do not automatically convert missing observations to zero or backfill a short-lived event for months.

### USA example: a change in sentiment

**Hypothesis:**  A recent change in sentiment may contain information not already captured by its level.

`change = ts_delta(scl12_sentiment, 3);` 
 `rank(change)`

This compares each instrument's sentiment with its value three trading days earlier, then ranks the changes across the universe. The positive direction tests whether improving sentiment predicts higher subsequent returns. That hypothesis is not established by the field description and needs testing.

If the baseline is promising but trades excessively, compare a separate smoothed version:

`change = ts_delta(scl12_sentiment, 3);` 
 `ts_decay_linear(rank(change), 4)`

The second expression smooths the ranked signal over four days. It may reduce responsiveness as well as turnover. Keep simulation decay and other settings fixed when making this comparison, so you can attribute the difference to the expression-level change.

In the default sparse mode ( `dense=false` ), the decay operator treats missing inputs as zero. Since valid ranks are between 0 and 1, missing values can pull the smoothed signal toward the low-ranked end. Check whether this treatment is meaningful for the field; changing the mode alone does not resolve the meaning of missing observations.

A useful follow-up question is whether  `scl12_buzz`  distinguishes informative changes from ordinary fluctuations. Add that condition only after the simple baseline is understood, and compare coverage before and after the change.

### GLB example: estimate changes relative to their own history

**Hypothesis:**  An unusually positive change in EPS estimates may indicate improving expectations.

After confirming a comparable forecast period and the absence of mechanical period-roll jumps, examine:

`estimate = anl4_fs_detail_estimates_basic_qf_v4_nd_eps_median;` 
 `revision = ts_delta(estimate, 5);` 
 `ts_rank(revision, 60)`

The five-day change measures movement in the estimate. The time-series rank compares that change with the same instrument's recent history rather than directly ranking raw currency-denominated EPS changes across countries.

This normalization does  **not**  fix currency changes, forecast-period rolls, stale data, or a small number of updates. Repeated zero changes can create many ties. Inspect those cases before treating the output as evidence of fresh information.

For GLB, inspect results by geography and country via visualization tool. Country-relative normalization or country neutralization can be separate, economically motivated comparisons, but neither guarantees broad performance. Do not add country-specific exceptions just to rescue one backtest.

## 04 | Adjust trading only after understanding the signal

What you observe
What to investigate
A controlled next experiment

Turnover below 15%
Is the data mostly stale, or have you over-smoothed a genuinely responsive signal?
Shorten one smoothing window, or test a revision/change feature that matches the idea. Do not add noise to force activity.

Turnover above 30%
Is the signal reacting to small fluctuations, outliers, or coverage changes?
Compare modestly longer decay or  `hump` , changing one control at a time.

Turnover in range, weak performance
Does the information actually predict returns at D1?
Revisit the mechanism, timing, and data quality instead of optimizing turnover further.

Good aggregate results, weak liquid-universe results
Are a few less-liquid names carrying the result?
Check concentration and more-liquid-universe performance before adding complexity.

Good GLB results, weak regional results
Is coverage or PnL dominated by one geography?
Inspect AMR, ASI separately, including coverage and the applicable platform checks.

`trade_when`  is another option when the hypothesis has a meaningful update and exit rule. It can hold the previous Alpha value between updates; it is not equivalent to setting the signal to zero on inactive days. An indefinite hold can preserve stale information, and subsequent portfolio processing can still change final weights. Design the exit behavior explicitly.

Ranking controls the cross-sectional scale; it does not guarantee lower turnover. Neutralization can also raise or lower turnover. Always inspect the final simulation results after the complete expression and settings have been applied.

## 05 | Run a small experiment you can explain

**1. Write the hypothesis first.** 
Identify the information event, expected direction, and likely persistence. Record what would falsify the idea.

**2. Check the data.** 
Inspect missingness, update frequency, outliers, and coverage. In GLB, repeat the coverage check by geography. Do not confuse populated values with fresh observations.

**3. Run the simple baseline.** 
Record the complete settings and results, including turnover, Sharpe, Fitness, margin, concentration, and applicable tests.

**4. Change one control.** 
For example, compare the baseline with two nearby smoothing windows while leaving the universe and neutralization unchanged. Look for a reasonably stable pattern, not one isolated winning parameter.

**5. Review robustness.** 
Inspect yearly results, liquid-universe behavior, and available cost-aware or investability diagnostics. Margin is useful context, not a substitute for a transaction-cost model. A separate smaller-universe simulation is also not identical to the platform's sub-universe test.

**6. Check the final candidate.** 
Re-run the applicable consultant submission checks and confirm current theme matching. The target turnover range does not waive Sharpe, Fitness, correlation, concentration, or regional requirements.

Use turnover across the full simulation as a diagnostic and review yearly variation as well; a stable full-period average can hide very different trading behavior across years. For theme eligibility, use the statistic and endpoint rules specified by the platform, not a rounded value or an assumed inclusive boundary.

One detail worth reading in  **Consultant Submission Tests** : the documentation describes a turnover-below-30% adjustment to IS Sharpe Ladder  *pass*  thresholds, not the fail threshold. This is separate from cohort eligibility. Consult the current documentation and actual check results rather than treating 30% as a universal submission shortcut.

## Before you submit

- Can you explain why the information should remain useful at Delay 1?
- Are you trading on new information rather than stale values, period rolls, or missing-data changes?
- Does the final Alpha match the theme's turnover range and eligible settings?
- Does it retain reasonable breadth and performance across years and relevant sub-universes?
- For GLB, have you reviewed geography-level results and the applicable sub-geography tests?
- Have you checked the full consultant submission results rather than only the headline metrics?

Start with one dataset and one hypothesis. A useful outcome is an experiment that explains both what the signal captures and why it trades at its observed rate, even if the first version does not qualify for submission.

 **Further reading** 

In BRAIN Learn, look for  **High Turnover Alphas** ,  **Understanding PnL Realization Horizon** ,  **Consultant Submission Tests** , and  **Investability Constrained Metrics** . Use  [Data Explorer](https://platform.worldquantbrain.com/data)  for dataset and field details, and  [Data and Operators](https://platform.worldquantbrain.com/learn/data-and-operators/operators)  for operator behavior and availability.

This article is educational material for the USA/D1 and GLB/D1 turnover-gap research theme. Dataset examples were verified in the stated search contexts at the time of writing; availability and fields may differ by account, region, universe, and delay. Illustrative expressions have not been backtested and are not submission recommendations. Theme eligibility, quotas, and submission requirements are governed by the platform's current rules.

---

## 讨论与评论 (7)

### 评论 #1 (作者: IM83681, 时间: 13天前)

Thank you very much for this teachings,I really needed it,it will help improve my alpha's.

Please can you create one on how to improve prod_correlation for IND region?

Thanks once again

---

### 评论 #2 (作者: SM35151, 时间: 12天前)

Very informative, thank you.

---

### 评论 #3 (作者: WG28617, 时间: 12天前)

Really insightful post. The idea of understanding the information and hypothesis first has really stood out for me.

---

### 评论 #4 (作者: SM47623, 时间: 12天前)

Thank you for the Information.

---

### 评论 #5 (作者: PB86281, 时间: 7天前)

Useful information

---

### 评论 #6 (作者: HY20721, 时间: 4天前)

thankyou for this information, it will improve my alphas in GLB region

---

### 评论 #7 (作者: LG66902, 时间: 4天前)

Follow this

---

