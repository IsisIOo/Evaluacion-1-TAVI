"""
Modelos de datos para MongoDB
Reutiliza los esquemas de cv_response.py para mantener consistencia
"""
from pydantic import BaseModel, Field, EmailStr
from typing import Optional
from datetime import datetime
from app.schemas.cv_response import Personal, Perfil, Experiencia, Formacion


class CVDocument(BaseModel):
    """
    Modelo de documento CV para almacenar en MongoDB.
    Extiende la estructura de CVResponse con metadata de persistencia.
    """
    id: Optional[str] = Field(None, alias="_id")
    user_id: str = Field(..., description="ID único del usuario")
    personal: Personal
    perfil: Perfil
    experiencias: list[Experiencia]
    formacion: list[Formacion]
    habilidades: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True


class UserDocument(BaseModel):
    """informacion del usuario para autenticacion y gestion de cuentas"""
    id: Optional[str] = Field(None, alias="_id")
    email: EmailStr = Field(..., description="Correo electrónico del usuario")
    password_hash: str = Field(..., description="Hash de la contraseña del usuario")    
    nombre: str = Field(..., description="Nombre completo del usuario")
    is_active: bool = Field(default=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:        
        populate_by_name = True
        