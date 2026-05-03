# Model Specification

This document defines the current explicit lineage mutation-selection model.

Status:

```text
implemented lineage model
exploratory and uncalibrated
```

The rewrite replaces the previous curve-first and lineage-class logic with an
explicit generational mutation-and-selection model. A run begins with one seed
lineage, creates new mutation-bearing lineages during each Mutation event, then
filters and resizes lineages during each Selection event.

The model remains exploratory. It must not be interpreted as a validated
population-genetic simulator or as evidence for a universal optimal mutation
rate.

## Scope

The model includes:

- explicit lineage records
- integer population sizes
- generation-by-generation Mutation and Selection events
- mutation counts separated into beneficial, harmful, lethal, and neutral
  categories
- weighted mean fitness by generation
- population-cap selection pressure
- clear parameter validation
- assumption-dependent reporting

The model does not include:

- deterministic `B(m, T)`, `D(m, T)`, `R(m, T)`, or `S(m, T)` curves as the
  primary mechanism
- Bayesian fitting
- stochastic simulation layers beyond the requested mutation and survival
  sampling
- database or cloud integrations
- automatic claims that a true biological optimum has been found

## Inputs

### Experimental Setup

```text
seed_fitness = 0.6
seed_population = 100000
population_cap = 1000000
generations = 1000
```

`seed_fitness` is the initial selected-environment fitness of the seed lineage.
It is bounded to `[0, 1]`.

`seed_population` is the starting number of bacteria in the seed lineage. It
must be a positive integer.

`population_cap` is the environmental carrying limit caused by food, space, or
another resource. The population can temporarily exceed the cap before the cap
selection step tightens lineage sizes. It must be a positive integer and should
normally be greater than or equal to `seed_population`.

`generations` is the number of Mutation and Selection event pairs to run. It
must be a non-negative integer.

### Mutation Supply

```text
mutation_rate = 0.002
beneficial_mutation_rate = 0.001
harmful_mutation_rate = 0.1
lethal_mutation_rate = 0.01
compound_effect = 0.1
```

`mutation_rate` is the expected mutation pressure per bacterium per Mutation
event. It is the Poisson rate parameter:

```text
K ~ Poisson(lambda = mutation_rate)
```

where `K` is the number of new mutations acquired by one bacterium during one
Mutation event. For small values, `mutation_rate` is approximately the fraction
of bacteria that produce a new mutation-bearing lineage.

`beneficial_mutation_rate`, `harmful_mutation_rate`, and
`lethal_mutation_rate` define baseline category weights for a new mutation
before compound effects. They are normalized into category probabilities during
mutation assignment.

`compound_effect` increases category chances as the inherited mutation count
increases. Compound-adjusted category weights are normalized before use.

`standard_deviation` and the misspelled `standart_deviation` are not model
inputs. Mutation multiplicity is controlled by the Poisson
distribution implied by `mutation_rate`.

### Selection Process

```text
mutation_effect = 0.01
minimum_fitness = 0.4
randomness = 0.1
```

`mutation_effect` is the selected-environment effect size of one net beneficial
or harmful mutation count on the lineage fitness score.

`minimum_fitness` is the lower viability threshold. Lineages with fitness below
this value are removed during Selection.

`randomness` is a provisional survival-noise standard deviation. It should be
applied using `random_seed` so stochastic runs remain reproducible.

### Simulation Controls

```text
random_seed
max_runtime_seconds = 60
max_lineage_classes
```

`random_seed` is retained as a reproducibility control for Mutation and
Selection sampling.

`max_runtime_seconds` is a computational safety guard. The first implementation
should stop and return a clear runtime-limit error if one run takes more than
60 seconds.

`max_lineage_classes` remains available as a future computational safety
control. If it is used as a safety guard, exceeding it should return a clear
error rather than silently merging, truncating, or reweighting lineages.

### Input Validation

The implementation should reject invalid parameters with clear error
messages. It should not silently clip user inputs.

Initial validation rules:

```text
0 <= seed_fitness <= 1
seed_population is a positive integer
population_cap is a positive integer
generations is a non-negative integer
mutation_rate >= 0
0 <= beneficial_mutation_rate <= 1
0 <= harmful_mutation_rate <= 1
0 <= lethal_mutation_rate <= 1
compound_effect >= 0
mutation_effect >= 0 and finite
0 <= minimum_fitness <= 1
randomness >= 0
random_seed is an integer if supplied
max_runtime_seconds is positive
max_lineage_classes is a positive integer if supplied
all numeric inputs are finite
```

The baseline mutation category values are treated as weights. They do not need
to sum to one because the compound-adjusted values are normalized during
mutation category assignment.

## Lineage State

Each current lineage is an explicit record:

```text
lineage_id
generation_created
total_mutations
beneficial_mutations
harmful_mutations
lethal_mutations
size
fitness_score
```

`total_mutations`, `beneficial_mutations`, `harmful_mutations`,
`lethal_mutations`, and `size` are integer values.

`fitness_score` is a decimal value calculated from mutation counts. The current
formula can leave the `[0, 1]` range; this is a known limitation to revisit.

`harmful_mutations` counts mutations that reduce selected-environment fitness or
act as a simplified genome-integrity burden proxy. It does not count mutations
that benefit adaptation.

`lethal_mutations` counts lethal mutations inherited by the lineage. Any
lineage with `lethal_mutations > 0` is removed at the next Selection event.

Neutral mutations are implicit:

```text
neutral_mutations =
  total_mutations
  - beneficial_mutations
  - harmful_mutations
  - lethal_mutations
```

The generation 0 seed lineage is:

```text
lineage_id = 1
generation_created = 0
total_mutations = 0
beneficial_mutations = 0
harmful_mutations = 0
lethal_mutations = 0
size = seed_population
fitness_score = seed_fitness
```

## Lineage Counter

The lineage counter starts at `1` for the seed lineage at generation 0.

Each new mutation-bearing lineage increments the lineage counter by one. The
counter is cumulative. It is not reduced when a lineage dies.

No-mutation descendants remain part of their existing lineage and do not
increment the counter.

## Generation Loop

For each generation from `1` through `generations`:

```text
1. Apply the Mutation event independently to each current lineage.
2. Apply the Selection event to the resulting lineage array.
3. Record population, lineage, and fitness summary outputs.
```

If all lineages are removed, the population is collapsed. Later generations
should remain collapsed unless a future model explicitly adds rescue,
immigration, or reseeding.

## Mutation Event

The Mutation event is calculated independently for each current lineage.

For each bacterium in parent lineage `i`, draw the number of new mutations from
the Poisson distribution:

```text
K ~ Poisson(lambda = mutation_rate)
```

Aggregated across parent population `N_i`, this creates a mutation-count
allocation:

```text
n_i(k) = number of bacteria in lineage i that receive exactly k new mutations
k = 0, 1, 2, ...
sum_k n_i(k) = N_i
```

`n_i(0)` remains in the original lineage. For every bacterium counted in
`n_i(k)` where `k > 0`, the model creates one new lineage with starting
population size `1`.

Example target behavior:

```text
N_i = 100
mutation_rate = 0.1

possible allocation:
  original lineage size = 90
  9 new lineages with 1 new mutation
  1 new lineage with 2 new mutations
```

This example is an illustrative stochastic allocation. Under the Poisson model,
the expected allocation for `N_i = 100` and `mutation_rate = 0.1` is near 90.5
unmutated bacteria, 9.0 bacteria with one mutation, and 0.45 bacteria with two
mutations before integer sampling.

## Mutation Category Assignment

Each new mutation in a new lineage is assigned to one of four categories:

```text
beneficial
harmful
lethal
neutral
```

For a mutation added to a lineage with inherited mutation count
`total_mutations_before`, compound-adjusted category weights are:

```text
compound_multiplier =
  1 + total_mutations_before * compound_effect

beneficial_weight =
  beneficial_mutation_rate * compound_multiplier

harmful_weight =
  harmful_mutation_rate * compound_multiplier

lethal_weight =
  lethal_mutation_rate * compound_multiplier

neutral_weight = 1
normalization_denominator =
  neutral_weight
  + beneficial_weight
  + harmful_weight
  + lethal_weight
```

The category probabilities are:

```text
p_beneficial =
  beneficial_weight / normalization_denominator

p_harmful =
  harmful_weight / normalization_denominator

p_lethal =
  lethal_weight / normalization_denominator

p_neutral =
  neutral_weight / normalization_denominator
```

This normalization keeps probabilities finite and summing to one even when
compound effects make the non-neutral weights large.

After assigning the category, the lineage updates inherited counts:

```text
total_mutations += 1

if beneficial:
  beneficial_mutations += 1

if harmful:
  harmful_mutations += 1

if lethal:
  lethal_mutations += 1
```

Neutral mutations increase `total_mutations` but do not increase the beneficial,
harmful, or lethal counters.

## Selection Event

Selection is applied after the Mutation event.

### 1. Remove Lethal Lineages

Remove every lineage where:

```text
lethal_mutations > 0
```

### 2. Double Surviving Lineage Populations

For every remaining lineage:

```text
size = size * 2
```

This represents the next round of population growth before viability and
capacity filtering.

### 3. Calculate Fitness

For each remaining lineage, calculate fitness using the current linear formula:

```text
fitness_score =
  seed_fitness
  + (beneficial_mutations - harmful_mutations) * mutation_effect
```

This formula is intentionally kept simple for the first implementation. It can
produce values below `0` or above `1`; future review should decide how to keep
fitness within biological score boundaries without hiding useful model behavior.

### 4. Remove Low-Fitness Lineages

Remove every lineage where:

```text
fitness_score < minimum_fitness
```

### 5. Calculate Mean Fitness

The weighted mean fitness is:

```text
mean_fitness =
  sum_i(size_i * fitness_score_i)
  / sum_i(size_i)
```

For example:

```text
lineage A: fitness_score = 0.7, size = 5
lineage B: fitness_score = 0.6, size = 1

mean_fitness = (0.7 * 5 + 0.6 * 1) / 6 = 0.683333...
```

The model reports `mean_fitness` after low-fitness removal and before
population-cap selection. This follows the numbered selection process above and
keeps the reported mean from being inflated by cap-pressure reallocation.

The model also reports `post_cap_mean_fitness` for audit and debugging. This is
the population-weighted mean after population-cap selection changes lineage
sizes.

### 6. Apply Population-Cap Selection

If total surviving population is less than or equal to `population_cap`, no cap
selection is applied.

If total surviving population is greater than `population_cap`, the default is
linear soft selection:

```text
selection_weight_i =
  size_i * adjusted_fitness_i

target_size_i =
  population_cap
  * selection_weight_i
  / sum_j(selection_weight_j)
```

`adjusted_fitness_i` should initially be `fitness_score_i`. If survival
randomness is retained, it should perturb the selection weight in a documented,
bounded way before `target_size_i` is calculated.

Linear weighting is preferred over squaring fitness for the first rewrite
because it is the simpler soft-selection assumption. A squared or exponentiated
fitness rule may be added later as a named `selection_strength` parameter only
if the stronger selection pressure is scientifically justified and validated.

`target_size_i` must be converted back to integer population counts by rounding
to the closest integer. Independently rounded values may leave the final total
slightly above or below `population_cap`; this is accepted for the first
implementation.

This rule changes lineage shares. High-fitness lineages lose less population
share than low-fitness lineages and may increase their relative abundance. If
the intended behavior is that every lineage must shrink whenever the population
exceeds the cap, a different mortality rule is required.

### 7. Remove Empty Lineages

Remove every lineage where:

```text
size == 0
```

After this step, temporary candidate arrays, per-parent mutation allocations,
and removed-lineage records that are not needed for outputs should be discarded.
The implementation should keep only the current surviving lineages and compact
generation summaries needed for later calculations and display.

## Outputs

Each generation should record:

```text
generation
total_population
lineage_count_current
lineage_counter_cumulative
mean_fitness
post_cap_mean_fitness
best_fitness
dominant_lineage_fitness
beneficial_mutation_count_total
harmful_mutation_count_total
lethal_lineages_removed
low_fitness_lineages_removed
post_cap_lineages_removed
```

The final output should include:

```text
final_population
final_current_lineage_count
final_cumulative_lineage_counter
final_mean_fitness
final_best_fitness
final_dominant_lineage
collapsed
```

All outputs must be described as conditional on the selected assumptions.

## Mutation-Rate Range Metrics

The single run uses one `mutation_rate`. It does not by itself locate
`mu_min`, `mu_peak`, or `mu_max`.

Any future range estimate should run the generational model across a
sweep of `mutation_rate` values and, if stochastic choices remain, repeated
replicates. Wording must remain conditional, for example:

```text
Under the selected assumptions, repeated lineage runs suggest a high-performing
mutation-rate region near X.
```

Avoid:

```text
The optimal mutation rate is X.
```

## Runtime And Memory Safety

The explicit-lineage model can create many lineages. The implementation
should protect local runs from crashing:

```text
max_runtime_seconds = 60
```

If one run exceeds this limit, return a clear error rather than continuing
indefinitely.

The implementation should also avoid retaining data that is not needed to
proceed:

- discard temporary mutation-allocation arrays after each parent lineage is
  processed
- discard lethal, low-fitness, and zero-size lineage records after their summary
  counts are recorded
- store compact per-generation summaries rather than every intermediate
  candidate state
- avoid keeping duplicate copies of large lineage arrays during selection

If future memory or lineage-count limits are needed, they should return clear
errors rather than silently altering scientific results.

## Implementation Readiness

The following choices still deserve explicit review before later model changes:

- the exact rule for applying `randomness` during survival or cap selection
- how to keep the current linear fitness formula within intended boundaries
- whether mean fitness is reported before or after cap selection, or both
- whether cap selection should use linear soft selection or a strict shrinkage
  rule that reduces every lineage
- whether the 60-second runtime limit should be user configurable
