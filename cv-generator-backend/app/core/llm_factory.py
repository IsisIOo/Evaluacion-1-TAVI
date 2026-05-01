from enum import Enum
from typing import Dict

from app.core.config import settings


class GeminiModel(str, Enum):
    GEMINI_3_0_FLASH = "gemini-3.0-flash"
    GEMINI_2_5_FLASH = "gemini-2.5-flash"
    GEMINI_1_5_FLASH = "gemini-1.5-flash"


SUPPORTED_MODELS: Dict[str, str] = {
    GeminiModel.GEMINI_3_0_FLASH.value: "Google Gemini",
    GeminiModel.GEMINI_2_5_FLASH.value: "Google Gemini",
    GeminiModel.GEMINI_1_5_FLASH.value: "Google Gemini",
}


def get_model_name() -> str:
    model_name = settings.model_name.strip()
    if model_name in SUPPORTED_MODELS:
        return model_name
    return GeminiModel.GEMINI_3_0_FLASH.value


def get_model_description() -> str:
    return SUPPORTED_MODELS.get(get_model_name(), "Google Gemini")
