# Validation Plan

This document describes how the current explicit lineage mutation-selection
model should be validated.

Status:

```text
implemented lineage model
exploratory and uncalibrated
```

## Validation Philosophy

The model should be validated against qualitative and quantitative patterns, not
just whether it produces an attractive adaptation curve.

The first question is:

```text
Do lineage trajectories behave plausibly under known biological constraints?
```

The later question is:

```text
Can the model reproduce empirical patterns within uncertainty?
```

## Review Before Further Model Changes

Before code changes, review and settle:

- biological interpretation of the implemented Normal cap-selection noise
- whether harmful mutation count is sufficient as a genome-integrity proxy
- how to keep the current linear fitness formula inside intended boundaries
- whether the soft cap-selection rule should remain or be replaced with a
  strict shrinkage rule

## Mathematical Checks

For valid parameter values:

- generation histories have expected length
- lineage sizes are integers
- lineage sizes are never negative
- total population remains finite after cap selection
- no NaN values are produced
- no infinite values are produced
- `fitness_score` values are finite
- mutation category probabilities are finite and valid
- mutation category probabilities sum to one after normalization
- `neutral_mutations` is never negative
- cumulative lineage counter never decreases
- current lineage count never exceeds cumulative lineage counter
- original lineage population is non-negative and never exceeds total population
- weighted mean fitness matches lineage sizes and fitness scores
- post-cap closest-integer rounding produces integer lineage sizes
- seeded stochastic runs are reproducible
- runs stop with a clear error if `max_runtime_seconds` is exceeded
- collapsed runs stay collapsed unless reseeding is explicitly added

## Behavioural Checks

The model should be able to produce:

- no mutation-bearing lineages when `mutation_rate = 0`
- mostly seed-lineage descendants when mutation supply is very low
- beneficial lineage appearance under favorable mutation supply
- beneficial lineage loss under unfavorable selection or low population
- harmful accumulation under high harmful mutation probability
- lethal-lineage removal when lethal mutations occur
- collapse under sufficiently harmful assumptions
- cap-driven selection that favors higher-fitness lineages
- different trajectories when survival noise is enabled

The model should not force beneficial adaptation when mutation and selection
assumptions do not support it.

## Sensitivity Analysis

Sensitivity analysis should test how outputs change when varying:

- `seed_fitness`
- `seed_population`
- `population_cap`
- `generations`
- `mutation_rate`
- `beneficial_mutation_rate`
- `harmful_mutation_rate`
- `lethal_mutation_rate`
- `compound_effect`
- `mutation_effect`
- `minimum_fitness`
- `randomness`
- `random_seed`
- `max_runtime_seconds`
- `max_lineage_classes`
- cap-selection rule
- closest-integer rounding rule

Report which parameters most affect:

- final population
- final current lineage count
- cumulative lineage counter
- final weighted mean fitness
- final best fitness
- dominant lineage fitness
- total beneficial mutation count
- total harmful mutation count
- lethal lineage removals
- low-fitness lineage removals
- collapse frequency across repeated seeds
- runtime-limit failures
- lineage-count-limit failures

## Empirical Validation Later

Later versions should compare trajectories against empirical data.

Potential comparisons:

- selected-environment fitness gain vs generation
- population persistence or collapse under high mutation rates
- mutation accumulation vs generation
- differences between wild-type and mutator lineages
- performance in alternative environments
- long-term decay signatures

## Validation Outputs

Create a validation report with:

```text
model version
parameter set
reviewed model choices
data sources, if any
plots
sensitivity results
known failures
interpretation limits
```

Do not present fitted or default parameters as biologically validated unless the
validation report supports that claim.

## Failure Modes To Detect

The validation process should detect:

- fitness leaves the intended `[0, 1]` score range too often
- compound-effect normalization makes neutral mutations vanish too quickly
- high mutation rates are rewarded unrealistically
- lethal mutations dominate all outputs immediately
- lineages grow beyond practical memory limits
- runs hit runtime or lineage-count limits for ordinary parameter sets
- cap selection produces unintuitive increases or losses
- survival randomness overwhelms fitness
- model is insensitive to major biological assumptions
- GUI defaults imply false precision

## Safe Validation Language

Use:

```text
The model reproduces this qualitative pattern under these assumptions.
```

Avoid:

```text
The model proves this mutation rate is optimal.
```
