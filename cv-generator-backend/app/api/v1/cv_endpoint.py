# endpoint para manejar las solicitudes relacionadas con la generación de CVs
import logging
from datetime import timedelta
from fastapi import APIRouter, HTTPException
from app.core.config import settings
from app.core.datetime_utils import utcnow
from app.schemas.cv_response import CVResponse
from app.schemas.cv_request import CVRequest
from app.services.retention import enrich_cv_with_retention, is_expired
from app.db.cv_repository import CVRepository

logger = logging.getLogger(__name__)

cv_router = APIRouter()  # instancia del router para este endpoint

@cv_router.post("/generate", response_model=dict)
async def generate_cv_endpoint(request: CVRequest):
    """
    Recibe el JSON con la estructura completa del formulario desde el frontend,
    llama al servicio LLM, guarda el CV en MongoDB y retorna la respuesta estructurada.
    """
    logger.info(f"Recibida solicitud de generación de CV para el usuario_id: {request.user_id}")

    try:
        # Importación perezosa para no arrastrar las dependencias pesadas del LLM
        # al importar el módulo (mantiene los tests de los demás endpoints livianos).
        from app.services import llm_service

        # Generar CV con IA
        cv_response = await llm_service.generate_cv(request)
        
        # Guardar CV en MongoDB
        cv_id = await CVRepository.save_cv(cv_response, request.user_id)
        
        logger.info(f"CV guardado en MongoDB con ID: {cv_id}")
        
        # Retornar respuesta con el CV generado, ID de MongoDB y tiempo de retención
        retention_seconds = settings.CV_RETENTION_DAYS * 86400
        expires_at = utcnow() + timedelta(days=settings.CV_RETENTION_DAYS)
        return {
            "success": True,
            "cv_id": cv_id,
            "user_id": request.user_id,
            "cv_data": cv_response.model_dump(),
            "expires_at": expires_at.isoformat() + "Z",
            "remaining_seconds": retention_seconds,
            "remaining_days": settings.CV_RETENTION_DAYS,
        }
        
    except HTTPException:
        raise
    except TimeoutError as e:
        logger.error(f"Timeout al generar CV: {e}")
        raise HTTPException(status_code=504, detail=str(e))
    except llm_service.QuotaExceededError as e:
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
    Obtiene un CV específico por su ID desde MongoDB.
    Si el CV superó su periodo de retención se elimina y responde 404
    para proteger los datos personales.
    """
    logger.info(f"Solicitando CV con ID: {cv_id}")
    
    try:
        cv = await CVRepository.get_cv_by_id(cv_id)
        
        if not cv:
            raise HTTPException(
                status_code=404,
                detail="CV no encontrado"
            )

        # Retención: si el CV ya venció, se elimina y se responde como no existente
        if is_expired(cv.get("created_at")):
            logger.info(f"CV {cv_id} vencido por política de retención. Eliminando...")
            await CVRepository.delete_cv(cv_id)
            raise HTTPException(
                status_code=404,
                detail="CV no encontrado"
            )
        
        cv = enrich_cv_with_retention(cv)
        
        return {
            "success": True,
            "cv_data": cv
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error al obtener CV {cv_id}: {e}")
        raise HTTPException(
            status_code=500,
            detail="Error al obtener el CV"
        )


@cv_router.get("/user/{user_id}", response_model=dict)
async def get_user_cvs_endpoint(user_id: str):
    """
    Obtiene todos los CVs vigentes de un usuario.
    Los CVs vencidos por política de retención se eliminan y no se listan.
    """
    logger.info(f"Solicitando CVs para usuario: {user_id}")
    
    try:
        cvs = await CVRepository.get_cvs_by_user(user_id)
        
        active_cvs = []
        for cv in cvs:
            if is_expired(cv.get("created_at")):
                logger.info(f"CV {cv.get('_id')} vencido por política de retención. Eliminando...")
                await CVRepository.delete_cv(cv.get("_id"))
                continue
            active_cvs.append(enrich_cv_with_retention(cv))
        
        return {
            "success": True,
            "user_id": user_id,
            "cvs": active_cvs,
            "total": len(active_cvs)
        }
        
    except Exception as e:
        logger.error(f"Error al obtener CVs del usuario {user_id}: {e}")
        raise HTTPException(
            status_code=500,
            detail="Error al obtener los CVs"
        )
