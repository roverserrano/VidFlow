import { Clipboard, Download, FileAudio, FileVideo, Globe2, Loader2, RotateCcw, X } from "lucide-react";
import { useMemo, useState } from "react";

import { EmptyState } from "../components/EmptyState.jsx";
import { ProgressBar } from "../components/ProgressBar.jsx";
import { toast } from "../components/Toast.jsx";
import { useDownloadStore } from "../store/downloadStore.js";
import { useSettingsStore } from "../store/settingsStore.js";

const PLATFORM_LABELS = {
  youtube: "YouTube",
  tiktok: "TikTok",
  facebook: "Facebook",
};

export function DownloadPage() {
  const {
    url,
    setUrl,
    metadata,
    analyzing,
    currentProgress,
    activeJob,
    analyzeUrl,
    startDownload,
    cancelActiveDownload,
  } = useDownloadStore();
  const { settings, chooseDirectory } = useSettingsStore();
  const [downloadType, setDownloadType] = useState("video");
  const [selectedFormat, setSelectedFormat] = useState("");

  const firstFormat = metadata?.formats?.[0];
  const formatSelector = selectedFormat || firstFormat?.selector || null;
  const selectedFormatObject = useMemo(
    () => metadata?.formats?.find((item) => item.selector === formatSelector) || firstFormat,
    [metadata, formatSelector, firstFormat],
  );

  async function pasteAndAnalyze() {
    try {
      const text = await navigator.clipboard.readText();
      setUrl(text);
      await analyzeUrl(text);
    } catch {
      toast("error", "No se pudo leer el portapapeles.");
    }
  }

  async function handleAnalyze() {
    await analyzeUrl(url);
  }

  async function ensureDirectory() {
    if (settings.download_directory) {
      return settings.download_directory;
    }
    const nextSettings = await chooseDirectory();
    return nextSettings.download_directory;
  }

  async function handleDownload() {
    if (!metadata) {
      return;
    }

    const outputDir = await ensureDirectory();
    if (!outputDir) {
      toast("error", "Debes seleccionar una carpeta de destino.");
      return;
    }

    await startDownload({
      url: metadata.webpage_url,
      title: metadata.title,
      platform: metadata.platform,
      thumbnail: metadata.thumbnail || "",
      download_type: downloadType,
      format_selector: downloadType === "video" ? formatSelector : null,
      resolution: downloadType === "video" ? selectedFormatObject?.resolution : "audio",
      audio_format: settings.audio_format || "mp3",
      output_dir: outputDir,
    });
  }

  const isRunning = ["queued", "preparing", "downloading", "processing"].includes(currentProgress?.status);
  const isFailed = currentProgress?.status === "error";

  return (
    <section className="page page-download">
      <header className="page-header">
        <div>
          <p className="eyebrow">Descarga</p>
          <h1>Nuevo archivo</h1>
        </div>
        <button className="ghost-button" type="button" onClick={pasteAndAnalyze} disabled={analyzing}>
          <Clipboard size={18} />
          Pegar y analizar
        </button>
      </header>

      <div className="download-grid">
        <section className="panel download-input-panel">
          <label className="field-label" htmlFor="url-input">URL</label>
          <div className="url-row">
            <input
              id="url-input"
              className="url-input"
              value={url}
              placeholder="https://..."
              onChange={(event) => setUrl(event.target.value)}
              onKeyDown={(event) => {
                if (event.key === "Enter") {
                  handleAnalyze();
                }
              }}
            />
            <button className="primary-button" type="button" onClick={handleAnalyze} disabled={analyzing}>
              {analyzing ? <Loader2 className="spin" size={18} /> : <Globe2 size={18} />}
              Analizar
            </button>
          </div>

          {metadata ? (
            <div className="metadata-layout">
              <div className="thumbnail-frame">
                {metadata.thumbnail ? <img src={metadata.thumbnail} alt="" /> : <FileVideo size={42} />}
              </div>
              <div className="metadata-copy">
                <span className="platform-pill">{PLATFORM_LABELS[metadata.platform] || metadata.platform}</span>
                <h2>{metadata.title}</h2>
                <p>{metadata.duration_text}</p>
              </div>
            </div>
          ) : (
            <EmptyState title="Esperando URL">Pega un enlace publico para analizarlo.</EmptyState>
          )}
        </section>

        <section className="panel options-panel">
          <div className="segmented-control" role="tablist" aria-label="Formato">
            <button
              type="button"
              className={downloadType === "video" ? "is-active" : ""}
              onClick={() => setDownloadType("video")}
            >
              <FileVideo size={18} />
              Video
            </button>
            <button
              type="button"
              className={downloadType === "audio" ? "is-active" : ""}
              onClick={() => setDownloadType("audio")}
            >
              <FileAudio size={18} />
              Audio
            </button>
          </div>

          {downloadType === "video" && (
            <label className="select-field">
              <span>Calidad</span>
              <select
                value={formatSelector || ""}
                onChange={(event) => setSelectedFormat(event.target.value)}
                disabled={!metadata?.formats?.length}
              >
                {(metadata?.formats || []).map((format) => (
                  <option key={format.id} value={format.selector}>
                    {format.label} · {format.filesize_text}
                  </option>
                ))}
              </select>
            </label>
          )}

          {downloadType === "audio" && (
            <div className="audio-format">
              <span>Formato</span>
              <strong>{(settings.audio_format || "mp3").toUpperCase()}</strong>
            </div>
          )}

          <button className="download-button" type="button" onClick={handleDownload} disabled={!metadata || isRunning}>
            <Download size={20} />
            Descargar
          </button>
        </section>
      </div>

      <section className="panel progress-panel">
        <div className="progress-header">
          <div>
            <span>Estado</span>
            <strong>{currentProgress?.message || "Listo"}</strong>
          </div>
          {isRunning && (
            <button className="icon-button" type="button" title="Cancelar" onClick={cancelActiveDownload}>
              <X size={18} />
            </button>
          )}
          {isFailed && (
            <button className="ghost-button compact" type="button" onClick={handleDownload}>
              <RotateCcw size={16} />
              Reintentar
            </button>
          )}
        </div>
        <ProgressBar value={currentProgress?.percent} />
        <div className="progress-meta">
          <span>{currentProgress?.percent != null ? `${currentProgress.percent.toFixed(1)}%` : "-"}</span>
          <span>{currentProgress?.speed || "-"}</span>
          <span>{currentProgress?.eta || "-"}</span>
        </div>
        {activeJob?.file_path && <button className="link-button" type="button" onClick={() => window.vidflow.filesystem.showItem(activeJob.file_path)}>Mostrar archivo</button>}
      </section>
    </section>
  );
}
