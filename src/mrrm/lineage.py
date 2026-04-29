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
    carrying_capacity: int
    actual_population_size: int
    candidate_population_size: int
    total_lineages_evolved: int
    viable_population_size: int
    viable_lineage_class_count: int
    mean_fitness: float
    best_fitness: float
    dominant_fitness: float
    mean_benefit: float
    mean_decay: float
    mean_robustness: float
    beneficial_adoption_fraction: float
    beneficial_dominant_population_size: int
    harmful_dominant_population_size: int
    harmful_fraction: float
    mixed_fraction: float
    lineage_class_count: int
    no_mutation_offspring: int
    neutral_mutation_offspring: int
    harmful_mutation_offspring: int
    beneficial_mutation_offspring: int
    mixed_mutation_offspring: int
    beneficial_parent_population_size: int
    beneficial_parent_no_mutation_offspring: int
    beneficial_parent_neutral_mutation_offspring: int
    beneficial_parent_harmful_mutation_offspring: int
    beneficial_parent_beneficial_mutation_offspring: int
    beneficial_parent_mixed_mutation_offspring: int


@dataclass(frozen=True)
class SelectionSummary:
    """Selection accounting for one generation transition."""

    candidate_population_size: int
    viable_population_size: int
    viable_lineage_class_count: int
    actual_population_size: int


@dataclass(frozen=True)
class LineageOutcomeSummary:
    """Final-run interpretation flags."""

    final_generation: int
    carrying_capacity: int
    final_actual_population_size: int
    final_viable_population_size: int
    final_total_lineages_evolved: int
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
        params.beneficial_mutation_rate * params.mutation_rate_multiplier
    )
    harmful_rate = (
        params.deleterious_mutation_rate * params.mutation_rate_multiplier
    )
    neutral_rate = params.neutral_mutation_rate * params.mutation_rate_multiplier
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
    initial_selection = SelectionSummary(
        candidate_population_size=params.effective_population_size,
        viable_population_size=params.effective_population_size,
        viable_lineage_class_count=1,
        actual_population_size=params.effective_population_size,
    )
    history = [
        _summarize_generation(
            0,
            lineages,
            zero_counts,
            zero_counts,
            0,
            initial_selection,
            0,
            params,
        )
    ]

    total_lineages_evolved = 0
    for generation in range(1, params.generations + 1):
        (
            candidates,
            transition_counts,
            beneficial_parent_transition_counts,
            beneficial_parent_population_size,
        ) = _mutate_generation(
            lineages,
            transition_array,
            params,
            rng,
        )
        lineages, selection = _select_survivors(candidates, params, rng)
        total_lineages_evolved += selection.candidate_population_size
        lineages = _merge_lineage_overflow(lineages, params)
        history.append(
            _summarize_generation(
                generation,
                lineages,
                transition_counts,
                beneficial_parent_transition_counts,
                beneficial_parent_population_size,
                selection,
                total_lineages_evolved,
                params,
            )
        )

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
        count=int(params.effective_population_size),
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
) -> tuple[tuple[LineageClass, ...], np.ndarray, np.ndarray, int]:
    candidates: dict[tuple[float, float, bool, bool], LineageClass] = {}
    transition_totals = np.zeros(len(TRANSITION_NAMES), dtype=np.int64)
    beneficial_parent_transition_totals = np.zeros(len(TRANSITION_NAMES), dtype=np.int64)
    beneficial_parent_population_size = 0

    for lineage in lineages:
        if lineage.count <= 0:
            continue
        draws = rng.multinomial(int(lineage.count), transition_probabilities)
        transition_totals += draws
        if lineage.has_beneficial:
            beneficial_parent_transition_totals += draws
            beneficial_parent_population_size += int(lineage.count)
        for transition_name, count in zip(TRANSITION_NAMES, draws):
            if count <= 0:
                continue
            updated = _apply_transition(lineage, transition_name, int(count), params)
            _add_candidate(candidates, updated)

    return (
        tuple(candidates.values()),
        transition_totals,
        beneficial_parent_transition_totals,
        beneficial_parent_population_size,
    )


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
    if params.benefit_saturation == 0 or params.beneficial_effect_size == 0:
        return inherited_benefit

    remaining_benefit = max(0.0, params.benefit_saturation - inherited_benefit)
    if remaining_benefit == 0:
        return inherited_benefit

    new_decay = params.decay_effect_size if adds_harmful else 0.0
    interference_load = inherited_decay + new_decay
    interference = 1.0 / (
        1.0
        + params.interference_strength
        * interference_load ** params.interference_exponent
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
) -> tuple[tuple[LineageClass, ...], SelectionSummary]:
    candidate_population_size = int(sum(lineage.count for lineage in candidates))
    if not candidates:
        return (), SelectionSummary(
            candidate_population_size=0,
            viable_population_size=0,
            viable_lineage_class_count=0,
            actual_population_size=0,
        )

    viable_candidates = tuple(
        lineage for lineage in candidates if _is_viable(lineage, params)
    )
    viable_population_size = int(sum(lineage.count for lineage in viable_candidates))
    if not viable_candidates:
        return (), SelectionSummary(
            candidate_population_size=candidate_population_size,
            viable_population_size=0,
            viable_lineage_class_count=0,
            actual_population_size=0,
        )

    competitive_weights = np.asarray(
        [_competitive_weight(lineage, params) for lineage in viable_candidates],
        dtype=float,
    )
    total_competitive_weight = float(np.sum(competitive_weights))
    if not np.isfinite(total_competitive_weight) or total_competitive_weight <= 0:
        return (), SelectionSummary(
            candidate_population_size=candidate_population_size,
            viable_population_size=viable_population_size,
            viable_lineage_class_count=len(viable_candidates),
            actual_population_size=0,
        )

    next_population_size = min(
        int(params.effective_population_size),
        viable_population_size,
    )
    if next_population_size <= 0:
        return (), SelectionSummary(
            candidate_population_size=candidate_population_size,
            viable_population_size=viable_population_size,
            viable_lineage_class_count=len(viable_candidates),
            actual_population_size=0,
        )

    probabilities = competitive_weights / total_competitive_weight
    survivor_counts = rng.multinomial(next_population_size, probabilities)
    survivors = [
        replace(lineage, count=int(count))
        for lineage, count in zip(viable_candidates, survivor_counts)
        if count > 0
    ]

    survivors_tuple = tuple(survivors)
    actual_population_size = int(sum(lineage.count for lineage in survivors_tuple))
    return survivors_tuple, SelectionSummary(
        candidate_population_size=candidate_population_size,
        viable_population_size=viable_population_size,
        viable_lineage_class_count=len(viable_candidates),
        actual_population_size=actual_population_size,
    )


def _is_viable(lineage: LineageClass, params: LineageParameters) -> bool:
    return (
        lineage.fitness >= params.viability_fitness_threshold
        and lineage.accumulated_decay <= params.lethal_decay_threshold
        and lineage.robustness >= params.minimum_viable_robustness
    )


def _competitive_weight(lineage: LineageClass, params: LineageParameters) -> float:
    if not _is_viable(lineage, params):
        return 0.0
    if params.selection_strength == 0:
        return float(lineage.count)
    return float(lineage.count) * lineage.fitness ** params.selection_strength


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
    beneficial_parent_transition_counts: np.ndarray,
    beneficial_parent_population_size: int,
    selection: SelectionSummary,
    total_lineages_evolved: int,
    params: LineageParameters,
) -> GenerationRecord:
    total_count = int(sum(lineage.count for lineage in lineages))
    if total_count <= 0:
        return GenerationRecord(
            generation=int(generation),
            carrying_capacity=int(params.effective_population_size),
            actual_population_size=0,
            candidate_population_size=selection.candidate_population_size,
            total_lineages_evolved=int(total_lineages_evolved),
            viable_population_size=selection.viable_population_size,
            viable_lineage_class_count=selection.viable_lineage_class_count,
            mean_fitness=0.0,
            best_fitness=0.0,
            dominant_fitness=0.0,
            mean_benefit=0.0,
            mean_decay=0.0,
            mean_robustness=0.0,
            beneficial_adoption_fraction=0.0,
            beneficial_dominant_population_size=0,
            harmful_dominant_population_size=0,
            harmful_fraction=0.0,
            mixed_fraction=0.0,
            lineage_class_count=0,
            no_mutation_offspring=int(transition_counts[0]),
            neutral_mutation_offspring=int(transition_counts[1]),
            harmful_mutation_offspring=int(transition_counts[2]),
            beneficial_mutation_offspring=int(transition_counts[3]),
            mixed_mutation_offspring=int(transition_counts[4]),
            beneficial_parent_population_size=int(beneficial_parent_population_size),
            beneficial_parent_no_mutation_offspring=int(
                beneficial_parent_transition_counts[0]
            ),
            beneficial_parent_neutral_mutation_offspring=int(
                beneficial_parent_transition_counts[1]
            ),
            beneficial_parent_harmful_mutation_offspring=int(
                beneficial_parent_transition_counts[2]
            ),
            beneficial_parent_beneficial_mutation_offspring=int(
                beneficial_parent_transition_counts[3]
            ),
            beneficial_parent_mixed_mutation_offspring=int(
                beneficial_parent_transition_counts[4]
            ),
        )

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
    beneficial_dominant_count = sum(
        lineage.count
        for lineage in lineages
        if _benefit_decay_balance(lineage, params) > 0.0
    )
    harmful_dominant_count = sum(
        lineage.count
        for lineage in lineages
        if _benefit_decay_balance(lineage, params) < 0.0
    )
    harmful_count = sum(lineage.count for lineage in lineages if lineage.has_harmful)
    mixed_count = sum(
        lineage.count
        for lineage in lineages
        if lineage.has_beneficial and lineage.has_harmful
    )
    return GenerationRecord(
        generation=int(generation),
        carrying_capacity=int(params.effective_population_size),
        actual_population_size=total_count,
        candidate_population_size=selection.candidate_population_size,
        total_lineages_evolved=int(total_lineages_evolved),
        viable_population_size=selection.viable_population_size,
        viable_lineage_class_count=selection.viable_lineage_class_count,
        mean_fitness=float(np.average(fitness_values, weights=weights)),
        best_fitness=float(np.max(fitness_values)),
        dominant_fitness=float(dominant.fitness),
        mean_benefit=float(np.average(benefit_values, weights=weights)),
        mean_decay=float(np.average(decay_values, weights=weights)),
        mean_robustness=float(np.average(robustness_values, weights=weights)),
        beneficial_adoption_fraction=beneficial_count / total_count,
        beneficial_dominant_population_size=int(beneficial_dominant_count),
        harmful_dominant_population_size=int(harmful_dominant_count),
        harmful_fraction=harmful_count / total_count,
        mixed_fraction=mixed_count / total_count,
        lineage_class_count=len(lineages),
        no_mutation_offspring=int(transition_counts[0]),
        neutral_mutation_offspring=int(transition_counts[1]),
        harmful_mutation_offspring=int(transition_counts[2]),
        beneficial_mutation_offspring=int(transition_counts[3]),
        mixed_mutation_offspring=int(transition_counts[4]),
        beneficial_parent_population_size=int(beneficial_parent_population_size),
        beneficial_parent_no_mutation_offspring=int(
            beneficial_parent_transition_counts[0]
        ),
        beneficial_parent_neutral_mutation_offspring=int(
            beneficial_parent_transition_counts[1]
        ),
        beneficial_parent_harmful_mutation_offspring=int(
            beneficial_parent_transition_counts[2]
        ),
        beneficial_parent_beneficial_mutation_offspring=int(
            beneficial_parent_transition_counts[3]
        ),
        beneficial_parent_mixed_mutation_offspring=int(
            beneficial_parent_transition_counts[4]
        ),
    )


def _benefit_decay_balance(
    lineage: LineageClass,
    params: LineageParameters,
) -> float:
    return (
        lineage.accumulated_benefit
        - params.decay_fitness_penalty * lineage.accumulated_decay
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
    collapsed = (
        final_record.actual_population_size == 0
        or final_record.mean_fitness <= params.collapse_fitness_threshold
    )
    return LineageOutcomeSummary(
        final_generation=final_record.generation,
        carrying_capacity=final_record.carrying_capacity,
        final_actual_population_size=final_record.actual_population_size,
        final_viable_population_size=final_record.viable_population_size,
        final_total_lineages_evolved=final_record.total_lineages_evolved,
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
    argument = params.robustness_decay_rate * decay
    return float(np.exp(-min(argument, MAX_EXP_ARGUMENT)))


def _fitness_from_state(
    accumulated_benefit: float,
    accumulated_decay: float,
    robustness: float,
    params: LineageParameters,
) -> float:
    performance_fitness = max(
        0.0,
        1.0
        + accumulated_benefit
        - params.decay_fitness_penalty * accumulated_decay,
    )
    robustness_modifier = max(
        0.0,
        1.0 - params.robustness_fitness_weight * (1.0 - robustness),
    )
    raw_fitness = performance_fitness * robustness_modifier
    if not np.isfinite(raw_fitness):
        raise ValueError("lineage fitness produced a non-finite value.")
    return float(raw_fitness)
