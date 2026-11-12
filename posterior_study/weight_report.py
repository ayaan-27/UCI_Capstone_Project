"""Write the weight/SMR audit from the user's workbook and saved evidence."""
import json
import pandas as pd
from .analysis import ROOT
OUT=ROOT/'grading_results'
w=pd.read_csv(OUT/'category_weights.csv');a=json.loads((OUT/'weight_audit.json').read_text())
inv=pd.read_csv(OUT/'assignment_inventory.csv');mapping=pd.read_csv(OUT/'historical_assignment_mapping_audit.csv')
def table(head,rows):return '\n'.join(['| '+' | '.join(head)+' |','| '+' | '.join(['---']*len(head))+' |']+['| '+' | '.join(map(str,r))+' |' for r in rows])
main=table(['Main category','Course weight'],[[r.category,f'{r.weight*100:g}%'] for r in w[~w.is_extra_credit].itertuples()])
extra=table(['Extra-credit category','Additional course percentage points at full credit'],[[r.category,f'{r.weight*100:g}'] for r in w[w.is_extra_credit].itertuples()])
pointtable=table(['Category','All inventory points','Published-only points'],[[r.category,f'{r.catalog_points_all:g}',f'{r.catalog_points_published:g}'] for r in w.itertuples() if r.catalog_points_all!=r.catalog_points_published])
report=f'''# Grading weights and summer exclusion

The supplied workbook has been parsed and audited. You confirmed that the **same category weights apply to all six historical non-summer terms**. That confirmation is recorded in `grading_results/grading_config.json`. The assignment dates and item roster in this particular workbook belong to Canvas course **84595** and are not backdated to earlier terms.

## Confirmed category weights

{main}

The main categories sum to **100%**.

{extra}

Extra credit sums to **1 additional percentage point** at full credit under these group weights. Do not divide all ten weights by 1.01: that would reduce the main grade to 99.01% and change the stated grading scheme. The My Learning Coach extra-credit group has zero weight in this workbook; that is grading arithmetic, not evidence about the causal or educational value of MLC.

These are **grading weights**, not estimated effects of wellness, EVC or LMS. Those statistical associations and predictive comparisons are distinct quantities.

## Summer/SMR exclusion

A shared policy now excludes summer/SMR course metadata before numeric temporal evaluation, model benchmarking and RETRO mapping/comparisons. It recognizes case variations and labels such as `2026 SMR`, `2026_SMR` and `Summer`. Summer-labelled predictor/category columns are rejected. Free-text reflections mentioning summer are not scanned as course metadata.

The current processed table already has **no summer students**:

{table(['Included cohort','Students'],[[k,v] for k,v in a['retained_cohort_counts'].items()])}

All **191 students** remain. RETRO also contains only Fall 2025, Winter 2026 and Spring 2026, so none of its 870 response rows is excluded as summer.

The historical grade-column manifest contains **168 SMR-labelled category aggregate entries** across the six exports. **Zero** was included in either assessment bundle. They remain only in the historical eligibility audit; they are not model predictors. The workbook itself already excludes SMR variants and the parser found no summer item/category rows to remove.

The affected analyses were rerun with explicit exclusions. Their numerical findings are unchanged: larger-grade MAE is about 2.9485 for grades only and 3.0364 for all numeric sources. The two-term RETRO text gains remain mixed. Those are still the earlier final-percentage target analyses, not newly fitted remaining-work models.

## What the workbook does and does not establish

The file lists **126 assignments**; **{int(inv.published.sum())} are marked published**. Cached category point subtotals were independently checked against the detailed rows. Source: {a['source_url']}.

Several categories include unpublished items alongside their replacements:

{pointtable}

For example, the verbal groups include both a published 100-point FeedbackFruits oral presentation and an unpublished 64-point upload version. These should not be added together as if both necessarily count. The export explicitly says its subtotals include published and unpublished items. Published status alone also does not establish final effective denominators, dropped/excused policies or student-specific exclusions. The output records both all-inventory and publication-only **scenarios**, without treating either as verified historical grading rules.

The historical mapping audit contains 138 selected source-assignment records (23 per term):

{table(['Mapping status','Records'],[[k,v] for k,v in a['historical_mapping_status_counts'].items()])}

Thus identical category weights do not establish identical assignment denominators or versions. Historical pitch reflections have 16 or 24 possible points; the workbook lists 16. Earlier oral presentations use a 64-point source that is unpublished here. Some historical titles have no exact current match. Other stored features pool assignments—for example, the draft/peer-editing feature combines items that are in different current categories—so their original separate contributions cannot be recovered uniquely from one aggregated percentage.

Even a title/point match does not prove an earlier category had the same total points. No broad fuzzy matching silently renames assignments or transfers the Fall 2026 schedule to earlier students.

Due dates are in **America/Los_Angeles**, as stated in the workbook. **Due dates are not score-release timestamps.** A score appearing in a final export is not proven available on its assignment deadline.

## Weighted remaining-work target

Under verified fixed category rules, for an assignment j in category c:

```
assignment course fraction = category_weight[c] * points_possible[j] / category_total_points[c]
earned contribution in final percentage points = 100 * category_weight[c] * score[j] / category_total_points[c]
```

A full main grade is the sum of these contributions across the active main assignments. Already released scores become a deterministic earned contribution; the model should predict what remains:

```
final_total = known_contribution + (1 - known_main_weight) * remaining_main_percentage + extra_credit_contribution
remaining_main_percentage = (final_total - extra_credit_contribution - known_contribution) / (1 - known_main_weight)
```

The new tested functions in `posterior_study/grading_weights.py` implement this accounting. `known_contributions` uses an effective main-assignment catalog, a student roster and actual historical `available_at` score snapshots. It preserves students without released scores, selects the latest state before a timezone-aware cutoff, and does not revive an earlier score after a later blank revokes it. It rejects incomplete category rosters, ambiguous snapshots and unsupported excused/dropped-score adjustments. Summer metadata is excluded first.

`remaining_target` requires the extra-credit contribution explicitly, rather than assuming it is zero. `combine_final` maps a remaining-performance estimate or simulation draws back to the final scale. It does not clip away accounting mismatches or transfer unpublished catalog items automatically.

**Illustration only, not a result from a real student:** a 20% category has two assignments worth 40 and 60 points. A released score of 30/40 contributes 6 final-percentage points and represents 8% of the main course weight. If the uncapped final total is 80.75 including 0.75 points of extra credit, the normalized remaining-work score is `(80.75 - .75 - 6)/.92 = 80.4348%`. Recombining gives 80.75 exactly.

## What remains before fitting that target

The category-weight question is resolved. The original source ZIP/complete historical grade exports are still needed to recover each term's effective assignment catalog, unaggregated scores and extra-credit contributions. Actual checkpoint score snapshots or release/revision evidence are needed for a verified early forecast. Student-specific excusals/drops and any grade caps or manual adjustments must also be accounted for; an unknown capped final total cannot simply be inverted.

The current processed table contains 16 aggregate assessment features and the reported final percentage, not that complete history. Therefore no new student remaining-work targets, remaining-work posterior effects or accuracy gains have been manufactured from the new workbook. If only final exports can be recovered, clearly labelled retrospective bundle analyses may still be possible; they would not establish week-4 availability.

## Files and reproduction

- `grading_results/grading_config.json`: confirmed main/extra weights, term scope and unresolved denominator/release fields.
- `grading_results/category_weights.csv`: category weights and independently checked point totals.
- `grading_results/assignment_inventory.csv`: all 126 non-summer items, publication status and scenario weights.
- `grading_results/historical_assignment_mapping_audit.csv`: exact-name/point comparison against the six historical source manifests.
- `grading_results/weight_audit.json`: source hash, exclusions, cohort counts and mapping summary.
- `posterior_study/cohort_policy.py`: shared summer exclusion and field guard.
- `posterior_study/grading_weights.py`: workbook extraction, audit and remaining-work accounting.
- `MLC_Weights_SMR_Audit.ipynb`: executed evidence and a clearly labelled arithmetic example.

```
cd /workspace/UCI_Capstone_Project
.venv/bin/python -m posterior_study.grading_weights --weights-xlsx /path/to/ENGR190W_weights.xlsx
.venv/bin/python -m posterior_study.weight_report
.venv/bin/python -m unittest discover -s tests -v
```

No additional Python package is required. The raw upload stays in ignored `data/`; it is not bundled with source archives. Workbook SHA-256: `{a['sha256']}`.

Fourteen statistical/data-integrity tests pass. Six new tests cover summer filtering, a summer RETRO course, category-specific arithmetic, no use of later scores, blank-score revocation, explicit extra credit, timezones and incomplete category rosters. Main and RETRO analyses were rerun after the exclusion changes; results are unchanged because these datasets already contained only non-summer courses.
'''
(ROOT/'WEIGHTS_AND_SMR.md').write_text(report)
print('Wrote WEIGHTS_AND_SMR.md')
