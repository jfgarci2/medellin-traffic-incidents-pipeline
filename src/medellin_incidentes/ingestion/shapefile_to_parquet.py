"""Convierte el shapefile de incidentes a Parquet, una carpeta por mes."""

import argparse
import logging
import shutil
from pathlib import Path

import pyarrow as pa
import pyarrow.parquet as pq
import pyogrio

from medellin_incidentes.ingestion.partitions import year_month

logger = logging.getLogger(__name__)

DEFAULT_SOURCE = Path("base datos") / "Incidentes2014_2022.shp"
DEFAULT_OUTPUT = Path("data") / "landing" / "incidentes"
REJECT_REASON = "fecha_invalida"


def read_attributes(source: Path) -> pa.Table:
    """Lee las columnas del shapefile, sin la geometría."""
    _metadata, table = pyogrio.read_arrow(source, read_geometry=False, encoding="UTF-8")
    return table


def split_by_month(table: pa.Table) -> tuple[dict[tuple[int, int], pa.Table], pa.Table]:
    """Separa filas con fecha válida de las que van a cuarentena."""
    keys = [year_month(fecha) for fecha in table.column("fecha").to_pylist()]
    groups: dict[tuple[int, int], list[int]] = {}
    invalid_rows: list[int] = []
    for index, key in enumerate(keys):
        if key is None:
            invalid_rows.append(index)
        else:
            groups.setdefault(key, []).append(index)

    valid = {key: table.take(pa.array(indexes)) for key, indexes in groups.items()}
    quarantine = table.take(pa.array(invalid_rows)) if invalid_rows else table.slice(0, 0)
    if quarantine.num_rows:
        quarantine = quarantine.append_column(
            "_reject_reason",
            pa.array([REJECT_REASON] * quarantine.num_rows),
        )
    return valid, quarantine


def reconcile(read_rows: int, valid_rows: int, quarantined_rows: int) -> None:
    """Falla si alguna fila se perdió entre la lectura y las dos salidas."""
    if read_rows != valid_rows + quarantined_rows:
        raise RuntimeError(
            "reconciliacion fallida: "
            f"leidas={read_rows} validas={valid_rows} cuarentena={quarantined_rows}"
        )


def write_landing(
    groups: dict[tuple[int, int], pa.Table],
    quarantine: pa.Table,
    output: Path,
) -> int:
    """Escribe cada mes en su carpeta. Si se corre otra vez, reemplaza la salida."""
    output.parent.mkdir(parents=True, exist_ok=True)
    temporary = output.parent / f".{output.name}.tmp"
    if temporary.exists():
        shutil.rmtree(temporary)

    file_count = 0
    for (year, month), part in sorted(groups.items()):
        path = temporary / f"year={year}" / f"month={month:02d}" / "incidentes.parquet"
        path.parent.mkdir(parents=True, exist_ok=True)
        pq.write_table(part, path, compression="zstd")
        file_count += 1

    if quarantine.num_rows:
        path = temporary / "_quarantine" / "incidentes.parquet"
        path.parent.mkdir(parents=True, exist_ok=True)
        pq.write_table(quarantine, path, compression="zstd")
        file_count += 1

    if output.exists():
        shutil.rmtree(output)
    temporary.rename(output)
    return file_count


def ingest(source: Path, output: Path) -> None:
    table = read_attributes(source)
    groups, quarantine = split_by_month(table)
    valid_rows = sum(part.num_rows for part in groups.values())
    reconcile(table.num_rows, valid_rows, quarantine.num_rows)
    file_count = write_landing(groups, quarantine, output)
    logger.info(
        "leidas=%s validas=%s cuarentena=%s archivos=%s salida=%s",
        table.num_rows,
        valid_rows,
        quarantine.num_rows,
        file_count,
        output,
    )


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    parser = argparse.ArgumentParser(description="Shapefile de incidentes a Parquet por mes")
    parser.add_argument("--source", type=Path, default=DEFAULT_SOURCE)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    ingest(args.source, args.output)
