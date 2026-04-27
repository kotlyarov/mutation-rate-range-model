"""Plotting helpers for deterministic model results and raw observations."""

from __future__ import annotations

import plotly.graph_objects as go

from .curves import ModelResults


def make_raw_observation_figure(observations: list[dict]) -> go.Figure:
    """Create a raw-observation plot from calibration_dataset_v0 rows."""

    fig = go.Figure()
    strains = sorted({row["strain_or_population"] for row in observations})
    for strain in strains:
        rows = [
            row
            for row in observations
            if row["strain_or_population"] == strain
            and row["measurement_kind"] == "genomic_mutation_rate_U"
        ]
        if not rows:
            continue
        x_values = [row["mutation_rate_multiplier"] for row in rows]
        y_values = [row["measurement_value"] for row in rows]
        lower_errors = [
            row["measurement_value"] - row["measurement_lower"]
            for row in rows
        ]
        upper_errors = [
            row["measurement_upper"] - row["measurement_value"]
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
            name=strain,
            text=labels,
            hovertemplate=(
                "%{text}<br>"
                "mutation-rate multiplier=%{x:.3g}<br>"
                "U=%{y:.3g}<extra></extra>"
            ),
        )

    fig.update_layout(
        title="Raw Sprouffske et al. 2018 mutation-rate observations",
        xaxis_title="Derived mutation-rate multiplier relative to MRS ancestor U",
        yaxis_title="Genomic mutation rate U",
        xaxis_type="log",
        yaxis_type="log",
        legend_title="Strain",
        template="plotly_white",
        margin={"l": 48, "r": 24, "t": 56, "b": 48},
    )
    return fig


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

    estimate = results.range_estimate
    _add_marker(fig, estimate.mu_min, "mu_min")
    _add_marker(fig, estimate.mu_peak, "mu_peak")
    _add_marker(fig, estimate.mu_max, "mu_max")

    fig.update_layout(
        title="Assumption-dependent deterministic curves",
        xaxis_title="Mutation-rate multiplier relative to wild type",
        yaxis_title="Relative model units",
        xaxis_type="log",
        legend_title="Curve",
        template="plotly_white",
        margin={"l": 48, "r": 24, "t": 56, "b": 48},
    )
    return fig


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
