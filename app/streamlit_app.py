"""Minimal local Streamlit explorer for the deterministic model."""

from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC = PROJECT_ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

import streamlit as st

from mrrm import ModelParameters, evaluate_model
from mrrm.plotting import make_curve_figure
from mrrm.validation import ParameterValidationError


def main() -> None:
    st.set_page_config(page_title="Mutation Rate Range Model", layout="wide")
    st.title("Mutation Rate Range Model")
    st.warning(
        "Exploratory deterministic curves only. Outputs are conditional on the "
        "selected assumptions and are not validated biological estimates."
    )

    params = _sidebar_parameters()
    try:
        results = evaluate_model(params)
    except (ParameterValidationError, ValueError) as exc:
        st.error(f"Parameter error: {exc}")
        return

    estimate = results.range_estimate
    st.subheader("Threshold estimates")
    st.caption(
        "Under the selected assumptions, the model estimates approximate "
        "threshold-based mutation-rate multipliers."
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


def _sidebar_parameters() -> ModelParameters:
    defaults = ModelParameters()
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


if __name__ == "__main__":
    main()
