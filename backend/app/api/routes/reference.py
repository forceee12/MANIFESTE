"""Référentiel exposé au frontend : codes ports, codes pays, options par défaut."""

from __future__ import annotations

from fastapi import APIRouter

from app.core.reference import COUNTRY_CODES, PORT_CODES
from app.schemas.manifest import ParseOptions

router = APIRouter(prefix="/api/reference", tags=["reference"])


@router.get("/options", response_model=ParseOptions)
async def default_options() -> ParseOptions:
    """Options par défaut du bureau, servies au premier chargement de l'interface."""
    return ParseOptions()


@router.get("/ports")
async def ports() -> dict[str, str]:
    return PORT_CODES


@router.get("/countries")
async def countries() -> dict[str, str]:
    return COUNTRY_CODES
