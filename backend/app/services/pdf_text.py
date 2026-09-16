"""PDF -> pages de mots positionnés.

Seul module qui dépend de pdfplumber. Le reste de la chaîne ne manipule que des
``Word``, ce qui rend le parseur testable sans PDF.
"""

from __future__ import annotations

import io
import re
from dataclasses import dataclass

import pdfplumber

from .layout import Word


class NotATextPdf(ValueError):
    """Le PDF ne contient pas de couche texte (manifeste scanné)."""


@dataclass
class Page:
    number: int
    width: float
    height: float
    words: list[Word]


def extract_pages(data: bytes) -> list[Page]:
    """Retourne une page par page du PDF, avec ses mots positionnés."""
    pages: list[Page] = []
    with pdfplumber.open(io.BytesIO(data)) as pdf:
        for index, page in enumerate(pdf.pages, start=1):
            words = [
                Word(
                    x=float(w["x0"]),
                    top=float(w["top"]),
                    s=re.sub(r"\s+", " ", w["text"]).strip(),
                )
                for w in page.extract_words(use_text_flow=False, keep_blank_chars=False)
                if w["text"].strip()
            ]
            pages.append(
                Page(number=index, width=float(page.width), height=float(page.height), words=words)
            )

    if not any(p.words for p in pages):
        raise NotATextPdf(
            "Ce PDF ne contient aucun texte : il s'agit probablement d'un scan. "
            "Demandez le manifeste au format PDF natif."
        )
    return pages
