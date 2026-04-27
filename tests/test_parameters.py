import pytest

from mrrm import ModelParameters
from mrrm.validation import ParameterValidationError


def test_default_parameters_are_valid():
    params = ModelParameters()

    assert params.m_min == 0.1
    assert params.m_max == 100.0
    assert params.n_points == 400


def test_invalid_mutation_range_raises_clear_error():
    with pytest.raises(ParameterValidationError, match="m_min must be less than m_max"):
        ModelParameters(m_min=10.0, m_max=1.0)


def test_invalid_generation_horizon_raises_clear_error():
    with pytest.raises(ParameterValidationError, match="T must be positive"):
        ModelParameters(T=0.0)


def test_invalid_penalty_weight_raises_clear_error():
    with pytest.raises(ParameterValidationError, match="lambda_decay must be non-negative"):
        ModelParameters(lambda_decay=-0.1)


def test_invalid_threshold_raises_clear_error():
    with pytest.raises(ParameterValidationError, match="net_threshold_fraction must be between 0 and 1"):
        ModelParameters(net_threshold_fraction=1.5)
