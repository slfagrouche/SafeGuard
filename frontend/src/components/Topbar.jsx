import React from "react";

export const Topbar = ({ viewName, criticalCount, highCount }) => {
  return (
    <header
      data-testid="topbar"
      className="h-[38px] bg-[#111318] border-b border-[rgba(255,255,255,0.08)] flex items-center justify-between px-4"
    >
      {/* View Name */}
      <h1
        data-testid="topbar-title"
        className="text-xs font-medium tracking-wider text-[#9ca3af] uppercase"
        style={{ fontFamily: "'IBM Plex Mono', monospace" }}
      >
        {viewName === "MAP" ? "INCIDENT MAP" : viewName.replace("_", " ")}
      </h1>

      {/* Live Counts */}
      <div className="flex items-center gap-4 text-xs" style={{ fontFamily: "'IBM Plex Mono', monospace" }}>
        {criticalCount > 0 && (
          <div
            data-testid="critical-count"
            className="flex items-center gap-1.5 text-[#ff2d2d]"
          >
            <span className="w-2 h-2 rounded-full bg-[#ff2d2d] animate-critical-pulse" />
            <span>{criticalCount} CRITICAL</span>
          </div>
        )}
        {highCount > 0 && (
          <div
            data-testid="high-count"
            className="flex items-center gap-1.5 text-[#ffb800]"
          >
            <span className="w-2 h-2 rounded-full bg-[#ffb800]" />
            <span>{highCount} HIGH</span>
          </div>
        )}
      </div>
    </header>
  );
};
