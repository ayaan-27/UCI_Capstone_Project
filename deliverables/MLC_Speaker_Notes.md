# Consolidated first-person speaker notes

## 1. Which data improve final-grade predictions?

Professor, this presentation brings the work into one story. I start with the original Bayesian DAG and ask whether wellness, motivation, LMS activity and reflections improve predictions beyond grades. I implemented posterior simulation and a Gibbs MCMC check, compared sources on later students, analyzed the newly supplied RETRO text, benchmarked other models and audited the grading weights. My central finding is that the extra numeric sources do not improve average error beyond the larger grade bundle. LMS alone has a modest signal when grades are absent. These are exploratory findings from existing non-summer terms, and none establishes a causal effect.

## 2. 191 students, six non-summer terms

The main analysis includes 191 distinct students from six Fall, Winter and Spring terms. The original early feature table has grades, logged LMS counts, EVC-style responses and wellness. Seventy-eight students lack the early survey measures. The new RETRO file adds a distinct text source for only the last three terms: 74 students have reflections at some point, and 68 have nonblank reflections in Week 2 or 4. I do not treat students in the earlier terms as nonrespondents to an instrument that was not available. Summer exclusion is explicit, and no existing student is removed because the current cohort was already non-summer.

## 3. The DAG makes assumptions visible

The original fitted graph has six non-grade inputs, sixteen grade inputs and final percentage. Its arrows are assumed conditional relationships. Every input is a direct parent of the outcome. The grouped picture here shows those outcome parents; it omits the predictor-to-predictor arrows for readability. With all inputs observed, the outcome conditional distribution is Bayesian regression. The predictor graph matters when evidence is missing. A plausible map does not prove predictive value or causality, so I test sources separately. The complete original graph is included as SVG, PNG and DOT in the package.

## 4. Three questions need different evidence

I separated three meanings of impact. First, a coefficient posterior describes plausible conditional associations after fitting the model. Second, a posterior predictive probability describes a student outcome under that model. Third, a paired later-term comparison measures whether an added source improves forecasts. The term Bayesian bootstrap used for error gains is not the same distribution as the coefficient posterior, and does not give a guaranteed chance of success in a new term. A continuous shrinkage coefficient also does not supply a probability that a causal edge exists.

## 5. Posterior simulation agrees with the exact solution

The current Normal–Inverse-Gamma model is conjugate, so an exact solution exists. I simulated 20,000 independent posterior draws and ran four actual Gibbs chains, each with 1,000 warmup and 4,000 retained iterations. Gibbs alternates coefficient and variance draws. The rank-normalized diagnostics and Monte Carlo errors agree with the analytic posterior. This supports computation, not the graph, likelihood or missing-data assumptions. MCMC is optional for this model; it would become more useful with a nonconjugate hierarchical or explicit missing-data model.

## 6. Learn from earlier terms; check later students

For each check I fit imputation, scaling and the model using earlier terms only. I compare all eight combinations of LMS, EVC and wellness in three grade contexts. Every comparison uses the same evaluation students. Main precision 10 is inherited from the explored original workflow; sensitivity runs use 1 and 100, missingness flags and non-grade complete respondents. The training windows overlap and these records and settings have already been explored, so the results are exploratory rather than independent confirmation. The grade bundles are not verified week-four snapshots.

## 7. All-source additions did not improve grade-based MAE

With no grades, all numeric sources give only a 0.014-point average improvement. With Block A, error rises from 3.61 to 3.70. With Block B, it rises from 2.95 to 3.04 and is worse in all four checks. These comparisons integrate outcome-parameter uncertainty but use median filling for missing prediction inputs. They differ from the original joint-Gaussian missing-evidence procedure. The old single Spring 2026 result of approximately 2.82 versus 2.83 is preserved, but is not the four-term macro result shown here.

## 8. LMS has a modest signal when grades are absent

The full-model comparison hides a useful nuance. Without grades, LMS alone reduces macro MAE from 6.54 to 6.36, an improvement of 0.177 points in all four terms. LMS plus wellness gives a similar 0.198-point gain, which does not establish a separate wellness benefit. EVC alone worsens MAE in all four terms. Adding every numeric source largely erases the LMS gain. The modest LMS association survives several shrinkage choices on average, but should guide a dated follow-up rather than be treated as a confirmed selected winner.

## 9. Conditional effects are small and uncertain

These coefficients hold grades and the other predictors fixed. Wellness has a mean conditional association of about plus 0.20 percentage points per training standard deviation, with an interval from minus 0.39 to plus 0.78. Every displayed interval includes zero. None is a causal effect per questionnaire point. Conditioning on grades may block pathways through which earlier motivation relates to outcomes, and the estimates depend on the prior and imputation. The cost/support label is the source cost field renamed by the old pipeline, not a newly validated or reverse-scored scale.

## 10. The new RETRO source contains open reflections

The uploaded RETRO is a distinct instrument from numerical EVC. It asks what went well, what did not go well and what could improve motivation and engagement. I analyze nonblank Week 2 and Week 4 responses only in the initial scenario, giving 68 respondents. Weeks 6, 8 and 10 are excluded. Exact submission times are absent. Only the last three terms have this instrument, so only two later-term checks are possible. The first text model trains on 20 students, of whom just 13 supplied early text. This small sample limits how much a text model can learn.

## 11. RETRO words show mixed added value

I separate the words from response behavior. Response measures include participation, number of answers and weeks, and word count. Then I add separate train-only TF-IDF channels for the three prompts. In the larger-grade scenario, words plus response measures reduce error by about 0.31 points in Winter but worsen it by about 0.04 in Spring. Response measures alone perform better on average, so I cannot attribute a reliable improvement to the words. These two-term comparisons use different training windows from the earlier four-term study. Alpha sensitivities and respondent-only comparisons are retained. This sparse text baseline is not validated factor scoring and does not show that the reflections contain no useful information.

## 12. Tested alternatives did not beat the grades baseline

I compared the Bayesian outcome model with Ridge, Huber robust regression, ExtraTrees and histogram gradient boosting. With the larger grades-only bundle, Bayesian and Ridge MAE is 2.95, Huber is 3.45, ExtraTrees is 4.27 and boosting is 4.32. Ridge and the Bayesian CPD have the same point forecast at the same penalty, so they are not independent discoveries. Some alternatives slightly help the no-grades full model, but the earlier Bayesian LMS-only MAE is still lower. This is not exhaustive tuning or a claim of the best possible model, and it does not compare posterior calibration of the alternatives.

## 13. Posterior probabilities can still miss low outcomes

For a complete-input Spring case, the model predicts 71.24 with a 35.6 percent probability below 70; the actual result is 75.95. Another case has a predicted mean of 77.60 and just a 2.3 percent below-70 probability, yet the actual result is 68.03. That student has missing surveys, filled from training medians. The model also predicts the extreme 20.01 outcome near 45.91 and misses severity. Parameter uncertainty alone does not fix these failures. Training posterior predictive checks do not establish later-term calibration, particularly with few low outcomes.

## 14. Confirmed weights and explicit summer exclusion

The main weights sum to 100 percent: written categories 20 and 35, verbal categories 10 and 10, teamwork 10, growth mindset 10, and resilience and agency 5. Surveys can add 0.75 points and team-manager credit 0.25; the MLC extra-credit group is zero-weight here. I keep extra credit separate, rather than renormalizing to 101 percent. These are grading rules, not wellness or coaching effects. Summer courses are explicitly excluded; the current 191 students were already non-summer. The old manifest contains 168 SMR-labelled aggregate entries but none was used as a predictor.

## 15. Predict remaining performance after earned marks

A cleaner forecasting target separates already earned grade points from performance on remaining coursework. The final total equals the known contribution plus remaining course weight times normalized remaining performance, plus extra credit. The functions implement this accounting and use actual score-availability cutoffs. However, the aggregate feature table does not identify the full historical item catalog, denominators, unaggregated scores or extra credit. The workbook dates and roster are from course 84595 and cannot be backdated. Published and unpublished alternative versions also coexist. No historical remaining-work accuracy has been invented from those incomplete inputs.

## 16. Improve timing and measurement before complexity

My recommendation is to retain the simple baseline and improve the data-generating question. A mark can change later motivation and reflections; those measurements may help predict later engagement and marks. I would unroll those feedback paths over time, validate EVC scoring and human-coded RETRO themes, and include observed prior preparation and term context where available. A regularized hierarchical Bayesian model with robust residuals is worth testing after longitudinal inputs are recovered, but has not been fitted here and is not guaranteed to help. The existing six terms suffice for an exploratory capstone; new-class confirmation would strengthen it later.

## 17. Technical reference: exact Bayesian regression

In standardized units the coefficient prior is normal conditional on residual variance, with precision 0.001 for the intercept and 10 for slopes. Variance has inverse-gamma shape 2 and scale 1. The posterior parameters are L, m, a and b. Independent sampling draws variance from its inverse-gamma marginal and coefficients from their conditional normal. Gibbs instead alternates conditional coefficient and variance draws, adding p over two to the inverse-gamma shape in the variance step. Integrating coefficients and variance for a fixed new design gives an exact Student-t predictive distribution. This does not integrate uncertainty in imputation, model selection or the DAG structure.

## 18. Technical reference: sensitivity and score limits

The larger-grade full-model MAE gain is negative under precision 1, precision 10, precision 100, missingness indicators and complete non-grade respondents. Respondent-only analysis selects a different population and does not solve nonrandom response. The paired-gain Bayesian bootstrap reweights four observed term mean differences with Dirichlet weights. Its intervals do not include all development or future-term uncertainty. When all four gains are negative, every positive-weight average is negative, so a zero reported bootstrap improvement probability is not proof of universal impossibility. The 0.5-point practical gain and below-70 risk threshold are illustrative, not agreed operational requirements.

## 19. Technical reference: evidence and reproducibility

The package preserves the original notebook and full graph alongside the three executed companion notebooks. The study runs from the included processed table. Uploaded source files are omitted from the public GitHub package; local copies are required to recompute RETRO and workbook audits. The original historical source ZIP remains unavailable, so the original raw workflow is not newly reproduced. Fourteen existing tests are rerun from the packaged project. Input hashes, package versions, MCMC checks, cohort exclusions and all per-term and per-student results are included. The study supports exploratory conditional prediction, not causal or prospective coaching claims. Standard references support the inference and diagnostics methods rather than our empirical results.