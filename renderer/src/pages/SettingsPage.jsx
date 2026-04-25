import { FolderOpen, HardDrive, MonitorCog, RefreshCcw } from "lucide-react";
import { useEffect, useState } from "react";

import { api } from "../services/api.js";
import { useSettingsStore } from "../store/settingsStore.js";

export function SettingsPage() {
  const { settings, storage, loadSettings, updateSettings, chooseDirectory } = useSettingsStore();
  const [health, setHealth] = useState(null);
  const [appInfo, setAppInfo] = useState(null);

  useEffect(() => {
    loadSettings();
    api.health().then(setHealth).catch(() => setHealth(null));
    window.vidflow.appInfo().then(setAppInfo);
  }, [loadSettings]);

  return (
    <section className="page">
      <header className="page-header">
        <div>
          <p className="eyebrow">Ajustes</p>
          <h1>Preferencias</h1>
        </div>
        <button className="ghost-button" type="button" onClick={loadSettings}>
          <RefreshCcw size={17} />
          Actualizar
        </button>
      </header>

      <section className="settings-grid">
        <div className="panel settings-panel">
          <div className="setting-title">
            <FolderOpen size={20} />
            <strong>Carpeta de destino</strong>
          </div>
          <div className="path-row">
            <input readOnly value={settings.download_directory || ""} />
            <button className="ghost-button compact" type="button" onClick={chooseDirectory}>Cambiar</button>
          </div>
          {storage && (
            <div className="storage-meter">
              <div>
                <HardDrive size={18} />
                <span>{storage.free_text} libres</span>
              </div>
              <div className="progress-bar">
                <span style={{ width: `${storage.total_bytes ? (storage.used_bytes / storage.total_bytes) * 100 : 0}%` }} />
              </div>
            </div>
          )}
        </div>

        <div className="panel settings-panel">
          <div className="setting-title">
            <MonitorCog size={20} />
            <strong>Interfaz</strong>
          </div>
          <label className="select-field">
            <span>Tema</span>
            <select value={settings.theme} onChange={(event) => updateSettings({ theme: event.target.value })}>
              <option value="system">Sistema</option>
              <option value="light">Claro</option>
              <option value="dark">Oscuro</option>
            </select>
          </label>
          <label className="select-field">
            <span>Audio por defecto</span>
            <select value={settings.audio_format} onChange={(event) => updateSettings({ audio_format: event.target.value })}>
              <option value="mp3">MP3</option>
              <option value="m4a">M4A</option>
              <option value="ogg">OGG</option>
            </select>
          </label>
        </div>

        <div className="panel settings-panel dependencies-panel">
          <strong>Aplicacion</strong>
          <dl>
            <div><dt>Version</dt><dd>{appInfo?.version || health?.version || "-"}</dd></div>
            <div><dt>Electron</dt><dd>{appInfo?.platform || "-"}</dd></div>
            <div><dt>yt-dlp</dt><dd>{health?.dependencies?.["yt-dlp"] || "-"}</dd></div>
            <div><dt>ffmpeg</dt><dd>{health?.dependencies?.ffmpeg || "-"}</dd></div>
          </dl>
        </div>
      </section>
    </section>
  );
}

