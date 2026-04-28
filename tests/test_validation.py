import numpy as np
import pytest

from mrrm import ModelParameters, evaluate_model
from mrrm.validation import CurveValidationError, ParameterValidationError, validate_curve_outputs


def test_validate_curve_outputs_accepts_valid_model_results():
    results = evaluate_model(ModelParameters(T=100, T_ref=100, n_points=40))

    validate_curve_outputs(
        results.m_values,
        results.benefit,
        results.decay,
        results.robustness,
        results.score,
    )


def test_validate_curve_outputs_rejects_nan_values():
    results = evaluate_model(ModelParameters(T=100, T_ref=100, n_points=40))
    benefit = results.benefit.copy()
    benefit[0] = np.nan

    with pytest.raises(CurveValidationError, match="finite"):
        validate_curve_outputs(
            results.m_values,
            benefit,
            results.decay,
            results.robustness,
            results.score,
        )


def test_validate_curve_outputs_rejects_unbounded_robustness():
    results = evaluate_model(ModelParameters(T=100, T_ref=100, n_points=40))
    retained = results.robustness.copy()
    retained[0] = 1.2

    with pytest.raises(CurveValidationError, match="bounded between 0 and 1"):
        validate_curve_outputs(
            results.m_values,
            results.benefit,
            results.decay,
            retained,
            results.score,
        )


def test_numerical_stability_validation_rejects_extreme_power():
    with pytest.raises(ParameterValidationError, match="numerical stability"):
        ModelParameters(m_max=1e200, gamma_decay=4.0)
