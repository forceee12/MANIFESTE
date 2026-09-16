/** Liste des contrôles avant dépôt. */
export default function ChecksPanel({ issues }) {
  const blocking = issues.filter((i) => i.level === 'error').length;

  return (
    <section className="panel">
      <header className="panel__head">
        <h2>Contrôles avant dépôt</h2>
        <span className="panel__count">
          {blocking ? `${blocking} à corriger` : 'Prêt pour le dépôt'}
        </span>
      </header>
      <div className="panel__body">
        {issues.length === 0 && (
          <div className="check check--ok">
            <b>OK</b>
            <span>Tous les contrôles passent.</span>
          </div>
        )}
        {issues.map((issue, index) => (
          <div key={index} className={`check check--${issue.level}`}>
            <b>{issue.level === 'error' ? 'Bloquant' : 'À vérifier'}</b>
            <span>{issue.message}</span>
          </div>
        ))}
      </div>
    </section>
  );
}
