"""Tests para app/services/retention.py: política de retención de CVs."""

from datetime import datetime, timedelta

from app.core.config import settings
from app.core.datetime_utils import utcnow
from app.services.retention import (
    get_expiration_date,
    get_remaining_days,
    get_remaining_seconds,
    is_expired,
    enrich_cv_with_retention,
    SECONDS_PER_DAY,
)


class TestGetExpirationDate:
    def test_default_uses_settings_retention_days(self):
        created = datetime(2025, 1, 1)
        expected = created + timedelta(days=settings.CV_RETENTION_DAYS)
        assert get_expiration_date(created) == expected

    def test_custom_retention_days(self):
        created = datetime(2025, 1, 1)
        assert get_expiration_date(created, retention_days=7) == datetime(2025, 1, 8)

    def test_accepts_iso_string(self):
        assert get_expiration_date("2025-01-01T00:00:00Z", retention_days=1) == datetime(2025, 1, 2)

    def test_aware_datetime_is_normalized_to_naive_utc(self):
        created = datetime(2025, 1, 1, tzinfo=datetime.now().astimezone().tzinfo)
        result = get_expiration_date(created, retention_days=1)
        assert result.tzinfo is None
        assert result == created.astimezone(__import__("datetime").timezone.utc).replace(tzinfo=None) + timedelta(days=1)

    def test_none_falls_back_to_now(self):
        result = get_expiration_date(None, retention_days=1)
        assert result > utcnow()


class TestIsExpired:
    def test_recent_cv_is_not_expired(self):
        assert is_expired(utcnow(), now=utcnow()) is False

    def test_old_cv_is_expired(self):
        created = utcnow() - timedelta(days=settings.CV_RETENTION_DAYS + 1)
        assert is_expired(created, now=utcnow()) is True

    def test_absent_date_is_never_expired(self):
        assert is_expired(None, now=utcnow()) is False


class TestGetRemainingSeconds:
    def test_remaining_seconds_positive(self):
        created = utcnow() - timedelta(days=5)
        seconds = get_remaining_seconds(created, now=utcnow())
        assert seconds > 0

    def test_expired_returns_zero(self):
        created = utcnow() - timedelta(days=999)
        assert get_remaining_seconds(created, now=utcnow()) == 0


class TestGetRemainingDays:
    def test_full_days_rounds_up(self):
        # 1 segundo restante de 31 días => 1 día
        now = utcnow()
        created = now - timedelta(days=settings.CV_RETENTION_DAYS) + timedelta(seconds=1)
        assert get_remaining_days(created, now=now) == 1

    def test_partial_days_round_up(self):
        # creado hace 28 días => le quedan 2 días completos
        now = utcnow()
        created = now - timedelta(days=28)
        assert get_remaining_days(created, now=now) == 2

    def test_fresh_cv_reports_full_period(self):
        now = utcnow()
        assert get_remaining_days(now, now=now) == settings.CV_RETENTION_DAYS

    def test_expired_returns_zero(self):
        created = utcnow() - timedelta(days=999)
        assert get_remaining_days(created, now=utcnow()) == 0

    def test_days_match_seconds(self):
        created = utcnow()
        seconds = get_remaining_seconds(created, now=utcnow())
        days = get_remaining_days(created, now=utcnow())
        assert days * SECONDS_PER_DAY >= seconds
        assert (days - 1) * SECONDS_PER_DAY < seconds


class TestEnrichCvWithRetention:
    def test_adds_retention_fields(self, cv_response_data):
        cv = dict(cv_response_data)
        enriched = enrich_cv_with_retention(cv, now=utcnow())

        assert "expires_at" in enriched
        assert "remaining_seconds" in enriched
        assert "remaining_days" in enriched
        assert "is_expired" in enriched
        assert enriched["is_expired"] is False
        assert enriched["remaining_days"] == settings.CV_RETENTION_DAYS
        # No muta el documento original
        assert "expires_at" not in cv

    def test_expired_cv_is_marked(self, cv_response_data):
        cv = dict(cv_response_data)
        cv["created_at"] = utcnow() - timedelta(days=999)
        enriched = enrich_cv_with_retention(cv, now=utcnow())
        assert enriched["is_expired"] is True
        assert enriched["remaining_seconds"] == 0

    def test_expires_at_uses_utc_z_suffix(self, cv_response_data):
        cv = dict(cv_response_data)
        enriched = enrich_cv_with_retention(cv, now=utcnow())
        assert enriched["expires_at"].endswith("Z")
