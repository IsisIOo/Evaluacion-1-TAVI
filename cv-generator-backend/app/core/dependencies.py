"""
Dependencias de autenticación para FastAPI.
"""
from typing import Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.core.security import decode_access_token
from app.db.models import UserDocument
from app.db.session import get_db
from app.db.user_repository import UserRepository

bearer_scheme = HTTPBearer(auto_error=False)


async def get_current_user_optional(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(bearer_scheme),
    db=Depends(get_db),
) -> Optional[UserDocument]:
    """
    Devuelve el usuario autenticado o None si no hay token válido.
    No lanza errores: se usa en endpoints que permiten acceso anónimo.
    """
    if credentials is None:
        return None

    subject = decode_access_token(credentials.credentials)
    if subject is None:
        return None

    user = await UserRepository(db).get_by_id(subject)
    if user is None or not user.is_active:
        return None

    return user


async def get_current_user(
    user: Optional[UserDocument] = Depends(get_current_user_optional),
) -> UserDocument:
    """
    Exige un token JWT válido. Lanza 401 si falta, es inválido o el usuario no existe.
    """
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="No autenticado: se requiere un token válido.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user
