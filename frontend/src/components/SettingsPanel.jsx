import { useState } from 'react';

import Field from './Field';

/**
 * Paramètres du bureau. Toute modification relance la lecture du PDF, car
 * certaines options (mode de description, choix du fret) agissent au parsing.
 */
export default function SettingsPanel({ options, onChange, onReset }) {
  const [open, setOpen] = useState(false);
  const [newPort, setNewPort] = useState({ name: '', code: '' });

  const set = (key) => (value) => onChange({ ...options, [key]: value });

  const setPort = (name, code) =>
    onChange({ ...options, port_codes: { ...options.port_codes, [name]: code.toUpperCase() } });

  const addPort = () => {
    const name = newPort.name.trim().toUpperCase();
    const code = newPort.code.trim().toUpperCase();
    if (!name || !code) return;
    setPort(name, code);
    setNewPort({ name: '', code: '' });
  };

  return (
    <section className="panel">
      <header className="panel__head">
        <h2>Paramètres</h2>
        <span className="panel__count">Mémorisés sur cet appareil</span>
        <button className="btn btn--ghost" onClick={() => setOpen(!open)}>
          {open ? 'Masquer' : 'Afficher'}
        </button>
      </header>

      {open && (
        <div className="panel__body">
          <div className="grid">
            <Field label="Bureau de douane" mono value={options.customs_office} onChange={set('customs_office')} />
            <Field
              label="Code port de départ"
              mono
              value={options.place_of_departure_code}
              onChange={set('place_of_departure_code')}
            />
            <Field label="Code transporteur" mono value={options.carrier_code} onChange={set('carrier_code')} />
            <Field label="Transporteur" value={options.carrier_name} onChange={set('carrier_name')} />
            <Field
              label="Adresse du transporteur"
              type="textarea"
              rows={2}
              wide
              value={options.carrier_address}
              onChange={set('carrier_address')}
            />
            <Field label="Nature du connaissement" mono value={options.bol_nature} onChange={set('bol_nature')} />
            <Field label="Type de connaissement" mono value={options.bol_type_code} onChange={set('bol_type_code')} />
            <Field label="Type de colis" mono value={options.package_type_code} onChange={set('package_type_code')} />
            <Field label="Code emplacement" mono value={options.location_code} onChange={set('location_code')} />
            <Field label="Emplacement" value={options.location_info} onChange={set('location_info')} />
            <Field label="Marques" value={options.shipping_marks} onChange={set('shipping_marks')} />
            <label className="field" style={{display:'flex',alignItems:'center',gap:8,marginTop:4}}>
              <input
                type="checkbox"
                checked={options.use_nm_for_marks}
                onChange={(e) => onChange({ ...options, use_nm_for_marks: e.target.checked })}
              />
              <span>
                <span className="field__label" style={{margin:0}}>Forcer N/M pour les marques</span>
                <span className="field__hint" style={{margin:0}}>Si activé, ignore les marques du PDF.</span>
              </span>
            </label>
            <Field
              label="Valeur du fret"
              type="select"
              value={options.freight_mode}
              onChange={set('freight_mode')}
              options={[
                ['base', 'Fret de base'],
                ['total', 'Fret total avec surcharges'],
              ]}
            />
            <Field
              label="Date de départ"
              type="select"
              value={options.departure_date_source}
              onChange={set('departure_date_source')}
              options={[
                ['print', "Date d'édition du manifeste"],
                ['sail', "Date d'appareillage"],
              ]}
            />
            <Field
              label="Désignation des marchandises"
              type="select"
              value={options.description_mode}
              onChange={set('description_mode')}
              options={[
                ['compact', 'Intitulé + liste des châssis'],
                ['full', 'Texte intégral du manifeste'],
              ]}
            />
          </div>

          <h3 className="sub">Codes UN/LOCODE des ports</h3>
          <p className="note">
            Un port absent de cette liste bloque la génération du connaissement concerné.
          </p>
          <div className="ports">
            {Object.keys(options.port_codes || {})
              .sort()
              .map((name) => (
                <div key={name} className="ports__row">
                  <span>{name}</span>
                  <input
                    className="mono"
                    value={options.port_codes[name]}
                    onChange={(e) => setPort(name, e.target.value)}
                  />
                </div>
              ))}
          </div>

          <div className="row">
            <input
              placeholder="Nom du port"
              value={newPort.name}
              onChange={(e) => setNewPort({ ...newPort, name: e.target.value })}
            />
            <input
              className="mono"
              placeholder="MGTMM"
              value={newPort.code}
              onChange={(e) => setNewPort({ ...newPort, code: e.target.value })}
            />
            <button className="btn" onClick={addPort}>
              Ajouter le port
            </button>
            <button className="btn btn--ghost" onClick={onReset}>
              Rétablir les valeurs d'origine
            </button>
          </div>
        </div>
      )}
    </section>
  );
}
