# AGENTS.md

Instructions for coding agents working on this repository.

## Project purpose

This repository contains the Mutation Rate Range Model: a local, reproducible research tool for exploring mutation-rate trade-offs in an *E. coli*-like asexual population.

The project does not try to calculate the exact fitness effect of every mutation. It uses transparent deterministic curves first, then may later add stochastic and data-fitting layers.

## Current implementation stage

The project is at the documentation/specification stage.

The first implementation must be narrow:

- create the Python package skeleton
- implement deterministic curves only
- validate parameters
- add tests
- add simple plotting helpers
- add a minimal Streamlit GUI

Do not add stochastic simulation, Bayesian fitting, database integrations, cloud services, or complex data pipelines unless explicitly requested later.

## Scientific constraints

All model results must be conditional on assumptions.

Never write code or UI text that implies the model has found a true universal optimal mutation rate.

Avoid language like:

```text
The optimal mutation rate is X.
```

Prefer language like:

```text
Under the selected assumptions, the model estimates a net-score peak near X.
```

The model must keep selected-environment fitness and genome integrity conceptually separate.

## Core model terms

Use these first-version functions:

```text
B(m, T) = selected-environment adaptive benefit
D(m, T) = mutation-accumulation / genome-decay proxy
R(m, T) = retained robustness
S(m, T) = net long-term score
```

Where:

```text
m = mutation-rate multiplier relative to wild type
T = generation horizon

S(m, T) = B(m, T) - lambda_decay * D(m, T) + rho_robustness * R(m, T)
```

Important: `D` is a proxy, not a literal measurement of every harmful mutation.

## Coding rules

Use Python 3.11+.

Prefer:

- small pure functions
- typed dataclasses or Pydantic models for parameters
- deterministic tests
- clear error messages
- no hidden global state
- no network access in core model code
- no hard-coded conclusions

Avoid:

- magic constants without names
- fitting fake data and presenting it as real
- silently clipping parameters without warning
- complex abstractions before the simple model works
- stochastic behaviour in deterministic tests

## Suggested package layout

```text
src/
  mrrm/
    __init__.py
    parameters.py
    curves.py
    sensitivity.py
    validation.py
    plotting.py

app/
  streamlit_app.py

tests/
  test_parameters.py
  test_curves.py
  test_sensitivity.py
  test_validation.py
```

Files such as `stochastic.py`, `fitting.py`, and `data_loaders.py` may exist as placeholders, but the first implementation should not build their full behaviour.

## First implementation requirements

Implement parameter validation for:

- mutation-rate range
- generation horizon
- benefit saturation
- decay penalty
- robustness weight
- numerical stability

Implement deterministic functions for:

- adaptive benefit
- mutation-accumulation / decay proxy
- retained robustness
- net score
- locating `mu_min`, `mu_peak`, and `mu_max` using threshold rules

Add tests that check:

- output arrays have expected shape
- no NaN or infinite values are produced for valid inputs
- benefit is non-negative
- decay is non-negative
- robustness is bounded
- net score changes when penalty weights change
- invalid parameters raise clear errors

## GUI requirements

The Streamlit GUI should be local and simple.

It should allow the user to:

- set mutation-rate multiplier range
- set generation horizon
- adjust benefit/decay/robustness parameters
- display curves for `B`, `D`, `R`, and `S`
- display approximate `mu_min`, `mu_peak`, and `mu_max`
- show a warning that outputs are assumption-dependent

The GUI should not imply that the model has been validated until validation code and reports exist.

## Documentation requirements

When changing model behaviour, update:

- `docs/model_spec.md`
- `docs/assumptions.md`
- `docs/known_limitations.md`
- tests that encode the expected behaviour

## Commit discipline

Prefer small commits:

```text
docs: clarify first deterministic model
model: implement deterministic curves
test: add curve and parameter tests
app: add minimal Streamlit explorer
```

Do not combine unrelated scientific, GUI, and infrastructure changes in one commit.
