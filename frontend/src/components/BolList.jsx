import BolCard from './BolCard';

/** Liste des connaissements du manifeste. */
export default function BolList({ bols, onChange }) {
  return (
    <section className="panel">
      <header className="panel__head">
        <h2>Connaissements</h2>
        <span className="panel__count">{bols.length} connaissements</span>
      </header>
      <div>
        {bols.map((bol, index) => (
          <BolCard key={`${bol.bol_reference}-${index}`} bol={bol} index={index} onChange={onChange} />
        ))}
      </div>
    </section>
  );
}
