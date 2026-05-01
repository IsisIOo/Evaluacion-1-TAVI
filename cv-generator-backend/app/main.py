from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.endpoints.cv_endpoint import router as cv_router

app = FastAPI(title="CV Generator AI API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(cv_router)


@app.get("/")
async def root():
    return {"message": "Bienvenido a la API del Generador de CV"}
