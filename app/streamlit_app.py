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
from mrrm.formatting import format_count_compact
from mrrm.plotting import make_lineage_population_figure
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
    cols = st.columns(5)
    cols[0].metric(
        "final population",
        format_count_compact(outcome.final_actual_population_size),
        f"cap {format_count_compact(outcome.carrying_capacity)}",
    )
    cols[1].metric("final mean fitness", f"{outcome.final_mean_fitness:.3g}")
    cols[2].metric("best lineage fitness", f"{outcome.final_best_fitness:.3g}")
    cols[3].metric(
        "beneficial adoption",
        f"{outcome.final_beneficial_adoption_fraction:.1%}",
    )
    cols[4].metric(
        "total lineages evolved",
        format_count_compact(outcome.final_total_lineages_evolved),
    )

    st.caption(
        "Population counts use the left axis. Mean fitness uses the right axis."
    )
    st.plotly_chart(make_lineage_population_figure(results), use_container_width=True)

    st.subheader("Run interpretation")
    st.write(
        {
            "mutation_rate_multiplier": params.mutation_rate_multiplier,
            "effective_population_size": params.effective_population_size,
            "final_actual_population_size": outcome.final_actual_population_size,
            "final_viable_population_size": outcome.final_viable_population_size,
            "total_lineages_evolved": outcome.final_total_lineages_evolved,
            "final_benefit_led_population_size": (
                results.history[-1].beneficial_dominant_population_size
            ),
            "final_decay_led_population_size": (
                results.history[-1].harmful_dominant_population_size
            ),
            "beneficial_survived": outcome.beneficial_survived,
            "beneficial_reached_adoption_threshold": outcome.beneficial_adopted,
            "collapsed": outcome.collapsed,
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

    _render_model_audit(results)


def _sidebar_parameters(defaults: LineageParameters | None = None) -> LineageParameters:
    defaults = defaults or LineageParameters()
    st.sidebar.header("Model inputs")

    with st.sidebar.expander("Experimental setup", expanded=True):
        mutation_rate_multiplier = st.number_input(
            "mutation_rate_multiplier",
            min_value=1e-9,
            value=float(defaults.mutation_rate_multiplier),
            format="%.6g",
        )
        effective_population_size = st.number_input(
            "effective_population_size",
            min_value=1,
            value=int(defaults.effective_population_size),
            step=10_000,
        )
        generations = st.number_input(
            "generations",
            min_value=1,
            value=int(defaults.generations),
            step=100,
        )

    with st.sidebar.expander("Mutation supply", expanded=True):
        neutral_mutation_rate = st.number_input(
            "neutral_mutation_rate",
            min_value=0.0,
            value=float(defaults.neutral_mutation_rate),
            format="%.6g",
        )
        deleterious_mutation_rate = st.number_input(
            "deleterious_mutation_rate",
            min_value=0.0,
            value=float(defaults.deleterious_mutation_rate),
            format="%.6g",
        )
        beneficial_mutation_rate = st.number_input(
            "beneficial_mutation_rate",
            min_value=0.0,
            value=float(defaults.beneficial_mutation_rate),
            format="%.6g",
        )

    with st.sidebar.expander("Mutation effects", expanded=True):
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
        benefit_saturation = st.number_input(
            "benefit_saturation",
            min_value=0.0,
            value=float(defaults.benefit_saturation),
            format="%.6g",
        )
        robustness_decay_rate = st.number_input(
            "robustness_decay_rate",
            min_value=0.0,
            value=float(defaults.robustness_decay_rate),
            format="%.6g",
        )
        interference_strength = st.number_input(
            "interference_strength",
            min_value=0.0,
            value=float(defaults.interference_strength),
            format="%.6g",
        )
        interference_exponent = st.number_input(
            "interference_exponent",
            min_value=1e-9,
            value=float(defaults.interference_exponent),
            format="%.6g",
        )

    with st.sidebar.expander("Selection and survival", expanded=True):
        selection_strength = st.number_input(
            "selection_strength",
            min_value=0.0,
            value=float(defaults.selection_strength),
            format="%.6g",
        )
        viability_fitness_threshold = st.number_input(
            "viability_fitness_threshold",
            min_value=0.0,
            value=float(defaults.viability_fitness_threshold),
            format="%.6g",
        )
        lethal_decay_threshold = st.number_input(
            "lethal_decay_threshold",
            min_value=0.0,
            value=float(defaults.lethal_decay_threshold),
            format="%.6g",
        )
        minimum_viable_robustness = st.number_input(
            "minimum_viable_robustness",
            min_value=0.0,
            max_value=1.0,
            value=float(defaults.minimum_viable_robustness),
            format="%.6g",
        )
        decay_fitness_penalty = st.number_input(
            "decay_fitness_penalty",
            min_value=0.0,
            value=float(defaults.decay_fitness_penalty),
            format="%.6g",
        )
        robustness_fitness_weight = st.number_input(
            "robustness_fitness_weight",
            min_value=0.0,
            value=float(defaults.robustness_fitness_weight),
            format="%.6g",
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

    with st.sidebar.expander("Advanced simulation controls", expanded=False):
        random_seed = st.number_input(
            "random_seed",
            min_value=0,
            value=int(defaults.random_seed or 0),
            step=1,
        )
        max_lineage_classes = st.number_input(
            "max_lineage_classes",
            min_value=1,
            value=int(defaults.max_lineage_classes),
            step=500,
        )

    return LineageParameters(
        mutation_rate_multiplier=mutation_rate_multiplier,
        effective_population_size=int(effective_population_size),
        generations=int(generations),
        beneficial_mutation_rate=beneficial_mutation_rate,
        neutral_mutation_rate=neutral_mutation_rate,
        deleterious_mutation_rate=deleterious_mutation_rate,
        beneficial_effect_size=beneficial_effect_size,
        decay_effect_size=decay_effect_size,
        benefit_saturation=benefit_saturation,
        interference_strength=interference_strength,
        interference_exponent=interference_exponent,
        robustness_decay_rate=robustness_decay_rate,
        decay_fitness_penalty=decay_fitness_penalty,
        robustness_fitness_weight=robustness_fitness_weight,
        selection_strength=selection_strength,
        viability_fitness_threshold=viability_fitness_threshold,
        lethal_decay_threshold=lethal_decay_threshold,
        minimum_viable_robustness=minimum_viable_robustness,
        beneficial_adoption_threshold=beneficial_adoption_threshold,
        collapse_fitness_threshold=collapse_fitness_threshold,
        random_seed=int(random_seed),
        max_lineage_classes=int(max_lineage_classes),
    )


def _render_model_audit(results) -> None:
    params = results.params
    final_record = results.history[-1]

    with st.expander("Model audit", expanded=False):
        st.subheader("Formulas")
        st.code(
            "\n".join(
                [
                    "r_b = beneficial_mutation_rate * mutation_rate_multiplier",
                    "r_h = deleterious_mutation_rate * mutation_rate_multiplier",
                    "r_n = neutral_mutation_rate * mutation_rate_multiplier",
                    "p_event = 1 - exp(-r_event)",
                    "no_new_mutation = (1 - p_b) * (1 - p_h) * (1 - p_n)",
                    "neutral = (1 - p_b) * (1 - p_h) * p_n",
                    "harmful = (1 - p_b) * p_h",
                    "beneficial = p_b * (1 - p_h)",
                    "mixed = p_b * p_h",
                    "the same class probabilities apply to every lineage each generation",
                    "has_beneficial does not reduce future harmful or mixed exposure",
                    "",
                    "interference = 1 / (1 + interference_strength * load^interference_exponent)",
                    "B_next = B_inherited + min(benefit_saturation - B_inherited, beneficial_effect_size * interference)",
                    "D_next = D_inherited + decay_effect_size for harmful or mixed offspring",
                    "R_next = exp(-robustness_decay_rate * D_next)",
                    "performance_fitness = max(0, 1 + B - decay_fitness_penalty * D)",
                    "robustness_modifier = max(0, 1 - robustness_fitness_weight * (1 - R))",
                    "fitness = performance_fitness * robustness_modifier",
                    "decay_pressure = decay_fitness_penalty * D",
                    "benefit_decay_balance = B - decay_pressure",
                    "new_mutation_lineages = neutral + harmful + beneficial + mixed offspring",
                    "total_lineages_evolved_next = total_lineages_evolved_prior + new_mutation_lineages",
                    "",
                    "viable = fitness >= viability_fitness_threshold and D <= lethal_decay_threshold and R >= minimum_viable_robustness",
                    "competitive_weight = 0 if not viable else class_count * fitness ** selection_strength",
                    "next_population_size = min(carrying_capacity, viable_population_size)",
                    "next class counts are sampled in proportion to competitive_weight",
                ]
            ),
            language="text",
        )

        st.subheader("Trajectory classification")
        st.code(
            "\n".join(
                [
                    "mostly_beneficial = benefit_decay_balance > 0",
                    "mostly_harmful_or_negative = benefit_decay_balance < 0",
                    "neutral_or_exactly_balanced = benefit_decay_balance == 0",
                    "benefit_led_population = sum(class_count for mostly_beneficial surviving classes)",
                    "decay_led_population = sum(class_count for mostly_harmful_or_negative surviving classes)",
                    "total_population = sum(class_count for all surviving classes)",
                    "classification uses surviving population counts, not fractions",
                ]
            ),
            language="text",
        )

        st.subheader("Population-cap logic")
        st.code(
            "\n".join(
                [
                    "carrying_capacity = effective_population_size",
                    "candidate_population_size = actual_population_size from previous generation",
                    "discard candidate classes below fitness, decay, or robustness viability gates",
                    "viable_population_size = sum(counts for viable candidate classes)",
                    "above viability, higher fitness changes competitive share without increasing population size",
                    "sample next class counts with Multinomial(next_population_size, competitive_weight / sum(competitive_weight))",
                    "actual_population_size_next = sum(survivors)",
                    "actual_population_size_next <= viable_population_size <= candidate_population_size",
                    "actual_population_size_next may be below carrying_capacity",
                    "no below-threshold lineage survives because empty capacity exists",
                    "collapse is possible when actual_population_size_next is zero",
                ]
            ),
            language="text",
        )

        st.subheader("Lineage-production accounting")
        st.code(
            "\n".join(
                [
                    "generation_0_total_lineages_evolved = 0",
                    "no_mutation_offspring continue an existing lineage and are not counted as new evolved lineages",
                    "new_mutation_lineages = neutral_mutation_offspring + harmful_mutation_offspring + beneficial_mutation_offspring + mixed_mutation_offspring",
                    "total_lineages_evolved = cumulative sum(new_mutation_lineages over generation transitions)",
                    "the count includes mutated offspring lineages that survive and mutated offspring lineages later lost to selection, extinction, or nonviability",
                    "starting lineages at generation 0 are not counted as produced during the run",
                ]
            ),
            language="text",
        )

        st.subheader("Current transition probabilities")
        st.write(results.transition_probabilities.as_dict())

        st.subheader("Final generation accounting")
        st.write(
            {
                "carrying_capacity": final_record.carrying_capacity,
                "candidate_population_size": final_record.candidate_population_size,
                "total_lineages_evolved": final_record.total_lineages_evolved,
                "viable_population_size": final_record.viable_population_size,
                "viable_lineage_class_count": final_record.viable_lineage_class_count,
                "actual_population_size": final_record.actual_population_size,
                "benefit_led_population": (
                    final_record.beneficial_dominant_population_size
                ),
                "decay_led_population": (
                    final_record.harmful_dominant_population_size
                ),
                "lineage_class_count": final_record.lineage_class_count,
            }
        )

        st.subheader("Beneficial-lineage mutation exposure")
        st.write(
            {
                "beneficial_parent_population_size": (
                    final_record.beneficial_parent_population_size
                ),
                "beneficial_parent_no_mutation_offspring": (
                    final_record.beneficial_parent_no_mutation_offspring
                ),
                "beneficial_parent_neutral_mutation_offspring": (
                    final_record.beneficial_parent_neutral_mutation_offspring
                ),
                "beneficial_parent_harmful_mutation_offspring": (
                    final_record.beneficial_parent_harmful_mutation_offspring
                ),
                "beneficial_parent_beneficial_mutation_offspring": (
                    final_record.beneficial_parent_beneficial_mutation_offspring
                ),
                "beneficial_parent_mixed_mutation_offspring": (
                    final_record.beneficial_parent_mixed_mutation_offspring
                ),
                "beneficial_parent_decay_exposed_offspring": (
                    final_record.beneficial_parent_harmful_mutation_offspring
                    + final_record.beneficial_parent_mixed_mutation_offspring
                ),
            }
        )
        st.caption(
            "These counts are offspring from parents that already had at least "
            "one beneficial mutation before the generation transition."
        )

        st.subheader("Advanced simulation controls")
        st.write(
            {
                "random_seed": params.random_seed,
                "max_lineage_classes": params.max_lineage_classes,
            }
        )

        st.subheader("Reporting thresholds")
        st.write(
            {
                "beneficial_adoption_threshold": (
                    params.beneficial_adoption_threshold
                ),
                "collapse_fitness_threshold": params.collapse_fitness_threshold,
            }
        )

        st.subheader("Input provenance")
        st.dataframe(_audit_rows(params), use_container_width=True)

        st.subheader("Data sources")
        st.write(
            {
                "lineage_model_calibrated_from_data": False,
                "empirical_inputs_used": [],
                "fitted_inputs_used": [],
                "current_values_source": "user-selected or exploratory defaults",
                "note": (
                    "The current lineage run does not consume the repository's "
                    "experimental data scaffold."
                ),
            }
        )


def _audit_rows(params: LineageParameters) -> list[dict[str, object]]:
    biological_inputs = {
        "mutation_rate_multiplier": "experimental setup",
        "effective_population_size": "experimental setup",
        "generations": "experimental setup",
        "beneficial_mutation_rate": "mutation supply",
        "neutral_mutation_rate": "mutation supply",
        "deleterious_mutation_rate": "mutation supply",
        "beneficial_effect_size": "mutation effect",
        "decay_effect_size": "mutation effect",
        "benefit_saturation": "mutation effect",
        "interference_strength": "interaction",
        "interference_exponent": "interaction",
        "robustness_decay_rate": "robustness",
        "decay_fitness_penalty": "fitness",
        "robustness_fitness_weight": "fitness",
        "selection_strength": "survival",
        "viability_fitness_threshold": "survival",
        "lethal_decay_threshold": "survival",
        "minimum_viable_robustness": "survival",
    }
    reporting_inputs = {
        "beneficial_adoption_threshold": "reporting threshold",
        "collapse_fitness_threshold": "reporting threshold",
    }
    simulation_inputs = {
        "random_seed": "reproducibility",
        "max_lineage_classes": "computational safety",
    }

    rows: list[dict[str, object]] = []
    for name, group in biological_inputs.items():
        rows.append(
            {
                "parameter": name,
                "value": getattr(params, name),
                "group": group,
                "provenance": "assumed",
                "role": "biological assumption or experimental setup",
            }
        )
    for name, group in reporting_inputs.items():
        rows.append(
            {
                "parameter": name,
                "value": getattr(params, name),
                "group": group,
                "provenance": "assumed",
                "role": "interpretation only",
            }
        )
    for name, group in simulation_inputs.items():
        rows.append(
            {
                "parameter": name,
                "value": getattr(params, name),
                "group": group,
                "provenance": "simulation-only",
                "role": "advanced simulation control",
            }
        )
    return rows


if __name__ == "__main__":
    main()
