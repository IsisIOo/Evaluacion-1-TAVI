# schema para definir la estructura de lo que viene del frontend
from pydantic import BaseModel, Field
from typing import List

class PersonalInfo(BaseModel):
    nombre_completo: str = Field(..., description="Nombre completo del usuario")
    profesion: str = Field(..., description="Profesión o cargo principal")
    email: str = Field(..., description="Correo electrónico")
    telefono: str = Field(..., description="Número de teléfono")
    linkedin: str = Field(..., description="URL del perfil de LinkedIn")
    rut: str = Field(..., description="RUT o documento de identidad")
    ciudad: str = Field(..., description="Ciudad de residencia")

class PerfilInfo(BaseModel):
    anios_experiencia: int = Field(..., description="Años de experiencia laboral")
    experticia: str = Field(..., description="Áreas de experiencia o especialización")
    propuesta_valor: str = Field(..., description="Propuesta de valor profesional")

class ExperienciaEntrada(BaseModel):
    cargo: str = Field(..., description="Cargo o posición ocupada")
    empresa: str = Field(..., description="Nombre de la empresa")
    pais: str = Field(..., description="País donde se trabajó")
    periodo: str = Field(..., description="Periodo de trabajo")
    descripcion: str = Field(..., description="Descripción de responsabilidades y resultados")
    logros: str = Field(..., description="Logros relevantes en el puesto")

class FormacionEntrada(BaseModel):
    titulo: str = Field(..., description="Título o grado obtenido")
    institucion: str = Field(..., description="Institución educativa")
    periodo: str = Field(..., description="Periodo de estudio")

class CVRequest(BaseModel):
    """
    Esquema que valida el formato enviado por el frontend.

    Input format example:
    {
      "user_id": "uuid-1234",
      "personal": { ... },
      "perfil": { ... },
      "experiencias": [ ... ],
      "formacion": [ ... ],
      "habilidades": "Python (Avanzado), Inglés (B2)"
    }
    """
    user_id: str = Field(..., description="Identificador único del usuario o sesión")
    personal: PersonalInfo = Field(..., description="Datos personales del usuario")
    perfil: PerfilInfo = Field(..., description="Resumen profesional y experiencia")
    experiencias: List[ExperienciaEntrada] = Field(..., description="Lista de experiencias laborales")
    formacion: List[FormacionEntrada] = Field(..., description="Lista de formación académica")
    habilidades: str = Field(..., description="Habilidades técnicas e idiomas en formato de texto")
