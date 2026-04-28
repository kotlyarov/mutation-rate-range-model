"""Deterministic curve functions for the first model version."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import numpy as np

from .parameters import ModelParameters
from .validation import (
    validate_curve_outputs,
    validate_estimation_inputs,
    validate_m_values,
    validate_parameters,
)

MAX_EXP_ARGUMENT = 700.0
MIN_SURVIVAL_PROBABILITY = np.finfo(float).tiny


@dataclass(frozen=True)
class RangeEstimate:
    """Threshold-based mutation-rate range summary."""

    mu_min: float | None
    mu_peak: float
    mu_max: float | None
    peak_score: float
    benefit_threshold: float
    net_threshold: float
    decay_threshold: float

    def as_dict(self) -> dict[str, float | None]:
        return {
            "mu_min": self.mu_min,
            "mu_peak": self.mu_peak,
            "mu_max": self.mu_max,
            "peak_score": self.peak_score,
            "benefit_threshold": self.benefit_threshold,
            "net_threshold": self.net_threshold,
            "decay_threshold": self.decay_threshold,
        }


@dataclass(frozen=True)
class SurvivalSelectionResult:
    """Expected survival-filtered landscape for threshold estimation."""

    enabled: bool
    effective_selection_strength: float
    relative_fitness: np.ndarray
    survival_probability: np.ndarray
    contribution_weight: np.ndarray
    post_selection_benefit: np.ndarray
    post_selection_decay: np.ndarray
    post_selection_score: np.ndarray


@dataclass(frozen=True)
class ModelResults:
    """Completed deterministic curve evaluation."""

    m_values: np.ndarray
    benefit: np.ndarray
    decay: np.ndarray
    robustness: np.ndarray
    score: np.ndarray
    survival_selection: SurvivalSelectionResult
    range_estimate: RangeEstimate


def make_m_values(params: ModelParameters) -> np.ndarray:
    """Create log-spaced mutation-rate multipliers."""

    validate_parameters(params)
    values = np.logspace(
        np.log10(params.m_min),
        np.log10(params.m_max),
        params.n_points,
    )
    validate_m_values(values)
    return values


def adaptive_benefit(m_values: np.ndarray, params: ModelParameters) -> np.ndarray:
    """Compute selected-environment adaptive benefit, B(m, T)."""

    validate_parameters(params)
    m_values = _as_float_array(m_values)
    validate_m_values(m_values)

    T_scaled = params.T / params.T_ref
    supply_argument = params.alpha_benefit * m_values * T_scaled
    beneficial_supply = -np.expm1(-np.clip(supply_argument, 0.0, MAX_EXP_ARGUMENT))
    interference = 1.0 / (
        1.0 + params.beta_interference * np.power(m_values, params.gamma_interference)
    )
    values = params.benefit_scale * beneficial_supply * interference
    _require_finite("adaptive benefit", values)
    return values


def decay_proxy(m_values: np.ndarray, params: ModelParameters) -> np.ndarray:
    """Compute mutation-accumulation / genome-decay proxy, D(m, T)."""

    validate_parameters(params)
    m_values = _as_float_array(m_values)
    validate_m_values(m_values)

    T_scaled = params.T / params.T_ref
    values = params.decay_scale * np.power(m_values, params.gamma_decay) * T_scaled
    _require_finite("decay proxy", values)
    return values


def robustness(
    m_values: np.ndarray,
    decay_values: np.ndarray,
    params: ModelParameters,
) -> np.ndarray:
    """Compute retained robustness, R(m, T), from decay proxy values."""

    validate_parameters(params)
    m_values = _as_float_array(m_values)
    decay_values = _as_float_array(decay_values)
    validate_m_values(m_values)
    if decay_values.shape != m_values.shape:
        raise ValueError("decay_values must match the shape of m_values.")
    if not np.all(np.isfinite(decay_values)):
        raise ValueError("decay_values must contain only finite values.")
    if not np.all(decay_values >= 0):
        raise ValueError("decay_values must be non-negative.")

    argument = params.k_robustness * decay_values
    values = np.exp(-np.clip(argument, 0.0, MAX_EXP_ARGUMENT))
    _require_finite("robustness", values)
    return values


def net_score(
    benefit_values: np.ndarray,
    decay_values: np.ndarray,
    robustness_values: np.ndarray,
    params: ModelParameters,
) -> np.ndarray:
    """Compute the assumption-dependent net long-term score, S(m, T)."""

    validate_parameters(params)
    benefit_values = _as_float_array(benefit_values)
    decay_values = _as_float_array(decay_values)
    robustness_values = _as_float_array(robustness_values)
    if not (benefit_values.shape == decay_values.shape == robustness_values.shape):
        raise ValueError("benefit, decay, and robustness arrays must have the same shape.")

    values = (
        benefit_values
        - params.lambda_decay * decay_values
        + params.rho_robustness * robustness_values
    )
    _require_finite("net score", values)
    return values


def survival_selection(
    benefit_values: np.ndarray,
    decay_values: np.ndarray,
    robustness_values: np.ndarray,
    score_values: np.ndarray,
    params: ModelParameters,
) -> SurvivalSelectionResult:
    """Apply expected fitness-weighted survival filtering.

    The layer is a soft-selection expectation, not an individual-based
    simulation. Survival probabilities are proportional to positive relative
    fitness weights derived from the net score, then mixed with neutral
    survival according to ``survival_stochasticity``.
    """

    validate_parameters(params)
    benefit_values = _as_float_array(benefit_values)
    decay_values = _as_float_array(decay_values)
    robustness_values = _as_float_array(robustness_values)
    score_values = _as_float_array(score_values)
    if score_values.ndim != 1 or score_values.size < 2:
        raise ValueError("survival selection arrays must contain at least two points.")
    if not (
        benefit_values.shape
        == decay_values.shape
        == robustness_values.shape
        == score_values.shape
    ):
        raise ValueError(
            "benefit, decay, robustness, and score arrays must have the same shape."
        )
    for label, values in {
        "benefit": benefit_values,
        "decay": decay_values,
        "robustness": robustness_values,
        "score": score_values,
    }.items():
        _require_finite(label, values)

    neutral_probability = np.full(
        score_values.shape,
        1.0 / score_values.size,
        dtype=float,
    )
    if not params.survival_selection_enabled:
        neutral_weight = np.ones_like(score_values, dtype=float)
        return SurvivalSelectionResult(
            enabled=False,
            effective_selection_strength=0.0,
            relative_fitness=neutral_weight,
            survival_probability=neutral_probability,
            contribution_weight=neutral_weight,
            post_selection_benefit=benefit_values.copy(),
            post_selection_decay=decay_values.copy(),
            post_selection_score=score_values.copy(),
        )

    effective_selection_strength = (
        params.selection_strength / params.population_growth_factor
    )
    relative_fitness = _relative_fitness_from_score(
        score_values,
        effective_selection_strength,
    )
    fitness_weighted_probability = relative_fitness / np.sum(relative_fitness)
    stochasticity = params.survival_stochasticity
    survival_probability = (
        (1.0 - stochasticity) * fitness_weighted_probability
        + stochasticity * neutral_probability
    )
    survival_probability = survival_probability / np.sum(survival_probability)
    survival_probability = np.maximum(survival_probability, MIN_SURVIVAL_PROBABILITY)
    survival_probability = survival_probability / np.sum(survival_probability)
    contribution_weight = survival_probability / neutral_probability

    post_selection_benefit = benefit_values * contribution_weight
    post_selection_decay = decay_values * contribution_weight
    post_selection_score = _post_selection_score(score_values, contribution_weight)
    for label, values in {
        "survival probability": survival_probability,
        "survival contribution weight": contribution_weight,
        "post-selection benefit": post_selection_benefit,
        "post-selection decay": post_selection_decay,
        "post-selection score": post_selection_score,
    }.items():
        _require_finite(label, values)

    return SurvivalSelectionResult(
        enabled=True,
        effective_selection_strength=float(effective_selection_strength),
        relative_fitness=relative_fitness,
        survival_probability=survival_probability,
        contribution_weight=contribution_weight,
        post_selection_benefit=post_selection_benefit,
        post_selection_decay=post_selection_decay,
        post_selection_score=post_selection_score,
    )


def estimate_range(
    m_values: np.ndarray,
    benefit_values: np.ndarray,
    decay_values: np.ndarray,
    robustness_values: np.ndarray,
    score_values: np.ndarray,
    params: ModelParameters,
) -> RangeEstimate:
    """Estimate mu_min, mu_peak, and mu_max with configurable thresholds."""

    validate_parameters(params)
    m_values = _as_float_array(m_values)
    benefit_values = _as_float_array(benefit_values)
    decay_values = _as_float_array(decay_values)
    robustness_values = _as_float_array(robustness_values)
    score_values = _as_float_array(score_values)
    validate_estimation_inputs(
        m_values,
        benefit_values,
        decay_values,
        robustness_values,
        score_values,
    )

    peak_index = int(np.argmax(score_values))
    mu_peak = float(m_values[peak_index])
    peak_score = float(score_values[peak_index])

    max_benefit = float(np.max(benefit_values))
    benefit_threshold = params.benefit_threshold_fraction * max_benefit
    benefit_mask = benefit_values >= benefit_threshold
    mu_min = float(m_values[np.flatnonzero(benefit_mask)[0]]) if np.any(benefit_mask) else None

    max_decay = float(np.max(decay_values))
    decay_threshold = params.decay_threshold_fraction * max_decay
    max_score = float(np.max(score_values))
    net_threshold = (
        params.net_threshold_fraction * max_score
        if max_score > 0
        else max_score
    )
    range_mask = (score_values >= net_threshold) & (decay_values <= decay_threshold)
    mu_max = float(m_values[np.flatnonzero(range_mask)[-1]]) if np.any(range_mask) else None

    return RangeEstimate(
        mu_min=mu_min,
        mu_peak=mu_peak,
        mu_max=mu_max,
        peak_score=peak_score,
        benefit_threshold=float(benefit_threshold),
        net_threshold=float(net_threshold),
        decay_threshold=float(decay_threshold),
    )


def evaluate_model(params: ModelParameters | None = None) -> ModelResults:
    """Evaluate all deterministic curves and range estimates."""

    params = params or ModelParameters()
    validate_parameters(params)
    m_values = make_m_values(params)
    benefit_values = adaptive_benefit(m_values, params)
    decay_values = decay_proxy(m_values, params)
    robustness_values = robustness(m_values, decay_values, params)
    score_values = net_score(benefit_values, decay_values, robustness_values, params)
    validate_curve_outputs(
        m_values,
        benefit_values,
        decay_values,
        robustness_values,
        score_values,
    )
    survival_values = survival_selection(
        benefit_values,
        decay_values,
        robustness_values,
        score_values,
        params,
    )
    validate_curve_outputs(
        m_values,
        survival_values.post_selection_benefit,
        survival_values.post_selection_decay,
        robustness_values,
        survival_values.post_selection_score,
    )
    range_estimate = estimate_range(
        m_values,
        survival_values.post_selection_benefit,
        survival_values.post_selection_decay,
        robustness_values,
        survival_values.post_selection_score,
        params,
    )
    return ModelResults(
        m_values=m_values,
        benefit=benefit_values,
        decay=decay_values,
        robustness=robustness_values,
        score=score_values,
        survival_selection=survival_values,
        range_estimate=range_estimate,
    )


def _as_float_array(values: Any) -> np.ndarray:
    return np.asarray(values, dtype=float)


def _relative_fitness_from_score(
    score_values: np.ndarray,
    effective_selection_strength: float,
) -> np.ndarray:
    if effective_selection_strength == 0:
        return np.ones_like(score_values, dtype=float)
    centered = score_values - np.max(score_values)
    exponent = np.clip(
        effective_selection_strength * centered,
        -MAX_EXP_ARGUMENT,
        0.0,
    )
    values = np.exp(exponent)
    if not np.any(values > 0):
        return np.ones_like(score_values, dtype=float)
    return values


def _post_selection_score(
    score_values: np.ndarray,
    contribution_weight: np.ndarray,
) -> np.ndarray:
    return score_values + np.log(contribution_weight)


def _require_finite(label: str, values: np.ndarray) -> None:
    if not np.all(np.isfinite(values)):
        raise ValueError(f"{label} produced non-finite values.")
