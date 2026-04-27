"""Small deterministic sensitivity helpers."""

from __future__ import annotations

from dataclasses import dataclass, replace
from typing import Iterable

import numpy as np

from .curves import evaluate_model
from .parameters import ModelParameters
from .validation import ParameterValidationError


@dataclass(frozen=True)
class SensitivityResult:
    """Summary for one parameter value in a one-at-a-time sweep."""

    parameter_name: str
    parameter_value: float
    mu_min: float | None
    mu_peak: float
    mu_max: float | None
    peak_score: float


def one_at_a_time_sensitivity(
    params: ModelParameters,
    parameter_name: str,
    values: Iterable[float],
) -> list[SensitivityResult]:
    """Evaluate range estimates while varying one parameter."""

    if not hasattr(params, parameter_name):
        raise ParameterValidationError(f"Unknown parameter: {parameter_name}.")

    sweep_values = np.asarray(list(values), dtype=float)
    if sweep_values.ndim != 1 or sweep_values.size == 0:
        raise ParameterValidationError("values must be a non-empty one-dimensional sequence.")
    if not np.all(np.isfinite(sweep_values)):
        raise ParameterValidationError("values must contain only finite numbers.")

    results: list[SensitivityResult] = []
    for value in sweep_values:
        trial_params = replace(params, **{parameter_name: float(value)})
        model = evaluate_model(trial_params)
        estimate = model.range_estimate
        results.append(
            SensitivityResult(
                parameter_name=parameter_name,
                parameter_value=float(value),
                mu_min=estimate.mu_min,
                mu_peak=estimate.mu_peak,
                mu_max=estimate.mu_max,
                peak_score=estimate.peak_score,
            )
        )
    return results
