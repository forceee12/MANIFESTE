/**
 * Client HTTP du backend FastAPI.
 * Unique endroit du frontend qui connaît les URL et la forme des erreurs.
 */

const BASE = import.meta.env.VITE_API_BASE_URL || '';

async function readError(response) {
  let detail = `Erreur ${response.status}`;
  try {
    const body = await response.json();
    if (typeof body.detail === 'string') detail = body.detail;
    else if (body.detail?.message) detail = body.detail.message;
  } catch {
    /* réponse non JSON : on garde le message générique */
  }
  const error = new Error(detail);
  error.status = response.status;
  return error;
}

/** Envoie le PDF et récupère le modèle éditable. */
export async function parseManifest(file, options) {
  const form = new FormData();
  form.append('file', file);
  if (options) form.append('options', JSON.stringify(options));

  const response = await fetch(`${BASE}/api/manifests/parse`, { method: 'POST', body: form });
  if (!response.ok) throw await readError(response);
  return response.json();
}

/** Aperçu du XML pour le modèle courant. */
export async function buildXml(model) {
  const response = await fetch(`${BASE}/api/manifests/xml`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ model }),
  });
  if (!response.ok) throw await readError(response);
  return response.json();
}

/** Télécharge le XML. Le backend refuse si un contrôle bloquant échoue. */
export async function downloadXml(model) {
  const response = await fetch(`${BASE}/api/manifests/xml/download`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ model }),
  });
  if (!response.ok) throw await readError(response);

  const disposition = response.headers.get('content-disposition') || '';
  const match = disposition.match(/filename="?([^"]+)"?/);
  const blob = await response.blob();
  const url = URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.href = url;
  link.download = match ? match[1] : 'manifeste.xml';
  document.body.appendChild(link);
  link.click();
  link.remove();
  setTimeout(() => URL.revokeObjectURL(url), 1000);
  return link.download;
}

/** Options par défaut du bureau, servies au démarrage. */
export async function fetchDefaultOptions() {
  const response = await fetch(`${BASE}/api/reference/options`);
  if (!response.ok) throw await readError(response);
  return response.json();
}
