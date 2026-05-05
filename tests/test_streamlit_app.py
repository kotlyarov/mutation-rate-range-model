import pytest

pytest.importorskip("streamlit")

from app.streamlit_app import _final_lineage_rows
from mrrm import LineageParameters, simulate_lineage_survival


def test_final_lineage_rows_use_clear_population_naming_and_sorting():
    params = LineageParameters(
        seed_population=100,
        population_cap=80,
        generations=2,
        mutation_rate=0.3,
        beneficial_mutation_rate=0.8,
        harmful_mutation_rate=0.0,
        lethal_mutation_rate=0.0,
        mutation_effect=0.1,
        randomness=0.0,
        random_seed=4,
    )
    results = simulate_lineage_survival(params)

    rows = _final_lineage_rows(results)
    populations = [int(row["current_population"]) for row in rows]
    original_rows = [row for row in rows if row["lineage_id"] == 1]

    assert rows
    assert populations == sorted(populations, reverse=True)
    assert "size" not in rows[0]
    assert original_rows[0]["lineage_label"] == "original seed lineage"
    assert original_rows[0]["created_generation"] == 0
