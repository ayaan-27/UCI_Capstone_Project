# Speaker notes for the uploaded six-slide presentation

Only the speaker notes were revised. The visible slides match the uploaded fixed-graph version. Read the main paragraphs aloud; presenter reminders and sources are reference material.

## Slide 1: Why use MCMC to evaluate a Bayesian DAG?

Alongside our predictions, we wanted to understand how uncertain the model’s answers were. MCMC helps us explore a distribution of plausible model settings, instead of relying on one fitted estimate.

The two boxes show what this can mean for a Bayesian graph. On the left, a sampler that changes the graph could count how often an arrow appears. The 85% is just an example, not a result from this study. On the right, two arrow directions can sometimes explain the same observations. That is called Markov equivalence: the data may not tell us which direction to choose.

For the analysis shown in this deck, we kept the graph fixed. We used MCMC to explore uncertainty in the weights and the unexplained grade variation. The next slide shows how.

Presenter reminder — not part of the spoken script
The upload is the earlier fixed-graph deck. A separate structure-learning study was done later and is presented in another version. Do not describe the illustrative 85% as measured evidence. MCMC means Markov chain Monte Carlo; graph probabilities depend on the model, prior assumptions and adequate sampling.

Source
posterior_study/analysis.py; uploaded slide 1. The graph example is illustrative.

## Slide 2: How we evaluated our fixed-graph model

The left box shows what stayed unchanged: the arrows in our graph and the values used to fill missing inputs. The right box shows what we allowed to vary: the predictor weights and the amount of grade variation the model could not explain.

We fitted this model using 148 earlier students. Gibbs sampling then repeated two steps: draw plausible weights given the current noise level, and draw a new noise level given those weights. Repeating that cycle explores different plausible combinations.

We ran the sampler four times from different starting noise levels. After discarding the warm-up samples, we kept 16,000 samples in total. This model also has an exact mathematical solution, so we could check whether the sampler reproduced the answer we should get. That is the comparison on the next slide.

Presenter reminder — not part of the spoken script
Each chain discarded 1,000 warm-up updates and retained 4,000 samples. The separate 20,000 direct posterior draws were not MCMC draws. Missing-input values stayed fixed, so their uncertainty was not included. The 43 Spring 2026 students were excluded from this 148-student fit.

Source
posterior_study/analysis.py: PosteriorRegression.sample, gibbs and run.

## Slide 3: The sampler matched the exact posterior

Read the horizontal axis as possible values of the LMS page-view weight. The blue bars show how often the sampler visited nearby values: taller bars mean those values appeared more often. The green line is the distribution calculated from the exact formula. The bars follow the line closely, which is what we wanted to see.

The numbers on the right check the sampling runs more broadly. R-hat compares the runs; values close to one suggest they are behaving similarly. Our largest value was 1.0007. Effective sample size accounts for consecutive draws being similar, rather than fully independent. We had at least 12,194 samples’ worth of independent information.

Together, these checks support the calculation within this fitted model. We still need separate evidence about what the inputs tell us and how well the model predicts.

Presenter reminder — not part of the spoken script
The plotted weight is expressed in final-grade points per one training-data standard deviation of log page views, holding other inputs fixed. Bar height is a density, not an edge probability or a percentage of accurate forecasts. The green curve is the exact posterior for the same model. Diagnostics support, but do not prove, convergence.

Source
posterior_results/mcmc_diagnostics.csv; posterior_results/provenance.json; original Gibbs implementation.

## Slide 4: Non-grade associations were small and uncertain

Now that we have checked the calculation, we can look at what the model says about the inputs. Each row is one non-grade input. The dot is its average estimated association with final grade. The horizontal line contains 95% of the plausible weight values under this model.

The dashed vertical line at zero means no association after accounting for grades and the other inputs. Every interval crosses it, so both negative and positive associations remain plausible. The green shading marks an illustrative range of minus one to plus one grade point.

For page views, a one-standard-deviation increase—one typical spread in the training data—is associated with about 0.34 more grade points on average. But the interval runs from minus 0.21 to plus 0.88. Once grades are included, these associations look small and uncertain. This does not tell us what would happen if we intervened to change a student’s behavior.

Presenter reminder — not part of the spoken script
These are conditional associations, not causal effects. Grade inputs may already capture information shared with engagement and survey measures. The one-point region is illustrative, not an approved coaching threshold. A coefficient’s probability of being positive is not an edge-inclusion probability. LMS means learning management system; EVC means expectancy, value and cost.

Source
posterior_results/coefficient_posteriors.csv; 148-student model fit.

## Slide 5: Most intervals covered outcomes; one missed badly

Here we move from uncertainty about weights to uncertainty about individual grades. The model gave each student a range containing 90% of its predicted grade probability.

Start on the left. For the 43 Spring 2026 students, 39 actual grades fell inside their ranges. The blue part of the bar represents those 39; the red part represents the four misses. That gives 90.7% coverage. It does not mean the grade predictions were “90.7% accurate.”

On the right, we deliberately show the largest error. The blue dot is the predicted mean, 45.9, and the blue band runs from 39.3 to 52.5. The red cross is the actual grade: 20.0. It is far outside the band, and the model overpredicted by 25.9 points.

So the overall coverage looks close to the intended level, but a serious individual miss remains. One small retrospective cohort cannot establish reliable coverage for future students.

Presenter reminder — not part of the spoken script
The displayed failure is the largest absolute error, not a typical case. Spring 2026 was excluded from the fit, but the data and settings were historically explored. This was not an untouched prospective test. Input release timing is unverified; graph, imputation and model-selection uncertainty were excluded from these intervals.

Source
posterior_results/spring2026_probabilities.csv; largest-absolute-error case, identity omitted.

## Slide 6: Did extra inputs improve forecast accuracy?

The last question is whether the extra inputs actually made forecasts better. The large numbers are average absolute errors: how far predictions were from the actual grades, ignoring whether we guessed too high or too low. Lower is better. The arrows mean before and after adding inputs.

On the left, the model started without recorded grades. Adding LMS activity reduced error from 6.54 to 6.36 points. That is a small improvement of 0.18 points, seen in all four evaluation terms.

On the right, the model already had the larger grade bundle. Adding LMS, EVC and wellness increased error from 2.95 to 3.04, worsening all four terms. These are two different starting situations, so we should compare before and after within each box.

What we can say is that our sampling calculation worked well, while the value of extra inputs depended on what the model already knew. Good sampling alone does not guarantee better forecasts.

Presenter reminder — not part of the spoken script
There were 146 predictions per model across four terms, including the 43 Spring cases. Each term’s error score received equal weight. These are retrospective comparisons, not proof of early-warning accuracy or coaching benefits. Some grade inputs directly contribute to final grade, and their release timing is unverified. LMS means learning management system; EVC means expectancy, value and cost.

Source
posterior_results/macro_metrics.csv; posterior_results/paired_gain_summary.csv.

