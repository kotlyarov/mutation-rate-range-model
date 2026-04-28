# Experimental Data Inventory

This report documents the first experimental-data scaffold for the Mutation Rate Range Model.

## Status

The current files are data curation scaffolds. `calibration_dataset_v0` now provides raw experimental inputs for calibration, but the deterministic model equations are unchanged and model outputs remain assumption-dependent.

calibration_dataset_v0 currently contains real Sprouffske et al. 2018 mutation-rate values and confidence intervals, plus curated Dryad growth-curve relative-fitness observations for the existing strain/replicate/final-generation calibration slots. Every fitness value names its same-batch ancestor control. The dataset still does not contain mutation-count/genome-decay costs or robustness observations, so decay and robustness conclusions remain unsupported.

The curated relative-fitness values are computed from Dryad `growth-curves.txt` as `r_evo - r_anc`, following the paper methods. The raw Dryad final timepoint is generation `2907`; the paper labels this final timepoint as approximately `3000` generations, and the processed rows preserve that context in curation notes.

## Files

- `data/source_registry.json`: registered source metadata for candidate experimental data sources.
- `data/processed/example_observations.csv`: schema example for curated processed observations.
- `data/raw/sprouffske_2018/s3_genomic_mutation_rates.xlsx`: raw PLOS Genetics supplementary S3 table for Sprouffske et al. 2018.
- `data/raw/sprouffske_2018/phenotyping_data.tar.gz`: original Dryad phenotyping archive for Sprouffske et al. 2018.
- `data/raw/sprouffske_2018/phenotyping_data/growth-curves.txt`: extracted raw Dryad growth-curve table used for relative-fitness curation.
- `data/processed/calibration_dataset_v0.csv`: first real-value processed calibration dataset with mutation-rate and relative-fitness observations.
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

`calibration_dataset_v0.csv` starts with Sprouffske et al. 2018 supplementary S3 genomic mutation-rate values and Dryad growth-curve relative-fitness rows for the same strain/replicate/final-generation slots.

Included:

- 34 genomic mutation-rate observations.
- 34 relative-fitness observations.
- `U` values in mutations per genome per cell generation.
- 95% confidence intervals from the source table.
- derived mutation-rate multiplier intervals relative to the `MRS` ancestor `U` row.
- fitness values computed as `r_evo - r_anc`, where `r_anc` is the mean of three same-strain ancestor growth-rate estimates in the same growth-curve batch.
- observed fitness distributions across three matched growth-curve batches for evolved rows; lower/upper values are observed min/max, not confidence intervals.
- generation `0` for ancestor rows and generation `3000` for evolved replicate rows, following the S3 table description.

Not included:

- robustness values.
- genome-sequencing mutation counts.
- decay/genome-integrity costs.
- fitted scientific conclusions.

No figure values were digitized. Fitness observations were curated from the original Dryad phenotyping archive. The raw Dryad final growth-curve generation is `2907`; rows are stored in the existing final-generation slot aligned with the paper's approximately `3000` generation label and the S3 mutation-rate rows.

In calibrated mode, `calibration_dataset_v0` supplies empirical values for the evaluated mutation-rate range and selected relative-fitness response by strain and closest experimental generation. Negative relative-fitness observations remain visible as raw data. The current non-negative benefit curve is fit only to non-negative selected fitness observations; decay, robustness, and utility-weight parameters remain assumed or unsupported until exact cost or robustness observations are added.

## Validation Checks

The loader currently checks:

- source-registry required fields
- duplicate source and observation identifiers
- required observation columns
- required observation values
- unknown source references
- non-finite or invalid numeric values
- non-negative generation, mutation-count, and decay-proxy values
- finite relative-fitness values, including negative values where observed
- positive mutation-rate multipliers
- robustness scores bounded between 0 and 1
- calibration role labels that avoid implying fitted model input
- calibration-dataset interval completeness
- calibration-dataset fitness values naming their controls

## Next Data Steps

Future work should download raw datasets into `data/raw/`, keep them immutable, and generate processed files reproducibly with scripts or notebooks. Model calibration should continue to separate raw observations, fitted parameters, and unsupported assumptions.

Next required dataset work: add the full Sprouffske growth-curve trajectory rows for intermediate generations, then add mutation-count/genome-decay and robustness observations where exact source values are available.
