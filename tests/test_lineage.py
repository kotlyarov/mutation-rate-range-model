import numpy as np
import pytest

from mrrm import (
    LineageParameters,
    mutation_transition_probabilities,
    simulate_lineage_survival,
)
from mrrm.validation import ParameterValidationError


def test_lineage_history_has_generation_axis_and_finite_metrics():
    params = LineageParameters(
        generations=12,
        population_size=5_000,
        T_ref=1_000,
        mutation_rate_multiplier=8.0,
        random_seed=17,
    )
    results = simulate_lineage_survival(params)
    history = results.history_arrays()

    assert history["generation"].shape == (params.generations + 1,)
    assert history["generation"][0] == 0
    assert history["generation"][-1] == params.generations
    for values in history.values():
        assert values.shape == (params.generations + 1,)
        assert np.all(np.isfinite(values.astype(float)))
    assert np.all(history["population_size"] == params.population_size)


def test_transition_probabilities_are_valid_and_sum_to_one():
    params = LineageParameters(mutation_rate_multiplier=25.0)
    probabilities = mutation_transition_probabilities(params).as_array()

    assert probabilities.shape == (5,)
    assert np.all(probabilities >= 0)
    assert np.all(probabilities <= 1)
    assert np.isclose(np.sum(probabilities), 1.0)


def test_accumulated_state_carries_forward_across_generations():
    params = LineageParameters(
        generations=4,
        population_size=2_000,
        T_ref=1,
        mutation_rate_multiplier=1.0,
        alpha_benefit=2.0,
        decay_scale=0.0,
        neutral_rate_scale=0.0,
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
        population_size=1,
        T_ref=1e9,
        mutation_rate_multiplier=1.0,
        alpha_benefit=1.0,
        decay_scale=0.0,
        neutral_rate_scale=0.0,
        random_seed=1,
    )
    results = simulate_lineage_survival(params)

    assert all(record.beneficial_mutation_offspring == 0 for record in results.history)
    assert results.outcome.beneficial_survived is False
    assert results.outcome.final_beneficial_adoption_fraction == 0.0


def test_seeded_stochastic_runs_are_reproducible():
    params = LineageParameters(
        generations=8,
        population_size=2_500,
        T_ref=500,
        mutation_rate_multiplier=12.0,
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
        population_size=10_000,
        T_ref=1,
        mutation_rate_multiplier=1.0,
        alpha_benefit=1.0,
        decay_scale=1.0,
        neutral_rate_scale=1.0,
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


def test_invalid_lineage_parameters_raise_clear_errors():
    with pytest.raises(ParameterValidationError, match="mutation_rate_multiplier"):
        LineageParameters(mutation_rate_multiplier=0.0)

    with pytest.raises(ParameterValidationError, match="population_size"):
        LineageParameters(population_size=0)

    with pytest.raises(ParameterValidationError, match="generations"):
        LineageParameters(generations=0)
