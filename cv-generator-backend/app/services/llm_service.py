import logging
from app.core.config import settings
from app.schemas.cv_request import CVRequest
from app.schemas.cv_response import CVResponse
from app.core.llm_factory import get_deterministic_llm, get_local_llm
from app.core.observability import AsyncObservabilityCallback

logger = logging.getLogger(__name__)

async def generate_cv(request: CVRequest) -> CVResponse:
    """
    Construye el prompt para el LLM y devuelve la respuesta estructurada del CV.
    Utiliza LangChain para invocar el modelo con .ainvoke y registrar el callback.
    """
    llm_estricto = get_deterministic_llm()
    modelo_con_formato = llm_estricto.with_structured_output(CVResponse)
    observability_callback = AsyncObservabilityCallback(user_id=request.user_id)

    prompt = _build_cv_prompt(request)
    logger.info(f"Generando CV para user_id={request.user_id} con modelo={settings.MODEL_NAME}")

    try:
        respuesta = await modelo_con_formato.ainvoke(
            prompt,
            config={"callbacks": [observability_callback]}
        )

        if isinstance(respuesta, CVResponse):
            return respuesta

        return CVResponse.model_validate(respuesta)

    except Exception as e:
        logger.error(f"Error en el servicio de IA: {str(e)}")
        raise RuntimeError(f"Falla en el servicio de IA: {str(e)}")


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
        "Genera un CV completo usando los datos del candidato. Completa cada campo del esquema CVResponse "
        "usando los nombres de los campos y sus descripciones. No agregues texto extra fuera de la estructura necesaria.\n\n"
        f"Nombre completo: {personal.nombre_completo}\n"
        f"Profesión: {personal.profesion}\n"
        f"Email: {personal.email}\n"
        f"Teléfono: {personal.telefono}\n"
        f"LinkedIn: {personal.linkedin}\n"
        f"RUT: {personal.rut}\n"
        f"Ciudad: {personal.ciudad}\n\n"
        "Perfil profesional:\n"
        f"Años de experiencia: {perfil.anios_experiencia}\n"
        f"Experticia: {perfil.experticia}\n"
        f"Propuesta de valor: {perfil.propuesta_valor}\n\n"
        "Experiencias laborales:\n"
        + "\n".join(experiencias)
        + "\n\nFormación académica:\n"
        + "\n".join(formacion)
        + "\n\nHabilidades: "
        + request.habilidades
    )
    return prompt
