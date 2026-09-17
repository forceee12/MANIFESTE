"""Tests de bout en bout sur un manifeste réel.

Le PDF de référence est dans ``tests/fixtures``. Ces tests verrouillent les
valeurs attendues : toute régression du parseur les fait tomber.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.schemas.manifest import ParseOptions
from app.services.manifest_parser import parse_manifest, vins_in_line
from app.services.mapper import to_model
from app.services.pdf_text import extract_pages
from app.services.validator import validate
from app.services.xml_builder import build_xml, xml_file_name

FIXTURE = Path(__file__).parent / "fixtures" / "MANIFEST_CATTLEYA_ACE_V_0112A.pdf"

# Référence B/L, colis, poids, volume, fret de base, nombre de châssis.
EXPECTED = [
    ("MOLU18009181230", 30, 51560.0, 449.400, 61199.29, 30),
    ("MOLU18009206615", 13, 30175.0, 238.348, 23596.45, 13),
    ("MOLU18008808578", 5, 9150.0, 75.235, 10532.90, 5),
    ("MOLU18008808583", 5, 13715.0, 105.215, 14730.10, 5),
    ("MOLU18008808599", 10, 20600.0, 191.590, 20116.95, 10),
    ("MOLU18009036838", 5, 9325.0, 89.700, 6516.71, 5),
    ("MOLU18009069913", 1, 1850.0, 17.086, 1158.77, 1),
    ("MOLU18009156896", 3, 6085.0, 49.860, 3622.33, 3),
    ("MOLU18009156900", 42, 80040.0, 757.880, 55059.98, 42),
    ("MOLU18009166195", 5, 12725.0, 105.785, 13752.05, 0),
]


@pytest.fixture(scope="module")
def model():
    return to_model(parse_manifest(extract_pages(FIXTURE.read_bytes())), ParseOptions())


@pytest.fixture(scope="module")
def client():
    return TestClient(app)


def test_bols_are_split_and_merged(model):
    """Dix connaissements, pages de continuation recollées, grand total exclu."""
    assert [b.bol_reference for b in model.bols] == [e[0] for e in EXPECTED]
    assert model.bols[0].source_pages == [2, 3]
    assert model.bols[4].source_pages == [10]


@pytest.mark.parametrize("index", range(len(EXPECTED)))
def test_bol_figures(model, index):
    ref, packages, mass, volume, freight, vins = EXPECTED[index]
    bol = model.bols[index]
    assert bol.bol_reference == ref
    assert bol.packages == packages
    assert bol.gross_mass == mass
    assert bol.volume == pytest.approx(volume)
    assert bol.freight_base == pytest.approx(freight)
    assert len(bol.vins) == vins


def test_general_segment(model):
    general = model.general
    assert general.voyage_number == "0112A"
    assert general.vessel_name == "CATTLEYA ACE"
    assert general.nationality_code == "JP"
    assert general.date_of_arrival == "2026-08-05"
    assert general.total_bols == 10
    assert general.total_packages == 119
    assert general.total_gross_mass == 235225.0
    assert model.bols[0].loading_code == "JPHIJ"


def test_totals_match_sum_of_bols(model):
    assert model.source.computed_packages == model.general.total_packages
    assert model.source.computed_mass == model.general.total_gross_mass


def test_vin_heuristics():
    assert vins_in_line("JN1HC2E26Z0 060014") == ["JN1HC2E26Z0060014"]   # châssis coupé
    assert vins_in_line("MAY 2026 PRODUCTION") == []                     # faux positif écarté
    assert vins_in_line("JTEARCAJ40K056932 9800722") == ["JTEARCAJ40K056932"]
    assert vins_in_line("ILIL26133MU0101374") == []                      # 18 caractères


def test_xml_structure(model):
    xml = build_xml(model)
    assert xml.startswith('<?xml version="1.0" encoding="UTF-8"?>')
    assert xml.count("<Bol_segment>") == 10
    assert xml.count("<Goods_segment>") == 10
    assert xml.count("<HS_Compliance>") == 10
    assert xml.count("<HS_code>") == 5
    assert "<HS_code>8703.23</HS_code>" in xml
    assert "<HS_code>8702.10</HS_code>" in xml
    assert "<HS_code>8704.21</HS_code>" in xml
    assert "<Freight_value>61199.29</Freight_value>" in xml
    assert "<Total_gross_mass>235225</Total_gross_mass>" in xml
    assert xml_file_name(model) == "CATTLEYA_ACE_0112A.XML"


def test_only_expected_warning(model):
    issues = validate(model)
    assert [i.level for i in issues] == ["warning"]
    assert "MOLU18009166195" in issues[0].message


def test_parse_endpoint(client):
    with FIXTURE.open("rb") as handle:
        response = client.post(
            "/api/manifests/parse",
            files={"file": (FIXTURE.name, handle, "application/pdf")},
            data={"options": json.dumps({"freight_mode": "total"})},
        )
    assert response.status_code == 200
    body = response.json()
    assert len(body["model"]["bols"]) == 10
    assert body["model"]["bols"][0]["freight_value"] == pytest.approx(74272.60)


def test_xml_endpoints(client, model):
    payload = {"model": json.loads(model.model_dump_json())}
    preview = client.post("/api/manifests/xml", json=payload)
    assert preview.status_code == 200
    assert preview.json()["file_name"] == "CATTLEYA_ACE_0112A.XML"

    download = client.post("/api/manifests/xml/download", json=payload)
    assert download.status_code == 200
    assert "attachment" in download.headers["content-disposition"]


def test_download_blocked_by_errors(client, model):
    broken = model.model_copy(deep=True)
    broken.bols[0].loading_code = ""
    response = client.post(
        "/api/manifests/xml/download", json={"model": json.loads(broken.model_dump_json())}
    )
    assert response.status_code == 409


def test_rejects_non_pdf(client):
    response = client.post(
        "/api/manifests/parse", files={"file": ("note.txt", b"bonjour", "text/plain")}
    )
    assert response.status_code == 415
