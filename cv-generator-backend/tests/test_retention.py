"""
Tests unitarios de la política de retención de CVs (protección de datos personales).
"""
from datetime import datetime, timedelta

from app.core.datetime_utils import utcnow
from app.services.retention import (
    enrich_cv_with_retention,
    get_expiration_date,
    get_remaining_days,
    get_remaining_seconds,
    is_expired,
)

RETENTION_DAYS = 30
CREATED_AT = datetime(2026, 1, 1, 12, 0, 0)


class TestGetExpirationDate:
    def test_expiration_date_es_creacion_mas_retencion(self):
        expira = get_expiration_date(CREATED_AT, retention_days=RETENTION_DAYS)
        assert expira == datetime(2026, 1, 31, 12, 0, 0)

    def test_acepta_string_iso(self):
        expira = get_expiration_date("2026-01-01T12:00:00", retention_days=RETENTION_DAYS)
        assert expira == datetime(2026, 1, 31, 12, 0, 0)

    def test_acepta_string_con_z(self):
        expira = get_expiration_date("2026-01-01T12:00:00Z", retention_days=RETENTION_DAYS)
        assert expira == datetime(2026, 1, 31, 12, 0, 0)

    def test_sin_created_at_usa_ahora(self):
        antes = utcnow()
        expira = get_expiration_date(None, retention_days=RETENTION_DAYS)
        despues = utcnow() + timedelta(days=RETENTION_DAYS)
        assert antes + timedelta(days=RETENTION_DAYS) <= expira <= despues


class TestGetRemainingSeconds:
    def test_restan_segundos_hasta_la_expiracion(self):
        now = datetime(2026, 1, 16, 12, 0, 0)  # justo a mitad del periodo
        restantes = get_remaining_seconds(CREATED_AT, now=now)
        assert restantes == 15 * 86400

    def test_vencido_devuelve_cero(self):
        now = datetime(2026, 2, 2, 12, 0, 0)
        restantes = get_remaining_seconds(CREATED_AT, now=now)
        assert restantes == 0

    def test_nunca_devuelve_negativos(self):
        now = datetime(2026, 3, 15, 12, 0, 0)
        restantes = get_remaining_seconds(CREATED_AT, now=now)
        assert restantes == 0


class TestGetRemainingDays:
    def test_redondea_hacia_arriba_dias_parciales(self):
        created = datetime(2026, 1, 1, 12, 0, 0)
        now = datetime(2026, 1, 29, 6, 0, 0)  # restan ~2.25 días
        assert get_remaining_days(created, now=now) == 3

    def test_periodo_completo_30_dias(self):
        now = datetime(2026, 1, 1, 12, 0, 0)
        assert get_remaining_days(CREATED_AT, now=now) == 30

    def test_vencido_devuelve_cero(self):
        now = datetime(2026, 2, 2, 12, 0, 0)
        assert get_remaining_days(CREATED_AT, now=now) == 0


class TestIsExpired:
    def test_cv_reciente_no_esta_vencido(self):
        assert is_expired(CREATED_AT, now=datetime(2026, 1, 15, 12, 0, 0)) is False

    def test_cv_en_el_limite_esta_vencido(self):
        now = datetime(2026, 1, 31, 12, 0, 0)  # exactamente al cumplir el periodo
        assert is_expired(CREATED_AT, now=now) is True

    def test_cv_antiguo_esta_vencido(self):
        assert is_expired(CREATED_AT, now=datetime(2026, 2, 20, 12, 0, 0)) is True

    def test_sin_created_at_no_se_marca_vencido(self):
        assert is_expired(None) is False


class TestEnrichCvWithRetention:
    def _cv(self, created_at=None):
        return {"_id": "abc123", "user_id": "user1", "created_at": created_at or CREATED_AT}

    def test_agrega_campos_de_retencion(self):
        now = datetime(2026, 1, 16, 12, 0, 0)
        enriquecido = enrich_cv_with_retention(self._cv(), now=now)

        assert enriquecido["expires_at"] == "2026-01-31T12:00:00Z"
        assert enriquecido["remaining_seconds"] == 15 * 86400
        assert enriquecido["remaining_days"] == 15
        assert enriquecido["is_expired"] is False

    def test_no_muta_el_documento_original(self):
        cv = self._cv()
        original_id = cv["_id"]
        enrich_cv_with_retention(cv)
        assert cv["_id"] == original_id
        assert "remaining_days" not in cv
        assert "expires_at" not in cv

    def test_cv_vencido_marca_is_expired_y_tiempo_cero(self):
        now = datetime(2026, 2, 20, 12, 0, 0)
        enriquecido = enrich_cv_with_retention(self._cv(), now=now)

        assert enriquecido["is_expired"] is True
        assert enriquecido["remaining_seconds"] == 0
        assert enriquecido["remaining_days"] == 0

    def test_respeta_el_valor_por_defecto_de_configuracion(self):
        enriquecido = enrich_cv_with_retention(
            {"_id": "abc", "created_at": utcnow()}
        )
        assert enriquecido["remaining_days"] == 30
        assert enriquecido["is_expired"] is False
        assert enriquecido["expires_at"].endswith("Z")
