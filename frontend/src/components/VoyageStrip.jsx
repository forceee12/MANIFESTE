import { formatNumber, formatVolume } from '../utils/format';

/** Bandeau de synthèse du voyage. */
export default function VoyageStrip({ model }) {
  const { general, bols } = model;
  const volume = bols.reduce((sum, bol) => sum + (Number(bol.volume) || 0), 0);

  const cells = [
    ['Navire', `${general.vessel_name || '—'} / ${general.voyage_number || '—'}`],
    ['Connaissements', general.total_bols],
    ['Colis', formatNumber(general.total_packages)],
    ['Poids brut', `${formatNumber(general.total_gross_mass)} kg`],
    ['Volume', `${formatVolume(volume)} m³`],
    ['Arrivée', general.date_of_arrival || '—'],
  ];

  return (
    <div className="strip">
      {cells.map(([label, value]) => (
        <div key={label}>
          <small>{label}</small>
          <b>{value}</b>
        </div>
      ))}
    </div>
  );
}
