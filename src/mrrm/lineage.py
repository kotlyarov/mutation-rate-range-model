"""Generational lineage-survival model."""

from __future__ import annotations

from dataclasses import dataclass, fields, replace
from typing import Iterable

import numpy as np

from .parameters import LineageParameters
from .validation import validate_lineage_parameters

MAX_EXP_ARGUMENT = 700.0
STATE_ROUND_DIGITS = 12
TRANSITION_NAMES = (
    "no_mutation",
    "neutral",
    "harmful",
    "beneficial",
    "mixed",
)


@dataclass(frozen=True)
class MutationTransitionProbabilities:
    """Per-offspring mutation-class probabilities for one generation."""

    no_mutation: float
    neutral: float
    harmful: float
    beneficial: float
    mixed: float

    def as_array(self) -> np.ndarray:
        """Return probabilities in the simulator's transition order."""

        return np.asarray(
            [
                self.no_mutation,
                self.neutral,
                self.harmful,
                self.beneficial,
                self.mixed,
            ],
            dtype=float,
        )

    def as_dict(self) -> dict[str, float]:
        """Return labelled probabilities."""

        return {
            "no_mutation": self.no_mutation,
            "neutral": self.neutral,
            "harmful": self.harmful,
            "beneficial": self.beneficial,
            "mixed": self.mixed,
        }


@dataclass(frozen=True)
class LineageClass:
    """Aggregated surviving lineage class with inherited biological state."""

    count: int
    accumulated_benefit: float
    accumulated_decay: float
    robustness: float
    fitness: float
    has_beneficial: bool
    has_harmful: bool


@dataclass(frozen=True)
class GenerationRecord:
    """Population summary after survival selection for one generation."""

    generation: int
    population_size: int
    mean_fitness: float
    best_fitness: float
    dominant_fitness: float
    mean_benefit: float
    mean_decay: float
    mean_robustness: float
    beneficial_adoption_fraction: float
    harmful_fraction: float
    mixed_fraction: float
    lineage_class_count: int
    no_mutation_offspring: int
    neutral_mutation_offspring: int
    harmful_mutation_offspring: int
    beneficial_mutation_offspring: int
    mixed_mutation_offspring: int


@dataclass(frozen=True)
class LineageOutcomeSummary:
    """Final-run interpretation flags."""

    final_generation: int
    final_mean_fitness: float
    final_best_fitness: float
    final_dominant_fitness: float
    final_beneficial_adoption_fraction: float
    final_mean_decay: float
    final_lineage_class_count: int
    beneficial_survived: bool
    beneficial_adopted: bool
    collapsed: bool


@dataclass(frozen=True)
class LineageSimulationResult:
    """Completed lineage-survival run."""

    params: LineageParameters
    history: tuple[GenerationRecord, ...]
    final_lineages: tuple[LineageClass, ...]
    transition_probabilities: MutationTransitionProbabilities
    outcome: LineageOutcomeSummary

    def history_arrays(self) -> dict[str, np.ndarray]:
        """Return generation records as numeric arrays for plotting or analysis."""

        arrays: dict[str, np.ndarray] = {}
        for field in fields(GenerationRecord):
            values = [getattr(record, field.name) for record in self.history]
            arrays[field.name] = np.asarray(values)
        return arrays


def mutation_transition_probabilities(
    params: LineageParameters,
) -> MutationTransitionProbabilities:
    """Calculate one-generation mutation-class probabilities.

    Beneficial, harmful, and neutral events are represented as independent
    Poisson arrivals. The simulator then collapses realizations into the
    high-level classes used by the lineage transition step.
    """

    validate_lineage_parameters(params)
    beneficial_rate = (
        params.alpha_benefit
        * params.mutation_rate_multiplier
        / params.T_ref
    )
    harmful_rate = (
        params.decay_scale
        * params.mutation_rate_multiplier ** params.gamma_decay
        / params.T_ref
    )
    neutral_rate = (
        params.neutral_rate_scale
        * params.mutation_rate_multiplier
        / params.T_ref
    )
    p_beneficial = _poisson_event_probability(beneficial_rate)
    p_harmful = _poisson_event_probability(harmful_rate)
    p_neutral = _poisson_event_probability(neutral_rate)

    no_mutation = (1.0 - p_beneficial) * (1.0 - p_harmful) * (1.0 - p_neutral)
    neutral = (1.0 - p_beneficial) * (1.0 - p_harmful) * p_neutral
    harmful = (1.0 - p_beneficial) * p_harmful
    beneficial = p_beneficial * (1.0 - p_harmful)
    mixed = p_beneficial * p_harmful
    values = np.asarray(
        [no_mutation, neutral, harmful, beneficial, mixed],
        dtype=float,
    )
    values = np.clip(values, 0.0, 1.0)
    values = values / np.sum(values)
    return MutationTransitionProbabilities(
        no_mutation=float(values[0]),
        neutral=float(values[1]),
        harmful=float(values[2]),
        beneficial=float(values[3]),
        mixed=float(values[4]),
    )


def simulate_lineage_survival(
    params: LineageParameters | None = None,
) -> LineageSimulationResult:
    """Run one stochastic generational lineage-survival simulation."""

    params = params or LineageParameters()
    validate_lineage_parameters(params)
    rng = np.random.default_rng(params.random_seed)
    transition_probabilities = mutation_transition_probabilities(params)
    transition_array = transition_probabilities.as_array()

    lineages: tuple[LineageClass, ...] = (_initial_lineage(params),)
    zero_counts = np.zeros(len(TRANSITION_NAMES), dtype=np.int64)
    history = [_summarize_generation(0, lineages, zero_counts)]

    for generation in range(1, params.generations + 1):
        candidates, transition_counts = _mutate_generation(
            lineages,
            transition_array,
            params,
            rng,
        )
        lineages = _select_survivors(candidates, params, rng)
        lineages = _merge_lineage_overflow(lineages, params)
        history.append(_summarize_generation(generation, lineages, transition_counts))

    outcome = _summarize_outcome(history[-1], params)
    return LineageSimulationResult(
        params=params,
        history=tuple(history),
        final_lineages=lineages,
        transition_probabilities=transition_probabilities,
        outcome=outcome,
    )


def _initial_lineage(params: LineageParameters) -> LineageClass:
    robustness = _robustness_from_decay(0.0, params)
    fitness = _fitness_from_state(0.0, 0.0, robustness, params)
    return LineageClass(
        count=int(params.population_size),
        accumulated_benefit=0.0,
        accumulated_decay=0.0,
        robustness=robustness,
        fitness=fitness,
        has_beneficial=False,
        has_harmful=False,
    )


def _mutate_generation(
    lineages: Iterable[LineageClass],
    transition_probabilities: np.ndarray,
    params: LineageParameters,
    rng: np.random.Generator,
) -> tuple[tuple[LineageClass, ...], np.ndarray]:
    candidates: dict[tuple[float, float, bool, bool], LineageClass] = {}
    transition_totals = np.zeros(len(TRANSITION_NAMES), dtype=np.int64)

    for lineage in lineages:
        if lineage.count <= 0:
            continue
        draws = rng.multinomial(int(lineage.count), transition_probabilities)
        transition_totals += draws
        for transition_name, count in zip(TRANSITION_NAMES, draws):
            if count <= 0:
                continue
            updated = _apply_transition(lineage, transition_name, int(count), params)
            _add_candidate(candidates, updated)

    return tuple(candidates.values()), transition_totals


def _apply_transition(
    lineage: LineageClass,
    transition_name: str,
    count: int,
    params: LineageParameters,
) -> LineageClass:
    adds_harmful = transition_name in {"harmful", "mixed"}
    adds_beneficial = transition_name in {"beneficial", "mixed"}

    accumulated_decay = lineage.accumulated_decay
    if adds_harmful:
        accumulated_decay += params.decay_effect_size

    accumulated_benefit = lineage.accumulated_benefit
    if adds_beneficial:
        accumulated_benefit = _benefit_after_new_mutation(
            inherited_benefit=lineage.accumulated_benefit,
            inherited_decay=lineage.accumulated_decay,
            adds_harmful=adds_harmful,
            params=params,
        )

    robustness = _robustness_from_decay(accumulated_decay, params)
    fitness = _fitness_from_state(
        accumulated_benefit,
        accumulated_decay,
        robustness,
        params,
    )
    return LineageClass(
        count=count,
        accumulated_benefit=accumulated_benefit,
        accumulated_decay=accumulated_decay,
        robustness=robustness,
        fitness=fitness,
        has_beneficial=lineage.has_beneficial or adds_beneficial,
        has_harmful=lineage.has_harmful or adds_harmful,
    )


def _benefit_after_new_mutation(
    inherited_benefit: float,
    inherited_decay: float,
    adds_harmful: bool,
    params: LineageParameters,
) -> float:
    if params.benefit_scale == 0 or params.beneficial_effect_size == 0:
        return inherited_benefit

    remaining_benefit = max(0.0, params.benefit_scale - inherited_benefit)
    if remaining_benefit == 0:
        return inherited_benefit

    new_decay = params.decay_effect_size if adds_harmful else 0.0
    interference_load = inherited_decay + new_decay
    interference = 1.0 / (
        1.0
        + params.beta_interference
        * interference_load ** params.gamma_interference
    )
    increment = min(remaining_benefit, params.beneficial_effect_size * interference)
    return inherited_benefit + increment


def _add_candidate(
    candidates: dict[tuple[float, float, bool, bool], LineageClass],
    lineage: LineageClass,
) -> None:
    key = _lineage_key(lineage)
    existing = candidates.get(key)
    if existing is None:
        candidates[key] = lineage
        return
    candidates[key] = replace(existing, count=existing.count + lineage.count)


def _lineage_key(lineage: LineageClass) -> tuple[float, float, bool, bool]:
    return (
        round(lineage.accumulated_benefit, STATE_ROUND_DIGITS),
        round(lineage.accumulated_decay, STATE_ROUND_DIGITS),
        lineage.has_beneficial,
        lineage.has_harmful,
    )


def _select_survivors(
    candidates: tuple[LineageClass, ...],
    params: LineageParameters,
    rng: np.random.Generator,
) -> tuple[LineageClass, ...]:
    if not candidates:
        return (_initial_lineage(params),)

    counts = np.asarray([lineage.count for lineage in candidates], dtype=float)
    weights = counts * np.asarray(
        [_survival_weight(lineage, params) for lineage in candidates],
        dtype=float,
    )
    if not np.all(np.isfinite(weights)) or float(np.sum(weights)) <= 0.0:
        weights = counts

    probabilities = weights / np.sum(weights)
    survivor_counts = rng.multinomial(int(params.population_size), probabilities)
    survivors = [
        replace(lineage, count=int(count))
        for lineage, count in zip(candidates, survivor_counts)
        if count > 0
    ]
    if not survivors:
        return (_initial_lineage(params),)
    return tuple(survivors)


def _survival_weight(lineage: LineageClass, params: LineageParameters) -> float:
    if params.selection_strength == 0:
        return 1.0
    fitness = max(lineage.fitness, params.minimum_survival_fitness)
    return fitness ** params.selection_strength


def _merge_lineage_overflow(
    lineages: tuple[LineageClass, ...],
    params: LineageParameters,
) -> tuple[LineageClass, ...]:
    if len(lineages) <= params.max_lineage_classes:
        return lineages

    sorted_lineages = sorted(lineages, key=lambda lineage: lineage.count, reverse=True)
    keep_count = max(0, params.max_lineage_classes - 1)
    kept = sorted_lineages[:keep_count]
    overflow = sorted_lineages[keep_count:]
    merged = _weighted_merge(overflow, params)
    return tuple([*kept, merged])


def _weighted_merge(
    lineages: list[LineageClass],
    params: LineageParameters,
) -> LineageClass:
    total_count = int(sum(lineage.count for lineage in lineages))
    if total_count <= 0:
        return _initial_lineage(params)

    weights = np.asarray([lineage.count for lineage in lineages], dtype=float)
    benefit = float(
        np.average(
            [lineage.accumulated_benefit for lineage in lineages],
            weights=weights,
        )
    )
    decay = float(
        np.average(
            [lineage.accumulated_decay for lineage in lineages],
            weights=weights,
        )
    )
    robustness = _robustness_from_decay(decay, params)
    fitness = _fitness_from_state(benefit, decay, robustness, params)
    return LineageClass(
        count=total_count,
        accumulated_benefit=benefit,
        accumulated_decay=decay,
        robustness=robustness,
        fitness=fitness,
        has_beneficial=any(lineage.has_beneficial for lineage in lineages),
        has_harmful=any(lineage.has_harmful for lineage in lineages),
    )


def _summarize_generation(
    generation: int,
    lineages: tuple[LineageClass, ...],
    transition_counts: np.ndarray,
) -> GenerationRecord:
    total_count = int(sum(lineage.count for lineage in lineages))
    if total_count <= 0:
        raise ValueError("lineage population disappeared unexpectedly.")

    weights = np.asarray([lineage.count for lineage in lineages], dtype=float)
    fitness_values = np.asarray([lineage.fitness for lineage in lineages], dtype=float)
    benefit_values = np.asarray(
        [lineage.accumulated_benefit for lineage in lineages],
        dtype=float,
    )
    decay_values = np.asarray(
        [lineage.accumulated_decay for lineage in lineages],
        dtype=float,
    )
    robustness_values = np.asarray([lineage.robustness for lineage in lineages], dtype=float)
    dominant = max(lineages, key=lambda lineage: lineage.count)
    beneficial_count = sum(
        lineage.count for lineage in lineages if lineage.has_beneficial
    )
    harmful_count = sum(lineage.count for lineage in lineages if lineage.has_harmful)
    mixed_count = sum(
        lineage.count
        for lineage in lineages
        if lineage.has_beneficial and lineage.has_harmful
    )
    return GenerationRecord(
        generation=int(generation),
        population_size=total_count,
        mean_fitness=float(np.average(fitness_values, weights=weights)),
        best_fitness=float(np.max(fitness_values)),
        dominant_fitness=float(dominant.fitness),
        mean_benefit=float(np.average(benefit_values, weights=weights)),
        mean_decay=float(np.average(decay_values, weights=weights)),
        mean_robustness=float(np.average(robustness_values, weights=weights)),
        beneficial_adoption_fraction=beneficial_count / total_count,
        harmful_fraction=harmful_count / total_count,
        mixed_fraction=mixed_count / total_count,
        lineage_class_count=len(lineages),
        no_mutation_offspring=int(transition_counts[0]),
        neutral_mutation_offspring=int(transition_counts[1]),
        harmful_mutation_offspring=int(transition_counts[2]),
        beneficial_mutation_offspring=int(transition_counts[3]),
        mixed_mutation_offspring=int(transition_counts[4]),
    )


def _summarize_outcome(
    final_record: GenerationRecord,
    params: LineageParameters,
) -> LineageOutcomeSummary:
    beneficial_survived = final_record.beneficial_adoption_fraction > 0.0
    beneficial_adopted = (
        final_record.beneficial_adoption_fraction
        >= params.beneficial_adoption_threshold
    )
    collapsed = final_record.mean_fitness <= params.collapse_fitness_threshold
    return LineageOutcomeSummary(
        final_generation=final_record.generation,
        final_mean_fitness=final_record.mean_fitness,
        final_best_fitness=final_record.best_fitness,
        final_dominant_fitness=final_record.dominant_fitness,
        final_beneficial_adoption_fraction=(
            final_record.beneficial_adoption_fraction
        ),
        final_mean_decay=final_record.mean_decay,
        final_lineage_class_count=final_record.lineage_class_count,
        beneficial_survived=beneficial_survived,
        beneficial_adopted=beneficial_adopted,
        collapsed=collapsed,
    )


def _poisson_event_probability(rate: float) -> float:
    if rate <= 0:
        return 0.0
    return float(-np.expm1(-min(rate, MAX_EXP_ARGUMENT)))


def _robustness_from_decay(decay: float, params: LineageParameters) -> float:
    argument = params.k_robustness * decay
    return float(np.exp(-min(argument, MAX_EXP_ARGUMENT)))


def _fitness_from_state(
    accumulated_benefit: float,
    accumulated_decay: float,
    robustness: float,
    params: LineageParameters,
) -> float:
    raw_fitness = (
        1.0
        + accumulated_benefit
        - params.lambda_decay * accumulated_decay
        + params.rho_robustness * (robustness - 1.0)
    )
    if not np.isfinite(raw_fitness):
        raise ValueError("lineage fitness produced a non-finite value.")
    return max(0.0, float(raw_fitness))
