# lee el archivo .env y carga las variables de entorno para la configuración de la aplicación
from pydantic.v1 import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    """
    Clase para gestionar variables de entorno y configuración de la aplicación y modelos
    Pydantic valida automaticamente los tipos al iniciar la app
    """
    # Base de datos
    #MONGO_URI: str = [ Isidora llenar URI de MongoDB]
    #MONGO_DB_NAME: str = [Isidora llenar nombre de la base de datos]

    # Configuración LLM
    GEMINI_API_KEY: str = Field(..., description="API key para acceder a modelo Gemini")
    MODEL_NAME: str = Field(default="gemini-1.5-flash", description="Nombre del modelo a usar")
    MAX_TOKENS: int = Field(default=1000, description="Máximo de tokens en la respuesta del modelo")
    
    # Configuración de Pydantic para leer el .env
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
    )

# settings es un singleton: una instancia global que se puede importar en cualquier parte de la aplicación 
# para acceder a la configuración
settings = Settings()