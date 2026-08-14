"""
Política de retención de CVs para protección de datos personales.

Los CVs almacenan datos personales, por lo que solo deben permanecer
disponibles durante un periodo limitado (configurable vía CV_RETENTION_DAYS).
Este módulo concentra la lógica de expiración: cálculo de fecha de vencimiento,
tiempo restante y utilidades para enriquecer las respuestas hacia el frontend.
"""
import math
from datetime import datetime, timedelta, timezone
from typing import Optional, Union

from app.core.config import settings
from app.core.datetime_utils import utcnow

SECONDS_PER_DAY = 86400


def _to_datetime(value: Union[datetime, str, None]) -> Optional[datetime]:
    """
    Normaliza un valor de fecha a datetime naive en UTC.
    Acepta datetime o string ISO 8601 (con o sin Z/offset).
    """
    if value is None:
        return None
    if isinstance(value, datetime):
        if value.tzinfo is not None:
            return value.astimezone(timezone.utc).replace(tzinfo=None)
        return value
    if isinstance(value, str):
        try:
            parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
            if parsed.tzinfo is not None:
                parsed = parsed.astimezone(timezone.utc).replace(tzinfo=None)
            return parsed
        except ValueError:
            return None
    return None


def get_expiration_date(created_at, retention_days: Optional[int] = None) -> datetime:
    """
    Fecha en la que el CV debe eliminarse: created_at + periodo de retención.

    Args:
        created_at: fecha de creación del CV (datetime, ISO string o None).
        retention_days: días de retención. Si es None usa settings.CV_RETENTION_DAYS.

    Returns:
        datetime naive en UTC con la fecha de expiración.
    """
    created = _to_datetime(created_at) or utcnow()
    days = retention_days if retention_days is not None else settings.CV_RETENTION_DAYS
    return created + timedelta(days=days)


def get_remaining_seconds(created_at, now: Optional[datetime] = None) -> int:
    """
    Segundos que le quedan de vida al CV (0 si ya está vencido).
    """
    created = _to_datetime(created_at)
    if created is None:
        created = utcnow()
    current = _to_datetime(now) or utcnow()
    expires_at = get_expiration_date(created)
    return max(0, int((expires_at - current).total_seconds()))


def get_remaining_days(created_at, now: Optional[datetime] = None) -> int:
    """
    Días completos restantes redondeados hacia arriba (0 si ya está vencido).
    """
    seconds = get_remaining_seconds(created_at, now=now)
    if seconds <= 0:
        return 0
    return math.ceil(seconds / SECONDS_PER_DAY)


def is_expired(created_at, now: Optional[datetime] = None) -> bool:
    """
    True si el CV superó su periodo de retención y debe eliminarse.
    """
    return get_remaining_seconds(created_at, now=now) <= 0


def enrich_cv_with_retention(
    cv: dict,
    now: Optional[datetime] = None,
    retention_days: Optional[int] = None,
) -> dict:
    """
    Agrega al documento del CV la información de retención para el frontend:
    - expires_at: fecha de expiración en ISO 8601 (UTC, con Z).
    - remaining_seconds: segundos restantes de vida útil.
    - remaining_days: días restantes redondeados hacia arriba.
    - is_expired: booleano que indica si ya superó la retención.

    No muta el documento original.
    """
    enriched = dict(cv)
    created_at = cv.get("created_at")
    created = _to_datetime(created_at) or utcnow()
    expires_at = get_expiration_date(created, retention_days=retention_days)

    enriched["expires_at"] = expires_at.isoformat() + "Z"
    enriched["remaining_seconds"] = get_remaining_seconds(created, now=now)
    enriched["remaining_days"] = get_remaining_days(created, now=now)
    enriched["is_expired"] = is_expired(created, now=now)
    return enriched
