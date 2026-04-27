"""Parameter object for the first deterministic model."""

from __future__ import annotations

from dataclasses import dataclass, replace


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

    benefit_threshold_fraction: float = 0.80
    net_threshold_fraction: float = 0.80
    decay_threshold_fraction: float = 0.80

    def __post_init__(self) -> None:
        from .validation import validate_parameters

        validate_parameters(self)

    def with_updates(self, **changes: float | int) -> "ModelParameters":
        """Return a validated copy with selected fields changed."""

        return replace(self, **changes)
