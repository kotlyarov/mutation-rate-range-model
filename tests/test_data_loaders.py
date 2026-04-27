import csv
import json

import pytest

from mrrm.data_loaders import (
    DataValidationError,
    build_data_inventory,
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

    with pytest.raises(DataValidationError, match="missing required observation columns"):
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
