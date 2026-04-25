import { useEffect, useState } from "react";
import { Download, History, Settings } from "lucide-react";

import { Sidebar } from "../components/Sidebar.jsx";
import { StatusBar } from "../components/StatusBar.jsx";
import { ToastViewport } from "../components/Toast.jsx";
import { DownloadPage } from "../pages/DownloadPage.jsx";
import { HistoryPage } from "../pages/HistoryPage.jsx";
import { SettingsPage } from "../pages/SettingsPage.jsx";
import { useDownloadStore } from "../store/downloadStore.js";
import { useSettingsStore } from "../store/settingsStore.js";

const NAV_ITEMS = [
  { id: "download", label: "Descarga", icon: Download },
  { id: "history", label: "Historial", icon: History },
  { id: "settings", label: "Ajustes", icon: Settings },
];

export function App() {
  const [activePage, setActivePage] = useState("download");
  const { settings, loadSettings } = useSettingsStore();
  const currentProgress = useDownloadStore((state) => state.currentProgress);

  useEffect(() => {
    loadSettings();
  }, [loadSettings]);

  useEffect(() => {
    document.documentElement.dataset.theme = settings.theme || "system";
  }, [settings.theme]);

  const statusText = currentProgress?.message || "Listo";
  const progress = currentProgress?.percent ?? null;

  return (
    <div className="app-shell">
      <Sidebar items={NAV_ITEMS} active={activePage} onNavigate={setActivePage} />
      <main className="workspace">
        {activePage === "download" && <DownloadPage />}
        {activePage === "history" && <HistoryPage />}
        {activePage === "settings" && <SettingsPage />}
      </main>
      <StatusBar status={statusText} progress={progress} />
      <ToastViewport />
    </div>
  );
}

