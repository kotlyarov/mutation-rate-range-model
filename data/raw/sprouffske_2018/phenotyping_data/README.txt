###############################################################################
Author:         Kathleen Sprouffske
Date:           4 July, 2017
Overview:       The data collected for phenotyping the 8 evolving replicates 
                from the S, M, L, and XL strains are described below.
###############################################################################

biolog.txt:
  strain:       S,M,L,X for strains with increasing mutation rates,
  rep:          0 is the ancestor strain and 1-8 are independent 
                evolutionary replicates,
  gen:          number of generations of evolution at measurement,
  abs_time:     hours of incubation in the biolog plate of the 
                absorbance reading,
  biolog_plate: Biolog plate identifier (plates have different chemicals),
  biolog_well:  the row letter and column number for the well,
  chemical:     the chemical provided in the well (several wells have the same
                chemical, the concentration increases as you move to the 
                right in the plate),
  abs600:       the raw absorbance reading at 600 nm

cell-density.txt:
  strain:       S,M,L,X for strains with increasing mutation rates,
  rep:          0 is the ancestor strain and 1-8 are independent 
                evolutionary replicates,
  gen:          number of generations of evolution at measurement,
  density:      number of cells / mL, determined by counting the number of
                cells on an agar plate, multiplied by the dilution used, and 
                divided by volume plated

growth-curves.txt:
  strain:       S,M,L,X for strains with increasing mutation rates,
                and k (where k is E. coli K12 wildtype)
  rep:          0 is the ancestor strain and 1-8 are independent 
                evolutionary replicates,
  gen:          number of generations of evolution at measurement,
  batch:        growth curves from the same experimental batch are comparable,
  r:            the "growth rate" r from fitting the growth curve data to the
                logistic curve (Nt = k / [(1 + (k - N0)/ N0) e^(-rt)],
  k,            the "carrying capacity" k from fitting the growth curve data 
                to the logistic curve, 
  n0,           the "initial population size" n0 from fitting the 
                growth curve data to the logistic curve,
  auc:          "area under the growth curve" from experimental measurements,
  sigma:        a measure of goodness of fit - smaller values are better 
                (see Sprouffske & Wagner, 2016, BMC Bioinformatics 17: 172)

mutation-rates.txt:
  strain:       S,M,L,X for strains with increasing mutation rates,
  rep:          0 is the ancestor strain and 1-8 are independent 
                evolutionary replicates,
  gen:          number of generations of evolution at measurement,
  u:            mutation rate to rifampicin, per generation,
  interval:     type of confidence intervals (Gerrish 2008, Genetics 180:1773)
  confLo,       95% confidence intervals,
  confHi,       95% confidence intervals,
  credLo,       95% credibility intervals,
  credHi        95% credibility intervals

phenotypes.txt:
  strain:       S,M,L,X for strains with increasing mutation rates, 
                and k,b (where k is E. coli K12 and b is a blank well)
  rep:          0 is the ancestor strain and 1-8 are independent 
                evolutionary replicates,
  gen:          number of generations of evolution at measurement,
  batch:        measurements made in the same batch are comparable,
  environment:  nitro, pH, or control for plates with medium containing
                nitrofurantoin, acidic pH, or control plates with the standard
                medium,
  concentration: the concentration of nitrofurantoin / or the pH of the medium,
  abs600:       the raw absorbance reading at 600 nm after 24 hours of growth
