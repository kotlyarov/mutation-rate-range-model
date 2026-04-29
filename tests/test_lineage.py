import numpy as np
import pytest

from mrrm import (
    LineageParameters,
    mutation_transition_probabilities,
    simulate_lineage_survival,
)
from mrrm.plotting import make_lineage_population_figure
from mrrm.validation import ParameterValidationError


def test_lineage_history_has_generation_axis_and_finite_metrics():
    params = LineageParameters(
        generations=12,
        effective_population_size=5_000,
        mutation_rate_multiplier=8.0,
        beneficial_mutation_rate=1.0 / 1_000.0,
        neutral_mutation_rate=1.0 / 1_000.0,
        deleterious_mutation_rate=1.0 / 1_000.0,
        random_seed=17,
    )
    results = simulate_lineage_survival(params)
    history = results.history_arrays()

    assert history["generation"].shape == (params.generations + 1,)
    assert history["generation"][0] == 0
    assert history["generation"][-1] == params.generations
    assert history["total_lineages_evolved"][0] == 0
    new_mutation_lineages = (
        history["neutral_mutation_offspring"]
        + history["harmful_mutation_offspring"]
        + history["beneficial_mutation_offspring"]
        + history["mixed_mutation_offspring"]
    )
    assert np.array_equal(
        np.diff(history["total_lineages_evolved"]),
        new_mutation_lineages[1:],
    )
    for values in history.values():
        assert values.shape == (params.generations + 1,)
        assert np.all(np.isfinite(values.astype(float)))
    assert np.all(history["carrying_capacity"] == params.effective_population_size)
    assert np.all(history["actual_population_size"] <= params.effective_population_size)
    assert np.all(history["actual_population_size"] <= history["viable_population_size"])
    assert np.all(history["viable_population_size"] <= history["candidate_population_size"])
    assert np.all(history["beneficial_dominant_population_size"] >= 0)
    assert np.all(history["harmful_dominant_population_size"] >= 0)
    assert np.all(
        history["beneficial_dominant_population_size"]
        + history["harmful_dominant_population_size"]
        <= history["actual_population_size"]
    )


def test_transition_probabilities_are_valid_and_sum_to_one():
    params = LineageParameters(mutation_rate_multiplier=25.0)
    probabilities = mutation_transition_probabilities(params).as_array()

    assert probabilities.shape == (5,)
    assert np.all(probabilities >= 0)
    assert np.all(probabilities <= 1)
    assert np.isclose(np.sum(probabilities), 1.0)


def test_no_mutation_offspring_do_not_count_as_new_lineages():
    params = LineageParameters(
        generations=5,
        effective_population_size=100,
        mutation_rate_multiplier=1.0,
        beneficial_mutation_rate=0.0,
        neutral_mutation_rate=0.0,
        deleterious_mutation_rate=0.0,
        random_seed=14,
    )
    results = simulate_lineage_survival(params)

    assert all(
        record.no_mutation_offspring == params.effective_population_size
        for record in results.history[1:]
    )
    assert all(record.total_lineages_evolved == 0 for record in results.history)
    assert results.outcome.final_total_lineages_evolved == 0


def test_accumulated_state_carries_forward_across_generations():
    params = LineageParameters(
        generations=4,
        effective_population_size=2_000,
        mutation_rate_multiplier=1.0,
        beneficial_mutation_rate=2.0,
        deleterious_mutation_rate=0.0,
        neutral_mutation_rate=0.0,
        beneficial_effect_size=0.1,
        selection_strength=0.0,
        random_seed=4,
    )
    results = simulate_lineage_survival(params)
    mean_benefit = np.asarray(
        [record.mean_benefit for record in results.history],
        dtype=float,
    )

    assert mean_benefit[0] == 0.0
    assert mean_benefit[-1] > mean_benefit[1] > 0.0
    assert results.history[-1].beneficial_adoption_fraction == 1.0


def test_tiny_population_does_not_create_fractional_impossible_lineages():
    params = LineageParameters(
        generations=10,
        effective_population_size=1,
        mutation_rate_multiplier=1.0,
        beneficial_mutation_rate=1e-9,
        deleterious_mutation_rate=0.0,
        neutral_mutation_rate=0.0,
        random_seed=1,
    )
    results = simulate_lineage_survival(params)

    assert all(record.beneficial_mutation_offspring == 0 for record in results.history)
    assert results.outcome.beneficial_survived is False
    assert results.outcome.final_beneficial_adoption_fraction == 0.0


def test_seeded_stochastic_runs_are_reproducible():
    params = LineageParameters(
        generations=8,
        effective_population_size=2_500,
        mutation_rate_multiplier=12.0,
        beneficial_mutation_rate=1.0 / 500.0,
        neutral_mutation_rate=1.0 / 500.0,
        deleterious_mutation_rate=1.0 / 500.0,
        random_seed=123,
    )
    first = simulate_lineage_survival(params)
    second = simulate_lineage_survival(params)

    assert np.array_equal(
        first.history_arrays()["mean_fitness"],
        second.history_arrays()["mean_fitness"],
    )
    assert first.outcome == second.outcome


def test_generation_records_split_offspring_into_mutation_classes():
    params = LineageParameters(
        generations=1,
        effective_population_size=10_000,
        mutation_rate_multiplier=1.0,
        beneficial_mutation_rate=1.0,
        deleterious_mutation_rate=1.0,
        neutral_mutation_rate=1.0,
        random_seed=3,
    )
    results = simulate_lineage_survival(params)
    record = results.history[-1]

    assert record.no_mutation_offspring > 0
    assert record.neutral_mutation_offspring > 0
    assert record.harmful_mutation_offspring > 0
    assert record.beneficial_mutation_offspring > 0
    assert record.mixed_mutation_offspring > 0
    assert record.mixed_fraction > 0


def test_population_capacity_is_not_refilled_after_viability_filtering():
    params = LineageParameters(
        generations=1,
        effective_population_size=10_000,
        mutation_rate_multiplier=1.0,
        beneficial_mutation_rate=1e9,
        neutral_mutation_rate=0.0,
        deleterious_mutation_rate=0.02,
        beneficial_effect_size=1.0,
        benefit_saturation=10.0,
        decay_effect_size=10.0,
        decay_fitness_penalty=0.0,
        robustness_fitness_weight=0.0,
        lethal_decay_threshold=5.0,
        selection_strength=3.0,
        random_seed=8,
    )
    results = simulate_lineage_survival(params)
    record = results.history[-1]

    assert record.carrying_capacity == params.effective_population_size
    assert record.candidate_population_size == params.effective_population_size
    assert 0 < record.viable_population_size < params.effective_population_size
    assert record.beneficial_mutation_offspring == record.viable_population_size
    assert record.mixed_mutation_offspring > 0
    assert record.actual_population_size == record.viable_population_size


def test_trajectory_classification_counts_benefit_and_decay_led_populations():
    beneficial_results = simulate_lineage_survival(
        LineageParameters(
            generations=1,
            effective_population_size=1_000,
            mutation_rate_multiplier=1.0,
            beneficial_mutation_rate=1e9,
            neutral_mutation_rate=0.0,
            deleterious_mutation_rate=0.0,
            beneficial_effect_size=0.2,
            random_seed=15,
        )
    )
    beneficial_record = beneficial_results.history[-1]

    assert beneficial_record.beneficial_dominant_population_size == 1_000
    assert beneficial_record.harmful_dominant_population_size == 0

    harmful_results = simulate_lineage_survival(
        LineageParameters(
            generations=1,
            effective_population_size=1_000,
            mutation_rate_multiplier=1.0,
            beneficial_mutation_rate=0.0,
            neutral_mutation_rate=0.0,
            deleterious_mutation_rate=1e9,
            decay_effect_size=1.0,
            decay_fitness_penalty=0.2,
            lethal_decay_threshold=100.0,
            robustness_fitness_weight=0.0,
            random_seed=16,
        )
    )
    harmful_record = harmful_results.history[-1]

    assert harmful_record.beneficial_dominant_population_size == 0
    assert harmful_record.harmful_dominant_population_size == 1_000


def test_population_trajectory_figure_uses_population_counts_and_solid_lines():
    params = LineageParameters(
        generations=3,
        effective_population_size=1_000,
        mutation_rate_multiplier=1.0,
        beneficial_mutation_rate=0.1,
        neutral_mutation_rate=0.0,
        deleterious_mutation_rate=0.1,
        random_seed=18,
    )
    results = simulate_lineage_survival(params)
    figure = make_lineage_population_figure(results)

    assert [trace.name for trace in figure.data] == [
        "Total population",
        "Benefit-led population",
        "Decay-led population",
        "Mean fitness",
    ]
    assert [trace.yaxis for trace in figure.data] == [None, None, None, "y2"]
    assert all(trace.mode == "lines" for trace in figure.data)
    assert all(trace.line.dash in (None, "solid") for trace in figure.data)
    assert list(figure.data[0].y) == [
        record.actual_population_size for record in results.history
    ]
    assert list(figure.data[1].y) == [
        record.beneficial_dominant_population_size for record in results.history
    ]
    assert list(figure.data[2].y) == [
        record.harmful_dominant_population_size for record in results.history
    ]
    assert figure.layout.yaxis.title.text == "Population size"
    assert figure.layout.yaxis2.title.text == "Mean fitness"


def test_population_can_collapse_when_all_candidates_are_nonviable():
    params = LineageParameters(
        generations=3,
        effective_population_size=500,
        mutation_rate_multiplier=1.0,
        beneficial_mutation_rate=0.0,
        neutral_mutation_rate=0.0,
        deleterious_mutation_rate=1e9,
        decay_effect_size=10.0,
        decay_fitness_penalty=1.0,
        robustness_fitness_weight=0.0,
        random_seed=2,
    )
    results = simulate_lineage_survival(params)
    first_generation = results.history[1]
    final_generation = results.history[-1]

    assert first_generation.viable_population_size == 0
    assert first_generation.actual_population_size == 0
    assert first_generation.total_lineages_evolved == params.effective_population_size
    assert final_generation.actual_population_size == 0
    assert final_generation.total_lineages_evolved == params.effective_population_size
    assert results.final_lineages == ()
    assert results.outcome.collapsed is True
    assert (
        results.outcome.final_total_lineages_evolved
        == params.effective_population_size
    )


def test_lethal_decay_threshold_overrides_high_benefit():
    params = LineageParameters(
        generations=2,
        effective_population_size=500,
        mutation_rate_multiplier=1.0,
        beneficial_mutation_rate=1e9,
        neutral_mutation_rate=0.0,
        deleterious_mutation_rate=1e9,
        beneficial_effect_size=100.0,
        benefit_saturation=1_000.0,
        decay_effect_size=10.0,
        decay_fitness_penalty=0.0,
        robustness_fitness_weight=0.0,
        lethal_decay_threshold=5.0,
        random_seed=11,
    )
    results = simulate_lineage_survival(params)
    first_generation = results.history[1]

    assert first_generation.mixed_mutation_offspring == params.effective_population_size
    assert first_generation.viable_population_size == 0
    assert first_generation.actual_population_size == 0
    assert results.outcome.collapsed is True


def test_minimum_robustness_threshold_overrides_high_benefit():
    params = LineageParameters(
        generations=2,
        effective_population_size=500,
        mutation_rate_multiplier=1.0,
        beneficial_mutation_rate=1e9,
        neutral_mutation_rate=0.0,
        deleterious_mutation_rate=1e9,
        beneficial_effect_size=100.0,
        benefit_saturation=1_000.0,
        decay_effect_size=2.0,
        decay_fitness_penalty=0.0,
        robustness_decay_rate=1.0,
        robustness_fitness_weight=0.0,
        lethal_decay_threshold=100.0,
        minimum_viable_robustness=0.5,
        random_seed=12,
    )
    results = simulate_lineage_survival(params)
    first_generation = results.history[1]

    assert first_generation.mixed_mutation_offspring == params.effective_population_size
    assert first_generation.viable_population_size == 0
    assert first_generation.actual_population_size == 0
    assert results.outcome.collapsed is True


def test_already_beneficial_lineages_continue_facing_mutation_exposure():
    params = LineageParameters(
        generations=2,
        effective_population_size=20_000,
        mutation_rate_multiplier=1.0,
        beneficial_mutation_rate=2.0,
        neutral_mutation_rate=0.0,
        deleterious_mutation_rate=0.5,
        beneficial_effect_size=0.5,
        decay_effect_size=0.1,
        decay_fitness_penalty=0.0,
        robustness_fitness_weight=0.0,
        benefit_saturation=10.0,
        lethal_decay_threshold=100.0,
        random_seed=23,
    )
    results = simulate_lineage_survival(params)
    second_generation = results.history[2]

    assert results.history[1].beneficial_adoption_fraction > 0
    assert second_generation.beneficial_parent_population_size > 0
    assert (
        second_generation.beneficial_parent_harmful_mutation_offspring
        + second_generation.beneficial_parent_mixed_mutation_offspring
    ) > 0
    assert (
        second_generation.beneficial_parent_no_mutation_offspring
        + second_generation.beneficial_parent_neutral_mutation_offspring
    ) > 0


def test_beneficial_effect_size_changes_competitive_success():
    base_params = {
        "generations": 10,
        "effective_population_size": 10_000,
        "mutation_rate_multiplier": 1.0,
        "beneficial_mutation_rate": 0.02,
        "neutral_mutation_rate": 0.0,
        "deleterious_mutation_rate": 0.005,
        "decay_effect_size": 0.2,
        "decay_fitness_penalty": 0.2,
        "robustness_fitness_weight": 0.0,
        "benefit_saturation": 10.0,
        "selection_strength": 2.0,
        "random_seed": 42,
    }
    low_effect = simulate_lineage_survival(
        LineageParameters(**base_params, beneficial_effect_size=1e-6)
    )
    high_effect = simulate_lineage_survival(
        LineageParameters(**base_params, beneficial_effect_size=1.0)
    )

    assert (
        high_effect.outcome.final_beneficial_adoption_fraction
        > low_effect.outcome.final_beneficial_adoption_fraction + 0.5
    )
    assert (
        high_effect.outcome.final_mean_fitness
        > low_effect.outcome.final_mean_fitness + 1.0
    )
    assert (
        high_effect.outcome.final_actual_population_size
        <= high_effect.outcome.final_viable_population_size
    )
    assert (
        low_effect.outcome.final_actual_population_size
        <= low_effect.outcome.final_viable_population_size
    )


def test_invalid_lineage_parameters_raise_clear_errors():
    with pytest.raises(ParameterValidationError, match="mutation_rate_multiplier"):
        LineageParameters(mutation_rate_multiplier=0.0)

    with pytest.raises(ParameterValidationError, match="effective_population_size"):
        LineageParameters(effective_population_size=0)

    with pytest.raises(ParameterValidationError, match="generations"):
        LineageParameters(generations=0)

    with pytest.raises(ParameterValidationError, match="viability_fitness_threshold"):
        LineageParameters(viability_fitness_threshold=-0.1)

    with pytest.raises(ParameterValidationError, match="lethal_decay_threshold"):
        LineageParameters(lethal_decay_threshold=-1.0)

    with pytest.raises(ParameterValidationError, match="minimum_viable_robustness"):
        LineageParameters(minimum_viable_robustness=1.1)
