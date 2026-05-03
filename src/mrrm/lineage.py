"""Explicit generational lineage mutation-selection model."""

from __future__ import annotations

from dataclasses import dataclass, fields, replace
from time import perf_counter
from typing import Iterable

import numpy as np

from .parameters import LineageParameters
from .validation import validate_lineage_parameters

MAX_EXP_ARGUMENT = 700.0
CATEGORY_NAMES = ("beneficial", "harmful", "lethal", "neutral")


class ComputationLimitError(ValueError):
    """Raised when a lineage run exceeds configured safety limits."""


@dataclass(frozen=True)
class MutationCategoryProbabilities:
    """Mutation category probabilities for one inherited mutation count."""

    beneficial: float
    harmful: float
    lethal: float
    neutral: float

    def as_array(self) -> np.ndarray:
        """Return probabilities in the simulator's category order."""

        return np.asarray(
            [self.beneficial, self.harmful, self.lethal, self.neutral],
            dtype=float,
        )

    def as_dict(self) -> dict[str, float]:
        """Return labelled probabilities."""

        return {
            "beneficial": self.beneficial,
            "harmful": self.harmful,
            "lethal": self.lethal,
            "neutral": self.neutral,
        }


MutationTransitionProbabilities = MutationCategoryProbabilities


@dataclass(frozen=True)
class LineageClass:
    """Explicit surviving lineage with inherited mutation counts."""

    lineage_id: int
    generation_created: int
    total_mutations: int
    beneficial_mutations: int
    harmful_mutations: int
    lethal_mutations: int
    size: int
    fitness_score: float


@dataclass(frozen=True)
class GenerationRecord:
    """Population summary after one Mutation and Selection event pair."""

    generation: int
    population_cap: int
    total_population: int
    pre_cap_population: int
    lineage_count_current: int
    lineage_counter_cumulative: int
    mean_fitness: float
    pre_cap_mean_fitness: float
    best_fitness: float
    dominant_lineage_fitness: float
    beneficial_lineage_population: int
    harmful_lineage_population: int
    neutral_or_balanced_population: int
    beneficial_adoption_fraction: float
    beneficial_mutation_count_total: int
    harmful_mutation_count_total: int
    lethal_mutation_count_total: int
    neutral_mutation_count_total: int
    mutation_lineages_created: int
    one_mutation_lineages_created: int
    multi_mutation_lineages_created: int
    new_mutations_total: int
    no_mutation_population: int
    lethal_lineages_removed: int
    low_fitness_lineages_removed: int
    post_cap_lineages_removed: int
    population_over_cap: bool
    runtime_seconds: float


@dataclass(frozen=True)
class LineageOutcomeSummary:
    """Final-run interpretation flags."""

    final_generation: int
    population_cap: int
    final_population: int
    final_current_lineage_count: int
    final_cumulative_lineage_counter: int
    final_mean_fitness: float
    final_best_fitness: float
    final_dominant_lineage_fitness: float
    final_beneficial_adoption_fraction: float
    beneficial_survived: bool
    beneficial_adopted: bool
    collapsed: bool


@dataclass(frozen=True)
class LineageSimulationResult:
    """Completed explicit lineage run."""

    params: LineageParameters
    history: tuple[GenerationRecord, ...]
    final_lineages: tuple[LineageClass, ...]
    mutation_category_probabilities: MutationCategoryProbabilities
    outcome: LineageOutcomeSummary

    @property
    def transition_probabilities(self) -> MutationCategoryProbabilities:
        """Compatibility alias for older callers."""

        return self.mutation_category_probabilities

    def history_arrays(self) -> dict[str, np.ndarray]:
        """Return generation records as numeric arrays for plotting or analysis."""

        arrays: dict[str, np.ndarray] = {}
        for field in fields(GenerationRecord):
            values = [getattr(record, field.name) for record in self.history]
            arrays[field.name] = np.asarray(values)
        return arrays


def mutation_category_probabilities(
    params: LineageParameters,
    total_mutations: int = 0,
) -> MutationCategoryProbabilities:
    """Return normalized mutation category probabilities.

    The beneficial, harmful, and lethal inputs are treated as baseline weights.
    Compound effects multiply those weights by inherited mutation load, then
    the non-neutral and neutral weights are normalized to sum to one.
    """

    validate_lineage_parameters(params)
    if total_mutations < 0:
        raise ValueError("total_mutations must be non-negative.")

    compound_multiplier = 1.0 + total_mutations * params.compound_effect
    beneficial_weight = params.beneficial_mutation_rate * compound_multiplier
    harmful_weight = params.harmful_mutation_rate * compound_multiplier
    lethal_weight = params.lethal_mutation_rate * compound_multiplier
    neutral_weight = 1.0
    denominator = (
        beneficial_weight + harmful_weight + lethal_weight + neutral_weight
    )
    if not np.isfinite(denominator) or denominator <= 0:
        raise ValueError("mutation category normalization produced an invalid value.")

    return MutationCategoryProbabilities(
        beneficial=float(beneficial_weight / denominator),
        harmful=float(harmful_weight / denominator),
        lethal=float(lethal_weight / denominator),
        neutral=float(neutral_weight / denominator),
    )


def mutation_transition_probabilities(
    params: LineageParameters,
) -> MutationCategoryProbabilities:
    """Compatibility wrapper returning seed-lineage category probabilities."""

    return mutation_category_probabilities(params, total_mutations=0)


def simulate_lineage_survival(
    params: LineageParameters | None = None,
) -> LineageSimulationResult:
    """Run one stochastic generational mutation-selection simulation."""

    params = params or LineageParameters()
    validate_lineage_parameters(params)
    rng = np.random.default_rng(params.random_seed)
    start_time = perf_counter()

    lineages: tuple[LineageClass, ...] = (_initial_lineage(params),)
    lineage_counter = 1
    history = [
        _summarize_generation(
            generation=0,
            lineages=lineages,
            lineage_counter=lineage_counter,
            stats=_empty_generation_stats(),
            params=params,
            start_time=start_time,
        )
    ]

    for generation in range(1, params.generations + 1):
        _check_runtime(start_time, params)
        if not lineages:
            history.append(
                _summarize_generation(
                    generation=generation,
                    lineages=(),
                    lineage_counter=lineage_counter,
                    stats=_empty_generation_stats(),
                    params=params,
                    start_time=start_time,
                )
            )
            continue

        candidates, lineage_counter, stats = _mutate_generation(
            lineages=lineages,
            generation=generation,
            lineage_counter=lineage_counter,
            params=params,
            rng=rng,
            start_time=start_time,
        )
        lineages, selection_stats = _select_generation(
            candidates=candidates,
            params=params,
            rng=rng,
        )
        stats.update(selection_stats)
        _check_lineage_limit(len(lineages), params)
        history.append(
            _summarize_generation(
                generation=generation,
                lineages=lineages,
                lineage_counter=lineage_counter,
                stats=stats,
                params=params,
                start_time=start_time,
            )
        )

    outcome = _summarize_outcome(history[-1], params)
    return LineageSimulationResult(
        params=params,
        history=tuple(history),
        final_lineages=lineages,
        mutation_category_probabilities=mutation_category_probabilities(params),
        outcome=outcome,
    )


def _initial_lineage(params: LineageParameters) -> LineageClass:
    return LineageClass(
        lineage_id=1,
        generation_created=0,
        total_mutations=0,
        beneficial_mutations=0,
        harmful_mutations=0,
        lethal_mutations=0,
        size=int(params.seed_population),
        fitness_score=float(params.seed_fitness),
    )


def _empty_generation_stats() -> dict[str, float | int]:
    return {
        "mutation_lineages_created": 0,
        "one_mutation_lineages_created": 0,
        "multi_mutation_lineages_created": 0,
        "new_mutations_total": 0,
        "no_mutation_population": 0,
        "lethal_lineages_removed": 0,
        "low_fitness_lineages_removed": 0,
        "post_cap_lineages_removed": 0,
        "pre_cap_population": 0,
        "pre_cap_mean_fitness": 0.0,
    }


def _mutate_generation(
    lineages: Iterable[LineageClass],
    generation: int,
    lineage_counter: int,
    params: LineageParameters,
    rng: np.random.Generator,
    start_time: float,
) -> tuple[tuple[LineageClass, ...], int, dict[str, float | int]]:
    candidates: list[LineageClass] = []
    stats = _empty_generation_stats()
    p_no_mutation = _poisson_zero_probability(params.mutation_rate)
    p_mutated = 1.0 - p_no_mutation

    for lineage in lineages:
        _check_runtime(start_time, params)
        if lineage.size <= 0:
            continue

        no_mutation_size = int(rng.binomial(lineage.size, p_no_mutation))
        mutated_count = int(lineage.size - no_mutation_size)
        stats["no_mutation_population"] += no_mutation_size

        if no_mutation_size > 0:
            candidates.append(replace(lineage, size=no_mutation_size))

        if mutated_count <= 0:
            continue
        _check_lineage_limit(len(candidates) + mutated_count, params)

        mutation_counts = _draw_positive_poisson(
            rng,
            params.mutation_rate,
            mutated_count,
        )
        stats["mutation_lineages_created"] += mutated_count
        stats["one_mutation_lineages_created"] += int(np.sum(mutation_counts == 1))
        stats["multi_mutation_lineages_created"] += int(np.sum(mutation_counts > 1))
        stats["new_mutations_total"] += int(np.sum(mutation_counts))

        for mutation_count in mutation_counts:
            lineage_counter += 1
            candidates.append(
                _create_mutated_lineage(
                    parent=lineage,
                    lineage_id=lineage_counter,
                    generation=generation,
                    mutation_count=int(mutation_count),
                    params=params,
                    rng=rng,
                )
            )

    _check_lineage_limit(len(candidates), params)
    return tuple(candidates), lineage_counter, stats


def _create_mutated_lineage(
    parent: LineageClass,
    lineage_id: int,
    generation: int,
    mutation_count: int,
    params: LineageParameters,
    rng: np.random.Generator,
) -> LineageClass:
    total_mutations = parent.total_mutations
    beneficial_mutations = parent.beneficial_mutations
    harmful_mutations = parent.harmful_mutations
    lethal_mutations = parent.lethal_mutations

    for _ in range(mutation_count):
        probabilities = mutation_category_probabilities(
            params,
            total_mutations=total_mutations,
        ).as_array()
        category = CATEGORY_NAMES[int(rng.choice(len(CATEGORY_NAMES), p=probabilities))]
        total_mutations += 1
        if category == "beneficial":
            beneficial_mutations += 1
        elif category == "harmful":
            harmful_mutations += 1
        elif category == "lethal":
            lethal_mutations += 1

    return LineageClass(
        lineage_id=lineage_id,
        generation_created=generation,
        total_mutations=total_mutations,
        beneficial_mutations=beneficial_mutations,
        harmful_mutations=harmful_mutations,
        lethal_mutations=lethal_mutations,
        size=1,
        fitness_score=parent.fitness_score,
    )


def _select_generation(
    candidates: tuple[LineageClass, ...],
    params: LineageParameters,
    rng: np.random.Generator,
) -> tuple[tuple[LineageClass, ...], dict[str, float | int]]:
    stats = {
        "lethal_lineages_removed": 0,
        "low_fitness_lineages_removed": 0,
        "post_cap_lineages_removed": 0,
        "pre_cap_population": 0,
    }
    nonlethal: list[LineageClass] = []
    for lineage in candidates:
        if lineage.lethal_mutations > 0:
            stats["lethal_lineages_removed"] += 1
        else:
            nonlethal.append(replace(lineage, size=lineage.size * 2))

    viable: list[LineageClass] = []
    for lineage in nonlethal:
        fitness = _fitness_from_lineage(lineage, params)
        updated = replace(lineage, fitness_score=fitness)
        if fitness < params.minimum_fitness:
            stats["low_fitness_lineages_removed"] += 1
        else:
            viable.append(updated)

    stats["pre_cap_population"] = int(sum(lineage.size for lineage in viable))
    stats["pre_cap_mean_fitness"] = _weighted_mean_fitness(viable)
    if stats["pre_cap_population"] <= params.population_cap:
        return tuple(viable), stats

    capped = _apply_population_cap(viable, params, rng)
    stats["post_cap_lineages_removed"] = len(viable) - len(capped)
    return tuple(capped), stats


def _apply_population_cap(
    lineages: list[LineageClass],
    params: LineageParameters,
    rng: np.random.Generator,
) -> list[LineageClass]:
    if not lineages:
        return []

    fitness_values = np.asarray(
        [lineage.fitness_score for lineage in lineages],
        dtype=float,
    )
    if params.randomness > 0:
        adjusted_fitness = fitness_values + rng.normal(
            loc=0.0,
            scale=params.randomness,
            size=len(lineages),
        )
        adjusted_fitness = np.maximum(adjusted_fitness, 0.0)
    else:
        adjusted_fitness = fitness_values

    sizes = np.asarray([lineage.size for lineage in lineages], dtype=float)
    selection_weights = sizes * adjusted_fitness
    total_weight = float(np.sum(selection_weights))
    if not np.isfinite(total_weight) or total_weight <= 0:
        selection_weights = sizes
        total_weight = float(np.sum(selection_weights))
    if total_weight <= 0:
        return []

    target_sizes = params.population_cap * selection_weights / total_weight
    rounded_sizes = np.rint(target_sizes).astype(np.int64)
    capped: list[LineageClass] = []
    for lineage, size in zip(lineages, rounded_sizes):
        if size <= 0:
            continue
        capped.append(replace(lineage, size=int(size)))
    return capped


def _fitness_from_lineage(lineage: LineageClass, params: LineageParameters) -> float:
    fitness = (
        params.seed_fitness
        + (lineage.beneficial_mutations - lineage.harmful_mutations)
        * params.mutation_effect
    )
    if not np.isfinite(fitness):
        raise ValueError("lineage fitness produced a non-finite value.")
    return float(fitness)


def _summarize_generation(
    generation: int,
    lineages: tuple[LineageClass, ...],
    lineage_counter: int,
    stats: dict[str, float | int],
    params: LineageParameters,
    start_time: float,
) -> GenerationRecord:
    total_population = int(sum(lineage.size for lineage in lineages))
    pre_cap_population = int(stats.get("pre_cap_population", total_population))
    if generation == 0:
        pre_cap_population = total_population

    if total_population <= 0:
        return GenerationRecord(
            generation=int(generation),
            population_cap=int(params.population_cap),
            total_population=0,
            pre_cap_population=pre_cap_population,
            lineage_count_current=0,
            lineage_counter_cumulative=int(lineage_counter),
            mean_fitness=0.0,
            pre_cap_mean_fitness=0.0,
            best_fitness=0.0,
            dominant_lineage_fitness=0.0,
            beneficial_lineage_population=0,
            harmful_lineage_population=0,
            neutral_or_balanced_population=0,
            beneficial_adoption_fraction=0.0,
            beneficial_mutation_count_total=0,
            harmful_mutation_count_total=0,
            lethal_mutation_count_total=0,
            neutral_mutation_count_total=0,
            mutation_lineages_created=int(stats["mutation_lineages_created"]),
            one_mutation_lineages_created=int(stats["one_mutation_lineages_created"]),
            multi_mutation_lineages_created=int(stats["multi_mutation_lineages_created"]),
            new_mutations_total=int(stats["new_mutations_total"]),
            no_mutation_population=int(stats["no_mutation_population"]),
            lethal_lineages_removed=int(stats["lethal_lineages_removed"]),
            low_fitness_lineages_removed=int(stats["low_fitness_lineages_removed"]),
            post_cap_lineages_removed=int(stats["post_cap_lineages_removed"]),
            population_over_cap=False,
            runtime_seconds=float(perf_counter() - start_time),
        )

    sizes = np.asarray([lineage.size for lineage in lineages], dtype=float)
    fitness_values = np.asarray(
        [lineage.fitness_score for lineage in lineages],
        dtype=float,
    )
    dominant = max(lineages, key=lambda lineage: lineage.size)
    beneficial_population = sum(
        lineage.size
        for lineage in lineages
        if lineage.beneficial_mutations > lineage.harmful_mutations
    )
    harmful_population = sum(
        lineage.size
        for lineage in lineages
        if lineage.harmful_mutations > lineage.beneficial_mutations
    )
    neutral_population = total_population - beneficial_population - harmful_population

    pre_cap_mean_fitness = float(stats.get("pre_cap_mean_fitness", 0.0))
    if generation == 0:
        pre_cap_mean_fitness = _weighted_mean_fitness(lineages)
    return GenerationRecord(
        generation=int(generation),
        population_cap=int(params.population_cap),
        total_population=total_population,
        pre_cap_population=pre_cap_population,
        lineage_count_current=len(lineages),
        lineage_counter_cumulative=int(lineage_counter),
        mean_fitness=float(np.average(fitness_values, weights=sizes)),
        pre_cap_mean_fitness=pre_cap_mean_fitness,
        best_fitness=float(np.max(fitness_values)),
        dominant_lineage_fitness=float(dominant.fitness_score),
        beneficial_lineage_population=int(beneficial_population),
        harmful_lineage_population=int(harmful_population),
        neutral_or_balanced_population=int(neutral_population),
        beneficial_adoption_fraction=beneficial_population / total_population,
        beneficial_mutation_count_total=int(
            sum(lineage.beneficial_mutations * lineage.size for lineage in lineages)
        ),
        harmful_mutation_count_total=int(
            sum(lineage.harmful_mutations * lineage.size for lineage in lineages)
        ),
        lethal_mutation_count_total=int(
            sum(lineage.lethal_mutations * lineage.size for lineage in lineages)
        ),
        neutral_mutation_count_total=int(
            sum(_neutral_mutations(lineage) * lineage.size for lineage in lineages)
        ),
        mutation_lineages_created=int(stats["mutation_lineages_created"]),
        one_mutation_lineages_created=int(stats["one_mutation_lineages_created"]),
        multi_mutation_lineages_created=int(stats["multi_mutation_lineages_created"]),
        new_mutations_total=int(stats["new_mutations_total"]),
        no_mutation_population=int(stats["no_mutation_population"]),
        lethal_lineages_removed=int(stats["lethal_lineages_removed"]),
        low_fitness_lineages_removed=int(stats["low_fitness_lineages_removed"]),
        post_cap_lineages_removed=int(stats["post_cap_lineages_removed"]),
        population_over_cap=total_population > params.population_cap,
        runtime_seconds=float(perf_counter() - start_time),
    )


def _weighted_mean_fitness(lineages: Iterable[LineageClass]) -> float:
    lineages = tuple(lineages)
    if not lineages:
        return 0.0
    total = sum(lineage.size for lineage in lineages)
    if total <= 0:
        return 0.0
    return float(
        np.average(
            [lineage.fitness_score for lineage in lineages],
            weights=[lineage.size for lineage in lineages],
        )
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
        final_record.total_population == 0
        or final_record.mean_fitness <= params.collapse_fitness_threshold
    )
    return LineageOutcomeSummary(
        final_generation=final_record.generation,
        population_cap=final_record.population_cap,
        final_population=final_record.total_population,
        final_current_lineage_count=final_record.lineage_count_current,
        final_cumulative_lineage_counter=final_record.lineage_counter_cumulative,
        final_mean_fitness=final_record.mean_fitness,
        final_best_fitness=final_record.best_fitness,
        final_dominant_lineage_fitness=final_record.dominant_lineage_fitness,
        final_beneficial_adoption_fraction=(
            final_record.beneficial_adoption_fraction
        ),
        beneficial_survived=beneficial_survived,
        beneficial_adopted=beneficial_adopted,
        collapsed=collapsed,
    )


def _draw_positive_poisson(
    rng: np.random.Generator,
    mutation_rate: float,
    count: int,
) -> np.ndarray:
    if count <= 0:
        return np.asarray([], dtype=np.int64)
    if mutation_rate <= 0:
        return np.zeros(count, dtype=np.int64)
    if mutation_rate >= 20:
        draws = rng.poisson(mutation_rate, size=count).astype(np.int64)
        zero_mask = draws == 0
        while np.any(zero_mask):
            draws[zero_mask] = rng.poisson(mutation_rate, size=int(np.sum(zero_mask)))
            zero_mask = draws == 0
        return draws

    values, probabilities = _zero_truncated_poisson_distribution(mutation_rate)
    return rng.choice(values, size=count, p=probabilities).astype(np.int64)


def _zero_truncated_poisson_distribution(
    mutation_rate: float,
) -> tuple[np.ndarray, np.ndarray]:
    p0 = _poisson_zero_probability(mutation_rate)
    positive_probability = 1.0 - p0
    probabilities: list[float] = []
    values: list[int] = []
    p_k = p0
    cumulative = 0.0
    k = 0
    while cumulative < positive_probability * (1.0 - 1e-12):
        k += 1
        p_k *= mutation_rate / k
        values.append(k)
        probabilities.append(p_k)
        cumulative += p_k
        if k > 10_000:
            raise ValueError("Poisson mutation count distribution did not converge.")
    probability_array = np.asarray(probabilities, dtype=float)
    probability_array = probability_array / float(np.sum(probability_array))
    return np.asarray(values, dtype=np.int64), probability_array


def _poisson_zero_probability(rate: float) -> float:
    if rate <= 0:
        return 1.0
    return float(np.exp(-min(rate, MAX_EXP_ARGUMENT)))


def _neutral_mutations(lineage: LineageClass) -> int:
    return (
        lineage.total_mutations
        - lineage.beneficial_mutations
        - lineage.harmful_mutations
        - lineage.lethal_mutations
    )


def _check_runtime(start_time: float, params: LineageParameters) -> None:
    elapsed = perf_counter() - start_time
    if elapsed > params.max_runtime_seconds:
        raise ComputationLimitError(
            "lineage simulation exceeded max_runtime_seconds="
            f"{params.max_runtime_seconds:g}; reduce population, generations, "
            "mutation_rate, or max_lineage_classes."
        )


def _check_lineage_limit(lineage_count: int, params: LineageParameters) -> None:
    if lineage_count > params.max_lineage_classes:
        raise ComputationLimitError(
            "lineage simulation would exceed max_lineage_classes="
            f"{params.max_lineage_classes}; reduce population, generations, "
            "or mutation_rate."
        )
