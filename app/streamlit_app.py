"""Minimal local Streamlit explorer for the deterministic model."""

from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC = PROJECT_ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

import streamlit as st

from mrrm import (
    CalibrationResult,
    ModelParameters,
    available_generations,
    available_strains,
    build_calibration_audit,
    derive_calibrated_parameters,
    evaluate_model,
    select_calibration_observations,
)
from mrrm.data_loaders import (
    DataValidationError,
    build_calibration_inventory,
    build_data_inventory,
    load_calibration_dataset,
    load_processed_observations,
    load_source_registry,
)
from mrrm.plotting import make_curve_figure, make_raw_observation_figure
from mrrm.validation import ParameterValidationError


def main() -> None:
    st.set_page_config(page_title="Mutation Rate Range Model", layout="wide")
    st.title("Mutation Rate Range Model")
    st.warning(
        "Exploratory deterministic curves only. Outputs are conditional on the "
        "selected assumptions and are not validated biological estimates."
    )
    observations = _load_calibration_observations()

    st.sidebar.title("Calibrated from data")
    if observations:
        strain_options = available_strains(observations)
        selected_strain = st.sidebar.selectbox("Strain", strain_options, index=0)
        generations = available_generations(observations, selected_strain)
        default_generation = max([generation for generation in generations if generation > 0] or generations)
        target_generation = st.sidebar.number_input(
            "Generation horizon T",
            min_value=1.0,
            value=float(default_generation),
            step=500.0,
        )
        calibration = derive_calibrated_parameters(
            observations,
            strain=selected_strain,
            target_generation=target_generation,
        )
        st.sidebar.caption(
            "Experimental observations derive supported inputs first; unsupported "
            "inputs remain marked in provenance."
        )
        show_calibration_audit = st.sidebar.checkbox("Show calibration audit", value=True)
        manual_overrides = st.sidebar.checkbox("Enable manual overrides", value=False)
        if manual_overrides:
            params = _sidebar_parameters(calibration.params)
            mode_label = "calibrated base with manual overrides"
        else:
            params = calibration.params
            mode_label = "calibrated from data"
    else:
        calibration = None
        selected_strain = None
        show_calibration_audit = False
        st.sidebar.caption(
            "Calibration data could not be loaded, so the app is using fallback "
            "exploratory parameters."
        )
        params = _sidebar_parameters(ModelParameters())
        mode_label = "fallback exploratory parameters"

    try:
        results = evaluate_model(params)
    except (ParameterValidationError, ValueError) as exc:
        st.error(f"Parameter error: {exc}")
        return

    estimate = results.range_estimate
    st.subheader("Threshold estimates")
    st.caption(
        f"Mode: {mode_label}. Thresholds respond to the model inputs currently "
        "shown in the parameter provenance and sidebar."
    )
    if calibration is not None:
        st.caption(
            f"Calibration driver: strain {calibration.selected_strain}, "
            f"generation horizon {calibration.target_generation:.0f}; "
            f"closest experimental generation {calibration.closest_generation}."
        )
    cols = st.columns(3)
    cols[0].metric("mu_min", _format_optional(estimate.mu_min))
    cols[1].metric("mu_peak", f"{estimate.mu_peak:.3g}x")
    cols[2].metric("mu_max", _format_optional(estimate.mu_max))

    st.plotly_chart(make_curve_figure(results), use_container_width=True)

    with st.expander("Threshold details", expanded=False):
        st.write(
            {
                "benefit_threshold": estimate.benefit_threshold,
                "net_threshold": estimate.net_threshold,
                "decay_threshold": estimate.decay_threshold,
                "peak_score": estimate.peak_score,
            }
        )
        st.caption(
            "D is a scalar decay proxy, not a direct measurement of every harmful mutation."
        )

    if calibration is not None:
        _render_parameter_provenance(calibration)
        if show_calibration_audit and observations is not None:
            _render_calibration_audit(observations, calibration)
    _render_calibration_dataset(calibration)
    _render_data_inventory()


def _sidebar_parameters(defaults: ModelParameters | None = None) -> ModelParameters:
    defaults = defaults or ModelParameters()
    st.sidebar.header("Model inputs")

    T = st.sidebar.number_input(
        "Generation horizon T",
        min_value=1.0,
        value=float(defaults.T),
        step=1_000.0,
    )
    T_ref = st.sidebar.number_input(
        "Reference horizon T_ref",
        min_value=1.0,
        value=float(defaults.T_ref),
        step=1_000.0,
    )
    m_min = st.sidebar.number_input(
        "Minimum mutation-rate multiplier",
        min_value=1e-6,
        value=float(defaults.m_min),
        format="%.6g",
    )
    m_max = st.sidebar.number_input(
        "Maximum mutation-rate multiplier",
        min_value=1e-6,
        value=float(defaults.m_max),
        format="%.6g",
    )
    n_points = st.sidebar.slider(
        "Evaluation points",
        min_value=20,
        max_value=2_000,
        value=defaults.n_points,
        step=20,
    )

    with st.sidebar.expander("Adaptive benefit", expanded=False):
        benefit_scale = st.number_input("benefit_scale", min_value=0.0, value=defaults.benefit_scale)
        alpha_benefit = st.number_input("alpha_benefit", min_value=0.0, value=defaults.alpha_benefit)
        beta_interference = st.number_input(
            "beta_interference",
            min_value=0.0,
            value=defaults.beta_interference,
            format="%.6g",
        )
        gamma_interference = st.number_input(
            "gamma_interference",
            min_value=1e-6,
            value=defaults.gamma_interference,
            format="%.6g",
        )

    with st.sidebar.expander("Decay and robustness", expanded=False):
        decay_scale = st.number_input("decay_scale", min_value=0.0, value=defaults.decay_scale)
        gamma_decay = st.number_input(
            "gamma_decay",
            min_value=1e-6,
            value=defaults.gamma_decay,
            format="%.6g",
        )
        k_robustness = st.number_input(
            "k_robustness",
            min_value=0.0,
            value=defaults.k_robustness,
            format="%.6g",
        )
        lambda_decay = st.number_input(
            "lambda_decay",
            min_value=0.0,
            value=defaults.lambda_decay,
            format="%.6g",
        )
        rho_robustness = st.number_input(
            "rho_robustness",
            min_value=0.0,
            value=defaults.rho_robustness,
            format="%.6g",
        )

    with st.sidebar.expander("Threshold rules", expanded=False):
        benefit_threshold_fraction = st.slider(
            "benefit_threshold_fraction",
            min_value=0.0,
            max_value=1.0,
            value=defaults.benefit_threshold_fraction,
            step=0.05,
        )
        net_threshold_fraction = st.slider(
            "net_threshold_fraction",
            min_value=0.0,
            max_value=1.0,
            value=defaults.net_threshold_fraction,
            step=0.05,
        )
        decay_threshold_fraction = st.slider(
            "decay_threshold_fraction",
            min_value=0.0,
            max_value=1.0,
            value=defaults.decay_threshold_fraction,
            step=0.05,
        )

    return ModelParameters(
        T=T,
        T_ref=T_ref,
        m_min=m_min,
        m_max=m_max,
        n_points=n_points,
        benefit_scale=benefit_scale,
        alpha_benefit=alpha_benefit,
        beta_interference=beta_interference,
        gamma_interference=gamma_interference,
        decay_scale=decay_scale,
        gamma_decay=gamma_decay,
        k_robustness=k_robustness,
        lambda_decay=lambda_decay,
        rho_robustness=rho_robustness,
        benefit_threshold_fraction=benefit_threshold_fraction,
        net_threshold_fraction=net_threshold_fraction,
        decay_threshold_fraction=decay_threshold_fraction,
    )


def _format_optional(value: float | None) -> str:
    if value is None:
        return "not identified"
    return f"{value:.3g}x"


def _render_data_inventory() -> None:
    st.subheader("Experimental-data inventory")
    st.info("Example/schema data only — not calibrated model input yet.")

    try:
        inventory = build_data_inventory()
        sources = load_source_registry()
        observations = load_processed_observations()
    except DataValidationError as exc:
        st.error(f"Experimental-data validation error: {exc}")
        return

    cols = st.columns(3)
    cols[0].metric("registered sources", inventory["source_count"])
    cols[1].metric("processed observations", inventory["observation_count"])
    cols[2].metric(
        "rows with mutation-rate values",
        inventory["numeric_field_counts"]["mutation_rate_multiplier"],
    )

    with st.expander("Registered sources", expanded=False):
        st.dataframe(sources, use_container_width=True)

    with st.expander("Example processed observations", expanded=False):
        st.dataframe(observations, use_container_width=True)


def _load_calibration_observations() -> list[dict] | None:
    try:
        return load_calibration_dataset()
    except DataValidationError:
        return None


def _render_calibration_dataset(calibration: CalibrationResult | None = None) -> None:
    st.subheader("Raw experimental observations")
    st.info(
        "calibration_dataset_v0 currently contains real Sprouffske et al. 2018 "
        "mutation-rate values and confidence intervals, plus curated Dryad "
        "growth-curve relative-fitness observations for the existing strain, "
        "replicate, and final-generation calibration slots. Fitness values name "
        "their same-batch ancestor controls. The dataset still does not contain "
        "mutation-count/genome-decay costs or robustness observations."
    )
    st.caption(
        "Curated relative-fitness values are r_evo - r_anc from Dryad "
        "growth-curves.txt. The raw Dryad final timepoint is generation 2907; "
        "the paper labels this final timepoint as approximately 3000 generations."
    )

    try:
        observations = load_calibration_dataset()
        inventory = build_calibration_inventory()
    except DataValidationError as exc:
        st.error(f"Calibration-data validation error: {exc}")
        return
    selected_observations = (
        select_calibration_observations(
            observations,
            strain=calibration.selected_strain,
            target_generation=calibration.target_generation,
        )
        if calibration is not None
        else observations
    )

    cols = st.columns(3)
    cols[0].metric("raw observations", inventory["observation_count"])
    cols[1].metric("fitness values", inventory["fitness_observation_count"])
    cols[2].metric("missing fitness rows", inventory["missing_fitness_observation_count"])

    if calibration is not None:
        st.caption(
            f"Showing selected calibration rows for strain {calibration.selected_strain} "
            f"at closest experimental generation {calibration.closest_generation}."
        )
    st.plotly_chart(make_raw_observation_figure(selected_observations), use_container_width=True)

    with st.expander("selected calibration rows", expanded=False):
        st.dataframe(selected_observations, use_container_width=True)
    with st.expander("all calibration_dataset_v0 rows", expanded=False):
        st.dataframe(observations, use_container_width=True)


def _render_calibration_audit(
    observations: list[dict],
    calibration: CalibrationResult,
) -> None:
    st.subheader("Calibration audit")
    st.caption(
        "Audit tables separate selected-strain-only fitting from all-strain fitting. "
        "Rows with negative relative fitness remain in residual tables but are not "
        "used to fit the current non-negative benefit curve."
    )
    audit = build_calibration_audit(
        observations,
        selected_strain=calibration.selected_strain,
        target_generation=calibration.target_generation,
    )

    selected_tab, all_tab, loo_tab = st.tabs(
        ["Selected strain", "All strains", "Leave-one-strain-out"]
    )
    with selected_tab:
        _render_audit_fit(audit.selected_strain_fit)
    with all_tab:
        _render_audit_fit(audit.all_strain_fit)
    with loo_tab:
        st.caption(
            "Each row trains on all other strains and evaluates residuals on the "
            "held-out strain's exact relative-fitness observations."
        )
        st.dataframe(audit.leave_one_strain_out, use_container_width=True)


def _render_audit_fit(audit_fit) -> None:
    st.markdown(f"**{audit_fit.label}**")
    cols = st.columns(4)
    cols[0].metric("selected rows", len(audit_fit.selected_rows))
    cols[1].metric("observed fitness rows", len(audit_fit.observed_rows))
    cols[2].metric("fit rows", len(audit_fit.fit_rows))
    cols[3].metric("excluded rows", len(audit_fit.excluded_rows))

    st.caption("Objective/loss on rows used for benefit fitting.")
    st.write(audit_fit.objective)
    st.caption("Threshold estimate from this calibration scope.")
    st.write(audit_fit.threshold_estimate)

    with st.expander("Rows used for fitting", expanded=True):
        st.dataframe(audit_fit.fit_rows, use_container_width=True)
    with st.expander("Fitted benefit/interference parameters", expanded=True):
        st.dataframe(audit_fit.fitted_parameters, use_container_width=True)
    with st.expander("Predicted vs observed fitness and residuals", expanded=True):
        st.dataframe(audit_fit.predictions, use_container_width=True)
    with st.expander("Observed rows excluded from benefit fitting", expanded=False):
        st.dataframe(audit_fit.excluded_rows, use_container_width=True)


def _render_parameter_provenance(calibration: CalibrationResult) -> None:
    st.subheader("Model input provenance")
    st.caption(
        "Every model input is classified as empirical, fitted, assumed, or "
        "unsupported by the current data. Unsupported values remain exploratory "
        "fallbacks until exact observations are curated."
    )
    st.dataframe(calibration.provenance_rows(), use_container_width=True)


if __name__ == "__main__":
    main()
