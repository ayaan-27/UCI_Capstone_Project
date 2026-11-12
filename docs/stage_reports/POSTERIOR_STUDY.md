> **Later RETRO upload:** This report describes the earlier run. See [RETRO_FOLLOWUP.md](RETRO_FOLLOWUP.md) for the newly supplied text survey and candidate-model benchmarks. The earlier unavailable-file statement is now superseded; the earlier numerical results are unchanged.

# Posterior simulation and predictive-value diagnosis

## Main finding

This is a useful **exploratory Bayesian forecasting framework**. The fixed DAG makes assumptions visible, and posterior prediction represents uncertainty. The existing data do **not** demonstrate added MAE value from all three non-grade sources beyond the larger grade bundle. **LMS alone does show a small exploratory gain when grades are absent**. MCMC validates a computation; it cannot make weak or mistimed predictors useful or establish causality.

The original `MLC_Bayesian_DAG_updated.ipynb`, its `mlc_results/`, and original presentation are preserved. The new executed notebook is `MLC_Posterior_Predictive_Value.ipynb`. The new model is a controlled outcome-CPD comparison, not a replacement claim that the whole DAG is now fully Bayesian.

## What the professor may have meant

The wording is ambiguous, but three distinct questions can be answered:

1. **Posterior coefficient probability:** given the model, prior and observed data, how probable is a positive or practically large conditional association?
2. **Posterior predictive probability:** what probability does the model assign to a student's future outcome, after integrating coefficient and residual-variance uncertainty and outcome noise?
3. **Incremental predictive value:** when a source is added, do predictions for the same later students improve? Posterior signs alone cannot answer this.

All three are now implemented. A graph with an arrow does not itself establish predictive utility. There is no posterior edge-inclusion probability here: all coefficients have continuous shrinkage priors, so the probability of an exact zero coefficient is zero by construction. A sign probability is not evidence that an edge is causal.

## Available data and the retrospective distinction

The input is `mlc_results/expanded_student_features.csv`: 191 distinct students in six ordered terms (18, 27, 43, 20, 40, 43). The processed table is already in the repository. Its SHA-256 is `7df7dcfc75aaf5d07571bfddc95d01db6c0d299e3c26ad42a6835ef9e9ff0fcb`. Raw extraction was not rerun.

- **Grades:** the existing Block A has ten aggregated scores; Block B has sixteen. Many scores are components of final percentage. Their release dates and historical revisions are not available, so these are retrospective evidence bundles, **not verified week-4 forecasts**.
- **LMS:** log(1 + page views) and log(1 + participations), aggregated over the original assumed first-four-week window. Two rows lack LMS measures. The instructional calendar remains an assumption to verify.
- **EVC-style early responses:** expectancy, value and the source `cost` field renamed `cost_support` by the original pipeline. The original code averages early WELL + SOM responses. The renaming does not establish reverse scoring, scale reliability or that a larger cost score is beneficial. Item wording and scoring should be checked against the raw questionnaire.
- **Wellness:** mean early self-report. All four survey measures are missing for 78/191 students (40.8%).
- **Separate MLC RETRO:** explicitly excluded by the original notebook, absent from the current processed table, and unavailable with the raw ZIP. **No new empirical claim is made about that separate export.** Recover it before testing retrospective responses. Responses after a forecast checkpoint may be analyzed as retrospective associations, but cannot be inputs to that earlier forecast.

## What changed mathematically

With complete predictor evidence, the original DAG outcome CPD reduces to regularized Bayesian linear regression. The other predictor arrows do not change the outcome distribution once every outcome parent is observed. A numerical regression test confirms that the new model's posterior coefficients and complete-input predictive means match the original outcome CPD (29 complete Spring 2026 rows).

For source comparisons, the new code uses training-only median filling at **both training and prediction time**, training-only centering/scaling, and a Normal–Inverse-Gamma outcome model. This provides the same missing-data interface for all sources. It differs from the original all-student inference, which marginalized missing prediction inputs using fitted joint-Gaussian parameters. Thus old and new all-student forecasts are not identical. The old pipeline remains available.

In standardized units:

```
z = A beta + epsilon, epsilon ~ Normal(0, sigma² I)
beta | sigma² ~ Normal(0, sigma² Lambda0^-1)
Lambda0 = diag(0.001, 10, ..., 10)
sigma² ~ InverseGamma(shape=2, scale=1)
L = Lambda0 + A.T @ A
m = solve(L, A.T @ z)
a = 2 + n/2
b = 1 + (z.T @ z - m.T @ L @ m)/2
```

All-student posterior predictive distributions are exact Student-t distributions **conditional on this fixed imputed design**, with `df=2a`, location `A_new @ m` and scale squared `(b/a)*(1 + A_new @ inv(L) @ A_new.T)`. Predictions are transformed back to percentage points. MAE/RMSE point predictions are clipped to [0,100]; densities and intervals use the unbounded Student-t distribution. Imputation and preprocessing uncertainty, model-selection uncertainty, ordinal measurement, term hierarchy and causal uncertainty are not integrated.

Independent posterior simulation uses 20,000 draws. Actual Gibbs MCMC uses four chains with 1,000 warmup and 4,000 retained iterations each:

```
beta | sigma²,D ~ Normal(m, sigma² inv(L))
sigma² | beta,D ~ IG(a+p/2, b + (beta-m).T @ L @ (beta-m)/2)
```

Here p includes the intercept. Cholesky solves avoid explicitly inverting matrices where practical. The exact posterior is the reference, so there is no need to rely on MCMC alone.

## Experiment design

Each model is trained on earlier terms and predicts the next term:

| Train through | Evaluate | n evaluation |
|---|---|---|
| Winter 2025 | Spring 2025 | 43 |
| Spring 2025 | Fall 2025 | 20 |
| Fall 2025 | Winter 2026 | 40 |
| Winter 2026 | Spring 2026 | 43 |

There are 146 unique later-student predictions per model. Every source comparison uses identical evaluation rows and grade features. All eight combinations of LMS, EVC and wellness are fit in three grade contexts: no grades, Block A and Block B. This gives 96 main fits. Add-one-source, combinations and remove-one-source comparisons are exported. There is no ranking-based selection of a new deployed model.

Precision 10 is inherited from the original explored workflow, whose earlier-fold results helped select it. It is fixed for these comparisons, with sensitivity runs at precisions 1 and 100, missingness indicators, and complete non-grade respondents. These settings and data are historically explored; **the results are exploratory, not an unbiased model-development or independent confirmation estimate**. No outer outcome labels enter fold-specific preprocessing. If selecting new settings, use inner earlier-term validation within each training fold; do not select them from these evaluation errors and claim the same errors as independent validation.

Macro scores weight the four evaluation terms equally. RMSE in the macro table is the mean of term RMSE values, not pooled RMSE. Results for every fold and student are retained. Jointly changing many feature sources and comparisons makes accidental favorable findings possible; no multiplicity-adjusted discovery claims are made.

## Prediction results

Positive reduction means lower MAE after adding the sources.

| Grade evidence | Baseline MAE | All-source MAE | MAE reduction |
| --- | --- | --- | --- |
| No grades | 6.5377 | 6.5238 | +0.0139 |
| Block A | 3.6067 | 3.6952 | -0.0885 |
| Block B | 2.9485 | 3.0364 | -0.0879 |

With Block B, all-source additions worsen MAE in **all four** evaluation terms. The macro increase is 0.0879 points. The term-by-term reductions are approximately -0.1812, -0.0141, -0.1403 and -0.0159 in chronological order. Adding LMS alone, EVC alone and wellness alone to Block B produces macro reductions of -0.0389, -0.0465 and -0.0234 points respectively. Remove-one-group gains are also small and mixed.

There is an important no-grades nuance:

| Added source(s), no grades | Macro MAE reduction | Terms with lower MAE |
| --- | --- | --- |
| LMS | +0.1770 | 4/4 |
| EVC | -0.1731 | 0/4 |
| Wellness | -0.0199 | 2/4 |
| LMS+EVC | -0.0117 | 2/4 |
| LMS+Wellness | +0.1976 | 4/4 |
| EVC+Wellness | -0.2014 | 0/4 |
| LMS+EVC+Wellness | +0.0139 | 2/4 |

**LMS alone improves by 0.1770 points in all four terms** (6.5377 to 6.3607 MAE), and improves negative log predictive density by 0.0607. LMS + wellness improves by 0.1976 points. This does not establish a separate wellness benefit. EVC alone worsens MAE in all four terms, and adding EVC to LMS + wellness worsens MAE by 0.1837 points. This could reflect weak measurement, missingness, shrinkage choices, redundant information, sample size or model limitations; it does not prove that the psychological constructs are unimportant.

No-grades LMS gains remain positive on average under precision 1 (+0.1680), precision 100 (+0.1326), and missingness indicators (+0.1175); respondent-only gain is +0.1143 with wider mixed-term uncertainty. The all-source no-grades gain is only +0.0139 and varies from -0.0992 to +0.0818 over the alternative precisions. These are modest explored gains below the **illustrative**, not agreed, 0.5-point practical target.

Block B full-model negative log density is 2.7735 versus 2.7606 for grades only (lower is better); 90% interval coverage is 91.1% versus 90.6%, and widths 12.08 versus 11.69 points. The below-70 Brier score is marginally lower, 0.05891 versus 0.05910. This mixed pattern does not establish useful distributional improvement. Near-nominal average coverage is not proof of calibrated low-outcome risks. The per-term scores also report low-outcome counts.

New Spring 2026 all-student Block B MAE is 2.8349 versus grades-only 2.8190. The original full joint plug-in result was 2.8322. Keep those distinct; the new posterior model's missing-input interface differs. The main four-term macro results are not the old single-term result.

`prediction_shift_summary.csv` separately measures how much adding a group changes point predictions. A source can change forecasts without reducing error. This separates **influence on the output** from **benefit to prediction**.

## Uncertainty about predictive gains

The code calculates paired student errors, averages their differences within each term, and performs a Bayesian bootstrap with Dirichlet(1,1,1,1) weights on the four term mean gains (40,000 replicates). The resulting interval describes reweighting of these observed terms. It is **not** a coefficient posterior, an edge probability, or a calibrated probability of future-term improvement. The terms have overlapping training windows and only four evaluation outcomes at the term level.

For Block B, the 95% bootstrap interval for the full-versus-grades MAE reduction is [-0.1508, -0.0285]. For no-grades LMS alone it is [+0.0992, +0.2393]. When all term gains have the same sign, every positive-weight bootstrap mean shares that sign: a displayed 0 or 1 probability partly follows from the bootstrap support. Do not convert it into a universal claim that improvement is impossible or certain. The 0.5-point practical target is an illustrative sensitivity threshold; the professor has not approved it.

## Conditional coefficient probabilities

Earlier 148-student fit, Block B, precision 10; one training SD increase with other predictors held fixed:

| Predictor | Mean points / training SD | 95% credible interval | P(positive) | P(abs effect > 1 point) |
| --- | --- | --- | --- | --- |
| log_page_views | +0.338 | [-0.207, +0.883] | 88.9% | 0.88% |
| log_lms_participations | -0.095 | [-0.632, +0.442] | 36.4% | 0.06% |
| cost_support | -0.214 | [-0.841, +0.412] | 25.0% | 0.72% |
| expectancy | -0.050 | [-0.703, +0.603] | 44.0% | 0.32% |
| value | -0.130 | [-0.735, +0.475] | 33.6% | 0.27% |
| wellness | +0.196 | [-0.388, +0.779] | 74.6% | 0.36% |

`P_positive` and `P_abs_gt_1point` are analytic posterior probabilities, not Monte Carlo labels. All six non-grade probabilities of an absolute effect over one final-percentage point are below 1% under this model. This is conditional on grades, the prior and median-filled design. It cannot establish absence of a causal effect: grades may mediate an earlier motivation effect, and predictors may be correlated or measured poorly. Full coefficient tables and results in the other grade contexts are exported.

## Student probabilities and failure diagnosis

The final posterior assigns `P(final < 70)` using the Student-t predictive CDF. The 70% threshold is illustrative, not an official pass/fail or intervention threshold. These probabilities integrate parameter and outcome noise but treat imputed inputs as known.

- A complete-input Spring 2026 case has predicted mean 71.24, 90% interval [65.72, 76.75], risk 35.6%, and actual 75.95.
- A missing-survey case has predicted mean 77.60, interval [71.36, 83.83], risk only 2.3%, but actual 68.03. This is a missed low outcome.
- The extreme actual outcome 20.01 is predicted at 45.91 with interval [39.33, 52.49]. The model correctly gives high below-70 risk but badly misses severity.

That last error is an original weakness, not something MCMC fixes. The Gaussian likelihood and fixed residual scale may not represent unusual failure patterns, omitted causes or term shifts. A robust Student-t *likelihood* would be a different model; it should not be confused with the current Student-t *predictive distribution* that arises from Gaussian likelihood plus parameter uncertainty. A future robust likelihood or hierarchical term model should be compared against this baseline rather than assumed to help.

Training-design posterior predictive checks include outcome SD, minimum and count below 70. The observed values fall inside the replicated 95% ranges. That does not validate held-out low-outcome behavior: these checks condition on observed training features and training fit, and the Spring failures remain. The simulated outcome distribution is unbounded; 0.039% of training posterior-replicated values are outside [0,100].

## Numerical validation actually completed

- Executed the new notebook, including the main study and all four sensitivity runs (480 regression fits total).
- Four unit tests pass: agreement with the original CPD on complete evidence; independent simulation against analytic posterior/predictive quantiles; training preprocessing unaffected by extreme evaluation inputs; and MCMC diagnostics detecting a deliberately shifted chain.
- Four Gibbs chains: maximum rank-normalized split/folded R-hat **1.000743**, minimum bulk ESS **12194**, minimum tail ESS **14735**. Mean discrepancies from the exact solution are at most **2.003 MCSE**. Marginal interval endpoints are within **0.040 posterior scale units** of the exact solution.
- 20,000 exact posterior draws: maximum absolute simulated-versus-analytic below-70 probability discrepancy **0.0023**.
- Tests and run assertions fail if these statistical checks miss their tolerances. MCMC convergence supports computation under the chosen model; it does not establish model adequacy.

## What I recommend

1. **Keep this as an exploratory baseline.** It gives a coherent answer to the professor's posterior and simulation suggestion without adding unnecessary MCMC dependence.
2. **Prioritize timing and measurement.** Recover raw surveys and grade release/revision snapshots. Distinguish early EVC responses from MLC RETRO. Check item scoring, survey reliability and response-selection patterns. A final-export score cannot establish what was known at an earlier forecast date.
3. **Test a clearly dated, useful checkpoint.** Run the same ablations with only historically available features. LMS's modest no-grades signal is worth investigating there. The grade-free model here is not itself proof of an early prediction date.
4. **Use the existing six terms honestly.** They suffice for an exploratory capstone. A new class is optional stronger confirmation, not a prerequisite to finishing this project. Freeze a future workflow before using new outcomes to evaluate it.
5. **Only add complexity to address diagnosed failures.** Consider robust residuals, term/section partial pooling, and explicit missing-data mechanisms. With six terms and missing surveys, inspect sensitivity before trusting a complex model. MCMC would then have a stronger purpose.
6. **Keep forecasting and coaching effects separate.** Showing that LMS predicts grades would not show that increasing LMS activity improves grades, or that the MLC intervention benefits students. That requires a causal design and explicit estimand.

## Reproduce

From the existing checkout; no worktree is needed:

```bash
cd /workspace/UCI_Capstone_Project
python3.12 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
export MPLCONFIGDIR=/tmp/mlc-matplotlib
export OPENBLAS_NUM_THREADS=2
.venv/bin/python -m posterior_study.analysis
.venv/bin/python -m unittest discover -s tests -v
# Optional editable presentation and matching PDF:
.venv/bin/python -m pip install -r posterior_study/requirements-presentation.txt
.venv/bin/python -m posterior_study.build_presentation
.venv/bin/python -m posterior_study.write_report
```

Open `MLC_Posterior_Predictive_Value.ipynb` with the `.venv` kernel and Run All to reproduce the analysis and displayed outputs. It writes only the new `posterior_results/` outputs. It does not require a Jupyter web server. The original raw notebook still requires the excluded ZIP. To use a different processed dataset, update the explicit input path, column schema and hard-coded cohort assertions deliberately; do not silently treat arbitrary rows as the original study.

Core analysis uses the existing pinned requirements. Presentation dependencies are separate. Numerical reproducibility uses seed 271828, original precision 10, 20,000 direct draws, 16,000 retained Gibbs draws and 40,000 term-bootstrap draws. Package versions and input hash are in `posterior_results/provenance.json`.

The optional presentation rebuild reads existing result files; run the analysis first. `MLC_posterior_updated.pptx` has editable native text/shapes and first-person notes; statistical plots are embedded PNGs. Its PDF is generated from the same slide layout with the same line wrapping, not from an office application. Both are reviewed visually. There are 14 main slides and three technical appendix slides.

## Method references

- Murphy, K. P. (2012). *Machine Learning: A Probabilistic Perspective*. Bayesian linear regression and conjugate inference.
- Rubin, D. B. (1981). The Bayesian Bootstrap. *Annals of Statistics*, 9(1), 130–134. https://doi.org/10.1214/aos/1176345338
- Vehtari, A., Gelman, A., Simpson, D., Carpenter, B., & Bürkner, P.-C. (2021). Rank-Normalization, Folding, and Localization: An Improved R-hat for Assessing Convergence of MCMC. *Bayesian Analysis*, 16(2), 667–718. https://doi.org/10.1214/20-BA1221

These references support the methods, not the empirical claims. No remote literature review or new raw-data verification is claimed.
