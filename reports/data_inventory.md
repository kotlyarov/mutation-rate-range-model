# Experimental Data Inventory

This report documents the first experimental-data scaffold for the Mutation Rate Range Model.

## Status

The current files are example/schema data only. They are not calibrated model input, and the deterministic model equations are unchanged.

## Files

- `data/source_registry.json`: registered source metadata for candidate experimental data sources.
- `data/processed/example_observations.csv`: schema example for curated processed observations.
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

## Next Data Steps

Future work should download raw datasets into `data/raw/`, keep them immutable, and generate processed files reproducibly with scripts or notebooks. Model calibration should wait until source-specific preprocessing, uncertainty handling, and validation reports exist.
