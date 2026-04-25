import { create } from "zustand";

import { toast } from "../components/Toast.jsx";
import { api } from "../services/api.js";

export const useHistoryStore = create((set) => ({
  items: [],
  loading: false,

  async loadHistory() {
    set({ loading: true });
    try {
      const items = await api.history();
      set({ items, loading: false });
    } catch (error) {
      set({ loading: false });
      toast("error", error.message);
    }
  },

  async deleteItem(id) {
    try {
      await api.deleteHistory(id);
      set((state) => ({ items: state.items.filter((item) => item.id !== id) }));
      toast("success", "Elemento eliminado.");
    } catch (error) {
      toast("error", error.message);
    }
  },
}));

