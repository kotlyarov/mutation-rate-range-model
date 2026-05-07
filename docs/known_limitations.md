# Known Limitations

This document lists known limitations of the current explicit lineage
mutation-selection model.

Status:

```text
implemented lineage model
exploratory and uncalibrated
```

## The Model Is Exploratory

The lineage model is intended to explore whether selected assumptions
produce plausible generational trajectories.

It does not estimate a true biological optimum.

## Remaining Scientific Review Points

Several implemented choices still need scientific review:

- whether the Normal cap-selection noise controlled by `randomness` is an
  appropriate survival proxy
- how to keep the current linear fitness formula inside intended boundaries
- whether harmful mutation count is sufficient as a genome-integrity proxy
- whether the cap-selection rule should stay as soft selection or become a
  strict shrinkage rule

These should be settled before later model-behavior changes.

## High-Level Mutation Categories

The model classifies mutations as:

```text
beneficial
harmful
lethal
neutral
```

It does not know the exact cost or benefit of each possible mutation.

The categories are selected-environment categories. A mutation that is
beneficial in the selected environment may be harmful elsewhere, and a mutation
that appears neutral in this model may matter under conditions not represented
here.

## Simplified Genome-Integrity Burden

The lineage rewrite removes the previous explicit `D` and `R` curve outputs
from the primary model. Harmful and lethal mutation counts become the main
genome-burden proxies.

This is simpler, but it weakens the separation between selected-environment
fitness and broader genome integrity. Future versions should consider explicit
genome-integrity or robustness outputs if that separation remains scientifically
central.

This limitation is accepted for the first explicit-lineage implementation to keep the model
simple, but reports should say that harmful and lethal counts are simplified
proxies rather than a full genome-integrity model.

## One Effect Size

The current fitness formula uses one `mutation_effect` for both beneficial and
harmful mutation counts:

```text
fitness_score =
  seed_fitness
  + (beneficial_mutations - harmful_mutations) * mutation_effect
```

This ignores distributions of fitness effects, diminishing returns, epistasis,
and mutation-specific consequences.

## Fitness Boundary Handling Is Unresolved

The current linear formula can produce `fitness_score` values below `0` or
above `1`.

This is accepted for the first implementation so the model behavior remains
transparent. Future review should decide whether to use clipping, a bounded
link function, different effect scaling, or a different fitness representation.

## Compound-Effect Normalization

The compound-effect formula can make raw category weights large:

```text
base_weight * (1 + total_mutations * compound_effect)
```

The model normalizes beneficial, harmful, lethal, and neutral weights
into valid probabilities. This prevents invalid probability sums, but it means
the input category rates are relative weights after compound effects, not exact
unconditional probabilities.

## Poisson Mutation Multiplicity

Mutation multiplicity is now specified as:

```text
K ~ Poisson(lambda = mutation_rate)
```

This is simple and standard, but it fixes the variance equal to the mean.
Overdispersed mutation processes would need a later model extension.

## Randomness And Reproducibility

`random_seed` is retained so stochastic Mutation and Selection choices can be
reproduced. The current survival-noise rule perturbs cap-selection fitness
weights with Normal noise and clips negative adjusted fitness to zero. The rule
is implemented, but its biological interpretation still needs review.

## Explicit Lineages Can Explode

Every mutation-bearing bacterium creates a new lineage. With large populations,
many generations, or high mutation rates, lineage counts can grow very quickly.

The safety guards are `max_runtime_seconds` and `max_lineage_classes`, plus
explicit discarding of temporary arrays and removed lineages. That reduces crash
risk but does not guarantee memory safety on every machine.

## Lineage Classes Are Not Full Family Trees

The final lineage table reports current surviving lineage classes, not all
descendants of a founding cell grouped as one family. Lineage id `1` is only
the exact unmutated seed lineage; when one of its bacteria mutates, that
descendant is assigned a new lineage id.

## Simplified Population Genetics

The model is not a full Wright-Fisher, Moran, branching-process, or
experimental transfer simulator.

It does not explicitly model:

- individual genome sequences
- nutrient dynamics
- lag phase or growth curves
- culture volume
- serial-transfer dilution mechanics
- fixation probabilities
- clonal interference
- hitchhiking
- spatial structure
- mutation-spectrum evolution
- repair-pathway evolution

## Population Cap Is A Simple Selection Proxy

The cap step uses fitness-weighted allocation when total population
exceeds `population_cap`.

This is a simple soft-selection proxy. It is not a mechanistic resource model.
Depending on the final formula, high-fitness lineages may increase relative
abundance even while the total population is capped.

## No Validated Mutation-Rate Optimum

A mutation-rate value that performs well in one run or one parameter set does
not apply universally.

The result may change with:

- seed fitness
- seed population
- population cap
- generation horizon
- mutation supply assumptions
- compound effect
- mutation effect
- minimum fitness threshold
- survival randomness
- category normalization rule
- cap-selection rule
- runtime limit
- lineage-count limit

## Risk Of False Precision

The GUI may make arbitrary parameters look authoritative.

To reduce this risk:

- display assumptions clearly
- avoid excessive decimal precision
- label outputs as exploratory
- show reviewed model choices and remaining limitations
- keep default parameters visibly provisional

## Risk Of Circular Reasoning

If the model is tuned to produce a desired adaptation or collapse pattern, it
may only confirm the modeller's assumptions.

Validation must compare model behavior against independent empirical patterns
where possible.

## Current Safe Interpretation

A safe interpretation is:

```text
Under these assumptions, this run produced surviving lineages with higher
weighted mean selected-environment fitness.
```

An unsafe interpretation is:

```text
The model proves that evolution optimises mutation rate at this value.
```
