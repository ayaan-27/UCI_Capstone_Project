# My Learning Coach — Bayesian DAG capstone

## Download the current artifacts

**[Download the complete public package](https://github.com/ayaan-27/UCI_Capstone_Project/raw/refs/heads/main/deliverables/MLC_Capstone_Public.zip)**

| Current deliverable | Download |
|---|---|
| Consolidated presentation — 16 main slides + 3 appendix slides | [Editable PowerPoint](https://github.com/ayaan-27/UCI_Capstone_Project/raw/refs/heads/main/deliverables/MLC_Consolidated_Presentation.pptx) · [PDF](https://github.com/ayaan-27/UCI_Capstone_Project/raw/refs/heads/main/deliverables/MLC_Consolidated_Presentation.pdf) |
| Integrated research report | [PDF](https://github.com/ayaan-27/UCI_Capstone_Project/raw/refs/heads/main/deliverables/MLC_Consolidated_Report.pdf) · [Markdown](deliverables/MLC_Consolidated_Report.md) |
| First-person speaker notes | [PDF](https://github.com/ayaan-27/UCI_Capstone_Project/raw/refs/heads/main/deliverables/MLC_Speaker_Notes.pdf) · [Markdown](deliverables/MLC_Speaker_Notes.md) |
| Validation | [14-test log](deliverables/Validation_Log.txt) · [Summary](deliverables/Validation.json) |

Open a file on GitHub and use **Download raw file** near the top-right of the viewer, or use these direct links. **Code → Download ZIP** downloads the repository. After unzipping the public package, start with `00_START_HERE.md` or `INDEX.html`.

## Current findings

- **191 students, six non-summer terms.** SMR/Summer courses and summer-labelled predictor fields are excluded.
- With the larger grade bundle, all numeric non-grade sources increase four-term macro MAE from **2.9485 to 3.0364** points.
- Without grades, LMS alone improves macro MAE from **6.5377 to 6.3607**, improving all four evaluation terms. EVC/wellness additions do not demonstrate a stable benefit beyond grades in this model.
- Coefficient posteriors describe uncertain **conditional associations**, not causal effects. Gibbs MCMC agrees with the exact conjugate solution; more sampling does not establish predictive usefulness.
- Newly supplied RETRO is **free text**, separate from early numerical EVC. Week 2/4 text has mixed gains across only two evaluation terms and does not consistently beat response-pattern measures in the larger-grade scenario.
- Tested robust and tree alternatives do not beat the simple larger-grade Bayesian/Ridge baseline.
- Confirmed main category weights sum to **100%**, with up to **1 extra-credit percentage point** kept separate. Remaining-work accounting is implemented/tested; actual historical remaining-work outcomes and models are not fitted.

These are explored retrospective comparisons with unverified grade-release timing, not independent prospective confirmation or evidence of coaching effectiveness. Numeric and RETRO experiments use different training windows; their MAEs should not be conflated.

## Project structure

| Path | Purpose |
|---|---|
| `deliverables/` | Current presentation, report, notes and downloadable public ZIP |
| `posterior_study/` | Statistical models, Gibbs diagnostics, RETRO/text comparison, weight audit, summer policy and packaging |
| `tests/` | 14 statistical and data-integrity tests |
| `posterior_results/` | Four-term ablations, posterior summaries, risks, diagnostics, sensitivities and figures |
| `retro_followup_results/` | RETRO audits, two-term text comparisons and candidate-model benchmarks |
| `grading_results/` | Confirmed weights, assignment inventory and historical mapping audit |
| `mlc_results/` | Original processed input, fixed DAG and earlier executed-study outputs |
| `diagrams/` | Complete original DAG and explicitly labelled temporal proposal |
| `docs/` | Earlier workspace guide for historical context |

Original presentations remain in the repository root for traceability. The files in `deliverables/` are the current combined account.

## Notebook order

1. `MLC_Bayesian_DAG_updated.ipynb` — original stored execution, extraction and fixed DAG. A raw rerun requires the missing original source ZIP.
2. `MLC_Posterior_Predictive_Value.ipynb` — executed posterior simulation, actual Gibbs sampling and source comparisons using included processed data.
3. `MLC_RETRO_Followup.ipynb` — executed display of RETRO and model-benchmark results.
4. `MLC_Weights_SMR_Audit.ipynb` — executed grading/summer audit and a labelled hypothetical arithmetic example.

## Install and reproduce

Use Python 3.12; the completed study used 3.12.14. Keep the existing isolated checkout in cloud tasks; no worktree is needed unless explicitly requested.

```bash
python3.12 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
bash run_available_studies.sh
```

The runner executes the numeric study and all 14 tests. It skips RETRO/workbook recomputation with a clear message when the user-provided source files are absent; existing derived results remain available. To recompute those stages locally, provide `data/retro_uploaded.csv` and `data/assignment_weights_uploaded.xlsx`, or pass your paths directly:

```bash
.venv/bin/python -m posterior_study.retro_followup --retro-csv /path/to/retro.csv
.venv/bin/python -m posterior_study.grading_weights --weights-xlsx /path/to/weights.xlsx
```

Optional public-artifact rebuild:

```bash
.venv/bin/python -m pip install -r posterior_study/requirements-presentation.txt
.venv/bin/python -m posterior_study.prepare_publication --output /path/to/new/public-package
```

No API key is required. Graphviz is optional for the original notebook. Inputs and environment directories are ignored by Git. Do not print or commit credentials.

## Included results and omitted source files

The uploaded RETRO response CSV, original workbook, pasted chat/context and environment/credential files are **not published**. The existing anonymized processed table and derived numerical findings are included. The original historical grade/source ZIP, effective historical denominators and score-release/revision history remain unavailable. Their absence prevents a newly verified historical early/remaining-work forecasting study; it does not invalidate the documented retrospective computations.
