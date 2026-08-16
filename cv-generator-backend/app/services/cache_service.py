import hashlib
import json
import logging
from datetime import datetime, timezone, timedelta
from typing import Optional

from app.core.config import settings
from app.db.session import get_db
from app.schemas.cv_request import CVRequest
from app.schemas.cv_response import CVResponse

logger = logging.getLogger(__name__)

def compute_request_hash(request: CVRequest) -> str:
    """
    Calcula un hash determinista SHA-256 a partir de los datos clave del candidato.
    """
    data = {
        "profesion": request.personal.profesion,
        "experticia": request.perfil.experticia,
        "propuesta_valor": request.perfil.propuesta_valor,
        "experiencias": [
            {
                "cargo": exp.cargo,
                "empresa": exp.empresa,
                "descripcion": exp.descripcion,
                "logros": exp.logros
            } for exp in request.experiencias
        ],
        "habilidades": request.habilidades
    }
    serialized = json.dumps(data, sort_keys=True, ensure_ascii=False)
    return hashlib.sha256(serialized.encode("utf-8")).hexdigest()


async def get_cached_cv_response(request: CVRequest) -> Optional[CVResponse]:
    """
    Busca si existe una respuesta guardada en caché vigente para la solicitud dada.
    Retorna None si la caché está desactivada, vencida o no existe.
    """
    if not settings.ENABLE_SEMANTIC_CACHE:
        return None

    try:
        db = get_db()
        if db is None:
            return None

        req_hash = compute_request_hash(request)
        cached_entry = await db.cv_responses_cache.find_one({"request_hash": req_hash})

        if not cached_entry:
            return None

        # Verificar si la caché no ha expirado (TTL)
        created_at = cached_entry.get("timestamp")
        if created_at:
            if created_at.tzinfo is None:
                created_at = created_at.replace(tzinfo=timezone.utc)
            now = datetime.now(timezone.utc)
            max_age = timedelta(hours=settings.CACHE_TTL_HOURS)
            if now - created_at > max_age:
                logger.info(f"Caché encontrada para hash {req_hash[:8]} pero expiró.")
                return None

        logger.info(f"[CACHE HIT] Respuesta de CV recuperada desde caché para user_id={request.user_id} (0 tokens consumidos)")
        response_data = cached_entry.get("cv_response")
        if response_data:
            return CVResponse.model_validate(response_data)

    except Exception as e:
        logger.warning(f"No se pudo consultar la caché en MongoDB: {e}")
        return None

    return None


async def save_cached_cv_response(request: CVRequest, response: CVResponse) -> None:
    """
    Guarda la respuesta generada del CV en la colección cv_responses_cache de MongoDB.
    """
    if not settings.ENABLE_SEMANTIC_CACHE:
        return

    try:
        db = get_db()
        if db is None:
            return

        req_hash = compute_request_hash(request)
        doc = {
            "request_hash": req_hash,
            "user_id": request.user_id,
            "cv_response": response.model_dump(),
            "timestamp": datetime.now(timezone.utc)
        }

        # Actualizar o insertar (upsert)
        await db.cv_responses_cache.update_one(
            {"request_hash": req_hash},
            {"$set": doc},
            upsert=True
        )
        logger.info(f"[CACHE SAVE] Guardada respuesta de CV en caché para hash {req_hash[:8]}")
    except Exception as e:
        logger.error(f"Error al guardar respuesta en caché en MongoDB: {e}")
