# Model Specification

This document defines the first deterministic version of the Mutation Rate Range Model.

## Scope

The first version is a deterministic curve model. It should be simple, inspectable, and easy to test.

It should not include:

- stochastic Wright-Fisher simulation
- Approximate Bayesian Computation
- Bayesian hierarchical fitting
- real-data parameter inference
- automatic scientific claims

Those may be added later.

## Inputs

The core inputs are:

```text
m = mutation-rate multiplier relative to wild type
T = number of generations
```

The model evaluates a vector of mutation-rate multipliers:

```text
m_values = [m_min, ..., m_max]
```

Example default range:

```text
m_min = 0.1
m_max = 100.0
n_points = 400
```

Use log-spaced mutation-rate values by default because the biologically interesting range may span orders of magnitude.

## Core outputs

The first model computes:

```text
B(m, T) = selected-environment adaptive benefit
D(m, T) = mutation-accumulation / genome-decay proxy
R(m, T) = retained robustness
S(m, T) = net long-term score
```

The net score is:

```text
S(m, T) = B(m, T) - lambda_decay * D(m, T) + rho_robustness * R(m, T)
```

Where:

```text
lambda_decay = penalty weight for mutation accumulation / genome decay
rho_robustness = reward weight for retained robustness
```

## Interpretation of terms

### Adaptive benefit: `B(m, T)`

`B` represents selected-environment fitness gain.

It should generally:

- be non-negative
- increase with generation horizon
- increase with mutation rate at low-to-moderate mutation rates
- saturate or decline at high mutation rates if deleterious interference is included

A simple first form:

```text
beneficial_supply(m) = 1 - exp(-alpha_benefit * m * T_scaled)
interference(m) = 1 / (1 + beta_interference * m^gamma_interference)

B(m, T) = benefit_scale * beneficial_supply(m) * interference(m)
```

Where:

```text
T_scaled = T / T_ref
```

### Decay proxy: `D(m, T)`

`D` represents a scalar proxy for mutation accumulation, deleterious load, and inferred genome-integrity loss.

It should generally:

- be non-negative
- increase with mutation rate
- increase with generation horizon
- be allowed to accelerate at high mutation rates

A simple first form:

```text
D(m, T) = decay_scale * (m^gamma_decay) * T_scaled
```

Important: `D` is not a literal count of harmful mutations. It is a modelling proxy.

### Robustness: `R(m, T)`

`R` represents retained robustness in alternative or future environments.

It should generally:

- be bounded between 0 and 1
- decline as mutation accumulation increases
- remain interpretable as a relative score, not a direct measurement

A simple first form:

```text
R(m, T) = exp(-k_robustness * D(m, T))
```

## Net score

The net score combines the three outputs:

```text
S(m, T) = B(m, T) - lambda_decay * D(m, T) + rho_robustness * R(m, T)
```

This score is not biological truth. It is an assumption-dependent utility score for exploring trade-offs.

## Derived range estimates

The model should estimate:

```text
mu_peak = m where S(m, T) is maximal
mu_min = lowest m that reaches a threshold fraction of peak benefit
mu_max = highest m before net score or decay threshold becomes unacceptable
```

Suggested default rules:

```text
benefit_threshold_fraction = 0.80
decay_threshold_fraction = 0.80
net_threshold_fraction = 0.80
```

Possible definitions:

```text
mu_min = lowest m where B(m, T) >= benefit_threshold_fraction * max(B)

mu_peak = m at max(S)

mu_max = highest m where:
  S(m, T) >= net_threshold_fraction * max(S)
  and D(m, T) <= decay_threshold_fraction * max(D)
```

These rules must be configurable and clearly labelled.

## Default parameter object

Suggested first parameter object:

```text
T = 50000
T_ref = 50000

m_min = 0.1
m_max = 100.0
n_points = 400

benefit_scale = 1.0
alpha_benefit = 1.0
beta_interference = 0.01
gamma_interference = 1.0

decay_scale = 1.0
gamma_decay = 1.2

k_robustness = 0.05

lambda_decay = 0.2
rho_robustness = 0.1

benefit_threshold_fraction = 0.80
net_threshold_fraction = 0.80
decay_threshold_fraction = 0.80
```

These defaults are placeholders for exploration. They must not be presented as fitted biological values.

## Required functions

Implement pure functions similar to:

```python
def make_m_values(params) -> np.ndarray:
    ...

def adaptive_benefit(m_values: np.ndarray, params) -> np.ndarray:
    ...

def decay_proxy(m_values: np.ndarray, params) -> np.ndarray:
    ...

def robustness(m_values: np.ndarray, decay_values: np.ndarray, params) -> np.ndarray:
    ...

def net_score(
    benefit_values: np.ndarray,
    decay_values: np.ndarray,
    robustness_values: np.ndarray,
    params,
) -> np.ndarray:
    ...

def estimate_range(
    m_values: np.ndarray,
    benefit_values: np.ndarray,
    decay_values: np.ndarray,
    robustness_values: np.ndarray,
    score_values: np.ndarray,
    params,
) -> dict:
    ...
```

## Validation rules

For valid inputs:

- all output arrays must match the shape of `m_values`
- no output should contain NaN or infinity
- `B` must be non-negative
- `D` must be non-negative
- `R` must be between 0 and 1
- `mu_peak` must be one of the evaluated `m_values`
- invalid parameters must raise clear exceptions

## GUI behaviour

The GUI should show:

- adaptive benefit curve
- decay proxy curve
- robustness curve
- net-score curve
- selected parameter values
- estimated `mu_min`, `mu_peak`, and `mu_max`
- warning that outputs are assumption-dependent

The GUI must not say that the model has discovered the true optimal mutation rate.

## Output language

Use cautious language:

```text
Under current assumptions...
The model estimates...
The score peaks near...
The result is sensitive to...
```

Avoid:

```text
The optimal mutation rate is...
Evolution chooses...
This proves...
```
