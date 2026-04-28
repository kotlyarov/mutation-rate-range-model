import math

import pytest

from mrrm.audit import build_calibration_audit
from mrrm.data_loaders import load_calibration_dataset


def test_calibration_audit_separates_selected_and_all_strain_fits():
    observations = load_calibration_dataset()
    audit = build_calibration_audit(
        observations,
        selected_strain="MRS",
        target_generation=3000,
    )

    selected = audit.selected_strain_fit
    all_strains = audit.all_strain_fit

    assert selected.label == "selected strain: MRS"
    assert len(selected.observed_rows) == 6
    assert len(selected.fit_rows) == 5
    assert len(selected.excluded_rows) == 1
    assert all(row["measurement_value"] >= 0 for row in selected.fit_rows)
    assert selected.objective["n_rows"] == 5
    assert selected.objective["sse"] >= 0

    assert all_strains.label == "all strains"
    assert len(all_strains.observed_rows) == 30
    assert len(all_strains.fit_rows) == 25
    assert len(all_strains.excluded_rows) == 5
    assert {row["strain"] for row in all_strains.predictions} == {"MRS", "MRM", "MRL", "MRXL"}


def test_calibration_audit_reports_prediction_residuals():
    observations = load_calibration_dataset()
    audit = build_calibration_audit(observations, selected_strain="MRXL", target_generation=3000)

    prediction = next(
        row
        for row in audit.selected_strain_fit.predictions
        if row["observation_id"] == "sprouffske_2018_growth_mrxl_rep2_relative_fitness"
    )

    assert prediction["observed_relative_fitness"] < 0
    assert prediction["used_for_fit"] is False
    assert prediction["residual_observed_minus_predicted"] == pytest.approx(
        prediction["observed_relative_fitness"] - prediction["predicted_benefit"]
    )
    assert prediction["fitness_control"] == "MRXL same-batch ancestor mean r"


def test_leave_one_strain_out_reports_heldout_loss_for_each_strain():
    observations = load_calibration_dataset()
    audit = build_calibration_audit(observations, selected_strain="MRS", target_generation=3000)

    rows = audit.leave_one_strain_out

    assert [row["heldout_strain"] for row in rows] == ["MRS", "MRM", "MRL", "MRXL"]
    assert all(row["training_fit_rows"] > 0 for row in rows)
    assert all(row["heldout_observed_rows"] > 0 for row in rows)
    assert all(math.isfinite(row["heldout_rmse"]) for row in rows)
    assert all(math.isfinite(row["trained_beta_interference"]) for row in rows)
