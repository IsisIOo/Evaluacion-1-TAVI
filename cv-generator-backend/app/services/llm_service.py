import json
import logging
from app.core.config import settings
from app.schemas.cv_request import CVRequest
from app.schemas.cv_response import CVResponse
from app.core.llm_factory import get_model

logger = logging.getLogger(__name__)

async def generate_cv(request: CVRequest) -> CVResponse:
    """
    Construye el prompt para el LLM y devuelve la respuesta estructurada del CV.
    Utiliza el SDK de Google Generative AI para obtener una respuesta JSON nativa.
    """
    # Obtenemos la instancia del modelo desde la factory
    model = get_model()
    
    prompt = _build_cv_prompt(request)

    logger.info(f"Generando CV para user_id={request.user_id} con modelo={settings.MODEL_NAME}")

    try:
        # Llamada asíncrona al modelo
        # Al haber configurado 'response_mime_type="application/json"' en la factory,
        # la respuesta será JSON puro.
        response = await model.generate_content_async(contents=prompt)
        
        # Parseamos el JSON devuelto directamente desde la respuesta
        data = json.loads(response.text)
        
        return CVResponse(**data)

    except json.JSONDecodeError as e:
        logger.error(f"Error decodificando JSON del modelo: {e}")
        raise RuntimeError("El modelo no devolvió un JSON válido.")
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
        f"user_id: {request.user_id}\n"
        "Datos personales:\n"
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
        + "\n\nPor favor, devuelve únicamente un JSON válido con la siguiente estructura:\n"
        "{\n"
        "  \"personal\": {\n"
        "    \"nombre_completo\": \"\",\n"
        "    \"profesion\": \"\",\n"
        "    \"email\": \"\",\n"
        "    \"telefono\": \"\",\n"
        "    \"linkedin\": \"\",\n"
        "    \"rut\": \"\",\n"
        "    \"ciudad\": \"\"\n"
        "  },\n"
        "  \"perfil\": {\n"
        "    \"anios_experiencia\": 0,\n"
        "    \"experticia\": \"\",\n"
        "    \"propuesta_valor\": \"\"\n"
        "  },\n"
        "  \"experiencias\": [\n"
        "    { \"cargo\": \"\", \"empresa\": \"\", \"pais\": \"\", \"periodo\": \"\", \"descripcion\": \"\", \"logros\": \"\" }\n"
        "  ],\n"
        "  \"formacion\": [\n"
        "    { \"titulo\": \"\", \"institucion\": \"\", \"periodo\": \"\" }\n"
        "  ],\n"
        "  \"habilidades\": \"\"\n"
        "}"
    )
    return prompt