"""Point d'entrée FastAPI.

    uvicorn app.main:app --reload --port 8000
"""

from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import manifests, reference
from app.core.config import settings

app = FastAPI(title=settings.app_name, version=settings.api_version)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=False,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

app.include_router(manifests.router)
app.include_router(reference.router)


@app.get("/api/health", tags=["health"])
async def health() -> dict[str, str]:
    return {"status": "ok", "version": settings.api_version}
