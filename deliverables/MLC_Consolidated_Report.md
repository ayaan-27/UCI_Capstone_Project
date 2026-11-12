# My Learning Coach — consolidated research report

Current state: completed exploratory non-summer analyses, with supplied RETRO and grading weights.

## 1. Executive findings

This is the current integrated account of the My Learning Coach capstone. It consolidates the original fixed Bayesian DAG, posterior simulation and Gibbs MCMC validation, temporal source ablations, newly supplied RETRO text, candidate-model benchmarks, confirmed grading weights and explicit summer exclusion. Earlier presentations and stage reports are archived, not treated as current guidance.

The main conclusion is conditional and exploratory: adding all numeric non-grade sources did not improve MAE beyond the larger assessment bundle. LMS activity alone showed a modest signal without grades. RETRO words had mixed two-term gains; participation and verbosity explain at least part of the apparent benefit. None of these analyses establishes causal or coaching effects.

| Grade context | Baseline MAE | All numeric MAE | MAE reduction |
| --- | --- | --- | --- |
| No grades | 6.538 | 6.524 | +0.014 |
| Block A | 3.607 | 3.695 | -0.089 |
| Block B | 2.948 | 3.036 | -0.088 |

- 191 unique students, six Fall/Winter/Spring terms; Summer/SMR excluded.
- 20,000 exact posterior draws and four Gibbs chains agree with the analytic outcome model.
- Source uploads are excluded from the public GitHub package; code and derived results are included.
- Fourteen tests pass from the packaged project.
- Weighted remaining-work arithmetic is implemented and tested; a real historical remaining-work forecasting model is not yet fitted.

Use the consolidated presentation for the talk, this report for interpretation and scope, and 03_Project for runnable code and full evidence. The missing prerequisite is the original complete historical grade/source archive and verified score-availability history, not another round of MCMC.

## 2. Data, graph and scope

| Source | Available representation | Important limit |
| --- | --- | --- |
| Grades | Block A: 10 scores; Block B: 16 | Aggregated from final exports; releases unverified |
| LMS | log(1+page views), log(1+participations) | Original assumed first-four-week window |
| Early EVC / wellness | Expectancy, value, source cost/support, wellness | 78/191 lack all four early survey features |
| RETRO | Three open reflection prompts; Weeks 2/4 used | Three terms only; no exact submission timestamps |
| Weights | Seven main categories + three extra-credit categories | Same weights confirmed; item versions differ by term |

The main processed sample is 18 Fall 2024, 27 Winter 2025, 43 Spring 2025, 20 Fall 2025, 40 Winter 2026 and 43 Spring 2026 students. All 191 IDs are distinct, so these are student-course rows rather than repeated independent survey observations. The current table contains no summer students. The historical eligibility manifest contains 168 SMR-labelled category aggregate entries; zero entered either predictor bundle.

The original fixed DAG contains 23 nodes and 62 arrows: six non-grade inputs, sixteen assessment nodes and final percentage. There are eight predictor-subgraph arrows, 32 arrows from expectancy/page views to the sixteen assessment nodes, and all 22 inputs are outcome parents. The structure is assumed, not learned as a causal discovery result. The full original SVG/PNG/DOT is in 04_Diagrams and the original results folder.

With complete outcome-parent evidence, the outcome CPD is regularized Bayesian regression. The other predictor arrows matter for missing-evidence inference. The updated same-student comparison instead uses training-median filling at both training and prediction time, with train-only scaling. It integrates outcome parameter uncertainty conditional on that fixed imputed design, not uncertainty in missing values, preprocessing, structure, model selection or causality.

The source cost variable was renamed cost_support in the original pipeline. Its item wording, direction and scale reliability have not been newly validated. RETRO is a separate free-text instrument and must not be described as the numerical EVC score. Some grades are components of the final target, creating part-whole predictive association. Calendar dates and historical grade revisions remain unverified.

## 3. Bayesian inference and numerical validation

Standardize predictors and response using training data. In standardized units the prior is beta|sigma² ~ Normal(0, sigma² Lambda0^-1), with intercept precision 0.001 and slope precision 10; sigma² ~ InverseGamma(shape=2, scale=1). The posterior is Normal–Inverse-Gamma.

```text
L = Lambda0 + A.T @ A
m = solve(L, A.T @ z)
a = 2 + n/2
b = 1 + (z.T @ z - m.T @ L @ m)/2
Predictive df = 2*a
Predictive location = A_new @ m
Predictive scale^2 = (b/a)*(1 + A_new @ inv(L) @ A_new.T)
```

Independent simulation draws variance from IG(a,b) and coefficients from Normal(m, sigma² L^-1). The actual two-block Gibbs sampler alternates that coefficient draw with variance|beta,D ~ IG(a+p/2, b+(beta-m)ᵀL(beta-m)/2). Four dispersed chains each use 1,000 warmup and 4,000 retained iterations. Exact independent sampling uses 20,000 draws.

| Recorded numerical check | Result |
| --- | --- |
| Maximum rank-normalized split/folded R-hat | 1.000743 |
| Minimum bulk ESS | 12,194 |
| Minimum tail ESS | 14,735 |
| Largest posterior-mean error / MCSE | 2.003 |
| Maximum simulated vs analytic risk-probability error | 0.0023 |

These results support computational correctness under the chosen model. MCMC is optional when a closed form exists. A Student-t predictive distribution arising from Gaussian likelihood plus parameter uncertainty is distinct from fitting a robust Student-t likelihood. No full missing-data DAG sampler, learned structure posterior, spike-and-slab inclusion probabilities or causal edge probabilities are claimed.

Continuous shrinkage priors assign zero probability to an exactly zero coefficient. Therefore P(beta>0) is not a posterior edge-inclusion probability. If discrete inclusion probabilities are desired, they require an explicitly different model and sensitivity analysis.

## 4. Temporal source comparisons

| Train through | Evaluate | Evaluation students |
| --- | --- | --- |
| Winter 2025 | Spring 2025 | 43 |
| Spring 2025 | Fall 2025 | 20 |
| Fall 2025 | Winter 2026 | 40 |
| Winter 2026 | Spring 2026 | 43 |

Every numeric comparison uses the same evaluation students. All eight subsets of LMS, EVC and wellness are tested under no grades, Block A and Block B: 96 main fits. Four sensitivity settings repeat the 96 fits (precision 1, precision 100, missingness indicators, complete non-grade respondents), giving 480 fits across main and sensitivity blocks. The final posterior interpretation also fits the earlier 148 students.

Main precision 10 is inherited from the previously explored workflow. Its historical selection used some earlier-fold outcomes. These are explored temporal comparisons with overlapping training sets, not an unbiased independent confirmation estimate. When choosing new settings, inner earlier-term tuning must stay inside each training fold. Macro scores give each evaluation term equal weight; macro RMSE is an average of term RMSE values, not pooled RMSE.

| No-grades source | Macro MAE | MAE reduction | Terms improved |
| --- | --- | --- | --- |
| LMS | 6.361 | +0.177 | 4/4 |
| EVC | 6.711 | -0.173 | 0/4 |
| Wellness | 6.558 | -0.020 | 2/4 |
| LMS+EVC | 6.549 | -0.012 | 2/4 |
| LMS+Wellness | 6.340 | +0.198 | 4/4 |
| EVC+Wellness | 6.739 | -0.201 | 0/4 |
| LMS+EVC+Wellness | 6.524 | +0.014 | 2/4 |

LMS alone improves no-grades MAE from 6.5377 to 6.3607 (0.1770 points) and improves all four terms. LMS plus wellness improves by 0.1976, without establishing a distinct wellness contribution. EVC alone worsens all four term MAEs. All sources together improve only 0.0139 and are prior-sensitive. These no-grades scenarios do not establish an actual early prediction date.

For Block B, the combined model worsens MAE in all four checks; average change is -0.0879 points of reduction. Adding individual groups and removing each from the full model is retained in paired_gain_summary.csv. Outcome-distribution metrics are mixed: full-model negative log density 2.7735 vs 2.7606 for grades only, coverage 91.1% vs 90.6%, width 12.08 vs 11.69, and Brier70 0.05891 vs 0.05910. This does not establish useful distributional improvement.

## 5. Factor sizes, predictive influence and risk

Final Block B interpretation fit: 148 earlier students; one training standard deviation increase holding the other inputs and grades fixed. Units are final-percentage points, not questionnaire rating points and not intervention effects.

| Input | Mean points/SD | 95% credible interval | P(positive) |
| --- | --- | --- | --- |
| LMS page views | +0.338 | [-0.207, +0.883] | 88.9% |
| LMS participations | -0.095 | [-0.632, +0.442] | 36.4% |
| Source cost/support | -0.214 | [-0.841, +0.412] | 25.0% |
| Expectancy | -0.050 | [-0.703, +0.603] | 44.0% |
| Value | -0.130 | [-0.735, +0.475] | 33.6% |
| Wellness | +0.196 | [-0.388, +0.779] | 74.6% |

All six non-grade probabilities of an absolute conditional coefficient above one final-percentage point are below 1% under this prior and design. The intervals include zero. Conditioning on grades can block a pathway from motivation to performance; correlated inputs, measurement error, missingness and shrinkage also affect the estimates. These are not total causal effects.

A separate prediction_shift_summary.csv distinguishes influence from utility. Adding all sources changes Block B predictions by roughly 0.31–0.50 points on average within the four evaluation terms, but those shifts do not reduce MAE. A source may affect an output without improving it.

| Reused Spring example | Mean | 90% interval | P(final<70) | Actual |
| --- | --- | --- | --- | --- |
| Complete inputs | 71.24 | 65.72–76.75 | 35.6% | 75.95 |
| Missing surveys; missed low result | 77.60 | 71.36–83.83 | 2.3% | 68.03 |
| Extreme outcome; severity missed | 45.91 | 39.33–52.49 | ~100% | 20.01 |

The 70% threshold is illustrative, not an official pass/fail or intervention policy. The last two examples show model failure despite integrating parameter uncertainty. Missing inputs are still treated as fixed after filling, and rare low outcomes are too few for strong calibration claims. Training posterior-predictive checks of SD, minimum and counts below 70 fall within replicated ranges; that does not validate later-term low-outcome behavior. Predictions and intervals are unbounded Student-t distributions; only MAE/RMSE point predictions are clipped.

## 6. RETRO: newly supplied text and response behavior

The upload has 870 rows, 290 student-week check-ins and 74 distinct students, all matching the grade table. Fifteen responses are blank and no student/week/question keys are duplicated. Only Fall 2025, Winter 2026 and Spring 2026 contain this instrument. Week 2/4 nonblank text gives 68 respondents: 13/20, 25/40 and 30/43. Exact timestamps are absent; Weeks 6/8/10 are excluded from the early-labelled scenario.

Three separate train-only TF-IDF channels preserve the prompts: what went well, what did not go well and what could improve. Unigrams/bigrams use min_df=2 and at most 200 features per prompt; no/not/nor/never are retained. Response measures are whether a student responded, number of answers and weeks, and log word count. No external NLP service, numerical sentiment inference or validated psychological factor coding is used.

Only two later-term checks are possible: Fall 2025 (20 students) trains the Winter 2026 test (40); Fall+Winter (60) trains the Spring 2026 test (43). The first model sees only 13 early text respondents. Ridge alpha 10 is the reference and alphas 1/100 are retained as sensitivity settings. All-student and respondent-only paired comparisons are exported. There are 108 fits across contexts, baselines, alphas and encodings.

| Evaluate | n | Grade-only MAE | Gain: response | Gain: text+response | Words over response |
| --- | --- | --- | --- | --- | --- |
| 2026 WTR | 40 | 3.820 | +0.347 | +0.307 | -0.040 |
| 2026 SPR | 43 | 3.590 | +0.053 | -0.039 | -0.091 |

In the Block B baseline scenario, text plus response improves Winter MAE by 0.3075 but worsens Spring by 0.0388. The mean gain is about 0.134 points, while response measures alone average about 0.200. The text content therefore has no consistent independent benefit in this scenario. Adding RETRO to all early numeric sources is also mixed. Other contexts and alpha values vary; selecting a favorable one would not establish a reliable effect.

These scores cannot be compared directly with the earlier four-term 2.95/3.04 values: training windows and covered terms differ. A small sparse text model failing to help does not establish that reflections contain no useful information. Response measures may proxy engagement or selection. Raw responses are omitted from the public package and are not quoted in the report or slides.

## 7. Candidate models and empirical diagnosis

Five fixed model labels are compared on the same four numeric temporal checks and populations (120 fits). Bayesian CPD and standardized Ridge have the same point forecasts at the same slope penalty. They are not independent evidence for a discovery.

| Model | Block B grades-only MAE | Block B all-numeric MAE |
| --- | --- | --- |
| Bayesian CPD | 2.948 | 3.036 |
| Ridge | 2.948 | 3.036 |
| Huber | 3.446 | 3.517 |
| ExtraTrees | 4.266 | 4.269 |
| HistGB | 4.317 | 4.408 |

Huber uses epsilon 1.35, alpha 1 and standardized outcomes; ExtraTrees uses 200 trees, depth 4 and minimum leaf 5; HistGB uses 150 iterations, seven leaves, min leaf 10, learning rate .05 and L2 10. Settings were not exhaustively tuned. This comparison is about point error, not posterior calibration of the alternatives.

No tested replacement beats the simple larger-grades baseline. With no grades, Huber/ExtraTrees full-model MAEs around 6.42 slightly improve on Bayesian full-model 6.52, but do not beat the earlier Bayesian LMS-only MAE of 6.36. A more flexible model is not automatically preferable in 191 students.

My diagnosis is that the current framework is a good exploratory capstone baseline: transparent assumptions, train-only preprocessing, temporal checks and quantifiable posterior uncertainty. It does not establish coaching effectiveness, causal paths, a verified early prediction time or robust low-outcome calibration. Grade-target part-whole dependence, missing surveys, six terms and unverified releases are more consequential than adding MCMC to an already tractable model.

A regularized hierarchical term/section model, robust likelihood and explicit missing-data mechanisms are sensible candidates to test against the baseline if suitable longitudinal and context data are recovered. With six terms, priors and pooling variance would need sensitivity checks. Those models have not been fitted or shown superior here.

## 8. Grading weights, SMR policy and remaining-work accounting

The user confirmed that the same category weights apply across the six historical non-summer terms. The main sum is 100%. Survey extra credit can add 0.75 final-percentage points and team-manager credit 0.25; MLC extra credit is weighted zero in this workbook. Do not renormalize the 101% combined weights. A zero grading weight is not a zero causal or educational effect.

| Main category | Weight |
| --- | --- |
| Written Mastery I | 20% |
| Written Mastery II | 35% |
| Verbal Mastery I | 10% |
| Verbal Mastery II | 10% |
| Teamwork Mastery | 10% |
| Life-Long Learning Mastery: Growth Mindset | 10% |
| Life-Long Learning Mastery: Resilience & Agency | 5% |

The workbook inventory for course 84595 contains 126 items, 118 published. It includes unpublished versions alongside replacements: verbal category denominators are 183 vs 119 published points and 164 vs 100; teamwork 262 vs 246. Cached subtotals were verified against item rows. Neither all-inventory nor publication-only totals are automatically official historical effective denominators.

Across 138 historical selected-assignment source rows, 116 match title and points but still lack verified historical group denominators; 12 have no exact current title match, six match an item unpublished in 84595, and four differ in point maximum. The workbook’s Fall 2026 due dates are not historical grade-release timestamps. Summer metadata is excluded before numeric/RETRO analyses and summer-labelled predictor columns are rejected. No existing row is removed and prior predictions were reproduced exactly.

```text
known assignment fraction = category_weight * assignment_points / category_total_points
known earned contribution = 100 * category_weight * earned_points / category_total_points
final_total = known_contribution + (1-known_weight)*remaining_main_percent + extra_credit
remaining_main_percent = (final_total-extra_credit-known_contribution)/(1-known_weight)
```

The implementation requires an effective main-assignment catalog and actual timezone-aware score snapshots. It preserves students without grades, selects the latest state before cutoff, handles blank-score revocation, and rejects incomplete category rosters or unsupported excused/dropped adjustments. Extra credit must be supplied explicitly. Arithmetic round-trip tests pass. No real historical remaining-work targets or forecasting results are claimed.

## 9. Prioritized next study and what remains unavailable

- Recover the original complete grade/source ZIP, historical effective assignment catalogs, unaggregated scores and extra-credit contributions.
- Verify score release/revision snapshots and survey submission times; select one useful checkpoint. Due dates alone are insufficient.
- Predict remaining coursework, then combine earned contribution and extra credit through deterministic grading rules.
- Unroll feedback through time: earlier marks may affect later EVC/RETRO, which may predict later activity and marks. Retrospective descriptions are not automatically causes.
- Validate EVC item wording/scoring and code RETRO themes such as workload, feedback, collaboration and study strategy with human agreement checks before giving them quantitative factor meanings.
- Use observed prior preparation and term/section context where available; describe unmeasured confounding and response selection explicitly. A drawn latent node does not identify an effect.
- If choosing new representations or tuning, use inner earlier-term validation. Test restrained pooling/robust/missing-data models against grades-only and LMS-only benchmarks.

The current processed table aggregates assignments and early surveys. It cannot uniquely reconstruct full historical grading components, response trajectories or what was known by a particular date. Identical category weights do not solve these missing inputs. The original historical source ZIP is not included because it has not been supplied in this environment.

The existing six terms are enough to finish an honest exploratory capstone. A new class would strengthen confirmation later, but is not a prerequisite for reporting these findings. A causal question about improving wellness or MLC coaching needs an explicit intervention/estimand and identification design beyond observational prediction.

## 10. Reproduction, verification and references

The package includes four notebooks. MLC_Bayesian_DAG_updated.ipynb is the original supplied executed study and requires the missing original source ZIP for raw rerun. The three companion notebooks are executed: posterior/source value; RETRO/model follow-up; and weights/SMR audit. The current report supersedes the availability and status statements in earlier stage reports.

```text
cd 03_Project
python3.12 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python -m unittest discover -s tests -v
# To rerun all available studies after installation:
bash run_available_studies.sh
```

Core runs use existing pinned requirements; optional presentation/report dependencies are in posterior_study/requirements-presentation.txt. Python 3.12.14, seed 271828 and recorded hashes support reproduction. The release validation log is in 02_Report; MANIFEST.json records every shipped file hash. This package is a validated artifact snapshot; GitHub publication is identified by the repository commit.

Fourteen tests cover original outcome-CPD agreement, exact simulation, training-only preprocessing, detection of nonconverged chains, late-RETRO exclusion, duplicate/unmatched IDs, training-only text vocabulary, numeric benchmark reproduction, summer metadata/field exclusion, category-specific accounting, later-score exclusion, explicit extra-credit recombination, blank-score revocation and timezone/category completeness. Tests are executed from the packaged project.

Method references: Murphy (2012), Machine Learning: A Probabilistic Perspective, Bayesian linear regression. Rubin (1981), The Bayesian Bootstrap, Annals of Statistics 9(1), 130–134, DOI 10.1214/aos/1176345338. Vehtari et al. (2021), Rank-Normalization, Folding, and Localization, Bayesian Analysis 16(2), 667–718, DOI 10.1214/20-BA1221. These support methods, not the empirical claims; no new remote literature review is claimed.

Input SHA-256 values: processed table 7df7dcfc75aaf5d07571bfddc95d01db6c0d299e3c26ad42a6835ef9e9ff0fcb; RETRO db54e9a7bd99092843469997be746de5f47fa85bb949e3910c0fc48faff5e8f9; workbook c75c8b6030def5d0c27587c70c38e95830bf99db24c68fa132cab75aca6357e4.
