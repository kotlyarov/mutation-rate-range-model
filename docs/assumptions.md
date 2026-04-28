# Assumptions

This document lists assumptions used by the first deterministic version of the Mutation Rate Range Model.

## General assumptions

The first model assumes:

- an *E. coli*-like asexual population
- mutation rate is represented as a multiplier relative to wild type
- selected-environment fitness and genome integrity can be represented separately
- model outputs are approximate curves, not exact biological measurements
- results are conditional on parameter choices
- Survival Selection, when enabled, is an expected survival filter rather than a
  full population-genetic simulation

## Biological assumptions

### Asexual population

The first version assumes no recombination.

This is reasonable for a simplified LTEE-like model, but it limits generality.

### Constant selected environment

The selected environment is treated as stable across the generation horizon.

This allows selected-environment fitness gain to be modelled separately from robustness in alternative environments.

### Mutation-rate multiplier

Mutation rate is represented as:

```text
m = mutation-rate multiplier relative to wild type
```

The model does not initially distinguish between:

- point mutations
- indels
- structural variants
- spectrum changes
- context-dependent mutation biases

Later versions may separate mutation rate and mutation spectrum.

### Adaptive benefit

The first version assumes selected-environment adaptive benefit increases with mutation supply at low-to-moderate mutation rates, then saturates or declines when interference or deleterious load becomes important.

### Genome decay proxy

The first version assumes mutation accumulation and genome-integrity loss can be approximated by a scalar proxy:

```text
D(m, T)
```

This is a simplification.

`D` is not a direct count of deleterious mutations and not a direct measurement of lost genes.

### Robustness

The first version assumes retained robustness can be represented as a bounded score:

```text
0 <= R(m, T) <= 1
```

This is a proxy for the ability to retain performance outside the selected environment.

### Net score

The net score is an artificial utility score:

```text
S(m, T) = B(m, T) - lambda_decay * D(m, T) + rho_robustness * R(m, T)
```

It is useful for comparing assumptions, not for declaring a biological law.

### Survival Selection

The optional Survival Selection block assumes that mutation-rate classes with
higher net scores contribute more to the next threshold landscape under
replacement competition.

The first implementation uses expected fitness-weighted survival probabilities
inside the generation loop. It does not create explicit organisms, lineages,
transfers, nutrient dynamics, or experimental bottleneck protocols.

`population_growth_factor` is only a pressure modifier:

- values above 1 weaken selection by increasing the effective growth buffer
- values below 1 strengthen selection by representing tighter replacement
  competition

`survival_stochasticity` is implemented as deterministic neutral mixing between
fitness-weighted survival and the previous generation's composition. It
represents probabilistic survival noise without sampling a random next
generation.

The default value, `0.23`, is not a direct fitted survival parameter. It maps
the closest experimental drift proxy found, LTEE ancestor descendant-number
variance around 1.3, to excess stochasticity `(1.3 - 1) / 1.3`.

## Modelling assumptions

### Deterministic curves first

The first version does not simulate individuals, lineages, fixation, drift, or clonal interference directly.

Instead, these effects are represented indirectly through curve shapes and parameters.
Survival Selection adds a minimal viability-selection expectation, but it still
does not model realized genetic drift or fixation.

### Log-spaced mutation-rate range

Mutation-rate multipliers should usually be evaluated on a log scale because biologically relevant differences can span orders of magnitude.

### Configurable thresholds

`mu_min` and `mu_max` are threshold-based estimates, not direct biological constants.

Thresholds must remain configurable.

### Defaults are not fitted values

Default parameters are placeholders for model exploration.

They must not be described as inferred from real data unless fitting code and validation reports are later added.

## Reporting assumptions

Any result must include language similar to:

```text
Under the selected assumptions and parameter ranges...
```

Do not report outputs as unconditional facts.

## Assumptions to revisit later

Later versions should revisit:

- mutation spectrum
- epistasis
- changing distribution of fitness effects
- population size
- bottlenecks
- clonal interference
- drift
- environmental change
- robustness across many alternative environments
- parameter fitting from empirical data
- uncertainty propagation
