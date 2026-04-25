from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="CV Generator AI API")

# Configuración de CORS para que Vue.js pueda conectarse
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # En producción, agregar aquí URL de frontend
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    return {"message": "Bienvenido a la API del Generador de CV"}
