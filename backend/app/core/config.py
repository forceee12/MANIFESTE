"""Configuration de l'application, surchargeable par variables d'environnement."""

from __future__ import annotations

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="MANIFEST_", env_file=".env", extra="ignore")

    app_name: str = "Manifeste MOL vers XML Sydonia"
    api_version: str = "1.0.0"
    # Origines autorisées pour le frontend React (Vite en développement).
    cors_origins: list[str] = ["http://localhost:5173", "http://127.0.0.1:5173"]
    max_upload_bytes: int = 25_000_000


settings = Settings()
