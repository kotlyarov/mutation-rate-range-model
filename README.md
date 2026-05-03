# Mutation Rate Range Model

A local, reproducible modelling tool for exploring mutation-rate trade-offs in
an *E. coli*-like asexual population.

The project is inspired by the Long-Term Evolution Experiment (LTEE),
mutator genome-decay studies, and theoretical models of mutation-rate
evolution.

## Current Status

The repository now implements the explicit lineage mutation-selection rewrite.

Important:

```text
the model remains exploratory and uncalibrated
outputs are conditional on selected assumptions
```

The current design uses an explicit generational mutation-and-selection model:

- one seed lineage starts the run
- each generation creates mutation-bearing descendant lineages
- mutations are counted as beneficial, harmful, lethal, or neutral
- lethal and low-fitness lineages are removed during selection
- surviving lineages can double before population-cap pressure is applied
- weighted mean fitness is calculated from lineage sizes and fitness scores

The project is **not calibrated yet**. Experimental-data files are currently a
schema and curation foundation, not final fitted biological data.

## Run Locally

The current application runs the explicit lineage mutation-selection model.

From the repository root:

```bash
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install -r requirements.txt
python3 -m pytest
streamlit run app/streamlit_app.py
```

The Streamlit app should open at:

```text
http://localhost:8501/
```

## Goal

The goal is not to calculate the exact fitness effect of every possible genomic
change. That is not currently realistic.

The current model asks:

```text
Under these assumptions, what lineage trajectories occur for this mutation
rate or mutation-rate sweep?
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

See [`docs/model_spec.md`](docs/model_spec.md) for the current lineage model.

Main inputs:

```text
seed_fitness
seed_population
population_cap
generations
mutation_rate
beneficial_mutation_rate
harmful_mutation_rate
lethal_mutation_rate
compound_effect
mutation_effect
minimum_fitness
randomness
random_seed
max_runtime_seconds
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

The current spec uses Poisson mutation multiplicity, normalized
compound-effect category weights, retained `random_seed`, the current linear
fitness formula, closest-integer cap rounding, and a 60-second runtime guard.

## Experimental Data Scaffold

The repository includes an experimental-data foundation.

Its purpose is to make it possible to add, validate, inspect, and document
curated observations from experimental evolution studies.

Current intended source areas include:

- Barrick lab LTEE-Ecoli genomics resources
- Sprouffske et al. 2018
- Couce et al. 2017
- Maddamsetti et al. 2020

The current data scaffold is **raw experimental input for calibration, not a
validated biological conclusion**.

Raw data should remain immutable. Processed data should document
transformations and avoid inventing missing values.

## Repository Structure

```text
mutation-rate-range-model/
  README.md
  AGENTS.md
  pyproject.toml
  requirements.txt

  data/
    raw/
    processed/
    source_registry.json

  docs/
    scientific_background.md
    assumptions.md
    model_spec.md
    model_rewrite_review.md
    validation_plan.md
    known_limitations.md
    references.md
    data_plan.md

  src/
    mrrm/

  app/
    streamlit_app.py

  tests/

  reports/
```

Some listed files may be placeholders or scaffolds for later stages.

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

## Development Commands

```bash
python3 -m pytest
streamlit run app/streamlit_app.py
```

## Documentation

Start with:

- [`docs/model_spec.md`](docs/model_spec.md)
- [`docs/model_rewrite_review.md`](docs/model_rewrite_review.md)
- [`docs/assumptions.md`](docs/assumptions.md)
- [`docs/known_limitations.md`](docs/known_limitations.md)
- [`docs/validation_plan.md`](docs/validation_plan.md)
- [`docs/references.md`](docs/references.md)
- [`docs/data_plan.md`](docs/data_plan.md)
