"""Minimal local Streamlit explorer for lineage survival."""

from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC = PROJECT_ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

import streamlit as st

from mrrm import LineageParameters, simulate_lineage_survival
from mrrm.plotting import make_lineage_fitness_figure
from mrrm.validation import ParameterValidationError


def main() -> None:
    st.set_page_config(page_title="Mutation Rate Range Model", layout="wide")
    st.title("Mutation Rate Range Model")
    st.warning(
        "Exploratory lineage-survival model only. Outputs are conditional on "
        "the selected assumptions and are not validated biological estimates."
    )

    params = _sidebar_parameters()
    try:
        results = simulate_lineage_survival(params)
    except (ParameterValidationError, ValueError) as exc:
        st.error(f"Parameter error: {exc}")
        return

    st.subheader("Single mutation-rate lineage run")
    st.caption(
        "One run fixes the mutation-rate multiplier and follows surviving "
        "lineage classes generation by generation."
    )

    outcome = results.outcome
    cols = st.columns(4)
    cols[0].metric("final mean fitness", f"{outcome.final_mean_fitness:.3g}")
    cols[1].metric("best lineage fitness", f"{outcome.final_best_fitness:.3g}")
    cols[2].metric(
        "beneficial adoption",
        f"{outcome.final_beneficial_adoption_fraction:.1%}",
    )
    cols[3].metric("mean decay proxy", f"{outcome.final_mean_decay:.3g}")

    st.plotly_chart(make_lineage_fitness_figure(results), use_container_width=True)

    st.subheader("Run interpretation")
    st.write(
        {
            "mutation_rate_multiplier": params.mutation_rate_multiplier,
            "population_size": params.population_size,
            "beneficial_survived": outcome.beneficial_survived,
            "beneficial_reached_adoption_threshold": outcome.beneficial_adopted,
            "mean_fitness_below_collapse_threshold": outcome.collapsed,
            "final_lineage_classes": outcome.final_lineage_class_count,
            "transition_probabilities": results.transition_probabilities.as_dict(),
        }
    )
    st.caption(
        "D is a scalar mutation-accumulation / genome-decay proxy, not a direct "
        "measurement of every harmful mutation."
    )

    with st.expander("Generation history", expanded=False):
        st.dataframe(
            [record.__dict__ for record in results.history],
            use_container_width=True,
        )

    with st.expander("Final surviving lineage classes", expanded=False):
        st.dataframe(
            [lineage.__dict__ for lineage in results.final_lineages],
            use_container_width=True,
        )


def _sidebar_parameters(defaults: LineageParameters | None = None) -> LineageParameters:
    defaults = defaults or LineageParameters()
    st.sidebar.header("Lineage run")

    mutation_rate_multiplier = st.sidebar.number_input(
        "mutation_rate_multiplier",
        min_value=1e-9,
        value=float(defaults.mutation_rate_multiplier),
        format="%.6g",
    )
    population_size = st.sidebar.number_input(
        "population_size",
        min_value=1,
        value=int(defaults.population_size),
        step=10_000,
    )
    generations = st.sidebar.number_input(
        "generations",
        min_value=1,
        value=int(defaults.generations),
        step=100,
    )
    random_seed = st.sidebar.number_input(
        "random_seed",
        min_value=0,
        value=int(defaults.random_seed or 0),
        step=1,
    )

    with st.sidebar.expander("Mutation supply", expanded=False):
        T_ref = st.number_input(
            "T_ref",
            min_value=1.0,
            value=float(defaults.T_ref),
            step=1_000.0,
        )
        alpha_benefit = st.number_input(
            "alpha_benefit",
            min_value=0.0,
            value=float(defaults.alpha_benefit),
            format="%.6g",
        )
        neutral_rate_scale = st.number_input(
            "neutral_rate_scale",
            min_value=0.0,
            value=float(defaults.neutral_rate_scale),
            format="%.6g",
        )
        decay_scale = st.number_input(
            "decay_scale",
            min_value=0.0,
            value=float(defaults.decay_scale),
            format="%.6g",
        )
        gamma_decay = st.number_input(
            "gamma_decay",
            min_value=1e-9,
            value=float(defaults.gamma_decay),
            format="%.6g",
        )

    with st.sidebar.expander("Inherited effects", expanded=False):
        benefit_scale = st.number_input(
            "benefit_scale",
            min_value=0.0,
            value=float(defaults.benefit_scale),
            format="%.6g",
        )
        beneficial_effect_size = st.number_input(
            "beneficial_effect_size",
            min_value=0.0,
            value=float(defaults.beneficial_effect_size),
            format="%.6g",
        )
        decay_effect_size = st.number_input(
            "decay_effect_size",
            min_value=0.0,
            value=float(defaults.decay_effect_size),
            format="%.6g",
        )
        beta_interference = st.number_input(
            "beta_interference",
            min_value=0.0,
            value=float(defaults.beta_interference),
            format="%.6g",
        )
        gamma_interference = st.number_input(
            "gamma_interference",
            min_value=1e-9,
            value=float(defaults.gamma_interference),
            format="%.6g",
        )

    with st.sidebar.expander("Fitness and survival", expanded=False):
        k_robustness = st.number_input(
            "k_robustness",
            min_value=0.0,
            value=float(defaults.k_robustness),
            format="%.6g",
        )
        lambda_decay = st.number_input(
            "lambda_decay",
            min_value=0.0,
            value=float(defaults.lambda_decay),
            format="%.6g",
        )
        rho_robustness = st.number_input(
            "rho_robustness",
            min_value=0.0,
            value=float(defaults.rho_robustness),
            format="%.6g",
        )
        selection_strength = st.number_input(
            "selection_strength",
            min_value=0.0,
            value=float(defaults.selection_strength),
            format="%.6g",
        )
        minimum_survival_fitness = st.number_input(
            "minimum_survival_fitness",
            min_value=1e-12,
            value=float(defaults.minimum_survival_fitness),
            format="%.6g",
        )

    with st.sidebar.expander("Reporting thresholds", expanded=False):
        max_lineage_classes = st.number_input(
            "max_lineage_classes",
            min_value=1,
            value=int(defaults.max_lineage_classes),
            step=500,
        )
        beneficial_adoption_threshold = st.slider(
            "beneficial_adoption_threshold",
            min_value=0.0,
            max_value=1.0,
            value=float(defaults.beneficial_adoption_threshold),
            step=0.05,
        )
        collapse_fitness_threshold = st.slider(
            "collapse_fitness_threshold",
            min_value=0.0,
            max_value=1.0,
            value=float(defaults.collapse_fitness_threshold),
            step=0.05,
        )

    return LineageParameters(
        generations=int(generations),
        T_ref=T_ref,
        mutation_rate_multiplier=mutation_rate_multiplier,
        population_size=int(population_size),
        benefit_scale=benefit_scale,
        alpha_benefit=alpha_benefit,
        beneficial_effect_size=beneficial_effect_size,
        neutral_rate_scale=neutral_rate_scale,
        decay_scale=decay_scale,
        gamma_decay=gamma_decay,
        decay_effect_size=decay_effect_size,
        beta_interference=beta_interference,
        gamma_interference=gamma_interference,
        k_robustness=k_robustness,
        lambda_decay=lambda_decay,
        rho_robustness=rho_robustness,
        selection_strength=selection_strength,
        minimum_survival_fitness=minimum_survival_fitness,
        random_seed=int(random_seed),
        max_lineage_classes=int(max_lineage_classes),
        beneficial_adoption_threshold=beneficial_adoption_threshold,
        collapse_fitness_threshold=collapse_fitness_threshold,
    )


if __name__ == "__main__":
    main()
