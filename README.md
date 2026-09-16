# Manifeste MOL → XML Sydonia

Convertit un manifeste de chargement MOL (« Cargo Manifest, one BL per page »)
en fichier XML `Awmds` pour Sydonia. Le parsing est déterministe : il repose sur
la géométrie du gabarit Crystal Reports, pas sur de l'OCR.

Backend FastAPI (lecture PDF, mapping, XML, contrôles) + frontend React
(relecture et correction avant export). Le service est sans état : aucun
manifeste n'est stocké.

## Arborescence

```
backend/
  app/
    main.py                     application FastAPI, CORS, montage des routeurs
    core/
      config.py                 réglages (préfixe d'env MANIFEST_)
      reference.py              codes UN/LOCODE et codes pays
    schemas/
      manifest.py               contrat d'échange Pydantic (options, modèle, anomalies)
    services/
      pdf_text.py               PDF -> mots positionnés (pdfplumber)
      layout.py                 bandes de colonnes, regroupement en lignes
      manifest_parser.py        mots -> connaissements bruts
      mapper.py                 connaissements bruts + options -> modèle Sydonia
      xml_builder.py            modèle -> XML Awmds
      validator.py              contrôles bloquants et avertissements
    api/routes/
      manifests.py              /parse, /xml, /xml/download
      reference.py              /options, /ports, /countries
  tests/
    test_pipeline.py            20 tests sur un manifeste réel
    fixtures/                   PDF de référence
  requirements.txt

frontend/
  src/
    main.jsx                    point d'entrée React
    App.jsx                     assemblage des panneaux
    styles.css                  jetons de couleur, thème clair et sombre
    api/client.js               appels HTTP et gestion des erreurs
    hooks/useManifest.js        état unique, actions, régénération du XML
    utils/format.js             formatage d'affichage
    utils/storage.js            persistance locale des options
    components/
      FileDrop.jsx              dépôt du PDF
      VoyageStrip.jsx           bandeau de synthèse
      GeneralForm.jsx           en-tête du manifeste
      BolList.jsx               liste des connaissements
      BolCard.jsx               un connaissement, repliable
      ChecksPanel.jsx           contrôles avant dépôt
      XmlPanel.jsx              aperçu, copie, téléchargement
      SettingsPanel.jsx         constantes du bureau et codes ports
      Field.jsx                 champ de formulaire générique
  vite.config.js                proxy /api vers FastAPI
```

## Démarrage

Backend :

```bash
cd backend
python -m venv .venv && source .venv/bin/activate    # Windows : .venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

Documentation interactive sur <http://127.0.0.1:8000/docs>.

Frontend :

```bash
cd frontend
npm install
npm run dev          # http://localhost:5173
```

Vite relaie `/api` vers `http://127.0.0.1:8000` : aucune configuration CORS
n'est nécessaire en développement. En production, servez `frontend/dist` derrière
le même domaine que l'API, ou renseignez `VITE_API_BASE_URL`.

Tests :

```bash
cd backend && pytest -q
```

## API

| Méthode | Route                          | Rôle                                              |
|---------|--------------------------------|---------------------------------------------------|
| POST    | `/api/manifests/parse`         | PDF (+ options JSON) → modèle éditable + anomalies |
| POST    | `/api/manifests/xml`           | modèle → XML en chaîne, pour l'aperçu              |
| POST    | `/api/manifests/xml/download`  | modèle → XML en pièce jointe (409 si bloquant)     |
| GET     | `/api/reference/options`       | options par défaut du bureau                       |
| GET     | `/api/reference/ports`         | table des codes UN/LOCODE                          |
| GET     | `/api/health`                  | supervision                                        |

Le modèle rendu par `/parse` est renvoyé tel quel à `/xml` : le backend ne
conserve rien entre les deux appels.

## Résultat sur le manifeste de référence

CATTLEYA ACE / 0112A : 10 connaissements, 119 colis, 235 225 kg, 2 080,099 m³,
114 châssis. Le XML produit est identique au fichier déposé manuellement, à
l'exception de la ligne « H.S CODE » conservée dans la désignation.

L'algorithme de lecture est décrit dans `ALGORITHME.md`.

## Pistes d'évolution

* Table `port_codes` en base, administrable, au lieu du dictionnaire en dur.
* Historique des manifestes traités (nécessite une politique de conservation).
* Gabarits d'autres armateurs : les bandes de `layout.py` deviennent alors un
  profil chargé par transporteur.
