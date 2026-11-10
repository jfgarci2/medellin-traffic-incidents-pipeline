from pathlib import Path

import pyarrow as pa
import pytest

from medellin_incidentes.ingestion.shapefile_to_parquet import (
    reconcile,
    split_by_month,
    write_landing,
)


def test_split_sends_bad_dates_to_quarantine() -> None:
    table = pa.table({"fecha": ["2014/01/15 00:00:00", "sin fecha", None]})
    groups, quarantine = split_by_month(table)

    assert list(groups) == [(2014, 1)]
    assert groups[(2014, 1)].num_rows == 1
    assert quarantine.num_rows == 2
    assert quarantine.column("_reject_reason").to_pylist() == ["fecha_invalida", "fecha_invalida"]


def test_reconcile_fails_when_a_row_disappears() -> None:
    with pytest.raises(RuntimeError, match="reconciliacion fallida"):
        reconcile(read_rows=3, valid_rows=1, quarantined_rows=1)


def test_write_replaces_the_previous_output(tmp_path: Path) -> None:
    table = pa.table({"fecha": ["2014/01/15 00:00:00"]})
    groups, quarantine = split_by_month(table)
    output = tmp_path / "incidentes"

    write_landing(groups, quarantine, output)
    write_landing(groups, quarantine, output)

    files = list(output.rglob("*.parquet"))
    assert [path.relative_to(output).as_posix() for path in files] == [
        "year=2014/month=01/incidentes.parquet"
    ]
