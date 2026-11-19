import unittest

import numpy as np
import pandas as pd

from posterior_study.analysis import RISK_THRESHOLD, ROOT, TERMS
from posterior_study.dashboard import (
    GRADE_BANDS,
    LMS,
    demo_values,
    fit_scenario,
    load_features,
    shift_cohort,
    student_inputs,
)


class DashboardTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.features = load_features()

    def test_baseline_matches_later_term_study(self):
        term = TERMS[-1]
        model = fit_scenario(self.features, term, "Block B", include_survey=True)
        outcome = self.features.loc[self.features.cohort.eq(term), "percentage"]
        baseline = model.predict(model.cohort_inputs)
        metrics = pd.read_csv(ROOT / "posterior_results/temporal_metrics.csv")
        reported = metrics.loc[
            metrics.term.eq(term) & metrics.context.eq("Block B") & metrics.group.eq("LMS+EVC+Wellness")
        ].iloc[0]
        self.assertEqual(model.training_size, reported.n_train)
        self.assertEqual(len(outcome), reported.n)
        self.assertAlmostEqual(np.abs(baseline.point - outcome).mean(), reported.MAE)
        shares = baseline.grade_mix()
        self.assertAlmostEqual(sum(shares.values()), 1.0)
        self.assertTrue(all(0 <= share <= 1 for share in shares.values()))
        self.assertAlmostEqual(shares[GRADE_BANDS[0]], baseline.probability_below(RISK_THRESHOLD).mean())

    def test_scenario_keeps_fixed_assessment_inputs(self):
        model = fit_scenario(self.features, TERMS[-1], "Block A", include_survey=False)
        reference = demo_values(model)
        page_views = LMS[0]
        baseline = student_inputs(model, reference)
        changed = student_inputs(model, {**reference, page_views: round(model.limits[page_views][1])})
        pd.testing.assert_frame_equal(baseline.drop(columns=page_views), changed.drop(columns=page_views))
        self.assertNotAlmostEqual(model.predict(baseline).point[0], model.predict(changed).point[0])

    def test_cohort_shifts_keep_missing_values_and_bound_changes(self):
        page_views = LMS[0]
        inputs = pd.DataFrame({
            page_views: np.log1p([150, 260, 10, np.nan]),
            "expectancy": [5.8, 6.2, np.nan, 1.2],
            "paper_a_pct": [78, 82, 84, 80],
        })
        limits = {page_views: (20, 200), "expectancy": (1, 6)}
        baseline = shift_cohort(inputs, limits, {page_views: 0, "expectancy": 0.0})
        pd.testing.assert_frame_equal(baseline, inputs)
        changed = shift_cohort(inputs, limits, {page_views: 50, "expectancy": 0.4})
        np.testing.assert_allclose(np.expm1(changed[page_views]), [200, 260, 15, np.nan])
        np.testing.assert_allclose(changed.expectancy, [6, 6.2, np.nan, 1.6])
        pd.testing.assert_series_equal(changed.paper_a_pct, inputs.paper_a_pct)
