"""Traduction du manifeste brut en modèle Sydonia éditable.

C'est ici que s'appliquent les décisions métier : quel port devient quel code,
quelle valeur de fret retenir, comment recomposer la désignation des marchandises.
Le parseur, lui, reste purement descriptif.
"""

from __future__ import annotations

import re

from app.schemas.manifest import BolSegment, GeneralSegment, ManifestModel, ParseOptions, SourceInfo

from .manifest_parser import RawBol, RawManifest, vins_in_line

VIN_MARKER_RE = re.compile(r"^VIN\s*(NO\.?|NUMBER|:)?\s*:?$", re.I)


def to_iso_date(value: str | None) -> str:
    """« 05-08-2026 » -> « 2026-08-05 »."""
    if not value:
        return ""
    match = re.search(r"(\d{2})-(\d{2})-(\d{4})", value)
    return f"{match.group(3)}-{match.group(2)}-{match.group(1)}" if match else ""


def port_code(name: str, options: ParseOptions) -> str:
    key = re.sub(r"\s+", " ", (name or "")).strip().upper()
    return options.port_codes.get(key, "")


def _clean_line(text: str) -> str:
    """Retire le tiret de continuation que MOL ajoute en fin de ligne d'adresse."""
    return re.sub(r"\s+", " ", re.sub(r"\s*-\s*$", "", text)).strip()


def split_name_address(lines: list[str] | None, clean: bool) -> tuple[str, str]:
    values = [_clean_line(v) for v in (lines or [])] if clean else list(lines or [])
    values = [v for v in values if v.strip()]
    if not values:
        return "", ""
    return values[0].strip(), "\n".join(values[1:]).strip()


def compact_description(goods_lines: list[str], vins: list[str]) -> str:
    """Intitulé commercial suivi de la liste des châssis.

    On coupe à la première ligne qui contient un châssis ou au marqueur
    « VIN NO. », puis on réémet la liste sous une forme homogène.
    """
    head: list[str] = []
    for line in goods_lines:
        if vins_in_line(line) or VIN_MARKER_RE.match(line):
            break
        if re.fullmatch(r"[-\s]+", line):
            continue
        head.append(line)
    text = "\n".join(head)
    if vins:
        text += ("\n" if text else "") + "VIN NO:\n" + "\n".join(vins)
    return text


def commercial_description_from_goods(goods_lines: list[str]) -> str:
    """Extrait la description commerciale sans VIN ni détails techniques."""
    head: list[str] = []
    stop_markers = ("VIN", "CHASSIS", "MODEL", "HS CODE", "H.S", "UNIT(", "**TOTAL**", "VIN NO", "FREIGHT", "PREPAID", "NUMBER(S)", "IDENTIFICATION")
    for line in goods_lines:
        upper = line.upper()
        if any(m in upper for m in stop_markers):
            break
        if re.fullmatch(r"[-\s]+", line):
            continue
        head.append(line)
    text = "\n".join(head)
    return re.sub(r"\s+", " ", text).strip() if text else ""


def _build_bol(index: int, raw: RawBol, options: ParseOptions, country_of_origin: str = "") -> BolSegment:
    exporter_name, exporter_address = split_name_address(raw.fields.get("SH"), options.clean_addresses)
    consignee_name, consignee_address = split_name_address(raw.fields.get("CO"), options.clean_addresses)
    notify_name, notify_address = split_name_address(raw.fields.get("NF"), options.clean_addresses)

    marks = "\n".join(raw.fields.get("MN") or []).strip() or options.shipping_marks
    if options.use_nm_for_marks:
        marks = options.shipping_marks

    if options.freight_mode == "total":
        freight = raw.freight_total if raw.freight_total is not None else raw.freight_base
    else:
        freight = raw.freight_base if raw.freight_base is not None else raw.freight_total

    description = (
        "\n".join(raw.goods_lines)
        if options.description_mode == "full"
        else compact_description(raw.goods_lines, raw.vins)
    )

    return BolSegment(
        line_number=index + 1,
        bol_reference=raw.bl_reference,
        bol_nature=options.bol_nature,
        bol_type_code=options.bol_type_code,
        loading_port=raw.loading_port,
        loading_code=port_code(raw.loading_port, options),
        unloading_port=raw.discharge_port,
        unloading_code=port_code(raw.discharge_port, options) or options.place_of_destination_code,
        exporter_name=exporter_name,
        exporter_address=exporter_address,
        consignee_name=consignee_name,
        consignee_address=consignee_address,
        notify_name=notify_name,
        notify_address=notify_address,
        packages=raw.packages or len(raw.vins) or 0,
        package_type_code=options.package_type_code,
        gross_mass=raw.weight or 0,
        volume=raw.volume or 0,
        containers=0,
        shipping_marks=marks,
        goods_description=description,
        vins=list(raw.vins),
        freight_value=freight,
        freight_currency=raw.currency or "USD",
        location_code=options.location_code,
        location_info=options.location_info,
        booking_number="\n".join(raw.fields.get("BN") or []).strip(),
        prepaid_at=raw.prepaid_at or "",
        freight_base=raw.freight_base,
        freight_total=raw.freight_total,
        source_pages=list(raw.pages),
        vehicle_make=raw.vehicle_make,
        vehicle_models=list(raw.vehicle_models),
        hs_codes=list(raw.hs_codes),
        hs_commercial_descriptions=[commercial_description_from_goods(raw.goods_lines)] * len(raw.hs_codes) if raw.hs_codes else [],
        country_of_origin=country_of_origin,
    )


def to_model(manifest: RawManifest, options: ParseOptions) -> ManifestModel:
    meta = manifest.meta
    country_of_origin = options.country_codes.get((meta.get("flag") or "").upper(), "")
    bols = [_build_bol(i, raw, options, country_of_origin) for i, raw in enumerate(manifest.bols)]

    computed_packages = sum(b.packages for b in bols)
    computed_mass = sum(b.gross_mass for b in bols)

    departure = meta.get("sail_date") if options.departure_date_source == "sail" else meta.get("print_date")

    general = GeneralSegment(
        customs_office=options.customs_office,
        voyage_number=meta.get("voyage", ""),
        date_of_departure=to_iso_date(departure),
        date_of_arrival=to_iso_date(meta.get("arrival_date")),
        total_bols=len(bols),
        total_packages=int(manifest.grand.get("packages") or computed_packages),
        total_containers=0,
        total_gross_mass=float(manifest.grand.get("weight") or computed_mass),
        carrier_code=options.carrier_code,
        carrier_name=options.carrier_name,
        carrier_address=options.carrier_address,
        mode_of_transport=options.mode_of_transport,
        vessel_name=meta.get("vessel_name", ""),
        nationality_code=options.country_codes.get((meta.get("flag") or "").upper(), ""),
        place_of_transporter=meta.get("flag", ""),
        place_of_departure_code=options.place_of_departure_code,
        place_of_destination_code=(
            port_code(meta.get("place_of_delivery") or meta.get("port_of_discharge", ""), options)
            or options.place_of_destination_code
        ),
    )

    source = SourceInfo(
        sail_date=to_iso_date(meta.get("sail_date")),
        print_date=to_iso_date(meta.get("print_date")),
        vessel_code=meta.get("vessel_code", ""),
        service_line=meta.get("service_line", ""),
        computed_packages=computed_packages,
        computed_mass=computed_mass,
        grand_packages=manifest.grand.get("packages"),
        grand_mass=manifest.grand.get("weight"),
    )

    return ManifestModel(general=general, bols=bols, source=source)
