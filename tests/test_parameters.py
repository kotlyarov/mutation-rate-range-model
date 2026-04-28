import pytest

from mrrm import ModelParameters
from mrrm.validation import ParameterValidationError


def test_default_parameters_are_valid():
    params = ModelParameters()

    assert params.m_min == 0.1
    assert params.m_max == 100.0
    assert params.n_points == 400
    assert params.survival_selection_enabled is True
    assert params.survival_stochasticity == pytest.approx(0.23)


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


def test_invalid_survival_selection_parameters_raise_clear_errors():
    with pytest.raises(
        ParameterValidationError,
        match="population_growth_factor must be positive",
    ):
        ModelParameters(population_growth_factor=0.0)

    with pytest.raises(
        ParameterValidationError,
        match="selection_strength must be non-negative",
    ):
        ModelParameters(selection_strength=-0.1)

    with pytest.raises(
        ParameterValidationError,
        match="survival_stochasticity must be between 0 and 1",
    ):
        ModelParameters(survival_stochasticity=1.1)


def test_survival_selection_enabled_must_be_boolean():
    with pytest.raises(
        ParameterValidationError,
        match="survival_selection_enabled must be true or false",
    ):
        ModelParameters(survival_selection_enabled=1)


def test_effective_selection_strength_limit_only_applies_when_enabled():
    disabled = ModelParameters(
        survival_selection_enabled=False,
        population_growth_factor=1e-6,
        selection_strength=1.0,
    )

    assert disabled.population_growth_factor == 1e-6

    with pytest.raises(ParameterValidationError, match="effective selection strength"):
        ModelParameters(
            survival_selection_enabled=True,
            population_growth_factor=1e-6,
            selection_strength=1.0,
        )
