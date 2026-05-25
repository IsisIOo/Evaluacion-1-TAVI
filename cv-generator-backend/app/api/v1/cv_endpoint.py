# endpoint para manejar las solicitudes relacionadas con la generación de CVs
import logging
from fastapi import APIRouter, HTTPException
from app.schemas.cv_response import CVResponse
from app.schemas.cv_request import CVRequest
from app.services.llm_service import generate_cv
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
        # Generar CV con IA
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
        
    except Exception as e:
        logger.error(f"Error al generar y guardar el CV: {e}")
        raise HTTPException(
            status_code=500,
            detail="Error al generar el CV. Por favor, inténtalo de nuevo más tarde."
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
