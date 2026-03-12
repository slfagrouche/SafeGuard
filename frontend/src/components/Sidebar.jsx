import React from "react";

export const Sidebar = ({ activeView, onNavigate, onReport }) => {
  const navItems = [
    { id: "map", icon: MapIcon, label: "Map" },
    { id: "ai", icon: AIIcon, label: "AI Hub" },
    { id: "alerts", icon: AlertsIcon, label: "Alerts" },
    { id: "resources", icon: ResourcesIcon, label: "Resources" },
  ];

  return (
    <aside
      data-testid="sidebar"
      className="hidden md:flex flex-col w-[52px] bg-[#111318] border-r border-[rgba(255,255,255,0.08)] h-screen"
    >
      {/* Nav Items */}
      <nav className="flex-1 flex flex-col pt-2">
        {navItems.map((item) => {
          const Icon = item.icon;
          const isActive = activeView === item.id;
          return (
            <button
              key={item.id}
              data-testid={`nav-${item.id}`}
              onClick={() => onNavigate(item.id)}
              className={`
                relative flex items-center justify-center w-full h-12
                transition-colors duration-150
                ${isActive 
                  ? "text-[#00e5ff] bg-[rgba(0,229,255,0.1)]" 
                  : "text-[#6b7280] hover:text-[#9ca3af] hover:bg-[#181c24]"
                }
              `}
              title={item.label}
            >
              {isActive && (
                <div className="absolute left-0 top-1/2 -translate-y-1/2 w-0.5 h-6 bg-[#00e5ff]" />
              )}
              <Icon className="w-5 h-5" />
            </button>
          );
        })}
      </nav>

      {/* Report Button - Pinned to Bottom */}
      <div className="pb-4 space-y-1">
        <a
          href="/admin"
          data-testid="nav-admin"
          className="
            flex items-center justify-center w-full h-12
            text-[#6b7280] hover:text-[#9ca3af] hover:bg-[#181c24]
            transition-colors duration-150
          "
          title="Admin"
        >
          <AdminIcon className="w-5 h-5" />
        </a>
        <button
          data-testid="nav-report"
          onClick={onReport}
          className="
            flex items-center justify-center w-full h-12
            bg-[rgba(255,45,45,0.15)] text-[#ff2d2d]
            hover:bg-[rgba(255,45,45,0.25)] transition-colors duration-150
          "
          title="Report Incident"
        >
          <PlusIcon className="w-5 h-5" />
        </button>
      </div>
    </aside>
  );
};

// Icon Components
const MapIcon = ({ className }) => (
  <svg className={className} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
    <polygon points="1 6 1 22 8 18 16 22 23 18 23 2 16 6 8 2 1 6" />
    <line x1="8" y1="2" x2="8" y2="18" />
    <line x1="16" y1="6" x2="16" y2="22" />
  </svg>
);

const AIIcon = ({ className }) => (
  <svg className={className} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
    <polygon points="12 2 22 8.5 22 15.5 12 22 2 15.5 2 8.5 12 2" />
    <line x1="12" y1="22" x2="12" y2="15.5" />
    <polyline points="22 8.5 12 15.5 2 8.5" />
  </svg>
);

const AlertsIcon = ({ className }) => (
  <svg className={className} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
    <path d="M4 15s1-1 4-1 5 2 8 2 4-1 4-1V3s-1 1-4 1-5-2-8-2-4 1-4 1z" />
    <line x1="4" y1="22" x2="4" y2="15" />
  </svg>
);

const ResourcesIcon = ({ className }) => (
  <svg className={className} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
    <line x1="3" y1="6" x2="21" y2="6" />
    <line x1="3" y1="12" x2="21" y2="12" />
    <line x1="3" y1="18" x2="21" y2="18" />
  </svg>
);

const PlusIcon = ({ className }) => (
  <svg className={className} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
    <line x1="12" y1="5" x2="12" y2="19" />
    <line x1="5" y1="12" x2="19" y2="12" />
  </svg>
);

const AdminIcon = ({ className }) => (
  <svg className={className} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
    <path d="M12 15a3 3 0 1 0 0-6 3 3 0 0 0 0 6z" />
    <path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1-2.83 2.83l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-4 0v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83-2.83l.06-.06A1.65 1.65 0 0 0 4.68 15a1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1 0-4h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 2.83-2.83l.06.06A1.65 1.65 0 0 0 9 4.68a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 4 0v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 2.83l-.06.06A1.65 1.65 0 0 0 19.4 9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 0 4h-.09a1.65 1.65 0 0 0-1.51 1z" />
  </svg>
);
