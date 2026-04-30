# inicializa los modelos y pipelines una sola vez para que estén disponibles en toda la aplicación 
import logging
from langchain_google_genai import ChatGoogleGenerativeAI
from app.core.config import settings

logger = logging.getLogger(__name__)

# [Para Toto] Ejemplo de modelo 1: Modelo determinista
deterministic_llm = ChatGoogleGenerativeAI(
    model=settings.MODEL_NAME,
    google_api_key=settings.GEMINI_API_KEY,
    temperature=0.1,
    max_tokens=settings.MAX_TOKENS,
)

# [Para Toto] Ejemplo de modelo 2: Modelo creativo
creative_llm = ChatGoogleGenerativeAI(
    model=settings.MODEL_NAME,
    google_api_key=settings.GEMINI_API_KEY,
    temperature=0.8,
    max_tokens=settings.MAX_TOKENS,
)

# getters para acceder a los modelos desde otros módulos
def get_deterministic_llm() -> ChatGoogleGenerativeAI:
    return deterministic_llm

def get_creative_llm() -> ChatGoogleGenerativeAI:
    return creative_llm