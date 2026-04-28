import numpy as np

from mrrm import (
    ModelParameters,
    adaptive_benefit,
    decay_proxy,
    estimate_range,
    evaluate_model,
    make_m_values,
    net_score,
    robustness,
    survival_selection,
)


def test_curve_outputs_have_expected_shape_and_finite_values():
    params = ModelParameters(n_points=64)
    m_values = make_m_values(params)
    benefit = adaptive_benefit(m_values, params)
    decay = decay_proxy(m_values, params)
    retained = robustness(m_values, decay, params)
    score = net_score(benefit, decay, retained, params)

    assert m_values.shape == (64,)
    for values in [benefit, decay, retained, score]:
        assert values.shape == m_values.shape
        assert np.all(np.isfinite(values))


def test_curve_invariants_for_valid_inputs():
    results = evaluate_model(ModelParameters(T=100, T_ref=100, n_points=80))

    assert np.all(results.benefit >= 0)
    assert np.all(results.decay >= 0)
    assert np.all(results.robustness >= 0)
    assert np.all(results.robustness <= 1)


def test_net_score_changes_when_penalty_weights_change():
    low_penalty = evaluate_model(
        ModelParameters(T=100, T_ref=100, n_points=80, lambda_decay=0.0)
    )
    high_penalty = evaluate_model(
        ModelParameters(T=100, T_ref=100, n_points=80, lambda_decay=0.8)
    )

    assert not np.allclose(low_penalty.score, high_penalty.score)


def test_estimate_range_returns_evaluated_peak():
    params = ModelParameters(T=100, T_ref=100, n_points=100)
    results = evaluate_model(params)
    estimate = estimate_range(
        results.m_values,
        results.benefit,
        results.decay,
        results.robustness,
        results.score,
        params,
    )

    assert estimate.mu_peak in results.m_values
    assert estimate.mu_min is None or params.m_min <= estimate.mu_min <= params.m_max
    assert estimate.mu_max is None or params.m_min <= estimate.mu_max <= params.m_max
    assert estimate.mu_min <= estimate.mu_peak <= estimate.mu_max


def test_estimate_range_uses_contiguous_chart_region_around_peak():
    params = ModelParameters(
        T=100,
        T_ref=100,
        n_points=6,
        net_threshold_fraction=0.8,
        decay_threshold_fraction=1.0,
    )
    m_values = np.asarray([0.1, 0.2, 0.3, 0.4, 0.5, 0.6])
    benefit = np.asarray([0.1, 0.2, 1.0, 0.9, 0.1, 0.95])
    decay = np.zeros_like(m_values)
    retained = np.ones_like(m_values)
    score = np.asarray([0.1, 0.2, 1.0, 0.9, 0.1, 0.95])

    estimate = estimate_range(m_values, benefit, decay, retained, score, params)

    assert estimate.mu_min == 0.3
    assert estimate.mu_peak == 0.3
    assert estimate.mu_max == 0.4


def test_disabled_survival_selection_keeps_threshold_inputs_unchanged():
    params = ModelParameters(
        n_points=80,
        survival_selection_enabled=False,
        population_growth_factor=0.5,
        selection_strength=4.0,
        survival_stochasticity=0.5,
    )
    m_values = make_m_values(params)
    benefit = adaptive_benefit(m_values, params)
    decay = decay_proxy(m_values, params)
    retained = robustness(m_values, decay, params)
    score = net_score(benefit, decay, retained, params)
    results = evaluate_model(params)
    survival = results.survival_selection

    assert survival.enabled is False
    assert np.array_equal(survival.contribution_weight, np.ones_like(score))
    assert np.array_equal(results.benefit, benefit)
    assert np.array_equal(results.decay, decay)
    assert np.array_equal(results.robustness, retained)
    assert np.array_equal(results.score, score)


def test_survival_selection_probabilities_are_finite_and_normalized():
    params = ModelParameters(
        T=100,
        T_ref=100,
        n_points=80,
        survival_selection_enabled=True,
    )
    m_values = make_m_values(params)
    benefit = adaptive_benefit(m_values, params)
    decay = decay_proxy(m_values, params)
    retained = robustness(m_values, decay, params)
    score = net_score(benefit, decay, retained, params)
    survival = survival_selection(
        m_values,
        benefit,
        decay,
        retained,
        score,
        params,
    )

    assert survival.enabled is True
    assert survival.survival_probability.shape == m_values.shape
    assert np.all(np.isfinite(survival.survival_probability))
    assert np.all(survival.survival_probability > 0)
    assert np.isclose(np.sum(survival.survival_probability), 1.0)
    assert np.all(np.isfinite(survival.contribution_weight))
    assert survival.generation_count == int(params.T)


def test_stronger_selection_reduces_high_decay_low_fitness_contribution():
    weak = evaluate_model(
        ModelParameters(
            n_points=120,
            T=100,
            T_ref=100,
            survival_selection_enabled=True,
            selection_strength=0.05,
        )
    )
    strong = evaluate_model(
        ModelParameters(
            n_points=120,
            T=100,
            T_ref=100,
            survival_selection_enabled=True,
            selection_strength=2.0,
        )
    )

    assert (
        strong.survival_selection.contribution_weight[-1]
        < weak.survival_selection.contribution_weight[-1]
    )
    assert (
        strong.decay[-1]
        < weak.decay[-1]
    )


def test_enabled_survival_selection_feeds_threshold_estimation():
    params = ModelParameters(
        n_points=120,
        T=100,
        T_ref=100,
        survival_selection_enabled=True,
        selection_strength=2.0,
        survival_stochasticity=0.0,
    )
    m_values = make_m_values(params)
    benefit = adaptive_benefit(m_values, params)
    decay = decay_proxy(m_values, params)
    retained = robustness(m_values, decay, params)
    score = net_score(benefit, decay, retained, params)
    results = evaluate_model(params)
    raw_estimate = estimate_range(
        m_values,
        benefit,
        decay,
        retained,
        score,
        params,
    )

    assert results.range_estimate.mu_max != raw_estimate.mu_max
    assert results.range_estimate.decay_threshold != raw_estimate.decay_threshold


def test_population_growth_factor_weakens_or_strengthens_selection_pressure():
    bottleneck = evaluate_model(
        ModelParameters(
            n_points=120,
            T=100,
            T_ref=100,
            survival_selection_enabled=True,
            population_growth_factor=0.5,
        )
    )
    growth = evaluate_model(
        ModelParameters(
            n_points=120,
            T=100,
            T_ref=100,
            survival_selection_enabled=True,
            population_growth_factor=2.0,
        )
    )

    assert (
        bottleneck.survival_selection.effective_selection_strength
        > growth.survival_selection.effective_selection_strength
    )
    assert (
        bottleneck.survival_selection.contribution_weight[-1]
        < growth.survival_selection.contribution_weight[-1]
    )


def test_survival_stochasticity_softens_recursive_selection():
    deterministic = evaluate_model(
        ModelParameters(
            n_points=100,
            T=100,
            T_ref=100,
            survival_selection_enabled=True,
            selection_strength=2.0,
            survival_stochasticity=0.0,
        )
    )
    softened = evaluate_model(
        ModelParameters(
            n_points=100,
            T=100,
            T_ref=100,
            survival_selection_enabled=True,
            selection_strength=2.0,
            survival_stochasticity=0.5,
        )
    )
    neutral = evaluate_model(
        ModelParameters(
            n_points=100,
            T=100,
            T_ref=100,
            survival_selection_enabled=True,
            selection_strength=2.0,
            survival_stochasticity=1.0,
        )
    )

    assert deterministic.survival_selection.contribution_weight[-1] < 1.0
    assert (
        deterministic.survival_selection.contribution_weight[-1]
        < softened.survival_selection.contribution_weight[-1]
        < neutral.survival_selection.contribution_weight[-1]
    )


def test_full_survival_stochasticity_returns_neutral_survival_weights():
    params = ModelParameters(
        n_points=80,
        T=100,
        T_ref=100,
        survival_selection_enabled=True,
        survival_stochasticity=1.0,
    )
    m_values = make_m_values(params)
    benefit = adaptive_benefit(m_values, params)
    decay = decay_proxy(m_values, params)
    retained = robustness(m_values, decay, params)
    score = net_score(benefit, decay, retained, params)
    results = evaluate_model(params)

    assert np.allclose(results.survival_selection.contribution_weight, 1.0)
    assert np.allclose(results.benefit, benefit)
    assert np.allclose(results.decay, decay)
    assert np.allclose(results.robustness, retained)
    assert np.allclose(results.score, score)
