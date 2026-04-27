# Assumptions

This document lists the assumptions used by the mutation-rate range model.

The project must keep assumptions explicit. No assumption should be hidden inside code.

## A1. Mutation rate affects both beneficial and deleterious mutation supply

Increasing mutation rate increases the supply of potentially beneficial mutations, but also increases the supply of neutral, deleterious, and lethal mutations.

The model does not assume that mutation knows whether a future change will be useful.

## A2. Beneficial effect is environment-dependent

A mutation that improves growth in one environment may be neutral or harmful in another environment.

The first model focuses on an LTEE-like selected environment but includes a separate robustness term for alternative environments.

## A3. Selected-environment fitness and genome integrity are different outputs

A population can improve fitness in the selected environment while losing broader genomic functionality.

This is one of the main lessons from mutator genome decay research.

Therefore, the model tracks:

selected-environment benefit
genome decay
retained robustness
net score

## A4. Genome decay cost is not directly known

The cost of genome decay depends on what future environments or functions matter.

The model does not treat genome decay cost as a universal biological constant.

Instead, it exposes a decay penalty:

lambda_decay

Higher values mean that genome integrity and future robustness are considered more important.

## A5. Mutation-rate optimum is not universal

The optimal mutation-rate range depends on:

population size
environment
time horizon
genome size
mutation spectrum
distribution of fitness effects
epistasis
strength of selection
importance of alternative environments

The model estimates conditional ranges, not universal constants.

## A6. Exact per-mutation costs are not assumed

The model does not attempt to calculate the exact cost of every possible base-pair change.

Instead, it uses empirical or fitted curves:

benefit curve
decay curve
robustness curve
net curve

## A7. Curves must include uncertainty

Every major curve should be displayed with uncertainty bands where possible.

The model should prefer: range with uncertainty

over: single precise number

## A8. Early adaptation and late adaptation may differ

Beneficial mutations are usually more available early in adaptation and less available later.

The first deterministic model approximates this using saturating benefit curves.

Later versions may model time-varying beneficial opportunity explicitly.

## A9. High mutation rates can become harmful

The model assumes that high mutation rates may eventually reduce net performance through:

deleterious load
lethal mutations
genome decay
clonal interference
loss of robustness

This assumption is experimentally supported but the threshold is parameter-dependent.

## A10. Robustness is a proxy

The robustness curve is not a direct physical measurement.

It represents retained capacity to perform in alternative environments, withstand stress, and preserve future adaptability.

In early versions, robustness is modelled as a function of genome decay:

R(m, T) = exp(-kr * D(m, T))

This is a simplification.

## A11. Mutation spectrum is initially simplified

The first model treats mutation rate mostly as a scalar multiplier.

This is incomplete because different mutator mechanisms can produce different mutation spectra.

Later versions should distinguish:

base substitutions
insertions
deletions
structural variants
mobile-element insertions
repair-defect-specific spectra

## A12. Epistasis is initially coarse-grained

The first model does not infer all pairwise or higher-order genetic interactions.

Instead, nonlinear decay terms approximate compound damage and epistasis.

Later versions may add:

global epistasis
gene-category epistasis
synthetic-lethal risk
state-space hidden decay variables

## A13. Model parameters must have provenance

Every parameter must be labelled as one of:

source-backed
fitted
placeholder
sensitivity-only

Placeholder parameters must not be presented as established scientific values.

## A14. Qualitative validation is required before quantitative claims

The model must first reproduce qualitative expectations:

benefit increases at low mutation rate
decay increases with mutation rate
robustness decreases with decay
very high mutation rate can reduce net score
increasing decay penalty lowers the optimum

Only after these checks pass should quantitative ranges be discussed.

## A15. No theory-confirming tuning

Do not tune parameters to force a preferred conclusion.

If the model does not produce a clear optimum, or if the result depends heavily on an uncertain parameter, report that directly.