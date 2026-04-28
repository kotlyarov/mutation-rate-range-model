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
    generation_count: int
    relative_fitness: np.ndarray
    survival_probability: np.ndarray
    contribution_weight: np.ndarray
    post_selection_benefit: np.ndarray
    post_selection_decay: np.ndarray
    post_selection_robustness: np.ndarray
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
    values = _adaptive_benefit_for_scaled_time(m_values, params, T_scaled)
    _require_finite("adaptive benefit", values)
    return values


def decay_proxy(m_values: np.ndarray, params: ModelParameters) -> np.ndarray:
    """Compute mutation-accumulation / genome-decay proxy, D(m, T)."""

    validate_parameters(params)
    m_values = _as_float_array(m_values)
    validate_m_values(m_values)

    T_scaled = params.T / params.T_ref
    values = _decay_proxy_for_scaled_time(m_values, params, T_scaled)
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

    values = _robustness_from_decay(decay_values, params)
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

    values = _net_score_from_components(
        benefit_values,
        decay_values,
        robustness_values,
        params,
    )
    _require_finite("net score", values)
    return values


def survival_selection(
    m_values: np.ndarray,
    benefit_values: np.ndarray,
    decay_values: np.ndarray,
    robustness_values: np.ndarray,
    score_values: np.ndarray,
    params: ModelParameters,
) -> SurvivalSelectionResult:
    """Apply recursive expected fitness-weighted survival filtering.

    The layer is a soft-selection expectation, not an individual-based
    simulation. Population composition is updated once per model generation,
    using fitness-weighted survival mixed with neutral survival according to
    ``survival_stochasticity``.
    """

    validate_parameters(params)
    m_values = _as_float_array(m_values)
    benefit_values = _as_float_array(benefit_values)
    decay_values = _as_float_array(decay_values)
    robustness_values = _as_float_array(robustness_values)
    score_values = _as_float_array(score_values)
    validate_m_values(m_values)
    if score_values.ndim != 1 or score_values.size < 2:
        raise ValueError("survival selection arrays must contain at least two points.")
    if not (
        m_values.shape
        == benefit_values.shape
        == decay_values.shape
        == robustness_values.shape
        == score_values.shape
    ):
        raise ValueError(
            "m_values, benefit, decay, robustness, and score arrays must have the same shape."
        )
    for label, values in {
        "m_values": m_values,
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
            generation_count=0,
            relative_fitness=neutral_weight,
            survival_probability=neutral_probability,
            contribution_weight=neutral_weight,
            post_selection_benefit=benefit_values.copy(),
            post_selection_decay=decay_values.copy(),
            post_selection_robustness=robustness_values.copy(),
            post_selection_score=score_values.copy(),
        )

    effective_selection_strength = (
        params.selection_strength / params.population_growth_factor
    )
    generation_count = _generation_count(params)
    total_scaled_time = params.T / params.T_ref
    stochasticity = params.survival_stochasticity
    composition = neutral_probability.copy()
    post_selection_benefit = np.zeros_like(score_values, dtype=float)
    post_selection_decay = np.zeros_like(score_values, dtype=float)
    previous_benefit = np.zeros_like(score_values, dtype=float)
    previous_decay = np.zeros_like(score_values, dtype=float)
    relative_fitness = np.ones_like(score_values, dtype=float)

    for generation in range(1, generation_count + 1):
        scaled_time = total_scaled_time * (generation / generation_count)
        current_benefit = _adaptive_benefit_for_scaled_time(
            m_values,
            params,
            scaled_time,
        )
        current_decay = _decay_proxy_for_scaled_time(m_values, params, scaled_time)
        current_robustness = _robustness_from_decay(current_decay, params)
        current_score = _net_score_from_components(
            current_benefit,
            current_decay,
            current_robustness,
            params,
        )

        relative_fitness = _relative_fitness_from_score(
            current_score,
            effective_selection_strength,
        )
        selected_composition = composition * relative_fitness
        selected_total = float(np.sum(selected_composition))
        if selected_total <= 0 or not np.isfinite(selected_total):
            selected_composition = composition.copy()
        else:
            selected_composition = selected_composition / selected_total

        next_composition = (
            (1.0 - stochasticity) * selected_composition
            + stochasticity * composition
        )
        next_composition = _normalize_probability(next_composition)
        contribution_weight = next_composition / neutral_probability

        benefit_increment = current_benefit - previous_benefit
        decay_increment = current_decay - previous_decay
        post_selection_benefit += benefit_increment * contribution_weight
        post_selection_decay += decay_increment * contribution_weight

        composition = next_composition
        previous_benefit = current_benefit
        previous_decay = current_decay

    survival_probability = composition
    contribution_weight = survival_probability / neutral_probability
    post_selection_robustness = _robustness_from_decay(post_selection_decay, params)
    post_selection_score = _net_score_from_components(
        post_selection_benefit,
        post_selection_decay,
        post_selection_robustness,
        params,
    )
    for label, values in {
        "survival probability": survival_probability,
        "survival contribution weight": contribution_weight,
        "post-selection benefit": post_selection_benefit,
        "post-selection decay": post_selection_decay,
        "post-selection robustness": post_selection_robustness,
        "post-selection score": post_selection_score,
    }.items():
        _require_finite(label, values)

    return SurvivalSelectionResult(
        enabled=True,
        effective_selection_strength=float(effective_selection_strength),
        generation_count=generation_count,
        relative_fitness=relative_fitness,
        survival_probability=survival_probability,
        contribution_weight=contribution_weight,
        post_selection_benefit=post_selection_benefit,
        post_selection_decay=post_selection_decay,
        post_selection_robustness=post_selection_robustness,
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
    max_score = float(np.max(score_values))
    net_threshold = (
        params.net_threshold_fraction * max_score
        if max_score > 0
        else max_score
    )
    max_decay = float(np.max(decay_values))
    decay_threshold = max(
        params.decay_threshold_fraction * max_decay,
        float(decay_values[peak_index]),
    )

    lower_mask = (benefit_values >= benefit_threshold) & (score_values >= net_threshold)
    upper_mask = (score_values >= net_threshold) & (decay_values <= decay_threshold)
    lower_mask[peak_index] = True
    upper_mask[peak_index] = True
    left_index = _left_bound_around_peak(lower_mask, peak_index)
    right_index = _right_bound_around_peak(upper_mask, peak_index)
    mu_min = float(m_values[left_index])
    mu_max = float(m_values[right_index])

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
        m_values,
        benefit_values,
        decay_values,
        robustness_values,
        score_values,
        params,
    )
    chart_benefit_values = survival_values.post_selection_benefit
    chart_decay_values = survival_values.post_selection_decay
    chart_robustness_values = survival_values.post_selection_robustness
    chart_score_values = survival_values.post_selection_score
    validate_curve_outputs(
        m_values,
        chart_benefit_values,
        chart_decay_values,
        chart_robustness_values,
        chart_score_values,
    )
    range_estimate = estimate_range(
        m_values,
        chart_benefit_values,
        chart_decay_values,
        chart_robustness_values,
        chart_score_values,
        params,
    )
    return ModelResults(
        m_values=m_values,
        benefit=chart_benefit_values,
        decay=chart_decay_values,
        robustness=chart_robustness_values,
        score=chart_score_values,
        survival_selection=survival_values,
        range_estimate=range_estimate,
    )


def _as_float_array(values: Any) -> np.ndarray:
    return np.asarray(values, dtype=float)


def _adaptive_benefit_for_scaled_time(
    m_values: np.ndarray,
    params: ModelParameters,
    T_scaled: float,
) -> np.ndarray:
    supply_argument = params.alpha_benefit * m_values * T_scaled
    beneficial_supply = -np.expm1(-np.clip(supply_argument, 0.0, MAX_EXP_ARGUMENT))
    interference = 1.0 / (
        1.0 + params.beta_interference * np.power(m_values, params.gamma_interference)
    )
    return params.benefit_scale * beneficial_supply * interference


def _decay_proxy_for_scaled_time(
    m_values: np.ndarray,
    params: ModelParameters,
    T_scaled: float,
) -> np.ndarray:
    return params.decay_scale * np.power(m_values, params.gamma_decay) * T_scaled


def _robustness_from_decay(
    decay_values: np.ndarray,
    params: ModelParameters,
) -> np.ndarray:
    argument = params.k_robustness * decay_values
    return np.exp(-np.clip(argument, 0.0, MAX_EXP_ARGUMENT))


def _net_score_from_components(
    benefit_values: np.ndarray,
    decay_values: np.ndarray,
    robustness_values: np.ndarray,
    params: ModelParameters,
) -> np.ndarray:
    return (
        benefit_values
        - params.lambda_decay * decay_values
        + params.rho_robustness * robustness_values
    )


def _generation_count(params: ModelParameters) -> int:
    return max(1, int(round(params.T)))


def _normalize_probability(values: np.ndarray) -> np.ndarray:
    values = np.maximum(values, MIN_SURVIVAL_PROBABILITY)
    return values / np.sum(values)


def _left_bound_around_peak(
    mask: np.ndarray,
    peak_index: int,
) -> int:
    left_index = peak_index
    while left_index > 0 and bool(mask[left_index - 1]):
        left_index -= 1
    return left_index


def _right_bound_around_peak(
    mask: np.ndarray,
    peak_index: int,
) -> int:
    right_index = peak_index
    while right_index < mask.size - 1 and bool(mask[right_index + 1]):
        right_index += 1
    return right_index


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


def _require_finite(label: str, values: np.ndarray) -> None:
    if not np.all(np.isfinite(values)):
        raise ValueError(f"{label} produced non-finite values.")
