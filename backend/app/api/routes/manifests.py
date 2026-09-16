"""Endpoints de traitement des manifestes.

Le service est sans état : ``/parse`` rend un modèle, le front le corrige et le
renvoie à ``/xml``. Rien n'est stocké côté serveur, ce qui évite d'avoir à gérer
la confidentialité des données commerciales des clients.
"""

from __future__ import annotations

import json

from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from fastapi.responses import Response

from app.core.config import settings
from app.schemas.manifest import ParseOptions, ParseResponse, XmlRequest, XmlResponse
from app.services.manifest_parser import parse_manifest
from app.services.mapper import to_model
from app.services.pdf_text import NotATextPdf, extract_pages
from app.services.validator import validate
from app.services.xml_builder import build_xml, xml_file_name

router = APIRouter(prefix="/api/manifests", tags=["manifests"])


def _read_options(raw: str | None) -> ParseOptions:
    if not raw:
        return ParseOptions()
    try:
        return ParseOptions.model_validate(json.loads(raw))
    except (json.JSONDecodeError, ValueError) as exc:
        raise HTTPException(status_code=422, detail=f"Options invalides : {exc}") from exc


@router.post("/parse", response_model=ParseResponse)
async def parse_manifest_pdf(
    file: UploadFile = File(..., description="Manifeste MOL au format PDF"),
    options: str | None = Form(None, description="ParseOptions sérialisées en JSON"),
) -> ParseResponse:
    """Lit un manifeste PDF et rend un modèle Sydonia éditable."""
    if file.content_type not in {"application/pdf", "application/octet-stream"} and not (
        file.filename or ""
    ).lower().endswith(".pdf"):
        raise HTTPException(status_code=415, detail="Le fichier doit être un PDF.")

    data = await file.read()
    if len(data) > settings.max_upload_bytes:
        raise HTTPException(
            status_code=413,
            detail=f"Fichier trop volumineux (maximum {settings.max_upload_bytes // 1_000_000} Mo).",
        )

    try:
        pages = extract_pages(data)
    except NotATextPdf as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except Exception as exc:  # PDF corrompu ou protégé
        raise HTTPException(status_code=422, detail=f"PDF illisible : {exc}") from exc

    manifest = parse_manifest(pages)
    if not manifest.bols:
        raise HTTPException(
            status_code=422,
            detail="Aucun connaissement trouvé : ce PDF n'a pas la forme d'un manifeste MOL.",
        )

    model = to_model(manifest, _read_options(options))
    return ParseResponse(file_name=file.filename or "manifeste.pdf", model=model, issues=validate(model))


@router.post("/xml", response_model=XmlResponse)
async def preview_xml(payload: XmlRequest) -> XmlResponse:
    """Rend le XML sous forme de chaîne, pour l'aperçu dans l'interface."""
    return XmlResponse(
        file_name=xml_file_name(payload.model),
        xml=build_xml(payload.model),
        issues=validate(payload.model),
    )


@router.post("/xml/download")
async def download_xml(payload: XmlRequest) -> Response:
    """Rend le XML en pièce jointe. Refuse si un contrôle bloquant échoue."""
    issues = validate(payload.model)
    blocking = [i for i in issues if i.level == "error"]
    if blocking:
        raise HTTPException(
            status_code=409,
            detail={"message": "Contrôles bloquants non résolus.", "issues": [i.model_dump() for i in blocking]},
        )

    name = xml_file_name(payload.model)
    return Response(
        content=build_xml(payload.model).encode("utf-8"),
        media_type="application/xml; charset=utf-8",
        headers={"Content-Disposition": f'attachment; filename="{name}"'},
    )
