"""Plotting helpers for model results and raw observations."""

from __future__ import annotations

import plotly.graph_objects as go

from .curves import ModelResults
from .lineage import LineageSimulationResult


def make_raw_observation_figure(observations: list[dict]) -> go.Figure:
    """Create a raw-observation plot from calibration_dataset_v0 rows."""

    fig = go.Figure()
    strains = sorted({row["strain_or_population"] for row in observations})
    for strain in strains:
        mutation_rows = [
            row
            for row in observations
            if row["strain_or_population"] == strain
            and row["measurement_kind"] == "genomic_mutation_rate_U"
        ]
        if mutation_rows:
            _add_raw_scatter(
                fig,
                rows=mutation_rows,
                name=f"{strain} mutation rate",
                yaxis="y",
                hover_measure="U",
            )

        fitness_rows = [
            row
            for row in observations
            if row["strain_or_population"] == strain
            and row["measurement_kind"] == "relative_fitness"
            and row["measurement_value"] is not None
        ]
        if fitness_rows:
            _add_raw_scatter(
                fig,
                rows=fitness_rows,
                name=f"{strain} relative fitness",
                yaxis="y2",
                hover_measure="relative fitness",
                marker_symbol="x",
            )

    fig.update_layout(
        title="Raw Sprouffske et al. 2018 observations",
        xaxis_title="Derived mutation-rate multiplier relative to MRS ancestor U",
        yaxis_title="Genomic mutation rate U",
        yaxis2={
            "title": "Relative fitness, r_evo - r_anc",
            "overlaying": "y",
            "side": "right",
            "zeroline": True,
        },
        xaxis_type="log",
        yaxis_type="log",
        legend_title="Strain",
        template="plotly_white",
        margin={"l": 48, "r": 24, "t": 56, "b": 48},
    )
    return fig


def _add_raw_scatter(
    fig: go.Figure,
    rows: list[dict],
    name: str,
    yaxis: str,
    hover_measure: str,
    marker_symbol: str = "circle",
) -> None:
    x_values = [row["mutation_rate_multiplier"] for row in rows]
    y_values = [row["measurement_value"] for row in rows]
    lower_errors = [
        row["measurement_value"] - row["measurement_lower"]
        if row["measurement_lower"] is not None
        else 0
        for row in rows
    ]
    upper_errors = [
        row["measurement_upper"] - row["measurement_value"]
        if row["measurement_upper"] is not None
        else 0
        for row in rows
    ]
    labels = [
        f"{row['strain_or_population']} {row['replicate']} generation {row['generation']}"
        for row in rows
    ]
    fig.add_scatter(
        x=x_values,
        y=y_values,
        error_y={
            "type": "data",
            "array": upper_errors,
            "arrayminus": lower_errors,
            "visible": True,
        },
        mode="markers",
        marker={"symbol": marker_symbol},
        name=name,
        text=labels,
        yaxis=yaxis,
        hovertemplate=(
            "%{text}<br>"
            "mutation-rate multiplier=%{x:.3g}<br>"
            f"{hover_measure}=%{{y:.3g}}<extra></extra>"
        ),
    )


def make_curve_figure(results: ModelResults) -> go.Figure:
    """Create a Plotly figure for B, D, R, and S curves."""

    fig = go.Figure()
    fig.add_scatter(
        x=results.m_values,
        y=results.benefit,
        mode="lines",
        name="B: adaptive benefit",
    )
    fig.add_scatter(
        x=results.m_values,
        y=results.decay,
        mode="lines",
        name="D: decay proxy",
    )
    fig.add_scatter(
        x=results.m_values,
        y=results.robustness,
        mode="lines",
        name="R: retained robustness",
    )
    fig.add_scatter(
        x=results.m_values,
        y=results.score,
        mode="lines",
        name="S: net score",
    )
    if results.survival_selection.enabled:
        fig.add_scatter(
            x=results.m_values,
            y=results.survival_selection.contribution_weight,
            mode="lines",
            name="survival contribution",
            yaxis="y2",
            line={"dash": "dot"},
        )

    estimate = results.range_estimate
    _add_marker(fig, estimate.mu_min, "mu_min")
    _add_marker(fig, estimate.mu_peak, "mu_peak")
    _add_marker(fig, estimate.mu_max, "mu_max")

    fig.update_layout(
        title="Assumption-dependent deterministic curves",
        xaxis_title="Mutation-rate multiplier relative to wild type",
        yaxis_title="Relative model units",
        xaxis_type="log",
        yaxis2={
            "title": "Survival contribution",
            "overlaying": "y",
            "side": "right",
            "showgrid": False,
            "visible": results.survival_selection.enabled,
        },
        legend_title="Curve",
        template="plotly_white",
        margin={"l": 48, "r": 24, "t": 56, "b": 48},
    )
    return fig


def make_lineage_population_figure(results: LineageSimulationResult) -> go.Figure:
    """Create a Plotly figure for population survival by generation."""

    history = results.history_arrays()
    fig = go.Figure()
    fig.add_scatter(
        x=history["generation"],
        y=history["total_population"],
        mode="lines",
        name="Total population",
        line={"width": 3},
    )
    fig.add_scatter(
        x=history["generation"],
        y=history["beneficial_lineage_population"],
        mode="lines",
        name="Benefit-led population",
    )
    fig.add_scatter(
        x=history["generation"],
        y=history["harmful_lineage_population"],
        mode="lines",
        name="Decay-led population",
    )
    fig.add_scatter(
        x=history["generation"],
        y=history["mean_fitness"],
        mode="lines",
        name="Mean fitness",
        yaxis="y2",
    )
    fig.update_layout(
        title="Population survival trajectory",
        xaxis_title="Generation",
        yaxis={"title": "Population size", "rangemode": "tozero"},
        yaxis2={
            "title": "Mean fitness",
            "overlaying": "y",
            "side": "right",
            "rangemode": "tozero",
            "showgrid": False,
        },
        legend_title="Trajectory",
        template="plotly_white",
        hovermode="x unified",
        margin={"l": 48, "r": 24, "t": 56, "b": 48},
    )
    return fig


def make_lineage_fitness_figure(results: LineageSimulationResult) -> go.Figure:
    """Create the current lineage trajectory figure.

    Kept as a compatibility alias for older callers.
    """

    return make_lineage_population_figure(results)


def _add_marker(fig: go.Figure, value: float | None, label: str) -> None:
    if value is None:
        return
    fig.add_vline(
        x=value,
        line_width=1,
        line_dash="dot",
        annotation_text=label,
        annotation_position="top",
    )
