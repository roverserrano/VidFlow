import { PanelLeftClose, PanelLeftOpen } from "lucide-react";
import { useState } from "react";

export function Sidebar({ items, active, onNavigate }) {
  const [collapsed, setCollapsed] = useState(false);

  return (
    <aside className={`sidebar ${collapsed ? "is-collapsed" : ""}`}>
      <div className="brand-block">
        <div className="brand-mark">V</div>
        {!collapsed && (
          <div>
            <strong>VidFlow</strong>
            <span>TikTok · Facebook · YouTube</span>
          </div>
        )}
      </div>

      <nav className="sidebar-nav" aria-label="Principal">
        {items.map((item) => {
          const Icon = item.icon;
          return (
            <button
              key={item.id}
              className={`nav-item ${active === item.id ? "is-active" : ""}`}
              type="button"
              title={collapsed ? item.label : undefined}
              onClick={() => onNavigate(item.id)}
            >
              <Icon size={19} />
              {!collapsed && <span>{item.label}</span>}
            </button>
          );
        })}
      </nav>

      <button
        className="sidebar-toggle"
        type="button"
        title={collapsed ? "Expandir" : "Colapsar"}
        onClick={() => setCollapsed((value) => !value)}
      >
        {collapsed ? <PanelLeftOpen size={18} /> : <PanelLeftClose size={18} />}
      </button>
    </aside>
  );
}

