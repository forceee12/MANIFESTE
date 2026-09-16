import { useCallback, useEffect, useRef, useState } from 'react';

import { buildXml, downloadXml, fetchDefaultOptions, parseManifest } from '../api/client';
import { clearOptions, loadOptions, saveOptions } from '../utils/storage';

/**
 * État unique de l'application.
 *
 * Cycle de vie :
 *   idle -> parsing -> ready (édition) -> idle (nouveau fichier)
 *
 * Le modèle est la seule source de vérité. Chaque modification relance, après
 * une temporisation, la génération du XML côté backend : l'aperçu et les
 * contrôles affichés correspondent donc toujours à ce qui sera téléchargé.
 */
export function useManifest() {
  const [status, setStatus] = useState('idle'); // idle | parsing | ready | error
  const [error, setError] = useState(null);
  const [fileName, setFileName] = useState('');
  const [model, setModel] = useState(null);
  const [issues, setIssues] = useState([]);
  const [xml, setXml] = useState('');
  const [xmlFileName, setXmlFileName] = useState('');
  const [options, setOptionsState] = useState(null);

  const lastFile = useRef(null);
  const xmlTimer = useRef(null);

  // Options : préférences locales sinon valeurs par défaut du bureau.
  useEffect(() => {
    const stored = loadOptions();
    if (stored) {
      setOptionsState(stored);
      return;
    }
    fetchDefaultOptions()
      .then(setOptionsState)
      .catch(() => setOptionsState({}));
  }, []);

  const refreshXml = useCallback((nextModel) => {
    clearTimeout(xmlTimer.current);
    xmlTimer.current = setTimeout(() => {
      buildXml(nextModel)
        .then((result) => {
          setXml(result.xml);
          setXmlFileName(result.file_name);
          setIssues(result.issues);
        })
        .catch((err) => setError(err.message));
    }, 300);
  }, []);

  const parse = useCallback(
    async (file) => {
      if (!file) return;
      lastFile.current = file;
      setStatus('parsing');
      setError(null);
      try {
        const result = await parseManifest(file, options);
        setFileName(result.file_name);
        setModel(result.model);
        setIssues(result.issues);
        setStatus('ready');
        refreshXml(result.model);
      } catch (err) {
        setError(err.message);
        setStatus('error');
      }
    },
    [options, refreshXml],
  );

  /** Modifie un champ de l'en-tête. */
  const updateGeneral = useCallback(
    (key, value) => {
      setModel((current) => {
        const next = { ...current, general: { ...current.general, [key]: value } };
        refreshXml(next);
        return next;
      });
    },
    [refreshXml],
  );

  /** Modifie un champ d'un connaissement. */
  const updateBol = useCallback(
    (index, key, value) => {
      setModel((current) => {
        const bols = current.bols.map((bol, i) => (i === index ? { ...bol, [key]: value } : bol));
        const next = { ...current, bols };
        refreshXml(next);
        return next;
      });
    },
    [refreshXml],
  );

  /** Change une option et relit le PDF : les options agissent dès le parsing. */
  const setOptions = useCallback(
    (next) => {
      setOptionsState(next);
      saveOptions(next);
      if (lastFile.current) {
        setStatus('parsing');
        parseManifest(lastFile.current, next)
          .then((result) => {
            setModel(result.model);
            setIssues(result.issues);
            setStatus('ready');
            refreshXml(result.model);
          })
          .catch((err) => {
            setError(err.message);
            setStatus('error');
          });
      }
    },
    [refreshXml],
  );

  const resetOptions = useCallback(async () => {
    clearOptions();
    const defaults = await fetchDefaultOptions();
    setOptions(defaults);
  }, [setOptions]);

  const reset = useCallback(() => {
    lastFile.current = null;
    setStatus('idle');
    setError(null);
    setFileName('');
    setModel(null);
    setIssues([]);
    setXml('');
  }, []);

  const download = useCallback(async () => {
    try {
      return await downloadXml(model);
    } catch (err) {
      setError(err.message);
      return null;
    }
  }, [model]);

  const blockingCount = issues.filter((i) => i.level === 'error').length;

  return {
    status,
    error,
    fileName,
    model,
    issues,
    blockingCount,
    xml,
    xmlFileName,
    options,
    parse,
    updateGeneral,
    updateBol,
    setOptions,
    resetOptions,
    reset,
    download,
  };
}
