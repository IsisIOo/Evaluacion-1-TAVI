# endpoint para manejar las solicitudes relacionadas con la generación de CVs
import logging
from fastapi import APIRouter, HTTPException
from app.schemas.cv_response import CVResponse, ExperienciaLaboralSalida, FormacionAcademicaSalida
from app.schemas.cv_request import CVRequest

logger = logging.getLogger(__name__)

router = APIRouter() # instancia del router para este endpoint

@router.post("/generate", response_model=CVResponse)
async def generate_cv_endpoint(request: CVRequest):
    """
    Recibe la información del usuario, llama al servicio de generación de CV y solicita la generación del CV.
    """
    logger.info(f"Recibida solicitud de generación de CV para el usuario: {request.nombre}")
    
    try:
        # [Para Toto]: aquí debes llamar a tu servicio de generación de CV, pasarle la información del usuario y retornar la respuesta generada por el LLM
        # ejemplo:
        # cv_response = await generar_cv(request)
        # return cv_response

        # respuesta de ejemplo
        formacion_mock = [FormacionAcademicaSalida(grado_y_lugar="Ingeniería Informática - Universidad de Santiago de Chile")]
        experiencia_mock = [ExperienciaLaboralSalida(
            puesto_y_empresa="Desarrollador Backend en TechCorp",
            resumen_logros="Desarrollé y mantuve la API principal, mejorando el rendimiento en un 30% y colaboré en la migración a la nube."
        )]
        return CVResponse(
                encabezado=f"Perfil profesional destacado de {request.nombre_completo}. Altamente motivado y con gran capacidad de adaptación.",
                formacion_academica=formacion_mock,
                experiencia_laboral=experiencia_mock,
                competencias_complementarias=["Trabajo en equipo", "Resolución de problemas", request.informacion_extra or "Proactividad"]
            )
    except Exception as e:
        logger.error(f"Error al generar el CV: {e}")
        raise HTTPException(
            status_code=500,
            detail="Error al generar el CV. Por favor, inténtalo de nuevo más tarde."
        )