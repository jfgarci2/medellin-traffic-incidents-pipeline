from datetime import datetime

_DATE_FORMAT = "%Y/%m/%d %H:%M:%S"


def year_month(fecha: str | None) -> tuple[int, int] | None:
    """Devuelve (año, mes) o None si la fecha no se puede leer.

    El shapefile trae la fecha como texto, por ejemplo '2014/01/15 00:00:00'.
    None manda la fila a cuarentena en lugar de perderla.
    """
    if not isinstance(fecha, str):
        return None
    text = fecha.strip()
    if not text:
        return None
    try:
        parsed = datetime.strptime(text, _DATE_FORMAT)
    except ValueError:
        return None
    return parsed.year, parsed.month
