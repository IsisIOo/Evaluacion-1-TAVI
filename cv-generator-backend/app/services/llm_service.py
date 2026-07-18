import asyncio
import logging
import json
import os
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma
from app.core.config import settings
from app.schemas.cv_request import CVRequest
from app.schemas.cv_response import CVResponse
from app.core.llm_factory import get_deterministic_llm, get_local_llm
from app.core.observability import AsyncObservabilityCallback

logger = logging.getLogger(__name__)

# Rutas para ChromaDB
BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DATA_DIR = os.path.join(BACKEND_DIR, "data")
POINTER_PATH = os.path.join(DATA_DIR, "active_pointer.json")

class QuotaExceededError(Exception):
    pass

def _is_quota_error(error: str) -> bool:
    keywords = ["quota", "resource exhausted", "rate limit", "429", "too many requests",
                "insufficient tokens", "daily limit", "monthly limit"]
    return any(kw in error.lower() for kw in keywords)

def _get_matching_job_offers(query: str, k: int = 3) -> str:
    """
    Busca ofertas de trabajo reales en la base de datos vectorial (ChromaDB)
    para usarlas como referencia/contexto de optimización.
    """
    try:
        if not os.path.exists(POINTER_PATH):
            logger.warning("No se encontró el puntero de base de datos activa en active_pointer.json")
            return ""

        with open(POINTER_PATH, "r") as f:
            active_store = json.load(f).get("active", "blue")

        vector_dir = os.path.join(DATA_DIR, f"vector_store_{active_store}")
        if not os.path.exists(vector_dir):
            logger.warning(f"No existe el directorio de la base de datos vectorial: {vector_dir}")
            return ""

        logger.info(f"RAG: Cargando base de datos activa: [{active_store.upper()}] para búsqueda")
        embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
        db = Chroma(persist_directory=vector_dir, embedding_function=embeddings)

        # Buscar las mejores k coincidencias
        results = db.similarity_search(query, k=k)
        if not results:
            logger.warning("RAG: No se encontraron ofertas coincidentes")
            return ""

        context_parts = []
        for idx, doc in enumerate(results):
            area = doc.metadata.get("area_trabajo", "General")
            context_parts.append(f"Oferta #{idx+1} (Área: {area}):\n{doc.page_content}\n")

        logger.info(f"RAG: Se encontraron {len(context_parts)} ofertas de referencia")
        return "\n".join(context_parts)
    except Exception as e:
        logger.error(f"Error al realizar la búsqueda vectorial RAG: {e}", exc_info=True)
        return ""

async def generate_cv(request: CVRequest) -> CVResponse:
    """
    Construye el prompt para el LLM y devuelve la respuesta estructurada del CV.
    Utiliza LangChain para invocar el modelo con .ainvoke y registrar el callback.
    """
    llm = get_deterministic_llm()
    modelo_con_formato = llm.with_structured_output(CVResponse)
    observability_callback = AsyncObservabilityCallback(user_id=request.user_id)

    # 1. Buscar ofertas de trabajo coincidentes en la base de datos vectorial
    query = f"{request.personal.profesion} {request.perfil.experticia} {request.habilidades}"
    target_jobs_context = _get_matching_job_offers(query, k=3)

    # 2. Construir el prompt con el contexto
    prompt = _build_cv_prompt(request, target_jobs_context)
    logger.info(f"Generando CV para user_id={request.user_id} con modelo={settings.MODEL_NAME}")

    try:
        respuesta = await asyncio.wait_for(
            modelo_con_formato.ainvoke(
                prompt,
                config={"callbacks": [observability_callback]}
            ),
            timeout=settings.LLM_TIMEOUT
        )

        if isinstance(respuesta, CVResponse):
            return respuesta

        return CVResponse.model_validate(respuesta)

    except asyncio.TimeoutError:
        logger.error("Timeout en la llamada al LLM")
        raise TimeoutError("La IA está tardando demasiado en responder. Intenta nuevamente.")
    except QuotaExceededError:
        raise
    except Exception as e:
        error_msg = str(e)
        logger.error(f"Error en el servicio de IA: {error_msg}")
        if _is_quota_error(error_msg):
            raise QuotaExceededError("La cuota de la API se ha agotado. Intenta nuevamente más tarde.")
        raise RuntimeError(f"Falla en el servicio de IA: {error_msg}")


def _build_cv_prompt(request: CVRequest, target_jobs_context: str = "") -> str:
    """
    Construye el prompt para el LLM basándose en los datos del request y el contexto RAG.
    """
    personal = request.personal
    perfil = request.perfil

    experiencias = []
    for exp in request.experiencias:
        experiencias.append(
            f"- {exp.cargo} en {exp.empresa} ({exp.periodo}, {exp.pais}): {exp.descripcion}. Logros: {exp.logros}"
        )

    formacion = []
    for edu in request.formacion:
        formacion.append(f"- {edu.titulo} en {edu.institucion} ({edu.periodo})")

    # Si hay contexto de ofertas de trabajo, lo agregamos al prompt
    context_section = ""
    if target_jobs_context:
        context_section = (
            "## OFERTAS DE TRABAJO REALES DE REFERENCIA (TARGET)\n"
            f"El candidato postula al cargo/profesión de '{personal.profesion}'. A continuación se muestran ofertas de trabajo reales relacionadas. "
            "Usa estas ofertas para extraer palabras clave, habilidades y responsabilidades clave para optimizar y adaptar el CV:\n\n"
            f"{target_jobs_context}\n"
        )

    prompt = (
        "Eres un experto en recursos humanos y redacción de CVs profesionales optimizados para sistemas ATS (Applicant Tracking Systems).\n"
        "Tu tarea es generar un CV completo, sumamente profesional, optimizado y bien estructurado en español, a partir de los datos del candidato.\n\n"

        "## INSTRUCCIONES GENERALES\n"
        f"- Optimiza y adapta el contenido para que coincida y destaque frente al puesto al que postula el candidato ('{personal.profesion}').\n"
        "- Puedes reformular, enriquecer y mejorar significativamente la redacción de la propuesta de valor, descripción de responsabilidades y habilidades.\n"
        "- IMPORTANTE: No inventes ni modifiques datos concretos e históricos: nombres de empresas, fechas exactas, títulos académicos o instituciones educativas deben mantenerse 100% fieles a lo ingresado por el candidato. Solo mejora el texto descriptivo.\n"
        "- Los logros deben ser redactados con verbos de acción fuertes en primera persona implícita y, si es posible, estimar o inferir métricas o impacto cuantitativo de acuerdo al contexto del rol.\n"
        "- La propuesta de valor debe resumir la carrera del candidato en 3 a 5 oraciones con alta densidad de palabras clave relevantes.\n"
        "- Responde ÚNICAMENTE con el JSON estructurado según el esquema CVResponse. Sin explicaciones, sin markdown, sin texto adicional.\n\n"

        + context_section +

        "## DATOS DEL CANDIDATO (INPUT)\n\n"

        "### Información Personal\n"
        f"- Nombre completo: {personal.nombre_completo}\n"
        f"- Profesión / Cargo Objetivo: {personal.profesion}\n"
        f"- Email: {personal.email}\n"
        f"- Teléfono: {personal.telefono}\n"
        f"- LinkedIn: {personal.linkedin}\n"
        f"- RUT: {personal.rut}\n"
        f"- Ciudad: {personal.ciudad}\n\n"

        "### Perfil Profesional\n"
        f"- Años de experiencia: {perfil.anios_experiencia}\n"
        f"- Área de experticia: {perfil.experticia}\n"
        f"- Propuesta de valor (borrador del candidato): {perfil.propuesta_valor}\n\n"

        "### Experiencias Laborales\n"
        + "\n".join(experiencias)
        + "\n\n"

        "### Formación Académica\n"
        + "\n".join(formacion)
        + "\n\n"

        "### Habilidades (input del candidato)\n"
        + request.habilidades
        + "\n\n"

        "## CRITERIOS ATS A APLICAR\n"
        "1. Incorpora palabras clave relevantes para el cargo objetivo de forma natural.\n"
        "2. Redacta las descripciones de tareas usando verbos de acción (por ejemplo: Lideré, Coordiné, Optimicé, Diseñé, etc.).\n"
        "3. La sección de habilidades debe ser categorizada y estructurada para fácil lectura por los ATS.\n"
        "4. Asegura coherencia y elimina modismos informales o lenguaje coloquial, manteniéndolo profesional.\n\n"

        "Genera ahora el JSON completo siguiendo el esquema CVResponse."
    )
    return prompt