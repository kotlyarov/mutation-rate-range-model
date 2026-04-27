# Known Limitations

This document lists known limitations of the first deterministic version of the Mutation Rate Range Model.

## The model is exploratory

The first model is intended to test whether assumptions produce biologically plausible curve shapes.

It does not estimate a true biological optimum.

## No exact mutation effects

The model does not know the exact cost or benefit of each possible mutation.

Instead, it uses aggregate curves for:

```text
adaptive benefit
mutation-accumulation / genome-decay proxy
retained robustness
net score
```

## Simplified genome decay

`D(m, T)` is a scalar proxy.

It may combine several distinct biological processes:

- mutation accumulation
- deleterious load
- relaxed selection
- loss of conditionally useful functions
- reduced robustness
- genome degradation

These should not be treated as identical in scientific interpretation.

## No explicit population genetics in version one

The first version does not explicitly model:

- individual organisms
- genetic drift
- fixation probabilities
- clonal interference
- population bottlenecks
- hitchhiking
- lineage structure
- extinction risk

Some of these effects may be approximated indirectly by parameters, but they are not simulated.

## No real-data fitting yet

Until fitting and validation code exist, parameters are exploratory.

The model should not claim that defaults are empirically estimated.

## No mutation spectrum

The first model treats mutation rate as a single multiplier.

It does not distinguish:

- transitions
- transversions
- indels
- structural variants
- DNA repair defects
- context-dependent mutation biases
- mutation-spectrum evolution

## No environment switching

The selected environment is treated as stable.

The robustness term is only a proxy for performance outside the selected environment.

## No universal optimum

A mutation-rate range estimated under one parameter set does not apply universally.

The result may change with:

- environment
- population size
- generation horizon
- benefit distribution
- deleterious-load assumptions
- robustness weighting
- mutation spectrum
- threshold choices

## Risk of false precision

The GUI may make arbitrary parameters look authoritative.

To reduce this risk:

- display assumptions clearly
- avoid excessive decimal precision
- show sensitivity analysis
- label outputs as exploratory
- keep default parameters visibly provisional

## Risk of circular reasoning

If the model is tuned to produce a desired peak, it may only confirm the modeller's assumptions.

Validation must compare curve behaviour against independent empirical patterns where possible.

## Current safe interpretation

A safe interpretation is:

```text
Under these assumptions, the model produces a plausible trade-off curve with a peak in this approximate range.
```

An unsafe interpretation is:

```text
The model proves that evolution optimises mutation rate at this value.
```
