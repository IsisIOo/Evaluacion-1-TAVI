# schema para definir la estructura de lo que viene del frontend
from pydantic import BaseModel, Field
from typing import List, Optional

# [Para Toto]: define aquí la estructura del JSON que viene del frontend

class ExperienciaEntrada(BaseModel):
    empresa: str = Field(..., description="Nombre de la empresa")
    cargo: str = Field(..., description="Cargo o posición ocupada")
    descripcion: str = Field(..., description="Que hizo o logro en el puesto")

class EducacionEntrada(BaseModel):
    institucion: str = Field(..., description="Nombre de la institución educativa")
    titulo: str = Field(..., description="Título obtenido o carrera estudiada")
    descripcion: str = Field(..., description="Detalles adicionales como logros académicos")

class CVRequest(BaseModel):
    """
    Esquema valida el formato enviado por el frontend
    """
    nombre: str = Field(..., description="Nombre completo del usuario")
    email: str = Field(..., description="Correo electrónico del usuario")
    telefono: str = Field(..., description="Número de teléfono del usuario")
    perfil: str = Field(..., description="Breve descripción o resumen profesional")
    experiencias: List[ExperienciaEntrada] = Field(..., description="Lista de experiencias laborales")
    educacion: List[EducacionEntrada] = Field(..., description="Lista de formación académica")
    informacion_adicional: Optional[str] = Field("", description="Cualquier otra información relevante para el CV")