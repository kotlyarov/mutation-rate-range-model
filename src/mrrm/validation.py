"""Validation helpers for model parameters and deterministic outputs."""

from __future__ import annotations

import math
import numbers
from typing import Any

import numpy as np

MAX_N_POINTS = 100_000
MAX_GENERATIONS = 1_000_000
MAX_POPULATION_SIZE = 10_000_000_000
MAX_LINEAGE_CLASSES = 1_000_000
MAX_SAFE_LOG = 700.0
ROBUSTNESS_TOLERANCE = 1e-12


class ParameterValidationError(ValueError):
    """Raised when model parameters are outside the supported domain."""


class CurveValidationError(ValueError):
    """Raised when deterministic curve outputs violate model invariants."""


def validate_parameters(params: Any) -> None:
    """Validate a ModelParameters-like object.

    The checks are intentionally conservative: invalid values raise clear
    exceptions rather than being silently clipped.
    """

    m_min = _require_positive("m_min", params.m_min)
    m_max = _require_positive("m_max", params.m_max)
    if m_min >= m_max:
        raise ParameterValidationError("m_min must be less than m_max.")

    if isinstance(params.n_points, bool) or not isinstance(params.n_points, numbers.Integral):
        raise ParameterValidationError("n_points must be an integer.")
    if params.n_points < 2:
        raise ParameterValidationError("n_points must be at least 2.")
    if params.n_points > MAX_N_POINTS:
        raise ParameterValidationError(f"n_points must be <= {MAX_N_POINTS}.")

    T = _require_positive("T", params.T)
    T_ref = _require_positive("T_ref", params.T_ref)
    T_scaled = T / T_ref
    if not math.isfinite(T_scaled) or T_scaled <= 0:
        raise ParameterValidationError("T / T_ref must be finite and positive.")

    _require_nonnegative("benefit_scale", params.benefit_scale)
    _require_nonnegative("alpha_benefit", params.alpha_benefit)
    _require_nonnegative("beta_interference", params.beta_interference)
    _require_positive("gamma_interference", params.gamma_interference)

    _require_nonnegative("decay_scale", params.decay_scale)
    _require_positive("gamma_decay", params.gamma_decay)

    _require_nonnegative("k_robustness", params.k_robustness)
    _require_nonnegative("lambda_decay", params.lambda_decay)
    _require_nonnegative("rho_robustness", params.rho_robustness)

    if not isinstance(params.survival_selection_enabled, bool):
        raise ParameterValidationError(
            "survival_selection_enabled must be true or false."
        )
    population_growth_factor = _require_positive(
        "population_growth_factor",
        params.population_growth_factor,
    )
    selection_strength = _require_nonnegative(
        "selection_strength",
        params.selection_strength,
    )
    _require_fraction("survival_stochasticity", params.survival_stochasticity)
    effective_selection_strength = selection_strength / population_growth_factor
    if (
        params.survival_selection_enabled
        and (
            not math.isfinite(effective_selection_strength)
            or effective_selection_strength > MAX_SAFE_LOG
        )
    ):
        raise ParameterValidationError(
            "effective selection strength would exceed numerical stability limits; "
            "increase population_growth_factor or reduce selection_strength."
        )

    _require_fraction("benefit_threshold_fraction", params.benefit_threshold_fraction)
    _require_fraction("net_threshold_fraction", params.net_threshold_fraction)
    _require_fraction("decay_threshold_fraction", params.decay_threshold_fraction)

    _require_safe_product(
        "beneficial supply argument",
        params.alpha_benefit,
        m_max,
        T_scaled,
    )
    _require_safe_power("interference term", m_max, params.gamma_interference)
    _require_safe_power("decay term", m_max, params.gamma_decay)
    _require_safe_product(
        "decay proxy",
        params.decay_scale,
        math.exp(params.gamma_decay * math.log(m_max)),
        T_scaled,
    )
    _require_safe_product(
        "weighted decay penalty",
        params.lambda_decay,
        params.decay_scale,
        math.exp(params.gamma_decay * math.log(m_max)),
        T_scaled,
    )


def validate_lineage_parameters(params: Any) -> None:
    """Validate a LineageParameters-like object."""

    mutation_rate_multiplier = _require_positive(
        "mutation_rate_multiplier",
        params.mutation_rate_multiplier,
    )

    if isinstance(params.effective_population_size, bool) or not isinstance(
        params.effective_population_size,
        numbers.Integral,
    ):
        raise ParameterValidationError("effective_population_size must be an integer.")
    if params.effective_population_size < 1:
        raise ParameterValidationError("effective_population_size must be at least 1.")
    if params.effective_population_size > MAX_POPULATION_SIZE:
        raise ParameterValidationError(
            f"effective_population_size must be <= {MAX_POPULATION_SIZE}."
        )

    if isinstance(params.generations, bool) or not isinstance(
        params.generations,
        numbers.Integral,
    ):
        raise ParameterValidationError("generations must be an integer.")
    if params.generations < 1:
        raise ParameterValidationError("generations must be at least 1.")
    if params.generations > MAX_GENERATIONS:
        raise ParameterValidationError(f"generations must be <= {MAX_GENERATIONS}.")

    _require_nonnegative("beneficial_mutation_rate", params.beneficial_mutation_rate)
    _require_nonnegative("neutral_mutation_rate", params.neutral_mutation_rate)
    _require_nonnegative("deleterious_mutation_rate", params.deleterious_mutation_rate)
    _require_nonnegative("beneficial_effect_size", params.beneficial_effect_size)
    _require_nonnegative("decay_effect_size", params.decay_effect_size)

    _require_nonnegative("benefit_saturation", params.benefit_saturation)
    _require_nonnegative("interference_strength", params.interference_strength)
    _require_positive("interference_exponent", params.interference_exponent)

    _require_nonnegative("robustness_decay_rate", params.robustness_decay_rate)
    _require_nonnegative("decay_fitness_penalty", params.decay_fitness_penalty)
    _require_nonnegative("robustness_fitness_weight", params.robustness_fitness_weight)
    _require_nonnegative("lethal_decay_threshold", params.lethal_decay_threshold)
    _require_fraction("minimum_viable_robustness", params.minimum_viable_robustness)
    _require_nonnegative("selection_strength", params.selection_strength)
    _require_nonnegative("viability_fitness_threshold", params.viability_fitness_threshold)
    _require_fraction(
        "beneficial_adoption_threshold",
        params.beneficial_adoption_threshold,
    )
    _require_fraction("collapse_fitness_threshold", params.collapse_fitness_threshold)

    if params.random_seed is not None and (
        isinstance(params.random_seed, bool)
        or not isinstance(params.random_seed, numbers.Integral)
    ):
        raise ParameterValidationError("random_seed must be an integer or None.")

    if isinstance(params.max_lineage_classes, bool) or not isinstance(
        params.max_lineage_classes,
        numbers.Integral,
    ):
        raise ParameterValidationError("max_lineage_classes must be an integer.")
    if params.max_lineage_classes < 1:
        raise ParameterValidationError("max_lineage_classes must be at least 1.")
    if params.max_lineage_classes > MAX_LINEAGE_CLASSES:
        raise ParameterValidationError(
            f"max_lineage_classes must be <= {MAX_LINEAGE_CLASSES}."
        )

    _require_safe_product(
        "beneficial event rate",
        params.beneficial_mutation_rate,
        mutation_rate_multiplier,
    )
    _require_safe_product(
        "neutral event rate",
        params.neutral_mutation_rate,
        mutation_rate_multiplier,
    )
    _require_safe_product(
        "deleterious event rate",
        params.deleterious_mutation_rate,
        mutation_rate_multiplier,
    )
    _require_safe_product(
        "maximum accumulated lineage decay",
        float(params.generations),
        params.decay_effect_size,
    )
    _require_safe_product(
        "maximum weighted lineage decay",
        float(params.generations),
        params.decay_effect_size,
        params.decay_fitness_penalty,
    )


def validate_m_values(m_values: np.ndarray) -> None:
    """Validate mutation-rate multipliers used by curve functions."""

    if m_values.ndim != 1:
        raise CurveValidationError("m_values must be a one-dimensional array.")
    if m_values.size < 2:
        raise CurveValidationError("m_values must contain at least two points.")
    if not np.all(np.isfinite(m_values)):
        raise CurveValidationError("m_values must contain only finite values.")
    if not np.all(m_values > 0):
        raise CurveValidationError("m_values must be strictly positive.")


def validate_estimation_inputs(
    m_values: np.ndarray,
    benefit_values: np.ndarray,
    decay_values: np.ndarray,
    robustness_values: np.ndarray,
    score_values: np.ndarray,
) -> None:
    """Validate arrays passed to threshold-based range estimation."""

    validate_m_values(m_values)
    if not np.all(np.diff(m_values) > 0):
        raise CurveValidationError("m_values must be strictly increasing for range estimation.")
    validate_curve_outputs(
        m_values,
        benefit_values,
        decay_values,
        robustness_values,
        score_values,
    )


def validate_curve_outputs(
    m_values: np.ndarray,
    benefit_values: np.ndarray,
    decay_values: np.ndarray,
    robustness_values: np.ndarray,
    score_values: np.ndarray,
) -> None:
    """Validate deterministic curve invariants for a completed evaluation."""

    expected_shape = m_values.shape
    arrays = {
        "benefit_values": benefit_values,
        "decay_values": decay_values,
        "robustness_values": robustness_values,
        "score_values": score_values,
    }
    for name, values in arrays.items():
        if values.shape != expected_shape:
            raise CurveValidationError(f"{name} must match the shape of m_values.")
        if not np.all(np.isfinite(values)):
            raise CurveValidationError(f"{name} must contain only finite values.")

    if not np.all(benefit_values >= 0):
        raise CurveValidationError("benefit_values must be non-negative.")
    if not np.all(decay_values >= 0):
        raise CurveValidationError("decay_values must be non-negative.")
    if np.any(robustness_values < -ROBUSTNESS_TOLERANCE) or np.any(
        robustness_values > 1.0 + ROBUSTNESS_TOLERANCE
    ):
        raise CurveValidationError("robustness_values must be bounded between 0 and 1.")


def _require_finite_number(name: str, value: Any) -> float:
    if isinstance(value, bool) or not isinstance(value, numbers.Real):
        raise ParameterValidationError(f"{name} must be a finite number.")
    value = float(value)
    if not math.isfinite(value):
        raise ParameterValidationError(f"{name} must be a finite number.")
    if abs(value) > math.exp(MAX_SAFE_LOG):
        raise ParameterValidationError(f"{name} is too large for stable numerical evaluation.")
    return value


def _require_positive(name: str, value: Any) -> float:
    value = _require_finite_number(name, value)
    if value <= 0:
        raise ParameterValidationError(f"{name} must be positive.")
    return value


def _require_nonnegative(name: str, value: Any) -> float:
    value = _require_finite_number(name, value)
    if value < 0:
        raise ParameterValidationError(f"{name} must be non-negative.")
    return value


def _require_fraction(name: str, value: Any) -> float:
    value = _require_finite_number(name, value)
    if not 0 <= value <= 1:
        raise ParameterValidationError(f"{name} must be between 0 and 1.")
    return value


def _require_safe_power(label: str, base: float, exponent: float) -> None:
    log_value = exponent * math.log(base)
    if log_value > MAX_SAFE_LOG:
        raise ParameterValidationError(
            f"{label} would exceed numerical stability limits; reduce m_max or exponent."
        )


def _require_safe_product(label: str, *factors: float) -> None:
    if any(factor == 0 for factor in factors):
        return
    if any(factor < 0 for factor in factors):
        raise ParameterValidationError(f"{label} factors must be non-negative.")
    log_value = sum(math.log(float(factor)) for factor in factors)
    if log_value > MAX_SAFE_LOG:
        raise ParameterValidationError(
            f"{label} would exceed numerical stability limits; reduce scale, horizon, or range."
        )
