import { create } from "zustand";

import { api } from "../services/api.js";
import { toast } from "../components/Toast.jsx";

export const useSettingsStore = create((set, get) => ({
  settings: {
    download_directory: null,
    audio_format: "mp3",
    theme: "system",
    log_level: "INFO",
  },
  storage: null,
  loading: false,

  async loadSettings() {
    set({ loading: true });
    try {
      const settings = await window.vidflow.config.get();
      const storage = await api.storage(settings.download_directory);
      set({ settings, storage, loading: false });
    } catch (error) {
      set({ loading: false });
      toast("error", error.message);
    }
  },

  async updateSettings(changes) {
    try {
      const settings = await window.vidflow.config.patch(changes);
      const storage = await api.storage(settings.download_directory);
      set({ settings, storage });
      toast("success", "Ajustes actualizados.");
      return settings;
    } catch (error) {
      toast("error", error.message);
      throw error;
    }
  },

  async chooseDirectory() {
    const result = await window.vidflow.filesystem.selectDirectory();
    if (!result.canceled && result.path) {
      return get().updateSettings({ download_directory: result.path });
    }
    return get().settings;
  },
}));

