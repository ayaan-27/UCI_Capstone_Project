"""My Learning Coach research dashboard. Run with streamlit run streamlit_app.py."""

from math import ceil, floor

import altair as alt
import pandas as pd
import streamlit as st

from posterior_study.analysis import CONTEXTS, RISK_THRESHOLD, ROOT, TERMS
from posterior_study.dashboard import (
    FEATURE_LABELS,
    GRADE_BANDS,
    LMS,
    MIN_COHORT_SIZE,
    SURVEY,
    demo_values,
    fit_scenario,
    load_features,
    raw_values,
    shift_cohort,
    student_inputs,
)

BASELINE = "Baseline"
SCENARIO = "What-if"
COMPARISON = [BASELINE, SCENARIO]
COLORS = ["#64748b", "#2457d5"]
DEMO_PAGE_VIEW_CHANGE = 20
CONTEXT_LABELS = {
    "No grades": "No assessment grades",
    "Block A": "Block A · 10 assessments",
    "Block B": "Block B · 16 assessments",
}
TERM_NAMES = {"FAL": "Fall", "WTR": "Winter", "SPR": "Spring"}
TERM_LABELS = {
    term: f"{TERM_NAMES[season]} {year}"
    for term in TERMS
    for year, season in [term.split()]
}
EVIDENCE_MODELS = {
    "Baseline": "Baseline",
    "LMS": "LMS only",
    "LMS+EVC+Wellness": "LMS + surveys",
}


@st.cache_data
def feature_data():
    return load_features()


@st.cache_resource
def scenario_model(term, context, include_survey):
    return fit_scenario(feature_data(), term, context, include_survey)


@st.cache_data
def evidence_data():
    return (
        pd.read_csv(ROOT / "posterior_results/temporal_metrics.csv"),
        pd.read_csv(ROOT / "posterior_results/macro_metrics.csv"),
    )


def settings(key, default="No grades"):
    context = st.selectbox(
        "Assessment evidence",
        list(CONTEXTS),
        index=list(CONTEXTS).index(default),
        format_func=CONTEXT_LABELS.get,
        key=f"{key}_context",
    )
    include_survey = st.toggle(
        "Include exploratory survey inputs",
        key=f"{key}_survey",
        help=(
            "Fits the study’s LMS + EVC + wellness model. The study found mixed results when adding surveys."
        ),
    )
    return context, include_survey


def reset_widgets(values):
    for key, value in values.items():
        st.session_state[key] = value


def offset(value):
    return f"{value:+.1f} pp" if abs(value) >= 0.05 else "0.0 pp"


def comparison_color(legend=None):
    return alt.Color(
        "Scenario:N",
        sort=COMPARISON,
        scale=alt.Scale(domain=COMPARISON, range=COLORS),
        legend=legend,
    )


def show_chart(chart, description):
    chart = chart.configure(
        background="#fff",
        view=alt.ViewConfig(stroke=None),
        axis=alt.AxisConfig(labelColor="#4b607d", titleColor="#4b607d", gridColor="#e4eaf3"),
        legend=alt.LegendConfig(labelColor="#4b607d"),
    )
    st.altair_chart(chart, width="stretch", alt=description)


def prediction_interval_chart(rows):
    source = pd.DataFrame(rows)
    low = floor(min(source.Lower.min(), source.Estimate.min())) - 2
    high = ceil(max(source.Upper.max(), source.Estimate.max())) + 2
    chart = alt.Chart(source).encode(
        y=alt.Y("Scenario:N", sort=COMPARISON, axis=alt.Axis(title=None, labelPadding=9)),
        color=comparison_color(),
    )
    x_axis = alt.Axis(title="Final course score (%)", tickCount=5)
    interval = chart.mark_rule(strokeWidth=3).encode(
        x=alt.X("Lower:Q", scale=alt.Scale(domain=[low, high]), axis=x_axis),
        x2="Upper:Q",
    )
    point = chart.mark_circle(size=100, opacity=1, stroke="white", strokeWidth=1.5).encode(
        x=alt.X("Estimate:Q", scale=alt.Scale(domain=[low, high]), axis=x_axis),
        tooltip=[
            "Scenario",
            alt.Tooltip("Estimate:Q", title="Point estimate (%)", format=".1f"),
            alt.Tooltip("Lower:Q", title="Lower bound (%)", format=".1f"),
            alt.Tooltip("Upper:Q", title="Upper bound (%)", format=".1f"),
        ],
    )
    return (interval + point).properties(height=132)


def grade_band_chart(baseline, scenario):
    source = pd.DataFrame(
        {"Scenario": name, "Band": band, "Share": share}
        for name, prediction in zip(COMPARISON, (baseline, scenario), strict=True)
        for band, share in prediction.grade_mix().items()
    )
    return (
        alt.Chart(source)
        .mark_bar(cornerRadiusTopLeft=4, cornerRadiusTopRight=4)
        .encode(
            x=alt.X("Band:N", sort=list(GRADE_BANDS), axis=alt.Axis(title=None, labelAngle=0)),
            xOffset=alt.XOffset("Scenario:N", sort=COMPARISON),
            y=alt.Y("Share:Q", axis=alt.Axis(title="Expected share", format="%", tickCount=4)),
            color=comparison_color(alt.Legend(title=None, orient="top")),
            tooltip=["Band", "Scenario", alt.Tooltip("Share:Q", format=".1%")],
        )
        .properties(height=212)
    )


def student_view():
    controls, results = st.columns([1, 1.85], gap="medium")
    with controls, st.container(key="student-controls", border=True):
        st.subheader("Scenario inputs")
        st.caption("Edit a synthetic profile based on earlier-term medians.")
        context, include_survey = settings("student")
        model = scenario_model(TERMS[-1], context, include_survey)
        references = demo_values(model)
        values = {}
        st.markdown("**LMS activity**")
        st.caption(f"Baseline · {references[LMS[0]]:,} page views and {references[LMS[1]]:,} participations")
        for feature, (lower, upper) in model.limits.items():
            reference = references[feature]
            initial = reference
            if feature in LMS:
                lower, upper, step, display = round(lower), round(upper), 1, "%d"
                if feature == LMS[0]:
                    initial = min(upper, round(reference * (1 + DEMO_PAGE_VIEW_CHANGE / 100)))
            else:
                lower = ceil(lower * 100 - 1e-8) / 100
                upper = floor(upper * 100 + 1e-8) / 100
                step, display = 0.01, "%.2f"
            if feature == SURVEY[0]:
                st.markdown("**Survey scores**")
                st.caption("The direction of the cost / support scale is unverified.")
            key = f"student_{feature}"
            st.session_state.setdefault(key, initial)
            help_text = f"Baseline {reference:,}. Range comes from earlier terms."
            if feature in LMS:
                help_text += " Counts cover the study’s assumed first four weeks."
            values[feature] = st.slider(
                FEATURE_LABELS[feature], lower, upper, step=step, format=display, key=key, help=help_text,
            )
        st.button(
            "Reset to baseline",
            key="reset_student",
            on_click=reset_widgets,
            args=({f"student_{feature}": value for feature, value in references.items()},),
        )

    baseline = model.predict(student_inputs(model, references))
    scenario = model.predict(student_inputs(model, values))
    baseline_risk = baseline.probability_below(RISK_THRESHOLD)[0]
    scenario_risk = scenario.probability_below(RISK_THRESHOLD)[0]
    rows = []
    for name, prediction in zip(COMPARISON, (baseline, scenario), strict=True):
        lower, upper = prediction.interval()[:, 0]
        rows.append({"Scenario": name, "Estimate": prediction.point[0], "Lower": lower, "Upper": upper})

    with results, st.container(key="student-results", border=True):
        st.subheader("Predicted final grade")
        st.caption(f"Bayesian model fitted to {model.training_size} records through Winter 2026.")
        current, what_if, risk = st.columns([1, 1, 1.15], gap="small")
        current.metric("Baseline estimate", f"{baseline.point[0]:.1f}%")
        what_if.metric(
            "What-if estimate",
            f"{scenario.point[0]:.1f}%",
            offset(scenario.point[0] - baseline.point[0]),
            delta_color="off",
            delta_arrow="off",
            delta_description="vs baseline",
        )
        risk.metric(
            f"What-if below {RISK_THRESHOLD:g}%",
            f"{scenario_risk:.1%}",
            offset(100 * (scenario_risk - baseline_risk)),
            delta_color="off",
            delta_arrow="off",
            delta_description="vs baseline",
            help=f"Model probability at an illustrative score threshold. Baseline {baseline_risk:.1%}.",
        )
        st.markdown("**90% prediction intervals**")
        show_chart(
            prediction_interval_chart(rows),
            "Final grade point estimate and 90% prediction interval for each scenario.",
        )
        st.caption("  ·  ".join(f"{r['Scenario']} {r['Lower']:.1f}–{r['Upper']:.1f}%" for r in rows))
        if any(r["Lower"] < 0 or r["Upper"] > 100 for r in rows):
            st.caption("The model’s continuous prediction interval can extend beyond 0–100%.")
        if context != "No grades":
            st.caption("Both scenarios use the same median assessment scores. Grade-release timing is unverified.")
        st.info("The model estimates historical associations. Measuring the effect of a change in practice requires a separate evaluation.")


def faculty_view():
    controls, results = st.columns([1, 1.85], gap="medium")
    eligible = feature_data().groupby("cohort").size()
    terms = [term for term in reversed(TERMS[2:]) if eligible.get(term, 0) >= MIN_COHORT_SIZE]
    if not terms:
        controls.info(f"Cohort comparison requires at least {MIN_COHORT_SIZE} records in an evaluation term.")
        return

    with controls, st.container(key="faculty-controls", border=True):
        st.subheader("Cohort scenario")
        st.caption("Apply an input change to a historical cohort.")
        term = st.selectbox("Evaluation term", terms, format_func=TERM_LABELS.get, key="faculty_term")
        context, include_survey = settings("faculty")
        model = scenario_model(term, context, include_survey)
        changes = {}
        st.markdown("**LMS activity**")
        for feature in LMS:
            key = f"faculty_{feature}"
            st.session_state.setdefault(key, DEMO_PAGE_VIEW_CHANGE if feature == LMS[0] else 0)
            changes[feature] = st.slider(
                f"{FEATURE_LABELS[feature]} change",
                -50, 50, step=5, format="%d%%", key=key,
            )
        if include_survey:
            st.markdown("**Survey scores**")
            st.caption("Shifts are in score points. The direction of the cost / support scale is unverified.")
            for feature in SURVEY:
                key = f"faculty_{feature}"
                st.session_state.setdefault(key, 0.0)
                changes[feature] = st.slider(
                    f"{FEATURE_LABELS[feature]} change",
                    -1.0, 1.0, step=0.1, format="%.1f", key=key,
                )
        st.button(
            "Reset to baseline",
            key="reset_faculty",
            on_click=reset_widgets,
            args=({f"faculty_{feature}": 0 if feature in LMS else 0.0 for feature in changes},),
        )

    original = model.cohort_inputs
    adjusted = shift_cohort(original, model.limits, changes)
    baseline, scenario = model.predict(original), model.predict(adjusted)
    baseline_risk = baseline.probability_below(RISK_THRESHOLD).mean()
    scenario_risk = scenario.probability_below(RISK_THRESHOLD).mean()
    with results, st.container(key="faculty-results", border=True):
        st.subheader("Predicted cohort distribution")
        st.caption(f"{TERM_LABELS[term]} · {len(original)} records · Fitted on {model.training_size} earlier records")
        current, what_if, risk = st.columns([1, 1, 1.15], gap="small")
        current.metric("Baseline mean grade", f"{baseline.point.mean():.1f}%")
        what_if.metric(
            "What-if mean grade",
            f"{scenario.point.mean():.1f}%",
            offset(scenario.point.mean() - baseline.point.mean()),
            delta_color="off",
            delta_arrow="off",
            delta_description="vs baseline",
        )
        risk.metric(
            f"What-if share below {RISK_THRESHOLD:g}%",
            f"{scenario_risk:.1%}",
            offset(100 * (scenario_risk - baseline_risk)),
            delta_color="off",
            delta_arrow="off",
            delta_description="vs baseline",
            help=f"Expected cohort share at an illustrative cutoff. Baseline {baseline_risk:.1%}.",
        )
        show_chart(
            grade_band_chart(baseline, scenario),
            "Expected cohort share in each grade band under the baseline and edited inputs.",
        )
        st.caption(
            "Shares average the model’s predictive probabilities. Shifts respect earlier data ranges "
            "and preserve recorded starting values. Missing values use earlier-term medians."
        )
        if context != "No grades":
            st.caption("Assessment scores stay fixed. Their historical release dates are unverified.")

    with results, st.container(key="faculty-activity", border=True):
        st.subheader("Average LMS inputs")
        st.caption("Recorded and edited counts, averaged over records with LMS data.")
        input_table = pd.DataFrame(
            {
                "Activity": FEATURE_LABELS[feature],
                "Baseline": raw_values(feature, original[feature]).mean(),
                "What-if": raw_values(feature, adjusted[feature]).mean(),
            }
            for feature in LMS
        )
        st.dataframe(
            input_table, hide_index=True,
            column_config={name: st.column_config.NumberColumn(format="%.0f")
                           for name in COMPARISON},
            alt="Average observed and edited LMS counts.",
        )


def evidence_view():
    temporal, macro = evidence_data()
    with st.container(key="evidence-results", border=True):
        st.subheader("How accurately did the models predict later terms?")
        st.caption("Each model was fitted on earlier terms and checked on the next term. Lower error is better.")
        context = st.selectbox(
            "Assessment evidence", list(CONTEXTS), index=2, format_func=CONTEXT_LABELS.get, key="evidence_context",
        )
        rows = macro.loc[macro.context.eq(context) & macro.group.isin(EVIDENCE_MODELS)]
        errors = rows.set_index("group").MAE
        for col, (group, label) in zip(st.columns(3), EVIDENCE_MODELS.items(), strict=True):
            col.metric(label, f"{errors[group]:.2f} pts", help="Mean absolute error, weighting each term equally.")
        folds = temporal.loc[temporal.context.eq(context) & temporal.group.isin(EVIDENCE_MODELS)].copy()
        folds["Model"] = folds.group.map(EVIDENCE_MODELS)
        folds["Term"] = folds.term.map(TERM_LABELS)
        series = list(EVIDENCE_MODELS.values())
        chart = (
            alt.Chart(folds[["Term", "Model", "MAE"]])
            .mark_line(point=True, strokeWidth=2.5)
            .encode(
                x=alt.X("Term:N", sort=[TERM_LABELS[t] for t in TERMS[2:]], axis=alt.Axis(title=None, labelAngle=0)),
                y=alt.Y("MAE:Q", axis=alt.Axis(title="Mean absolute error (points)", tickCount=4)),
                color=alt.Color("Model:N", sort=series, scale=alt.Scale(domain=series, range=[*COLORS, "#a56222"]),
                                legend=alt.Legend(title=None, orient="top")),
                tooltip=["Term", "Model", alt.Tooltip("MAE:Q", title="Error (points)", format=".2f")],
            )
            .properties(height=230)
        )
        show_chart(chart, "Mean absolute error by model for four later-term checks.")
        st.caption(
            "Baseline uses only the selected assessment bundle, or the training mean when no assessments "
            "are selected. These are retrospective checks on previously explored data."
        )

    with st.container(key="evidence-pilot", border=True):
        st.subheader("Before a live pilot")
        st.markdown(
            "- Choose a forecast date and recover the grade-release history for it. Verify the LMS window "
            "and survey scoring, including the meaning of the cost / support score.\n"
            "- Test on new cohorts and check that predicted probabilities match observed frequencies. "
            "Set any support threshold with course staff.\n"
            "- To add Bloom levels, reflection sentiment, or weekly engagement forecasts, collect and "
            "validate those measures for the chosen forecast date. Agree on data access and cohort privacy "
            "rules before connecting live student records."
        )


st.set_page_config(page_title="My Learning Coach | What-if dashboard", layout="wide")
st.html(ROOT / "posterior_study/dashboard.css")
st.html(
    """
    <header class="mlc-hero">
        <div class="mlc-brand">
            <span class="mlc-emblem" aria-hidden="true"><i></i><i></i><i></i></span>
            <span>My Learning Coach</span>
        </div>
        <span class="mlc-demo">Research demo</span>
        <h1>What-if dashboard</h1>
        <p>Compare grade estimates under different inputs with the capstone’s Bayesian model.</p>
    </header>
    """
)
student_tab, faculty_tab, evidence_tab = st.tabs(["Student view", "Faculty view", "Model evidence"])
with student_tab:
    student_view()
with faculty_tab:
    faculty_view()
with evidence_tab:
    evidence_view()
