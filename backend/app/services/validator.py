"""Contrôles avant dépôt.

Deux niveaux :

* ``error``   : le XML serait rejeté ou incomplet. Le téléchargement est bloqué.
* ``warning`` : cohérence à vérifier par le déclarant, sans blocage.
"""

from __future__ import annotations

from app.schemas.manifest import ManifestModel, ValidationIssue


def validate(model: ManifestModel) -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []
    general = model.general

    if not general.voyage_number:
        issues.append(ValidationIssue(level="error", message="Numéro de voyage introuvable."))
    if not general.date_of_arrival:
        issues.append(ValidationIssue(level="error", message="Date d'arrivée introuvable."))
    if not general.place_of_departure_code:
        issues.append(ValidationIssue(level="error", message="Code du port de départ manquant."))
    if not general.nationality_code:
        issues.append(
            ValidationIssue(level="warning", message=f"Pavillon « {general.place_of_transporter} » non mappé en code pays.")
        )
    if not model.bols:
        issues.append(ValidationIssue(level="error", message="Aucun connaissement dans le manifeste."))

    if model.source.computed_packages != general.total_packages:
        issues.append(
            ValidationIssue(
                level="warning",
                message=(
                    f"Total colis ({general.total_packages}) différent de la somme "
                    f"des connaissements ({model.source.computed_packages})."
                ),
            )
        )
    if abs(model.source.computed_mass - general.total_gross_mass) > 1:
        issues.append(
            ValidationIssue(
                level="warning",
                message=(
                    f"Poids total ({general.total_gross_mass:g}) différent de la somme "
                    f"des connaissements ({model.source.computed_mass:g})."
                ),
            )
        )

    seen: set[str] = set()
    for bol in model.bols:
        prefix = f"B/L {bol.bol_reference} : "
        line = bol.line_number

        if bol.bol_reference in seen:
            issues.append(ValidationIssue(level="error", message=prefix + "référence en double.", bol_line=line))
        seen.add(bol.bol_reference)

        if not bol.loading_code:
            issues.append(
                ValidationIssue(
                    level="error",
                    message=prefix + f"port de chargement « {bol.loading_port} » non mappé.",
                    bol_line=line,
                )
            )
        if not bol.unloading_code:
            issues.append(ValidationIssue(level="error", message=prefix + "port de déchargement non mappé.", bol_line=line))
        if not bol.exporter_name:
            issues.append(ValidationIssue(level="error", message=prefix + "expéditeur manquant.", bol_line=line))
        if not bol.consignee_name:
            issues.append(ValidationIssue(level="error", message=prefix + "destinataire manquant.", bol_line=line))
        if not bol.gross_mass:
            issues.append(ValidationIssue(level="error", message=prefix + "poids brut manquant.", bol_line=line))
        if not bol.packages:
            issues.append(ValidationIssue(level="error", message=prefix + "nombre de colis manquant.", bol_line=line))

        if bol.freight_value is None:
            issues.append(ValidationIssue(level="warning", message=prefix + "valeur de fret non détectée.", bol_line=line))
        if not bol.vins:
            issues.append(
                ValidationIssue(level="warning", message=prefix + "aucun numéro de châssis détecté.", bol_line=line)
            )
        elif len(bol.vins) != bol.packages:
            issues.append(
                ValidationIssue(
                    level="warning",
                    message=prefix + f"{len(bol.vins)} châssis pour {bol.packages} colis.",
                    bol_line=line,
                )
            )

    return issues
