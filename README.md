# Incidentes de tránsito de Medellín

Pipeline incremental de 370.404 incidentes (2014–2022): del shapefile a un modelo
listo para análisis.

## Arquitectura

```mermaid
flowchart LR
    A[Shapefile] --> B[Parquet por mes]
    B --> C[BigQuery raw]
    C --> D[dbt]
    D --> E[Airflow]
```

| Pieza | Estado |
|---|---|
| Proyecto Python, ruff, pre-commit | Listo |
| Shapefile a Parquet | F1 |
| BigQuery, dbt, Airflow | Después |

Los datos no van en Git. Van en `data/`, que está ignorada.

## Revisar el código

```powershell
uv sync
uv run ruff check .
```
