"""
Utilidades de fecha y hora.
"""
from datetime import datetime, timezone


def utcnow() -> datetime:
    """
    Fecha/hora actual en UTC como datetime naive.

    PyMongo devuelve los campos de tipo fecha de BSON como datetime NAIVE en UTC,
    por lo que los valores que se comparan o almacenan con MongoDB deben ser naive
    en UTC (mezclar una fecha aware con una naive lanza TypeError).

    Reemplaza a datetime.utcnow(), que está en desuso.
    """
    return datetime.now(timezone.utc).replace(tzinfo=None)
