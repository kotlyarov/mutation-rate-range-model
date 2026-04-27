# AGENTS.md

This repository builds a scientific model for estimating mutation-rate ranges in which long-term E. coli adaptation remains beneficial after accounting for genome decay.

## Scientific rules

- Do not present fitted parameters as universal constants.
- Do not claim exact per-mutation costs.
- Always separate:
  - observed data
  - inferred parameters
  - model assumptions
  - speculative interpretation
- Every parameter must have one of:
  - source citation
  - fitted estimate
  - explicit placeholder status
  - sensitivity range
- If a result is sensitive to an uncertain parameter, report that sensitivity clearly.
- Prefer simple models first.
- Add complexity only when tests or validation justify it.
- Do not hide failed model behaviour.

## Coding rules

- Use Python.
- Keep model logic separate from GUI.
- All formulas must be unit tested.
- Use fixed random seeds for reproducible stochastic tests.
- Avoid notebooks as the source of truth.
- Streamlit app should call functions from src/mrrm, not contain model logic.
- All plots must label units and assumptions.

## Testing commands

Run:

```bash
pytest
python -m mrrm.validation
streamlit run app/streamlit_app.py