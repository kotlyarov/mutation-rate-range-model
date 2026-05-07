# Mutation Rate Range Model

A local, reproducible modelling tool for exploring mutation-rate trade-offs in
an *E. coli*-like asexual population.

The current application runs an explicit generational lineage
mutation-selection model. It is exploratory and uncalibrated: outputs are
conditional on selected assumptions and should not be presented as validated
biological estimates.

## Requirements

- Python 3.11 or newer
- `pip`
- A local browser for the Streamlit interface

Python dependencies are listed in [`requirements.txt`](requirements.txt):

```text
numpy
plotly
streamlit
pytest
```

## Run Locally

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

## Current Status

The repository implements the explicit lineage mutation-selection rewrite.

Current model behavior:

- one seed lineage starts generation 0
- each Mutation event creates new mutation-bearing descendant lineages
- mutations are counted as beneficial, harmful, lethal, or neutral
- lethal and low-fitness lineages are removed during Selection
- surviving lineages double before population-cap pressure is applied
- weighted mean fitness is recorded before population-cap reallocation
- post-cap mean fitness is retained separately for audit and debugging
- final surviving lineages are current lineage classes, not full family trees

The data scaffold is present for future calibration work, but the current app
does not fit model parameters from empirical data.

## Development Commands

```bash
python3 -m pytest
streamlit run app/streamlit_app.py
```

## Documentation

Start with:

- [`docs/model_lore.md`](docs/model_lore.md)
- [`docs/model_spec.md`](docs/model_spec.md)
- [`docs/assumptions.md`](docs/assumptions.md)
- [`docs/known_limitations.md`](docs/known_limitations.md)
- [`docs/validation_plan.md`](docs/validation_plan.md)
- [`docs/model_rewrite_review.md`](docs/model_rewrite_review.md)
- [`docs/scientific_background.md`](docs/scientific_background.md)
- [`docs/references.md`](docs/references.md)
- [`docs/data_plan.md`](docs/data_plan.md)
