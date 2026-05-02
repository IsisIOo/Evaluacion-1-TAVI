import logging
import google.generativeai as genai
from app.core.config import settings

logger = logging.getLogger(__name__)

# Configurar el SDK de Google
if settings.GEMINI_API_KEY:
    genai.configure(api_key=settings.GEMINI_API_KEY)
    logger.info("Google Generative AI configurado correctamente.")

def get_model():
    """Retorna la instancia del modelo configurada."""
    # Usamos response_mime_type para forzar salida JSON nativa
    return genai.GenerativeModel(
        model_name=settings.MODEL_NAME,
        generation_config={"response_mime_type": "application/json"}
    )