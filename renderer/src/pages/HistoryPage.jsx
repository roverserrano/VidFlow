import { Calendar, ExternalLink, FolderOpen, Search, Trash2 } from "lucide-react";
import { useEffect, useMemo, useState } from "react";

import { EmptyState } from "../components/EmptyState.jsx";
import { useHistoryStore } from "../store/historyStore.js";

export function HistoryPage() {
  const { items, loadHistory, deleteItem } = useHistoryStore();
  const [query, setQuery] = useState("");
  const [platform, setPlatform] = useState("all");
  const [format, setFormat] = useState("all");

  useEffect(() => {
    loadHistory();
  }, [loadHistory]);

  const filtered = useMemo(() => {
    return items.filter((item) => {
      const matchesQuery = item.title?.toLowerCase().includes(query.toLowerCase());
      const matchesPlatform = platform === "all" || item.platform === platform;
      const matchesFormat = format === "all" || item.download_type === format;
      return matchesQuery && matchesPlatform && matchesFormat;
    });
  }, [items, query, platform, format]);

  return (
    <section className="page">
      <header className="page-header">
        <div>
          <p className="eyebrow">Historial</p>
          <h1>Descargas</h1>
        </div>
      </header>

      <div className="toolbar">
        <label className="search-field">
          <Search size={18} />
          <input value={query} placeholder="Buscar" onChange={(event) => setQuery(event.target.value)} />
        </label>
        <select value={platform} onChange={(event) => setPlatform(event.target.value)}>
          <option value="all">Todas</option>
          <option value="youtube">YouTube</option>
          <option value="tiktok">TikTok</option>
          <option value="facebook">Facebook</option>
        </select>
        <select value={format} onChange={(event) => setFormat(event.target.value)}>
          <option value="all">Video y audio</option>
          <option value="video">Video</option>
          <option value="audio">Audio</option>
        </select>
      </div>

      <section className="history-list">
        {filtered.length === 0 && <EmptyState title="Sin resultados">Las descargas completadas apareceran aqui.</EmptyState>}
        {filtered.map((item) => (
          <article className="history-item" key={item.id}>
            <div className="history-thumb">{item.thumbnail ? <img src={item.thumbnail} alt="" /> : <Calendar size={22} />}</div>
            <div className="history-copy">
              <strong>{item.title}</strong>
              <span>{item.platform} · {item.download_type} · {item.format?.toUpperCase()} · {item.created_at}</span>
            </div>
            <div className="history-actions">
              <button type="button" title="Abrir archivo" onClick={() => window.vidflow.filesystem.openPath(item.file_path)}>
                <ExternalLink size={17} />
              </button>
              <button type="button" title="Abrir carpeta" onClick={() => window.vidflow.filesystem.showItem(item.file_path)}>
                <FolderOpen size={17} />
              </button>
              <button type="button" title="Eliminar" onClick={() => deleteItem(item.id)}>
                <Trash2 size={17} />
              </button>
            </div>
          </article>
        ))}
      </section>
    </section>
  );
}

