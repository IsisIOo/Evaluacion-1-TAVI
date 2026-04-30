# agregador de rutas
from fastapi import APIRouter
from app.api.v1.cv_endpoint import cv_router

api_router = APIRouter()

api_router.include_router(cv_router.router, prefix="/cv", tags=["Generación de CV"])