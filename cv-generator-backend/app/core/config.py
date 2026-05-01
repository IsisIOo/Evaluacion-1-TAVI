from pathlib import Path

from dotenv import load_dotenv
from pydantic import Field
from pydantic_settings import BaseSettings


env_path = Path(__file__).resolve().parents[2] / ".env"
load_dotenv(dotenv_path=env_path)


class Settings(BaseSettings):
    google_api_key: str = Field(..., env="GOOGLE_API_KEY")
    model_name: str = Field("gemini-3.0-flash", env="MODEL_NAME")
    mongo_uri: str = Field("mongodb://localhost:27017/cv_db", env="MONGO_URI")
    api_prefix: str = Field("/api/v1", env="API_PREFIX")

    class Config:
        env_file = env_path
        extra = "ignore"


settings = Settings()
