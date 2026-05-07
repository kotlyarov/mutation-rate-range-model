# References

This document lists references and data sources relevant to the Mutation Rate Range Model.

## Core empirical references

### Couce et al. 2017

Couce, A., Caudwell, L. V., Feinauer, C., Hindré, T., Feugeas, J.-P., Weigt, M., Lenski, R. E., Schneider, D., & Tenaillon, O. (2017). *Mutator genomes decay, despite sustained fitness gains, in a long-term experiment with bacteria*. Proceedings of the National Academy of Sciences, 114(43), E9026-E9035.

DOI:

```text
10.1073/pnas.1705887114
```

Project relevance:

- motivates separating selected-environment fitness gain from genome integrity
- supports the idea that hypermutable lineages can continue adapting while accumulating genome decay

### Sprouffske et al. 2018

Sprouffske, K., Aguilar-Rodríguez, J., Sniegowski, P., & Wagner, A. (2018). *High mutation rates limit evolutionary adaptation in Escherichia coli*. PLOS Genetics, 14(4), e1007324.

DOI:

```text
10.1371/journal.pgen.1007324
```

Project relevance:

- provides experimental evidence that high mutation rates can limit adaptation
- includes engineered *E. coli* strains with different mutation rates
- includes growth measures in the original environment and many novel chemical environments

### Good & Desai 2016

Good, B. H., & Desai, M. M. (2016). *Evolution of Mutation Rates in Rapidly Adapting Asexual Populations*. Genetics, 204(3), 1249-1266.

DOI:

```text
10.1534/genetics.116.193565
```

Project relevance:

- provides theoretical background for mutation-rate evolution in rapidly adapting asexual populations
- motivates caution around clonal interference, linkage, and population-genetic context

### Ascensao et al. 2026

Ascensao, J. A., Yu, Q., et al. (2026). *The evolution of genetic drift over
50,000 generations*. bioRxiv preprint.

DOI:

```text
10.64898/2026.01.25.701616
```

Project relevance:

- provides background for future review of drift and stochastic survival
  assumptions
- is not currently used to fit the lineage app's `randomness` input

### Human Population Genetics and Genomics selection chapter

Pritchard Lab. *Natural selection: background and models*. Human Population
Genetics and Genomics, chapter 2.5.

URL:

```text
https://web.stanford.edu/group/pritchardlab/HGbook/Release-2023-09/HGBook-2023-09-chapters/HGBook-2023-09-23-ch2.5.pdf
```

Project relevance:

- motivates the simple soft-selection assumption that post-selection
  frequencies are proportional to pre-selection frequency times relative fitness
- motivates keeping deterministic expectations separate from random drift or
  Wright-Fisher sampling

## LTEE resources

### Long-Term Evolution Experiment website

The LTEE website provides publications and resources related to the long-running *E. coli* evolution experiment.

URL:

```text
https://the-ltee.org/
```

Project relevance:

- source of relevant publications
- source for mutation-finder and data resources
- context for long-term empirical evolution in *E. coli*

### LTEE resources page

URL:

```text
https://the-ltee.org/resources/
```

Project relevance:

- entry point for LTEE Mutation Finder and related resources

## Additional useful references

### Wielgoss et al. 2011

Wielgoss, S., Barrick, J. E., Tenaillon, O., Wiser, M. J., Dittmar, W. J., Cruveiller, S., Chane-Woon-Ming, B., Médigue, C., Lenski, R. E., & Schneider, D. (2011). *Mutation Rate Inferred From Synonymous Substitutions in a Long-Term Evolution Experiment With Escherichia coli*. G3: Genes, Genomes, Genetics, 1(3), 183-186.

DOI:

```text
10.1534/g3.111.000406
```

Project relevance:

- provides mutation-rate inference from LTEE genomic data
- useful for wild-type baseline discussion

### Good et al. 2017

Good, B. H., McDonald, M. J., Barrick, J. E., Lenski, R. E., & Desai, M. M. (2017). *The dynamics of molecular evolution over 60,000 generations*. Nature, 551, 45-50.

DOI:

```text
10.1038/nature24287
```

Project relevance:

- useful for long-term mutation accumulation and molecular-evolution dynamics in LTEE

## Notes for future data work

Before using any dataset, record:

- source URL
- access date
- license or usage terms
- data version or commit hash if available
- preprocessing steps
- columns used
- known caveats

Do not silently mix datasets with different assumptions or measurement methods.
