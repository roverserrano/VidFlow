let backendUrlPromise = null;

export async function backendUrl() {
  if (!backendUrlPromise) {
    backendUrlPromise = window.vidflow?.backendUrl
      ? window.vidflow.backendUrl()
      : Promise.resolve("http://127.0.0.1:8716");
  }
  return backendUrlPromise;
}

export async function fetchJson(path, options = {}) {
  const base = await backendUrl();
  const response = await fetch(`${base}${path}`, {
    headers: { "Content-Type": "application/json", ...(options.headers || {}) },
    ...options,
  });
  const data = await response.json();
  if (!response.ok) {
    throw new Error(data?.error?.message || "No se pudo completar la operacion.");
  }
  return data;
}

export async function createDownloadEventSource(jobId) {
  const base = await backendUrl();
  return new EventSource(`${base}/downloads/${jobId}/events`);
}

export const api = {
  health: () => fetchJson("/health"),
  storage: (path) => fetchJson(`/settings/storage${path ? `?path=${encodeURIComponent(path)}` : ""}`),
  history: () => fetchJson("/history"),
  deleteHistory: (id) => fetchJson(`/history/${id}`, { method: "DELETE" }),
};

