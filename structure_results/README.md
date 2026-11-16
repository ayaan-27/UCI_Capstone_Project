# Which connections are consistently supported?

This is a **new exploratory structure-MCMC analysis**, distinct from the earlier fixed-DAG Gibbs regression sampler. It samples changes to arrows, with no directions imposed. It does not establish causal effects.

## Main finding

Three survey connections appeared repeatedly across all eight tested settings. These are probabilities of **a connection in either direction**, not probabilities of a causal arrow.

| Connection | Main analysis: fraction of graphs containing the connection | Range across eight tested settings |
|---|---:|---:|
| EVC expectancy — EVC value | 100.00% | 99.96–100.00% |
| EVC cost/support — Wellness | 100.00% | 98.99–100.00% |
| EVC cost/support — EVC expectancy | 99.73% | 98.90–100.00% |

The clear pattern is a connected group of **wellness, cost/support, expectancy and value**. A compact way to display the supported connections is:

`Wellness — Cost/support — Expectancy — Value`

The lines deliberately have no arrows. The measures come from the same survey collection system and can share response patterns or unmeasured causes. This does not show that changing any one measure improves another or improves grades.

A value of 100% here means that every one of the 40,000 retained sampled graphs contained that connection. It does not establish a mathematically certain population relationship or an exact posterior probability of one.

## Direction remains uncertain

Main-analysis frequencies for the two possible arrows are:

| Pair (A, B) | A → B | B → A | No connection |
|---|---:|---:|---:|
| EVC expectancy, EVC value | 69.69% | 30.30% | 0.00% |
| EVC cost/support, Wellness | 72.29% | 27.71% | 0.00% |
| EVC cost/support, EVC expectancy | 53.86% | 45.88% | 0.27% |

These are unconditional directed-edge frequencies, so the three columns sum to 100% up to rounding. Equivalent DAGs receive equal likelihood scores under the BGe model. Aggregate direction frequencies need not split 50/50: each arrow may occur in different numbers and kinds of graphs. Observational data, prior assumptions and the seven-variable model do not establish causal direction. In particular, the roughly balanced cost/support–expectancy directions illustrate why connection support is stronger than direction support.

## What about final grade?

The LMS page-views–final-grade connection appeared in **52.45%** of main-analysis graphs, but ranged from **19.46% to 99.82%** across the eight settings. It is **not consistently strong** under these checks. No connection to final grade exceeded 95% in every tested setting.

This does not contradict the earlier forecast comparisons or fixed-regression coefficient results. The new graph analysis uses seven variables without assessment grades, mostly survey-complete respondents, and asks about joint conditional relationships. The earlier regression held assessment grades fixed and evaluated a different question. Absence of an edge in this model does not prove that a variable has no association, indirect influence or predictive information.

## Data and design

- Seven variables: log LMS page views, log LMS participation, cost/support, expectancy, value, wellness, and final percentage. Assessment components are excluded because they contribute directly to final grade.
- The processed table has 191 unique students across six non-summer terms. Each survey variable is missing for 78 students and both LMS variables for two students. The main complete-case analysis has **111 students**. It uses all six terms, including Spring 2026, so it is not a new held-out or prospective evaluation.
- The eight settings are: main complete cases; sparser graph prior; uniform-over-DAG prior; one-quarter prior scale; four-times prior scale; within-cohort demeaning; median filling with 191 students; and earlier five terms only with 82 complete cases.
- Within-cohort demeaning is a plug-in sensitivity check, not a hierarchical model. Median filling ignores missing-value uncertainty and is only a sensitivity check. Complete cases can differ systematically from nonrespondents.
- A linear-Gaussian Bayesian network is scored with **BGe**, integrating a compatible normal-Wishart prior. Every subset uses degrees of freedom `|subset| + 2`, mean precision 1, and scale matrix `prior_scale / 2 * I`, after centering and scaling each analysis dataset. This is an empirical scale convention, not an externally fixed prior in raw measurement units.
- The graph prior assigns each unordered pair probabilities `(1-q, q/2, q/2)` for no edge, forward or reverse, jointly conditioned on acyclicity. The main q is 0.5; sensitivities use 0.2 and 2/3. Because of acyclicity, q is not the marginal prior connection probability. q=2/3 is uniform over DAGs. No topological ordering, parent cap or causal direction is imposed.
- A symmetric Metropolis-Hastings proposal selects a pair and one of its other two states. Cyclic proposals are rejected. No legal-neighbor-count correction is needed because proposals are symmetric.
- Each setting uses four chains from empty to dense starting graphs. Each chain has 20,000 warm-up proposals and 100,000 subsequent proposals, retaining every tenth state: **40,000 graphs per setting**, 320,000 across all settings. Seed: 7291 plus chain index.

## Validation and numerical uncertainty

The largest split/folded rank R-hat among monitored nonrare varying indicators, graph scores and edge counts was **1.0023** across all settings; the smallest bulk effective sample size was **2,028**. Main-analysis values were **1.0019** and **2,850**. These support agreement for the monitored quantities, not a proof of global exploration. The independent chain means are available in the edge tables.

Exactly constant indicators have no estimable R-hat/ESS and are explicitly flagged. Bernoulli tail ESS is not reported because tail quantile indicators can be constant. For graph-score diagnostic ranks only, scores are rounded to eight decimal places to treat numerically equal equivalent-DAG scores as ties; this does not affect proposal acceptance or graph probabilities. Raw scores and graph samples are retained.

All **18 tests passed**, including four new checks: scalar marginal likelihood against independent sequential Student-t prediction; score equivalence for all 25 three-node DAGs grouped into 11 equivalence classes; sampled joint graph and directed-edge frequencies against exact three-node enumeration; and rejection of cyclic/invalid inputs. The original 14 statistical/data-integrity tests also passed.

## Limits and presentation wording

The sensitivity range is a comparison of different assumptions/datasets, **not a posterior credible interval**. It does not measure stability across independent new cohorts. These are Gaussian approximations to bounded/averaged survey measures and grades; alternative likelihoods, latent factors, missing-not-at-random responses and verified temporal ordering could change the interpretation. Raw source files and independent prospective data are not available.

Suggested wording:

> “When we sampled alternative seven-variable graphs, three connections among expectancy, value, cost/support and wellness recurred in at least 98.9% of graphs across our eight tested settings. Their causal directions were not established. Connections to final grade were much less stable.”

## Reproduce

From the repository root, with the existing Python 3.12 environment:

```bash
OPENBLAS_NUM_THREADS=2 OMP_NUM_THREADS=2 .venv/bin/python -m unittest discover -s tests -v
OPENBLAS_NUM_THREADS=2 OMP_NUM_THREADS=2 .venv/bin/python -m posterior_study.structure_learning --output /path/to/fresh/results
```

The input SHA-256, settings and chain diagnostics are in `provenance.json`. Edge probabilities and sensitivity ranges are in `main_edge_probabilities.csv`, `edge_probabilities_all_scenarios.csv` and `connection_stability.csv`. Compressed sampled graphs store one parent-bitmask per node in the variable order listed in provenance. The PNG is a presentation-ready summary; its ranges are sensitivity ranges.
