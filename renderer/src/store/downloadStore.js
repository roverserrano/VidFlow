import { create } from "zustand";

import { toast } from "../components/Toast.jsx";
import { createDownloadEventSource } from "../services/api.js";
import { useHistoryStore } from "./historyStore.js";

export const useDownloadStore = create((set, get) => ({
  url: "",
  metadata: null,
  analyzing: false,
  activeJob: null,
  currentProgress: null,
  eventSource: null,

  setUrl(url) {
    set({ url });
  },

  async analyzeUrl(url) {
    const nextUrl = (url || get().url || "").trim();
    if (!nextUrl) {
      toast("error", "Debes pegar una URL.");
      return null;
    }

    set({ analyzing: true, metadata: null, currentProgress: { message: "Analizando URL...", percent: 0 } });
    try {
      const metadata = await window.vidflow.downloads.analyze(nextUrl);
      set({ metadata, url: nextUrl, analyzing: false, currentProgress: { message: "Analisis completado.", percent: null } });
      return metadata;
    } catch (error) {
      set({ analyzing: false, currentProgress: { message: "Error al analizar.", percent: null } });
      toast("error", error.message);
      return null;
    }
  },

  async startDownload(payload) {
    try {
      const job = await window.vidflow.downloads.start(payload);
      set({ activeJob: job, currentProgress: { message: job.message, percent: job.percent } });
      await get().subscribeToProgress(job.job_id);
      return job;
    } catch (error) {
      toast("error", error.message);
      return null;
    }
  },

  async subscribeToProgress(jobId) {
    const previous = get().eventSource;
    if (previous) {
      previous.close();
    }

    const source = await createDownloadEventSource(jobId);
    source.onmessage = (event) => {
      const data = JSON.parse(event.data);
      set({ currentProgress: data, activeJob: { ...(get().activeJob || {}), ...data } });

      if (data.status === "completed") {
        toast("success", "Descarga completada.");
        window.vidflow.notify({ title: "VidFlow", body: "Descarga completada." });
        useHistoryStore.getState().loadHistory();
        source.close();
      }

      if (data.status === "error") {
        toast("error", data.error || data.message);
        source.close();
      }

      if (data.status === "canceled") {
        toast("info", "Descarga cancelada.");
        source.close();
      }
    };
    source.onerror = () => {
      source.close();
    };
    set({ eventSource: source });
  },

  async cancelActiveDownload() {
    const jobId = get().activeJob?.job_id;
    if (!jobId) {
      return;
    }
    await window.vidflow.downloads.cancel(jobId);
  },
}));

