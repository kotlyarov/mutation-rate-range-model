# Model Specification

This document defines the current high-level Mutation Rate Range Model.

## Scope

The primary model is now a generational lineage-survival model. A single run
fixes one mutation-rate multiplier and asks whether beneficial lineages survive
and spread before harmful mutation accumulation and genome-decay proxy effects
derail them.

The model remains exploratory and transparent. It should not be interpreted as a
validated population-genetic simulator.

It should not include:

- Approximate Bayesian Computation
- Bayesian hierarchical fitting
- database or cloud integrations
- automatic scientific claims
- hidden parameter fitting

Those may be added only after explicit design and validation work.

## Core inputs

The main single-run inputs are:

```text
mutation_rate_multiplier = mutation-rate multiplier relative to wild type
population_size = number of surviving lineages sampled each generation
generations = generation horizon
```

Additional transparent assumptions control mutation supply, inherited effects,
interference, and survival selection:

```text
T_ref = reference horizon used to scale per-generation event rates
alpha_benefit = beneficial event-rate scale
neutral_rate_scale = neutral event-rate scale
decay_scale = harmful / decay event-rate scale
gamma_decay = nonlinearity for harmful / decay event supply
beneficial_effect_size = benefit increment from one beneficial event before interference
decay_effect_size = decay-proxy increment from one harmful event
benefit_scale = saturation ceiling for accumulated selected-environment benefit
beta_interference, gamma_interference = interference parameters
lambda_decay = fitness penalty weight for accumulated decay proxy
rho_robustness = fitness penalty/reward weight for retained robustness
selection_strength = strength of fitness-weighted survival
random_seed = seed for reproducible stochastic runs
```

## Lineage state

Each surviving lineage class carries inherited biological state:

```text
count
accumulated_benefit
accumulated_decay
robustness
fitness
has_beneficial
has_harmful
```

This state is not reset between generations. The same generation-transition
rules are reapplied to the surviving classes.

The core biological quantities remain conceptually separated:

```text
B = accumulated selected-environment adaptive benefit
D = accumulated mutation-accumulation / genome-decay proxy
R = retained robustness
fitness = survival-relevant relative fitness
```

`D` remains a proxy. It is not a literal measurement of every harmful mutation.

## One-generation mutation rules

For one generation, event probabilities are derived from independent Poisson
arrival assumptions:

```text
r_b = alpha_benefit * mutation_rate_multiplier / T_ref
r_h = decay_scale * mutation_rate_multiplier^gamma_decay / T_ref
r_n = neutral_rate_scale * mutation_rate_multiplier / T_ref

p_b = 1 - exp(-r_b)
p_h = 1 - exp(-r_h)
p_n = 1 - exp(-r_n)
```

Offspring from each lineage class are stochastically split into high-level
mutation classes:

```text
no_new_mutation = (1 - p_b) * (1 - p_h) * (1 - p_n)
neutral = (1 - p_b) * (1 - p_h) * p_n
harmful = (1 - p_b) * p_h
beneficial = p_b * (1 - p_h)
mixed = p_b * p_h
```

The simulator samples integer counts from these probabilities. This means tiny
expected probabilities do not automatically create fractional impossible
lineages. For example, if the population has 1,000,000 individuals and a class
has expected count far below one, that class usually does not exist unless the
stochastic draw creates it.

## State update rules

For a no-new-mutation or neutral offspring class:

```text
B_next = B_inherited
D_next = D_inherited
```

For a harmful offspring class:

```text
D_next = D_inherited + decay_effect_size
B_next = B_inherited
```

For a beneficial offspring class:

```text
interference =
  1 / (1 + beta_interference * interference_load^gamma_interference)

benefit_increment =
  min(benefit_scale - B_inherited, beneficial_effect_size * interference)

B_next = B_inherited + benefit_increment
D_next = D_inherited
```

For a mixed beneficial-plus-harmful offspring class, the harmful decay increment
is applied and the beneficial increment is reduced by interference from both the
inherited decay and the newly acquired harmful increment:

```text
interference_load = D_inherited + decay_effect_size
```

After updating `B` and `D`:

```text
R_next = exp(-k_robustness * D_next)

fitness_next =
  max(0, 1 + B_next - lambda_decay * D_next + rho_robustness * (R_next - 1))
```

The `rho_robustness * (R - 1)` term makes the starting generation fitness equal
to 1.0 and treats robustness loss as a conditional fitness penalty rather than
an unconditional bonus.

## Survival selection

After mutation creates candidate offspring classes, survival selection samples
the next generation. The population size is fixed by resampling exactly
`population_size` survivors.

For candidate class `i`:

```text
survival_weight_i =
  candidate_count_i * max(fitness_i, minimum_survival_fitness)^selection_strength

survival_probability_i =
  survival_weight_i / sum_j(survival_weight_j)
```

The next generation's class counts are sampled from a multinomial distribution
with these survival probabilities. A class can disappear if its sampled survivor
count is zero. Surviving classes seed the next generation with their accumulated
state intact.

This is stochastic lineage-class sampling, not a deterministic post-processing
weight over mutation-rate bins.

## Main outputs

The main chart uses:

```text
X axis = generation
Y axis = relative fitness
```

It should show:

- starting generation
- mean population fitness
- best surviving lineage fitness
- dominant lineage fitness
- beneficial adoption fraction over time

The run also reports:

```text
final mean fitness
final best lineage fitness
final dominant lineage fitness
final beneficial adoption fraction
final mean decay proxy
whether any beneficial lineage survived
whether beneficial adoption crossed the configured threshold
whether mean fitness crossed the configured collapse threshold
```

All outputs must be described as conditional on the selected assumptions.

## Static curve helpers

The older deterministic mutation-rate landscape helpers are retained for
calibration context and future mutation-rate sweeps:

```text
B(m, T) = selected-environment adaptive benefit curve
D(m, T) = mutation-accumulation / genome-decay proxy curve
R(m, T) = retained robustness curve
S(m, T) = net long-term score curve
```

They should not be used as the primary survival mechanism. Survival is now
modelled generation by generation in the lineage model.

## Later mutation-rate sweep

After the single-run lineage model is working, a mutation-rate sweep should run
the same generational model repeatedly across mutation-rate multiplier values.
The sweep should compare:

- final mean fitness
- best surviving lineage fitness
- beneficial lineage survival and adoption
- mean decay proxy
- collapse or derailment frequency across repeated seeds

Only then should the project estimate an assumption-dependent mutation-rate
range from lineage-survival outcomes. The wording must remain conditional, for
example:

```text
Under the selected assumptions, repeated lineage runs suggest a high-performing
mutation-rate multiplier region near X.
```
