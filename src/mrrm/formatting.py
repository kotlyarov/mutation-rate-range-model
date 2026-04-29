"""Formatting helpers for user-facing model output."""

from __future__ import annotations

COUNT_UNITS = (
    (1_000_000_000_000, "T"),
    (1_000_000_000, "G"),
    (1_000_000, "M"),
    (1_000, "k"),
)


def format_count_compact(value: int | float) -> str:
    """Format large counts with compact SI-style suffixes."""

    count = int(value)
    magnitude = abs(count)
    if magnitude <= 99_999:
        return f"{count:,}"

    sign = "-" if count < 0 else ""
    for threshold, suffix in COUNT_UNITS:
        if magnitude >= threshold:
            return f"{sign}{magnitude // threshold}{suffix}"

    return f"{count:,}"
