import asyncio
import logging
from app.core.config import settings
from app.schemas.cv_request import CVRequest
from app.schemas.cv_response import CVResponse
from app.core.llm_factory import get_deterministic_llm, get_local_llm
from app.core.observability import AsyncObservabilityCallback

logger = logging.getLogger(__name__)

class QuotaExceededError(Exception):
    pass

def _is_quota_error(error: str) -> bool:
    keywords = ["quota", "resource exhausted", "rate limit", "429", "too many requests",
                "insufficient tokens", "daily limit", "monthly limit"]
    return any(kw in error.lower() for kw in keywords)

async def generate_cv(request: CVRequest) -> CVResponse:
    """
    Construye el prompt para el LLM y devuelve la respuesta estructurada del CV.
    Utiliza LangChain para invocar el modelo con .ainvoke y registrar el callback.
    """
    llm = get_deterministic_llm()
    modelo_con_formato = llm.with_structured_output(CVResponse)
    observability_callback = AsyncObservabilityCallback(user_id=request.user_id)

    prompt = _build_cv_prompt(request)
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


def _build_cv_prompt(request: CVRequest) -> str:
    """
    Construye el prompt para el LLM basándose en los datos del request.
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

    prompt = (
        "Eres un experto en recursos humanos y redacción de CVs profesionales optimizados para sistemas ATS (Applicant Tracking Systems). "
        "Tu tarea es generar un CV completo, profesional y bien estructurado a partir de los datos del candidato.\n\n"

        "## INSTRUCCIONES GENERALES\n"
        "- Optimiza el contenido para ATS: usa palabras clave relevantes del sector, verbos de acción fuertes y métricas cuando sea posible.\n"
        "- Puedes reformular, enriquecer y mejorar el texto del candidato, pero sin inventar datos concretos (empresas, fechas, títulos).\n"
        "- Cada sección debe ser completa, clara y orientada a resultados.\n"
        "- El tono debe ser profesional, en primera persona implícita (sin usar 'yo').\n"
        "- Usa verbos de acción en pasado para experiencias anteriores y presente para el rol actual.\n"
        "- La propuesta de valor debe tener entre 3 y 5 oraciones impactantes que resuman la carrera del candidato.\n"
        "- Los logros deben incluir métricas o impacto concreto cuando se pueda inferir del contexto.\n"
        "- Las habilidades deben estar organizadas por categorías (técnicas, blandas, herramientas, idiomas, etc.).\n"
        "- Responde ÚNICAMENTE con el JSON estructurado según el esquema CVResponse. Sin texto adicional, sin markdown, sin explicaciones.\n\n"

        "## DATOS DEL CANDIDATO\n\n"

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
        "1. Incorpora palabras clave del sector profesional del candidato de forma natural.\n"
        "2. Evita tablas, columnas, imágenes o caracteres especiales que los ATS no puedan leer.\n"
        "3. Los cargos deben usar nomenclatura estándar reconocida en el mercado laboral.\n"
        "4. La descripción de cada experiencia debe tener al menos 2-3 oraciones con verbos de acción.\n"
        "5. Los logros deben comenzar con un verbo de acción (Lideré, Implementé, Reduje, Aumenté, etc.).\n"
        "6. La sección de habilidades debe ser rica en términos técnicos y blandas relevantes para el rol.\n\n"

        "Genera ahora el JSON completo siguiendo el esquema CVResponse."
    )
    return prompt
