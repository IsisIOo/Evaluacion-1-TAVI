# app/api/v1/auth_endpoint.py
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from app.db.session import get_db
from app.db.user_repository import UserRepository
from app.schemas.user import UserCreate, UserResponse
from app.db.models import UserDocument
from app.core.security import get_password_hash, verify_password, create_access_token


router = APIRouter()

# Alias esperado por el agregador de rutas
auth_router = router

@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(user_in: UserCreate, db = Depends(get_db)):
    user_repo = UserRepository(db)
    
    # Verificar si el correo ya existe
    existing_user = await user_repo.get_by_email(user_in.email)
    if existing_user:
        raise HTTPException(
            status_code=400,
            detail="El correo electrónico ya está registrado."
        )
    
    # Hashear contraseña y guardar
    hashed_password = get_password_hash(user_in.password)
    new_user_doc = UserDocument(
        email=user_in.email,
        password_hash=hashed_password,
        nombre=user_in.nombre
    )
    
    created_user = await user_repo.create_user(new_user_doc)
    return created_user

@router.post("/login")
async def login(form_data: OAuth2PasswordRequestForm = Depends(), db = Depends(get_db)):
    user_repo = UserRepository(db)
    
    # El formulario del OAuth2 guarda el email en el campo 'username'
    user = await user_repo.get_by_email(form_data.username)
    if not user or not verify_password(form_data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Correo o contraseña incorrectos",
            headers={"WWw-Authenticate": "Bearer"},
        )
    
    # Generar Token
    access_token = create_access_token(subject=user.id)
    return {
        "access_token": access_token,
        "token_type": "bearer"
    }

@router.get("/users", response_model=list[UserResponse])
async def get_users(db = Depends(get_db)):
    """
    Endpoint para obtener el listado de todos los usuarios registrados
    """
    user_repo = UserRepository(db)
    users = await user_repo.get_all_users()
    return users