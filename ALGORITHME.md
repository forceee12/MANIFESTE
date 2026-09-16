# Algorithme de lecture du manifeste

Le manifeste MOL est un état Crystal Reports : le texte est vectoriel et la mise
en page est rigoureusement constante (937 × 576 points, un connaissement par
page, débordement sur page suivante). On n'utilise donc ni OCR ni IA — la
position des mots suffit, et le résultat est déterministe et rejouable.

## 1. Extraction — `services/pdf_text.py`

`pdfplumber` rend chaque mot avec son abscisse `x0` et son ordonnée `top`.
Un PDF sans couche texte (scan) lève `NotATextPdf`, transformé en erreur 422.

## 2. Reconstruction des lignes — `services/layout.py`

Les mots sont regroupés par ordonnée avec une tolérance de 5 points. Cette
tolérance n'est pas cosmétique : dans le PDF, un libellé et sa valeur ne
partagent pas toujours la même ordonnée. `CO:` est à 272, `OCEAN TRADE` à 272,
mais `NF:` est à 320 quand `OCEAN TRADE` est à 316. Sans tolérance, le nom se
détache de son libellé. Cinq points restent bien en dessous de l'interligne réel
(environ 12 points), donc deux lignes voisines ne fusionnent jamais.

## 3. Découpage en colonnes — `BANDS`

| Bande      | Abscisses  | Contenu                                        |
|------------|------------|------------------------------------------------|
| `bl`       | 0 – 78     | `MOLU` puis le numéro de connaissement          |
| `party`    | 78 – 262   | blocs `BN:`, `SH:`, `CO:`, `NF:`, `MN:`, `RC:`… |
| `goods`    | 262 – 400  | désignation et numéros de châssis               |
| `wm`       | 395 – 432  | marqueurs `W` (poids) et `M` (volume)           |
| `figure`   | 452 – 552  | valeurs de poids et de volume                   |
| `label`    | 615 – 706  | libellés de surcharges (BUNKER, CURRENCY…)      |
| `prepaid`  | 740 – 852  | montants prépayés                               |
| `collect`  | 852 – …    | montants en port dû                             |

Chaque colonne est reconstruite en lignes indépendamment des autres. C'est ce
qui permet de lire l'adresse de l'expéditeur et la liste des châssis alors
qu'elles se chevauchent verticalement sur la page.

## 4. Lecture de l'en-tête — `_parse_header`

Le bandeau supérieur est éclaté différemment selon les pages : on le lit d'un
seul bloc (toutes les lignes au-dessus de 55 points concaténées) puis on
recherche `n of N` et la date d'édition.

Les valeurs du navire et des ports sont accumulées par bande puis recollées :
`CATTLEYA` et `ACE` sont deux mots dans la même bande, un simple écrasement
donnerait « ACE ».

Une page sans `Port of Loading` est une page de paramètres : elle n'alimente ni
les connaissements, ni les métadonnées du voyage.

## 5. Champs des intervenants

Dans la colonne `party`, une ligne qui commence par `XX:` ouvre un bloc ; les
lignes suivantes indentées le prolongent. Une ligne non préfixée mais alignée
à gauche (abscisse ≤ 96) est du texte libre — typiquement la mention de
transbordement — et va dans un bloc `FREE` qui n'est pas exporté.

Le premier élément d'un bloc devient le nom, le reste devient l'adresse.
`clean_addresses` retire le tiret de continuation que MOL ajoute en fin de ligne
(`ANDRAHARO 101 ANTANANARIVO -`).

## 6. Détection des châssis

Un jeton de 17 caractères alphanumériques contenant au moins une lettre et un
chiffre. Deux pièges traités :

* le châssis coupé par un espace (`JN1HC2E26Z0 060014`) : on recolle uniquement
  si le résultat se termine par six chiffres ;
* le faux positif `MAY 2026 PRODUCTION`, qui fait exactement 17 caractères une
  fois recollé — écarté par la même règle.

`ILIL26133MU0101374` (18 caractères, un numéro de crédit documentaire) est
écarté par la longueur.

## 7. Recollage des pages

Une page portant `* Continued from prev. page *` prolonge le connaissement
courant : ses lignes de marchandise, ses châssis et ses totaux sont ajoutés au
lieu d'ouvrir un nouveau B/L. Le connaissement `MOLU18009181230` occupe ainsi
les pages 2 et 3, avec 21 châssis sur la première et 9 sur la seconde.

## 8. Bande « GRAND TOTAL »

La dernière page porte à la fois la fin d'un connaissement et le grand total du
manifeste. On repère l'ordonnée de `GRAND TOTAL`, puis :

* les lignes dans une bande de ±16 points alimentent les totaux du manifeste ;
* les lignes en dessous (récapitulatif par place de paiement) sont ignorées ;
* tout le reste appartient au connaissement.

Sans cette séparation, le dernier connaissement héritait des 119 colis et des
235 225 kg du manifeste entier.

## 9. Montants

La ligne de taux se reconnaît à la présence de `/M3` (ou `/RT`, `/UNIT`…) : le
montant de sa colonne `prepaid` est le fret de base. La ligne `**TOTAL**` donne
le fret total, surcharges comprises. Les deux sont conservés dans le modèle ;
l'option `freight_mode` décide lequel part dans `<Freight_value>`.

## 10. Points à confirmer avec la douane

Deux valeurs sont reprises du fichier XML de référence sans que leur origine
soit documentée dans le manifeste :

* `place_of_departure_code` = `REPDG` ;
* `date_of_departure` = date d'édition du manifeste, et non date d'appareillage.

Les deux sont des options modifiables (`ParseOptions`), pas des constantes du
code.
