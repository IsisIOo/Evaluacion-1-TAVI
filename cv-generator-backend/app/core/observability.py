# configuración de observabilidad y guardado de logs en MongoDB
from datetime import datetime, timezone
import logging
import uuid
from langchain_core.callbacks import AsyncCallbackHandler
from typing import Any, Dict, List, Optional
from langchain_core.outputs import LLMResult
from app.core.config import settings
from app.db.session import get_db

# [Para Isidora]: esta clase se encargará de interceptar las llamadas al LLM, recoger información y guardarla
# el script tiene una forma tentativa de calcular costos, duración y tokens usados
# puedes editarlo como quieras mientras decides que recoger, cómo recogerlo, y como guardarlo

logger = logging.getLogger(__name__)

# [Para Isidora]: diccionario de costos, hay que investigar, los numeros que puse me los invente
MODEL_COST_PER_1M = {
    "gemini-1.5-pro": {"input": 0.0004, "output": 0.0008},
}

class AsyncObservabilityCallback(AsyncCallbackHandler):
    """
    Callback asincrono para interceptar y registrar el uso de tokens, tiempo de ejecución y costos
    """
    def __init__(self, user_id: str = "anonymous",  request_id: Optional[str] = None):
        self.user_id = user_id
        self.request_id = request_id or str(uuid.uuid4())  # Genera un ID único para esta solicitud
        self.start_time = None
    
    async def on_llm_start(self, serialized: Dict[str, Any], prompts: List[str], **kwargs: Any) -> None:
        """
        Se ejecuta antes de enviar el prompt al LLM.

        serialized: información serializada del LLM (modelo, configuración, etc.)
        prompts: lista de prompts que se enviarán al LLM
        kwargs: otros argumentos adicionales, se debe incluir porque la función de callback de langchain puede enviar información extra
        """
        self.start_time = datetime.now(timezone.utc)
        logger.info(f"[{self.request_id}] Iniciando llamada al LLM para el usuario {self.user_id}")
    
    async def on_llm_end(self, response: LLMResult, **kwargs: Any) -> None:
        """
        Se ejecuta después de recibir la respuesta del LLM.

        response: resultado devuelto por el LLM, contiene información sobre tokens usados, tiempo de ejecución, etc.
        kwargs: otros argumentos adicionales
        """
        end_time = datetime.now(timezone.utc)
        duration = (end_time - self.start_time).total_seconds() if self.start_time else None

        # extraer el output general
        llm_output = response.llm_output or {}
        
        # intentar obtener el diccionario de uso (puede venir en varios formatos)
        token_usage = llm_output.get("token_usage", {})
        
        # --- Lógica de extracción multimodelo ---
        # Intentamos las llaves estándar (OpenAI/Llama) y las de Google (Gemini)
        input_tokens = (
            token_usage.get("prompt_tokens") or 
            token_usage.get("prompt_token_count") or 
            0
        )
        output_tokens = (
            token_usage.get("completion_tokens") or 
            token_usage.get("candidates_token_count") or 
            token_usage.get("output_tokens") or 
            0
        )
        
        # Si sigue siendo 0, a veces Gemini guarda la info en la primera "generación"
        if input_tokens == 0 and response.generations:
            generation_info = response.generations[0][0].generation_info or {}
            usage = generation_info.get("usage_metadata", {}) # Formato nuevo de LangChain
            input_tokens = usage.get("prompt_token_count", 0)
            output_tokens = usage.get("candidates_token_count", 0)

        total_tokens = token_usage.get("total_tokens", input_tokens + output_tokens)
        # ------------------------------------------

        # Calcular costos aproximados
        cost = self._calculate_cost(settings.MODEL_NAME, input_tokens, output_tokens)

        # Documento de log para MongoDB
        log_entry = {
            "request_id": self.request_id,      # ID único para esta solicitud
            "user_id": self.user_id,            # ID del usuario que hizo la solicitud
            "model_name": settings.MODEL_NAME,  # modelo usado en esta llamada
            "input_tokens": input_tokens,       # tokens usados en el prompt
            "output_tokens": output_tokens,     # tokens usados en la respuesta
            "total_tokens": total_tokens,       # tokens totales usados
            "duration_seconds": duration,       # duración de la llamada
            "cost_usd": cost,                   # costo aproximado de esta llamada
            "timestamp": end_time,              # fecha y hora de la llamada
            "status": "success"                 # estado de la llamada
        }

        await self._save_log(log_entry)

    async def on_llm_error(self, error: BaseException, **kwargs: Any) -> None:
        """
        Se ejecuta si ocurre un error durante la llamada al LLM.

        error: excepción que se lanzó
        kwargs: otros argumentos adicionales
        """
        end_time = datetime.now(timezone.utc)
        duration = (end_time - self.start_time).total_seconds() if self.start_time else None

        log_entry = {
            "request_id": self.request_id,
            "user_id": self.user_id,
            "model_name": settings.MODEL_NAME,
            "duration_seconds": duration,
            "error_message": str(error),
            "timestamp": end_time,
            "status": "error"
        }

        # Guardar en MongoDB
        await self._save_log(log_entry)

    def _calculate_cost(self, model_name: str, input_tokens: int, output_tokens: int) -> float:
        """
        Calcula el costo en base a las tarifas por modelo
        """
        rates = MODEL_COST_PER_1M.get(model_name, {"input": 0.0, "output": 0.0})
        input_cost = (input_tokens / 1_000_000) * rates["input"]
        output_cost = (output_tokens / 1_000_000) * rates["output"]
        return input_cost + output_cost
    
    async def _save_log(self, log_entry: Dict[str, Any]) -> None:
        """
        Guarda el log en MongoDB
        """
        try:
            db = get_db()
        except Exception as e:
            logger.warning(f"[{self.request_id}] No se pudo obtener la conexión a MongoDB: {e}. Log no guardado: {log_entry}")
            return

        if db is not None:
            try:
                await db.observability_logs.insert_one(log_entry)
                logger.info(f"[{self.request_id}] Log guardado en MongoDB. Costo: ${log_entry.get('cost_usd', 0):.6f}")
            except Exception as e:
                logger.error(f"[{self.request_id}] Error al guardar log en MongoDB: {e}")
        else:
            logger.warning(f"[{self.request_id}] No se pudo obtener la conexión a MongoDB. log no guardado: {log_entry}")