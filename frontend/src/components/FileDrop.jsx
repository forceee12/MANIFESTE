import { useRef, useState } from 'react';

/** Zone de dépôt du manifeste PDF. */
export default function FileDrop({ onFile, status, error }) {
  const input = useRef(null);
  const [over, setOver] = useState(false);

  const handleFiles = (files) => {
    const file = files?.[0];
    if (file) onFile(file);
  };

  return (
    <div
      className={`drop${over ? ' drop--over' : ''}`}
      onDragEnter={(e) => {
        e.preventDefault();
        setOver(true);
      }}
      onDragOver={(e) => e.preventDefault()}
      onDragLeave={() => setOver(false)}
      onDrop={(e) => {
        e.preventDefault();
        setOver(false);
        handleFiles(e.dataTransfer.files);
      }}
    >
      <h1>Déposez le manifeste PDF</h1>
      <p>
        Le manifeste de chargement MOL est lu page par page, puis converti en fichier XML
        <span className="mono"> Awmds</span> pour Sydonia. Vous relisez et corrigez avant export.
      </p>
      <button className="btn btn--primary" onClick={() => input.current.click()} disabled={status === 'parsing'}>
        {status === 'parsing' ? 'Lecture en cours…' : 'Choisir un fichier'}
      </button>
      <input
        ref={input}
        type="file"
        accept="application/pdf,.pdf"
        hidden
        onChange={(e) => handleFiles(e.target.files)}
      />
      <p className="drop__hint">
        {error || 'PDF texte uniquement — un manifeste scanné ne peut pas être lu.'}
      </p>
    </div>
  );
}
