from mrrm.formatting import format_count_compact


def test_format_count_compact_keeps_small_counts_readable():
    assert format_count_compact(0) == "0"
    assert format_count_compact(12_345) == "12,345"
    assert format_count_compact(99_999) == "99,999"


def test_format_count_compact_uses_suffixes_for_six_digits_and_above():
    assert format_count_compact(100_000) == "100k"
    assert format_count_compact(123_456) == "123k"
    assert format_count_compact(123_000_067) == "123M"
    assert format_count_compact(1_234_000_000) == "1G"
    assert format_count_compact(1_234_000_000_000) == "1T"
