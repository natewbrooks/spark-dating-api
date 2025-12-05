import json
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field
from fastapi.encoders import jsonable_encoder

class Settings(BaseSettings):
    app_name: str = "Spark API"

    supabase_jwt_secret: str = Field(env="SUPABASE_JWT_SECRET")
    supabase_url: str = Field(env="SUPABASE_URL")
    supabase_anon_key: str = Field(env="SUPABASE_ANON_KEY")
    supabase_service_key: str = Field(env="SUPABASE_SERVICE_KEY")

    db_user: str = Field(env="DB_USER")
    db_pass: str = Field(env="DB_PASS")
    db_port: str = Field(env="DB_PORT")
    db_host: str = Field(env="DB_HOST")
    db_name: str = Field(env="DB_NAME")
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
    )

settings = Settings()