from dataclasses import fields

import pytest

from mrrm.calibration import (
    PROVENANCE_EMPIRICAL,
    PROVENANCE_UNSUPPORTED,
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

    assert calibration.fitness_observation_count == 0
    assert calibration.decay_observation_count == 0
    assert calibration.estimates["beta_interference"].provenance == PROVENANCE_UNSUPPORTED
    assert calibration.estimates["gamma_decay"].provenance == PROVENANCE_UNSUPPORTED
    assert "requires exact fitness observations" in calibration.estimates["beta_interference"].notes


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
