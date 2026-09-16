import Field from './Field';

/** Formulaire de l'en-tête du manifeste (General_segment). */
export default function GeneralForm({ general, source, onChange }) {
  const bind = (key) => ({ value: general[key], onChange: (value) => onChange(key, value) });

  return (
    <section className="panel">
      <header className="panel__head">
        <h2>En-tête du manifeste</h2>
        <span className="panel__count">
          PDF : édition {source.print_date || '—'} · appareillage {source.sail_date || '—'}
        </span>
      </header>
      <div className="panel__body grid">
        <Field label="Bureau de douane" mono {...bind('customs_office')} />
        <Field label="Voyage" mono {...bind('voyage_number')} />
        <Field label="Date de départ" type="date" {...bind('date_of_departure')} />
        <Field label="Date d'arrivée" type="date" {...bind('date_of_arrival')} />
        <Field label="Nombre de connaissements" type="number" {...bind('total_bols')} />
        <Field label="Total colis" type="number" {...bind('total_packages')} />
        <Field label="Total conteneurs" type="number" {...bind('total_containers')} />
        <Field label="Poids brut total (kg)" type="number" {...bind('total_gross_mass')} />
        <Field label="Navire" {...bind('vessel_name')} />
        <Field label="Pavillon" {...bind('place_of_transporter')} />
        <Field label="Code pays du navire" mono {...bind('nationality_code')} />
        <Field label="Mode de transport" mono {...bind('mode_of_transport')} />
        <Field label="Code port de départ" mono {...bind('place_of_departure_code')} />
        <Field label="Code port de destination" mono {...bind('place_of_destination_code')} />
        <Field label="Code transporteur" mono {...bind('carrier_code')} />
        <Field label="Transporteur" {...bind('carrier_name')} />
        <Field label="Adresse du transporteur" type="textarea" rows={2} wide {...bind('carrier_address')} />
      </div>
    </section>
  );
}
