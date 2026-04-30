# codigo para la conexión a la base de datos MongoDB
import logging
from app.core.config import settings
from motor.motor_asyncio import AsyncIOMotorClient

#[Para Isidora]: editalo como haga falta, esto es solo la plantilla

logger = logging.getLogger(__name__)

class DatabaseSession:
    """
    Clase para mantener el estado de la conexión a MongoDB
    """
    client: AsyncIOMotorClient = None # AsyncIOMotorClient permite que las operaciones con la base de datos no bloqueen el hilo principal
    db = None

# instancia global que mantiene la conexión viva
db_session = DatabaseSession()

async def connect_to_mongo():
    """
    Abre la conexión a MongoDB, se ejecuta al iniciar la aplicación
    """
    try:
        #[Para Isidora]: la URI y el nombre los defines en config.py

        logger.info("Conectando a MongoDB...")
        db_session.client = AsyncIOMotorClient(settings.MONGO_URI)
        db_session.db = db_session.client[settings.MONGO_DB_NAME]
        logger.info("Conexión a MongoDB establecida.")
    except Exception as e:
        logger.error(f"Error al conectar a MongoDB: {e}")
        raise e

async def close_mongo_connection():
    """
    Cierra la conexión a MongoDB, se ejecuta al cerrar la aplicación
    """
    if db_session.client:
        logger.info("Cerrando conexión a MongoDB...")
        db_session.client.close()
        logger.info("Conexión a MongoDB cerrada.")

def get_db():
    """
    Inyección de dependencia para FastAPI:
    Cada vez que un endpoint necesite acceder a la base de datos, llamará a esta función para obtener la instancia de la base de datos.
    """
    if db_session.db is None:
        raise Exception("Conexión a MongoDB no establecida.")
    return db_session.db