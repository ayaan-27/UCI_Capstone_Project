# What we can now say about wellness, EVC, RETRO, and model choice

This follow-up incorporates the newly supplied RETRO CSV. It supersedes the **availability statement** in the earlier report, which correctly described the files then available. Earlier results using the early WELL + SOM features remain unchanged. This upload is a different instrument: **free-text reflections**, not numerical EVC ratings.

## Have we established an effect?

**We have estimated conditional associations and changes in prediction error. We have not established causal effects.** A prediction changing when a feature changes is not evidence that changing a student's wellness would change their grade by that amount. MCMC cannot bridge that distinction.

There are three useful meanings of “how much”:

1. **Conditional association:** how much the model's expected final percentage shifts per training standard deviation of an input, holding other predictors fixed.
2. **Predictive value:** how much adding an input reduces error for the same later students.
3. **Causal effect:** how much a student's result would change if the factor were changed through an intervention. The current observational DAG and data do not identify this.

The earlier Block B posterior fit, trained on 148 earlier students, gives the following conditional associations in **final-percentage points per one training standard deviation**. These are not effects per one questionnaire rating point:

| Input | Conditional mean association | 95% credible interval |
| --- | --- | --- |
| log_page_views | +0.338 | [-0.207, +0.883] |
| log_lms_participations | -0.095 | [-0.632, +0.442] |
| cost_support | -0.214 | [-0.841, +0.412] |
| expectancy | -0.050 | [-0.703, +0.603] |
| value | -0.130 | [-0.735, +0.475] |
| wellness | +0.196 | [-0.388, +0.779] |

For example, wellness has a mean association of about **+0.20 points**, with a 95% interval **[-0.39, +0.78]**. That interval includes zero and negative associations. It is not an established +0.20-point causal benefit. The estimates depend on the prior, linear form, missing-value filling and inclusion of grades. Conditioning on grades can block pathways through which earlier motivation or wellness relates to outcomes; these are not total effects.

The six non-grade posterior probabilities of an absolute conditional coefficient exceeding one final-percentage point are below 1% under that model. This is conditional, prior-dependent evidence about those fitted coefficients, not proof that these constructs never matter. The early cost field's wording and scoring still require validation.

Predictive checks likewise did not show a useful wellness-only or EVC-only improvement beyond the larger grade bundle. Without grades, LMS alone provided a modest **0.177-point** MAE reduction across four terms, while adding all non-grade sources gave only 0.014 points. These are explored retrospective findings.

## What is in the new RETRO file?

The upload has **870 question-response rows, 290 student-week check-ins, and 74 distinct students**, all matching the existing grade table by student and cohort. There are no duplicate student/week/question records, and 15 responses are blank.

Three prompts ask what did not go well, what went well, and what could improve motivation and engagement. Responses occur in Weeks 2, 4, 6, 8 and 10, in Fall 2025, Winter 2026 and Spring 2026. The file does **not** cover the first three terms, and earlier students are not treated as if they declined this survey.

Using only Week 2/4 nonblank responses gives **68 respondents**: 13/20 in Fall 2025, 25/40 in Winter 2026, and 30/43 in Spring 2026. The CSV contains week labels but **no submission timestamps**. Week-labelled scenarios therefore do not prove exactly what was available at an end-of-week checkpoint. The grade bundles also still lack release/revision timestamps.

The new code excludes Weeks 6/8/10 from the early scenario. Tests verify that altering a later response cannot affect the early inputs. Raw reflection text is retained only in the ignored local input `data/retro_uploaded.csv`; figures and result tables do not publish the responses.

## How RETRO was tested

These are initial text baselines, not validated psychological scoring:

- Preserve the three prompts as separate channels. Concatenate only Week 2/4 responses within a student and prompt.
- Fit TF-IDF vocabularies **on training students only**, with unigrams/bigrams, minimum document frequency 2, and at most 200 features per prompt. Negation words no/not/nor/never are retained. No external NLP service or sentiment inference is used.
- Compare the numeric baseline with (a) response measures alone and (b) text plus the same response measures. Response measures are whether a student responded, number of answered prompts, number of response weeks, and log word count. This distinguishes text content from participation/verbosity.
- Use Ridge regression at fixed alpha 10, with alpha 1 and 100 as sensitivity checks. Numerical predictors and outcomes use train-only imputation/scaling. Text is L2 normalized by TF-IDF; no evaluation vocabulary is fitted.
- Compare no grades, Block A and Block B, both with and without the early LMS/EVC/wellness inputs. Preserve every evaluation student, including nonrespondents; repeat reported paired comparisons within respondents as a descriptive sensitivity.

Only **two later-term evaluations** are possible using terms where this instrument exists: train on Fall 2025 (20 students), predict Winter 2026 (40); then train on Fall + Winter (60), predict Spring 2026 (43). The first text fit sees only 13 early respondents. This is a very small text-learning problem. No bootstrap interval based on two terms is presented as strong future-term uncertainty.

For the larger grades-only baseline and alpha 10, positive gains below mean lower MAE:

| Evaluation term | Grades-only MAE | Gain: response measures | Gain: words + response | Gain: words over response |
| --- | --- | --- | --- | --- |
| 2026 WTR | 3.820 | +0.347 | +0.307 | -0.040 |
| 2026 SPR | 3.590 | +0.053 | -0.039 | -0.091 |

The macro mean gain from text plus response measures is **+0.134 points**, but it is mixed across the two terms. Response measures alone gain **+0.200 points**; the words add **-0.066 points** beyond those response measures. Thus the text itself **has not shown a consistent independent benefit** in this larger-grade scenario.

Adding RETRO to the larger grade model plus all early non-grade sources also gives mixed term gains. No-grades results are mixed by term and alpha as well. All results and alpha sensitivities are retained rather than selecting the best-looking combination. Response measures may proxy engagement or response selection; they are not causal effects of reflecting more.

These numbers cannot be compared directly to the old four-term 2.95/3.04 macro MAEs: the RETRO experiment has different training windows and only two evaluation terms. A separate coefficient called the “effect of RETRO” would be misleading because RETRO contains diverse text, not a single validated quantity. Failure of this sparse text baseline does not establish that the reflections contain no useful information.

## Is there a better model?

I tested fixed, modest candidate settings using the same four earlier-to-later checks as the previous numeric study. This is an exploratory comparison, not exhaustive tuning or a guarantee of the best possible model.

| Model, grades only | Four-term macro MAE |
| --- | --- |
| Ridge | 2.948 |
| Bayesian CPD | 2.948 |
| Huber | 3.446 |
| ExtraTrees | 4.266 |
| HistGB | 4.317 |

The current Bayesian outcome CPD and standardized Ridge have the same point predictions at the same slope precision/penalty. They do not represent two independent discoveries. Huber uses epsilon 1.35 and alpha 1 in standardized outcome units. ExtraTrees uses 200 trees, depth 4 and minimum leaf size 5. Histogram gradient boosting uses 150 iterations, at most 7 leaves, minimum leaf size 10 and L2 penalty 10. These settings are fixed rather than chosen on each evaluation outcome.

**No tested replacement beats the simple larger-grades baseline.** With all numeric sources, the ordering is similar: Bayesian/Ridge 3.036, Huber 3.517, ExtraTrees 4.269, HistGB 4.408. With no grades, Huber and ExtraTrees with all sources slightly improve over Bayesian full-model MAE (about 6.42 versus 6.52), but the earlier Bayesian LMS-only result is lower at 6.36. A more flexible model is not automatically better in 191 students.

This benchmark assesses point prediction. It does not establish superior posterior uncertainty or calibration for Huber/trees. Low-outcome errors remain substantial. The Gaussian-likelihood Bayesian model's Student-t *predictive distribution* is also not a robust Student-t *likelihood*; changing the likelihood would require a new fit and validation.

## How I would improve the DAG

I recommend improving the **question, temporal ordering and measurement** before adding arrows or a larger sampler.

1. **Specify one prediction time and one target.** For an early forecast, use only grades and reflections actually available then. Consider predicting *remaining coursework performance*, then combining it with already earned marks using known course weights. This reduces the built-in part-whole association between completed assessments and final percentage. Implementing that target requires actual weights and release snapshots; it is not newly implemented here.
2. **Unroll feedback through time.** A poor mark can change a later reflection or motivation rating, which may relate to subsequent activity and later marks. Represent `marks(t) → EVC/RETRO(t+1) → activity(t+1) → marks(t+2)` as hypotheses, rather than simultaneous cycles. A retrospective response may describe earlier success or difficulty; it should not automatically be modeled as its cause.
3. **Represent measurement separately.** EVC and wellness questionnaire items measure constructs; free-text RETRO can provide qualitative indicators of experiences. Validate a coding scheme for themes such as workload, feedback, collaboration and study strategy, using two human coders and agreement checks. Then test those features on later students. TF-IDF is an initial baseline, not evidence that these constructs have been reliably measured.
4. **Include observed context where available.** Prior preparation, previous performance, term/section/instructor and response selection can affect both survey responses and grades. Some may be unobserved. Drawing an unmeasured prior-ability node makes the assumption visible but does not identify its effect. Missingness deserves an explicit sensitivity analysis; adding response flags alone does not solve nonrandom response.
5. **Try a restrained hierarchical Bayesian model if longitudinal inputs can be recovered.** Use partial pooling for term/section, regularized slopes, and repeated time-indexed measurements. Evaluate a robust likelihood to address unusual residuals. With only six terms, variance estimates and random slopes need strong regularization and sensitivity checks; improved performance is a hypothesis, not a result. Actual longitudinal measurement cannot be recovered from the current early averages alone.
6. **Preserve simple benchmarks and test added value.** Keep grades-only and LMS-only baselines. If choosing hyperparameters or text representations, use inner earlier-term validation inside each training fold. Do not select on these outer errors and call the same errors independent confirmation. The existing six terms are enough for exploratory capstone work; new-class confirmation would strengthen it later.

An interpretable next study would ask: **“Among students with the same observed performance at a defined checkpoint, do earlier engagement and coded reflections improve prediction of the remaining coursework?”** That is a sharper question than whether every arrow in the original DAG is “real.” A causal question about improving wellness or coaching effectiveness requires a separately specified intervention/estimand and identification assumptions.

## What was executed and checked

- Input SHA-256: `db54e9a7bd99092843469997be746de5f47fa85bb949e3910c0fc48faff5e8f9`.
- 120 numeric model fits across four temporal checks; 108 RETRO/numeric comparisons across two checks, three contexts, two source baselines, three alphas and three text/response encodings.
- Eight tests pass: the original four posterior tests plus checks that later reflections are excluded, duplicate/unmatched IDs fail, evaluation words cannot enter the text vocabulary, and the numeric Bayesian benchmark reproduces the previous predictions.
- No causal intervention, new raw grade extraction, validated RETRO factor coding, hierarchical fit or robust Bayesian likelihood fit is claimed.

## Reproduce

```
cd /workspace/UCI_Capstone_Project
# Uses the existing requirements.txt; no new packages are required.
OPENBLAS_NUM_THREADS=2 OMP_NUM_THREADS=2 .venv/bin/python -m posterior_study.retro_followup --retro-csv data/retro_uploaded.csv
MPLCONFIGDIR=/tmp/mlc-matplotlib .venv/bin/python -m posterior_study.retro_report
.venv/bin/python -m unittest discover -s tests -v
```

The uploaded source CSV is not included in the distributable code ZIP; supply it via `--retro-csv` at its local path. The full earlier code and results are retained. The new notebook `MLC_RETRO_Followup.ipynb` displays this follow-up's executed results, and `MLC_RETRO_followup` slides are an addendum to the previous presentation, whose earlier unavailable-file statement is now superseded.
