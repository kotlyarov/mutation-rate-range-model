import csv
import json

import pytest

from mrrm.data_loaders import (
    CALIBRATION_FIELDS,
    DataValidationError,
    build_calibration_inventory,
    build_data_inventory,
    load_calibration_dataset,
    load_processed_observations,
    load_source_registry,
)


def test_source_registry_loads_registered_sources():
    sources = load_source_registry()

    assert len(sources) == 4
    assert {source["source_id"] for source in sources} == {
        "barrick_ltee_ecoli",
        "sprouffske_2018",
        "couce_2017",
        "maddamsetti_2020",
    }


def test_processed_observations_load_with_typed_optional_numbers():
    observations = load_processed_observations()
    sprouffske = next(
        observation
        for observation in observations
        if observation["source_id"] == "sprouffske_2018"
    )

    assert len(observations) == 4
    assert sprouffske["generation"] == 3000
    assert sprouffske["mutation_rate_multiplier"] == 100.0
    assert sprouffske["relative_fitness"] is None
    assert sprouffske["calibration_role"] == "schema_example_only"


def test_data_inventory_summarizes_sources_and_observations():
    inventory = build_data_inventory()

    assert inventory["source_count"] == 4
    assert inventory["observation_count"] == 4
    assert inventory["calibration_roles"] == {"schema_example_only": 4}
    assert inventory["numeric_field_counts"]["generation"] == 1


def test_missing_required_observation_column_is_rejected(tmp_path):
    bad_csv = tmp_path / "bad_observations.csv"
    bad_csv.write_text(
        "observation_id,source_id,experiment\n"
        "obs_001,sprouffske_2018,experiment\n",
        encoding="utf-8",
    )

    with pytest.raises(DataValidationError, match="missing required columns"):
        load_processed_observations(bad_csv)


def test_invalid_numeric_observation_value_is_rejected(tmp_path):
    bad_csv = tmp_path / "bad_observations.csv"
    fieldnames = [
        "observation_id",
        "source_id",
        "source_label",
        "experiment",
        "strain_or_population",
        "generation",
        "mutation_rate_multiplier",
        "relative_fitness",
        "mutation_count",
        "genome_decay_proxy",
        "robustness_environment",
        "robustness_score",
        "observation_kind",
        "calibration_role",
        "method_notes",
        "uncertainty_notes",
        "qualitative_summary",
    ]
    with bad_csv.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerow(
            {
                "observation_id": "obs_bad",
                "source_id": "sprouffske_2018",
                "source_label": "Sprouffske et al. 2018",
                "experiment": "Engineered mutation-rate evolution experiment",
                "strain_or_population": "engineered strain",
                "generation": "-1",
                "mutation_rate_multiplier": "100",
                "relative_fitness": "",
                "mutation_count": "",
                "genome_decay_proxy": "",
                "robustness_environment": "",
                "robustness_score": "",
                "observation_kind": "qualitative_summary",
                "calibration_role": "schema_example_only",
                "method_notes": "",
                "uncertainty_notes": "",
                "qualitative_summary": "Invalid generation should be caught.",
            }
        )

    with pytest.raises(DataValidationError, match="generation must be a non-negative integer"):
        load_processed_observations(bad_csv)


def test_invalid_source_registry_is_rejected(tmp_path):
    bad_registry = tmp_path / "bad_registry.json"
    bad_registry.write_text(json.dumps({"sources": [{"source_id": "missing_fields"}]}), encoding="utf-8")

    with pytest.raises(DataValidationError, match="missing required field"):
        load_source_registry(bad_registry)


def test_calibration_dataset_v0_loads_real_sprouffske_values():
    observations = load_calibration_dataset()
    ancestor = next(
        row
        for row in observations
        if row["observation_id"] == "sprouffske_2018_s3_mrs_ancestor_U"
    )
    mrxl = next(
        row
        for row in observations
        if row["observation_id"] == "sprouffske_2018_s3_mrxl_ancestor_U"
    )

    assert len(observations) == 68
    assert ancestor["measurement_value"] == 0.00034
    assert ancestor["measurement_lower"] == 0.00025
    assert ancestor["measurement_upper"] == 0.00045
    assert ancestor["mutation_rate_multiplier"] == 1.0
    assert mrxl["measurement_value"] == 0.03596
    assert mrxl["mutation_rate_multiplier"] > 100
    assert sum(row["uncertainty_type"] == "interval" for row in observations) == 34
    assert sum(row["uncertainty_type"] == "missing" for row in observations) == 34
    assert all(row["calibration_role"] == "raw_observation_not_fit" for row in observations)


def test_calibration_inventory_is_data_first_not_fit():
    inventory = build_calibration_inventory()

    assert inventory["dataset_version"] == "calibration_dataset_v0"
    assert inventory["observation_count"] == 68
    assert inventory["fitness_observation_count"] == 0
    assert inventory["missing_fitness_observation_count"] == 34
    assert inventory["measurement_kinds"] == {
        "genomic_mutation_rate_U": 34,
        "relative_fitness": 34,
    }
    assert inventory["calibration_roles"] == {"raw_observation_not_fit": 68}


def test_calibration_interval_rows_require_interval_bounds(tmp_path):
    row = _calibration_row()
    row["measurement_lower"] = ""
    bad_csv = _write_calibration_rows(tmp_path, [row])

    with pytest.raises(DataValidationError, match="interval observations require"):
        load_calibration_dataset(bad_csv)


def test_calibration_fitness_values_require_named_control(tmp_path):
    row = _calibration_row()
    row["measurement_kind"] = "relative_fitness"
    row["measurement_value"] = "0.12"
    row["measurement_lower"] = "0.1"
    row["measurement_upper"] = "0.14"
    row["measurement_units"] = "growth-rate difference"
    row["fitness_control"] = ""
    row["fitness_control_description"] = ""
    bad_csv = _write_calibration_rows(tmp_path, [row])

    with pytest.raises(DataValidationError, match="every fitness value must name its control"):
        load_calibration_dataset(bad_csv)


def _calibration_row():
    return {
        "observation_id": "test_observation",
        "source_id": "sprouffske_2018",
        "dataset_version": "calibration_dataset_v0",
        "source_table": "S3 Table. Genomic mutation rates.",
        "experiment": "Engineered mutation-rate evolution experiment",
        "strain_or_population": "MRS",
        "replicate": "Ancestor",
        "generation": "0",
        "environment": "DM1000 original selected environment",
        "measurement_kind": "genomic_mutation_rate_U",
        "measurement_value": "0.00034",
        "measurement_lower": "0.00025",
        "measurement_upper": "0.00045",
        "uncertainty_type": "interval",
        "uncertainty_level": "95% confidence interval",
        "measurement_units": "mutations per genome per cell generation",
        "mutation_rate_multiplier": "1",
        "mutation_rate_multiplier_lower": "1",
        "mutation_rate_multiplier_upper": "1",
        "mutation_rate_multiplier_uncertainty_type": "control_definition",
        "fitness_control": "",
        "fitness_control_description": "",
        "raw_source_file": "data/raw/sprouffske_2018/s3_genomic_mutation_rates.xlsx",
        "method_notes": "Test row.",
        "curation_notes": "No fitness value is encoded in this row.",
        "calibration_role": "raw_observation_not_fit",
    }


def _write_calibration_rows(tmp_path, rows):
    path = tmp_path / "calibration_dataset.csv"
    with path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=CALIBRATION_FIELDS)
        writer.writeheader()
        writer.writerows(rows)
    return path
