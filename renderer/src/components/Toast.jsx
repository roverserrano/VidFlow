import { useEffect, useState } from "react";
import { AlertCircle, CheckCircle2, Info, X } from "lucide-react";

const ICONS = {
  success: CheckCircle2,
  error: AlertCircle,
  info: Info,
};

export function toast(level, message) {
  window.dispatchEvent(new CustomEvent("vidflow-toast", { detail: { level, message } }));
}

export function ToastViewport() {
  const [items, setItems] = useState([]);

  useEffect(() => {
    const onToast = (event) => {
      const id = crypto.randomUUID();
      setItems((current) => [...current, { id, ...event.detail }]);
      setTimeout(() => {
        setItems((current) => current.filter((item) => item.id !== id));
      }, 4200);
    };

    window.addEventListener("vidflow-toast", onToast);
    return () => window.removeEventListener("vidflow-toast", onToast);
  }, []);

  return (
    <div className="toast-viewport">
      {items.map((item) => {
        const Icon = ICONS[item.level] || Info;
        return (
          <div className={`toast toast-${item.level || "info"}`} key={item.id}>
            <Icon size={18} />
            <span>{item.message}</span>
            <button
              type="button"
              aria-label="Cerrar"
              onClick={() => setItems((current) => current.filter((entry) => entry.id !== item.id))}
            >
              <X size={16} />
            </button>
          </div>
        );
      })}
    </div>
  );
}

