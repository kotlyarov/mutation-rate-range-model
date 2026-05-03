"""Minimal local Streamlit explorer for explicit lineage survival."""

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
        "Exploratory lineage mutation-selection model only. Outputs are "
        "conditional on the selected assumptions and are not validated "
        "biological estimates."
    )

    params = _sidebar_parameters()
    if not st.sidebar.button("Run simulation", type="primary"):
        st.info(
            "Set model inputs in the sidebar, then run the simulation. The "
            "full default explicit-lineage run is intentionally heavy and may "
            "hit the runtime or lineage-count safety guard."
        )
        return

    try:
        results = simulate_lineage_survival(params)
    except (ParameterValidationError, ValueError) as exc:
        st.error(f"Model run stopped: {exc}")
        return

    st.subheader("Single mutation-rate lineage run")
    st.caption(
        "One run follows explicit lineages through repeated Mutation and "
        "Selection events."
    )

    outcome = results.outcome
    cols = st.columns(5)
    cols[0].metric(
        "final population",
        format_count_compact(outcome.final_population),
        f"cap {format_count_compact(outcome.population_cap)}",
    )
    cols[1].metric("final mean fitness", f"{outcome.final_mean_fitness:.3g}")
    cols[2].metric("best lineage fitness", f"{outcome.final_best_fitness:.3g}")
    cols[3].metric(
        "current lineages",
        format_count_compact(outcome.final_current_lineage_count),
    )
    cols[4].metric(
        "cumulative lineages",
        format_count_compact(outcome.final_cumulative_lineage_counter),
    )

    st.caption(
        "Population counts use the left axis. Mean fitness uses the right axis."
    )
    st.plotly_chart(make_lineage_population_figure(results), use_container_width=True)

    st.subheader("Run interpretation")
    st.write(
        {
            "mutation_rate": params.mutation_rate,
            "seed_population": params.seed_population,
            "population_cap": params.population_cap,
            "final_population": outcome.final_population,
            "final_current_lineage_count": outcome.final_current_lineage_count,
            "final_cumulative_lineage_counter": (
                outcome.final_cumulative_lineage_counter
            ),
            "final_benefit_led_population": (
                results.history[-1].beneficial_lineage_population
            ),
            "final_harmful_led_population": (
                results.history[-1].harmful_lineage_population
            ),
            "beneficial_survived": outcome.beneficial_survived,
            "beneficial_reached_adoption_threshold": outcome.beneficial_adopted,
            "collapsed": outcome.collapsed,
            "seed_category_probabilities": (
                results.mutation_category_probabilities.as_dict()
            ),
        }
    )
    st.caption(
        "Harmful and lethal mutation counts are simplified burden proxies, not "
        "a full genome-integrity model."
    )

    with st.expander("Generation history", expanded=False):
        st.dataframe(
            [record.__dict__ for record in results.history],
            use_container_width=True,
        )

    with st.expander("Final surviving lineages", expanded=False):
        st.dataframe(
            [lineage.__dict__ for lineage in results.final_lineages],
            use_container_width=True,
        )

    _render_model_audit(results)


def _sidebar_parameters(defaults: LineageParameters | None = None) -> LineageParameters:
    defaults = defaults or LineageParameters()
    st.sidebar.header("Model inputs")

    with st.sidebar.expander("Experimental setup", expanded=True):
        seed_fitness = st.slider(
            "seed_fitness",
            min_value=0.0,
            max_value=1.0,
            value=float(defaults.seed_fitness),
            step=0.01,
        )
        seed_population = st.number_input(
            "seed_population",
            min_value=1,
            value=int(defaults.seed_population),
            step=10_000,
        )
        population_cap = st.number_input(
            "population_cap",
            min_value=1,
            value=int(defaults.population_cap),
            step=10_000,
        )
        generations = st.number_input(
            "generations",
            min_value=0,
            value=int(defaults.generations),
            step=100,
        )

    with st.sidebar.expander("Mutation supply", expanded=True):
        mutation_rate = st.number_input(
            "mutation_rate",
            min_value=0.0,
            value=float(defaults.mutation_rate),
            format="%.6g",
        )
        beneficial_mutation_rate = st.number_input(
            "beneficial_mutation_rate",
            min_value=0.0,
            max_value=1.0,
            value=float(defaults.beneficial_mutation_rate),
            format="%.6g",
        )
        harmful_mutation_rate = st.number_input(
            "harmful_mutation_rate",
            min_value=0.0,
            max_value=1.0,
            value=float(defaults.harmful_mutation_rate),
            format="%.6g",
        )
        lethal_mutation_rate = st.number_input(
            "lethal_mutation_rate",
            min_value=0.0,
            max_value=1.0,
            value=float(defaults.lethal_mutation_rate),
            format="%.6g",
        )
        compound_effect = st.number_input(
            "compound_effect",
            min_value=0.0,
            value=float(defaults.compound_effect),
            format="%.6g",
        )

    with st.sidebar.expander("Selection process", expanded=True):
        mutation_effect = st.number_input(
            "mutation_effect",
            min_value=0.0,
            value=float(defaults.mutation_effect),
            format="%.6g",
        )
        minimum_fitness = st.slider(
            "minimum_fitness",
            min_value=0.0,
            max_value=1.0,
            value=float(defaults.minimum_fitness),
            step=0.01,
        )
        randomness = st.number_input(
            "randomness",
            min_value=0.0,
            value=float(defaults.randomness),
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
        max_runtime_seconds = st.number_input(
            "max_runtime_seconds",
            min_value=0.1,
            value=float(defaults.max_runtime_seconds),
            step=1.0,
            format="%.3g",
        )
        max_lineage_classes = st.number_input(
            "max_lineage_classes",
            min_value=1,
            value=int(defaults.max_lineage_classes),
            step=10_000,
        )

    return LineageParameters(
        seed_fitness=seed_fitness,
        seed_population=int(seed_population),
        population_cap=int(population_cap),
        generations=int(generations),
        mutation_rate=mutation_rate,
        beneficial_mutation_rate=beneficial_mutation_rate,
        harmful_mutation_rate=harmful_mutation_rate,
        lethal_mutation_rate=lethal_mutation_rate,
        compound_effect=compound_effect,
        mutation_effect=mutation_effect,
        minimum_fitness=minimum_fitness,
        randomness=randomness,
        beneficial_adoption_threshold=beneficial_adoption_threshold,
        collapse_fitness_threshold=collapse_fitness_threshold,
        random_seed=int(random_seed),
        max_runtime_seconds=max_runtime_seconds,
        max_lineage_classes=int(max_lineage_classes),
    )


def _render_model_audit(results) -> None:
    params = results.params
    final_record = results.history[-1]

    with st.expander("Model audit", expanded=False):
        st.subheader("Final formulas")
        st.code(
            "\n".join(
                [
                    "Mutation multiplicity:",
                    "  K ~ Poisson(lambda = mutation_rate)",
                    "  K = number of new mutations in one bacterium during one Mutation event",
                    "",
                    "Compound-effect category weights for each new mutation:",
                    "  compound_multiplier = 1 + total_mutations_before * compound_effect",
                    "  beneficial_weight = beneficial_mutation_rate * compound_multiplier",
                    "  harmful_weight = harmful_mutation_rate * compound_multiplier",
                    "  lethal_weight = lethal_mutation_rate * compound_multiplier",
                    "  neutral_weight = 1",
                    "  denominator = beneficial_weight + harmful_weight + lethal_weight + neutral_weight",
                    "  p_beneficial = beneficial_weight / denominator",
                    "  p_harmful = harmful_weight / denominator",
                    "  p_lethal = lethal_weight / denominator",
                    "  p_neutral = neutral_weight / denominator",
                    "",
                    "Lineage fitness:",
                    "  fitness = seed_fitness + (beneficial_mutations - harmful_mutations) * mutation_effect",
                    "  current limitation: this formula can leave the [0, 1] range",
                    "",
                    "Selection:",
                    "  remove lineages with lethal_mutations > 0",
                    "  size = size * 2 for remaining lineages",
                    "  remove lineages with fitness < minimum_fitness",
                    "  mean_fitness = sum(size * fitness) / sum(size)",
                    "",
                    "Population cap when total population exceeds population_cap:",
                    "  adjusted_fitness = max(0, fitness + Normal(0, randomness))",
                    "  selection_weight = size * adjusted_fitness",
                    "  target_size = population_cap * selection_weight / sum(selection_weight)",
                    "  size = round(target_size) to the closest integer",
                    "  rounded total may go slightly above or below population_cap",
                ]
            ),
            language="text",
        )

        st.subheader("Lineage state")
        st.code(
            "\n".join(
                [
                    "lineage_id",
                    "generation_created",
                    "total_mutations",
                    "beneficial_mutations",
                    "harmful_mutations",
                    "lethal_mutations",
                    "size",
                    "fitness_score",
                ]
            ),
            language="text",
        )

        st.subheader("Final generation accounting")
        st.write(
            {
                "population_cap": final_record.population_cap,
                "total_population": final_record.total_population,
                "pre_cap_population": final_record.pre_cap_population,
                "lineage_count_current": final_record.lineage_count_current,
                "lineage_counter_cumulative": (
                    final_record.lineage_counter_cumulative
                ),
                "beneficial_lineage_population": (
                    final_record.beneficial_lineage_population
                ),
                "harmful_lineage_population": final_record.harmful_lineage_population,
                "neutral_or_balanced_population": (
                    final_record.neutral_or_balanced_population
                ),
                "population_over_cap": final_record.population_over_cap,
                "runtime_seconds": final_record.runtime_seconds,
            }
        )

        st.subheader("Mutation accounting")
        st.write(
            {
                "mutation_lineages_created": (
                    final_record.mutation_lineages_created
                ),
                "one_mutation_lineages_created": (
                    final_record.one_mutation_lineages_created
                ),
                "multi_mutation_lineages_created": (
                    final_record.multi_mutation_lineages_created
                ),
                "new_mutations_total": final_record.new_mutations_total,
                "beneficial_mutation_count_total": (
                    final_record.beneficial_mutation_count_total
                ),
                "harmful_mutation_count_total": (
                    final_record.harmful_mutation_count_total
                ),
                "neutral_mutation_count_total": (
                    final_record.neutral_mutation_count_total
                ),
                "lethal_lineages_removed": final_record.lethal_lineages_removed,
                "low_fitness_lineages_removed": (
                    final_record.low_fitness_lineages_removed
                ),
                "post_cap_lineages_removed": final_record.post_cap_lineages_removed,
            }
        )

        st.subheader("Seed-lineage category probabilities")
        st.write(results.mutation_category_probabilities.as_dict())

        st.subheader("Advanced simulation controls")
        st.write(
            {
                "random_seed": params.random_seed,
                "max_runtime_seconds": params.max_runtime_seconds,
                "max_lineage_classes": params.max_lineage_classes,
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
        "seed_fitness": "experimental setup",
        "seed_population": "experimental setup",
        "population_cap": "experimental setup",
        "generations": "experimental setup",
        "mutation_rate": "mutation supply",
        "beneficial_mutation_rate": "mutation supply",
        "harmful_mutation_rate": "mutation supply",
        "lethal_mutation_rate": "mutation supply",
        "compound_effect": "mutation supply",
        "mutation_effect": "selection process",
        "minimum_fitness": "selection process",
        "randomness": "selection process",
    }
    reporting_inputs = {
        "beneficial_adoption_threshold": "reporting threshold",
        "collapse_fitness_threshold": "reporting threshold",
    }
    simulation_inputs = {
        "random_seed": "reproducibility",
        "max_runtime_seconds": "computational safety",
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
