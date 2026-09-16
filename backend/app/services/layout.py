"""Géométrie du manifeste MOL.

Le manifeste est un état Crystal Reports en colonnes fixes (page 937 x 576 pts).
Tout le parsing repose sur deux primitives :

* ``cluster_rows``  : regrouper des mots en lignes visuelles (les libellés et
  leurs valeurs ne partagent pas toujours exactement la même ordonnée, d'où la
  tolérance) ;
* ``Band``          : une plage d'abscisses qui identifie une colonne.

Aucune dépendance métier ici : ce module ne connaît que des coordonnées.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Iterable, Sequence

# Tolérance verticale, en points, pour considérer deux mots sur la même ligne.
ROW_TOLERANCE = 5.0

# Bandes de colonnes, en points, relevées sur le gabarit MOL.
BANDS: dict[str, tuple[float, float]] = {
    "bl": (0.0, 78.0),          # colonne « B/L No. » (MOLU + numéro)
    "party": (78.0, 262.0),     # bloc BN/SH/CO/NF/MN/RC/DL/BK/IS/RM
    "goods": (262.0, 400.0),    # désignation des marchandises + châssis
    "wm": (395.0, 432.0),       # marqueurs W (poids) et M (volume)
    "figure": (452.0, 552.0),   # valeurs de poids et de volume
    "rated": (552.0, 615.0),    # base de taxation
    "label": (615.0, 706.0),    # libellés des surcharges (BUNKER, CURRENCY...)
    "currency": (640.0, 760.0),
    "prepaid": (740.0, 852.0),
    "collect": (852.0, 9999.0),
}

_NUMBER_RE = re.compile(r"^-?\d+(\.\d+)?$")


@dataclass(frozen=True)
class Word:
    """Un mot positionné sur la page."""

    x: float      # abscisse du bord gauche
    top: float    # ordonnée depuis le haut de la page
    s: str        # texte normalisé (espaces compressés)


@dataclass
class Row:
    """Une ligne visuelle : des mots triés de gauche à droite."""

    top: float
    words: list[Word] = field(default_factory=list)

    @property
    def text(self) -> str:
        return re.sub(r"\s+", " ", " ".join(w.s for w in self.words)).strip()

    def in_band(self, band: str) -> list[Word]:
        return [w for w in self.words if in_band(w.x, band)]

    def first_number(self, band: str) -> float | None:
        for word in self.in_band(band):
            value = to_number(word.s)
            if value is not None:
                return value
        return None


def in_band(x: float, band: str) -> bool:
    low, high = BANDS[band]
    return low <= x < high


def to_number(text: str | None) -> float | None:
    """Convertit « 51560.000 » ou « -9509.04 » en float, sinon None."""
    if text is None:
        return None
    cleaned = str(text).replace(",", "").strip()
    return float(cleaned) if _NUMBER_RE.match(cleaned) else None


def cluster_rows(words: Iterable[Word], tolerance: float = ROW_TOLERANCE) -> list[Row]:
    """Regroupe des mots en lignes.

    Un libellé (« CO: ») et sa valeur (« OCEAN TRADE ») peuvent différer de 1 à
    4 points d'ordonnée dans le PDF d'origine ; la tolérance les réunit, tout en
    restant bien en dessous de l'interligne réel (environ 12 points).
    """
    ordered = sorted(words, key=lambda w: (w.top, w.x))
    rows: list[Row] = []
    current: Row | None = None
    for word in ordered:
        if current is None or word.top - current.top > tolerance:
            current = Row(top=word.top, words=[word])
            rows.append(current)
        else:
            current.words.append(word)
    for row in rows:
        row.words.sort(key=lambda w: w.x)
    return rows


def rows_in_band(words: Sequence[Word], band: str, tolerance: float = ROW_TOLERANCE) -> list[Row]:
    """Lignes reconstruites à partir d'une seule colonne."""
    return cluster_rows([w for w in words if in_band(w.x, band)], tolerance)


def find_row(rows: Sequence[Row], pattern: str | re.Pattern[str]) -> Row | None:
    regex = re.compile(pattern, re.I) if isinstance(pattern, str) else pattern
    for row in rows:
        if regex.search(row.text):
            return row
    return None
