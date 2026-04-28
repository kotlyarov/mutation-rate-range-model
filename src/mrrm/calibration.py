"""Data-driven parameter calibration and provenance tracking."""

from __future__ import annotations

from dataclasses import dataclass, fields, replace
from typing import Any

import numpy as np

from .data_loaders import load_calibration_dataset
from .parameters import ModelParameters

PROVENANCE_EMPIRICAL = "Empirical"
PROVENANCE_FITTED = "Fitted"
PROVENANCE_ASSUMED = "Assumed"
PROVENANCE_UNSUPPORTED = "Unidentified / unsupported by current data"

BENEFIT_PARAMETER_NAMES = {
    "benefit_scale",
    "alpha_benefit",
    "beta_interference",
    "gamma_interference",
}
DECAY_PARAMETER_NAMES = {"decay_scale", "gamma_decay"}
ROBUSTNESS_PARAMETER_NAMES = {"k_robustness"}
WEIGHT_PARAMETER_NAMES = {"lambda_decay", "rho_robustness"}
THRESHOLD_PARAMETER_NAMES = {
    "benefit_threshold_fraction",
    "net_threshold_fraction",
    "decay_threshold_fraction",
}


@dataclass(frozen=True)
class ParameterEstimate:
    """Value and provenance for one model input."""

    name: str
    value: float | int
    lower: float | int | None
    upper: float | int | None
    provenance: str
    source: str
    notes: str

    def as_dict(self) -> dict[str, Any]:
        return {
            "parameter": self.name,
            "value": self.value,
            "lower": self.lower,
            "upper": self.upper,
            "provenance": self.provenance,
            "source": self.source,
            "notes": self.notes,
        }


@dataclass(frozen=True)
class CalibrationResult:
    """Calibrated parameters plus provenance for every model input."""

    params: ModelParameters
    estimates: dict[str, ParameterEstimate]
    observation_count: int
    fitness_observation_count: int
    decay_observation_count: int

    def provenance_rows(self) -> list[dict[str, Any]]:
        return [self.estimates[name].as_dict() for name in model_parameter_names()]


def model_parameter_names() -> list[str]:
    """Return ModelParameters fields in dataclass order."""

    return [field.name for field in fields(ModelParameters)]


def derive_calibrated_parameters(
    observations: list[dict[str, Any]] | None = None,
    base_params: ModelParameters | None = None,
) -> CalibrationResult:
    """Derive model inputs from calibration observations where data support it."""

    observations = observations if observations is not None else load_calibration_dataset()
    base_params = base_params or ModelParameters()
    updates: dict[str, float | int] = {}
    estimates: dict[str, ParameterEstimate] = {}

    _derive_mutation_axis(observations, base_params, updates, estimates)
    _derive_generation_horizon(observations, base_params, updates, estimates)

    working_params = replace(base_params, **updates)
    fitness_rows = _rows_with_measurement(observations, "fitness")
    decay_rows = _rows_with_decay_measurements(observations)

    if fitness_rows:
        fitted = _fit_benefit_parameters(fitness_rows, working_params)
        updates.update(fitted)
        working_params = replace(base_params, **updates)
        for name in BENEFIT_PARAMETER_NAMES:
            estimates[name] = ParameterEstimate(
                name=name,
                value=getattr(working_params, name),
                lower=None,
                upper=None,
                provenance=PROVENANCE_FITTED,
                source="calibration_dataset_v0 fitness-vs-control rows",
                notes="Estimated by deterministic least-squares fit to exact fitness observations.",
            )

    if decay_rows:
        fitted = _fit_decay_parameters(decay_rows, working_params)
        updates.update(fitted)
        working_params = replace(base_params, **updates)
        for name in DECAY_PARAMETER_NAMES:
            estimates[name] = ParameterEstimate(
                name=name,
                value=getattr(working_params, name),
                lower=None,
                upper=None,
                provenance=PROVENANCE_FITTED,
                source="calibration_dataset_v0 mutation-count/genome-decay rows",
                notes="Estimated by log-linear fit to exact decay-proxy observations.",
            )

    params = replace(base_params, **updates)
    _fill_unestimated_parameters(params, estimates)
    return CalibrationResult(
        params=params,
        estimates=estimates,
        observation_count=len(observations),
        fitness_observation_count=len(fitness_rows),
        decay_observation_count=len(decay_rows),
    )


def _derive_mutation_axis(
    observations: list[dict[str, Any]],
    base_params: ModelParameters,
    updates: dict[str, float | int],
    estimates: dict[str, ParameterEstimate],
) -> None:
    rows = [
        row
        for row in observations
        if row.get("mutation_rate_multiplier") is not None
    ]
    if not rows:
        return

    lower_values = [
        row.get("mutation_rate_multiplier_lower") or row["mutation_rate_multiplier"]
        for row in rows
    ]
    upper_values = [
        row.get("mutation_rate_multiplier_upper") or row["mutation_rate_multiplier"]
        for row in rows
    ]
    m_min = float(min(lower_values))
    m_max = float(max(upper_values))
    updates["m_min"] = m_min
    updates["m_max"] = m_max
    source = "calibration_dataset_v0 mutation-rate multiplier intervals"
    estimates["m_min"] = ParameterEstimate(
        name="m_min",
        value=m_min,
        lower=m_min,
        upper=m_min,
        provenance=PROVENANCE_EMPIRICAL,
        source=source,
        notes="Smallest lower bound among observed mutation-rate multiplier intervals.",
    )
    estimates["m_max"] = ParameterEstimate(
        name="m_max",
        value=m_max,
        lower=m_max,
        upper=m_max,
        provenance=PROVENANCE_EMPIRICAL,
        source=source,
        notes="Largest upper bound among observed mutation-rate multiplier intervals.",
    )


def _derive_generation_horizon(
    observations: list[dict[str, Any]],
    base_params: ModelParameters,
    updates: dict[str, float | int],
    estimates: dict[str, ParameterEstimate],
) -> None:
    generations = [
        row["generation"]
        for row in observations
        if row.get("generation") is not None
    ]
    positive_generations = [generation for generation in generations if generation > 0]
    if not positive_generations:
        return

    horizon = float(max(positive_generations))
    updates["T"] = horizon
    updates["T_ref"] = horizon
    source = "calibration_dataset_v0 generation values"
    estimates["T"] = ParameterEstimate(
        name="T",
        value=horizon,
        lower=float(min(positive_generations)),
        upper=horizon,
        provenance=PROVENANCE_EMPIRICAL,
        source=source,
        notes="Maximum positive generation represented by current calibration observations.",
    )
    estimates["T_ref"] = ParameterEstimate(
        name="T_ref",
        value=horizon,
        lower=horizon,
        upper=horizon,
        provenance=PROVENANCE_EMPIRICAL,
        source=source,
        notes="Set equal to empirical horizon so calibrated evaluations use T_scaled = 1.",
    )


def _fill_unestimated_parameters(
    params: ModelParameters,
    estimates: dict[str, ParameterEstimate],
) -> None:
    for name in model_parameter_names():
        if name in estimates:
            continue
        value = getattr(params, name)
        provenance, source, notes = _fallback_provenance(name)
        estimates[name] = ParameterEstimate(
            name=name,
            value=value,
            lower=None,
            upper=None,
            provenance=provenance,
            source=source,
            notes=notes,
        )


def _fallback_provenance(name: str) -> tuple[str, str, str]:
    if name == "n_points":
        return (
            PROVENANCE_ASSUMED,
            "computational grid setting",
            "Resolution of model evaluation grid, not a biological parameter.",
        )
    if name in THRESHOLD_PARAMETER_NAMES:
        return (
            PROVENANCE_ASSUMED,
            "user-selected decision rule",
            "Threshold rule for range reporting; not estimated from current data.",
        )
    if name in WEIGHT_PARAMETER_NAMES:
        return (
            PROVENANCE_ASSUMED,
            "exploratory utility weighting",
            "Retained manual weight because current data do not identify this trade-off weight.",
        )
    if name in BENEFIT_PARAMETER_NAMES:
        return (
            PROVENANCE_UNSUPPORTED,
            "no exact fitness-vs-control values in calibration_dataset_v0",
            "Exploratory fallback value only; requires exact fitness observations to fit.",
        )
    if name in DECAY_PARAMETER_NAMES:
        return (
            PROVENANCE_UNSUPPORTED,
            "no mutation-count/genome-decay cost values in calibration_dataset_v0",
            "Exploratory fallback value only; requires exact decay observations to fit.",
        )
    if name in ROBUSTNESS_PARAMETER_NAMES:
        return (
            PROVENANCE_UNSUPPORTED,
            "no exact robustness observations in calibration_dataset_v0",
            "Exploratory fallback value only; requires exact robustness observations to fit.",
        )
    return (
        PROVENANCE_ASSUMED,
        "exploratory default",
        "Retained from default model parameters.",
    )


def _rows_with_measurement(observations: list[dict[str, Any]], token: str) -> list[dict[str, Any]]:
    return [
        row
        for row in observations
        if token in row.get("measurement_kind", "")
        and row.get("measurement_value") is not None
        and row.get("mutation_rate_multiplier") is not None
    ]


def _rows_with_decay_measurements(observations: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        row
        for row in observations
        if row.get("measurement_kind") in {"mutation_count", "genome_decay_proxy"}
        and row.get("measurement_value") is not None
        and row.get("mutation_rate_multiplier") is not None
    ]


def _fit_benefit_parameters(
    rows: list[dict[str, Any]],
    params: ModelParameters,
) -> dict[str, float]:
    m_values = np.asarray([row["mutation_rate_multiplier"] for row in rows], dtype=float)
    y_values = np.asarray([row["measurement_value"] for row in rows], dtype=float)
    if np.any(y_values < 0):
        raise ValueError("Benefit fitting requires non-negative fitness benefit values.")

    alpha_grid = np.logspace(-3, 1, 24)
    beta_grid = np.logspace(-4, 1, 24)
    gamma_grid = np.asarray([0.5, 1.0, 1.5, 2.0, 3.0], dtype=float)
    T_scaled = params.T / params.T_ref
    best: tuple[float, float, float, float, float] | None = None
    for alpha in alpha_grid:
        supply = -np.expm1(-alpha * m_values * T_scaled)
        for beta in beta_grid:
            for gamma in gamma_grid:
                basis = supply / (1.0 + beta * np.power(m_values, gamma))
                denominator = float(np.dot(basis, basis))
                if denominator <= 0:
                    continue
                scale = max(float(np.dot(basis, y_values) / denominator), 0.0)
                residual = scale * basis - y_values
                sse = float(np.dot(residual, residual))
                if best is None or sse < best[0]:
                    best = (sse, scale, alpha, beta, gamma)

    if best is None:
        raise ValueError("Could not fit benefit parameters from calibration data.")
    _sse, scale, alpha, beta, gamma = best
    return {
        "benefit_scale": scale,
        "alpha_benefit": alpha,
        "beta_interference": beta,
        "gamma_interference": gamma,
    }


def _fit_decay_parameters(
    rows: list[dict[str, Any]],
    params: ModelParameters,
) -> dict[str, float]:
    m_values = np.asarray([row["mutation_rate_multiplier"] for row in rows], dtype=float)
    y_values = np.asarray([row["measurement_value"] for row in rows], dtype=float)
    positive = (m_values > 0) & (y_values > 0)
    if np.count_nonzero(positive) < 2:
        raise ValueError("Decay fitting requires at least two positive observations.")

    slope, intercept = np.polyfit(np.log(m_values[positive]), np.log(y_values[positive]), 1)
    T_scaled = params.T / params.T_ref
    return {
        "decay_scale": float(np.exp(intercept) / T_scaled),
        "gamma_decay": float(slope),
    }
