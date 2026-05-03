# Calibration Audit Report

This report audits the pre-rewrite deterministic calibration path. It is a
historical diagnostic report, not a validation claim for the current lineage
mutation-selection model. The fitted benefit curve is non-negative, so
negative relative-fitness observations are preserved in residual tables but are
not used as benefit-fit rows.

Source rows are from `data/processed/calibration_dataset_v0.csv`. Fitness values
come from Sprouffske et al. 2018 Dryad `growth-curves.txt` and are computed as
`r_evo - r_anc` with same-strain, same-batch ancestor controls.

## Audit Scope

- Selected-strain audit: `MRS`, generation horizon `3000`.
- All-strain audit: all `MRS`, `MRM`, `MRL`, and `MRXL` final-generation rows.
- Objective: sum of squared residuals on non-negative relative-fitness rows used
  to fit the current benefit/interference parameters.
- Excluded from benefit fit: observed negative relative-fitness rows and ancestor
  baseline rows.

## Selected-Strain Calibration: MRS

Counts:

- selected rows: 12
- observed final fitness rows: 6
- rows used for benefit fitting: 5
- observed rows excluded from benefit fitting: 1

Objective/loss on fit rows:

| metric | value |
| --- | --- |
| n_rows | 5 |
| sse | 0.820666 |
| mse | 0.164133 |
| rmse | 0.405134 |
| mae | 0.304275 |
| mean_residual | 0.0998054 |

Threshold estimate from selected-strain calibration:

| metric | value |
| --- | --- |
| mu_min | 0.0644923 |
| mu_peak | 0.169787 |
| mu_max | 0.453698 |
| peak_score | 1.47524 |

Fitted benefit/interference parameters:

| parameter | value | provenance |
| --- | --- | --- |
| alpha_benefit | 10 | Fitted |
| benefit_scale | 5.99287 | Fitted |
| beta_interference | 6.0619 | Fitted |
| gamma_interference | 0.5 | Fitted |

Rows used for fitting:

| observation_id | strain | rep | mutation_rate_multiplier | observed_relative_fitness |
| --- | --- | --- | --- | --- |
| sprouffske_2018_growth_mrs_rep1_relative_fitness | MRS | 1 | 0.735294 | 0.774572 |
| sprouffske_2018_growth_mrs_rep2_relative_fitness | MRS | 2 | 0.147059 | 1.57244 |
| sprouffske_2018_growth_mrs_rep4_relative_fitness | MRS | 4 | 0.205882 | 1.32517 |
| sprouffske_2018_growth_mrs_rep5_relative_fitness | MRS | 5 | 0.911765 | 0.632072 |
| sprouffske_2018_growth_mrs_rep6_relative_fitness | MRS | 6 | 9.88235 | 1.12492 |

Predicted vs observed fitness:

| strain | rep | mutation_rate_multiplier | observed | predicted | residual | used_for_fit |
| --- | --- | --- | --- | --- | --- | --- |
| MRS | 1 | 0.735294 | 0.774572 | 0.96628 | -0.191707 | True |
| MRS | 2 | 0.147059 | 1.57244 | 1.38836 | 0.184087 | True |
| MRS | 4 | 0.205882 | 1.32517 | 1.39397 | -0.068809 | True |
| MRS | 5 | 0.911765 | 0.632072 | 0.882729 | -0.250657 | True |
| MRS | 6 | 9.88235 | 1.12492 | 0.298802 | 0.826113 | True |
| MRS | 8 | 0.323529 | -0.0877578 | 1.29431 | -1.38207 | False |

## All-Strain Calibration

Counts:

- selected rows: 60
- observed final fitness rows: 30
- rows used for benefit fitting: 25
- observed rows excluded from benefit fitting: 5

Objective/loss on fit rows:

| metric | value |
| --- | --- |
| n_rows | 25 |
| sse | 7.65256 |
| mse | 0.306102 |
| rmse | 0.553265 |
| mae | 0.468374 |
| mean_residual | 0.00829929 |

Threshold estimate from all-strain calibration:

| metric | value |
| --- | --- |
| mu_min | 0.163697 |
| mu_peak | 0.400229 |
| mu_max | 1.42022 |
| peak_score | 1.13153 |

Fitted benefit/interference parameters:

| parameter | value | provenance |
| --- | --- | --- |
| alpha_benefit | 10 | Fitted |
| benefit_scale | 1.12037 | Fitted |
| beta_interference | 0.0001 | Fitted |
| gamma_interference | 0.5 | Fitted |

Rows used for fitting:

| observation_id | strain | rep | mutation_rate_multiplier | observed_relative_fitness |
| --- | --- | --- | --- | --- |
| sprouffske_2018_growth_mrs_rep1_relative_fitness | MRS | 1 | 0.735294 | 0.774572 |
| sprouffske_2018_growth_mrs_rep2_relative_fitness | MRS | 2 | 0.147059 | 1.57244 |
| sprouffske_2018_growth_mrs_rep4_relative_fitness | MRS | 4 | 0.205882 | 1.32517 |
| sprouffske_2018_growth_mrs_rep5_relative_fitness | MRS | 5 | 0.911765 | 0.632072 |
| sprouffske_2018_growth_mrs_rep6_relative_fitness | MRS | 6 | 9.88235 | 1.12492 |
| sprouffske_2018_growth_mrm_rep1_relative_fitness | MRM | 1 | 4.05882 | 1.33379 |
| sprouffske_2018_growth_mrm_rep3_relative_fitness | MRM | 3 | 4.02941 | 1.0407 |
| sprouffske_2018_growth_mrm_rep4_relative_fitness | MRM | 4 | 1.76471 | 0.28835 |
| sprouffske_2018_growth_mrm_rep5_relative_fitness | MRM | 5 | 0.735294 | 1.56409 |
| sprouffske_2018_growth_mrm_rep6_relative_fitness | MRM | 6 | 6.23529 | 1.31399 |
| sprouffske_2018_growth_mrm_rep7_relative_fitness | MRM | 7 | 4.38235 | 1.70465 |
| sprouffske_2018_growth_mrm_rep8_relative_fitness | MRM | 8 | 3.64706 | 0.69916 |
| sprouffske_2018_growth_mrl_rep1_relative_fitness | MRL | 1 | 5.32353 | 1.72001 |
| sprouffske_2018_growth_mrl_rep2_relative_fitness | MRL | 2 | 7.47059 | 1.58122 |
| sprouffske_2018_growth_mrl_rep3_relative_fitness | MRL | 3 | 4.35294 | 1.93455 |
| sprouffske_2018_growth_mrl_rep4_relative_fitness | MRL | 4 | 3.94118 | 0.258062 |
| sprouffske_2018_growth_mrl_rep5_relative_fitness | MRL | 5 | 13.5294 | 0.273216 |
| sprouffske_2018_growth_mrl_rep6_relative_fitness | MRL | 6 | 9.88235 | 0.355682 |
| sprouffske_2018_growth_mrl_rep7_relative_fitness | MRL | 7 | 20.7647 | 1.64591 |
| sprouffske_2018_growth_mrl_rep8_relative_fitness | MRL | 8 | 19.0882 | 1.39046 |
| sprouffske_2018_growth_mrxl_rep1_relative_fitness | MRXL | 1 | 44.4118 | 1.52576 |
| sprouffske_2018_growth_mrxl_rep3_relative_fitness | MRXL | 3 | 18.4118 | 1.11916 |
| sprouffske_2018_growth_mrxl_rep5_relative_fitness | MRXL | 5 | 5.08824 | 1.49684 |
| sprouffske_2018_growth_mrxl_rep6_relative_fitness | MRXL | 6 | 12.1765 | 0.00832111 |
| sprouffske_2018_growth_mrxl_rep8_relative_fitness | MRXL | 8 | 2.29412 | 1.12483 |

Predicted vs observed fitness by strain:

| strain | rep | mutation_rate_multiplier | observed | predicted | residual | used_for_fit |
| --- | --- | --- | --- | --- | --- | --- |
| MRS | 1 | 0.735294 | 0.774572 | 1.11956 | -0.344986 | True |
| MRS | 2 | 0.147059 | 1.57244 | 0.862888 | 0.709554 | True |
| MRS | 4 | 0.205882 | 1.32517 | 0.977364 | 0.347802 | True |
| MRS | 5 | 0.911765 | 0.632072 | 1.12014 | -0.48807 | True |
| MRS | 6 | 9.88235 | 1.12492 | 1.12002 | 0.0048957 | True |
| MRS | 8 | 0.323529 | -0.0877578 | 1.07623 | -1.16398 | False |
| MRM | 1 | 4.05882 | 1.33379 | 1.12015 | 0.213647 | True |
| MRM | 2 | 2.41176 | -0.0168967 | 1.1202 | -1.13709 | False |
| MRM | 3 | 4.02941 | 1.0407 | 1.12015 | -0.0794504 | True |
| MRM | 4 | 1.76471 | 0.28835 | 1.12022 | -0.831873 | True |
| MRM | 5 | 0.735294 | 1.56409 | 1.11956 | 0.444532 | True |
| MRM | 6 | 6.23529 | 1.31399 | 1.12009 | 0.193901 | True |
| MRM | 7 | 4.38235 | 1.70465 | 1.12014 | 0.584516 | True |
| MRM | 8 | 3.64706 | 0.69916 | 1.12016 | -0.420998 | True |
| MRL | 1 | 5.32353 | 1.72001 | 1.12011 | 0.599899 | True |
| MRL | 2 | 7.47059 | 1.58122 | 1.12007 | 0.461153 | True |
| MRL | 3 | 4.35294 | 1.93455 | 1.12014 | 0.814411 | True |
| MRL | 4 | 3.94118 | 0.258062 | 1.12015 | -0.862087 | True |
| MRL | 5 | 13.5294 | 0.273216 | 1.11996 | -0.846744 | True |
| MRL | 6 | 9.88235 | 0.355682 | 1.12002 | -0.764338 | True |
| MRL | 7 | 20.7647 | 1.64591 | 1.11986 | 0.526044 | True |
| MRL | 8 | 19.0882 | 1.39046 | 1.11988 | 0.270576 | True |
| MRXL | 1 | 44.4118 | 1.52576 | 1.11963 | 0.406135 | True |
| MRXL | 2 | 36.1471 | -0.150119 | 1.1197 | -1.26982 | False |
| MRXL | 3 | 18.4118 | 1.11916 | 1.11989 | -0.000726967 | True |
| MRXL | 4 | 13.2941 | -0.0207922 | 1.11996 | -1.14076 | False |
| MRXL | 5 | 5.08824 | 1.49684 | 1.12012 | 0.376722 | True |
| MRXL | 6 | 12.1765 | 0.00832111 | 1.11998 | -1.11166 | True |
| MRXL | 7 | 20.3824 | -0.0245256 | 1.11987 | -1.14439 | False |
| MRXL | 8 | 2.29412 | 1.12483 | 1.1202 | 0.00462884 | True |

## Leave-One-Strain-Out Check

Each row trains on all other strains and evaluates predictions on the held-out
strain's exact relative-fitness observations. Held-out residuals include
negative relative-fitness observations because they are real observations.

| heldout_strain | training_fit_rows | heldout_observed_rows | training_rmse | heldout_rmse | heldout_mae | heldout_bias | trained_benefit_scale | trained_beta_interference |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| MRS | 20 | 6 | 0.577531 | 0.623716 | 0.509823 | -0.154767 | 1.11927 | 0.0001 |
| MRM | 18 | 8 | 0.584706 | 0.589381 | 0.488251 | -0.123111 | 1.11438 | 0.0001 |
| MRL | 17 | 8 | 0.486283 | 0.674179 | 0.646197 | 0.0370264 | 1.10821 | 0.0001 |
| MRXL | 20 | 8 | 0.552468 | 0.858676 | 0.689092 | -0.501772 | 1.13717 | 0.0001 |

## Interpretation Guardrails

- The selected-strain-only fit and all-strain fit produce different fitted
  parameters and different threshold estimates, so current thresholds are
  calibration-sensitive.
- The all-strain fit collapses to a nearly flat predicted benefit around
  `1.12` for most rows, which is a warning sign that the pre-rewrite
  deterministic benefit curve is underidentified by final-generation fitness
  data alone.
- Leave-one-strain-out errors are non-trivial, especially for `MRXL`, so the
  current fitted parameters should be treated as exploratory diagnostics rather
  than validated biological estimates.
- Decay, robustness, and utility weights are still not identified by exact
  mutation-count, genome-decay, or robustness observations in this dataset.
