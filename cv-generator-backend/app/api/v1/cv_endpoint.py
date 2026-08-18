# endpoint para manejar las solicitudes relacionadas con la generación de CVs
import logging
from datetime import datetime, timezone, timedelta
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException
from app.core.config import settings
from app.core.datetime_utils import utcnow
from app.core.dependencies import get_current_user, get_current_user_optional
from app.db.models import UserDocument
from app.db.session import get_db
from app.schemas.cv_request import CVRequest
from app.services.llm_service import generate_cv, QuotaExceededError
from app.services.retention import enrich_cv_with_retention, is_expired

from app.db.cv_repository import CVRepository

logger = logging.getLogger(__name__)

cv_router = APIRouter()

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
async def generate_cv_endpoint(
    request: CVRequest,
    current_user: Optional[UserDocument] = Depends(get_current_user_optional),
):
    """
    Genera un CV con IA. Permite acceso anónimo: un usuario anónimo recibe el CV
    generado pero NO se persiste en MongoDB (política de minimización de datos
    personales). Si hay sesión autenticada, el CV se guarda bajo el id del token.
    """
    logger.info(f"Recibida solicitud de generación de CV para el usuario_id: {request.user_id}")

    try:
        await check_user_token_quota(request.user_id)

        cv_response = await generate_cv(request)

        # Persistir solo si el usuario está autenticado (datos personales protegidos).
        # El dueño siempre es el usuario del token, no el user_id del body.
        cv_id = None
        if current_user is not None:
            cv_id = await CVRepository.save_cv(cv_response, current_user.id)
            logger.info(f"CV guardado en MongoDB con ID: {cv_id} para usuario {current_user.id}")
        else:
            logger.info("CV generado por usuario anónimo: no se persiste por política de datos personales")

        retention_seconds = settings.CV_RETENTION_DAYS * 86400
        expires_at = utcnow() + timedelta(days=settings.CV_RETENTION_DAYS)
        return {
            "success": True,
            "cv_id": cv_id,
            "user_id": current_user.id if current_user else request.user_id,
            "persisted": current_user is not None,
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
    except QuotaExceededError as e:
        logger.error(f"Cuota de API agotada: {e}")
        raise HTTPException(status_code=429, detail=str(e))
    except Exception as e:
        logger.error(f"Error al generar y guardar el CV: {e}")
        raise HTTPException(
            status_code=500,
            detail="Error al generar el CV. Por favor, inténtalo de nuevo más tarde."
        )


@cv_router.get("/{cv_id}", response_model=dict)
async def get_cv_endpoint(
    cv_id: str,
    current_user: UserDocument = Depends(get_current_user),
):
    """
    Obtiene un CV específico por su ID. Exige autenticación y que el CV
    pertenezca al usuario autenticado (evita acceso a CVs de terceros).
    Si el CV superó su periodo de retención se elimina y responde 404.
    """
    logger.info(f"Solicitando CV con ID: {cv_id} por usuario {current_user.id}")

    try:
        cv = await CVRepository.get_cv_by_id(cv_id)

        if not cv:
            raise HTTPException(
                status_code=404,
                detail="CV no encontrado"
            )

        # Control de propiedad: solo el dueño puede leer su CV
        if cv.get("user_id") != current_user.id:
            raise HTTPException(
                status_code=403,
                detail="No tienes permiso para acceder a este CV"
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
async def get_user_cvs_endpoint(
    user_id: str,
    current_user: UserDocument = Depends(get_current_user),
):
    """
    Obtiene los CVs vigentes del usuario autenticado. Exige que el user_id
    solicitado sea el del propio usuario autenticado.
    Los CVs vencidos por política de retención se eliminan y no se listan.
    """
    logger.info(f"Solicitando CVs para usuario: {user_id}")

    if user_id != current_user.id:
        raise HTTPException(
            status_code=403,
            detail="No tienes permiso para ver los CVs de este usuario"
        )

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
