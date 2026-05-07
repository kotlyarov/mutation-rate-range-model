# Model Lore

This document collects the project-level goal, motivation, current scope, data
scaffold notes, and reporting rule. The detailed formulas live in
[`model_spec.md`](model_spec.md).

## Goal

The goal is not to calculate the exact fitness effect of every possible genomic
change. That is not currently realistic.

The current model asks:

```text
Under these assumptions, what lineage trajectories occur for this mutation
rate?
```

The model should never imply that it has found a true universal optimal
mutation rate.

## Scientific Motivation

Several experimental and theoretical results motivate this project:

- Couce et al. 2017 showed that hypermutable LTEE bacteria can keep gaining
  fitness in the selected environment while their genomes decay.
- Sprouffske et al. 2018 showed that high mutation rates can limit adaptive
  evolution in *E. coli*.
- Good & Desai 2016 developed theory for mutation-rate evolution in rapidly
  adapting asexual populations.
- LTEE datasets provide long-term empirical data for mutation accumulation,
  fitness change, and evolutionary dynamics.
- Maddamsetti et al. 2020 studied mutation-rate and mutation-bias evolution in
  LTEE populations.

The project treats selected-environment fitness and genome integrity as related
but separate concepts. In the current lineage model, beneficial mutation counts
and fitness score describe selected-environment adaptation, while harmful and
lethal mutation counts are simplified burden proxies.

## What This Project Is

This project is:

- a transparent modelling tool
- a local GUI for exploring assumptions
- a reproducible Python codebase
- a place to curate experimental observations
- a way to test sensitivity of conclusions to uncertain parameters

## What This Project Is Not

This project is not:

- a full whole-cell simulation
- a proof of a universal optimal mutation rate
- a model that knows the exact cost of every mutation
- a calibrated biological predictor yet
- a claim that "good" and "bad" mutations are absolute categories
- a replacement for experimental biology

## Current Model Version

The current version is an explicit generational lineage mutation-selection
model. See [`model_spec.md`](model_spec.md) for formulas and event order.

Current default inputs in the Python model are:

```text
seed_fitness = 0.6
seed_population = 1000
population_cap = 10000
generations = 2500
mutation_rate = 0.02
beneficial_mutation_rate = 0.01
harmful_mutation_rate = 0.5
lethal_mutation_rate = 0.1
compound_effect = 0.1
mutation_effect = 0.01
minimum_fitness = 0.4
randomness = 0.1
random_seed = 1
max_runtime_seconds = 600
max_lineage_classes = 100000
```

Main lineage state:

```text
lineage_id
generation_created
total_mutations
beneficial_mutations
harmful_mutations
lethal_mutations
size
fitness_score
```

The interface labels `size` as current population in the final surviving
lineages table. Lineage id `1` is the exact unmutated seed lineage; mutated
descendants receive new lineage ids.

The current implementation uses Poisson mutation multiplicity, normalized
compound-effect category weights, retained `random_seed`, the current linear
fitness formula, closest-integer cap rounding, a configurable runtime guard,
and an active lineage-count safety guard.

## Data Scaffolds

The repository includes an experimental-data foundation.

Its purpose is to make it possible to add, validate, inspect, and document
curated observations from experimental evolution studies.

Current scaffolded data files include:

- `data/source_registry.json`
- `data/raw/sprouffske_2018/phenotyping_data.tar.gz`
- `data/raw/sprouffske_2018/s3_genomic_mutation_rates.xlsx`
- `data/processed/example_observations.csv`
- `data/processed/calibration_dataset_v0.csv`

The current intended source areas include:

- Barrick lab LTEE-Ecoli genomics resources
- Sprouffske et al. 2018
- Couce et al. 2017
- Maddamsetti et al. 2020

The current data scaffold is raw and early processed input for future
calibration work, not a validated biological conclusion. The Streamlit lineage
app does not currently fit model parameters from these files.

Raw data should remain immutable. Processed data should document
transformations and avoid inventing missing values.

## Scientific Rule

Every result must be reported as conditional on assumptions.

A valid result is not:

```text
The optimal mutation rate is exactly 17.3x wild type.
```

A valid result is:

```text
Under these assumptions, this run produced surviving lineages with higher
weighted mean selected-environment fitness.
```

Experimental observations should be used to constrain, compare, or falsify
assumptions, not to create false precision.
