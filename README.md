# Mutation Rate Range Model

A local, reproducible modelling tool for exploring the mutation-rate range in which an *E. coli*-like asexual population can improve fitness over long periods while avoiding excessive mutation accumulation, genome decay, or robustness loss.

The project is inspired by the Long-Term Evolution Experiment (LTEE), mutator genome-decay studies, and theoretical models of mutation-rate evolution.

## Current status

This repository now contains:

- a generational lineage-survival model
- retained deterministic curve helpers for calibration context and later sweeps
- a local Streamlit GUI for inspecting one lineage run
- parameter validation and tests
- plotting helpers
- an experimental-data scaffold for curated observations

The project is **not calibrated yet**. The included experimental-data files are currently a schema/pipeline foundation, not final fitted biological data.

## Run locally

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

If Streamlit asks for an email address on first launch, it can be left blank.

The app may print a warning about `urllib3`, LibreSSL, or Streamlit's `use_container_width` deprecation. These warnings do not necessarily stop the app from running, but the deprecation warning should be cleaned up in a future code update.

## Goal

The goal is not to calculate the exact fitness effect of every possible genomic change. That is not currently realistic.

Instead, this project follows aggregated lineage classes generation by generation:

- one run fixes a mutation-rate multiplier
- each generation samples no-new, neutral, harmful, beneficial, and mixed offspring classes
- accumulated benefit, decay proxy, robustness, and fitness carry forward
- stochastic survival selection determines which classes seed the next generation

The current main question is:

```text
Will beneficial lineages survive and spread before being derailed by harmful mutations / genome decay?
```

A later mutation-rate sweep should run the same lineage model repeatedly across
mutation-rate multipliers and random seeds before estimating an approximate
assumption-dependent range.

Mutation rate is represented as a multiplier relative to a wild-type *E. coli* baseline.

## Scientific motivation

Several experimental and theoretical results motivate this project:

- Couce et al. 2017 showed that hypermutable LTEE bacteria can keep gaining fitness in the selected environment while their genomes decay.
- Sprouffske et al. 2018 showed that high mutation rates can limit adaptive evolution in *E. coli*.
- Good & Desai 2016 developed theory for mutation-rate evolution in rapidly adapting asexual populations.
- LTEE datasets provide long-term empirical data for mutation accumulation, fitness change, and evolutionary dynamics.
- Maddamsetti et al. 2020 studied mutation-rate and mutation-bias evolution in LTEE populations.

The project treats selected-environment fitness and genome integrity as related but separate outputs.

## What this project is

This project is:

- a transparent modelling tool
- a local GUI for exploring assumptions
- a high-level stochastic lineage-survival approximation
- a reproducible Python codebase
- a place to curate experimental observations
- a way to test sensitivity of conclusions to uncertain parameters

## What this project is not

This project is not:

- a full whole-cell simulation
- a proof of a universal optimal mutation rate
- a model that knows the exact cost of every mutation
- a calibrated biological predictor yet
- a claim that "good" and "bad" mutations are absolute categories
- a replacement for experimental biology

## Current model version

The current primary model uses generational lineage survival:

```text
mutation_rate_multiplier = fixed input for one run
effective_population_size = carrying-capacity limit for actual population size
generation = X axis for the main population trajectory chart
```

Each surviving lineage class carries:

```text
accumulated selected-environment benefit
accumulated mutation-accumulation / genome-decay proxy
retained robustness
relative fitness
```

Important: `D` is a scalar proxy. It is not a direct measurement of every harmful mutation. It combines mutation accumulation, deleterious load, and inferred loss of genome integrity into one deliberately simplified term.

The lineage model is intended to test whether assumptions produce biologically plausible survival trajectories, not to estimate a true biological optimum.

The older deterministic curve helpers remain in the package for calibration context and future mutation-rate sweeps, but survival is now modelled generation by generation rather than as a final weight over mutation-rate bins.

## Experimental data scaffold

The repository now includes an experimental-data foundation.

Its purpose is to make it possible to add, validate, inspect, and document curated observations from experimental evolution studies.

Current intended source areas include:

- Barrick lab LTEE-Ecoli genomics resources
- Sprouffske et al. 2018
- Couce et al. 2017
- Maddamsetti et al. 2020

The current data scaffold is **raw experimental input for calibration, not a validated biological conclusion**.

calibration_dataset_v0 currently contains real Sprouffske et al. 2018 mutation-rate values and confidence intervals, plus curated Dryad growth-curve relative-fitness observations for the existing strain/replicate/final-generation calibration slots. Every fitness value names its same-batch ancestor control. The dataset still does not contain mutation-count/genome-decay costs or robustness observations, so decay and robustness conclusions remain unsupported.

The curated relative-fitness values are computed from Dryad `growth-curves.txt` as `r_evo - r_anc`, following the paper methods. The raw Dryad final timepoint is generation `2907`; the paper labels this final timepoint as approximately `3000` generations, and the processed rows preserve that context in curation notes.

Processed observations should preserve source context, including:

- source or paper
- experiment
- strain or population
- generation
- mutation-rate multiplier if known
- relative fitness if known
- mutation count or genome-decay proxy if known
- robustness or environment information if known
- uncertainty and method notes

Raw data should remain immutable. Processed data should document transformations and avoid inventing missing values.

## Streamlit app

The local GUI allows the user to:

- set a fixed mutation-rate multiplier
- set effective population size and generation horizon
- adjust mutation supply, benefit, decay, robustness, and survival parameters
- observe total population size, benefit-led population size, decay-led population size, and mean fitness by generation
- see total mutated lineages evolved and total mutated lineages still surviving
- inspect generation history and final surviving lineage classes
- inspect the collapsed model audit for formulas, trajectory classification, lineage-production accounting, probabilities, population-cap logic, hidden simulation controls, thresholds, and input provenance

The GUI should be read as an exploratory single-run view. Changing the random
seed can change rare-lineage outcomes.

## Repository structure

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
    validation_plan.md
    known_limitations.md
    references.md
    data_plan.md

  src/
    mrrm/
      __init__.py
      parameters.py
      curves.py
      lineage.py
      sensitivity.py
      validation.py
      data_loaders.py
      plotting.py

  app/
    streamlit_app.py

  tests/
    test_curves.py
    test_lineage.py
    test_parameters.py
    test_sensitivity.py
    test_validation.py
    test_data_loaders.py

  reports/
    first_model_report.md
    data_inventory.md
```

Some listed files may be placeholders or scaffolds for later stages.

## Scientific rule

Every result must be reported as conditional on assumptions.

A valid result is not:

```text
The optimal mutation rate is exactly 17.3x wild type.
```

A valid result is:

```text
Under these assumptions and this random seed, beneficial lineage adoption rose
while mean fitness remained above the selected collapse threshold.
```

Experimental observations should be used to constrain, compare, or falsify assumptions — not to create false precision.

## Development commands

```bash
python3 -m pytest
streamlit run app/streamlit_app.py
```

## Documentation

Start with:

- [`docs/model_spec.md`](docs/model_spec.md)
- [`docs/assumptions.md`](docs/assumptions.md)
- [`docs/known_limitations.md`](docs/known_limitations.md)
- [`docs/references.md`](docs/references.md)
- [`docs/data_plan.md`](docs/data_plan.md)
- [`docs/validation_plan.md`](docs/validation_plan.md)
- [`reports/first_model_report.md`](reports/first_model_report.md)
- [`reports/data_inventory.md`](reports/data_inventory.md)
- [`reports/calibration_audit.md`](reports/calibration_audit.md)

## Next steps

Likely next development steps:

1. add a mutation-rate sweep that repeats the lineage model across small multiplier steps
2. compare final fitness, beneficial lineage adoption, and collapse frequency across repeated seeds
3. add validation plots for the generational trajectories
4. document which assumptions are supported, weakly supported, or contradicted
5. compare lineage trajectories against curated experimental observations
