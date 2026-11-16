# MCMC for Our Bayesian DAG — Speaker Notes

The six-slide deck now includes actual structure-MCMC results. Speak the “Spoken walkthrough” sections; the separate reference sections are optional. The script explains each visual’s encodings, finding and limits.

## Slide 1: Why use MCMC to evaluate our Bayesian DAG?

SPOKEN WALKTHROUGH

MCMC samples plausible models or parameter values from the posterior: their probabilities after combining assumptions with data. We now have two analyses, shown in the two boxes. On the left, the new structure sampler changes arrows and records which connections recur. Its main analysis uses 111 students with complete data. We retained 40,000 graphs for each of eight tested settings. On the right, the earlier Gibbs sampler keeps the graph fixed and varies predictor weights and unexplained grade variation. That model used 148 earlier students.

The two analyses answer different questions. I will first show the actual graph findings, then the computational checks and the earlier forecast results.

REFERENCE — ONLY IF ASKED

MCMC means Markov chain Monte Carlo. A Bayesian DAG is a directed graph without directed loops. The posterior combines prior assumptions with data. The graph study excludes assessment components; its main data span all six terms. The eight settings vary priors, missing-data handling, cohort demeaning and the included terms. The 111 and 148 are different analysis samples, not additional groups to add together.

SOURCES

structure_results/provenance.json; posterior_results/provenance.json; posterior_study/structure_learning.py and analysis.py.

## Slide 2: Three survey connections recur across settings

SPOKEN WALKTHROUGH

Read the connection names down the left. The horizontal axis shows the percentage of sampled graphs containing each connection, in either direction. A dot is the main complete-data analysis. A band spans the smallest and largest percentages across our eight settings. It compares settings, rather than showing an uncertainty interval within one model.

The three green dots are near 100%, with very short bands: expectancy–value, cost/support–wellness, and cost/support–expectancy stayed above 98.9%. The orange page-views–grade dot is only 52.5%, and its band spans about 19.5% to 99.8%. That link depends heavily on the assumptions and data handling. We can therefore describe a stable survey cluster, while remaining cautious about a direct grade connection.

REFERENCE — ONLY IF ASKED

Exact ranges: expectancy–value 99.9625–100%; cost/support–wellness 98.9925–100%; cost/support–expectancy 98.9025–100%. A frequency of 100% means every retained graph contained the connection; it does not prove certainty. The survey variables come from the same collection system, so shared response patterns or unmeasured factors may contribute. These are model-dependent exploratory associations, not causal effects or independent replications.

SOURCES

structure_results/connection_stability.csv; edge_probabilities_all_scenarios.csv; README.md.

## Slide 3: Connection support does not settle arrow direction

SPOKEN WALKTHROUGH

This bar zooms in on cost/support and expectancy. Their connection appears in 99.7% of the main-analysis graphs. Among graphs containing it, blue shows cost/support pointing to expectancy, and green shows the reverse. The bar splits about 54% and 46%, so neither direction has clear dominance.

Markov equivalence explains part of the difficulty: some different graph orientations imply the same observed relationships. The other edges and our assumptions also affect the shares, so they need not be equal. The defensible result is that these measures are connected. We have not established that changing one causes the other to change.

REFERENCE — ONLY IF ASKED

The bar is conditional on the connection being present. Unconditional frequencies are 53.86% cost/support → expectancy, 45.875% reverse and 0.265% absent. The aggregate 54/46 split is not itself a test that every sampled graph belongs to one equivalence class. BGe gives equal likelihood scores to equivalent DAGs; this was tested by exact three-variable enumeration. Observational data and unverified timing do not establish causal direction.

SOURCES

structure_results/main_edge_probabilities.csv; tests/test_structure_learning.py.

## Slide 4: Gibbs samples matched the exact posterior

SPOKEN WALKTHROUGH

Now we check the calculations. In this earlier fixed-graph analysis, the horizontal axis shows possible LMS page-view weights. Blue bars show how often nearby weights appeared in Gibbs samples. The horizontal axis measures grade points per one standard-deviation increase in page views, holding other inputs fixed. One standard deviation means one typical spread in training values. The green curve is the exact posterior. Their close overlap shows the sampler reproduced the expected uncertainty distribution.

The card reports agreement between the fixed-model chains: R-hat is 1.0007, close to the desired value of one. There are at least 12,194 effective samples, an estimate of usable information despite similarity between consecutive draws. Separately, the new structure sampler passed an exact three-variable test and its monitored R-hat stayed below 1.003. These checks support the calculations; they do not establish causality or forecast accuracy.

REFERENCE — ONLY IF ASKED

The plotted curve and bars describe one fixed-regression coefficient, not a graph-edge probability. The fixed model has a closed-form reference. Seven-node graph probabilities were not exactly enumerated; exact validation used all 25 three-node DAGs. Structure diagnostics cover nonrare varying indicators, graph score and edge count; constant indicators have no estimable R-hat. All 18 tests passed. R-hat and effective sample size support monitoring, not proof of global convergence.

SOURCES

posterior_results/mcmc_diagnostics.csv; structure_results/provenance.json; Validation_Log.txt.

## Slide 5: Most intervals covered outcomes; one missed badly

SPOKEN WALKTHROUGH

For the earlier fixed model, each 90% prediction interval contains 90% of that student’s predicted grade probability. The left panel shows that 39 of 43 actual Spring 2026 grades fell inside their intervals: 90.7% coverage. The blue portion of the bar represents those 39; red represents the four misses.

The right panel deliberately shows the largest error. The blue dot is the predicted mean, 45.9; the blue band runs from 39.3 to 52.5. The red cross is the actual grade, 20.0. It is far outside the band. This shows why overall coverage can look good while an individual forecast fails badly.

REFERENCE — ONLY IF ASKED

This is one small retrospective cohort, not a new prospective calibration study. These forecasts predate the new graph sampler and were not generated by its sampled graphs. The new exploratory graph study used complete cases from all six terms; it did not create a fresh holdout. Prediction intervals omit imputation, graph and model-selection uncertainty; input release timing remains unverified. The selected failure is the largest absolute error, not a typical case.

SOURCES

posterior_results/spring2026_probabilities.csv; 148-student training fit, 43 evaluated cases.

## Slide 6: Did extra inputs improve forecast accuracy?

SPOKEN WALKTHROUGH

The large numbers are average absolute grade errors: lower is better. The arrow in each card means before and after adding inputs; it is not a causal arrow. On the left, adding LMS activity without recorded grades reduced error from 6.54 to 6.36 points, improving all four evaluation terms. On the right, when the larger grade bundle was already available, adding LMS, EVC and wellness increased error from 2.95 to 3.04, worsening all four terms.

These are different starting situations, not a direct comparison between the cards. Our conclusion is that survey connections recur, causal directions remain uncertain, and predictive value depends on what the model already knows.

REFERENCE — ONLY IF ASKED

LMS means learning management system; EVC means expectancy, value and cost. Scores average each evaluation term equally across four terms and 146 predictions per model, including the 43 Spring cases. These are earlier fixed-model forecasts, not a prospective evaluation of the new structure-learning model. Some grade inputs directly contribute to final grade; release timing is unverified. Neither graph support nor error comparisons show a coaching intervention benefit.

SOURCES

posterior_results/macro_metrics.csv and paired_gain_summary.csv; structure_results/README.md.

