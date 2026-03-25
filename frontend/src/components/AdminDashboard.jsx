import React, { useState, useEffect, useCallback } from "react";
import axios from "axios";
import { useAuth } from "@/components/AuthContext";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Badge } from "@/components/ui/badge";
import { toast } from "sonner";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

export const AdminDashboard = () => {
  const { user, login, logout, loading } = useAuth();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [loginError, setLoginError] = useState("");
  const [isLoggingIn, setIsLoggingIn] = useState(false);
  const [stats, setStats] = useState(null);
  const [incidents, setIncidents] = useState([]);
  const [totalIncidents, setTotalIncidents] = useState(0);
  const [subscribers, setSubscribers] = useState([]);
  const [filterStatus, setFilterStatus] = useState("");
  const [activeTab, setActiveTab] = useState("overview");

  const fetchStats = useCallback(async () => {
    try {
      const res = await axios.get(`${API}/admin/stats`, { withCredentials: true });
      setStats(res.data);
    } catch (err) {
      console.error("Error fetching stats:", err);
    }
  }, []);

  const fetchIncidents = useCallback(async () => {
    try {
      const params = filterStatus ? `?status=${filterStatus}` : "";
      const res = await axios.get(`${API}/admin/incidents${params}`, { withCredentials: true });
      setIncidents(res.data.incidents);
      setTotalIncidents(res.data.total);
    } catch (err) {
      console.error("Error fetching incidents:", err);
    }
  }, [filterStatus]);

  const fetchSubscribers = useCallback(async () => {
    try {
      const res = await axios.get(`${API}/admin/subscribers`, { withCredentials: true });
      setSubscribers(res.data);
    } catch (err) {
      console.error("Error fetching subscribers:", err);
    }
  }, []);

  useEffect(() => {
    if (user && user.role === "admin") {
      fetchStats();
      fetchIncidents();
      fetchSubscribers();
    }
  }, [user, fetchStats, fetchIncidents, fetchSubscribers]);

  const handleLogin = async (e) => {
    e.preventDefault();
    setLoginError("");
    setIsLoggingIn(true);
    try {
      await login(email, password);
      toast.success("Logged in as admin");
    } catch (err) {
      const detail = err.response?.data?.detail;
      setLoginError(typeof detail === "string" ? detail : "Login failed");
    } finally {
      setIsLoggingIn(false);
    }
  };

  const handleVerify = async (incidentId) => {
    try {
      await axios.put(`${API}/admin/incidents/${incidentId}/verify`, {}, { withCredentials: true });
      toast.success(`Incident #${incidentId} verified`);
      fetchIncidents();
      fetchStats();
    } catch (err) {
      toast.error("Failed to verify incident");
    }
  };

  const handleReject = async (incidentId) => {
    try {
      await axios.put(`${API}/admin/incidents/${incidentId}/reject`, {}, { withCredentials: true });
      toast.success(`Incident #${incidentId} rejected`);
      fetchIncidents();
      fetchStats();
    } catch (err) {
      toast.error("Failed to reject incident");
    }
  };

  if (loading) {
    return (
      <div className="h-full flex items-center justify-center bg-[#0a0c10]">
        <span className="text-[#6b7280] animate-thinking" style={{ fontFamily: "'IBM Plex Mono', monospace" }}>░░░ Loading...</span>
      </div>
    );
  }

  // Login Form
  if (!user || user.role !== "admin") {
    return (
      <div className="h-full flex items-center justify-center bg-[#0a0c10]" data-testid="admin-login">
        <div className="w-full max-w-sm p-6 bg-[#111318] border border-[rgba(255,255,255,0.08)] rounded-md">
          <h2 className="text-lg font-semibold text-[#f0f0f0] mb-1" style={{ fontFamily: "'Epilogue', sans-serif" }}>
            Admin Access
          </h2>
          <p className="text-xs text-[#6b7280] mb-6">SafeGuard verification dashboard</p>

          <form onSubmit={handleLogin} className="space-y-4">
            {loginError && (
              <div className="p-2 bg-[rgba(255,45,45,0.1)] border border-[#ff2d2d] rounded text-xs text-[#ff2d2d]" data-testid="login-error">
                {loginError}
              </div>
            )}
            <div>
              <Input
                data-testid="admin-email-input"
                type="email" value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="Admin email"
                className="bg-[#181c24] border-[rgba(255,255,255,0.08)] text-[#f0f0f0] placeholder:text-[#6b7280]"
              />
            </div>
            <div>
              <Input
                data-testid="admin-password-input"
                type="password" value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="Password"
                className="bg-[#181c24] border-[rgba(255,255,255,0.08)] text-[#f0f0f0] placeholder:text-[#6b7280]"
              />
            </div>
            <Button
              type="submit" data-testid="admin-login-btn"
              disabled={isLoggingIn}
              className="w-full bg-[#00e5ff] text-black hover:bg-[#00c8e0]"
            >
              {isLoggingIn ? "Signing in..." : "SIGN IN"}
            </Button>
          </form>
        </div>
      </div>
    );
  }

  // Admin Dashboard
  const sevColors = {
    critical: "text-[#ff2d2d] bg-[rgba(255,45,45,0.15)]",
    high: "text-[#ffb800] bg-[rgba(255,184,0,0.15)]",
    medium: "text-[#3b82f6] bg-[rgba(59,130,246,0.15)]",
    low: "text-[#00d26a] bg-[rgba(0,210,106,0.15)]",
  };

  const vsColors = {
    unverified: "text-[#6b7280] bg-[#181c24]",
    verified: "text-[#00d26a] bg-[rgba(0,210,106,0.15)]",
    flagged: "text-[#ffb800] bg-[rgba(255,184,0,0.15)]",
    rejected: "text-[#ff2d2d] bg-[rgba(255,45,45,0.15)]",
  };

  const formatDate = (d) => {
    if (!d) return "-";
    const date = new Date(d);
    return date.toLocaleDateString("en-US", { month: "short", day: "numeric", hour: "2-digit", minute: "2-digit" });
  };

  return (
    <div className="h-full flex flex-col bg-[#0a0c10]" data-testid="admin-dashboard">
      {/* Admin Header */}
      <div className="flex items-center justify-between p-4 border-b border-[rgba(255,255,255,0.08)]">
        <div>
          <h2 className="text-lg font-semibold text-[#f0f0f0]" style={{ fontFamily: "'Epilogue', sans-serif" }}>
            Admin Dashboard
          </h2>
          <p className="text-xs text-[#6b7280]">{user.email}</p>
        </div>
        <Button
          data-testid="admin-logout-btn"
          variant="outline" size="sm"
          onClick={logout}
          className="text-xs border-[rgba(255,255,255,0.08)] text-[#9ca3af] hover:text-[#f0f0f0]"
        >
          LOGOUT
        </Button>
      </div>

      {/* Tabs */}
      <div className="flex border-b border-[rgba(255,255,255,0.08)] px-4">
        {["overview", "incidents", "subscribers"].map((tab) => (
          <button
            key={tab}
            data-testid={`admin-tab-${tab}`}
            onClick={() => setActiveTab(tab)}
            className={`px-4 py-2 text-xs font-medium uppercase tracking-wider border-b-2 transition-colors ${
              activeTab === tab
                ? "border-[#00e5ff] text-[#00e5ff]"
                : "border-transparent text-[#6b7280] hover:text-[#9ca3af]"
            }`}
          >
            {tab}
          </button>
        ))}
      </div>

      {/* Content */}
      <div className="flex-1 overflow-hidden">
        {activeTab === "overview" && stats && (
          <div className="p-4 md:p-6 space-y-6">
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              {[
                { label: "Total Incidents", value: stats.incidents.total, color: "#f0f0f0" },
                { label: "Critical", value: stats.incidents.critical, color: "#ff2d2d" },
                { label: "Unverified", value: stats.incidents.unverified, color: "#ffb800" },
                { label: "Verified", value: stats.incidents.verified, color: "#00d26a" },
                { label: "Flagged", value: stats.incidents.flagged, color: "#ffb800" },
                { label: "Rejected", value: stats.incidents.rejected, color: "#ff2d2d" },
                { label: "Subscribers", value: stats.subscribers, color: "#00e5ff" },
                { label: "Resources", value: stats.resources, color: "#3b82f6" },
              ].map((stat) => (
                <div
                  key={stat.label}
                  className="p-4 bg-[#111318] border border-[rgba(255,255,255,0.08)] rounded-md"
                >
                  <p className="text-xs text-[#6b7280] uppercase tracking-wider">{stat.label}</p>
                  <p className="text-2xl font-bold mt-1" style={{ color: stat.color, fontFamily: "'IBM Plex Mono', monospace" }}>
                    {stat.value}
                  </p>
                </div>
              ))}
            </div>
          </div>
        )}

        {activeTab === "incidents" && (
          <div className="flex flex-col h-full">
            {/* Filters */}
            <div className="flex items-center gap-2 p-4 border-b border-[rgba(255,255,255,0.08)]">
              {["", "unverified", "verified", "flagged", "rejected"].map((status) => (
                <button
                  key={status || "all"}
                  data-testid={`admin-filter-${status || "all"}`}
                  onClick={() => setFilterStatus(status)}
                  className={`px-3 py-1.5 text-xs rounded transition-colors ${
                    filterStatus === status
                      ? "bg-[rgba(0,229,255,0.15)] text-[#00e5ff]"
                      : "text-[#6b7280] hover:text-[#9ca3af] hover:bg-[#181c24]"
                  }`}
                >
                  {status ? status.toUpperCase() : "ALL"}
                </button>
              ))}
              <span className="ml-auto text-xs text-[#6b7280]">{totalIncidents} incidents</span>
            </div>

            {/* Incident List */}
            <ScrollArea className="flex-1">
              <div className="p-4 space-y-2">
                {incidents.map((incident) => (
                  <div
                    key={incident.id}
                    data-testid={`admin-incident-${incident.id}`}
                    className="p-3 bg-[#111318] border border-[rgba(255,255,255,0.08)] rounded-md"
                  >
                    <div className="flex items-start justify-between">
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center gap-2 mb-1">
                          <span className="text-xs text-[#6b7280]">#{incident.id}</span>
                          <Badge variant="outline" className={`text-[10px] uppercase border-none ${sevColors[incident.severity]}`}>
                            {incident.severity}
                          </Badge>
                          <Badge variant="outline" className={`text-[10px] uppercase border-none ${vsColors[incident.verification_status]}`}>
                            {incident.verification_status}
                          </Badge>
                        </div>
                        <p className="text-sm text-[#f0f0f0]">{incident.description}</p>
                        <div className="flex items-center gap-3 mt-1 text-[10px] text-[#6b7280]">
                          <span>{formatDate(incident.datetime)}</span>
                          <span>{incident.lat?.toFixed(3)}, {incident.lng?.toFixed(3)}</span>
                          {incident.source && <span>src: {incident.source}</span>}
                        </div>
                      </div>
                      <div className="flex gap-1 ml-3">
                        {incident.verification_status !== "verified" && (
                          <Button
                            size="sm"
                            data-testid={`verify-btn-${incident.id}`}
                            onClick={() => handleVerify(incident.id)}
                            className="text-[10px] h-7 bg-[rgba(0,210,106,0.15)] text-[#00d26a] hover:bg-[rgba(0,210,106,0.25)] border-none"
                          >
                            VERIFY
                          </Button>
                        )}
                        {incident.verification_status !== "rejected" && (
                          <Button
                            size="sm"
                            data-testid={`reject-btn-${incident.id}`}
                            onClick={() => handleReject(incident.id)}
                            className="text-[10px] h-7 bg-[rgba(255,45,45,0.15)] text-[#ff2d2d] hover:bg-[rgba(255,45,45,0.25)] border-none"
                          >
                            REJECT
                          </Button>
                        )}
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </ScrollArea>
          </div>
        )}

        {activeTab === "subscribers" && (
          <ScrollArea className="h-full">
            <div className="p-4 space-y-2">
              {subscribers.length === 0 ? (
                <p className="text-center text-[#6b7280] text-sm py-8">No subscribers</p>
              ) : (
                subscribers.map((sub, i) => (
                  <div key={sub.id || i} className="p-3 bg-[#111318] border border-[rgba(255,255,255,0.08)] rounded-md">
                    <div className="flex items-center justify-between">
                      <div>
                        <p className="text-sm text-[#f0f0f0]">{sub.name}</p>
                        <p className="text-[10px] text-[#6b7280]">{sub.email}</p>
                        {sub.address && <p className="text-[10px] text-[#9ca3af]">{sub.address}</p>}
                      </div>
                      <div className="text-right text-[10px] text-[#6b7280]">
                        <p>{sub.radius_km} km radius</p>
                        {sub.latitude && sub.longitude && (
                          <p>{sub.latitude.toFixed(2)}, {sub.longitude.toFixed(2)}</p>
                        )}
                        <p className={sub.active ? "text-[#00d26a]" : "text-[#ff2d2d]"}>
                          {sub.active ? "ACTIVE" : "INACTIVE"}
                        </p>
                      </div>
                    </div>
                  </div>
                ))
              )}
            </div>
          </ScrollArea>
        )}
      </div>
    </div>
  );
};
