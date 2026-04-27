# Mutation Rate Range Model

A local, reproducible modelling tool for exploring the mutation-rate range in which an *E. coli*-like asexual population can improve fitness over long periods while avoiding excessive genome decay.

The project is inspired by the Long-Term Evolution Experiment (LTEE), mutator genome-decay studies, and theoretical models of mutation-rate evolution.

## Current status

This repository is at the specification stage.

It currently contains project documentation and modelling requirements. The Python implementation, curated datasets, fitted parameters, and validation reports are not yet complete.

The first implementation should be deliberately small: deterministic curves, tests, and a minimal local interface for inspecting model behaviour.

## Goal

The goal is not to calculate the exact fitness effect of every possible genomic change. That is not currently realistic.

Instead, this project estimates empirical curves:

- mutation rate -> selected-environment fitness gain
- mutation rate -> mutation accumulation / genome-decay proxy
- mutation rate -> retained robustness in alternative environments
- mutation rate -> net long-term score

The model should identify an approximate range:

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

The project treats selected-environment fitness and genome integrity as related but separate outputs.

## What this project is

This project is:

- a transparent modelling tool
- a local GUI for exploring assumptions
- a curve-based approximation with uncertainty bands
- a reproducible Python codebase
- a way to test sensitivity of conclusions to uncertain parameters

## What this project is not

This project is not:

- a full whole-cell simulation
- a proof of a universal optimal mutation rate
- a model that knows the exact cost of every mutation
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

Later versions may add stochastic Wright-Fisher simulation, Approximate Bayesian Computation, Bayesian hierarchical fitting, and state-space models.

## Planned local GUI

The GUI should allow the user to:

- change mutation-rate range
- change generation horizon
- change benefit and decay parameters
- observe benefit, decay, robustness, and net-score curves
- view uncertainty bands
- inspect sensitivity analysis
- spot unrealistic model behaviour visually

Preferred stack:

- Python 3.11+
- NumPy
- SciPy
- pandas
- Plotly
- Streamlit
- Pydantic
- pytest

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
    external/
    README.md

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
      data_loaders.py
      plotting.py

  app/
    streamlit_app.py

  tests/
    test_curves.py
    test_parameters.py
    test_sensitivity.py
    test_validation.py

  notebooks/
    01_explore_sources.ipynb
    02_fit_initial_curves.ipynb
    03_validate_against_ltee.ipynb

  reports/
    first_model_report.md
```

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

The first model is intended to test whether assumptions produce biologically plausible curve shapes, not to estimate a true biological optimum.

## First Codex task

Build the initial Python project skeleton from `docs/model_spec.md`.

Implement only:

- deterministic curve functions
- parameter validation
- tests
- simple plotting helpers
- a basic Streamlit GUI for local inspection

Do not implement yet:

- stochastic simulation
- Bayesian fitting
- real-data fitting
- automated conclusions
- publication-style claims

## Development commands

Expected commands after the first implementation:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pytest
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
