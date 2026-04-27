# Data Directory

This directory is for empirical data used by the Mutation Rate Range Model.

## Current status

The repository includes a small source registry and an example processed
observation file for schema validation. It also includes
`calibration_dataset_v0.csv`, a first real-value processed dataset seeded from
Sprouffske et al. 2018 supplementary S3 genomic mutation-rate values.

These files are not calibrated model inputs. The deterministic model should
continue to work without treating empirical observations as fitted parameters.

## Directory structure

```text
data/
  source_registry.json
  raw/
    sprouffske_2018/
      s3_genomic_mutation_rates.xlsx
  processed/
    example_observations.csv
    calibration_dataset_v0.csv
  external/
  README.md
```

## `raw/`

Original downloaded data files.

Do not manually edit these files.

## `processed/`

Generated cleaned data files.

Every file in this directory should be reproducible from scripts or notebooks.

The current `example_observations.csv` file is schema/example data only. It
preserves source context and validates field conventions, but it should not be
used to make model conclusions.

The current `calibration_dataset_v0.csv` file contains raw or directly derived
experimental observations only. It starts with Sprouffske et al. 2018 S3
genomic mutation-rate values. Fitness values are not included in v0 because the
exact raw fitness table has not yet been curated. Any future fitness row must
name its control.

## `external/`

Small reference files or metadata tables.

## Required metadata

For every dataset, document:

```text
source_name
source_url
access_date
license_or_terms
download_method
raw_filename
processing_script
notes
```

## Rule

Do not present exploratory model defaults as fitted values unless the fitting process and data sources are documented.
