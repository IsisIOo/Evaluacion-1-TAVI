# schema para definir la estructura de lo que se devuelve al frontend
from pydantic import BaseModel, Field
from typing import List

# [Para Toto]: define aquí la estructura del JSON que el LLM debe generar

class ExperienciaLaboralSalida(BaseModel):
    puesto_y_empresa: str = Field(..., description="Posición ocupada y nombre de la empresa")
    resumen_logros: str = Field(..., description="Resumen profesional y mejorado por el LLM")

class FormacionAcademicaSalida(BaseModel):
    grado_y_lugar: str = Field(..., description="Ejemplo: 'Ingeniería Informática - Universidad Nacional'")

class CVResponse(BaseModel):
    """
    Esquema del JSON final que el LLM debe generar y que el BFF enviará al frontend.
    """
    encabezado: str = Field(
        ..., 
        description="Un breve perfil profesional o resumen atractivo generado a partir del nombre y la experiencia del usuario."
    )
    formacion_academica: List[FormacionAcademicaSalida] = Field(
        ..., 
        description="Lista de la formación académica redactada formalmente."
    )
    experiencia_laboral: List[ExperienciaLaboralSalida] = Field(
        ..., 
        description="Lista de las experiencias laborales con redacción profesional orientada a logros."
    )
    competencias_complementarias: List[str] = Field(
        ..., 
        description="Lista de habilidades (técnicas o blandas) extraídas de la información extra, formateadas como viñetas cortas."
    )