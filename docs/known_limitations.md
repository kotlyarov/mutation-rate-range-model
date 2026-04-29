# Known Limitations

This document lists known limitations of the current Mutation Rate Range Model.

## The model is exploratory

The lineage-survival model is intended to explore whether selected assumptions
produce plausible generational trajectories.

It does not estimate a true biological optimum.

## High-level mutation classes

The model splits new offspring into aggregate classes:

```text
no new mutation
neutral
harmful / decay
beneficial
mixed beneficial plus harmful
```

It does not know the exact cost or benefit of each possible mutation.

## Simplified genome decay

`D` is a scalar proxy.

It may combine several distinct biological processes:

- mutation accumulation
- deleterious load
- relaxed selection
- loss of conditionally useful functions
- reduced robustness
- genome degradation

These should not be treated as identical in scientific interpretation.

## Aggregated lineage classes, not individuals

The model tracks lineage classes with shared accumulated state. It does not
simulate every organism as a separate object.

This is deliberate for transparency and speed, but it means within-class
heterogeneity is hidden.

## Approximate merging at high class counts

If the number of surviving classes exceeds the advanced `max_lineage_classes`
simulation control, small classes are merged into a weighted aggregate state.

This prevents runaway class growth but can blur rare lineage details. Analyses
that depend on rare classes should check sensitivity to this limit.

## Simplified population genetics

The model includes stochastic mutation sampling and stochastic survival
selection, but it is still not a full Wright-Fisher, Moran, or experimental
transfer-process simulator.

It does not explicitly model:

- individual organisms
- nutrient dynamics
- carrying capacity
- culture volume
- serial-transfer dilution mechanics
- explicit fixation probabilities
- full clonal interference
- hitchhiking
- spatial structure
- mutation-spectrum evolution

Some effects may be approximated indirectly by parameters, but they are not
mechanistically simulated.

## Effective population size is only a cap

Each generation has at most `effective_population_size` survivors.

This captures integer stochasticity, lineage disappearance, and simple
population decline. It still does not model absolute population growth,
resource-dependent recovery, crash dynamics, or experimental extinction
protocols mechanistically.

## Event-rate assumptions are simple

Beneficial, harmful, and neutral events are treated as independent Poisson
arrivals before being collapsed into mutation classes.

This ignores correlations among mutation types, context dependence, repair
defects, structural variants, and changing distributions of fitness effects.

## Fitness is a transparent score

Fitness is calculated as:

```text
performance_fitness = max(0, 1 + B - decay_fitness_penalty * D)
robustness_modifier = max(0, 1 - robustness_fitness_weight * (1 - R))
fitness = performance_fitness * robustness_modifier
```

This is useful for exploring assumptions, but it is not a validated biological
fitness law. Separate viability gates can also remove lineages whose accumulated
decay exceeds `lethal_decay_threshold` or whose retained robustness falls below
`minimum_viable_robustness`.

## No validated mutation-rate optimum

A mutation-rate value that performs well in one run or one parameter set does
not apply universally.

The result may change with:

- environment
- effective population size
- generation horizon
- random seed
- beneficial event supply
- deleterious-load assumptions
- robustness weighting
- mutation spectrum
- survival strength
- collapse or adoption thresholds

## Sweep model is not implemented yet

The current primary implementation is a single-run lineage model.

A future mutation-rate sweep should run the same generational model repeatedly
across mutation-rate multipliers and random seeds before estimating an
assumption-dependent high-performing range.

## Risk of false precision

The GUI may make arbitrary parameters look authoritative.

To reduce this risk:

- display assumptions clearly
- avoid excessive decimal precision
- show stochastic outcomes and seeds
- label outputs as exploratory
- keep default parameters visibly provisional

## Risk of circular reasoning

If the model is tuned to produce a desired adoption or collapse pattern, it may
only confirm the modeller's assumptions.

Validation must compare model behavior against independent empirical patterns
where possible.

## Current safe interpretation

A safe interpretation is:

```text
Under these assumptions and this random seed, beneficial lineage adoption rose
while mean fitness remained above the selected collapse threshold.
```

An unsafe interpretation is:

```text
The model proves that evolution optimises mutation rate at this value.
```
