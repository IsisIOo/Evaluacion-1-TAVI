# agregador de rutas
from fastapi import APIRouter
from app.api.v1.cv_endpoint import cv_router
from app.api.v1.auth_endpoint import auth_router

api_router = APIRouter()

api_router.include_router(cv_router, prefix="/cv", tags=["Generación de CV"])

# nueva ruta de autenticación
api_router.include_router(auth_router, prefix="/auth", tags=["Auth"])