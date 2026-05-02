# endpoint para manejar las solicitudes relacionadas con la generación de CVs
import logging
from fastapi import APIRouter, HTTPException
from app.schemas.cv_response import CVResponse
from app.schemas.cv_request import CVRequest
from app.services.llm_service import generate_cv

logger = logging.getLogger(__name__)

cv_router = APIRouter()  # instancia del router para este endpoint

@cv_router.post("/generate", response_model=CVResponse)
async def generate_cv_endpoint(request: CVRequest):
    """
    Recibe el JSON con la estructura completa del formulario desde el frontend,
    llama al servicio LLM y retorna la respuesta estructurada.
    """
    logger.info(f"Recibida solicitud de generación de CV para el usuario_id: {request.user_id}")

    try:
        cv_response = await generate_cv(request)
        return cv_response
    except Exception as e:
        logger.error(f"Error al generar el CV: {e}")
        raise HTTPException(
            status_code=500,
            detail="Error al generar el CV. Por favor, inténtalo de nuevo más tarde."
        )