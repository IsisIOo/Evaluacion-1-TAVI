from pydantic import BaseModel, Field
from typing import List

class Personal(BaseModel):
    nombre_completo: str = Field(..., description="Nombre completo del candidato")
    profesion: str = Field(..., description="Profesión actual")
    email: str = Field(..., description="Correo electrónico")
    telefono: str = Field(..., description="Número de teléfono")
    linkedin: str = Field(..., description="URL de LinkedIn")
    rut: str = Field(..., description="RUT del candidato")
    ciudad: str = Field(..., description="Ciudad de residencia")

class Perfil(BaseModel):
    anios_experiencia: int = Field(..., description="Años totales de experiencia laboral")
    experticia: str = Field(..., description="Breve descripción de la experticia")
    propuesta_valor: str = Field(..., description="Resumen profesional o propuesta de valor")

class Experiencia(BaseModel):
    cargo: str = Field(..., description="Cargo ocupado")
    empresa: str = Field(..., description="Nombre de la empresa")
    pais: str = Field(..., description="País donde se realizó la experiencia")
    periodo: str = Field(..., description="Periodo de tiempo trabajado")
    descripcion: str = Field(..., description="Descripción de las funciones")
    logros: str = Field(..., description="Logros alcanzados")

class Formacion(BaseModel):
    titulo: str = Field(..., description="Título obtenido")
    institucion: str = Field(..., description="Institución educativa")
    periodo: str = Field(..., description="Periodo de estudio")

class CVResponse(BaseModel):
    """
    Esquema del JSON final que el backend enviará al frontend.
    """
    personal: Personal
    perfil: Perfil
    experiencias: List[Experiencia]
    formacion: List[Formacion]
    habilidades: str = Field(..., description="Texto que resume las habilidades del usuario")