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
effective_population_size = number of surviving lineages sampled each generation
generations = generation horizon
```

Additional transparent assumptions control mutation supply, inherited effects,
interference, and survival selection:

```text
neutral_mutation_rate = neutral per-generation event rate at 1x mutation rate
deleterious_mutation_rate = harmful / decay per-generation event rate at 1x mutation rate
beneficial_mutation_rate = beneficial per-generation event rate at 1x mutation rate
beneficial_effect_size = benefit increment from one beneficial event before interference
decay_effect_size = decay-proxy increment from one harmful event
benefit_saturation = saturation ceiling for accumulated selected-environment benefit
interference_strength, interference_exponent = interference parameters
robustness_decay_rate = effect of accumulated decay on retained robustness
decay_fitness_penalty = gradual performance penalty weight for accumulated decay proxy
robustness_fitness_weight = weight for retained-robustness performance modifier
lethal_decay_threshold = hard accumulated-decay viability ceiling
minimum_viable_robustness = hard retained-robustness viability floor
selection_strength = strength of fitness-weighted survival
viability_fitness_threshold = minimum fitness for a candidate class to remain viable
beneficial_adoption_threshold = interpretation threshold for adoption
collapse_fitness_threshold = interpretation threshold for collapse
```

Simulation controls are not biological assumptions and should be kept out of
the main model interface:

```text
random_seed = reproducibility control
max_lineage_classes = computational class-count safety limit
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
r_b = beneficial_mutation_rate * mutation_rate_multiplier
r_h = deleterious_mutation_rate * mutation_rate_multiplier
r_n = neutral_mutation_rate * mutation_rate_multiplier

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

These transition probabilities are applied to every surviving lineage class in
every generation, including classes that already carry beneficial mutations.
Existing beneficial state does not reduce future harmful or mixed mutation
exposure.

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
  1 / (1 + interference_strength * interference_load^interference_exponent)

benefit_increment =
  min(benefit_saturation - B_inherited, beneficial_effect_size * interference)

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
R_next = exp(-robustness_decay_rate * D_next)

performance_fitness =
  max(0, 1 + B_next - decay_fitness_penalty * D_next)

robustness_modifier =
  max(0, 1 - robustness_fitness_weight * (1 - R_next))

fitness_next = performance_fitness * robustness_modifier
```

Robustness is not an additive benefit that can cancel decay. It acts as a
performance modifier and as a separate viability gate.

## Survival selection

After mutation creates candidate offspring classes, survival selection first
removes nonviable classes. `effective_population_size` is a carrying-capacity
limit, not a guarantee that the next generation is full.

For candidate class `i`:

```text
viable_i =
  fitness_i >= viability_fitness_threshold
  and D_i <= lethal_decay_threshold
  and R_i >= minimum_viable_robustness

competitive_weight_i =
  0, if viable_i is false
  candidate_count_i * fitness_i^selection_strength, otherwise

actual_population_size_next =
  min(effective_population_size, viable_population_size)

survivor_counts ~ Multinomial(
  actual_population_size_next,
  competitive_weight / sum(competitive_weight)
)

actual_population_size_next <= viable_population_size <= candidate_population_size
```

The next generation can be smaller than the carrying capacity. A badly damaged
lineage does not survive just because empty capacity exists. Above the viability
threshold, higher fitness improves competitive lineage success because it
increases competitive weight without being capped at one. The competitive weight
changes lineage proportions among viable offspring; it does not create extra
population after nonviable offspring have been removed. If all candidate classes
are nonviable, the actual population size becomes zero and the run is collapsed.

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
final actual population size
carrying capacity
viable candidate population size
final beneficial adoption fraction
final mean decay proxy
whether any beneficial lineage survived
whether beneficial adoption crossed the configured threshold
whether mean fitness crossed the configured collapse threshold or population collapsed
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
