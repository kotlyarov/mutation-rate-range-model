# Experimental Data Inventory

This report documents the first experimental-data scaffold for the Mutation Rate Range Model.

## Status

The current files are example/schema data only. They are not calibrated model input, and the deterministic model equations are unchanged.

calibration_dataset_v0 currently contains real Sprouffske et al. 2018 mutation-rate values and confidence intervals, plus explicit missing-value slots for strain/replicate/generation fitness rows. It does not yet contain exact fitness-vs-control values, mutation-count/genome-decay costs, or fitted benefit/decay curves. Therefore it anchors the mutation-rate axis and prepares the fitness-calibration path, but does not yet answer the main biological question.

Next required dataset work: extract exact fitness-vs-control values from Sprouffske et al. 2018 or its Dryad files if available. If exact numeric values are unavailable, record the value as missing and document whether figure digitisation would be required.

## Files

- `data/source_registry.json`: registered source metadata for candidate experimental data sources.
- `data/processed/example_observations.csv`: schema example for curated processed observations.
- `data/raw/sprouffske_2018/s3_genomic_mutation_rates.xlsx`: raw PLOS Genetics supplementary S3 table for Sprouffske et al. 2018.
- `data/processed/calibration_dataset_v0.csv`: first real-value processed calibration dataset, currently mutation-rate observations only.
- `src/mrrm/data_loaders.py`: low-level loading, normalization, and validation helpers.
- `tests/test_data_loaders.py`: validation and loader tests.

## Registered Sources

- `barrick_ltee_ecoli`: Barrick lab LTEE-Ecoli public genomics resources.
- `sprouffske_2018`: engineered E. coli mutation-rate experiment with selected-environment growth, alternative-environment robustness assays, and sequencing.
- `couce_2017`: LTEE mutator genome-decay analysis motivating separation of selected-environment fitness from genome-integrity proxies.
- `maddamsetti_2020`: LTEE metagenomic analysis of mutation-rate and mutation-bias divergence.

## Processed Observation Schema

Each processed observation keeps source context and uses nullable numeric fields:

- source and experiment identifiers
- strain or population label
- generation
- mutation-rate multiplier
- relative fitness
- mutation count
- genome-decay proxy
- robustness or environment information
- uncertainty and method notes

Blank numeric fields mean the value has not been curated. Qualitative rows must not be treated as fitted model inputs.

## Calibration Dataset v0

`calibration_dataset_v0.csv` starts with Sprouffske et al. 2018 supplementary S3 genomic mutation-rate values and missing fitness/growth input rows for the same strain/replicate/generation slots.

Included:

- 34 genomic mutation-rate observations.
- 34 explicit missing fitness/growth observations.
- `U` values in mutations per genome per cell generation.
- 95% confidence intervals from the source table.
- derived mutation-rate multiplier intervals relative to the `MRS` ancestor `U` row.
- generation `0` for ancestor rows and generation `3000` for evolved replicate rows, following the S3 table description.

Not included:

- exact fitness values.
- robustness values.
- genome-sequencing mutation counts.
- fitted model parameters.

No figure values were digitized. Missing fitness data are left absent rather than guessed.

In calibrated mode, `calibration_dataset_v0` currently supplies empirical values for the evaluated mutation-rate range by selected strain and closest experimental generation. The generation horizon control selects the nearest available experimental generation. The dataset does not yet supply exact fitted benefit, interference, decay, robustness, or utility-weight parameters. Those inputs are therefore displayed as assumed or unsupported exploratory fallbacks in the app provenance table until exact fitness or cost observations are added.

## Validation Checks

The loader currently checks:

- source-registry required fields
- duplicate source and observation identifiers
- required observation columns
- required observation values
- unknown source references
- non-finite or invalid numeric values
- non-negative generation, mutation-count, fitness, and decay-proxy values
- positive mutation-rate multipliers
- robustness scores bounded between 0 and 1
- calibration role labels that avoid implying fitted model input
- calibration-dataset interval completeness
- calibration-dataset fitness values naming their controls

## Next Data Steps

Future work should download raw datasets into `data/raw/`, keep them immutable, and generate processed files reproducibly with scripts or notebooks. Model calibration should wait until source-specific preprocessing, uncertainty handling, and validation reports exist.

Next required dataset work: extract exact fitness-vs-control values from Sprouffske et al. 2018 or its Dryad files if available. If exact numeric values are unavailable, record the value as missing and document whether figure digitisation would be required.
