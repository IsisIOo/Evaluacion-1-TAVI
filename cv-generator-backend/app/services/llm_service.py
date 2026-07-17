import asyncio
import json
import logging
import re
from typing import Any, Dict, List, Optional

from langchain_core.messages import HumanMessage, SystemMessage

from app.core.config import settings
from app.core.llm_factory import get_deterministic_llm
from app.core.observability import AsyncObservabilityCallback
from app.schemas.cv_request import CVRequest
from app.schemas.cv_response import CVResponse

import os
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Errores
# ---------------------------------------------------------------------------
class QuotaExceededError(Exception):
    pass


def _is_quota_error(error: str) -> bool:
    keywords = [
        "quota", "resource exhausted", "rate limit", "429",
        "too many requests", "insufficient tokens",
        "daily limit", "monthly limit",
    ]
    return any(kw in error.lower() for kw in keywords)


# ---------------------------------------------------------------------------
# Contexto general
# ---------------------------------------------------------------------------
ATS_SYSTEM_POLICY = (
    "Eres un experto senior en recursos humanos y redacción de CVs profesionales "
    "optimizados para sistemas ATS (Applicant Tracking Systems).\n"
    "Reglas de estilo que SIEMPRE debes respetar:\n"
    "- Tono profesional, en primera persona implícita (sin usar 'yo').\n"
    "- Verbos de acción fuertes (Lideré, Implementé, Reduje, Diseñé, etc.).\n"
    "- Métricas concretas cuando se puedan inferir del contexto.\n"
    "- Vocabulario del sector del candidato.\n"
    "- No inventar empresas, fechas, títulos ni datos concretos que NO ESTEN EN EL CONTEXTO.\n"
    "- Devolver EXCLUSIVAMENTE un JSON válido, sin markdown, sin ```json, sin explicaciones."
)

def _get_relevant_jobs(request: CVRequest) -> str:
    """
    Busca las 3 ofertas laborales más afines al usuario en la base de datos vectorial activa.
    """
    # 1. Armar la "pregunta" usando la experticia y habilidades del usuario
    query = f"Experiencia en: {request.perfil.experticia}. Habilidades: {request.habilidades}"
    
    # 2. Configurar rutas hacia la carpeta data/
    # Subimos 3 niveles desde app/services/llm_service.py -> app/services -> app -> raíz
    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
    data_dir = os.path.join(base_dir, "data")
    pointer_path = os.path.join(data_dir, "active_pointer.json")
    
    # 3. Leer el puntero Blue/Green
    active_store = "blue"
    if os.path.exists(pointer_path):
        try:
            with open(pointer_path, "r") as f:
                data = json.load(f)
                active_store = data.get("active", "blue")
        except Exception as e:
            logger.warning(f"No se pudo leer el puntero, usando blue por defecto: {e}")
            
    vector_dir = os.path.join(data_dir, f"vector_store_{active_store}")
    
    # 4. Conectar al RAG y buscar (Top K = 3)
    try:
        embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
        db = Chroma(persist_directory=vector_dir, embedding_function=embeddings)
        
        resultados = db.similarity_search(query, k=3)
        
        if not resultados:
            return "No se encontraron ofertas laborales de contexto."
            
        # 5. Formatear los resultados para el Prompt Aumentado
        contexto_ofertas = "## OFERTAS LABORALES (Usa EXCLUSIVAMENTE su terminología para optimizar el CV):\n\n"
        for i, doc in enumerate(resultados):
            area = doc.metadata.get("area_trabajo", "General")
            contexto_ofertas += f"### Oferta {i+1} (Área: {area})\n{doc.page_content}\n\n"
            
        return contexto_ofertas
        
    except Exception as e:
        logger.error(f"Error al buscar en el RAG: {e}")
        return "Sin contexto de ofertas laborales."

def _build_general_context(request: CVRequest) -> str:
    personal = request.personal
    perfil = request.perfil

    experiencias = "\n".join(
        f"- {exp.cargo} en {exp.empresa} ({exp.periodo}, {exp.pais}): "
        f"{exp.descripcion}. Logros: {exp.logros}"
        for exp in request.experiencias
    ) or "- (sin experiencias declaradas)"

    formacion = "\n".join(
        f"- {edu.titulo} en {edu.institucion} ({edu.periodo})"
        for edu in request.formacion
    ) or "- (sin formación declarada)"

    return (
        "## CONTEXTO GENERAL DEL CANDIDATO (úsalo para mantener coherencia)\n\n"
        "### Información Personal\n"
        f"- Nombre completo: {personal.nombre_completo}\n"
        f"- Profesión: {personal.profesion}\n"
        f"- Email: {personal.email}\n"
        f"- Teléfono: {personal.telefono}\n"
        f"- LinkedIn: {personal.linkedin}\n"
        f"- RUT: {personal.rut}\n"
        f"- Ciudad: {personal.ciudad}\n\n"
        "### Perfil Profesional\n"
        f"- Años de experiencia: {perfil.anios_experiencia}\n"
        f"- Área de experticia: {perfil.experticia}\n"
        f"- Propuesta de valor (borrador del candidato): {perfil.propuesta_valor}\n\n"
        "### Experiencias Laborales (input)\n"
        f"{experiencias}\n\n"
        "### Formación Académica (input)\n"
        f"{formacion}\n\n"
        "### Habilidades brutas (input)\n"
        f"{request.habilidades}\n"
    )


# ---------------------------------------------------------------------------
# Helpers de parseo robustos
# ---------------------------------------------------------------------------
_JSON_FENCE_RE = re.compile(r"```(?:json)?\s*(.*?)```", re.DOTALL | re.IGNORECASE)


def _extract_json(raw: str) -> Optional[Any]:
    if not raw:
        return None

    candidates: List[str] = []
    candidates.append(raw.strip())

    fence_match = _JSON_FENCE_RE.search(raw)
    if fence_match:
        candidates.append(fence_match.group(1).strip())

    # buscar el primer {...} o [...] balanceado
    for opener, closer in [("{", "}"), ("[", "]")]:
        first = raw.find(opener)
        last = raw.rfind(closer)
        if first != -1 and last != -1 and last > first:
            candidates.append(raw[first:last + 1])

    for cand in candidates:
        cand = cand.strip()
        if not cand:
            continue
        try:
            return json.loads(cand)
        except json.JSONDecodeError:
            continue
    return None


async def _invoke_json_prompt(
    user_prompt: str,
    *,
    user_id: str,
    temperature: float = 0.2,
) -> Any:
    llm = get_deterministic_llm()
    if llm is None:
        raise RuntimeError("El servicio de IA no está disponible: falta configuración de Gemini.")

    # forzamos temperature baja solo para esta llamada
    try:
        llm = llm.bind(temperature=temperature)
    except Exception:
        pass

    callback = AsyncObservabilityCallback(user_id=user_id)

    try:
        response = await asyncio.wait_for(
            llm.ainvoke(
                [
                    SystemMessage(content=ATS_SYSTEM_POLICY),
                    HumanMessage(content=user_prompt),
                ],
                config={"callbacks": [callback]},
            ),
            timeout=settings.LLM_TIMEOUT,
        )
    except asyncio.TimeoutError:
        logger.error("Timeout en llamada parcial al LLM")
        raise TimeoutError("La IA está tardando demasiado. Intenta nuevamente.")
    except Exception as e:
        msg = str(e)
        if _is_quota_error(msg):
            raise QuotaExceededError("La cuota de la API se ha agotado.")
        raise RuntimeError(f"Falla en el servicio de IA: {msg}")

    raw = getattr(response, "content", "") or ""
    
    # FIX: Si Gemini devuelve una lista de bloques, extraemos el texto
    if isinstance(raw, list):
        if len(raw) > 0 and isinstance(raw[0], dict) and "text" in raw[0]:
            raw = raw[0]["text"]
        elif len(raw) > 0 and isinstance(raw[0], str):
            raw = "".join(raw)
        else:
            raw = str(raw)
    elif not isinstance(raw, str):
        raw = str(raw)

    return _extract_json(raw)


# ---------------------------------------------------------------------------
# Prompts por bloque
# ---------------------------------------------------------------------------
def _prompt_personal(request: CVRequest, context: str) -> str:
    p = request.personal
    return (
        f"{context}\n\n"
        "## TAREA\n"
        "Optimiza la sección de información personal del candidato para ATS. "
        "Mantén los datos EXACTOS que entrega el candidato (no inventes, no cambies "
        "teléfono, email, RUT, LinkedIn ni ciudad), lo que puedes cambiar si se amerita es la profesión. Devuelve un JSON con esta forma:\n\n"
        "{\n"
        '  "nombre_completo": string,\n'
        '  "profesion": string,\n'
        '  "email": string,\n'
        '  "telefono": string,\n'
        '  "linkedin": string,\n'
        '  "rut": string,\n'
        '  "ciudad": string\n'
        "}\n\n"
        "Datos crudos del candidato:\n"
        f"- Nombre: {p.nombre_completo}\n"
        f"- Profesión: {p.profesion}\n"
        f"- Email: {p.email}\n"
        f"- Teléfono: {p.telefono}\n"
        f"- LinkedIn: {p.linkedin}\n"
        f"- RUT: {p.rut}\n"
        f"- Ciudad: {p.ciudad}\n"
    )


def _prompt_perfil(request: CVRequest, context: str) -> str:
    pf = request.perfil
    return (
        f"{context}\n\n"
        "## TAREA\n"
        "Reescribe la sección de perfil profesional para ATS. La propuesta de valor "
        "debe tener entre 3 y 5 oraciones impactantes que resuman la carrera del candidato. "
        "Mantén los años de experiencia tal como el candidato los declara. Devuelve JSON:\n\n"
        "{\n"
        '  "anios_experiencia": integer,\n'
        '  "experticia": string,\n'
        '  "propuesta_valor": string\n'
        "}\n\n"
        "Datos crudos:\n"
        f"- Años de experiencia: {pf.anios_experiencia}\n"
        f"- Áreas de experticia: {pf.experticia}\n"
        f"- Propuesta de valor: {pf.propuesta_valor}\n"
    )


def _prompt_experiencia(idx: int, exp, context: str) -> str:
    return (
        f"{context}\n\n"
        "## TAREA\n"
        f"Optimiza la experiencia #{idx + 1} del candidato. Descripción debe tener al menos "
        "2-3 oraciones con verbos de acción. Los logros deben comenzar con un verbo de acción "
        "e idealmente incluir métricas. No inventes empresas ni fechas. Devuelve JSON:\n\n"
        "{\n"
        '  "cargo": string,\n'
        '  "empresa": string,\n'
        '  "pais": string,\n'
        '  "periodo": string,\n'
        '  "descripcion": string,\n'
        '  "logros": string\n'
        "}\n\n"
        "Datos crudos:\n"
        f"- Cargo: {exp.cargo}\n"
        f"- Empresa: {exp.empresa}\n"
        f"- País: {exp.pais}\n"
        f"- Periodo: {exp.periodo}\n"
        f"- Descripción: {exp.descripcion}\n"
        f"- Logros: {exp.logros}\n"
    )


def _prompt_formacion(idx: int, edu, context: str) -> str:
    return (
        f"{context}\n\n"
        "## TAREA\n"
        f"Optimiza la formación #{idx + 1}. Mantén título, institución y periodo exactos. "
        "Si el título es muy informal, normalízalo a la nomenclatura estándar. Devuelve JSON:\n\n"
        "{\n"
        '  "titulo": string,\n'
        '  "institucion": string,\n'
        '  "periodo": string\n'
        "}\n\n"
        "Datos crudos:\n"
        f"- Título: {edu.titulo}\n"
        f"- Institución: {edu.institucion}\n"
        f"- Periodo: {edu.periodo}\n"
    )


def _prompt_habilidades(request: CVRequest, context: str) -> str:
    return (
        f"{context}\n\n"
        "## TAREA\n"
        "Consolida las habilidades del candidato en un único string optimizado para ATS, "
        "organizado por categorías (técnicas, blandas, herramientas, idiomas). "
        "Usa el formato 'Categoría: habilidad1, habilidad2, ...' separado por saltos de línea. "
        "No inventes habilidades que no estén en el input. Devuelve un JSON con la forma:\n\n"
        "{ \"habilidades\": string }\n\n"
        f"Habilidades crudas del candidato:\n{request.habilidades}\n"
    )


# ---------------------------------------------------------------------------
# Validación + ensamblaje
# ---------------------------------------------------------------------------
def _safe_str(value: Any, default: str = "") -> str:
    if value is None:
        return default
    return str(value).strip() or default


def _safe_int(value: Any, default: int = 0) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _assemble_cv(
    request: CVRequest,
    personal_data: Optional[dict],
    perfil_data: Optional[dict],
    experiencias_data: List[Optional[dict]],
    formacion_data: List[Optional[dict]],
    habilidades_data: Optional[dict],
) -> CVResponse:
    p_src = request.personal
    personal = personal_data or {}
    personal_final = {
        "nombre_completo": _safe_str(personal.get("nombre_completo"), p_src.nombre_completo),
        "profesion":       _safe_str(personal.get("profesion"), p_src.profesion),
        "email":           _safe_str(personal.get("email"), p_src.email),
        "telefono":        _safe_str(personal.get("telefono"), p_src.telefono),
        "linkedin":        _safe_str(personal.get("linkedin"), p_src.linkedin),
        "rut":             _safe_str(personal.get("rut"), p_src.rut),
        "ciudad":          _safe_str(personal.get("ciudad"), p_src.ciudad),
    }

    pf_src = request.perfil
    perfil = perfil_data or {}
    perfil_final = {
        "anios_experiencia": _safe_int(perfil.get("anios_experiencia"), pf_src.anios_experiencia),
        "experticia":        _safe_str(perfil.get("experticia"), pf_src.experticia),
        "propuesta_valor":   _safe_str(perfil.get("propuesta_valor"), pf_src.propuesta_valor),
    }

    experiencias_final = []
    for idx, exp_src in enumerate(request.experiencias):
        data = experiencias_data[idx] if idx < len(experiencias_data) else None
        data = data or {}
        experiencias_final.append({
            "cargo":       _safe_str(data.get("cargo"), exp_src.cargo),
            "empresa":     _safe_str(data.get("empresa"), exp_src.empresa),
            "pais":        _safe_str(data.get("pais"), exp_src.pais),
            "periodo":     _safe_str(data.get("periodo"), exp_src.periodo),
            "descripcion": _safe_str(data.get("descripcion"), exp_src.descripcion),
            "logros":      _safe_str(data.get("logros"), exp_src.logros),
        })

    formacion_final = []
    for idx, edu_src in enumerate(request.formacion):
        data = formacion_data[idx] if idx < len(formacion_data) else None
        data = data or {}
        formacion_final.append({
            "titulo":      _safe_str(data.get("titulo"), edu_src.titulo),
            "institucion": _safe_str(data.get("institucion"), edu_src.institucion),
            "periodo":     _safe_str(data.get("periodo"), edu_src.periodo),
        })

    habilidades = _safe_str(
        (habilidades_data or {}).get("habilidades"),
        request.habilidades,
    )

    return CVResponse(
        personal=personal_final,             
        perfil=perfil_final,                  
        experiencias=experiencias_final,      
        formacion=formacion_final,            
        habilidades=habilidades,
    )


# ---------------------------------------------------------------------------
# Orquestador
# ---------------------------------------------------------------------------
async def generate_cv(request: CVRequest) -> CVResponse:
    logger.info(
        f"Generando CV multi-prompt para user_id={request.user_id} "
        f"con modelo={settings.MODEL_NAME}"
    )

    context = _build_general_context(request)

    async def safe_personal():
        try:
            return await _invoke_json_prompt(
                _prompt_personal(request, context),
                user_id=request.user_id,
            )
        except (QuotaExceededError, TimeoutError):
            raise
        except Exception as e:
            logger.warning(f"Fallback en personal: {e}")
            return None

    async def safe_perfil():
        try:
            return await _invoke_json_prompt(
                _prompt_perfil(request, context),
                user_id=request.user_id,
            )
        except (QuotaExceededError, TimeoutError):
            raise
        except Exception as e:
            logger.warning(f"Fallback en perfil: {e}")
            return None

    async def safe_exp(idx, exp):
        try:
            return await _invoke_json_prompt(
                _prompt_experiencia(idx, exp, context),
                user_id=request.user_id,
            )
        except (QuotaExceededError, TimeoutError):
            raise
        except Exception as e:
            logger.warning(f"Fallback en experiencia #{idx + 1}: {e}")
            return None

    async def safe_edu(idx, edu):
        try:
            return await _invoke_json_prompt(
                _prompt_formacion(idx, edu, context),
                user_id=request.user_id,
            )
        except (QuotaExceededError, TimeoutError):
            raise
        except Exception as e:
            logger.warning(f"Fallback en formación #{idx + 1}: {e}")
            return None

    async def safe_habilidades():
        try:
            return await _invoke_json_prompt(
                _prompt_habilidades(request, context),
                user_id=request.user_id,
            )
        except (QuotaExceededError, TimeoutError):
            raise
        except Exception as e:
            logger.warning(f"Fallback en habilidades: {e}")
            return None

    try:
        (
            personal_data,
            perfil_data,
            experiencias_data,
            formacion_data,
            habilidades_data,
        ) = await asyncio.gather(
            safe_personal(),
            safe_perfil(),
            asyncio.gather(*(safe_exp(i, e) for i, e in enumerate(request.experiencias))),
            asyncio.gather(*(safe_edu(i, e) for i, e in enumerate(request.formacion))),
            safe_habilidades(),
        )
    except asyncio.TimeoutError:
        logger.error("Timeout en la generación multi-prompt")
        raise TimeoutError("La IA está tardando demasiado en responder. Intenta nuevamente.")
    except QuotaExceededError:
        raise
    except Exception as e:
        error_msg = str(e)
        logger.error(f"Error en el servicio de IA: {error_msg}")
        if _is_quota_error(error_msg):
            raise QuotaExceededError("La cuota de la API se ha agotado. Intenta nuevamente más tarde.")
        raise RuntimeError(f"Falla en el servicio de IA: {error_msg}")

    return _assemble_cv(
        request=request,
        personal_data=personal_data,
        perfil_data=perfil_data,
        experiencias_data=list(experiencias_data),
        formacion_data=list(formacion_data),
        habilidades_data=habilidades_data,
    )
