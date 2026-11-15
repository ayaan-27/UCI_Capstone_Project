# MCMC for Our Bayesian DAG — Six-Slide Speaker Notes

The spoken script is about five minutes at a measured pace. “If asked” paragraphs are optional, not part of the main script. Notes are embedded in the PowerPoint.

## Slide 1: Why use MCMC to evaluate a Bayesian DAG?

MCMC, or Markov chain Monte Carlo, explores the uncertainty behind a Bayesian model. A graph sampler can ask which arrows are supported: for example, whether an arrow appears in 85% of sampled graphs. That number is an illustration, not our result. It can also preserve alternative arrow directions when the observations cannot distinguish them. This is called Markov equivalence. Their probabilities need not be equal.

Our project used a narrower form of MCMC: the graph stayed fixed. We evaluated uncertainty in predictor weights and unexplained grade variation. Here is how we checked that calculation and what it told us.

If asked: Graph probabilities depend on the model, graph prior and adequate sampler exploration. MCMC alone does not identify causal direction.

Evidence: General graph-sampling illustration; actual study scope in posterior_study/analysis.py.

## Slide 2: How we evaluated our fixed-graph model

We fit the detailed model to 148 earlier students and checked predictions for 43 Spring 2026 students. The graph and filled-in inputs stayed fixed. Gibbs MCMC repeatedly drew predictor weights, then unexplained grade variation, then repeated the cycle.

We ran four chains from different starting noise levels and kept 16,000 samples after warm-up. This particular model also has an exact mathematical solution, giving us a reference answer. So MCMC was useful as a check of our uncertainty calculation, even though we did not need it to compute the forecast.

If asked: Each chain discarded 1,000 warm-up updates and kept 4,000 draws. The separate 20,000 direct posterior draws were not MCMC. Missing-input uncertainty was excluded.

Evidence: posterior_study/analysis.py: gibbs, PosteriorRegression.sample and run.

## Slide 3: The sampler matched the exact posterior

This picture checks whether the sampler worked. The blue bars show sampled values of the LMS page-view weight. Taller bars mean those values occurred more often. The green line is the exact posterior. Their close overlap is the key result.

Across all parameters, the chains agreed well: the largest R-hat was 1.0007, close to the ideal value of one. There were at least 12,194 effective samples. These results support reliable computation within our fitted model. They do not prove that the graph is causal or that predictions are accurate. Next, what did the posterior tell us?

If asked: Effective sample size estimates information relative to independent draws. R-hat is a diagnostic, not a proof of convergence.

Evidence: posterior_results/mcmc_diagnostics.csv and provenance.json; exact-versus-Gibbs comparison.

## Slide 4: Non-grade associations were small and uncertain

Each dot is an estimated association with final grade. Each line contains 95% of that coefficient’s posterior probability. Every interval crosses zero, so the direction remains uncertain. Grades and the other inputs are held fixed.

For example, an increase of one typical training-data spread in page views is associated with only 0.34 more grade points on average. Its interval runs from minus 0.21 to plus 0.88. The shaded area marks an illustrative range of plus or minus one point. These are small conditional associations, not evidence that changing student behavior would cause those grade changes.

If asked: A typical training-data spread means one standard deviation. LMS means learning management system; EVC means expectancy, value and cost. These results depend on the prior and fixed imputation.

Evidence: posterior_results/coefficient_posteriors.csv; 148-student model fit.

## Slide 5: Most intervals covered outcomes; one missed badly

Now we check actual later outcomes. A 90% prediction interval is the range containing 90% of the model’s predicted probability for a student’s grade. For Spring 2026, 39 of 43 grades fell inside their intervals: 90.7% coverage.

But the largest error, shown on the right, was substantial. The model predicted 45.9, with an interval from 39.3 to 52.5. The actual grade was 20.0. This case was deliberately selected as the largest miss, not a typical example. It shows why good overall coverage and good MCMC diagnostics do not guarantee a reliable forecast for every student.

If asked: This small cohort was historically explored, not an untouched prospective test. Input release timing is unverified; graph, imputation and model-selection uncertainty are excluded.

Evidence: posterior_results/spring2026_probabilities.csv; largest-absolute-error case, identity omitted.

## Slide 6: Did extra inputs improve forecast accuracy?

Finally, did the extra inputs improve forecasts? Average absolute error measures the size of grade prediction errors; lower is better. Across four later-term evaluations, adding LMS without grades reduced average error from 6.54 to 6.36 points—a small improvement, seen in all four terms.

When the larger grade bundle was already included, adding LMS, EVC and wellness increased error from 2.95 to 3.04, worsening all four terms. These are different starting situations. Our conclusion is that the sampler worked well, but predictive value depended on what the model already knew. These retrospective results do not establish causal effects or coaching benefits.

If asked: There were 146 predictions per model across four terms, including the 43 Spring cases. Term scores were averaged equally. Grade inputs can directly contribute to final grade; this does not establish early prediction. 95% term-bootstrap improvement intervals: +0.099 to +0.239 without grades plus LMS; −0.151 to −0.028 with the larger grade bundle plus all sources. These are not Gibbs intervals.

Evidence: posterior_results/macro_metrics.csv and paired_gain_summary.csv.

