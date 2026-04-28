# Mutation Rate Range Model

A local, reproducible modelling tool for exploring the mutation-rate range in which an *E. coli*-like asexual population can improve fitness over long periods while avoiding excessive mutation accumulation, genome decay, or robustness loss.

The project is inspired by the Long-Term Evolution Experiment (LTEE), mutator genome-decay studies, and theoretical models of mutation-rate evolution.

## Current status

This repository now contains:

- a first deterministic curve-based model
- a local Streamlit GUI for inspecting model behaviour
- parameter validation and tests
- plotting helpers
- an experimental-data scaffold for curated observations
- an experimental-data inventory section in the app

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

Instead, this project estimates empirical curves:

- mutation rate -> selected-environment fitness gain
- mutation rate -> mutation accumulation / genome-decay proxy
- mutation rate -> retained robustness in alternative environments
- mutation rate -> net long-term score

The model should eventually identify an approximate range:

- `mu_min`: mutation-rate multiplier below which adaptation is too slow
- `mu_peak`: mutation-rate multiplier with the highest net score
- `mu_max`: mutation-rate multiplier above which mutation accumulation, deleterious load, or robustness loss dominates

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
- a curve-based approximation with uncertainty bands
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

## First model version

The first version uses deterministic curves:

```text
B(m, T) = selected-environment adaptive benefit
D(m, T) = mutation-accumulation / genome-decay proxy
R(m, T) = retained robustness
S(m, T) = net long-term score
```

Where:

```text
m = mutation-rate multiplier relative to wild type
T = number of generations

S(m, T) = B(m, T) - lambda_decay * D(m, T) + rho_robustness * R(m, T)
```

Important: `D(m, T)` is a scalar proxy. It is not a direct measurement of every harmful mutation. It combines mutation accumulation, deleterious load, and inferred loss of genome integrity into one deliberately simplified term.

The first model is intended to test whether assumptions produce biologically plausible curve shapes, not to estimate a true biological optimum.

Later versions may add stochastic Wright-Fisher simulation, Approximate Bayesian Computation, Bayesian hierarchical fitting, and state-space models.

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

In calibrated mode, the app derives the evaluated mutation-rate range from the selected strain and closest experimental generation in `calibration_dataset_v0` before computing thresholds. The generation horizon control selects the nearest experimental generation for calibration. Every model input is displayed with provenance: empirical, fitted, assumed, or unsupported by the current data. Parameters that cannot yet be estimated from exact observations remain marked as unsupported exploratory fallbacks rather than fitted values.

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

- inspect raw experimental observations before model curves
- enable manual parameter overrides for hypothesis exploration
- select Sprouffske strain class (`MRS`, `MRM`, `MRL`, `MRXL`)
- change mutation-rate range
- change generation horizon
- change benefit, decay, and robustness parameters
- observe benefit, decay, robustness, and net-score curves
- inspect whether curve behaviour looks biologically plausible
- view model-input provenance and the experimental-data inventory scaffold

The experimental-data section should be read with the provenance table. Current calibrated thresholds are sensitive to the empirical mutation-rate axis, but unsupported benefit and decay terms still depend on exploratory fallback values until exact observations are curated.

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
    sources.yaml

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
      config.py
      parameters.py
      curves.py
      stochastic.py
      fitting.py
      sensitivity.py
      validation.py
      datasets.py
      data_loaders.py
      plotting.py

  app/
    streamlit_app.py

  tests/
    test_curves.py
    test_parameters.py
    test_sensitivity.py
    test_validation.py
    test_datasets.py
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
Under these assumptions and uncertainty ranges, the model estimates a likely net-beneficial mutation-rate range between A and B times wild type, with the peak near C to D times wild type. The result is most sensitive to genome-decay penalty and DFE assumptions.
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

1. add the full Sprouffske growth-curve trajectory rows for intermediate generations
2. separate placeholder/schema rows from real processed observations
3. compare deterministic curves against curated data points
4. replace deprecated Streamlit `use_container_width` calls with `width`
5. add validation plots
6. document which assumptions are supported, weakly supported, or contradicted
7. only then consider stochastic simulation
