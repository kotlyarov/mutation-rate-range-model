# Scientific Background

This document explains the biological motivation for the Mutation Rate Range Model.

## Problem

Mutation is necessary for adaptation, but mutation is also costly.

A very low mutation rate can slow adaptation because beneficial variants appear too rarely. A very high mutation rate can increase deleterious load, genome degradation, and loss of robustness. The interesting question is not whether mutation is good or bad. The interesting question is whether there is a mutation-rate range where adaptation remains strong while long-term genomic damage is not yet dominant.

## Why use an *E. coli*-like asexual population?

The first version focuses on an *E. coli*-like asexual population because:

- *E. coli* is experimentally well studied.
- LTEE data provides unusually long evolutionary time series.
- Asexual populations avoid complications from recombination.
- Mutator strains allow comparison between different mutation-rate regimes.
- Existing literature already discusses trade-offs between adaptation and mutation burden.

This is not a claim that the model applies directly to all organisms.

## Key idea

Selected-environment fitness and genome integrity are not the same thing.

A lineage may continue improving in the selected environment while losing functions that are weakly selected, conditionally useful, or irrelevant in the current environment. This is one reason the model separates selected-environment adaptive benefit from genome-decay or robustness-loss proxies.

## Relevant empirical themes

### Sustained adaptation with genome decay

Hypermutable LTEE lineages can show sustained fitness gains in the selected laboratory environment while also accumulating signatures of genome decay.

This motivates separate model outputs:

```text
selected-environment fitness gain
genome-decay proxy
retained robustness
```

### High mutation rates can limit adaptation

Experimental work with engineered *E. coli* mutation rates suggests that increasing mutation rate is not always beneficial. At high enough rates, the cost of deleterious mutations can limit adaptive evolution.

This motivates a net-score curve that can peak and then decline.

### Mutation-rate evolution is context-dependent

Theoretical work on rapidly adapting asexual populations shows that mutation-rate evolution depends on population size, beneficial-mutation supply, deleterious load, linkage, and adaptation dynamics.

This motivates reporting all results as conditional on assumptions.

## Model implication

The model should not answer:

```text
What is the exact optimal mutation rate?
```

It should answer:

```text
Under these assumptions, what mutation-rate range produces plausible benefit, cost, and robustness trade-offs?
```

## Why curve-based modelling first?

A full model would require:

- distributions of fitness effects
- changing environments
- epistasis
- clonal interference
- genetic drift
- population bottlenecks
- lineage-specific mutator dynamics
- uncertainty in empirical measurements

The first model deliberately avoids this complexity. It starts with transparent deterministic curves so that assumptions are visible and easy to challenge.

## Scientific caution

The first model is exploratory. It is intended to test whether assumptions produce biologically plausible curve shapes, not to estimate a true biological optimum.
