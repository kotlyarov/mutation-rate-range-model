from dataclasses import fields

import pytest

from mrrm.calibration import (
    PROVENANCE_EMPIRICAL,
    PROVENANCE_FITTED,
    PROVENANCE_UNSUPPORTED,
    available_generations,
    available_strains,
    derive_calibrated_parameters,
)
from mrrm.curves import evaluate_model
from mrrm.data_loaders import load_calibration_dataset
from mrrm.parameters import ModelParameters


def test_calibration_derives_mutation_axis_and_horizon_from_observations():
    calibration = derive_calibrated_parameters()

    assert calibration.params.T == 3000.0
    assert calibration.params.T_ref == 3000.0
    assert calibration.params.m_min == 0.0444444444444
    assert calibration.params.m_max == 168.16
    assert calibration.estimates["T"].provenance == PROVENANCE_EMPIRICAL
    assert calibration.estimates["m_min"].provenance == PROVENANCE_EMPIRICAL
    assert calibration.estimates["m_max"].provenance == PROVENANCE_EMPIRICAL


def test_every_model_parameter_has_provenance():
    calibration = derive_calibrated_parameters()
    expected_names = {field.name for field in fields(ModelParameters)}

    assert set(calibration.estimates) == expected_names
    assert {row["parameter"] for row in calibration.provenance_rows()} == expected_names


def test_unsupported_parameters_are_not_silently_presented_as_fitted():
    calibration = derive_calibrated_parameters()

    assert calibration.fitness_observation_count == 34
    assert calibration.missing_fitness_observation_count == 0
    assert calibration.decay_observation_count == 0
    assert calibration.estimates["beta_interference"].provenance == PROVENANCE_FITTED
    assert calibration.estimates["gamma_decay"].provenance == PROVENANCE_UNSUPPORTED
    assert "non-negative fitness observations" in calibration.estimates["beta_interference"].notes
    assert "requires exact decay observations" in calibration.estimates["gamma_decay"].notes


def test_calibrated_thresholds_are_sensitive_to_observed_mutation_axis():
    observations = load_calibration_dataset()
    narrow_observations = [
        {
            **row,
            "mutation_rate_multiplier": min(row["mutation_rate_multiplier"], 10.0),
            "mutation_rate_multiplier_lower": min(row["mutation_rate_multiplier_lower"], 10.0),
            "mutation_rate_multiplier_upper": min(row["mutation_rate_multiplier_upper"], 10.0),
        }
        for row in observations
    ]

    full = evaluate_model(derive_calibrated_parameters(observations).params)
    narrow = evaluate_model(derive_calibrated_parameters(narrow_observations).params)

    assert full.m_values[-1] == pytest.approx(168.16)
    assert narrow.m_values[-1] == pytest.approx(10.0)
    assert full.range_estimate.mu_max != narrow.range_estimate.mu_max


def test_available_strains_and_generations_support_ui_selectors():
    observations = load_calibration_dataset()

    assert available_strains(observations) == ["MRS", "MRM", "MRL", "MRXL"]
    assert available_generations(observations, "MRXL") == [0, 3000]


def test_selected_strain_and_generation_drive_calibrated_axis():
    observations = load_calibration_dataset()
    mrs = derive_calibrated_parameters(observations, strain="MRS", target_generation=3000)
    mrxl = derive_calibrated_parameters(observations, strain="MRXL", target_generation=3000)

    assert mrs.selected_strain == "MRS"
    assert mrs.closest_generation == 3000
    assert mrs.params.m_max == pytest.approx(16.92)
    assert mrxl.params.m_max == pytest.approx(75.04)
    assert evaluate_model(mrs.params).range_estimate.mu_max != evaluate_model(mrxl.params).range_estimate.mu_max


def test_negative_relative_fitness_rows_are_raw_data_not_benefit_fit_inputs():
    observations = load_calibration_dataset()
    calibration = derive_calibrated_parameters(observations, strain="MRXL", target_generation=3000)

    assert calibration.fitness_observation_count == 8
    assert calibration.estimates["benefit_scale"].provenance == PROVENANCE_FITTED
    assert "Excluded 3 negative relative-fitness row(s)" in calibration.estimates["benefit_scale"].notes


def test_exact_fitness_rows_fit_benefit_parameters_when_curated():
    observations = load_calibration_dataset()
    enriched = []
    fitness_values = [0.04, 0.02, 0.025, 0.05, 0.01, 0.03]
    fitness_index = 0
    for row in observations:
        if (
            row["strain_or_population"] == "MRS"
            and row["generation"] == 3000
            and row["measurement_kind"] == "relative_fitness"
        ):
            value = fitness_values[fitness_index]
            fitness_index += 1
            enriched.append(
                {
                    **row,
                    "measurement_value": value,
                    "measurement_lower": max(value - 0.005, 0.0),
                    "measurement_upper": value + 0.005,
                    "uncertainty_type": "interval",
                    "fitness_control": "MRS ancestor",
                    "fitness_control_description": "Synthetic exact-row test control.",
                }
            )
        else:
            enriched.append(row)

    calibration = derive_calibrated_parameters(enriched, strain="MRS", target_generation=3000)

    assert calibration.fitness_observation_count == 6
    assert calibration.missing_fitness_observation_count == 0
    assert calibration.estimates["beta_interference"].provenance == PROVENANCE_FITTED
    assert calibration.estimates["benefit_scale"].provenance == PROVENANCE_FITTED
