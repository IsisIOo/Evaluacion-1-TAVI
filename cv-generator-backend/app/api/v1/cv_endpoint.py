# endpoint para manejar las solicitudes relacionadas con la generación de CVs
import logging
from datetime import datetime, timezone, timedelta
from fastapi import APIRouter, HTTPException
from app.core.config import settings
from app.db.session import get_db
from app.schemas.cv_response import CVResponse
from app.schemas.cv_request import CVRequest
from app.services.llm_service import generate_cv, QuotaExceededError

from app.db.cv_repository import CVRepository

logger = logging.getLogger(__name__)

cv_router = APIRouter()  # instancia del router para este endpoint

async def check_user_token_quota(user_id: str):
    """
    Verifica si el user_id ha superado el límite diario de tokens en observability_logs.
    """
    if settings.DAILY_USER_TOKEN_LIMIT <= 0:
        return

    try:
        db = get_db()
        if db is None:
            return

        yesterday = datetime.now(timezone.utc) - timedelta(hours=24)
        pipeline = [
            {
                "$match": {
                    "user_id": user_id,
                    "timestamp": {"$gte": yesterday},
                    "status": "success"
                }
            },
            {
                "$group": {
                    "_id": "$user_id",
                    "total_tokens_used": {"$sum": "$total_tokens"}
                }
            }
        ]
        result = await db.observability_logs.aggregate(pipeline).to_list(length=1)
        if result:
            used_tokens = result[0].get("total_tokens_used", 0)
            if used_tokens >= settings.DAILY_USER_TOKEN_LIMIT:
                logger.warning(f"Usuario {user_id} superó la cuota diaria de tokens ({used_tokens}/{settings.DAILY_USER_TOKEN_LIMIT})")
                raise HTTPException(
                    status_code=429,
                    detail=f"Has alcanzado el límite diario de {settings.DAILY_USER_TOKEN_LIMIT} tokens. Intenta nuevamente más tarde."
                )
    except HTTPException:
        raise
    except Exception as e:
        logger.warning(f"Error al verificar la cuota diaria de tokens de {user_id}: {e}")

@cv_router.post("/generate", response_model=dict)
async def generate_cv_endpoint(request: CVRequest):
    """
    Recibe el JSON con la estructura completa del formulario desde el frontend,
    verifica cuotas, llama al servicio LLM (con caché), guarda el CV en MongoDB y retorna la respuesta.
    """
    logger.info(f"Recibida solicitud de generación de CV para el usuario_id: {request.user_id}")

    try:
        # Verificar cuota diaria del usuario
        await check_user_token_quota(request.user_id)

        # Generar CV con IA (o recuperar de caché con 0 tokens)
        cv_response = await generate_cv(request)
        
        # Guardar CV en MongoDB
        cv_id = await CVRepository.save_cv(cv_response, request.user_id)
        
        logger.info(f"CV guardado en MongoDB con ID: {cv_id}")
        
        # Retornar respuesta con el CV generado e ID de MongoDB
        return {
            "success": True,
            "cv_id": cv_id,
            "user_id": request.user_id,
            "cv_data": cv_response.model_dump()
        }
        
    except HTTPException:
        raise
    except TimeoutError as e:
        logger.error(f"Timeout al generar CV: {e}")
        raise HTTPException(status_code=504, detail=str(e))
    except QuotaExceededError as e:
        logger.error(f"Cuota de API agotada: {e}")
        raise HTTPException(status_code=429, detail=str(e))
    except Exception as e:
        logger.error(f"Error al generar y guardar el CV: {e}")
        raise HTTPException(
            status_code=500,
            detail=str(e) if str(e) else "Error al generar el CV. Por favor, inténtalo de nuevo más tarde."
        )


@cv_router.get("/{cv_id}", response_model=dict)
async def get_cv_endpoint(cv_id: str):
    """
    Obtiene un CV específico por su ID desde MongoDB
    """
    logger.info(f"Solicitando CV con ID: {cv_id}")
    
    try:
        cv = await CVRepository.get_cv_by_id(cv_id)
        
        if not cv:
            raise HTTPException(
                status_code=404,
                detail="CV no encontrado"
            )
        
        return {
            "success": True,
            "cv_data": cv
        }
        
    except Exception as e:
        logger.error(f"Error al obtener CV {cv_id}: {e}")
        raise HTTPException(
            status_code=500,
            detail="Error al obtener el CV"
        )


@cv_router.get("/user/{user_id}", response_model=dict)
async def get_user_cvs_endpoint(user_id: str):
    """
    Obtiene todos los CVs de un usuario
    """
    logger.info(f"Solicitando CVs para usuario: {user_id}")
    
    try:
        cvs = await CVRepository.get_cvs_by_user(user_id)
        
        return {
            "success": True,
            "user_id": user_id,
            "cvs": cvs,
            "total": len(cvs)
        }
        
    except Exception as e:
        logger.error(f"Error al obtener CVs del usuario {user_id}: {e}")
        raise HTTPException(
            status_code=500,
            detail="Error al obtener los CVs"
        )
