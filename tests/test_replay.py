from pathlib import Path

import pyarrow as pa
import pyarrow.parquet as pq

from medellin_incidentes.ingestion.replay import next_unpublished, publish_month, replay


def _write_month(root: Path, year: int, month: int) -> None:
    path = root / f"year={year}" / f"month={month:02d}" / "incidentes.parquet"
    path.parent.mkdir(parents=True)
    pq.write_table(pa.table({"fecha": [f"{year}/{month:02d}/01 00:00:00"]}), path)


def test_replay_publishes_one_month_then_the_next(tmp_path: Path) -> None:
    landing = tmp_path / "landing"
    bucket = tmp_path / "bucket"
    _write_month(landing, 2014, 1)
    _write_month(landing, 2014, 2)

    first = replay(landing, bucket)
    second = replay(landing, bucket)

    assert first is not None and first.parent.name == "month=01"
    assert second is not None and second.parent.name == "month=02"
    assert next_unpublished(landing, bucket) is None


def test_publishing_the_same_month_twice_keeps_one_file(tmp_path: Path) -> None:
    landing = tmp_path / "landing"
    bucket = tmp_path / "bucket"
    _write_month(landing, 2014, 3)

    publish_month(landing, bucket, 2014, 3)
    publish_month(landing, bucket, 2014, 3)

    files = list(bucket.rglob("*.parquet"))
    assert len(files) == 1
