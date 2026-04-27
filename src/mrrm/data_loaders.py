"""Loading and validation helpers for curated experimental observations."""

from __future__ import annotations

import csv
import json
import math
from collections import Counter
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_SOURCE_REGISTRY_PATH = PROJECT_ROOT / "data" / "source_registry.json"
DEFAULT_OBSERVATIONS_PATH = PROJECT_ROOT / "data" / "processed" / "example_observations.csv"
DEFAULT_CALIBRATION_DATASET_PATH = (
    PROJECT_ROOT / "data" / "processed" / "calibration_dataset_v0.csv"
)

REQUIRED_SOURCE_FIELDS = (
    "source_id",
    "source_name",
    "source_url",
    "source_type",
    "citation",
    "license_or_terms",
    "download_method",
    "notes",
)

OBSERVATION_FIELDS = (
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
)

REQUIRED_OBSERVATION_VALUES = (
    "observation_id",
    "source_id",
    "source_label",
    "experiment",
    "strain_or_population",
    "observation_kind",
    "calibration_role",
)

OPTIONAL_NUMERIC_FIELDS = {
    "generation": "nonnegative_integer",
    "mutation_rate_multiplier": "positive_float",
    "relative_fitness": "nonnegative_float",
    "mutation_count": "nonnegative_integer",
    "genome_decay_proxy": "nonnegative_float",
    "robustness_score": "unit_interval",
}

ALLOWED_CALIBRATION_ROLES = {"schema_example_only", "candidate_not_calibrated"}
BLANK_VALUES = {"", "na", "n/a", "none", "null", "unknown"}

CALIBRATION_FIELDS = (
    "observation_id",
    "source_id",
    "dataset_version",
    "source_table",
    "experiment",
    "strain_or_population",
    "replicate",
    "generation",
    "environment",
    "measurement_kind",
    "measurement_value",
    "measurement_lower",
    "measurement_upper",
    "uncertainty_type",
    "uncertainty_level",
    "measurement_units",
    "mutation_rate_multiplier",
    "mutation_rate_multiplier_lower",
    "mutation_rate_multiplier_upper",
    "mutation_rate_multiplier_uncertainty_type",
    "fitness_control",
    "fitness_control_description",
    "raw_source_file",
    "method_notes",
    "curation_notes",
    "calibration_role",
)

REQUIRED_CALIBRATION_VALUES = (
    "observation_id",
    "source_id",
    "dataset_version",
    "source_table",
    "experiment",
    "strain_or_population",
    "generation",
    "measurement_kind",
    "uncertainty_type",
    "measurement_units",
    "raw_source_file",
    "calibration_role",
)

CALIBRATION_NUMERIC_FIELDS = {
    "generation": "nonnegative_integer",
    "measurement_value": "nonnegative_float",
    "measurement_lower": "nonnegative_float",
    "measurement_upper": "nonnegative_float",
    "mutation_rate_multiplier": "positive_float",
    "mutation_rate_multiplier_lower": "positive_float",
    "mutation_rate_multiplier_upper": "positive_float",
}

CALIBRATION_UNCERTAINTY_TYPES = {"missing", "interval", "distribution"}
MULTIPLIER_UNCERTAINTY_TYPES = {
    "control_definition",
    "derived_interval_from_95ci",
    "interval",
    "missing",
    "distribution",
}
CALIBRATION_ROLES = {"raw_observation_not_fit"}


class DataValidationError(ValueError):
    """Raised when a source registry or observation file is invalid."""


def load_source_registry(path: str | Path | None = None) -> list[dict[str, str]]:
    """Load and validate the experimental source registry."""

    registry_path = Path(path) if path is not None else DEFAULT_SOURCE_REGISTRY_PATH
    with registry_path.open(encoding="utf-8") as file:
        payload = json.load(file)

    sources = payload.get("sources")
    if not isinstance(sources, list):
        raise DataValidationError("Source registry must contain a 'sources' list.")

    normalized_sources = [_normalize_source(source, registry_path) for source in sources]
    _validate_unique_ids(normalized_sources, "source_id", "source registry")
    return normalized_sources


def load_processed_observations(
    path: str | Path | None = None,
    source_registry_path: str | Path | None = None,
) -> list[dict[str, Any]]:
    """Load validated processed observations.

    These observations are schema examples and candidate records only. They are
    not used to calibrate model parameters.
    """

    observation_path = Path(path) if path is not None else DEFAULT_OBSERVATIONS_PATH
    sources = load_source_registry(source_registry_path)
    known_source_ids = {source["source_id"] for source in sources}

    with observation_path.open(newline="", encoding="utf-8") as file:
        reader = csv.DictReader(file)
        _validate_observation_header(reader.fieldnames, observation_path)
        rows = [
            _normalize_observation(row, known_source_ids, observation_path, line_number)
            for line_number, row in enumerate(reader, start=2)
        ]

    _validate_unique_ids(rows, "observation_id", "processed observations")
    return rows


def build_data_inventory(
    source_registry_path: str | Path | None = None,
    observations_path: str | Path | None = None,
) -> dict[str, Any]:
    """Summarize registered sources and processed observation records."""

    sources = load_source_registry(source_registry_path)
    observations = load_processed_observations(observations_path, source_registry_path)

    numeric_counts = {
        field: sum(observation[field] is not None for observation in observations)
        for field in OPTIONAL_NUMERIC_FIELDS
    }
    return {
        "source_count": len(sources),
        "observation_count": len(observations),
        "source_types": dict(Counter(source["source_type"] for source in sources)),
        "observation_kinds": dict(
            Counter(observation["observation_kind"] for observation in observations)
        ),
        "calibration_roles": dict(
            Counter(observation["calibration_role"] for observation in observations)
        ),
        "sources_referenced_by_observations": sorted(
            {observation["source_id"] for observation in observations}
        ),
        "numeric_field_counts": numeric_counts,
    }


def load_calibration_dataset(
    path: str | Path | None = None,
    source_registry_path: str | Path | None = None,
) -> list[dict[str, Any]]:
    """Load validated raw observations for future calibration work.

    The v0 dataset is deliberately data-first. Rows are raw or directly derived
    experimental observations and are not fitted to the deterministic model.
    """

    dataset_path = Path(path) if path is not None else DEFAULT_CALIBRATION_DATASET_PATH
    sources = load_source_registry(source_registry_path)
    known_source_ids = {source["source_id"] for source in sources}

    with dataset_path.open(newline="", encoding="utf-8") as file:
        reader = csv.DictReader(file)
        _validate_required_header(reader.fieldnames, CALIBRATION_FIELDS, dataset_path)
        rows = [
            _normalize_calibration_row(row, known_source_ids, dataset_path, line_number)
            for line_number, row in enumerate(reader, start=2)
        ]

    _validate_unique_ids(rows, "observation_id", "calibration dataset")
    return rows


def build_calibration_inventory(
    path: str | Path | None = None,
    source_registry_path: str | Path | None = None,
) -> dict[str, Any]:
    """Summarize calibration-dataset observations without fitting a model."""

    observations = load_calibration_dataset(path, source_registry_path)
    return {
        "dataset_version": "calibration_dataset_v0",
        "observation_count": len(observations),
        "sources": sorted({observation["source_id"] for observation in observations}),
        "measurement_kinds": dict(
            Counter(observation["measurement_kind"] for observation in observations)
        ),
        "strain_or_population": dict(
            Counter(observation["strain_or_population"] for observation in observations)
        ),
        "calibration_roles": dict(
            Counter(observation["calibration_role"] for observation in observations)
        ),
        "fitness_observation_count": sum(
            "fitness" in observation["measurement_kind"]
            and observation["measurement_value"] is not None
            for observation in observations
        ),
    }


def _normalize_source(source: Any, path: Path) -> dict[str, str]:
    if not isinstance(source, dict):
        raise DataValidationError(f"Every source in {path} must be an object.")

    normalized = {field: _clean_text(source.get(field)) for field in source}
    for field in REQUIRED_SOURCE_FIELDS:
        if _is_blank(normalized.get(field)):
            raise DataValidationError(f"Source registry entry is missing required field: {field}.")
    return normalized


def _validate_observation_header(fieldnames: list[str] | None, path: Path) -> None:
    _validate_required_header(fieldnames, OBSERVATION_FIELDS, path)


def _validate_required_header(
    fieldnames: list[str] | None,
    required_fields: tuple[str, ...],
    path: Path,
) -> None:
    if fieldnames is None:
        raise DataValidationError(f"{path} is empty or missing a CSV header.")

    missing = [field for field in required_fields if field not in fieldnames]
    if missing:
        joined = ", ".join(missing)
        raise DataValidationError(f"{path} is missing required columns: {joined}.")


def _normalize_observation(
    row: dict[str, str],
    known_source_ids: set[str],
    path: Path,
    line_number: int,
) -> dict[str, Any]:
    normalized: dict[str, Any] = {
        field: _clean_text(row.get(field))
        for field in OBSERVATION_FIELDS
    }

    for field in REQUIRED_OBSERVATION_VALUES:
        if _is_blank(normalized[field]):
            raise DataValidationError(
                f"{path}:{line_number} is missing required observation field: {field}."
            )

    source_id = normalized["source_id"]
    if source_id not in known_source_ids:
        raise DataValidationError(f"{path}:{line_number} references unknown source_id: {source_id}.")

    calibration_role = normalized["calibration_role"]
    if calibration_role not in ALLOWED_CALIBRATION_ROLES:
        allowed = ", ".join(sorted(ALLOWED_CALIBRATION_ROLES))
        raise DataValidationError(
            f"{path}:{line_number} has invalid calibration_role {calibration_role!r}; "
            f"expected one of: {allowed}."
        )

    for field, rule in OPTIONAL_NUMERIC_FIELDS.items():
        normalized[field] = _parse_optional_number(normalized[field], field, rule, path, line_number)

    return normalized


def _parse_optional_number(
    value: str,
    field: str,
    rule: str,
    path: Path,
    line_number: int,
) -> float | int | None:
    if _is_blank(value):
        return None

    try:
        parsed = float(value)
    except ValueError as exc:
        raise DataValidationError(
            f"{path}:{line_number} has invalid numeric value for {field}: {value!r}."
        ) from exc

    if not math.isfinite(parsed):
        raise DataValidationError(
            f"{path}:{line_number} has non-finite numeric value for {field}: {value!r}."
        )

    if rule == "positive_float":
        if parsed <= 0:
            raise DataValidationError(f"{path}:{line_number} {field} must be positive.")
        return parsed
    if rule == "nonnegative_float":
        if parsed < 0:
            raise DataValidationError(f"{path}:{line_number} {field} must be non-negative.")
        return parsed
    if rule == "unit_interval":
        if parsed < 0 or parsed > 1:
            raise DataValidationError(f"{path}:{line_number} {field} must be between 0 and 1.")
        return parsed
    if rule == "nonnegative_integer":
        if parsed < 0 or not parsed.is_integer():
            raise DataValidationError(
                f"{path}:{line_number} {field} must be a non-negative integer."
            )
        return int(parsed)

    raise DataValidationError(f"Unknown numeric validation rule for {field}: {rule}.")


def _normalize_calibration_row(
    row: dict[str, str],
    known_source_ids: set[str],
    path: Path,
    line_number: int,
) -> dict[str, Any]:
    normalized: dict[str, Any] = {
        field: _clean_text(row.get(field))
        for field in CALIBRATION_FIELDS
    }

    for field in REQUIRED_CALIBRATION_VALUES:
        if _is_blank(normalized[field]):
            raise DataValidationError(
                f"{path}:{line_number} is missing required calibration field: {field}."
            )

    source_id = normalized["source_id"]
    if source_id not in known_source_ids:
        raise DataValidationError(f"{path}:{line_number} references unknown source_id: {source_id}.")

    calibration_role = normalized["calibration_role"]
    if calibration_role not in CALIBRATION_ROLES:
        allowed = ", ".join(sorted(CALIBRATION_ROLES))
        raise DataValidationError(
            f"{path}:{line_number} has invalid calibration_role {calibration_role!r}; "
            f"expected one of: {allowed}."
        )

    uncertainty_type = normalized["uncertainty_type"]
    if uncertainty_type not in CALIBRATION_UNCERTAINTY_TYPES:
        allowed = ", ".join(sorted(CALIBRATION_UNCERTAINTY_TYPES))
        raise DataValidationError(
            f"{path}:{line_number} has invalid uncertainty_type {uncertainty_type!r}; "
            f"expected one of: {allowed}."
        )

    multiplier_uncertainty_type = normalized["mutation_rate_multiplier_uncertainty_type"]
    if not _is_blank(multiplier_uncertainty_type) and (
        multiplier_uncertainty_type not in MULTIPLIER_UNCERTAINTY_TYPES
    ):
        allowed = ", ".join(sorted(MULTIPLIER_UNCERTAINTY_TYPES))
        raise DataValidationError(
            f"{path}:{line_number} has invalid mutation_rate_multiplier_uncertainty_type "
            f"{multiplier_uncertainty_type!r}; expected one of: {allowed}."
        )

    for field, rule in CALIBRATION_NUMERIC_FIELDS.items():
        normalized[field] = _parse_optional_number(normalized[field], field, rule, path, line_number)

    _validate_uncertainty_representation(normalized, path, line_number)
    _validate_interval(
        normalized,
        "measurement_value",
        "measurement_lower",
        "measurement_upper",
        path,
        line_number,
    )
    _validate_interval(
        normalized,
        "mutation_rate_multiplier",
        "mutation_rate_multiplier_lower",
        "mutation_rate_multiplier_upper",
        path,
        line_number,
    )
    _validate_fitness_control(normalized, path, line_number)
    return normalized


def _validate_uncertainty_representation(
    row: dict[str, Any],
    path: Path,
    line_number: int,
) -> None:
    value_fields = ("measurement_value", "measurement_lower", "measurement_upper")
    if row["uncertainty_type"] == "missing":
        if any(row[field] is not None for field in value_fields):
            raise DataValidationError(
                f"{path}:{line_number} missing observations must not include numeric values."
            )
        return
    if row["uncertainty_type"] == "interval":
        if any(row[field] is None for field in value_fields):
            raise DataValidationError(
                f"{path}:{line_number} interval observations require value, lower, and upper."
            )
        return
    if row["uncertainty_type"] == "distribution":
        if not _is_blank(row["curation_notes"]):
            return
        raise DataValidationError(
            f"{path}:{line_number} distribution observations require distribution notes."
        )


def _validate_interval(
    row: dict[str, Any],
    value_field: str,
    lower_field: str,
    upper_field: str,
    path: Path,
    line_number: int,
) -> None:
    value = row[value_field]
    lower = row[lower_field]
    upper = row[upper_field]
    if value is None and lower is None and upper is None:
        return
    if value is None or lower is None or upper is None:
        raise DataValidationError(
            f"{path}:{line_number} {value_field} interval fields must be all present or all blank."
        )
    if lower > upper:
        raise DataValidationError(f"{path}:{line_number} {lower_field} must be <= {upper_field}.")
    if value < lower or value > upper:
        raise DataValidationError(
            f"{path}:{line_number} {value_field} must lie within its interval."
        )


def _validate_fitness_control(row: dict[str, Any], path: Path, line_number: int) -> None:
    if "fitness" not in row["measurement_kind"] or row["measurement_value"] is None:
        return
    if _is_blank(row["fitness_control"]):
        raise DataValidationError(
            f"{path}:{line_number} every fitness value must name its control."
        )


def _validate_unique_ids(rows: list[dict[str, Any]], id_field: str, label: str) -> None:
    ids = [row[id_field] for row in rows]
    duplicates = sorted(identifier for identifier, count in Counter(ids).items() if count > 1)
    if duplicates:
        joined = ", ".join(duplicates)
        raise DataValidationError(f"Duplicate {id_field} values in {label}: {joined}.")


def _clean_text(value: Any) -> str:
    if value is None:
        return ""
    return str(value).strip()


def _is_blank(value: Any) -> bool:
    if value is None:
        return True
    return str(value).strip().lower() in BLANK_VALUES
