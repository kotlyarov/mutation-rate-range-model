# Known Limitations

This project is an exploratory scientific model, not a complete biological simulation.

## 1. It does not know the exact cost of every mutation

The model cannot calculate the exact fitness effect of every possible genomic change in *E. coli*.

Many mutation effects depend on:

environment
genetic background
epistasis
gene expression
metabolic state
population dynamics

The project uses empirical curves and uncertainty bands instead.

## 2. Genome-decay cost is partly subjective

Genome decay can be measured in several ways:

lost genes
lost metabolic functions
reduced fitness in alternative environments
deleterious load
reduced future adaptability

There is no single universal cost function.

The model exposes the decay penalty as a parameter rather than hiding it.

## 3. LTEE-like conditions are not all natural conditions

The LTEE is a powerful experiment, but it is a simplified laboratory environment.

A mutation-rate range that works in LTEE-like glucose-limited conditions may not apply to:

soil
gut microbiomes
fluctuating environments
host-pathogen interactions
small populations
sexually recombining organisms
large eukaryotic genomes

## 4. Mutation rate is not only one number

Different mutator mechanisms can change the mutation spectrum.

For example, one mutator may increase mostly transitions, while another may increase indels or structural changes.

The first model treats mutation rate mostly as a scalar multiplier, which is incomplete.

## 5. Epistasis is simplified

The first model uses nonlinear terms to approximate compound damage and interaction between mutations.

It does not infer a full genome-wide epistasis map.

A complete epistasis map would require enormous experimental data, including engineered combinations of mutations and growth measurements across environments.

## 6. Benefit and cost curves may be non-identifiable

Different parameter sets may produce similar net curves.

Therefore, the model must show:

uncertainty bands
sensitivity analysis
parameter provenance
warnings when results are underdetermined

## 7. The model may create false visual confidence

A GUI can make a weak model look authoritative.

Every chart must show:

assumptions
parameter source status
uncertainty
warnings

## 8. The model is not a proof about evolution in general

The project estimates mutation-rate trade-offs under specified assumptions.

It should not be used to claim a universal mutation-rate range for all life.

The result is conditional on:

organism
environment
population size
generation horizon
fitness definition
decay penalty

## 9. Data sources are related but not identical

The model may combine data from LTEE, mutator studies, mutation-accumulation studies, and controlled mutation-rate experiments.

These sources are not perfectly interchangeable.

The project must document when a parameter comes from a different environment, strain, or experimental design.

## 10. Initial model is deterministic

The first version uses deterministic curves.

This is useful for transparency but cannot capture all population-genetic dynamics, including:

drift
clonal interference
lineage extinction
hitchhiking
rare innovation events
mutation-rate modifier dynamics

Later versions should add stochastic simulation.

## 11. The model may fail to produce a clear optimum

Some parameter combinations may produce:

monotonic benefit
monotonic harm
flat net score
optimum outside tested range
extreme sensitivity to decay penalty

These are valid outcomes and must be reported.

## 12. It does not model Cit+ directly

The first version is about mutation-rate trade-offs and genome decay.

It does not directly model the evolution of aerobic citrate use.

Cit+ could be added later as a special rare-innovation module with:

potentiation
actualization
refinement
lineage survival

## 13. Parameter precision is limited

Even well-studied variables such as wild-type mutation rate, beneficial mutation supply, and deleterious DFE vary by strain, environment, measurement method, and time.

The project should use parameter ranges and uncertainty rather than single hard-coded constants.

## 14. Validation is initially qualitative

Early validation checks whether the model behaves consistently with known findings.

Quantitative validation requires curated datasets and careful fitting.

## 15. The model cannot replace experiments

The model can suggest plausible ranges and identify sensitive assumptions.

It cannot prove the true biological optimum without experimental validation.
