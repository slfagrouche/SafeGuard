import { useState, useEffect, useCallback, useRef } from "react";
import "@/App.css";
import { BrowserRouter, Routes, Route, useNavigate, useLocation } from "react-router-dom";
import axios from "axios";
import { MapView } from "@/components/MapView";
import { AIHub } from "@/components/AIHub";
import { AlertsView } from "@/components/AlertsView";
import { ResourcesView } from "@/components/ResourcesView";
import { ReportSheet } from "@/components/ReportSheet";
import { Sidebar } from "@/components/Sidebar";
import { Topbar } from "@/components/Topbar";
import { AdminDashboard } from "@/components/AdminDashboard";
import { AuthProvider } from "@/components/AuthContext";
import { Toaster } from "@/components/ui/sonner";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

// Derive WebSocket URL from backend URL
const getWsUrl = () => {
  const url = new URL(BACKEND_URL);
  const protocol = url.protocol === "https:" ? "wss:" : "ws:";
  return `${protocol}//${url.host}/ws/incidents`;
};

const MainLayout = () => {
  const [incidents, setIncidents] = useState([]);
  const [resources, setResources] = useState([]);
  const [activeView, setActiveView] = useState("map");
  const [showReportSheet, setShowReportSheet] = useState(false);
  const [criticalCount, setCriticalCount] = useState(0);
  const [highCount, setHighCount] = useState(0);
  const wsRef = useRef(null);
  const reconnectRef = useRef(null);
  const navigate = useNavigate();
  const location = useLocation();

  const fetchIncidents = useCallback(async () => {
    try {
      const response = await axios.get(`${API}/incidents/`);
      setIncidents(response.data);
      setCriticalCount(response.data.filter(i => i.severity === "critical").length);
      setHighCount(response.data.filter(i => i.severity === "high").length);
    } catch (e) {
      console.error("Error fetching incidents:", e);
    }
  }, []);

  const fetchResources = useCallback(async () => {
    try {
      const response = await axios.get(`${API}/resources/`);
      setResources(response.data);
    } catch (e) {
      console.error("Error fetching resources:", e);
    }
  }, []);

  // WebSocket connection for real-time updates
  const connectWebSocket = useCallback(() => {
    try {
      const ws = new WebSocket(getWsUrl());
      wsRef.current = ws;

      ws.onopen = () => {
        console.log("WebSocket connected");
        if (reconnectRef.current) {
          clearTimeout(reconnectRef.current);
          reconnectRef.current = null;
        }
      };

      ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          if (data.type === "new_incident") {
            setIncidents(prev => [data.incident, ...prev]);
            if (data.incident.severity === "critical") {
              setCriticalCount(prev => prev + 1);
            } else if (data.incident.severity === "high") {
              setHighCount(prev => prev + 1);
            }
          } else if (data.type === "incident_updated") {
            setIncidents(prev =>
              prev.map(inc => inc.id === data.incident.id ? data.incident : inc)
            );
          } else if (data.type === "incident_removed") {
            setIncidents(prev => prev.filter(inc => inc.id !== data.incident_id));
          }
        } catch (e) {
          console.error("WS message parse error:", e);
        }
      };

      ws.onclose = () => {
        console.log("WebSocket disconnected, reconnecting in 5s...");
        reconnectRef.current = setTimeout(connectWebSocket, 5000);
      };

      ws.onerror = () => {
        ws.close();
      };
    } catch (e) {
      console.error("WS connection error:", e);
      reconnectRef.current = setTimeout(connectWebSocket, 5000);
    }
  }, []);

  const seedData = useCallback(async () => {
    try {
      await axios.post(`${API}/seed/`);
      fetchIncidents();
      fetchResources();
    } catch (e) {
      console.error("Error seeding:", e);
    }
  }, [fetchIncidents, fetchResources]);

  useEffect(() => {
    fetchIncidents();
    fetchResources();
    connectWebSocket();

    return () => {
      if (wsRef.current) wsRef.current.close();
      if (reconnectRef.current) clearTimeout(reconnectRef.current);
    };
  }, [fetchIncidents, fetchResources, connectWebSocket]);

  useEffect(() => {
    if (incidents.length === 0) seedData();
  }, [incidents.length, seedData]);

  useEffect(() => {
    const path = location.pathname;
    if (path === "/" || path === "/map") setActiveView("map");
    else if (path === "/ai") setActiveView("ai");
    else if (path === "/alerts") setActiveView("alerts");
    else if (path === "/resources") setActiveView("resources");
  }, [location]);

  const handleNavigation = (view) => {
    setActiveView(view);
    navigate(view === "map" ? "/" : `/${view}`);
  };

  const handleReportSubmit = async (data) => {
    try {
      await axios.post(`${API}/report/`, data);
      setShowReportSheet(false);
      fetchIncidents();
    } catch (e) {
      console.error("Error submitting report:", e);
      throw e;
    }
  };

  return (
    <div className="flex h-screen bg-[#0a0c10] overflow-hidden" data-testid="main-layout">
      <Sidebar activeView={activeView} onNavigate={handleNavigation} onReport={() => setShowReportSheet(true)} />

      <div className="flex-1 flex flex-col min-w-0">
        <Topbar viewName={activeView.toUpperCase()} criticalCount={criticalCount} highCount={highCount} />

        <main className="flex-1 overflow-hidden">
          {activeView === "map" && <MapView incidents={incidents} onRefresh={fetchIncidents} onReport={() => setShowReportSheet(true)} />}
          {activeView === "ai" && <AIHub />}
          {activeView === "alerts" && <AlertsView />}
          {activeView === "resources" && <ResourcesView resources={resources} onRefresh={fetchResources} />}
        </main>
      </div>

      {/* Mobile Bottom Nav */}
      <div className="fixed bottom-0 left-0 right-0 md:hidden bg-[#111318] border-t border-[rgba(255,255,255,0.08)] z-50">
        <div className="flex items-center justify-around h-14">
          {[
            { id: "map", d: "M12 2L2 7l10 5 10-5-10-5zM2 17l10 5 10-5M2 12l10 5 10-5" },
            { id: "ai", d: "M12 2L2 12l10 10 10-10L12 2z" },
            { id: "alerts", d: "M4 15s1-1 4-1 5 2 8 2 4-1 4-1V3s-1 1-4 1-5-2-8-2-4 1-4 1zM4 22v-7" },
            { id: "resources", d: "M4 6h16M4 12h16M4 18h16" },
          ].map(({ id, d }) => (
            <button key={id} data-testid={`mobile-nav-${id}`} onClick={() => handleNavigation(id)}
              className={`flex-1 flex items-center justify-center h-full ${activeView === id ? "text-[#00e5ff] bg-[rgba(0,229,255,0.1)]" : "text-[#6b7280]"}`}>
              <svg className="w-6 h-6" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d={d} /></svg>
            </button>
          ))}
          <button data-testid="mobile-nav-report" onClick={() => setShowReportSheet(true)}
            className="flex-1 flex items-center justify-center h-full bg-[rgba(255,45,45,0.15)] text-[#ff2d2d]">
            <svg className="w-6 h-6" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M12 5v14M5 12h14" /></svg>
          </button>
        </div>
      </div>

      <ReportSheet open={showReportSheet} onOpenChange={setShowReportSheet} onSubmit={handleReportSubmit} />
      <Toaster position="top-right" />
    </div>
  );
};

function App() {
  return (
    <div className="App">
      <AuthProvider>
        <BrowserRouter>
          <Routes>
            <Route path="/admin" element={<AdminDashboard />} />
            <Route path="/*" element={<MainLayout />} />
          </Routes>
        </BrowserRouter>
      </AuthProvider>
    </div>
  );
}

export default App;
