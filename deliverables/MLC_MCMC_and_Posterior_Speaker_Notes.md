# MCMC for Our Bayesian DAG — Speaker Notes

These notes are embedded in the PowerPoint. The 85% edge example is illustrative; graph learning was not performed.

## Slide 1: Why use MCMC to evaluate our Bayesian DAG?

Our project uses a Bayesian DAG: a directed acyclic graph. Its arrows describe assumed relationships among student inputs and grades, with no directed loops. A fitted model gives us one set of answers, but we also want to know how much those answers could vary. The posterior describes how plausible different model settings are after combining prior assumptions with the data. MCMC is a way to explore that range by taking many related random samples.

We used MCMC as an evaluation tool: first, to check our uncertainty calculation; then, to help interpret plausible predictor weights and possible grades. We also tested predictions separately. I will first explain what MCMC can do for Bayesian graphs in general, and then show exactly what our project did.

Evidence: posterior_study/analysis.py; deliverables/MLC_Consolidated_Report.md, sections 2–4.

## Slide 2: Why MCMC helps: structural uncertainty

One useful application is structural uncertainty: uncertainty about which arrows should be in the graph. A structure sampler proposes alternative graphs and, when designed and checked properly, spends more time in graphs that have greater posterior support.

Here is an illustration, not a project result. Suppose we keep 1,000 sampled graphs and 850 contain the arrow from A to B. We would estimate an 85% posterior probability for that directed edge. That is more informative than a single yes-or-no graph choice. The estimate depends on the data, prior assumptions and allowed graphs. It also requires a sampler that explores those graphs adequately. Our Gibbs sampler did not change arrows, so we cannot report an 85% edge probability for our project.

If asked: An edge probability is conditional on the model and graph prior. It does not by itself establish a causal relationship. The remaining graphs may reverse the arrow or omit the connection.

Evidence: Illustrative Bayesian structure-learning explanation; no graph-sampling results are claimed.

## Slide 3: Why MCMC helps: uncertain arrow directions

A second advantage concerns Markov equivalence. This means that two different directed graphs can imply the same pattern of statistical relationships. In this simplified example, graph one says expectancy points to engagement, which points to grade. Graph two says engagement points to both expectancy and grade.

These two graphs have the same connections and the same conditional-independence pattern. A group of such graphs is called a Markov equivalence class. Under standard observational models, those patterns alone cannot tell us which direction is correct. A structure sampler can keep both explanations plausible rather than declare one winner. In this way, posterior probability can be shared across equivalent graphs. Their probabilities need not be equal: priors, restrictions and additional modeling assumptions matter. MCMC represents the uncertainty; it does not remove it. For our project, verified measurement timing or intervention evidence would help assess direction. We did not sample these alternative graphs.

If asked: The example assumes only the two displayed connections and no timing constraints. Both graphs imply that expectancy and grade are independent conditional on engagement. Score-equivalent likelihoods cannot distinguish them; informative priors or additional assumptions may favor one.

Evidence: Illustrative three-node Markov-equivalence example; not the full project DAG.

## Slide 4: Our study kept the graph fixed

Now let me separate those general possibilities from what we actually did. We kept the graph fixed. We did not add, remove or reverse arrows. We sampled the predictor weights in the final-grade model and the amount of grade variation left unexplained. A weight tells us how an input is associated with the final grade while the other inputs are held fixed.

For the detailed sampling analysis, we fit the model to 148 students from the earlier five terms. We then inspected predictions for 43 Spring 2026 students. Missing inputs were filled using training-data values and kept fixed during sampling. So our analysis captures uncertainty about weights and noise, but not every possible source of uncertainty. This narrower scope is what makes the next results interpretable.

If asked: No graph posterior, edge-inclusion probability or full joint-DAG missing-data sampler was fitted. Later source comparisons use four temporal evaluations, explained separately.

Evidence: posterior_study/analysis.py: PosteriorRegression and run; posterior_results/provenance.json.

## Slide 5: How our Gibbs MCMC sampler works

Our MCMC method is called Gibbs sampling. Start with a possible amount of unexplained grade variation. First, draw plausible predictor weights given that amount of variation. Next, draw a new amount of unexplained variation given those weights. Keep repeating these two updates. The retained samples describe the posterior uncertainty.

We ran four chains, meaning four runs from different starting noise levels. In each run we discarded the first 1,000 warm-up updates and kept 4,000 samples, for 16,000 retained samples in total. Our model also has an exact mathematical solution. We used it, along with 20,000 direct independent posterior samples, as a reference. MCMC was therefore a method check here, rather than something required to obtain the forecast.

If asked: The 20,000 direct samples are not MCMC samples. The exact solution is available because the outcome regression uses a conjugate Bayesian model.

Evidence: posterior_study/analysis.py: gibbs and PosteriorRegression.sample.

## Slide 6: The sampler matched the exact posterior

The blue bars show the weights visited by Gibbs sampling for one input: LMS page views. The green line is the exact posterior for that same weight. Taller bars mean nearby values appeared more often. Their close overlap is the main point of this picture: the sampler is reproducing the distribution we expect.

We also checked all sampled parameters. The largest R-hat was 1.0007; values near one mean the separate chains are behaving similarly. The smallest effective sample size was 12,194, indicating substantial usable sampling information despite dependence between consecutive draws. These are strong computational checks for this model. They do not prove the graph is correct, that any arrow is causal or that future grades will be predicted accurately. Now that the calculation is checked, we can interpret what the posterior says.

If asked: R-hat is a chain-agreement diagnostic, not a proof of convergence. Effective sample size estimates information relative to independent draws. The largest mean discrepancy from the exact solution was about 2.01 estimated Monte Carlo standard errors.

Evidence: posterior_results/mcmc_diagnostics.csv and provenance.json; plot regenerated using the original Gibbs implementation and seed.

## Slide 7: Non-grade associations were small and uncertain

Each dot is an estimated association with final grade. Each line is a 95% credible interval: a range containing 95% of the coefficient’s posterior probability under our model. Zero means no association after holding the other inputs fixed. Every line crosses zero.

For page views, a one-standard-deviation increase—one typical training-data spread—is associated with about 0.34 more final-grade points on average. The interval runs from about minus 0.21 to plus 0.88. The posterior leans positive, but the association is small and its direction remains uncertain. The shaded area marks an illustrative range of minus one to plus one grade point. This is about conditional association, not the effect of making a student use the LMS more. Because grades are already included, they may absorb information shared with these inputs.

If asked: EVC means expectancy, value and cost; LMS means learning management system. Page views have 88.9% probability of a positive coefficient, but only 0.88% probability of a magnitude above one point per training SD. The one-point threshold is illustrative, and results depend on the prior and fixed imputation. Sign probability is not edge probability.

Evidence: posterior_results/coefficient_posteriors.csv; 148-student fit.

## Slide 8: Could the fitted model generate grades like ours?

Next we ask whether the fitted model can produce a familiar feature of our data. We simulated 20,000 sets of grades for the same 148 training students. For each simulated set, we counted how many students scored below 70. The blue bars show those counts; taller bars mean that count occurred more often.

The actual training data had 19 students below 70, marked by the red line. The middle 95% of simulated counts ran from 11 to 21, so 19 is plausible under this model. This is called a posterior predictive check. It supports the model for this selected feature of the training data, but it does not show that future students will be predicted well. The cutoff of 70 is illustrative. The next slide tests actual later outcomes.

If asked: These replications use independent exact posterior draws from the distribution validated by Gibbs sampling. The range 11–21 describes a simulated count across 148 students, not an individual grade interval. Other stored checks concern grade spread and the minimum.

Evidence: posterior_results/provenance.json: posterior_predictive_checks.n_below70; simulations regenerated with the original seed and sequence.

## Slide 9: Most intervals covered outcomes; one missed badly

A prediction interval is a range for an individual student’s possible final grade. Under the fitted model, each 90% interval contains 90% of that student’s predicted outcome probability. On the left, 39 of the 43 later actual grades fell inside their intervals: 90.7% coverage. Four fell outside.

The right-hand picture shows the largest absolute prediction error, selected deliberately to reveal a failure. The blue interval ran from 39.3 to 52.5, and the predicted mean was 45.9. The actual grade was only 20.0. The model overpredicted by 25.9 points and the interval missed badly. So the sampler can work well while the forecast still fails for a student. One small retrospective cohort cannot establish calibration for future use.

If asked: The data and settings were historically explored. Input release timing is unverified. Intervals exclude imputation, graph and model-selection uncertainty. This example is the largest miss, not a typical case, and does not establish a systematic problem for all low-grade students.

Evidence: posterior_results/spring2026_probabilities.csv; largest-absolute-error case, with identity omitted.

## Slide 10: Did extra inputs improve forecast accuracy?

Finally, uncertainty analysis needs a practical question: do the extra inputs improve forecasts? Here the score is mean absolute error, or MAE. It measures how far predictions are from actual grades, ignoring whether the errors are above or below. Lower is better. We averaged each term’s score equally across four later-term evaluations, totaling 146 predictions per model.

Without recorded grades, adding LMS activity reduced error from 6.54 to 6.36 points, an improvement of 0.18, with improvement in all four terms. With the larger grade bundle, adding LMS, EVC and wellness increased error from 2.95 to 3.04, worsening all four terms. These are two different starting situations. We are not comparing the rows as one controlled experiment. The message is that a source can help modestly when little is known and add no benefit once grades are included.

If asked: The 146 predictions include the 43 Spring 2026 cases; they are not 146 additional independent students beyond that evaluation. 95% term Bayesian-bootstrap intervals for improvement: LMS without grades +0.099 to +0.239; all sources with larger grades −0.151 to −0.028. These intervals summarize term reweighting, not Gibbs samples. Some grade inputs contribute directly to final grade; this is not proof of early prediction. Results are retrospective; grade-release timing is unverified.

Evidence: posterior_results/macro_metrics.csv and paired_gain_summary.csv; four expanding-window evaluation terms.

## Slide 11: What did the evaluation establish?

We can now answer our original question. First, the computation worked well: the Gibbs sampler matched the exact posterior and the chains agreed. Second, the posterior described small and uncertain non-grade associations after grades were included. Third, the model passed the selected training-data check, but later predictions still included a major individual miss. LMS gave a modest forecast improvement only in the no-grades comparison shown.

These are useful findings, including the limitations. They tell us what to trust and what still needs work. We have not learned which arrows are causal, and we have not shown that coaching based on these forecasts improves student outcomes. More iterations of the same sampler are unlikely to answer those questions, because they require different models or new evidence.

Evidence: Synthesis of slides 6–10; no new analysis or structure-learning claim.

## Slide 12: Two next questions need different evidence

To return to the two ideas we started with, structural uncertainty and Markov equivalence would require a graph-learning study. We would need to define which arrows are allowed, specify graph priors, sample alternative structures and check that the sampler moves between plausible explanations. We could then report edge probabilities and any unresolved directions, with sensitivity to the assumptions. That work has not been done here.

For the coaching goal, we need a separate practical test: verify what information was actually available at prediction time, freeze the model and evaluate a new term. That would test early-warning accuracy and risk calibration. Showing that coaching itself helps would require intervention evidence. Our current contribution is a checked uncertainty calculation and an honest account of what this exploratory model can and cannot support.

Evidence: Future-work proposal; neither graph sampling nor a new prospective evaluation is claimed.

