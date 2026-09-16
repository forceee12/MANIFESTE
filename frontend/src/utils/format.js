/** Formatage d'affichage, sans effet sur les valeurs envoyées au backend. */

export function formatNumber(value, decimals = 0) {
  if (value === null || value === undefined || value === '') return '—';
  const number = Number(value);
  if (Number.isNaN(number)) return String(value);
  return number.toLocaleString('fr-FR', {
    minimumFractionDigits: decimals,
    maximumFractionDigits: decimals,
  });
}

export function formatVolume(value) {
  return formatNumber(value, 3);
}

export function formatMoney(value, currency = '') {
  if (value === null || value === undefined || value === '') return '—';
  return `${formatNumber(value, 2)}${currency ? ` ${currency}` : ''}`;
}

/** Résumé d'une ligne de connaissement pour l'en-tête repliée. */
export function bolSummary(bol) {
  return `${bol.packages} u · ${formatNumber(bol.gross_mass)} kg · ${formatMoney(
    bol.freight_value,
    bol.freight_currency,
  )}`;
}
