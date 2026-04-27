"""Plotting helpers for deterministic model results."""

from __future__ import annotations

import plotly.graph_objects as go

from .curves import ModelResults


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
