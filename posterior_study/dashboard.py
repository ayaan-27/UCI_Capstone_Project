"""Data and prediction helpers for the what-if dashboard."""

from dataclasses import dataclass

import numpy as np
import pandas as pd
from scipy import stats

from .analysis import CONTEXTS, GRADES, GROUPS, RISK_THRESHOLD, ROOT, TERMS, PosteriorRegression
from .cohort_policy import exclude_summer_rows

LMS = tuple(GROUPS["LMS"])
SURVEY = (*GROUPS["EVC"], *GROUPS["Wellness"])
FEATURE_LABELS = {
    "log_page_views": "Page views",
    "log_lms_participations": "LMS participations",
    "cost_support": "Cost / support score",
    "expectancy": "Expectancy · confidence in succeeding",
    "value": "Value · importance and usefulness",
    "wellness": "Self-reported wellness",
}
GRADE_CUTS = (RISK_THRESHOLD, 80.0, 90.0)
GRADE_BANDS = ("Below 70%", "70–<80%", "80–<90%", "90% or above")
MIN_COHORT_SIZE = 20


def load_features():
    frame, _ = exclude_summer_rows(pd.read_csv(ROOT / "mlc_results/expanded_student_features.csv"))
    return frame[["cohort", "percentage", *GRADES, *LMS, *SURVEY]]


@dataclass(frozen=True)
class Prediction:
    location: np.ndarray
    scale: np.ndarray
    df: float

    @property
    def point(self):
        return np.clip(self.location, 0, 100)

    def interval(self):
        return self.location + stats.t.ppf([[0.05], [0.95]], self.df) * self.scale

    def probability_below(self, cutoff):
        return stats.t.cdf(cutoff, self.df, loc=self.location, scale=self.scale)

    def grade_mix(self):
        """Expected cohort shares from the individual predictive probabilities."""
        cumulative = [self.probability_below(cutoff).mean() for cutoff in GRADE_CUTS]
        return dict(zip(GRADE_BANDS, np.diff([0, *cumulative, 1]), strict=True))


@dataclass(frozen=True)
class ScenarioModel:
    regression: PosteriorRegression
    limits: dict[str, tuple[float, float]]
    cohort_inputs: pd.DataFrame
    training_size: int

    def predict(self, inputs):
        return Prediction(*self.regression.predictive(inputs))


def fit_scenario(frame, term, context, include_survey):
    """Use the study's expanding-window split and training-only preprocessing."""
    earlier_terms = TERMS[:TERMS.index(term)]
    train = frame.loc[frame.cohort.isin(earlier_terms)]
    editable = (*LMS, *SURVEY) if include_survey else LMS
    columns = [*CONTEXTS[context], *editable]
    regression = PosteriorRegression().fit(train[columns], train.percentage)
    limits = {}
    for feature in editable:
        raw = raw_values(feature, train[feature])
        limits[feature] = (float(raw.min()), float(raw.max()))
    return ScenarioModel(regression, limits, frame.loc[frame.cohort.eq(term), columns], len(train))


def raw_values(feature, values):
    return np.expm1(values) if feature in LMS else values


def demo_values(model):
    """Synthetic reference near the earlier terms' medians in display units."""
    values = {}
    for feature in model.limits:
        median = float(raw_values(feature, model.regression.medians[feature]))
        values[feature] = round(median) if feature in LMS else round(median, 2)
    return values


def student_inputs(model, values):
    inputs = model.regression.medians.copy()
    for feature, value in values.items():
        inputs[feature] = np.log1p(value) if feature in LMS else value
    return inputs.to_frame().T


def shift_cohort(inputs, limits, changes):
    """Shift observed activity by a percentage and survey scores by points.

    Preserve missing inputs and prevent further movement outside training ranges.
    The original value stays reachable when a held-out input exceeds those ranges.
    """
    shifted = inputs.copy()
    for feature, delta in changes.items():
        if delta == 0:
            continue
        original = raw_values(feature, inputs[feature])
        if feature in LMS:
            proposed = (original * (1 + delta / 100)).round()
        else:
            proposed = original + delta
        lo, hi = limits[feature]
        bounded = proposed.clip(np.minimum(original, lo), np.maximum(original, hi))
        transformed = np.log1p(bounded) if feature in LMS else bounded
        shifted[feature] = transformed.where(bounded.ne(original), inputs[feature])
    return shifted
