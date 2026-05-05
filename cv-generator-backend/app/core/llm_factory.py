import logging
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_community.chat_models import ChatLlamaCpp
from app.core.config import settings

logger = logging.getLogger(__name__)

# Inicializa los modelos una sola vez para que estén disponibles en toda la aplicación
# Definimos parámetros claros de temperatura, top_p, top_k y tokens.

deterministic_llm = ChatGoogleGenerativeAI(
    model=settings.MODEL_NAME,
    google_api_key=settings.GEMINI_API_KEY,
    temperature=settings.TEMPERATURE,
    top_p=settings.TOP_P,
    top_k=settings.TOP_K,
    max_tokens=settings.MAX_TOKENS,
)

creative_llm = ChatGoogleGenerativeAI(
    model=settings.MODEL_NAME,
    google_api_key=settings.GEMINI_API_KEY,
    temperature=0.8,
    top_p=0.95,
    top_k=40,
    max_tokens=settings.MAX_TOKENS,
)


def get_deterministic_llm() -> ChatGoogleGenerativeAI:
    return deterministic_llm


def get_creative_llm() -> ChatGoogleGenerativeAI:
    return creative_llm


def get_local_llm() -> ChatLlamaCpp:
    """
    Carga y devuelve un LLM local GGUF usando LlamaCpp.
    """
    model_path = settings.LOCAL_MODEL_PATH
    try:
        local_llm = ChatLlamaCpp(
            model_path=model_path,
            temperature=settings.TEMPERATURE,
            top_p=settings.TOP_P,
            top_k=settings.TOP_K,
            max_tokens=settings.MAX_TOKENS,
            n_ctx=4096,
        )
        return local_llm
    except Exception as e:
        logger.exception("Error al cargar el modelo local: %s", e)
        raise
