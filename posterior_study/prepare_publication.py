"""Prepare the GitHub-safe deliverables; never push or include source uploads.

python -m posterior_study.prepare_publication --output /workspace/MLC_Capstone_Public
Uses completed derived results. Numeric analysis runs with the public processed
input; RETRO/workbook recomputation requires the user's omitted source files.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
import zipfile
from .analysis import ROOT
from . import create_release as release


def clean_sections(sections):
    substitutions={
        'The supplied RETRO and weight files are now included in the runnable package.':'Source uploads are excluded from the public GitHub package; code and derived results are included.',
        'Raw responses are included for local reproducibility but are not quoted in the report or slides.':'Raw responses are omitted from the public package and are not quoted in the report or slides.',
        'This package is a filesystem snapshot of current work, not a claim of a published environment or a Git push.':'This package is a validated artifact snapshot; GitHub publication is identified by the repository commit.',
    }
    def clean(value):
        if isinstance(value,str):
            for before,after in substitutions.items():value=value.replace(before,after)
            return value
        if isinstance(value,list):return [clean(v) for v in value]
        if isinstance(value,tuple):return tuple(clean(v) for v in value)
        return value
    return clean(sections)


def build_public(output):
    output=Path(output).resolve()
    if output==ROOT or ROOT in output.parents:raise ValueError('Choose an output outside the source repository')
    if output.exists() and any(output.iterdir()):raise ValueError('Public output must be new or empty')
    output.mkdir(parents=True,exist_ok=True)
    release.register_fonts();e=release.evidence()
    release.copy_project(output/'03_Project',include_inputs=False)
    project=output/'03_Project'
    # Override private-distribution run instructions copied by the common builder.
    (project/'data/README.md').write_text('''# Source files excluded from GitHub

The public package contains no uploaded RETRO response CSV, workbook, prior chat, tokens, virtual environment or credential files. The derived processed table is in ../mlc_results/.

To recompute the optional raw-input stages locally, place your own original RETRO CSV at data/retro_uploaded.csv and your workbook at data/assignment_weights_uploaded.xlsx, or pass their paths to the modules. Original historical grade/source ZIP and release/revision snapshots remain unavailable. Existing derived tables and all 14 tests can be used without those uploads.
''')
    (project/'README.md').write_text('''# Runnable public project

The current report and presentation are in ../02_Report/ and ../01_Presentation/. Four notebooks, the existing anonymized processed table, code, tests and all derived results are included. Uploaded source responses/workbooks and chat history are excluded.

```bash
python3.12 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
bash run_available_studies.sh
```

The runner always executes the numeric study and all 14 tests. RETRO and workbook recomputation run only when the omitted inputs are provided locally at the paths documented in data/README.md. All derived result tables remain available even when those optional source files are absent. The original raw-data notebook still requires the missing historical source ZIP.

Optional presentation/report rebuild:

```bash
.venv/bin/python -m pip install -r posterior_study/requirements-presentation.txt
.venv/bin/python -m posterior_study.prepare_publication --output /path/to/new/public-package
```

Notebook order: original DAG; posterior predictive value; RETRO follow-up; weights/SMR audit. The latter three have saved executed outputs. The original execution is preserved, not newly reproduced from raw data. Summer/SMR is excluded. The remaining-work accounting is tested; actual historical remaining-work targets/models are not fitted. No causal effects are established.
''')
    runner='''#!/usr/bin/env bash
set -euo pipefail
cd -- "$(dirname -- "$0")"
if [[ ! -x .venv/bin/python ]]; then
  echo "Create .venv with Python 3.12 and install requirements.txt first." >&2
  exit 1
fi
export OPENBLAS_NUM_THREADS=2
export OMP_NUM_THREADS=2
export MPLCONFIGDIR="${TMPDIR:-/tmp}/mlc-matplotlib"
.venv/bin/python -m posterior_study.analysis
if [[ -f data/retro_uploaded.csv ]]; then
  .venv/bin/python -m posterior_study.retro_followup --retro-csv data/retro_uploaded.csv
else
  echo "SKIP RETRO recomputation: supply data/retro_uploaded.csv locally; derived results are included."
fi
if [[ -f data/assignment_weights_uploaded.xlsx ]]; then
  .venv/bin/python -m posterior_study.grading_weights --weights-xlsx data/assignment_weights_uploaded.xlsx
else
  echo "SKIP workbook extraction: supply data/assignment_weights_uploaded.xlsx locally; audited weights are included."
fi
.venv/bin/python -m unittest discover -s tests -v
'''
    (project/'run_available_studies.sh').write_text(runner);(project/'run_available_studies.sh').chmod(0o755)
    release.presentation(output/'01_Presentation',e,public=True)
    release.reports(output/'02_Report',e,sections=clean_sections(release.report_sections(e)))
    release.diagrams(output/'04_Diagrams')
    # Earlier public project artifacts already remain in the repository history;
    # do not import private user-provided context into the public distribution.
    archive=output/'05_Archive';archive.mkdir()
    (archive/'README.md').write_text('# Earlier versions\n\nEarlier public project presentations and results remain in the GitHub repository and its history. They are not duplicated here. Uploaded reference files, source responses and pasted conversations are excluded. Use the consolidated report for the current interpretation.\n')
    (output/'00_START_HERE.md').write_text('''# My Learning Coach — public GitHub package

## Start with the current deliverables

- 01_Presentation/MLC_Consolidated_Presentation.pptx — editable 19-slide talk (16 main + 3 appendix).
- 01_Presentation/MLC_Consolidated_Presentation.pdf — portable slide copy.
- 01_Presentation/Speaker_Notes.pdf — first-person rehearsal notes.
- 02_Report/MLC_Consolidated_Report.pdf — integrated research report.
- 03_Project/ — four notebooks, code, tests, processed input and complete derived tables/figures.
- 04_Diagrams/ — full original DAG and a labelled temporal proposal.

The main sample contains 191 non-summer students. All-source additions do not improve the larger-grade MAE; LMS alone has a modest no-grades signal. RETRO text gains are mixed. No causal or coaching effects are established. Weights are confirmed; remaining-work arithmetic is tested, but historical remaining-work targets/models are not fitted.

## What is omitted

Uploaded RETRO responses, the original workbook, pasted conversation/context and environment/credential files are not published. Supply your own raw files locally to recompute those stages. Their derived audit tables and the already-public anonymized processed feature table are included. The original historical source ZIP and score-availability history remain missing.

Open INDEX.html after unzipping for navigation. See 03_Project/README.md for installation and running. The public package passes the same 14 tests without the omitted raw inputs. MANIFEST.json hashes all shipped files.
''')
    (project/'NOTEBOOK_ORDER.md').write_text('''# Notebook order

1. MLC_Bayesian_DAG_updated.ipynb — original supplied execution, raw rerun blocked by missing historical ZIP.
2. MLC_Posterior_Predictive_Value.ipynb — executed posterior/source study using included processed rows.
3. MLC_RETRO_Followup.ipynb — executed result display; raw RETRO recomputation requires your local CSV.
4. MLC_Weights_SMR_Audit.ipynb — executed weight audit/arithmetic example; source workbook must be supplied locally for re-extraction.

These are explored retrospective analyses. Two-term RETRO MAEs and four-term numeric MAEs use different training/evaluation windows.
''')
    report=output/'02_Report'
    result=subprocess.run([sys.executable,'-m','unittest','discover','-s','tests','-v'],cwd=project,capture_output=True,text=True,timeout=120)
    (report/'Validation_Log.txt').write_text(result.stdout+result.stderr)
    if result.returncode or 'Ran 14 tests' not in result.stderr:raise RuntimeError('Public project tests failed')
    import nbformat
    notebooks={}
    for p in project.glob('*.ipynb'):
        n=nbformat.read(p,as_version=4);nbformat.validate(n)
        if any(o.output_type=='error' for c in n.cells if c.cell_type=='code' for o in c.get('outputs',[])):raise ValueError(f'Notebook output error: {p.name}')
        notebooks[p.name]='saved execution preserved and structure validated'
    validation={'tests_executed':14,'tests_passed':14,'test_exit_code':0,'test_working_directory':'03_Project','uploaded_inputs_included':False,'pasted_chat_included':False,'environment_or_credential_files_included':False,'notebooks':notebooks,'consolidated_slides':19,'original_raw_workflow_rerun':False,'remaining_work_model_fitted':False}
    (report/'Validation.json').write_text(json.dumps(validation,indent=2))
    for p in project.rglob('__pycache__'):shutil.rmtree(p)
    release.render_previews(output)
    # Replace only the public landing-page wording; common index metadata is neutral.
    release.index_and_manifest(output,validation)
    page=output/'INDEX.html';page.write_text(page.read_text().replace('supplied inputs and labelled archives','input requirements and labelled archives'))
    manifest=output/'MANIFEST.json';m=json.loads(manifest.read_text());m['files']['INDEX.html']={'bytes':page.stat().st_size,'sha256':release.sha(page)};m['distribution']='public GitHub; source uploads and pasted chat excluded';manifest.write_text(json.dumps(m,indent=2))
    print(json.dumps({'output':str(output),'tests_passed':14,'public_inputs_omitted':True},indent=2))
    return output


def make_zip(public_root,target):
    public_root=Path(public_root);target=Path(target)
    forbidden=[]
    for p in public_root.rglob('*'):
        if not p.is_file():continue
        rel=p.relative_to(public_root)
        if p.name.startswith('.env') or p.suffix in ['.csv','.xlsx'] and rel.parts[:2]==('03_Project','data') or 'User_Provided_Context' in rel.parts or p.name=='Pasted text.txt':forbidden.append(str(rel))
    if forbidden:raise ValueError(f'Unexpected private files: {forbidden}')
    review=public_root/'01_Presentation/_rendered_review'
    if review.exists():shutil.rmtree(review)
    target.parent.mkdir(parents=True,exist_ok=True)
    with zipfile.ZipFile(target,'w',zipfile.ZIP_DEFLATED) as z:
        for p in sorted(public_root.rglob('*')):
            if p.is_file():z.write(p,Path('MLC_Capstone_Public')/p.relative_to(public_root))
    with zipfile.ZipFile(target) as z:
        if z.testzip() is not None:raise ValueError('ZIP validation failed')
    return target


if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--output',type=Path,required=True)
    args=ap.parse_args();build_public(args.output)
