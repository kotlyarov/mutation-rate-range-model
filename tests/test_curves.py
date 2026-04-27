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
    results = evaluate_model(ModelParameters(n_points=80))

    assert np.all(results.benefit >= 0)
    assert np.all(results.decay >= 0)
    assert np.all(results.robustness >= 0)
    assert np.all(results.robustness <= 1)


def test_net_score_changes_when_penalty_weights_change():
    low_penalty = evaluate_model(ModelParameters(n_points=80, lambda_decay=0.0))
    high_penalty = evaluate_model(ModelParameters(n_points=80, lambda_decay=0.8))

    assert not np.allclose(low_penalty.score, high_penalty.score)


def test_estimate_range_returns_evaluated_peak():
    params = ModelParameters(n_points=100)
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
