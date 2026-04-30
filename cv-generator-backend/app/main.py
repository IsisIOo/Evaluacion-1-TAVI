import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from app.db.session import connect_to_mongo, close_mongo_connection
from fastapi.middleware.cors import CORSMiddleware
from app.api.api import api_router

# configuración de logs para consola
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

@asynccontextmanager # contexto para manejar la conexión a MongoDB durante el ciclo de vida de la aplicación
async def lifespan(app: FastAPI):
    """
    Manejador del ciclo de vida de la aplicación FastAPI
    """
    # logica de inicio
    logger.info("Iniciando la aplicación FastAPI")
    await connect_to_mongo() # abre la conexión a MongoDB al iniciar la aplicación
    logger.info("Aplicación FastAPI iniciada correctamente")
    
    yield # aquí es donde se ejecutan los endpoints y la lógica de la aplicación mientras está corriendo

    # logica de cierre
    logger.info("Cerrando la aplicación FastAPI")
    await close_mongo_connection() 
    logger.info("Aplicación FastAPI cerrada correctamente")

def create_app() -> FastAPI:
    """
    Función para crear la instancia de FastAPI con el manejador de ciclo de vida
    """
    app = FastAPI(
        title="CV Generator Backend",
        description="Backend para generar CVs",
        version="1.0.0",
        lifespan=lifespan,
    )

    # configuración de CORS
    # ajustar a valores más restrictivos en un futuro
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"], # En producción, agregar aquí URL de frontend
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # rutas
    app.include_router(api_router, prefix="/api")

    # endpoint de salud
    @app.get("/", tags=["Health"])
    async def root():
        return {
            "status": "ok",
            "project": "CV Generator Backend",
            "docs": "/docs",
        }

    return app

# instancia de la aplicación
app = create_app() 