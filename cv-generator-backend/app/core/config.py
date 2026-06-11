# lee el archivo .env y carga las variables de entorno para la configuración de la aplicación
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    """
    Clase para gestionar variables de entorno y configuración de la aplicación y modelos
    Pydantic valida automaticamente los tipos al iniciar la app
    """
    # Base de datos
    MONGO_URI: str = Field(..., description="URI de conexión de MongoDB")
    MONGO_DB_NAME: str = Field(default="cv_db", description="Nombre de la base de datos MongoDB")

    # Configuración LLM
    # OPENAI_API_KEY: str | None = Field(None, description="API key para OpenAI")
    GEMINI_API_KEY: str | None = Field(None, description="API key para acceder a modelo Gemini")
    MODEL_NAME: str = Field(default="gemini-3.5-flash", description="Nombre del modelo a usar")
    MAX_TOKENS: int = Field(default=1000, description="Máximo de tokens en la respuesta del modelo")
    TEMPERATURE: float = Field(default=0.1, description="Temperatura para la generación del modelo")
    TOP_P: float = Field(default=0.95, description="Probabilidad acumulada top-p para el muestreo del modelo")
    TOP_K: int = Field(default=40, description="Número máximo de tokens a considerar en top-k para el modelo")
    LOCAL_MODEL_PATH: str = Field(default="models/gguf/model.gguf", description="Ruta al modelo local GGUF para LlamaCpp")
    LLM_TIMEOUT: int = Field(default=360, description="Timeout en segundos para la llamada al LLM")
    
    # Configuración de Pydantic para leer el .env
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

# settings es un singleton: una instancia global que se puede importar en cualquier parte de la aplicación 
# para acceder a la configuración
settings = Settings()