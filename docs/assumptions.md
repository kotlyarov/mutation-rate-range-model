# Assumptions

This document lists assumptions for the current explicit lineage
mutation-selection model.

Status:

```text
implemented lineage model
exploratory and uncalibrated
```

## General Assumptions

The model assumes:

- an *E. coli*-like asexual population
- one stable selected environment during the run
- one seed lineage at generation 0
- integer population sizes and explicit lineage records
- generation-by-generation Mutation and Selection events
- results are exploratory trajectories, not exact biological measurements
- results are conditional on parameter choices and unresolved modelling choices

The model must not imply that it has found a true universal optimal mutation
rate.

## Biological Assumptions

### Asexual Population

The model assumes no recombination.

This is useful for a simplified LTEE-like setting, but it limits generality.

### Constant Selected Environment

The selected environment is treated as stable across the generation horizon.

Fitness is therefore a selected-environment score. It is not a general measure
of performance across all environments.

### Seed Fitness

`seed_fitness` is the selected-environment fitness of the founding lineage.

The default value is provisional. It is not fitted to data.

### Mutation Supply

`mutation_rate` controls the expected number of new mutations per bacterium
during the Mutation event.

For small values, `mutation_rate` can be read approximately as the fraction of
the lineage that mutates in one event. For larger values or for multiple
mutations per descendant, it must be treated as a count-distribution parameter,
not a simple percent.

Mutation multiplicity is modelled as:

```text
K ~ Poisson(lambda = mutation_rate)
```

### Mutation Categories

Each new mutation is classified as:

```text
beneficial
harmful
lethal
neutral
```

These are high-level categories. The model does not initially distinguish:

- point mutations
- indels
- structural variants
- repair-pathway changes
- mutation-spectrum shifts
- mutation context
- gene-specific effects

### Beneficial Mutations

Beneficial mutations increase selected-environment fitness through the current
linear fitness formula.

This does not mean every beneficial mutation has the same true biological
effect. It is a first-pass scoring assumption.

### Harmful Mutations

Harmful mutations reduce selected-environment fitness through the current
linear fitness formula.

They also serve as a simplified genome-integrity burden proxy. This proxy is
not a literal count of every biologically damaging event and does not separate
all possible costs.

### Lethal Mutations

Any lineage with one or more lethal mutations is removed at the next Selection
event.

This makes lethality a lineage-level viability gate rather than a gradual
fitness penalty.

### Neutral Mutations

Neutral mutations increase `total_mutations` but do not directly alter the
fitness formula.

They can still affect future mutation-category probabilities through the
compound-effect formula because they contribute to `total_mutations`.

### Compound Effect

The compound-effect formula increases the raw category weights as the
inherited mutation count grows:

```text
category_weight =
  base_category_rate * (1 + total_mutations * compound_effect)
```

The resulting beneficial, harmful, lethal, and neutral weights are normalized
to probabilities before category assignment.

This assumes that lineages with more accumulated mutations become more likely
to produce beneficial, harmful, or lethal category assignments. The assumption
is biologically strong, and normalization changes the category rates from direct
probabilities into relative weights.

### Fitness

Fitness is calculated with the current linear formula:

```text
fitness_score =
  seed_fitness
  + (beneficial_mutations - harmful_mutations) * mutation_effect
```

This is deliberately simple. It can produce values outside `[0, 1]`, so future
model review should decide how to keep fitness within intended score boundaries
without masking useful behavior.

### Population Growth

After lethal filtering, surviving lineage populations double during Selection:

```text
size = size * 2
```

The model does not yet simulate nutrient concentration, lag phase, growth-rate
curves, culture volume, or serial-transfer dilution.

### Minimum Fitness

Lineages with:

```text
fitness_score < minimum_fitness
```

are removed.

This is a hard viability threshold, not a fitted experimental extinction rule.

### Population Cap

If the total population exceeds `population_cap`, the default is linear soft
selection:

```text
selection_weight = size * fitness_score
```

The cap is then allocated across lineages in proportion to selection weights.

This is preferred over squaring fitness in the first rewrite because it is
simpler and less aggressive. A stronger exponent should be added only as a
named, reviewed parameter.

### Randomness

The requested `randomness` parameter is intended to make survival less
deterministic.

The exact rule is not defined yet. Any stochastic use of `randomness` should use
the retained `random_seed` so runs can be reproduced.

## Modelling Assumptions

### Explicit Lineages

The current lineage model tracks explicit lineages rather than aggregated lineage
classes.

This makes lineage accounting easier to understand but can cause explosive
lineage growth. The implementation includes a 60-second runtime
limit and should discard temporary arrays and removed lineages once their
summary counts have been recorded.

### Integer Population Counts

All lineage sizes are integer counts.

Any proportional cap selection must therefore use documented closest-integer
rounding. The rounded total may be slightly above or below `population_cap`.

### Mean Fitness

Mean fitness is population-weighted:

```text
mean_fitness =
  sum(size * fitness_score) / sum(size)
```

`mean_fitness` is measured after lethal and low-fitness lineages are removed,
but before population-cap selection is applied. If cap selection changes lineage
composition, `post_cap_mean_fitness` records the population-weighted mean after
that cap step.

### Defaults Are Not Fitted Values

Default parameters are placeholders for model exploration.

They must not be described as inferred from real data unless fitting code and
validation reports are later added.

## Reporting Assumptions

Any result must include language similar to:

```text
Under the selected assumptions...
```

If stochastic choices remain, use:

```text
Under the selected assumptions and this run...
```

Do not report outputs as unconditional facts.

## Assumptions To Revisit Later

Later versions should revisit:

- alternatives to the Poisson mutation multiplicity assumption
- biological effects of category-probability normalization
- survival randomness and reproducibility
- boundary handling for the current linear fitness formula
- separate genome-integrity outputs beyond harmful mutation counts
- changing distributions of fitness effects
- epistasis
- clonal interference
- genetic drift
- explicit bottleneck and transfer protocols
- nutrient and carrying-capacity dynamics
- environmental change
- robustness across alternative environments
- parameter fitting from empirical data
- uncertainty propagation across repeated runs
