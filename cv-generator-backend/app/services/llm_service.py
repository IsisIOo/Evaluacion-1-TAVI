import asyncio
import logging
import json
import os
from typing import List
from pydantic import BaseModel, Field

from langchain_core.messages import SystemMessage, HumanMessage

# Importar dependencias de RAG de forma opcional para no romper el arranque
try:
    from langchain_huggingface import HuggingFaceEmbeddings
    from langchain_community.vectorstores import Chroma
    RAG_AVAILABLE = True
except Exception:
    HuggingFaceEmbeddings = None
    Chroma = None
    RAG_AVAILABLE = False

from app.core.config import settings
from app.schemas.cv_request import CVRequest
from app.schemas.cv_response import CVResponse, Personal, Perfil, Experiencia, Formacion
from app.core.llm_factory import get_deterministic_llm
from app.core.observability import AsyncObservabilityCallback
from app.services.cache_service import get_cached_cv_response, save_cached_cv_response

logger = logging.getLogger(__name__)

if not RAG_AVAILABLE:
    logger.warning("RAG dependencies not available: langchain_huggingface/langchain_community. RAG deshabilitado.")

# Rutas para ChromaDB
BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DATA_DIR = os.path.join(BACKEND_DIR, "data")
POINTER_PATH = os.path.join(DATA_DIR, "active_pointer.json")

class QuotaExceededError(Exception):
    pass

def _is_quota_error(error: str) -> bool:
    keywords = ["quota", "resource exhausted", "resource has been exhausted", "rate limit", "429", "too many requests",
                "insufficient tokens", "daily limit", "monthly limit"]
    return any(kw in error.lower() for kw in keywords)

# Esquema optimizado para la salida del LLM (respuestas extremadamente ricas, profesionales y realistas de nivel Senior)
class ExperienciaOptimizada(BaseModel):
    index: int = Field(..., description="Índice de la experiencia (0-indexed)")
    descripcion: str = Field(..., description="Descripción altamente desarrollada, exhaustiva y realista de responsabilidades y funciones (entre 120 y 200 palabras)")
    logros: str = Field(..., description="Logros detallados con contexto de negocio, herramientas aplicadas e impacto cuantitativo medible (entre 70 y 120 palabras)")

class OptimizedCVContent(BaseModel):
    propuesta_valor: str = Field(..., description="Resumen ejecutivo profesional amplio, persuasivo y elegante (5 a 7 oraciones de alta densidad ATS)")
    experiencias: List[ExperienciaOptimizada] = Field(..., description="Lista de experiencias laborales optimizadas y desarrolladas con máximo nivel de detalle")
    habilidades: str = Field(..., description="Matriz exhaustiva y categorizada de habilidades (Técnicas & Lenguajes, Herramientas & Cloud, Metodologías, Blandas)")

# Prompt del sistema estático (permite Context Caching automático en Gemini / LLMs)
SYSTEM_PROMPT = (
    "Eres un mentor ejecutivo de carrera de élite y redactor principal de CVs de alto impacto para sistemas ATS (Applicant Tracking Systems).\n"
    "Tu misión absoluta es actuar como el 'asistente definitivo' para cualquier candidato: transformar incluso el borrador más simple, breve o informal en un CV profesional extraordinariamente completo, realista, extenso y convincente.\n\n"
    "REGLAS MAESTRAS DE ASISTENCIA Y REDACCIÓN MÁXIMA:\n"
    "1. ASISTENCIA PROACTIVA E INFERENCIA CONTEXTUAL: Si el candidato ingresó textos muy breves, sencillos o informales (ej. 'hacía ventas', 'programaba', 'atendía clientes'), DEBES inferir el contexto profesional estándar de su industria y EXPANDIR el contenido con responsabilidades reales de alto nivel, arquitecturas, metodologías, herramientas habituales y mejores prácticas del sector.\n"
    "2. PROPUESTA DE VALOR EJECUTIVA EXTENSA: Construye un resumen profesional persuasivo y elegante de 5 a 7 oraciones completas. Debe resaltar la trayectoria, años de experiencia, áreas de maestría técnica, enfoque de resolución de problemas y valor estratégico hacia la organización objetivo.\n"
    "3. DESCRIPCIONES LABORALES EXHAUSTIVAS Y DETALLADAS: Redacta bloques descriptivos profundos de 120 a 200 palabras por experiencia laboral. Explica con claridad el objetivo del puesto, alcance de los proyectos, tareas operativas diarias, colaboración multifuncional, tecnologías/herramientas empleadas y metodologías de trabajo (Scrum, Kanban, Agile, ITIL, etc.).\n"
    "4. LOGROS IMPACTANTES CON MÉTRICAS DE NEGOCIO: Para cada experiencia, redacta logros detallados de 70 a 120 palabras estructurados en torno a la problemática abordada, la solución implementada y el resultado cuantificable. Si el usuario no especificó números, infiere métricas realistas y coherentes (porcentajes de optimización, reducción de costos o tiempos, incremento en ventas o satisfacción de usuarios).\n"
    "5. MATRIZ DE HABILIDADES COMPLETA Y CATEGORIZADA: Expande cualquier lista de palabras clave en una matriz profesional dividida en 4 categorías: 'Competencias Técnicas & Lenguajes: ... | Herramientas & Plataformas Cloud: ... | Metodologías & Frameworks: ... | Habilidades Profesionales & Liderazgo: ...'.\n"
    "6. FIDELIDAD HISTÓRICA: Mantiene 100% exactos los datos fijos del candidato (nombres de empresas, cargos, fechas e instituciones). Solo formaliza, expande y enriquece la redacción descriptiva.\n"
    "7. Devuelve ÚNICAMENTE la estructura JSON requerida sin texto ni explicaciones adicionales."
)

def _get_matching_job_offers(query: str, k: int = 3) -> str:
    """
    Busca ofertas de trabajo reales en la base de datos vectorial (ChromaDB)
    para usarlas como referencia/contexto de optimización.
    """
    # Si las dependencias de RAG no están presentes, no intentamos usar la búsqueda vectorial
    if not RAG_AVAILABLE:
        logger.warning("RAG no disponible; omitiendo búsqueda vectorial de ofertas.")
        return ""

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
    Construye los mensajes para el LLM y devuelve la respuesta estructurada del CV completada en Python.
    Consulta primero la caché en MongoDB para evitar llamadas repetidas al LLM (0 tokens).
    """
    # 0. Verificar si la respuesta ya existe en caché (Ahorro del 100% de tokens en solicitudes repetidas)
    cached_response = await get_cached_cv_response(request)
    if cached_response:
        return cached_response

    llm = get_deterministic_llm()
    # Usar el esquema reducido OptimizedCVContent para minimizar Output Tokens
    modelo_con_formato = llm.with_structured_output(OptimizedCVContent)
    observability_callback = AsyncObservabilityCallback(user_id=request.user_id)

    # 1. Buscar ofertas de trabajo coincidentes en la base de datos vectorial
    query = f"{request.personal.profesion} {request.perfil.experticia} {request.habilidades}"
    target_jobs_context = _get_matching_job_offers(query, k=3)

    # 2. Construir los mensajes (SystemMessage para caché + HumanMessage para datos del candidato)
    messages = _build_cv_messages(request, target_jobs_context)
    logger.info(f"Generando CV para user_id={request.user_id} con modelo={settings.MODEL_NAME}")

    try:
        respuesta_optimzada: OptimizedCVContent = await asyncio.wait_for(
            modelo_con_formato.ainvoke(
                messages,
                config={"callbacks": [observability_callback]}
            ),
            timeout=settings.LLM_TIMEOUT
        )

        if not isinstance(respuesta_optimzada, OptimizedCVContent):
            respuesta_optimzada = OptimizedCVContent.model_validate(respuesta_optimzada)

        # 3. Ensamblar en Python la respuesta final manteniendo datos fijos e inmutables
        final_response = _assemble_cv_response(request, respuesta_optimzada)

        # 4. Guardar en caché para futuras solicitudes idénticas
        await save_cached_cv_response(request, final_response)

        return final_response

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


def _build_cv_messages(request: CVRequest, target_jobs_context: str = ""):
    """
    Construye la lista de mensajes para enviar al LLM: mensaje de sistema y mensaje humano.
    """
    system_msg = SystemMessage(content=SYSTEM_PROMPT)
    human_content = _build_cv_prompt(request, target_jobs_context)
    human_msg = HumanMessage(content=human_content)
    return [system_msg, human_msg]


def _assemble_cv_response(request: CVRequest, optimized: OptimizedCVContent) -> CVResponse:
    """
    Ensambla la respuesta final `CVResponse` usando los datos originales del request
    y el contenido optimizado devuelto por el LLM.
    """
    # Personal
    personal_data = request.personal.model_dump() if hasattr(request.personal, 'model_dump') else request.personal.dict()
    personal = Personal(**personal_data)

    # Perfil (sustituir propuesta de valor por la optimizada)
    perfil_data = request.perfil.model_dump() if hasattr(request.perfil, 'model_dump') else request.perfil.dict()
    perfil = Perfil(**perfil_data)
    perfil.propuesta_valor = optimized.propuesta_valor

    # Experiencias: mapear cada experiencia por índice y sustituir descripcion/logros si existen
    experiencias_out = []
    optimized_map = {e.index: e for e in optimized.experiencias}
    for idx, exp in enumerate(request.experiencias):
        if hasattr(exp, 'model_dump'):
            base = exp.model_dump()
        else:
            base = exp.dict()

        descripcion = base.get('descripcion', '')
        logros = base.get('logros', '')
        if idx in optimized_map:
            descripcion = optimized_map[idx].descripcion
            logros = optimized_map[idx].logros

        experiencia = Experiencia(
            cargo=base.get('cargo', ''),
            empresa=base.get('empresa', ''),
            pais=base.get('pais', ''),
            periodo=base.get('periodo', ''),
            descripcion=descripcion,
            logros=logros,
        )
        experiencias_out.append(experiencia)

    # Formacion: copiar tal cual
    formacion_out = []
    for f in request.formacion:
        if hasattr(f, 'model_dump'):
            fd = f.model_dump()
        else:
            fd = f.dict()
        formacion_out.append(Formacion(**fd))

    habilidades_text = optimized.habilidades if getattr(optimized, 'habilidades', None) else request.habilidades

    return CVResponse(
        personal=personal,
        perfil=perfil,
        experiencias=experiencias_out,
        formacion=formacion_out,
        habilidades=habilidades_text,
    )