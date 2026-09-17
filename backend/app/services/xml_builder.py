"""Sérialisation du modèle en XML Awmds (Sydonia).

L'écriture est faite à la main plutôt qu'avec ElementTree : la douane attend une
indentation et un ordre de balises stables, et les sauts de ligne à l'intérieur
des adresses doivent être conservés tels quels.
"""

from __future__ import annotations

import re

from app.schemas.manifest import BolSegment, ManifestModel

_ESCAPES = (("&", "&amp;"), ("<", "&lt;"), (">", "&gt;"))


def escape(value) -> str:
    text = "" if value is None else str(value)
    for old, new in _ESCAPES:
        text = text.replace(old, new)
    return text


def tag(name: str, value, indent: str) -> str:
    return f"{indent}<{name}>{escape(value)}</{name}>"


def fmt_decimal(value) -> str:
    """Nombre sans zéros inutiles : 51560.0 -> « 51560 », 449.400 -> « 449.4 »."""
    if value is None or value == "":
        return ""
    try:
        number = float(value)
    except (TypeError, ValueError):
        return str(value)
    return f"{round(number, 3):g}"


def fmt_money(value) -> str:
    if value is None or value == "":
        return ""
    try:
        return f"{float(value):.2f}"
    except (TypeError, ValueError):
        return str(value)


def xml_file_name(model: ManifestModel) -> str:
    vessel = re.sub(r"[^A-Za-z0-9]+", "_", model.general.vessel_name or "MANIFESTE").strip("_")
    return f"{vessel}_{model.general.voyage_number}.xml".upper()


def _bol_block(bol: BolSegment) -> list[str]:
    lines = ["", "  <Bol_segment>", "    <Bol_id>"]
    lines += [
        tag("Bol_reference", bol.bol_reference, "      "),
        tag("Line_number", bol.line_number, "      "),
        tag("Bol_nature", bol.bol_nature, "      "),
        tag("Bol_type_code", bol.bol_type_code, "      "),
        "    </Bol_id>",
        "",
        "    <Load_unload_place>",
        tag("Place_of_loading_code", bol.loading_code, "      "),
        tag("Place_of_unloading_code", bol.unloading_code, "      "),
        "    </Load_unload_place>",
        "",
        "    <Traders_segment>",
        "      <Exporter>",
        tag("Exporter_name", bol.exporter_name, "        "),
        tag("Exporter_address", bol.exporter_address, "        "),
        "      </Exporter>",
        "",
        "      <Notify>",
        tag("Notify_name", bol.notify_name, "        "),
        tag("Notify_address", bol.notify_address, "        "),
        "      </Notify>",
        "",
        "      <Consignee>",
        tag("Consignee_name", bol.consignee_name, "        "),
        tag("Consignee_address", bol.consignee_address, "        "),
        "      </Consignee>",
        "    </Traders_segment>",
        "",
        "    <Goods_segment>",
        tag("Number_of_packages", bol.packages, "      "),
        tag("Package_type_code", bol.package_type_code, "      "),
        tag("Gross_mass", fmt_decimal(bol.gross_mass), "      "),
        tag("Shipping_marks", bol.shipping_marks, "      "),
        tag("Goods_description", bol.goods_description, "      "),
        tag("Volume_in_cubic_meters", fmt_decimal(bol.volume), "      "),
        tag("Num_of_ctn_for_this_bol", bol.containers or 0, "      "),
        "    </Goods_segment>",
        "",
        "    <Value_segment>",
        "      <Freight_segment>",
        tag("Freight_value", fmt_money(bol.freight_value), "        "),
        tag("Freight_currency", bol.freight_currency, "        "),
        "      </Freight_segment>",
        "    </Value_segment>",
        "",
        "    <Location>",
        tag("Location_code", bol.location_code, "      "),
        tag("Location_info", bol.location_info, "      "),
        "    </Location>",
        "    <Authorize/>",
        "    <HS_Compliance>",
    ]
    for idx, hs_code in enumerate(bol.hs_codes):
        lines.append(tag("HS_code", hs_code, "      "))
        desc = bol.hs_commercial_descriptions[idx] if idx < len(bol.hs_commercial_descriptions) else ""
        lines.append(tag("Commercial_description", desc, "      "))
        lines.append(tag("Number_of_packages", bol.packages or 0, "      "))
        lines.append(tag("Gross_mass", fmt_decimal(bol.gross_mass), "      "))
        lines.append(tag("Volume_in_cubic_meters", fmt_decimal(bol.volume), "      "))
        lines.append(tag("Package_type_code", bol.package_type_code or "", "      "))
        lines.append(tag("Country_of_origin", bol.country_of_origin or "", "      "))
    lines += [
        "    </HS_Compliance>",
        "  </Bol_segment>",
    ]
    return lines


def build_xml(model: ManifestModel) -> str:
    general = model.general
    lines = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        "<Awmds>",
        "  <General_segment>",
        "    <General_segment_id>",
        tag("Customs_office_code", general.customs_office, "      "),
        tag("Voyage_number", general.voyage_number, "      "),
        tag("Date_of_departure", general.date_of_departure, "      "),
        tag("Date_of_arrival", general.date_of_arrival, "      "),
        "    </General_segment_id>",
        "",
        "    <Totals_segment>",
        tag("Total_number_of_bols", general.total_bols, "      "),
        tag("Total_number_of_packages", general.total_packages, "      "),
        tag("Total_number_of_containers", general.total_containers, "      "),
        tag("Total_gross_mass", fmt_decimal(general.total_gross_mass), "      "),
        "    </Totals_segment>",
        "",
        "    <Transport_information>",
        "      <Carrier>",
        tag("Carrier_code", general.carrier_code, "        "),
        tag("Carrier_name", general.carrier_name, "        "),
        tag("Carrier_address", general.carrier_address, "        "),
        "      </Carrier>",
        "",
        tag("Mode_of_transport_code", general.mode_of_transport, "      "),
        tag("Identity_of_transporter", general.vessel_name, "      "),
        tag("Nationality_of_transporter_code", general.nationality_code, "      "),
        tag("Place_of_transporter", general.place_of_transporter, "      "),
        "    </Transport_information>",
        "",
        "    <Load_unload_place>",
        tag("Place_of_departure_code", general.place_of_departure_code, "      "),
        tag("Place_of_destination_code", general.place_of_destination_code, "      "),
        "    </Load_unload_place>",
        "  </General_segment>",
    ]
    for bol in model.bols:
        lines += _bol_block(bol)
    lines.append("</Awmds>")
    return "\n".join(lines)
