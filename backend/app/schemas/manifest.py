"""Contrat d'échange entre FastAPI et React.

``ManifestModel`` est à la fois la sortie de ``POST /api/manifests/parse`` et
l'entrée de ``POST /api/manifests/xml`` : le front reçoit un modèle, l'utilisateur
le corrige, le front le renvoie tel quel. Le back ne conserve rien entre les deux.
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

from app.core.reference import COUNTRY_CODES, PORT_CODES


class ParseOptions(BaseModel):
    """Constantes du bureau et choix de restitution."""

    customs_office: str = "21TO"
    place_of_departure_code: str = "REPDG"
    place_of_destination_code: str = "MGTMM"

    carrier_code: str = "AGL"
    carrier_name: str = "AFRICA GLOBAL LOGISTICS"
    carrier_address: str = (
        "RUE DU CAPITAINE SCHOEL  AMPASIMAZA\nAMPASIMAZAVA BP 411 TOAMASINA"
    )

    mode_of_transport: str = "1"
    bol_nature: str = "23"
    bol_type_code: str = "CTR"
    package_type_code: str = "VH"
    location_code: str = "21TO.TPH"
    location_info: str = "TPH VEHICULES FER TOAMASINA"

    shipping_marks: str = "N/M"
    use_nm_for_marks: bool = False
    clean_addresses: bool = True
    description_mode: Literal["compact", "full"] = "compact"
    freight_mode: Literal["base", "total"] = "base"
    departure_date_source: Literal["print", "sail"] = "print"
    default_hs_code: str = "8703"

    port_codes: dict[str, str] = Field(default_factory=lambda: dict(PORT_CODES))
    country_codes: dict[str, str] = Field(default_factory=lambda: dict(COUNTRY_CODES))


class GeneralSegment(BaseModel):
    customs_office: str = ""
    voyage_number: str = ""
    date_of_departure: str = ""
    date_of_arrival: str = ""

    total_bols: int = 0
    total_packages: int = 0
    total_containers: int = 0
    total_gross_mass: float = 0

    carrier_code: str = ""
    carrier_name: str = ""
    carrier_address: str = ""

    mode_of_transport: str = "1"
    vessel_name: str = ""
    nationality_code: str = ""
    place_of_transporter: str = ""

    place_of_departure_code: str = ""
    place_of_destination_code: str = ""


class BolSegment(BaseModel):
    line_number: int
    bol_reference: str
    bol_nature: str
    bol_type_code: str

    loading_port: str = ""
    loading_code: str = ""
    unloading_port: str = ""
    unloading_code: str = ""

    exporter_name: str = ""
    exporter_address: str = ""
    consignee_name: str = ""
    consignee_address: str = ""
    notify_name: str = ""
    notify_address: str = ""

    packages: int = 0
    package_type_code: str = "VH"
    gross_mass: float = 0
    volume: float = 0
    containers: int = 0
    shipping_marks: str = ""
    goods_description: str = ""
    vins: list[str] = Field(default_factory=list)
    vehicle_make: str = ""
    vehicle_models: list[str] = Field(default_factory=list)
    hs_codes: list[str] = Field(default_factory=list)
    hs_commercial_descriptions: list[str] = Field(default_factory=list)

    freight_value: float | None = None
    freight_currency: str = "USD"

    location_code: str = ""
    location_info: str = ""

    # Informations de traçabilité, non exportées dans le XML.
    booking_number: str = ""
    prepaid_at: str = ""
    freight_base: float | None = None
    freight_total: float | None = None
    source_pages: list[int] = Field(default_factory=list)


class SourceInfo(BaseModel):
    """Ce que disait le PDF, pour comparer avec ce que l'utilisateur a saisi."""

    sail_date: str = ""
    print_date: str = ""
    vessel_code: str = ""
    service_line: str = ""
    computed_packages: int = 0
    computed_mass: float = 0
    grand_packages: int | None = None
    grand_mass: float | None = None


class ManifestModel(BaseModel):
    general: GeneralSegment
    bols: list[BolSegment]
    source: SourceInfo


class ValidationIssue(BaseModel):
    level: Literal["error", "warning"]
    message: str
    bol_line: int | None = None


class ParseResponse(BaseModel):
    file_name: str
    model: ManifestModel
    issues: list[ValidationIssue]


class XmlRequest(BaseModel):
    model: ManifestModel


class XmlResponse(BaseModel):
    file_name: str
    xml: str
    issues: list[ValidationIssue]
