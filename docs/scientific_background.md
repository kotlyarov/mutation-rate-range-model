# Scientific Background

This document explains the biological motivation for the Mutation Rate Range
Model.

## Problem

Mutation is necessary for adaptation, but mutation is also costly.

A very low mutation rate can slow adaptation because beneficial variants appear
too rarely. A very high mutation rate can increase deleterious load, lethal
events, genome degradation, and loss of robustness. The interesting question is
not whether mutation is good or bad. The interesting question is whether there
are assumption-dependent regimes where adaptation can occur before mutation
burden dominates.

## Why Use An *E. coli*-Like Asexual Population?

The first reviewed model focuses on an *E. coli*-like asexual population
because:

- *E. coli* is experimentally well studied.
- LTEE data provides unusually long evolutionary time series.
- Asexual populations avoid complications from recombination.
- Mutator strains allow comparison between different mutation-rate regimes.
- Existing literature discusses trade-offs between adaptation and mutation
  burden.

This is not a claim that the model applies directly to all organisms.

## Key Idea

Selected-environment fitness and genome integrity are not the same thing.

A lineage may continue improving in the selected environment while losing
functions that are weakly selected, conditionally useful, or irrelevant in the
current environment. The current lineage model keeps selected-environment adaptation
visible through beneficial mutation counts and fitness score, while harmful and
lethal mutation counts act as simplified burden proxies.

This separation is still incomplete. A future model may need explicit
genome-integrity or robustness outputs beyond mutation counts.

## Relevant Empirical Themes

### Sustained Adaptation With Genome Decay

Hypermutable LTEE lineages can show sustained fitness gains in the selected
laboratory environment while also accumulating signatures of genome decay.

This motivates reporting selected-environment fitness separately from harmful,
lethal, and neutral mutation accumulation.

### High Mutation Rates Can Limit Adaptation

Experimental work with engineered *E. coli* mutation rates suggests that
increasing mutation rate is not always beneficial. At high enough rates, the
cost of deleterious and lethal mutations can limit adaptive evolution.

This motivates explicit mutation supply, harmful mutation probability, lethal
mutation probability, and minimum-fitness filtering.

### Mutation-Rate Evolution Is Context-Dependent

Theoretical work on rapidly adapting asexual populations shows that
mutation-rate evolution depends on population size, beneficial-mutation supply,
deleterious load, linkage, and adaptation dynamics.

This motivates reporting all results as conditional on assumptions.

## Model Implication

The model should not answer:

```text
What is the exact optimal mutation rate?
```

It should answer:

```text
Under these assumptions, what lineage trajectories occur for this mutation
rate?
```

## Why A Lineage Mutation-Selection Model?

The lineage rewrite moves away from using deterministic curves as the primary
model behavior because the previous formulas were too far from the intended
biological process.

A lineage mutation-selection model makes the following assumptions explicit:

- mutation-bearing descendants are produced generation by generation
- descendants inherit previous mutation counts
- beneficial, harmful, lethal, and neutral mutations are tracked separately
- lethal and low-fitness lineages are removed
- population pressure is applied when population exceeds a cap
- weighted mean fitness is calculated from surviving lineages

This is still a simplified model. It is easier to inspect than a full
population-genetic simulator, but it remains far from real bacterial evolution.

## Scientific Caution

The current lineage model is exploratory and uncalibrated.

It is intended to test whether assumptions produce biologically plausible
lineage trajectories, not to estimate a true biological optimum.
