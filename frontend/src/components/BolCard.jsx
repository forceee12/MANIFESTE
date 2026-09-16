import { useState } from 'react';

import Field from './Field';
import { bolSummary, formatMoney } from '../utils/format';

/** Un connaissement : en-tête repliable puis formulaire complet. */
export default function BolCard({ bol, index, onChange }) {
  const [open, setOpen] = useState(false);
  const bind = (key) => ({ value: bol[key], onChange: (value) => onChange(index, key, value) });

  return (
    <article className={`bol${open ? ' bol--open' : ''}`}>
      <button type="button" className="bol__head" onClick={() => setOpen(!open)}>
        <span className="bol__n">{bol.line_number}</span>
        <span className="bol__ref">{bol.bol_reference}</span>
        <span className="bol__route">
          {bol.loading_port || '?'} → {bol.unloading_port || '?'}
          {!bol.loading_code && ' (code port à définir)'}
        </span>
        <span className="bol__fig">{bolSummary(bol)}</span>
        <span className="bol__chev">›</span>
      </button>

      {open && (
        <div className="bol__body">
          <h3 className="sub">Identification</h3>
          <div className="grid">
            <Field label="Référence" mono {...bind('bol_reference')} />
            <Field label="Numéro de ligne" type="number" {...bind('line_number')} />
            <Field label="Nature" mono {...bind('bol_nature')} />
            <Field label="Type" mono {...bind('bol_type_code')} />
            <Field label="Code port de chargement" mono hint={bol.loading_port} {...bind('loading_code')} />
            <Field label="Code port de déchargement" mono hint={bol.unloading_port} {...bind('unloading_code')} />
          </div>

          <h3 className="sub">Intervenants</h3>
          <div className="grid">
            <Field label="Expéditeur" {...bind('exporter_name')} />
            <Field label="Adresse expéditeur" type="textarea" {...bind('exporter_address')} />
            <Field label="Destinataire" {...bind('consignee_name')} />
            <Field label="Adresse destinataire" type="textarea" {...bind('consignee_address')} />
            <Field label="Notify" {...bind('notify_name')} />
            <Field label="Adresse notify" type="textarea" {...bind('notify_address')} />
          </div>

          <h3 className="sub">Marchandise</h3>
          <div className="grid">
            <Field label="Nombre de colis" type="number" {...bind('packages')} />
            <Field label="Type de colis" mono {...bind('package_type_code')} />
            <Field label="Poids brut (kg)" type="number" {...bind('gross_mass')} />
            <Field label="Volume (m³)" type="number" {...bind('volume')} />
            <Field label="Conteneurs" type="number" {...bind('containers')} />
            <Field label="Marques" {...bind('shipping_marks')} />
            <Field label="Désignation des marchandises" type="textarea" rows={6} wide {...bind('goods_description')} />
          </div>

          <h3 className="sub">Fret</h3>
          <div className="grid">
            <Field label="Valeur du fret" type="number" {...bind('freight_value')} />
            <Field label="Devise" mono {...bind('freight_currency')} />
            <Field label="Code emplacement" mono {...bind('location_code')} />
            <Field label="Emplacement" {...bind('location_info')} />
          </div>
          <p className="note">
            Manifeste : fret de base {formatMoney(bol.freight_base)} · total avec surcharges{' '}
            {formatMoney(bol.freight_total)}
            {bol.prepaid_at && ` · payable à ${bol.prepaid_at}`} · page(s) {bol.source_pages.join(', ')}
          </p>

          <h3 className="sub">Châssis ({bol.vins.length})</h3>
          {bol.vins.length ? (
            <div className="vins">
              {bol.vins.map((vin) => (
                <div key={vin}>{vin}</div>
              ))}
            </div>
          ) : (
            <p className="note">
              Aucun châssis imprimé sur ces pages. Le XML ne contiendra pas de segment véhicule pour
              ce connaissement.
            </p>
          )}
        </div>
      )}
    </article>
  );
}
