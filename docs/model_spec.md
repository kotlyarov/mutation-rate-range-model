# Model Specification

## Project name

Mutation Rate Range Model

## Purpose

Build a reproducible local model to estimate the mutation-rate range in which an *E. coli*-like asexual population can improve selected-environment fitness over long periods without excessive genome decay.

The model should be useful for reasoning about LTEE-like evolution and mutator trade-offs.

## Central research question

What mutation-rate range allows long-term adaptive improvement while keeping deleterious load and genome decay below a chosen cost threshold?

## Scientific background

This project is based on the following scientific observations:

1. Mutation rate can accelerate adaptation by increasing the supply of beneficial mutations.
2. Mutation rate also increases deleterious and lethal mutation supply.
3. Hypermutator lineages can gain selected-environment fitness while accumulating genome decay.
4. Very high mutation rates can limit adaptation.
5. The optimal or viable mutation-rate range depends on population size, environment, time horizon, DFE, and decay penalty.

## Model philosophy

Do not attempt to calculate the exact effect of every possible genomic change.

Instead, model empirical curves:

Benefit curve:
  mutation rate -> selected-environment fitness gain

Cost curve:
  mutation rate -> genome decay / deleterious load

Robustness curve:
  mutation rate -> retained alternative-environment capacity

Net curve:
  benefit - weighted cost + robustness value

Use uncertainty bands rather than false precision.

## Main variables

mu0       wild-type mutation rate
m         mutation-rate multiplier relative to wild type
mu        mu0 * m

T         number of generations
Ne        effective population size

Ub        beneficial mutation rate per genome per generation
Ud        deleterious mutation rate per genome per generation
Ul        lethal mutation rate per genome per generation

B(m, T)   selected-environment adaptive benefit
D(m, T)   genome-decay / deleterious-load cost
R(m, T)   retained robustness / alternative-environment capacity
S(m, T)   net long-term score

## First deterministic model

Use a deliberately simple first model.

B(m, T) = Bmax * (1 - exp(-kb * m * T)) * exp(-hb * max(0, m - m_burn)^p)

Interpretation:

* At low mutation rates, more mutations increase adaptive opportunity.
* Benefit saturates as adaptation approaches a local limit.
* At high mutation rates, deleterious load, clonal interference, or mutation burden can reduce realised adaptation.

Parameters:

Bmax    maximum selected-environment adaptive benefit
kb      adaptation benefit coefficient
hb      high-mutation-rate harm coefficient
m_burn  mutation-rate multiplier where high-rate harm begins
p       high-rate harm curvature

## Genome-decay curve:

D(m, T) = kd * (m^alpha) * T + ke * (m^beta) * (T^gamma)

Interpretation:

* Genome decay increases with mutation rate and time.
* The second term allows nonlinear accumulation caused by epistasis, hitchhiking, or compounding damage.

Parameters:

kd      linear decay coefficient
ke      nonlinear / epistatic decay coefficient
alpha   mutation-rate exponent for linear decay
beta    mutation-rate exponent for nonlinear decay
gamma   time exponent for nonlinear decay

## Robustness curve

R(m, T) = exp(-kr * D(m, T))

Interpretation:

* Robustness decreases as decay accumulates.
* Robustness represents retained ability to handle alternative environments, stress, or future adaptation.

Parameters:

kr      robustness-loss coefficient

## Net score

S(m, T) = B(m, T) - lambda_decay * D(m, T) + rho_robustness * R(m, T)

Interpretation:

* Selected-environment fitness is good.
* Genome decay is bad.
* Retained robustness is good.

Parameters:

lambda_decay   penalty weight for genome decay
rho_robustness value weight for retained robustness

## Mutation-rate range outputs

For each parameter set, calculate:

mu_min:
  lowest mutation-rate multiplier where net score becomes meaningfully positive

mu_peak:
  mutation-rate multiplier where net score is maximal

mu_max:
  highest mutation-rate multiplier before net score falls below acceptable threshold

If no internal optimum exists, report that directly.

## Uncertainty handling

The model must support parameter uncertainty.

Implement:

sample_params(base_params, uncertainty_spec, n, seed)

For each curve, output:

median
5th percentile
95th percentile

The GUI must show uncertainty bands.

## Sensitivity analysis

The model must estimate which parameters most affect:

mu_min
mu_peak
mu_max

At minimum, implement one-at-a-time sensitivity sweeps.

Later versions may include Sobol sensitivity analysis.

## GUI requirements

Use Streamlit.

Required screens:

1. Overview

Show:

* model version
* current parameter set
* current mutation-rate range
* warnings

2. Parameter controls

Controls for:

mu0
T
Ne
Bmax
kb
hb
m_burn
p
kd
ke
alpha
beta
gamma
kr
lambda_decay
rho_robustness
m_min
m_max
m_points
bootstrap_samples
random_seed

3. Curve viewer

Plot:

B(m, T)
D(m, T)
R(m, T)
S(m, T)

4. Phase diagram

Heatmap:

x-axis: mutation-rate multiplier
y-axis: generation horizon
colour: net score

5. Sensitivity analysis

Rank parameters by effect on:

mu_min
mu_peak
mu_max

6. Evidence panel

For every fitted/default parameter, show:

source
status
confidence
notes

Statuses:

source-backed
fitted
placeholder
sensitivity-only

## Initial parameter schema

Create a Pydantic model:

class ModelParams(BaseModel):
    mu0: float
    generations: int
    ne: float

    bmax: float
    kb: float
    hb: float
    m_burn: float
    p: float

    kd: float
    ke: float
    alpha: float
    beta: float
    gamma: float
    kr: float

    lambda_decay: float
    rho_robustness: float

    m_min: float
    m_max: float
    m_points: int

Add validation:

all rates must be positive
generation count must be positive
m_max > m_min
m_points >= 10
exponents must be positive

## Required modules

src/mrrm/parameters.py
  Pydantic schemas and default parameter sets

src/mrrm/curves.py
  deterministic benefit, decay, robustness, and net-score functions

src/mrrm/sensitivity.py
  one-at-a-time parameter sweeps

src/mrrm/validation.py
  qualitative validation checks

src/mrrm/plotting.py
  reusable Plotly figures

app/streamlit_app.py
  GUI only; no model logic

## Required tests

Tests must verify:

benefit increases at low mutation rate
decay increases with mutation rate
robustness decreases as decay increases
net score can have an internal peak
higher decay penalty shifts optimum downward
higher benefit coefficient shifts optimum upward
invalid parameters fail validation
fixed seeds produce reproducible uncertainty bands

## Validation targets

The model should reproduce qualitative findings:

V1. Increasing mutation rate can accelerate short-term adaptation.
V2. Very high mutation rates can limit adaptation.
V3. Hypermutators can gain selected-environment fitness while genome decay accumulates.
V4. Longer time horizon can shift optimal mutation rate downward when decay matters.
V5. Higher decay penalty shifts the optimum downward.
V6. Higher beneficial opportunity shifts the optimum upward.

## Later stochastic model

After the deterministic model is working, add a stochastic simulator.

Possible structure:

population state:
  fitness
  deleterious load
  lethal fraction
  genome integrity
  robustness
  mutation-rate class

events:
  beneficial mutation
  weakly deleterious mutation
  strongly deleterious mutation
  lethal mutation
  mutator mutation
  antimutator mutation

Possible methods:

Wright-Fisher approximation
branching process approximation
Approximate Bayesian Computation
particle filter / state-space model

Do not add this until the deterministic version is tested and documented.

## Output report

Generate:

reports/first_model_report.md

It must include:

model version
parameter set
assumptions
curve plots
mutation-rate range
sensitivity results
known limitations
failed validation checks

## Failure policy

The model must report when:

no optimum exists
the optimum is outside the search range
the result is dominated by uncertain parameters
the curves behave biologically unrealistically
the data cannot support the requested conclusion

Never tune parameters only to produce a nice-looking answer.