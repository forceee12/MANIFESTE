/** Champ de formulaire générique : libellé + contrôle contrôlé. */
export default function Field({
  label,
  value,
  onChange,
  type = 'text',
  rows,
  wide = false,
  mono = false,
  options,
  hint,
}) {
  const className = `field${wide ? ' field--wide' : ''}${mono ? ' field--mono' : ''}`;
  const current = value ?? '';

  return (
    <label className={className}>
      <span className="field__label">{label}</span>
      {type === 'textarea' && (
        <textarea rows={rows || 3} value={current} onChange={(e) => onChange(e.target.value)} />
      )}
      {type === 'select' && (
        <select value={current} onChange={(e) => onChange(e.target.value)}>
          {options.map(([key, text]) => (
            <option key={key} value={key}>
              {text}
            </option>
          ))}
        </select>
      )}
      {type !== 'textarea' && type !== 'select' && (
        <input type={type} value={current} onChange={(e) => onChange(e.target.value)} />
      )}
      {hint && <span className="field__hint">{hint}</span>}
    </label>
  );
}
