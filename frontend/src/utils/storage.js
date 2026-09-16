/** Persistance locale des options du bureau (aucun serveur impliqué). */

const KEY = 'manifest-xml-options-v1';

export function loadOptions() {
  try {
    const raw = localStorage.getItem(KEY);
    return raw ? JSON.parse(raw) : null;
  } catch {
    return null;
  }
}

export function saveOptions(options) {
  try {
    localStorage.setItem(KEY, JSON.stringify(options));
  } catch {
    /* mode privé ou quota : on continue sans persistance */
  }
}

export function clearOptions() {
  try {
    localStorage.removeItem(KEY);
  } catch {
    /* ignoré */
  }
}
