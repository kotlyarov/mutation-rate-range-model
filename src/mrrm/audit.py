"""Calibration audit helpers for fitted deterministic inputs."""

from __future__ import annotations

from dataclasses import dataclass
from math import sqrt
from typing import Any

import numpy as np

from .calibration import (
    BENEFIT_PARAMETER_NAMES,
    CalibrationResult,
    available_strains,
    derive_calibrated_parameters,
    select_calibration_observations,
)
from .curves import adaptive_benefit, evaluate_model
from .parameters import ModelParameters


@dataclass(frozen=True)
class CalibrationAuditFit:
    """Audit details for one calibration scope."""

    label: str
    calibration: CalibrationResult
    selected_rows: list[dict[str, Any]]
    observed_rows: list[dict[str, Any]]
    fit_rows: list[dict[str, Any]]
    excluded_rows: list[dict[str, Any]]
    fitted_parameters: list[dict[str, Any]]
    objective: dict[str, float | int | str]
    predictions: list[dict[str, Any]]
    threshold_estimate: dict[str, float | None]


@dataclass(frozen=True)
class CalibrationAudit:
    """Selected-strain, all-strain, and leave-one-strain-out audit."""

    selected_strain: str | None
    target_generation: float | None
    selected_strain_fit: CalibrationAuditFit
    all_strain_fit: CalibrationAuditFit
    leave_one_strain_out: list[dict[str, Any]]


def build_calibration_audit(
    observations: list[dict[str, Any]],
    selected_strain: str | None,
    target_generation: float | None,
    base_params: ModelParameters | None = None,
) -> CalibrationAudit:
    """Build transparent diagnostics for current calibration evidence."""

    base_params = base_params or ModelParameters()
    selected_fit = build_calibration_audit_fit(
        observations,
        label=f"selected strain: {selected_strain or 'all'}",
        strain=selected_strain,
        target_generation=target_generation,
        base_params=base_params,
    )
    all_fit = build_calibration_audit_fit(
        observations,
        label="all strains",
        strain=None,
        target_generation=target_generation,
        base_params=base_params,
    )
    return CalibrationAudit(
        selected_strain=selected_strain,
        target_generation=target_generation,
        selected_strain_fit=selected_fit,
        all_strain_fit=all_fit,
        leave_one_strain_out=_leave_one_strain_out(
            observations,
            target_generation=target_generation,
            base_params=base_params,
        ),
    )


def build_calibration_audit_fit(
    observations: list[dict[str, Any]],
    label: str,
    strain: str | None,
    target_generation: float | None,
    base_params: ModelParameters | None = None,
) -> CalibrationAuditFit:
    """Build diagnostics for one selected calibration scope."""

    base_params = base_params or ModelParameters()
    calibration = derive_calibrated_parameters(
        observations,
        base_params=base_params,
        strain=strain,
        target_generation=target_generation,
    )
    selected_rows = select_calibration_observations(
        observations,
        strain=strain,
        target_generation=target_generation,
    )
    observed_rows = _exact_fitness_rows(selected_rows)
    fit_rows = _benefit_fit_rows(observed_rows)
    excluded_rows = [row for row in observed_rows if row not in fit_rows]
    predictions = _prediction_rows(
        observed_rows,
        calibration.params,
        fit_row_ids=_row_ids(fit_rows),
    )
    fit_predictions = _prediction_rows(
        fit_rows,
        calibration.params,
        fit_row_ids=_row_ids(fit_rows),
    )
    return CalibrationAuditFit(
        label=label,
        calibration=calibration,
        selected_rows=selected_rows,
        observed_rows=observed_rows,
        fit_rows=fit_rows,
        excluded_rows=excluded_rows,
        fitted_parameters=_fitted_parameter_rows(calibration),
        objective=_loss_summary(
            fit_predictions,
            objective="sum squared residuals on rows used for benefit fitting",
        ),
        predictions=predictions,
        threshold_estimate=evaluate_model(calibration.params).range_estimate.as_dict(),
    )


def _leave_one_strain_out(
    observations: list[dict[str, Any]],
    target_generation: float | None,
    base_params: ModelParameters,
) -> list[dict[str, Any]]:
    selected_rows = select_calibration_observations(
        observations,
        target_generation=target_generation,
    )
    strains = available_strains(selected_rows)
    results: list[dict[str, Any]] = []
    for heldout in strains:
        training_rows = [
            row for row in selected_rows if row.get("strain_or_population") != heldout
        ]
        heldout_rows = [
            row for row in selected_rows if row.get("strain_or_population") == heldout
        ]
        training_fit = build_calibration_audit_fit(
            training_rows,
            label=f"leave out {heldout}",
            strain=None,
            target_generation=target_generation,
            base_params=base_params,
        )
        heldout_observed = _exact_fitness_rows(heldout_rows)
        heldout_predictions = _prediction_rows(
            heldout_observed,
            training_fit.calibration.params,
            fit_row_ids=set(),
        )
        train_loss = training_fit.objective
        heldout_loss = _loss_summary(
            heldout_predictions,
            objective="sum squared residuals on held-out observed fitness rows",
        )
        results.append(
            {
                "heldout_strain": heldout,
                "training_fit_rows": len(training_fit.fit_rows),
                "heldout_observed_rows": len(heldout_observed),
                "training_sse": train_loss["sse"],
                "training_rmse": train_loss["rmse"],
                "heldout_sse": heldout_loss["sse"],
                "heldout_rmse": heldout_loss["rmse"],
                "heldout_mae": heldout_loss["mae"],
                "heldout_bias": heldout_loss["mean_residual"],
                "trained_benefit_scale": training_fit.calibration.params.benefit_scale,
                "trained_alpha_benefit": training_fit.calibration.params.alpha_benefit,
                "trained_beta_interference": training_fit.calibration.params.beta_interference,
                "trained_gamma_interference": training_fit.calibration.params.gamma_interference,
            }
        )
    return results


def _exact_fitness_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        row
        for row in rows
        if row.get("measurement_kind") == "relative_fitness"
        and row.get("measurement_value") is not None
        and row.get("generation") is not None
        and row["generation"] > 0
        and row.get("mutation_rate_multiplier") is not None
    ]


def _benefit_fit_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        row
        for row in rows
        if row.get("measurement_value") is not None
        and row["measurement_value"] >= 0
    ]


def _prediction_rows(
    rows: list[dict[str, Any]],
    params: ModelParameters,
    fit_row_ids: set[str],
) -> list[dict[str, Any]]:
    if not rows:
        return []

    m_values = np.asarray([row["mutation_rate_multiplier"] for row in rows], dtype=float)
    predicted = adaptive_benefit(m_values, params)
    prediction_rows: list[dict[str, Any]] = []
    for row, prediction in zip(rows, predicted):
        observed = float(row["measurement_value"])
        predicted_value = float(prediction)
        residual = observed - predicted_value
        prediction_rows.append(
            {
                "observation_id": row["observation_id"],
                "strain": row["strain_or_population"],
                "replicate": row["replicate"],
                "generation": row["generation"],
                "mutation_rate_multiplier": row["mutation_rate_multiplier"],
                "observed_relative_fitness": observed,
                "predicted_benefit": predicted_value,
                "residual_observed_minus_predicted": residual,
                "absolute_residual": abs(residual),
                "used_for_fit": row["observation_id"] in fit_row_ids,
                "fitness_control": row["fitness_control"],
            }
        )
    return prediction_rows


def _loss_summary(
    predictions: list[dict[str, Any]],
    objective: str,
) -> dict[str, float | int | str]:
    if not predictions:
        return {
            "n_rows": 0,
            "sse": 0.0,
            "mse": 0.0,
            "rmse": 0.0,
            "mae": 0.0,
            "mean_residual": 0.0,
            "objective": objective,
        }

    residuals = np.asarray(
        [row["residual_observed_minus_predicted"] for row in predictions],
        dtype=float,
    )
    absolute = np.abs(residuals)
    sse = float(np.dot(residuals, residuals))
    mse = float(sse / len(residuals))
    return {
        "n_rows": len(predictions),
        "sse": sse,
        "mse": mse,
        "rmse": float(sqrt(mse)),
        "mae": float(np.mean(absolute)),
        "mean_residual": float(np.mean(residuals)),
        "objective": objective,
    }


def _fitted_parameter_rows(calibration: CalibrationResult) -> list[dict[str, Any]]:
    rows = []
    for name in sorted(BENEFIT_PARAMETER_NAMES):
        estimate = calibration.estimates[name]
        rows.append(estimate.as_dict())
    return rows


def _row_ids(rows: list[dict[str, Any]]) -> set[str]:
    return {row["observation_id"] for row in rows}
