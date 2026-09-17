"""Lecture d'un manifeste MOL « Cargo Manifest (one BL per page) ».

Algorithme, page par page :

1. L'en-tête (au-dessus de la ligne « B/L No. ») donne le navire, le voyage, le
   pavillon, les dates et les ports. Une page sans « Port of Loading » n'est pas
   une page de connaissement (page de paramètres) et est ignorée.
2. Le corps est découpé en colonnes par abscisse :
   - colonne B/L    -> la référence (« MOLU » + numéro) ;
   - colonne partie -> les blocs préfixés ``XX:`` (SH, CO, NF, MN, RC...) ;
   - colonne marchandise -> désignation et numéros de châssis ;
   - colonnes de droite -> poids, volume, taux, fret et surcharges.
3. Une page portant « * Continued from prev. page * » prolonge le connaissement
   précédent : ses lignes sont concaténées au lieu d'ouvrir un nouveau B/L.
4. La bande « GRAND TOTAL » de la dernière page alimente les totaux du manifeste
   et n'est jamais attribuée à un connaissement.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

from .layout import Row, Word, cluster_rows, in_band, rows_in_band, to_number
from .pdf_text import Page

# Un châssis : 17 caractères alphanumériques, avec au moins une lettre et un chiffre.
VIN_RE = re.compile(r"^[A-Z0-9]{17}$")
LABEL_RE = re.compile(r"^([A-Z]{2}):\s*(.*)$")
DATE_RE = re.compile(r"\d{2}-\d{2}-\d{4}")
UNITS_RE = re.compile(r"^(\d+)\s*UNIT\(S\)$", re.I)
TOTAL_UNITS_RE = re.compile(r"^(\d+)\s*\*\*TOTAL\*\*")
RATE_RE = re.compile(r"/\s*(M3|RT|W/M|UNIT|CBM)", re.I)
CURRENCY_RE = re.compile(r"\b(USD|EUR|JPY|ZAR|MGA)\b")
PREPAID_RE = re.compile(r"PREPAID\s*AT\s*:?\s*(.*)$", re.I)
VIN_MARKER_RE = re.compile(r"^VIN\s*(NO\.?|NUMBER|:)?\s*:?$", re.I)
VEHICLE_MAKE_RE = re.compile(r"([A-Z]+)\s+VEHICLES?", re.I)
MODEL_SECTION_RE = re.compile(r"MODEL\s*UNIT\(S\)", re.I)
MODEL_CODE_RE = re.compile(r"\b([A-Z0-9]{4,}-?[A-Z0-9]{1,})\b")
HS_RE = re.compile(r"\b(\d{4}\.\d{2}(?:/\d{4}\.\d{2})*)\b")

GRAND_BAND = 16.0  # hauteur, en points, de la bande « GRAND TOTAL »


def is_vin(token: str) -> bool:
    return bool(VIN_RE.match(token)) and any(c.isalpha() for c in token) and any(c.isdigit() for c in token)


def vins_in_line(line: str) -> list[str]:
    """Châssis contenus dans une ligne.

    Cas particulier : certains manifestes coupent le châssis en deux
    (« JN1HC2E26Z0 060014 »). On recolle uniquement si le résultat se termine par
    six chiffres, sinon « MAY 2026 PRODUCTION » passerait pour un châssis.
    """
    tokens = line.split()
    found = [t for t in tokens if is_vin(t)]
    if not found and len(tokens) == 2:
        joined = "".join(tokens)
        if is_vin(joined) and re.search(r"\d{6}$", joined) and sum(c.isdigit() for c in joined) >= 6:
            found = [joined]
    return found


@dataclass
class Charge:
    label: str
    amount: float
    collect: bool = False


def _extract_hs_codes(goods_lines: list[str]) -> list[str]:
    codes: list[str] = []
    for line in goods_lines:
        if not re.search(r"H\.?\s*S\.?\s*(CODE|:)", line, re.I):
            continue
        for token in line.split():
            match = HS_RE.match(token)
            if match and match.group(1) not in codes:
                codes.append(match.group(1))
        idx = goods_lines.index(line)
        for next_line in goods_lines[idx + 1 :]:
            if re.search(r"H\.?\s*S\.?\s*(CODE|:)", next_line, re.I) or re.search(r"\bVIN\b", next_line, re.I):
                break
            if not next_line.strip() or re.fullmatch(r"[-\s]+", next_line):
                continue
            for token in next_line.split():
                match = HS_RE.match(token)
                if match and match.group(1) not in codes:
                    codes.append(match.group(1))
    return codes


def _extract_vehicle_info(goods_lines: list[str]) -> tuple[str, list[str]]:
    make = ""
    models: list[str] = []
    for line in goods_lines:
        if not make:
            match = VEHICLE_MAKE_RE.search(line)
            if match:
                make = match.group(1).upper()
        if not MODEL_SECTION_RE.search(line):
            continue
        for next_line in goods_lines[goods_lines.index(line) + 1 :]:
            if re.fullmatch(r"[-\s]+", next_line) or not next_line.strip():
                continue
            match = MODEL_CODE_RE.search(next_line)
            if match:
                code = match.group(1)
                if code not in models:
                    models.append(code)
            else:
                break
    return make, models


@dataclass
class PageResult:
    head: dict = field(default_factory=dict)
    continued: bool = False
    is_grand_total: bool = False
    bl_reference: str = ""
    fields: dict[str, list[str]] = field(default_factory=dict)
    goods_lines: list[str] = field(default_factory=list)
    vins: list[str] = field(default_factory=list)
    unit_count: int | None = None
    total_units: int | None = None
    weight: float | None = None
    volume: float | None = None
    freight_base: float | None = None
    freight_total: float | None = None
    collect_total: float | None = None
    charges: list[Charge] = field(default_factory=list)
    prepaid_at: str | None = None
    currency: str | None = None
    grand: dict = field(default_factory=dict)
    vehicle_make: str = ""
    vehicle_models: list[str] = field(default_factory=list)
    hs_codes: list[str] = field(default_factory=list)


@dataclass
class RawBol:
    bl_reference: str
    pages: list[int] = field(default_factory=list)
    loading_port: str = ""
    discharge_port: str = ""
    delivery_port: str = ""
    fields: dict[str, list[str]] = field(default_factory=dict)
    goods_lines: list[str] = field(default_factory=list)
    vins: list[str] = field(default_factory=list)
    packages: int | None = None
    weight: float | None = None
    volume: float | None = None
    freight_base: float | None = None
    freight_total: float | None = None
    collect_total: float | None = None
    charges: list[Charge] = field(default_factory=list)
    prepaid_at: str | None = None
    currency: str | None = None
    vehicle_make: str = ""
    vehicle_models: list[str] = field(default_factory=list)
    hs_codes: list[str] = field(default_factory=list)


@dataclass
class RawManifest:
    meta: dict = field(default_factory=dict)
    grand: dict = field(default_factory=dict)
    bols: list[RawBol] = field(default_factory=list)


# --------------------------------------------------------------------------- #
# En-tête de page
# --------------------------------------------------------------------------- #
def _parse_header(rows: list[Row]) -> dict:
    head: dict = {}

    # Le bandeau supérieur (« MITSUI O.S.K. LINES  Page: 2 of 20  27-07-2026 ») est
    # éclaté en plusieurs lignes visuelles selon les pages : on le lit d'un bloc.
    banner = " ".join(r.text for r in rows if r.top < 55)
    match = re.search(r"(\d+)\s+of\s+(\d+)", banner)
    if match:
        head["page_no"] = int(match.group(1))
        head["page_count"] = int(match.group(2))
    date = DATE_RE.search(banner)
    if date:
        head["print_date"] = date.group(0)

    vessel_row = next((r for r in rows if r.text.startswith("Vessel")), None)
    if vessel_row:
        # Un nom de navire ou un port tient souvent sur plusieurs mots : on
        # accumule par bande puis on recolle, au lieu d'écraser à chaque mot.
        buckets: dict[str, list[str]] = {}
        for word in vessel_row.words:
            text = word.s.lstrip(":").strip()
            if not text or text in {":", "/"} or re.match(r"^(Vessel|Voyage|Flag|Date|of|Sail|Arrival)$", text):
                continue
            if 50 <= word.x < 85:
                buckets.setdefault("vessel_code", []).append(text)
            elif 85 <= word.x < 240:
                buckets.setdefault("vessel_name", []).append(text)
            elif 285 <= word.x < 340:
                buckets.setdefault("voyage", []).append(text)
            elif 340 <= word.x < 440:
                buckets.setdefault("service_line", []).append(text)
            elif 460 <= word.x < 620:
                buckets.setdefault("flag", []).append(text)
            elif word.x >= 700 and DATE_RE.search(text):
                head["sail_date"] = DATE_RE.search(text).group(0)
        head.update({k: " ".join(v) for k, v in buckets.items()})

    arrival_row = next((r for r in rows if "Date of Arrival" in r.text), None)
    if arrival_row and DATE_RE.search(arrival_row.text):
        head["arrival_date"] = DATE_RE.search(arrival_row.text).group(0)

    port_row = next((r for r in rows if r.text.startswith("Port of Loading")), None)
    if port_row:
        buckets = {}
        for word in port_row.words:
            text = word.s.strip()
            if not text or text in {":", "/"} or re.match(r"^(Port|Place|of|Loading|Discharge|Delivery)$", text):
                continue
            if 85 <= word.x < 292 and not text.isdigit():
                buckets.setdefault("port_of_loading", []).append(text)
            elif 395 <= word.x < 620:
                buckets.setdefault("port_of_discharge", []).append(text)
            elif word.x >= 690:
                buckets.setdefault("place_of_delivery", []).append(text)
        head.update({k: " ".join(v) for k, v in buckets.items()})

    return head


# --------------------------------------------------------------------------- #
# Corps de page
# --------------------------------------------------------------------------- #
def parse_page(page: Page) -> PageResult:
    all_rows = cluster_rows(page.words)

    body_row = next((r for r in all_rows if r.text.startswith("B/L No.")), None)
    body_top = body_row.top + 6 if body_row else 190.0

    header_rows = [r for r in all_rows if r.top < body_top]
    body_words: list[Word] = [w for w in page.words if w.top >= body_top]
    body_rows = cluster_rows(body_words)

    result = PageResult(head=_parse_header(header_rows))
    result.continued = any(re.search(r"Continued from", r.text, re.I) for r in body_rows)

    grand_top = next((r.top for r in body_rows if re.search(r"GRAND\s*TOTAL", r.text, re.I)), None)
    result.is_grand_total = grand_top is not None

    def in_grand(top: float) -> bool:
        return grand_top is not None and abs(top - grand_top) <= GRAND_BAND

    def below_grand(top: float) -> bool:
        return grand_top is not None and top > grand_top + GRAND_BAND

    def skip(top: float) -> bool:
        return in_grand(top) or below_grand(top)

    # --- colonne B/L ---
    parts: list[str] = []
    for row in rows_in_band(body_words, "bl"):
        text = row.text.strip()
        if not text or skip(row.top):
            continue
        if re.search(r"GRAND\s*TOTAL", text, re.I) or re.search(r"Continued", text, re.I):
            continue
        parts.append(text)
    result.bl_reference = "".join(parts)

    # --- colonne des intervenants ---
    current_key: str | None = None
    for row in rows_in_band(body_words, "party"):
        text = row.text
        if not text or skip(row.top) or re.search(r"Continued from", text, re.I):
            continue
        match = LABEL_RE.match(text)
        if match:
            current_key = match.group(1)
            result.fields.setdefault(current_key, [])
            if match.group(2).strip():
                result.fields[current_key].append(match.group(2).strip())
        elif row.words[0].x <= 96:
            # texte libre aligné sur les libellés (mentions de transbordement)
            current_key = "FREE"
            result.fields.setdefault(current_key, []).append(text)
        elif current_key:
            result.fields[current_key].append(text)

    # --- colonne marchandise ---
    for row in rows_in_band(body_words, "goods"):
        text = row.text
        if not text or skip(row.top) or re.search(r"Continued from", text, re.I):
            continue
        units = UNITS_RE.match(text)
        if units:
            result.unit_count = int(units.group(1))
            continue
        if "**TOTAL**" in text:
            total = TOTAL_UNITS_RE.match(text)
            if total:
                result.total_units = int(total.group(1))
            continue
        if re.fullmatch(r"[-\s]+", text):
            continue
        for vin in vins_in_line(text):
            if vin not in result.vins:
                result.vins.append(vin)
        result.goods_lines.append(text)

    result.vehicle_make, result.vehicle_models = _extract_vehicle_info(result.goods_lines)
    result.hs_codes = _extract_hs_codes(result.goods_lines)

    # --- colonnes chiffrées ---
    right_words = [w for w in body_words if w.x >= 260]
    for row in cluster_rows(right_words):
        if below_grand(row.top):
            continue
        is_grand_row = in_grand(row.top)
        text = row.text

        marker = next((w.s.strip() for w in row.in_band("wm") if w.s.strip() in {"W", "M"}), None)
        figure = row.first_number("figure")
        if not is_grand_row:
            if marker == "W" and figure is not None:
                result.weight = figure
            if marker == "M" and figure is not None:
                result.volume = figure

        for word in row.words:
            found = CURRENCY_RE.search(word.s)
            if found and in_band(word.x, "currency"):
                result.currency = found.group(1)

        prepaid = next((v for v in (to_number(w.s) for w in row.in_band("prepaid")) if v is not None), None)
        collect = next((v for v in (to_number(w.s) for w in row.in_band("collect")) if v is not None), None)

        if is_grand_row:
            if prepaid is not None:
                result.grand["prepaid"] = prepaid
            if collect is not None:
                result.grand["collect"] = collect
            if marker == "W" and figure is not None:
                result.grand["weight"] = figure
            if marker == "M" and figure is not None:
                result.grand["volume"] = figure
            packages = next((v for v in (to_number(w.s) for w in row.in_band("goods")) if v is not None), None)
            if packages is not None:
                result.grand["packages"] = int(packages)
            continue

        if "**TOTAL**" in text:
            if prepaid is not None:
                result.freight_total = prepaid
            if collect is not None:
                result.collect_total = collect
            continue

        paid = PREPAID_RE.search(text)
        if paid:
            if paid.group(1).strip():
                result.prepaid_at = paid.group(1).strip()
            continue

        if any(RATE_RE.search(w.s) for w in row.words) and prepaid is not None and result.freight_base is None:
            result.freight_base = prepaid
            continue

        if prepaid is not None or collect is not None:
            label = " ".join(
                w.s.strip() for w in row.in_band("label") if not CURRENCY_RE.fullmatch(w.s.strip())
            ).strip()
            if label:
                result.charges.append(
                    Charge(
                        label=label,
                        amount=prepaid if prepaid is not None else collect,
                        collect=prepaid is None,
                    )
                )

    return result


# --------------------------------------------------------------------------- #
# Document complet
# --------------------------------------------------------------------------- #
META_KEYS = (
    "vessel_name", "vessel_code", "voyage", "service_line", "flag",
    "sail_date", "arrival_date", "print_date", "page_count",
    "port_of_discharge", "place_of_delivery",
)


def parse_manifest(pages: list[Page]) -> RawManifest:
    manifest = RawManifest()
    current: RawBol | None = None

    for page in pages:
        result = parse_page(page)

        if "port_of_loading" not in result.head:
            continue  # page de garde / paramètres : n'alimente ni les métadonnées ni les totaux

        for key in META_KEYS:
            if key not in manifest.meta and key in result.head:
                manifest.meta[key] = result.head[key]
        manifest.grand.update(result.grand)

        if not (result.bl_reference or result.goods_lines or result.fields):
            continue

        if not result.continued and result.bl_reference:
            current = RawBol(
                bl_reference=result.bl_reference,
                loading_port=result.head.get("port_of_loading", ""),
                discharge_port=result.head.get("port_of_discharge", ""),
                delivery_port=result.head.get("place_of_delivery", ""),
                vehicle_make=result.vehicle_make,
                vehicle_models=list(result.vehicle_models),
                hs_codes=list(result.hs_codes),
            )
            manifest.bols.append(current)
        if current is None:
            continue

        current.pages.append(result.head.get("page_no", page.number))
        for key, values in result.fields.items():
            current.fields.setdefault(key, []).extend(values)
        current.goods_lines.extend(result.goods_lines)
        for vin in result.vins:
            if vin not in current.vins:
                current.vins.append(vin)
        if result.vehicle_make and not current.vehicle_make:
            current.vehicle_make = result.vehicle_make
        for model in result.vehicle_models:
            if model not in current.vehicle_models:
                current.vehicle_models.append(model)
        for hs_code in result.hs_codes:
            if hs_code not in current.hs_codes:
                current.hs_codes.append(hs_code)
        if result.unit_count is not None:
            current.packages = result.unit_count
        if result.total_units is not None:
            current.packages = result.total_units
        if result.weight is not None:
            current.weight = result.weight
        if result.volume is not None:
            current.volume = result.volume
        if result.freight_base is not None and current.freight_base is None:
            current.freight_base = result.freight_base
        if result.freight_total is not None:
            current.freight_total = result.freight_total
        if result.collect_total is not None:
            current.collect_total = result.collect_total
        if result.prepaid_at:
            current.prepaid_at = result.prepaid_at
        if result.currency:
            current.currency = result.currency
        current.charges.extend(result.charges)

    return manifest
