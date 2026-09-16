import BolList from './components/BolList';
import ChecksPanel from './components/ChecksPanel';
import FileDrop from './components/FileDrop';
import GeneralForm from './components/GeneralForm';
import SettingsPanel from './components/SettingsPanel';
import VoyageStrip from './components/VoyageStrip';
import XmlPanel from './components/XmlPanel';
import { useManifest } from './hooks/useManifest';

export default function App() {
  const manifest = useManifest();
  const { status, model, options } = manifest;

  return (
    <>
      <header className="topbar">
        <div className="topbar__inner">
          <div className="brand">
            <b>Manifeste MOL → XML Sydonia</b>
            <span>{manifest.fileName || 'Aucun manifeste chargé'}</span>
          </div>
          {status === 'ready' && (
            <>
              <button className="btn" onClick={manifest.reset}>
                Charger un autre PDF
              </button>
              <button
                className="btn btn--primary"
                onClick={manifest.download}
                disabled={manifest.blockingCount > 0}
              >
                Télécharger le XML
              </button>
            </>
          )}
        </div>
      </header>

      <main className="wrap">
        {status !== 'ready' && (
          <FileDrop onFile={manifest.parse} status={status} error={manifest.error} />
        )}

        {status === 'ready' && model && (
          <>
            <VoyageStrip model={model} />
            <GeneralForm
              general={model.general}
              source={model.source}
              onChange={manifest.updateGeneral}
            />
            <BolList bols={model.bols} onChange={manifest.updateBol} />
            <ChecksPanel issues={manifest.issues} />
            <XmlPanel
              xml={manifest.xml}
              fileName={manifest.xmlFileName}
              blocked={manifest.blockingCount > 0}
              onDownload={manifest.download}
            />
          </>
        )}

        {options && (
          <SettingsPanel
            options={options}
            onChange={manifest.setOptions}
            onReset={manifest.resetOptions}
          />
        )}
      </main>
    </>
  );
}
