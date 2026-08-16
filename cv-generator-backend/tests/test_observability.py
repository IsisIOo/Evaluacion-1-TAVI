"""Tests para app/core/observability.py: cálculo de costos y logs."""

import pytest
from unittest.mock import patch, AsyncMock

from app.core.observability import AsyncObservabilityCallback


class TestCalculateCost:
    def setup_method(self):
        self.callback = AsyncObservabilityCallback(user_id="test-user")

    def test_zero_cost_for_unknown_model(self):
        cost = self.callback._calculate_cost("unknown-model", 1000, 500)
        assert cost == 0.0

    def test_zero_cost_for_zero_tokens(self):
        cost = self.callback._calculate_cost("gemini-1.5-pro", 0, 0)
        assert cost == 0.0

    def test_cost_for_known_model(self):
        # gemini-1.5-pro: input 0.0004/1M, output 0.0008/1M
        cost = self.callback._calculate_cost("gemini-1.5-pro", 1_000_000, 500_000)
        assert cost == pytest.approx(0.0004 + 0.0004)

    def test_cost_is_float(self):
        cost = self.callback._calculate_cost("gemini-1.5-pro", 655, 984)
        assert isinstance(cost, float)


class TestSaveLog:
    @pytest.mark.asyncio
    async def test_saves_log_to_mongo(self):
        callback = AsyncObservabilityCallback(user_id="user-1", request_id="req-1")
        fake_db = AsyncMock()
        fake_db.observability_logs = AsyncMock()
        fake_db.observability_logs.insert_one = AsyncMock()

        with patch("app.core.observability.get_db", return_value=fake_db):
            await callback._save_log({"request_id": "req-1", "status": "success"})

        fake_db.observability_logs.insert_one.assert_awaited_once_with(
            {"request_id": "req-1", "status": "success"}
        )

    @pytest.mark.asyncio
    async def test_does_not_fail_when_db_unavailable(self):
        callback = AsyncObservabilityCallback(user_id="user-1", request_id="req-1")

        with patch("app.core.observability.get_db", side_effect=Exception("no db")):
            # No debe lanzar excepción
            await callback._save_log({"request_id": "req-1"})


class TestOnLlmError:
    @pytest.mark.asyncio
    async def test_logs_error_entry(self):
        callback = AsyncObservabilityCallback(user_id="user-1", request_id="req-1")
        fake_db = AsyncMock()
        fake_db.observability_logs.insert_one = AsyncMock()

        with patch("app.core.observability.get_db", return_value=fake_db):
            await callback.on_llm_error(Exception("timeout"))

        insert_call = fake_db.observability_logs.insert_one.call_args[0][0]
        assert insert_call["status"] == "error"
        assert "timeout" in insert_call["error_message"]
