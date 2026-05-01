# Validation Plan

This document describes how the Mutation Rate Range Model should be validated.

## Validation philosophy

The model should be validated against qualitative and quantitative patterns, not just whether it produces a nice-looking peak.

The first question is:

```text
Do lineage trajectories behave plausibly under known biological constraints?
```

The later question is:

```text
Can the model reproduce empirical patterns within uncertainty?
```

## Current lineage-model validation

For the generational lineage-survival model, validation should focus on
mathematical checks, stochastic reproducibility checks, and behavioural checks.

### Mathematical checks

For valid parameter values:

- generation histories have expected length
- no NaN values
- no infinite values
- actual population size never exceeds effective population size
- actual population size can decline below effective population size
- mutation-class probabilities are finite and sum to one
- benefit and decay proxy are non-negative
- robustness is bounded between 0 and 1
- seeded stochastic runs are reproducible

### Behavioural checks

The model should be able to produce:

- no impossible fractional lineages at tiny effective population size
- beneficial lineage appearance and loss under rare-event assumptions
- beneficial lineage spread under favourable assumptions
- increasing decay proxy when deleterious mutation supply is high
- reduced robustness as decay proxy accumulates
- collapse or derailment under sufficiently harmful assumptions

The model should not force beneficial adoption when stochastic mutation and
survival sampling do not support it.

## Sensitivity analysis

Sensitivity analysis should test how outputs change when varying:

- `effective_population_size`
- `beneficial_mutation_rate`
- `neutral_mutation_rate`
- `deleterious_mutation_rate`
- `beneficial_effect_size`
- `decay_effect_size`
- `interference_strength`
- `interference_exponent`
- `robustness_decay_rate`
- `decay_fitness_penalty`
- `robustness_fitness_weight`
- `lethal_decay_threshold`
- `minimum_viable_robustness`
- `selection_strength`
- `viability_fitness_threshold`
- biological interpretation thresholds
- generation horizon

Report which parameters most affect:

- final mean fitness
- final best lineage fitness
- beneficial lineage survival
- beneficial adoption fraction
- total lineages evolved
- total lineages survived
- decay-led population size, when inspecting genome-decay behaviour specifically
- collapse / derailment frequency across repeated seeds

## Empirical validation later

Later versions should compare lineage trajectories against empirical data.

Potential comparisons:

- selected-environment fitness gain vs generation
- mutation accumulation vs generation
- differences between wild-type and mutator lineages
- performance in alternative environments
- long-term decay signatures

## Validation outputs

Create a validation report with:

```text
model version
parameter set
data sources, if any
plots
range estimates
sensitivity results
known failures
interpretation limits
```

## Failure modes to detect

The validation process should detect:

- peak exists only because of arbitrary thresholds
- high mutation rates are rewarded unrealistically
- decay proxy dominates all outputs immediately
- robustness term overwhelms benefit and decay
- model is insensitive to major biological assumptions
- GUI defaults imply false precision

## Safe validation language

Use:

```text
The model reproduces this qualitative pattern under these assumptions.
```

Avoid:

```text
The model proves this mutation rate is optimal.
```
