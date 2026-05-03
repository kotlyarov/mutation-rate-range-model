import numpy as np
import pytest

from mrrm import (
    ComputationLimitError,
    LineageParameters,
    mutation_category_probabilities,
    simulate_lineage_survival,
)
from mrrm.plotting import make_lineage_population_figure
from mrrm.validation import ParameterValidationError


def test_lineage_history_has_generation_axis_and_finite_metrics():
    params = LineageParameters(
        seed_population=300,
        population_cap=1_000,
        generations=8,
        mutation_rate=0.05,
        beneficial_mutation_rate=0.2,
        harmful_mutation_rate=0.1,
        lethal_mutation_rate=0.02,
        randomness=0.0,
        random_seed=17,
    )
    results = simulate_lineage_survival(params)
    history = results.history_arrays()

    assert history["generation"].shape == (params.generations + 1,)
    assert history["generation"][0] == 0
    assert history["generation"][-1] == params.generations
    assert history["lineage_counter_cumulative"][0] == 1
    assert np.all(np.diff(history["lineage_counter_cumulative"]) >= 0)
    for values in history.values():
        assert values.shape == (params.generations + 1,)
        assert np.all(np.isfinite(values.astype(float)))
    assert np.all(history["total_population"] >= 0)
    assert np.all(history["lineage_count_current"] <= history["lineage_counter_cumulative"])
    assert np.all(history["neutral_mutation_count_total"] >= 0)


def test_category_probabilities_are_valid_and_compound_normalized():
    params = LineageParameters(
        beneficial_mutation_rate=0.1,
        harmful_mutation_rate=0.2,
        lethal_mutation_rate=0.05,
        compound_effect=0.5,
    )
    seed_probabilities = mutation_category_probabilities(params, total_mutations=0)
    loaded_probabilities = mutation_category_probabilities(params, total_mutations=10)

    assert seed_probabilities.as_array().shape == (4,)
    assert np.all(seed_probabilities.as_array() >= 0)
    assert np.isclose(np.sum(seed_probabilities.as_array()), 1.0)
    assert np.isclose(np.sum(loaded_probabilities.as_array()), 1.0)
    assert loaded_probabilities.neutral < seed_probabilities.neutral
    assert loaded_probabilities.harmful > seed_probabilities.harmful


def test_no_mutation_rate_keeps_seed_lineage_and_grows_population():
    params = LineageParameters(
        seed_population=20,
        population_cap=1_000,
        generations=3,
        mutation_rate=0.0,
        randomness=0.0,
        random_seed=14,
    )
    results = simulate_lineage_survival(params)

    assert [record.total_population for record in results.history] == [20, 40, 80, 160]
    assert all(record.mutation_lineages_created == 0 for record in results.history)
    assert all(record.lineage_counter_cumulative == 1 for record in results.history)
    assert len(results.final_lineages) == 1
    assert results.final_lineages[0].lineage_id == 1


def test_poisson_mutation_event_can_create_multi_mutation_lineages():
    params = LineageParameters(
        seed_population=250,
        population_cap=10_000,
        generations=1,
        mutation_rate=1.5,
        beneficial_mutation_rate=0.0,
        harmful_mutation_rate=0.0,
        lethal_mutation_rate=0.0,
        randomness=0.0,
        random_seed=3,
    )
    results = simulate_lineage_survival(params)
    record = results.history[-1]

    assert record.mutation_lineages_created > 0
    assert record.one_mutation_lineages_created > 0
    assert record.multi_mutation_lineages_created > 0
    assert record.lineage_counter_cumulative == 1 + record.mutation_lineages_created
    assert any(lineage.total_mutations > 1 for lineage in results.final_lineages)


def test_lethal_mutation_lineages_are_removed_at_selection():
    params = LineageParameters(
        seed_population=200,
        population_cap=1_000,
        generations=1,
        mutation_rate=1.0,
        beneficial_mutation_rate=0.0,
        harmful_mutation_rate=0.0,
        lethal_mutation_rate=1.0,
        randomness=0.0,
        random_seed=8,
    )
    results = simulate_lineage_survival(params)
    record = results.history[-1]

    assert record.lethal_lineages_removed > 0
    assert all(lineage.lethal_mutations == 0 for lineage in results.final_lineages)
    assert record.lethal_mutation_count_total == 0


def test_low_fitness_lineages_are_removed():
    params = LineageParameters(
        seed_fitness=0.6,
        seed_population=200,
        population_cap=1_000,
        generations=1,
        mutation_rate=1.0,
        beneficial_mutation_rate=0.0,
        harmful_mutation_rate=1.0,
        lethal_mutation_rate=0.0,
        mutation_effect=0.4,
        minimum_fitness=0.4,
        randomness=0.0,
        random_seed=9,
    )
    results = simulate_lineage_survival(params)
    record = results.history[-1]

    assert record.low_fitness_lineages_removed > 0
    assert all(lineage.fitness_score >= params.minimum_fitness for lineage in results.final_lineages)


def test_seeded_stochastic_runs_are_reproducible():
    params = LineageParameters(
        seed_population=300,
        population_cap=700,
        generations=5,
        mutation_rate=0.1,
        beneficial_mutation_rate=0.2,
        harmful_mutation_rate=0.1,
        lethal_mutation_rate=0.01,
        random_seed=123,
    )
    first = simulate_lineage_survival(params)
    second = simulate_lineage_survival(params)

    assert np.array_equal(
        first.history_arrays()["mean_fitness"],
        second.history_arrays()["mean_fitness"],
    )
    assert first.final_lineages == second.final_lineages
    assert first.outcome == second.outcome


def test_population_cap_uses_rounded_fitness_weighted_selection():
    params = LineageParameters(
        seed_population=100,
        population_cap=80,
        generations=3,
        mutation_rate=0.3,
        beneficial_mutation_rate=0.8,
        harmful_mutation_rate=0.0,
        lethal_mutation_rate=0.0,
        mutation_effect=0.1,
        randomness=0.0,
        random_seed=4,
    )
    results = simulate_lineage_survival(params)

    assert any(record.pre_cap_population > params.population_cap for record in results.history)
    assert all(record.total_population >= 0 for record in results.history)
    assert results.history[-1].beneficial_lineage_population > 0


def test_population_trajectory_figure_uses_population_counts_and_solid_lines():
    params = LineageParameters(
        seed_population=200,
        population_cap=500,
        generations=3,
        mutation_rate=0.1,
        beneficial_mutation_rate=0.2,
        harmful_mutation_rate=0.1,
        lethal_mutation_rate=0.0,
        randomness=0.0,
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
        record.total_population for record in results.history
    ]
    assert list(figure.data[1].y) == [
        record.beneficial_lineage_population for record in results.history
    ]
    assert list(figure.data[2].y) == [
        record.harmful_lineage_population for record in results.history
    ]
    assert figure.layout.yaxis.title.text == "Population size"
    assert figure.layout.yaxis2.title.text == "Mean fitness"


def test_lineage_limit_returns_clear_error():
    params = LineageParameters(
        seed_population=50,
        population_cap=100,
        generations=1,
        mutation_rate=5.0,
        max_lineage_classes=5,
        random_seed=1,
    )

    with pytest.raises(ComputationLimitError, match="max_lineage_classes"):
        simulate_lineage_survival(params)


def test_invalid_lineage_parameters_raise_clear_errors():
    with pytest.raises(ParameterValidationError, match="seed_fitness"):
        LineageParameters(seed_fitness=1.5)

    with pytest.raises(ParameterValidationError, match="seed_population"):
        LineageParameters(seed_population=0)

    with pytest.raises(ParameterValidationError, match="population_cap"):
        LineageParameters(population_cap=0)

    with pytest.raises(ParameterValidationError, match="generations"):
        LineageParameters(generations=-1)

    with pytest.raises(ParameterValidationError, match="beneficial_mutation_rate"):
        LineageParameters(beneficial_mutation_rate=1.1)

    with pytest.raises(ParameterValidationError, match="minimum_fitness"):
        LineageParameters(minimum_fitness=1.1)

    with pytest.raises(ParameterValidationError, match="max_runtime_seconds"):
        LineageParameters(max_runtime_seconds=0.0)
