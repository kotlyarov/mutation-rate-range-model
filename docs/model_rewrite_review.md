# Lineage Rewrite Review Notes

This document records logical, mathematical, and scientific issues found while
translating the requested rewrite into documentation.

Status:

```text
implemented; remaining concerns require scientific review
```

## Summary

The lineage rewrite is now specified and implemented:

- mutation multiplicity uses a Poisson model
- `standard_deviation` and `standart_deviation` are removed
- compound-effect category weights are normalized
- `random_seed` is retained
- fitness uses the current linear formula
- population cap sizes are rounded to the closest integer
- runtime and lineage-count safety guards are implemented and documented
- harmful and lethal counts remain simplified proxies by design
- `mean_fitness` is recorded before population-cap reallocation, with
  `post_cap_mean_fitness` retained for audit

The remaining concerns are mostly about interpretation and implementation
details rather than missing math.

## Decisions Recorded

### 1. Mutation Multiplicity Uses Poisson

Decision:

```text
K ~ Poisson(lambda = mutation_rate)
```

`mutation_rate` is the expected number of new mutations per bacterium per
Mutation event. For small values it is approximately the fraction of bacteria
that mutate.

Concern:

Poisson variance equals the mean. If real mutation counts are overdispersed,
the model may understate rare multi-mutation descendants. A later model could
add a negative binomial distribution if this becomes important.

### 2. `standard_deviation` Is Removed

Decision:

`standard_deviation` and the misspelled `standart_deviation` are removed from
the input list. Mutation-count variability is now implied by the
Poisson distribution.

Concern:

Removing this input makes the first model clearer, but it removes a direct knob
for overdispersion. That is acceptable for a narrow first rewrite.

### 3. Compound Effects Are Normalized

Decision:

Compound effects create category weights:

```text
category_weight =
  base_category_rate * (1 + total_mutations * compound_effect)
```

Then the model normalizes beneficial, harmful, lethal, and neutral weights:

```text
p_category =
  category_weight / sum(all_category_weights)
```

with:

```text
neutral_weight = 1
```

Concern:

After normalization, `beneficial_mutation_rate`, `harmful_mutation_rate`, and
`lethal_mutation_rate` behave as relative weights rather than exact direct
probabilities. At high compound load, neutral mutations can become rare because
non-neutral weights dominate.

### 4. `random_seed` Is Retained

Decision:

`random_seed` remains a model control so stochastic Mutation and Selection
events can be reproduced.

Concern:

The implemented survival-noise rule perturbs cap-selection fitness weights with
normal noise. This should still be reviewed scientifically before treating
noisy outcomes as meaningful.

### 5. Fitness Uses The Current Linear Formula

Decision:

Fitness is calculated as:

```text
fitness_score =
  seed_fitness
  + (beneficial_mutations - harmful_mutations) * mutation_effect
```

The first implementation keeps this transparent formula and leaves boundary
handling for later review.

Concern:

This can produce values below `0` or above `1`. Future review should decide
whether clipping, a bounded link function, weaker boundary effects, or a
different fitness representation is scientifically preferable.

### 6. Population Counts Use Closest-Integer Rounding

Decision:

Cap-selection target sizes are rounded to the closest integer.

Concern:

Independent closest-integer rounding may not sum exactly to `population_cap`.
The first implementation allows the final total to go slightly above or below
the cap.

### 7. Runtime And Lineage-Count Protection Is Required

Decision:

The implementation stops a run with a clear error if it exceeds
`max_runtime_seconds` or `max_lineage_classes`. It also discards temporary
mutation arrays, removed lineages, and intermediate candidate states that are
not needed for future calculations or display.

Concern:

A time limit is hardware-dependent and the lineage-count guard does not fully
protect against sudden memory exhaustion. A later implementation may still need
a memory-budget error threshold.

### 8. Harmful And Lethal Counts Stay Simplified

Decision:

Harmful and lethal mutation counts remain as specified for the first rewrite.
They are kept simple rather than replaced with separate genome-integrity or
robustness state variables.

Concern:

This weakens the conceptual separation between selected-environment fitness and
genome integrity. The limitation should be visible in reports and GUI text.

### 9. The Single-Run Model Still Does Not Locate `mu_min`, `mu_peak`, Or `mu_max`

Decision:

The current inputs run one `mutation_rate` at a time.

Concern:

Range metrics require a sweep across mutation rates and repeated seeds. They
should not be reported from one run.

## Recommended Review Order

1. Review whether the implemented Normal cap-selection noise is biologically
   appropriate.
2. Decide how to keep linear fitness inside intended boundaries later.
3. Decide whether the cap rule should remain soft selection or become a strict
   shrinkage rule.
4. Decide how future mutation-rate sweeps should aggregate stochastic
   replicates.
