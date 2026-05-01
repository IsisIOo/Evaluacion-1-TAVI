import google.generativeai as genai

from app.core.config import settings

genai.configure(api_key=settings.google_api_key)


def get_gemini_client():
    return genai


def get_gemini_model():
    from app.core.llm_factory import get_model_name
    return get_model_name()
