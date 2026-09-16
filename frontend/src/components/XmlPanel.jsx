import { useState } from 'react';

/** Aperçu du XML, copie et téléchargement. */
export default function XmlPanel({ xml, fileName, blocked, onDownload }) {
  const [copied, setCopied] = useState(false);

  const copy = async () => {
    try {
      await navigator.clipboard.writeText(xml);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch {
      setCopied(false);
    }
  };

  const size = (new Blob([xml]).size / 1024).toFixed(1);

  return (
    <section className="panel">
      <header className="panel__head">
        <h2>Fichier XML</h2>
        <span className="panel__count">
          {fileName} · {size} Ko
        </span>
        <button className="btn" onClick={copy} disabled={!xml}>
          {copied ? 'Copié' : 'Copier'}
        </button>
        <button className="btn btn--primary" onClick={onDownload} disabled={!xml || blocked}>
          Télécharger
        </button>
      </header>
      <div className="panel__body">
        <pre>{xml}</pre>
      </div>
    </section>
  );
}
