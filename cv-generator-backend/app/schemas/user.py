from pydantic import BaseModel, EmailStr, Field

class UserCreate(BaseModel):
    """Esquema para la creación de un nuevo usuario."""
    email: EmailStr 
    password: str = Field(..., min_length=6, description="Contraseña del usuario")
    nombre: str

class UserResponse(BaseModel):
    """Esquema para la respuesta de datos de usuario."""
    id: str 
    email: EmailStr
    nombre: str
    is_active: bool

    class Config:
        from_attributes = True