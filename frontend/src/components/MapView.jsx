import React, { useState, useEffect, useRef, useCallback } from "react";
import { MapContainer, TileLayer, Marker, Popup, useMap } from "react-leaflet";
import MarkerClusterGroup from "react-leaflet-cluster";
import L from "leaflet";
import "leaflet/dist/leaflet.css";
import axios from "axios";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { toast } from "sonner";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

// Fix default marker icons
delete L.Icon.Default.prototype._getIconUrl;
L.Icon.Default.mergeOptions({
  iconRetinaUrl: "https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/images/marker-icon-2x.png",
  iconUrl: "https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/images/marker-icon.png",
  shadowUrl: "https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/images/marker-shadow.png",
});

const createMarkerIcon = (severity) => {
  const sizes = { critical: 16, high: 12, medium: 10, low: 8 };
  const colors = { critical: "#ff2d2d", high: "#ffb800", medium: "#3b82f6", low: "#00d26a" };
  const size = sizes[severity] || 10;
  const color = colors[severity] || "#3b82f6";
  const glow = severity === "critical" ? `box-shadow: 0 0 12px 4px rgba(255,45,45,0.5);` : severity === "high" ? `box-shadow: 0 0 8px 2px rgba(255,184,0,0.3);` : "";

  return L.divIcon({
    className: `incident-marker ${severity}`,
    html: `<div style="width:${size}px;height:${size}px;background-color:${color};border-radius:50%;${glow}${severity === 'critical' ? 'animation:critical-pulse 2s ease-in-out infinite;' : ''}"></div>`,
    iconSize: [size, size],
    iconAnchor: [size / 2, size / 2],
  });
};

// Custom cluster icon
const createClusterIcon = (cluster) => {
  const markers = cluster.getAllChildMarkers();
  const count = markers.length;
  const hasCritical = markers.some(m => m.options.severity === "critical");
  const hasHigh = markers.some(m => m.options.severity === "high");
  const borderColor = hasCritical ? "#ff2d2d" : hasHigh ? "#ffb800" : "#3b82f6";
  const glow = hasCritical ? "box-shadow: 0 0 12px rgba(255,45,45,0.5);" : "";
  
  return L.divIcon({
    html: `<div style="display:flex;align-items:center;justify-content:center;width:36px;height:36px;border-radius:50%;background:#111318;border:2px solid ${borderColor};color:#f0f0f0;font-family:'IBM Plex Mono',monospace;font-size:11px;font-weight:500;${glow}">${count}</div>`,
    className: "marker-cluster-custom",
    iconSize: L.point(36, 36),
  });
};

// Map controller component
const MapController = ({ center, zoom, filters }) => {
  const map = useMap();
  useEffect(() => {
    if (center && zoom) {
      map.setView(center, zoom, { animate: true });
    } else if (center) {
      map.setView(center, map.getZoom());
    }
  }, [center, zoom, map]);
  return null;
};

export const MapView = ({ incidents, onRefresh, onReport }) => {
  const [selectedIncident, setSelectedIncident] = useState(null);
  const [expandedIncident, setExpandedIncident] = useState(null);
  const [filters, setFilters] = useState({ critical: true, high: true, medium: true, low: true, verified: "all" });
  const [showFilters, setShowFilters] = useState(false);
  const [mapCenter, setMapCenter] = useState([20, 0]);
  const [mapZoom, setMapZoom] = useState(null);
  
  // Map Intelligence state
  const [showMapChat, setShowMapChat] = useState(false);
  const [mapChatInput, setMapChatInput] = useState("");
  const [mapChatMessages, setMapChatMessages] = useState([]);
  const [isMapChatLoading, setIsMapChatLoading] = useState(false);
  const [flaggingIncidentId, setFlaggingIncidentId] = useState(null);
  const mapChatEndRef = useRef(null);

  const filteredIncidents = incidents.filter((incident) => {
    if (!filters[incident.severity]) return false;
    if (filters.verified !== "all" && incident.verification_status !== filters.verified) return false;
    return true;
  });

  const formatTime = (dateString) => {
    const date = new Date(dateString);
    const now = new Date();
    const diff = now - date;
    const hours = Math.floor(diff / (1000 * 60 * 60));
    if (hours < 1) return "< 1h ago";
    if (hours < 24) return `${hours}h ago`;
    return `${Math.floor(hours / 24)}d ago`;
  };

  const handleIncidentClick = (incident) => {
    setSelectedIncident(incident);
    setExpandedIncident(incident.id);
    setMapCenter([incident.lat, incident.lng]);
  };

  const severityColors = { critical: "bg-[#ff2d2d]", high: "bg-[#ffb800]", medium: "bg-[#3b82f6]", low: "bg-[#00d26a]" };

  const verificationBadge = (status) => {
    if (status === "verified") return <span className="text-[10px] text-[#00d26a]">VERIFIED</span>;
    if (status === "flagged") return <span className="text-[10px] text-[#ff2d2d]">FLAGGED</span>;
    return <span className="text-[10px] text-[#6b7280]">UNVERIFIED</span>;
  };

  const handleFlagIncident = async (incidentId) => {
    const reasonRaw = window.prompt(
      "Select reason: inaccurate | duplicate | spam | outdated",
      "inaccurate"
    );
    if (reasonRaw === null) return;

    const reason = String(reasonRaw).trim().toLowerCase();
    const validReasons = ["inaccurate", "duplicate", "spam", "outdated"];
    if (!validReasons.includes(reason)) {
      toast.error("Invalid reason. Use: inaccurate, duplicate, spam, or outdated.");
      return;
    }

    setFlaggingIncidentId(incidentId);
    try {
      const res = await axios.post(`${API}/incidents/${incidentId}/flag/`, { reason });
      const count = res?.data?.flag_count;
      toast.success(
        count != null
          ? `Incident flagged. Total flags: ${count}`
          : "Incident flagged successfully."
      );
      if (onRefresh) await onRefresh();
    } catch (e) {
      const msg = e?.response?.data?.error || e?.response?.data?.message;
      toast.error(msg || "Failed to flag incident.");
    } finally {
      setFlaggingIncidentId(null);
    }
  };

  // Map Intelligence Chat
  const handleMapChatSend = async () => {
    if (!mapChatInput.trim() || isMapChatLoading) return;
    const msg = mapChatInput.trim();
    setMapChatInput("");
    setMapChatMessages(prev => [...prev, { role: "user", content: msg }]);
    setIsMapChatLoading(true);

    try {
      const res = await axios.post(`${API}/ai/chat/`, { agent_type: "map_intelligence", message: msg });
      const taskId = res.data.task_id;
      
      // Poll for response
      const poll = async () => {
        for (let i = 0; i < 30; i++) {
          await new Promise(r => setTimeout(r, 2000));
          const statusRes = await axios.get(`${API}/ai/status/${taskId}/`);
          if (statusRes.status === 200 && statusRes.data.status === "success") {
            const content = statusRes.data.content;
            setMapChatMessages(prev => [...prev, { role: "assistant", content }]);
            
            // Parse JSON commands from response
            const jsonMatch = content.match(/```json\s*([\s\S]*?)\s*```/);
            if (jsonMatch) {
              try {
                const command = JSON.parse(jsonMatch[1]);
                executeMapCommand(command);
              } catch (e) {
                console.error("Failed to parse map command:", e);
              }
            }
            return;
          } else if (statusRes.data.status === "error") {
            setMapChatMessages(prev => [...prev, { role: "assistant", content: statusRes.data.message || "Error processing request." }]);
            return;
          }
        }
        setMapChatMessages(prev => [...prev, { role: "assistant", content: "Request timed out." }]);
      };
      
      await poll();
    } catch (e) {
      setMapChatMessages(prev => [...prev, { role: "assistant", content: "Failed to send request." }]);
    } finally {
      setIsMapChatLoading(false);
    }
  };

  const executeMapCommand = (command) => {
    if (!command || !command.action) return;
    
    switch (command.action) {
      case "filter":
        if (command.params?.severity) {
          const newFilters = { critical: false, high: false, medium: false, low: false, verified: filters.verified };
          command.params.severity.forEach(s => { newFilters[s] = true; });
          setFilters(newFilters);
        }
        if (command.params?.verified !== undefined) {
          setFilters(prev => ({ ...prev, verified: command.params.verified ? "verified" : "all" }));
        }
        break;
      case "zoom":
        if (command.params?.lat && command.params?.lng) {
          setMapCenter([command.params.lat, command.params.lng]);
          setMapZoom(command.params.zoom || 13);
        }
        break;
      case "reset":
        setFilters({ critical: true, high: true, medium: true, low: true, verified: "all" });
        setMapCenter([20, 0]);
        setMapZoom(2);
        break;
      default:
        break;
    }
  };

  useEffect(() => {
    mapChatEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [mapChatMessages]);

  return (
    <div className="relative h-full w-full" data-testid="map-view">
      {/* Map */}
      <MapContainer center={mapCenter} zoom={2} className="absolute inset-0 z-0" zoomControl={true} style={{ background: "#0a0c10" }}>
        <TileLayer attribution='&copy; <a href="https://carto.com/">CARTO</a>' url="https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png" />
        <MapController center={mapCenter} zoom={mapZoom} />
        
        <MarkerClusterGroup
          chunkedLoading
          iconCreateFunction={createClusterIcon}
          maxClusterRadius={50}
          spiderfyOnMaxZoom={true}
          showCoverageOnHover={false}
        >
          {filteredIncidents.map((incident) => (
            <Marker
              key={incident.id}
              position={[incident.lat, incident.lng]}
              icon={createMarkerIcon(incident.severity)}
              severity={incident.severity}
              eventHandlers={{ click: () => handleIncidentClick(incident) }}
            >
              <Popup>
                <div className="p-3 min-w-[200px]">
                  <div className="flex items-center gap-2 mb-2">
                    <span className={`w-3 h-3 rounded-full ${severityColors[incident.severity]}`} />
                    <span className="text-xs font-medium uppercase text-[#f0f0f0]">{incident.severity}</span>
                    {verificationBadge(incident.verification_status)}
                  </div>
                  <p className="text-sm text-[#f0f0f0] mb-2">{incident.description}</p>
                  <p className="text-xs text-[#6b7280]">{formatTime(incident.datetime)}</p>
                </div>
              </Popup>
            </Marker>
          ))}
        </MarkerClusterGroup>
      </MapContainer>

      {/* Filter Toggle */}
      <button data-testid="filter-toggle" onClick={() => setShowFilters(!showFilters)}
        className="absolute top-3 right-[296px] z-20 p-2 bg-[#111318] border border-[rgba(255,255,255,0.08)] rounded hover:bg-[#181c24] transition-colors md:right-[296px] right-3">
        <svg className="w-5 h-5 text-[#9ca3af]" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
          <polygon points="22 3 2 3 10 12.46 10 19 14 21 14 12.46 22 3" />
        </svg>
      </button>

      {/* Map Intelligence Toggle */}
      <button data-testid="map-intel-toggle" onClick={() => setShowMapChat(!showMapChat)}
        className={`absolute top-3 z-20 p-2 bg-[#111318] border border-[rgba(255,255,255,0.08)] rounded hover:bg-[#181c24] transition-colors ${showMapChat ? "text-[#00e5ff] border-[#00e5ff]" : "text-[#9ca3af]"}`}
        style={{ right: showFilters ? "calc(280px + 240px + 12px)" : "calc(280px + 48px)" }}
        title="Map Intelligence">
        <svg className="w-5 h-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
          <polygon points="12 2 22 8.5 22 15.5 12 22 2 15.5 2 8.5 12 2" />
          <line x1="12" y1="22" x2="12" y2="15.5" />
          <polyline points="22 8.5 12 15.5 2 8.5" />
        </svg>
      </button>

      {/* Filter Panel */}
      {showFilters && (
        <div data-testid="filter-panel"
          className="absolute top-14 right-[296px] z-20 p-3 bg-[#111318] border border-[rgba(255,255,255,0.08)] rounded-md w-56 md:right-[296px] right-3">
          <p className="text-xs text-[#9ca3af] mb-3 uppercase tracking-wider">Severity</p>
          <div className="space-y-2 mb-4">
            {["critical", "high", "medium", "low"].map((severity) => (
              <label key={severity} className="flex items-center gap-2 cursor-pointer">
                <input type="checkbox" checked={filters[severity]}
                  onChange={(e) => setFilters({ ...filters, [severity]: e.target.checked })}
                  className="w-4 h-4 rounded border-[rgba(255,255,255,0.16)] bg-[#181c24]" />
                <span className={`w-2 h-2 rounded-full ${severityColors[severity]}`} />
                <span className="text-xs text-[#f0f0f0] uppercase">{severity}</span>
              </label>
            ))}
          </div>
          <p className="text-xs text-[#9ca3af] mb-2 uppercase tracking-wider">Verification</p>
          <select value={filters.verified} onChange={(e) => setFilters({ ...filters, verified: e.target.value })}
            className="w-full px-2 py-1.5 text-xs bg-[#181c24] border border-[rgba(255,255,255,0.08)] rounded text-[#f0f0f0] focus:outline-none focus:border-[#00e5ff]">
            <option value="all">All</option>
            <option value="verified">Verified only</option>
            <option value="unverified">Unverified</option>
            <option value="flagged">Flagged</option>
          </select>
        </div>
      )}

      {/* Map Intelligence Chat Panel */}
      {showMapChat && (
        <div data-testid="map-intel-panel"
          className="absolute top-14 z-20 bg-[#111318] border border-[rgba(255,255,255,0.08)] rounded-md w-80 flex flex-col"
          style={{ right: "calc(280px + 48px)", maxHeight: "60vh" }}>
          <div className="p-3 border-b border-[rgba(255,255,255,0.08)] flex items-center gap-2">
            <svg className="w-4 h-4 text-[#00e5ff]" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <polygon points="12 2 22 8.5 22 15.5 12 22 2 15.5 2 8.5 12 2" />
            </svg>
            <span className="text-xs font-medium text-[#00e5ff] uppercase tracking-wider">Map Intelligence</span>
          </div>
          
          <ScrollArea className="flex-1 p-3 max-h-[40vh]">
            <div className="space-y-3">
              {mapChatMessages.length === 0 && (
                <div className="text-center py-4">
                  <p className="text-xs text-[#6b7280]">Ask about the map</p>
                  <div className="mt-3 space-y-1">
                    {["Show critical incidents", "Zoom to Khartoum", "Reset filters"].map((q) => (
                      <button key={q} onClick={() => { setMapChatInput(q); }}
                        className="block w-full text-left text-[10px] text-[#9ca3af] hover:text-[#00e5ff] p-1.5 rounded hover:bg-[#181c24]">
                        "{q}"
                      </button>
                    ))}
                  </div>
                </div>
              )}
              {mapChatMessages.map((msg, i) => (
                <div key={i} className={`${msg.role === "user" ? "text-right" : ""}`}>
                  <div className={`inline-block max-w-[90%] p-2 rounded text-xs ${
                    msg.role === "user" ? "bg-[#181c24] text-[#f0f0f0]" : "bg-[rgba(0,229,255,0.05)] text-[#f0f0f0] border border-[rgba(0,229,255,0.1)]"
                  }`}>
                    {msg.content.split(/```json[\s\S]*?```/).map((part, j) => (
                      <span key={j}>{part}</span>
                    ))}
                  </div>
                </div>
              ))}
              {isMapChatLoading && (
                <div className="text-xs animate-thinking" style={{ fontFamily: "'IBM Plex Mono', monospace" }}>
                  ░░░
                </div>
              )}
              <div ref={mapChatEndRef} />
            </div>
          </ScrollArea>
          
          <div className="p-2 border-t border-[rgba(255,255,255,0.08)]">
            <div className="flex gap-1.5">
              <Input data-testid="map-intel-input" value={mapChatInput}
                onChange={(e) => setMapChatInput(e.target.value)}
                onKeyPress={(e) => e.key === "Enter" && handleMapChatSend()}
                placeholder="e.g. Show critical incidents..."
                disabled={isMapChatLoading}
                className="flex-1 h-8 text-xs bg-[#181c24] border-[rgba(255,255,255,0.08)] text-[#f0f0f0] placeholder:text-[#6b7280]" />
              <Button data-testid="map-intel-send" onClick={handleMapChatSend} disabled={isMapChatLoading || !mapChatInput.trim()}
                size="sm" className="h-8 w-8 p-0 bg-[#00e5ff] text-black hover:bg-[#00c8e0]">
                <svg className="w-3.5 h-3.5" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <line x1="22" y1="2" x2="11" y2="13" /><polygon points="22 2 15 22 11 13 2 9 22 2" />
                </svg>
              </Button>
            </div>
          </div>
        </div>
      )}

      {/* Incident Panel */}
      <aside data-testid="incident-panel"
        className="absolute top-0 right-0 bottom-0 w-[280px] bg-[#111318] border-l border-[rgba(255,255,255,0.08)] z-10 hidden md:flex flex-col">
        <div className="p-3 border-b border-[rgba(255,255,255,0.08)]">
          <div className="flex items-center justify-between">
            <h2 className="text-xs font-medium text-[#9ca3af] uppercase tracking-wider">Incidents</h2>
            <span className="text-xs text-[#6b7280]">{filteredIncidents.length}</span>
          </div>
        </div>

        <ScrollArea className="flex-1">
          <div className="p-2 space-y-1">
            {filteredIncidents.length === 0 ? (
              <div className="p-4 text-center text-xs text-[#6b7280]">No incidents</div>
            ) : (
              filteredIncidents.map((incident) => (
                <div key={incident.id} data-testid={`incident-row-${incident.id}`}
                  onClick={() => handleIncidentClick(incident)}
                  className={`p-2 rounded cursor-pointer transition-colors ${expandedIncident === incident.id ? "bg-[#181c24] border border-[rgba(255,255,255,0.08)]" : "hover:bg-[#181c24]"}`}>
                  <div className="flex items-start gap-2">
                    <span className={`w-2 h-2 rounded-full mt-1.5 flex-shrink-0 ${severityColors[incident.severity]} ${incident.severity === "critical" ? "animate-critical-pulse" : ""}`} />
                    <div className="flex-1 min-w-0">
                      <p className="text-xs text-[#f0f0f0] line-clamp-2">{incident.description}</p>
                      <div className="flex items-center gap-2 mt-1">
                        <span className="text-[10px] text-[#6b7280]">{formatTime(incident.datetime)}</span>
                        {verificationBadge(incident.verification_status)}
                      </div>
                    </div>
                  </div>

                  {expandedIncident === incident.id && (
                    <div className="mt-3 pt-3 border-t border-[rgba(255,255,255,0.08)] panel-expand">
                      <div className="space-y-2 text-xs">
                        <div>
                          <span className="text-[#6b7280]">Severity: </span>
                          <Badge variant="outline" className={`text-[10px] uppercase ${
                            incident.severity === "critical" ? "border-[#ff2d2d] text-[#ff2d2d]" :
                            incident.severity === "high" ? "border-[#ffb800] text-[#ffb800]" :
                            incident.severity === "medium" ? "border-[#3b82f6] text-[#3b82f6]" : "border-[#00d26a] text-[#00d26a]"
                          }`}>{incident.severity}</Badge>
                        </div>
                        <div>
                          <span className="text-[#6b7280]">Coordinates: </span>
                          <button onClick={(e) => { e.stopPropagation(); navigator.clipboard.writeText(`${incident.lat}, ${incident.lng}`); }}
                            className="text-[#00e5ff] hover:underline">
                            {incident.lat?.toFixed(4)}, {incident.lng?.toFixed(4)}
                          </button>
                        </div>
                        {incident.source && <div><span className="text-[#6b7280]">Source: </span><span className="text-[#f0f0f0]">{incident.source}</span></div>}
                        {(incident.image || incident.image_file_id) && (
                          <div>
                            <span className="text-[#6b7280]">Photo: </span>
                            {incident.image_file_id ? (
                              <img src={`${API}/files/${incident.image_file_id}`} alt="Incident" className="mt-1 w-full rounded-md border border-[rgba(255,255,255,0.08)]" />
                            ) : incident.image ? (
                              <img src={incident.image} alt="Incident" className="mt-1 w-full rounded-md border border-[rgba(255,255,255,0.08)]" />
                            ) : null}
                          </div>
                        )}
                        <Button variant="outline" size="sm"
                          data-testid={`flag-incident-${incident.id}`}
                          disabled={flaggingIncidentId === incident.id}
                          className="w-full mt-2 text-[10px] h-7 border-[rgba(255,255,255,0.08)] text-[#9ca3af] hover:text-[#f0f0f0] hover:bg-[#181c24]"
                          onClick={(e) => {
                            e.stopPropagation();
                            handleFlagIncident(incident.id);
                          }}>
                          {flaggingIncidentId === incident.id ? "FLAGGING..." : "FLAG INCIDENT"}
                        </Button>
                      </div>
                    </div>
                  )}
                </div>
              ))
            )}
          </div>
        </ScrollArea>
      </aside>

      {/* Report FAB */}
      <button data-testid="report-fab" onClick={onReport}
        className="absolute bottom-6 right-6 md:bottom-6 md:right-[296px] md:mr-6 hidden md:flex items-center gap-2 px-4 py-3 bg-[#ff2d2d] text-white text-sm font-medium rounded-md hover:bg-[#e62626] transition-colors z-20">
        <svg className="w-4 h-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
          <line x1="12" y1="5" x2="12" y2="19" /><line x1="5" y1="12" x2="19" y2="12" />
        </svg>
        REPORT
      </button>
    </div>
  );
};
