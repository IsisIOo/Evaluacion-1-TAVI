"""Tests para app/services/llm_service.py: prompt, detección de cuotas y RAG."""

import json
import asyncio
from unittest.mock import patch, MagicMock, AsyncMock, mock_open

import pytest

from app.schemas.cv_response import CVResponse
from app.services.llm_service import (
    _is_quota_error,
    _build_cv_prompt,
    _get_matching_job_offers,
    QuotaExceededError,
    generate_cv,
)


class TestIsQuotaError:
    def test_detects_quota_keyword(self):
        assert _is_quota_error("Quota exceeded for API") is True

    def test_detects_resource_exhausted(self):
        assert _is_quota_error("Resource has been exhausted for this project") is True

    def test_detects_rate_limit(self):
        assert _is_quota_error("rate limit reached") is True

    def test_detects_http_429(self):
        assert _is_quota_error("HTTP 429 Too Many Requests") is True

    def test_detects_daily_limit(self):
        assert _is_quota_error("daily limit exceeded") is True

    def test_returns_false_for_unrelated_error(self):
        assert _is_quota_error("Connection refused") is False

    def test_returns_false_for_empty_string(self):
        assert _is_quota_error("") is False


class TestBuildCvPrompt:
    def test_prompt_contains_role(self, cv_request):
        prompt = _build_cv_prompt(cv_request)
        assert "experto en recursos humanos" in prompt

    def test_prompt_contains_personal_data(self, cv_request):
        prompt = _build_cv_prompt(cv_request)
        assert "Jaime Gustamante" in prompt
        assert "jaime@gmail.com" in prompt
        assert "+56 9 1234 5678" in prompt
        assert "Santiago" in prompt

    def test_prompt_contains_perfil_data(self, cv_request):
        prompt = _build_cv_prompt(cv_request)
        assert "3" in prompt
        assert "Desarrollo web y APIs en Python" in prompt

    def test_prompt_contains_experiencias(self, cv_request):
        prompt = _build_cv_prompt(cv_request)
        assert "TechCorp" in prompt
        assert "Desarrollador Backend" in prompt

    def test_prompt_contains_formacion(self, cv_request):
        prompt = _build_cv_prompt(cv_request)
        assert "Ingeniería Civil en Informática" in prompt
        assert "Universidad de Santiago" in prompt

    def test_prompt_contains_habilidades(self, cv_request):
        prompt = _build_cv_prompt(cv_request)
        assert "Python, FastAPI, MongoDB" in prompt

    def test_prompt_contains_ats_criteria(self, cv_request):
        prompt = _build_cv_prompt(cv_request)
        assert "CRITERIOS ATS" in prompt

    def test_prompt_without_rag_context(self, cv_request):
        prompt = _build_cv_prompt(cv_request, target_jobs_context="")
        assert "OFERTAS DE TRABAJO REALES" not in prompt

    def test_prompt_with_rag_context(self, cv_request):
        context = "Oferta #1 (Área: Tecnología):\nSe busca programador..."
        prompt = _build_cv_prompt(cv_request, target_jobs_context=context)
        assert "OFERTAS DE TRABAJO REALES" in prompt
        assert "Se busca programador..." in prompt


class TestGetMatchingJobOffers:
    def test_returns_empty_when_pointer_missing(self, tmp_path):
        with patch("app.services.llm_service.POINTER_PATH", str(tmp_path / "missing.json")):
            result = _get_matching_job_offers("query")
        assert result == ""

    def test_returns_empty_when_vector_dir_missing(self, tmp_path):
        pointer = tmp_path / "active_pointer.json"
        pointer.write_text(json.dumps({"active": "blue"}), encoding="utf-8")
        with patch("app.services.llm_service.POINTER_PATH", str(pointer)):
            with patch("app.services.llm_service.DATA_DIR", str(tmp_path)):
                result = _get_matching_job_offers("query")
        assert result == ""

    def test_returns_context_when_matches_found(self, tmp_path):
        pointer = tmp_path / "active_pointer.json"
        pointer.write_text(json.dumps({"active": "blue"}), encoding="utf-8")
        vector_dir = tmp_path / "vector_store_blue"
        vector_dir.mkdir(parents=True)

        fake_doc = MagicMock()
        fake_doc.page_content = "Se busca desarrollador Python con experiencia en APIs."
        fake_doc.metadata = {"area_trabajo": "Tecnología"}

        fake_db = MagicMock()
        fake_db.similarity_search.return_value = [fake_doc]

        with patch("app.services.llm_service.POINTER_PATH", str(pointer)):
            with patch("app.services.llm_service.DATA_DIR", str(tmp_path)):
                with patch("app.services.llm_service.HuggingFaceEmbeddings") as mock_emb:
                    with patch("app.services.llm_service.Chroma") as mock_chroma:
                        mock_chroma.return_value = fake_db
                        result = _get_matching_job_offers("programador python", k=1)

        assert "Oferta #1" in result
        assert "Tecnología" in result
        assert "Se busca desarrollador Python" in result

    def test_handles_errors_gracefully(self):
        with patch("app.services.llm_service.os.path.exists", return_value=False):
            result = _get_matching_job_offers("query")
        assert result == ""


class TestGenerateCv:
    @pytest.mark.asyncio
    async def test_returns_cv_response_directly(self, cv_request, cv_response):
        fake_llm = MagicMock()
        fake_structured = AsyncMock()
        fake_structured.ainvoke.return_value = cv_response
        fake_llm.with_structured_output.return_value = fake_structured

        with patch("app.services.llm_service.get_deterministic_llm", return_value=fake_llm):
            with patch("app.services.llm_service._get_matching_job_offers", return_value=""):
                result = await generate_cv(cv_request)

        assert result == cv_response
        fake_llm.with_structured_output.assert_called_once()
        fake_structured.ainvoke.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_validates_dict_response(self, cv_request, cv_response_data):
        fake_llm = MagicMock()
        fake_structured = AsyncMock()
        fake_structured.ainvoke.return_value = dict(cv_response_data)
        fake_llm.with_structured_output.return_value = fake_structured

        with patch("app.services.llm_service.get_deterministic_llm", return_value=fake_llm):
            with patch("app.services.llm_service._get_matching_job_offers", return_value=""):
                result = await generate_cv(cv_request)

        assert isinstance(result, CVResponse)
        assert result.personal.nombre_completo == "Jaime Gustamante"

    @pytest.mark.asyncio
    async def test_raises_quota_error(self, cv_request):
        fake_llm = MagicMock()
        fake_structured = AsyncMock()
        fake_structured.ainvoke.side_effect = RuntimeError("Resource has been exhausted quota")
        fake_llm.with_structured_output.return_value = fake_structured

        with patch("app.services.llm_service.get_deterministic_llm", return_value=fake_llm):
            with patch("app.services.llm_service._get_matching_job_offers", return_value=""):
                with pytest.raises(QuotaExceededError):
                    await generate_cv(cv_request)

    @pytest.mark.asyncio
    async def test_raises_timeout(self, cv_request):
        fake_llm = MagicMock()
        fake_structured = AsyncMock()
        fake_structured.ainvoke.side_effect = asyncio.TimeoutError()
        fake_llm.with_structured_output.return_value = fake_structured

        with patch("app.services.llm_service.get_deterministic_llm", return_value=fake_llm):
            with patch("app.services.llm_service._get_matching_job_offers", return_value=""):
                with pytest.raises(TimeoutError):
                    await generate_cv(cv_request)

    @pytest.mark.asyncio
    async def test_raises_runtime_error_on_generic_failure(self, cv_request):
        fake_llm = MagicMock()
        fake_structured = AsyncMock()
        fake_structured.ainvoke.side_effect = Exception("boom")
        fake_llm.with_structured_output.return_value = fake_structured

        with patch("app.services.llm_service.get_deterministic_llm", return_value=fake_llm):
            with patch("app.services.llm_service._get_matching_job_offers", return_value=""):
                with pytest.raises(RuntimeError):
                    await generate_cv(cv_request)
