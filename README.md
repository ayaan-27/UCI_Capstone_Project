# My Learning Coach — Bayesian DAG capstone

## Deliverables
- `MLC_technical_presentation.pptx`: six editable slides following a plain-language research story, with first-person speaker notes.
- `MLC_technical_presentation.pdf`: portable presentation copy.
- `MLC_speaker_notes.txt`: a connected first-person script for speaking to a professor.
- `MLC_speaker_notes.pdf`: the same script in a readable six-page rehearsal copy.
- `MLC_Bayesian_DAG_updated.ipynb`: rerun original study plus audited additions.
- `mlc_results/`: generated tables, provenance, predictions and fitted DAG.

## Run the notebook
Use Python 3.12 and install `requirements.txt` in a virtual environment. Put the original uploaded `Annoymized Data…zip` alongside the notebook, or set `MLC_DATA_ZIP` to its path. Run All. A local `data/` directory is extracted and `mlc_results/` is generated. Original uploads are unchanged. The source archive is not included in this repository. Graphviz is optional; the notebook has a Matplotlib graph fallback. No external API key is needed.

## What changed
- Clarified the unit of analysis: 191 unique student-course observations, not thousands of independent students.
- Added per-term sample/missingness audits, source-archive SHA-256 and runtime versions.
- Implemented the training-mean baseline that the original notebook mentioned but did not calculate.
- Retained conjugate CPD posterior quantities without changing original plug-in point predictions.
- Added exact Student-t outcome-CPD predictions for complete retained evidence, integrating coefficient and variance uncertainty conditional on fixed preprocessing/imputed training inputs. Missing evidence is explicitly rejected by this new interface; original joint-Gaussian marginal inference remains available.
- Compared exact and plug-in intervals on matching complete-case subsets: full model n=29, grades-only n=43. These are diagnostics, not a new selected model or a full Bayesian missing-data solution.
- Added and verified a conjugate sequential-update function with preprocessing frozen; this is a tested building block, not a deployed online learner.
- Kept original diagnostic/selection separation and clarified unverifiable historical timing.

## Reproduced main evidence
Three earlier-term development folds select Block B, coefficient precision 10 (macro MAE 3.0868). Final training n=148; reused Spring 2026 evaluation n=43. Full-model MAE 2.8322 points, RMSE 4.9203, R² 0.8175. Same-bundle/precision grades-only MAE 2.8190; train-mean MAE 8.1282. Plug-in 90% intervals cover 39/43 with mean width 10.0209. Past-error calibration also covers 39/43 and has width 11.7424. This does not demonstrate survey/LMS incremental MAE improvement or independent prospective validation.

## Boundaries
Release timestamps and historical score snapshots are absent. The first-four-week survey/LMS features do not make Block A/B verified week-4 forecasts. Calendar starts are assumptions to verify. Current fitted DAG has no explicit MLC exposure/use, latent prior ability, section effects or term hierarchy. Training missingness is median-imputed; Gaussian support is unbounded, and clipping is only a reporting projection. Letter-grade accuracy uses illustrative thresholds rather than official recorded grade labels. No causal or coaching-effectiveness claim is supported.

The repository contains the reviewed presentation, executed notebook and generated research results. Raw source exports and the uploaded data archive are excluded; supply the original archive locally to rerun the workflow.

## Quick start

```bash
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
```

Open `MLC_Bayesian_DAG_updated.ipynb` in a notebook editor, select the virtual environment, and run all cells. Keep the original data ZIP locally; `data/`, source ZIPs and virtual environments are ignored by Git.

## Presentation flow

1. What a Bayesian DAG is: a map of assumed relationships, learned from data.
2. Which student records fill the map.
3. How the model learns and makes a forecast, with a real historical example.
4. How earlier terms are used to check predictions for later students.
5. What the results show, including the grades-only comparison and uncertainty.
6. How to test whether surveys and online activity help at an earlier date.

The slides explain model terms in plain language. The notes are written as connected first-person speech, with a transition to the next slide. All numerical results still come from the executed notebook; the prediction model and notebook were not changed for this presentation revision. The final experiment is proposed work, not a new result.
