"""Parameter objects for mutation-rate exploration models."""

from __future__ import annotations

from dataclasses import dataclass, replace
from typing import Any

DEFAULT_SURVIVAL_STOCHASTICITY = 0.23


@dataclass(frozen=True)
class ModelParameters:
    """Exploratory parameters for deterministic mutation-rate curves.

    Defaults are placeholders for inspecting curve behaviour. They are not
    fitted biological values.
    """

    T: float = 50_000.0
    T_ref: float = 50_000.0

    m_min: float = 0.1
    m_max: float = 100.0
    n_points: int = 400

    benefit_scale: float = 1.0
    alpha_benefit: float = 1.0
    beta_interference: float = 0.01
    gamma_interference: float = 1.0

    decay_scale: float = 1.0
    gamma_decay: float = 1.2

    k_robustness: float = 0.05

    lambda_decay: float = 0.2
    rho_robustness: float = 0.1

    survival_selection_enabled: bool = True
    population_growth_factor: float = 1.0
    selection_strength: float = 1.0
    survival_stochasticity: float = DEFAULT_SURVIVAL_STOCHASTICITY

    benefit_threshold_fraction: float = 0.80
    net_threshold_fraction: float = 0.80
    decay_threshold_fraction: float = 0.80

    def __post_init__(self) -> None:
        from .validation import validate_parameters

        validate_parameters(self)

    def with_updates(self, **changes: float | int) -> "ModelParameters":
        """Return a validated copy with selected fields changed."""

        return replace(self, **changes)


@dataclass(frozen=True)
class LineageParameters:
    """Inputs for one explicit lineage mutation-selection run.

    Defaults are exploratory assumptions, not fitted biological constants.
    """

    seed_fitness: float = 0.6
    seed_population: int = 1_000
    population_cap: int = 10_000
    generations: int = 2_500

    mutation_rate: float = 0.02
    beneficial_mutation_rate: float = 0.01
    harmful_mutation_rate: float = 0.5
    lethal_mutation_rate: float = 0.1
    compound_effect: float = 0.1

    mutation_effect: float = 0.01
    minimum_fitness: float = 0.4
    randomness: float = 0.1

    beneficial_adoption_threshold: float = 0.50
    collapse_fitness_threshold: float = 0.50

    random_seed: int | None = 1
    max_runtime_seconds: float = 600.0
    max_lineage_classes: int = 100_000

    def __post_init__(self) -> None:
        from .validation import validate_lineage_parameters

        validate_lineage_parameters(self)

    def with_updates(self, **changes: Any) -> "LineageParameters":
        """Return a validated copy with selected fields changed."""

        return replace(self, **changes)
