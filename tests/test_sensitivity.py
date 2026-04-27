import pytest

from mrrm import ModelParameters
from mrrm.sensitivity import one_at_a_time_sensitivity
from mrrm.validation import ParameterValidationError


def test_one_at_a_time_sensitivity_returns_rows():
    params = ModelParameters(n_points=60)
    rows = one_at_a_time_sensitivity(params, "lambda_decay", [0.0, 0.2, 0.5])

    assert len(rows) == 3
    assert [row.parameter_value for row in rows] == [0.0, 0.2, 0.5]
    assert len({row.peak_score for row in rows}) > 1


def test_unknown_sensitivity_parameter_raises_clear_error():
    with pytest.raises(ParameterValidationError, match="Unknown parameter"):
        one_at_a_time_sensitivity(ModelParameters(), "not_a_parameter", [1.0])
