from medellin_incidentes.ingestion.partitions import year_month


def test_reads_year_and_month() -> None:
    assert year_month("2014/01/15 00:00:00") == (2014, 1)


def test_rejects_empty_date() -> None:
    assert year_month("") is None
    assert year_month("   ") is None


def test_rejects_bad_text() -> None:
    assert year_month("sin fecha") is None


def test_rejects_missing_date() -> None:
    assert year_month(None) is None
