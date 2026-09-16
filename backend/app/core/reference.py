"""Données de référence et valeurs par défaut du bureau de Toamasina.

À terme, ``PORT_CODES`` a vocation à vivre en base (table ``port_codes``) pour
être administrable ; il est ici en dur pour rester sans dépendance.
"""

from __future__ import annotations

PORT_CODES: dict[str, str] = {
    # Madagascar
    "TAMATAVE": "MGTMM", "TOAMASINA": "MGTMM",
    "MAJUNGA": "MGMJN", "MAHAJANGA": "MGMJN",
    "DIEGO SUAREZ": "MGDIE", "ANTSIRANANA": "MGDIE",
    "TULEAR": "MGTLE", "TOLIARA": "MGTLE",
    "EHOALA": "MGEHL", "FORT DAUPHIN": "MGFTU",
    # Japon
    "HIROSHIMA": "JPHIJ", "NAGOYA": "JPNGO", "YOKOHAMA": "JPYOK", "TOKYO": "JPTYO",
    "KOBE": "JPUKB", "KANDA": "JPKND", "OSAKA": "JPOSA", "MOJI": "JPMOJ",
    "YOKKAICHI": "JPYKK",
    # Asie du Sud-Est
    "SINGAPORE": "SGSIN", "PORT KELANG": "MYPKG", "PORT KLANG": "MYPKG",
    "LAEM CHABANG": "THLCH", "BANGKOK": "THBKK", "JAKARTA": "IDJKT",
    "HO CHI MINH": "VNSGN",
    # Chine et Corée
    "SHANGHAI": "CNSHA", "GUANGZHOU": "CNGZG", "NANSHA": "CNNSA", "XIAMEN": "CNXMN",
    "TIANJIN": "CNTSN", "YANTAI": "CNYNT", "LIANYUNGANG": "CNLYG",
    "MASAN": "KRMAS", "PYEONGTAEK": "KRPTK", "ULSAN": "KRUSN",
    "PUSAN": "KRPUS", "BUSAN": "KRPUS",
    # Océan Indien, Afrique, autres
    "PORT LOUIS": "MUPLU", "DURBAN": "ZADUR", "MOMBASA": "KEMBA",
    "DAR ES SALAAM": "TZDAR", "JEBEL ALI": "AEJEA",
    "MUMBAI": "INBOM", "CHENNAI": "INMAA", "KOLKATA": "INCCU",
    "NEW JERSEY": "USNJY",
}

COUNTRY_CODES: dict[str, str] = {
    "JAPAN": "JP", "PANAMA": "PA", "SINGAPORE": "SG", "LIBERIA": "LR",
    "MALTA": "MT", "MARSHALL ISLANDS": "MH", "BAHAMAS": "BS", "HONG KONG": "HK",
    "CYPRUS": "CY", "CHINA": "CN", "KOREA": "KR", "THAILAND": "TH",
    "MADAGASCAR": "MG", "FRANCE": "FR", "ISLE OF MAN": "IM", "PORTUGAL": "PT",
    "ITALY": "IT", "NORWAY": "NO", "GREECE": "GR",
}
