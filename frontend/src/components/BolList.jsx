import { useState } from 'react';

import BolCard from './BolCard';

/** Liste des connaissements du manifeste avec sélection par menu déroulant. */
export default function BolList({ bols, onChange, selectedIndex, onSelect }) {
  return (
    <section className="panel">
      <header className="panel__head">
        <h2>Connaissements</h2>
        <span className="panel__count">{bols.length} connaissements</span>
      </header>
      <div className="panel__body">
        {bols.length > 1 && (
          <div className="dropdown">
            <label htmlFor="bol-select">Connaissement :</label>
            <select
              id="bol-select"
              value={selectedIndex}
              onChange={(e) => onSelect(Number(e.target.value))}
            >
              {bols.map((bol, index) => (
                <option key={`${bol.bol_reference}-${index}`} value={index}>
                  #{bol.line_number} — {bol.bol_reference || 'Sans référence'}
                </option>
              ))}
            </select>
          </div>
        )}
        <div>
          {(bols[selectedIndex] ? [bols[selectedIndex]] : []).map((bol, idx) => (
            <BolCard key={`${bol.bol_reference}-${selectedIndex}-${idx}`} bol={bol} index={selectedIndex} onChange={onChange} />
          ))}
        </div>
      </div>
    </section>
  );
}
