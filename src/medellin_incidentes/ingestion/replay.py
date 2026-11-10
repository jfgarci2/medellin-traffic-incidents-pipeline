"""Publica un mes por ejecución, como si la Alcaldía lo entregara cada mes."""

import argparse
import logging
import shutil
from pathlib import Path

logger = logging.getLogger(__name__)

DEFAULT_LANDING = Path("data") / "landing" / "incidentes"
DEFAULT_BUCKET = Path("data") / "bucket" / "incidentes"
PARQUET_NAME = "incidentes.parquet"


def list_months(root: Path) -> list[tuple[int, int]]:
    """Meses que ya tienen un Parquet, en orden cronológico."""
    if not root.exists():
        return []
    months: list[tuple[int, int]] = []
    for path in root.glob("year=*/month=*"):
        if not (path / PARQUET_NAME).is_file():
            continue
        year = int(path.parent.name.removeprefix("year="))
        month = int(path.name.removeprefix("month="))
        months.append((year, month))
    return sorted(months)


def next_unpublished(landing: Path, bucket: Path) -> tuple[int, int] | None:
    """El mes más antiguo que está en landing y todavía no está en el bucket."""
    published = set(list_months(bucket))
    for month in list_months(landing):
        if month not in published:
            return month
    return None


def publish_month(landing: Path, bucket: Path, year: int, month: int) -> Path:
    """Copia un mes al bucket. La misma ruta se sobrescribe si se publica otra vez."""
    source = landing / f"year={year}" / f"month={month:02d}" / PARQUET_NAME
    if not source.is_file():
        raise FileNotFoundError(f"no existe la partición {year}-{month:02d} en {landing}")
    target = bucket / f"year={year}" / f"month={month:02d}" / PARQUET_NAME
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(source, target)
    return target


def replay(
    landing: Path,
    bucket: Path,
    year: int | None = None,
    month: int | None = None,
) -> Path | None:
    if (year is None) != (month is None):
        raise ValueError("pasa year y month juntos, o ninguno")
    if year is None or month is None:
        chosen = next_unpublished(landing, bucket)
        if chosen is None:
            logger.info("no hay meses pendientes")
            return None
        year, month = chosen
    target = publish_month(landing, bucket, year, month)
    logger.info("publicado year=%s month=%02d archivo=%s", year, month, target)
    return target


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    parser = argparse.ArgumentParser(description="Publica un mes de incidentes en el bucket")
    parser.add_argument("--landing", type=Path, default=DEFAULT_LANDING)
    parser.add_argument("--bucket", type=Path, default=DEFAULT_BUCKET)
    parser.add_argument("--year", type=int)
    parser.add_argument("--month", type=int)
    args = parser.parse_args()
    replay(args.landing, args.bucket, args.year, args.month)
