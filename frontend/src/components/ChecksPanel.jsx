import { useState } from 'react';

/** Contrôles avant dépôt avec filtre par menu déroulant. */
export default function ChecksPanel({ issues }) {
  const [filter, setFilter] = useState('all');
  const blocking = issues.filter((i) => i.level === 'error').length;

  const filtered =
    filter === 'error'
      ? issues.filter((i) => i.level === 'error')
      : filter === 'warning'
        ? issues.filter((i) => i.level === 'warning')
        : issues;

  return (
    <section className="panel">
      <header className="panel__head">
        <h2>Contrôles avant dépôt</h2>
        <span className="panel__count">
          {blocking ? `${blocking} à corriger` : 'Prêt pour le dépôt'}
        </span>
      </header>
      <div className="panel__body">
        <div className="dropdown">
          <label htmlFor="issue-filter">Filtrer :</label>
          <select id="issue-filter" value={filter} onChange={(e) => setFilter(e.target.value)}>
            <option value="all">Tous</option>
            <option value="error">Erreurs</option>
            <option value="warning">Avertissements</option>
          </select>
        </div>
        {filtered.length === 0 && (
          <div className="check check--ok">
            <b>OK</b>
            <span>Tous les contrôles passent.</span>
          </div>
        )}
        {filtered.map((issue, index) => (
          <div key={index} className={`check check--${issue.level}`}>
            <b>{issue.level === 'error' ? 'Bloquant' : 'À vérifier'}</b>
            <span>{issue.message}</span>
          </div>
        ))}
      </div>
    </section>
  );
}
