# Validation Plan

This document describes how the Mutation Rate Range Model should be validated.

## Validation philosophy

The model should be validated against qualitative and quantitative patterns, not just whether it produces a nice-looking peak.

The first question is:

```text
Do the curves behave plausibly under known biological constraints?
```

The later question is:

```text
Can the model reproduce empirical patterns within uncertainty?
```

## Version-one validation

For the deterministic first version, validation should focus on mathematical and behavioural checks.

### Mathematical checks

For valid parameter values:

- output arrays have expected shape
- no NaN values
- no infinite values
- benefit is non-negative
- decay proxy is non-negative
- robustness is bounded between 0 and 1
- net score changes when penalty weights change

### Behavioural checks

The model should be able to produce:

- slow adaptation at very low mutation rates
- increasing benefit at low-to-moderate mutation rates
- increasing decay proxy at higher mutation rates
- reduced robustness as decay proxy increases
- a net-score peak under some parameter sets
- monotonic or no-peak behaviour under other parameter sets if assumptions imply it

The model should not force a peak when the parameter choices do not support one.

## Sensitivity analysis

Sensitivity analysis should test how outputs change when varying:

- `alpha_benefit`
- `beta_interference`
- `gamma_interference`
- `decay_scale`
- `gamma_decay`
- `k_robustness`
- `lambda_decay`
- `rho_robustness`
- threshold fractions
- generation horizon

Report which parameters most affect:

- `mu_min`
- `mu_peak`
- `mu_max`
- peak score
- robustness at peak
- decay proxy at peak

## Empirical validation later

Later versions should compare model curves against empirical data.

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
