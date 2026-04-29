# Assumptions

This document lists assumptions used by the current Mutation Rate Range Model.

## General assumptions

The model assumes:

- an *E. coli*-like asexual population
- mutation rate is represented as a multiplier relative to wild type
- one lineage run uses one fixed mutation-rate multiplier
- population size controls stochastic mutation and survival sampling
- selected-environment benefit and genome integrity remain conceptually separate
- outputs are exploratory trajectories, not exact biological measurements
- results are conditional on parameter choices and random seed

## Biological assumptions

### Asexual population

The model assumes no recombination.

This is useful for a simplified LTEE-like setting, but it limits generality.

### Constant selected environment

The selected environment is treated as stable across the generation horizon.

This allows selected-environment fitness gain to be modelled separately from
retained robustness.

### Mutation-rate multiplier

Mutation rate is represented as:

```text
mutation_rate_multiplier = mutation rate relative to wild type
```

The single-run lineage model does not evaluate mutation rate on the X axis.
Instead, it fixes the multiplier and tracks lineage survival over generations.

### Mutation classes

Each generation splits offspring into high-level classes:

```text
no new mutation
neutral mutation
harmful mutation / decay
beneficial mutation
mixed beneficial plus harmful mutation
```

These are aggregate classes. The model does not initially distinguish:

- point mutations
- indels
- structural variants
- spectrum changes
- context-dependent mutation biases

Later versions may separate mutation rate and mutation spectrum.

### Population size

Population size is modelled through integer stochastic sampling.

Tiny expected probabilities do not create fractional lineage classes. A rare
class appears only if a random mutation draw creates at least one offspring and
then a survival draw leaves at least one survivor.

### Adaptive benefit

Accumulated selected-environment benefit is represented as `B`.

Beneficial mutations add increments to inherited benefit until the configured
`benefit_scale` is reached. This is a saturation assumption, not a claim that
all beneficial mutations share one real effect size.

### Genome decay proxy

Accumulated harmful mutation pressure and genome-integrity loss are represented
by a scalar proxy:

```text
D
```

`D` is not a direct count of deleterious mutations and not a direct measurement
of lost genes.

### Robustness

Retained robustness is represented as:

```text
R = exp(-k_robustness * D)
```

It is a bounded proxy for the ability to retain performance outside the selected
environment.

### Interference

New beneficial effects are reduced by interference from inherited decay and, in
mixed cases, newly acquired harmful decay:

```text
interference_load = inherited_decay + new_harmful_decay
```

This is a transparent approximation. It is not a full clonal-interference,
epistasis, or distribution-of-fitness-effects model.

### Fitness

Lineage fitness is calculated from inherited state:

```text
fitness = max(0, 1 + B - lambda_decay * D + rho_robustness * (R - 1))
```

The starting generation has fitness 1.0. Selected-environment benefit, decay
proxy, and retained robustness remain separately reported even though survival
selection uses the combined fitness.

### Survival selection

Survival selection is stochastic. Candidate offspring classes are sampled from
the current lineage classes, then the next generation is sampled from
fitness-weighted candidate classes.

The model does not reset biological state each generation. Surviving classes
carry accumulated benefit, accumulated decay, robustness, and fitness forward.

## Modelling assumptions

### Aggregated lineage classes

The model tracks aggregated lineage classes rather than individual organisms.

This keeps the implementation transparent and fast enough for local exploration,
but it is still an approximation. If the number of surviving classes exceeds
`max_lineage_classes`, small classes are merged into a weighted aggregate class.

### Fixed surviving population size

Each generation is resampled to `population_size` survivors. The current model
does not simulate explicit resource growth, dilution protocols, culture volume,
or carrying-capacity dynamics.

### Seeded randomness

Runs are stochastic but can be reproduced with `random_seed`.

Changing the seed can change whether rare lineages appear, survive, or disappear.
Scientific interpretation should use repeated runs, especially once mutation-rate
sweeps are added.

### Defaults are not fitted values

Default parameters are placeholders for model exploration.

They must not be described as inferred from real data unless fitting code and
validation reports are later added.

## Reporting assumptions

Any result must include language similar to:

```text
Under the selected assumptions and random seed...
```

Do not report outputs as unconditional facts.

## Assumptions to revisit later

Later versions should revisit:

- mutation spectrum
- epistasis
- changing distribution of fitness effects
- explicit bottleneck and transfer protocols
- clonal interference
- drift calibration
- environmental change
- robustness across many alternative environments
- parameter fitting from empirical data
- uncertainty propagation across repeated seeds
