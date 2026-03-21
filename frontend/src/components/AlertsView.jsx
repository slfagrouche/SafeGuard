import React, { useState, useEffect, useCallback } from "react";
import axios from "axios";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Slider } from "@/components/ui/slider";
import { ScrollArea } from "@/components/ui/scroll-area";
import { toast } from "sonner";
import { MapContainer, TileLayer, Marker, useMapEvents, Circle } from "react-leaflet";
import "leaflet/dist/leaflet.css";
import L from "leaflet";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const locationIcon = L.divIcon({
  className: "location-marker",
  html: `<div style="width:12px;height:12px;background-color:#00e5ff;border-radius:50%;border:2px solid #0a0c10;box-shadow:0 0 8px rgba(0,229,255,0.5);"></div>`,
  iconSize: [12, 12],
  iconAnchor: [6, 6],
});

const MapClickHandler = ({ onClick }) => {
  useMapEvents({ click: (e) => onClick(e.latlng) });
  return null;
};

export const AlertsView = () => {
  const [subscriptions, setSubscriptions] = useState([]);
  const [formData, setFormData] = useState({
    name: "",
    email: "",
    address: "",
    latitude: null,
    longitude: null,
    radius_km: 10,
  });
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [mapCenter] = useState([15.5007, 32.5599]);

  const fetchSubscriptions = useCallback(async () => {
    try {
      const response = await axios.get(`${API}/subscribers/`);
      setSubscriptions(response.data);
    } catch (error) {
      console.error("Error fetching subscriptions:", error);
    }
  }, []);

  useEffect(() => {
    fetchSubscriptions();
  }, [fetchSubscriptions]);

  const handleMapClick = (latlng) => {
    setFormData((prev) => ({ ...prev, latitude: latlng.lat, longitude: latlng.lng }));
  };

  const handleGetLocation = () => {
    if (navigator.geolocation) {
      navigator.geolocation.getCurrentPosition(
        (position) => {
          setFormData((prev) => ({
            ...prev,
            latitude: position.coords.latitude,
            longitude: position.coords.longitude,
          }));
          toast.success("Location detected");
        },
        () => toast.error("Could not get your location")
      );
    } else {
      toast.error("Geolocation not supported");
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!formData.name || !formData.email) {
      toast.error("Please fill in name and email");
      return;
    }

    setIsSubmitting(true);
    try {
      // POST /api/subscribe/ — matches Django contract
      await axios.post(`${API}/subscribe/`, {
        name: formData.name,
        email: formData.email,
        address: formData.address,
        latitude: formData.latitude,
        longitude: formData.longitude,
        radius_km: formData.radius_km,
      });
      toast.success("Alert subscription created");
      setFormData({ name: "", email: "", address: "", latitude: null, longitude: null, radius_km: 10 });
      fetchSubscriptions();
    } catch (error) {
      const msg = error.response?.data?.message || error.response?.data?.detail || "Failed to create subscription";
      toast.error(msg);
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleDeactivate = async (subscriberId) => {
    try {
      await axios.delete(`${API}/subscribers/${subscriberId}/`);
      toast.success("Subscription deactivated");
      fetchSubscriptions();
    } catch (error) {
      toast.error("Failed to deactivate subscription");
    }
  };

  return (
    <div className="h-full flex flex-col md:flex-row bg-[#0a0c10]" data-testid="alerts-view">
      {/* Subscription Form */}
      <div className="w-full md:w-1/2 p-4 md:p-6 border-b md:border-b-0 md:border-r border-[rgba(255,255,255,0.08)] overflow-y-auto">
        <h2 className="text-lg font-semibold text-[#f0f0f0] mb-4" style={{ fontFamily: "'Epilogue', sans-serif" }}>
          Create Alert Subscription
        </h2>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <Label htmlFor="name" className="text-xs text-[#9ca3af] uppercase tracking-wider">Name *</Label>
            <Input
              id="name" data-testid="alert-name-input"
              value={formData.name}
              onChange={(e) => setFormData({ ...formData, name: e.target.value })}
              placeholder="Your name"
              className="mt-1 bg-[#111318] border-[rgba(255,255,255,0.08)] text-[#f0f0f0] placeholder:text-[#6b7280]"
            />
          </div>

          <div>
            <Label htmlFor="email" className="text-xs text-[#9ca3af] uppercase tracking-wider">Email *</Label>
            <Input
              id="email" data-testid="alert-email-input" type="email"
              value={formData.email}
              onChange={(e) => setFormData({ ...formData, email: e.target.value })}
              placeholder="your@email.com"
              className="mt-1 bg-[#111318] border-[rgba(255,255,255,0.08)] text-[#f0f0f0] placeholder:text-[#6b7280]"
            />
          </div>

          <div>
            <Label htmlFor="address" className="text-xs text-[#9ca3af] uppercase tracking-wider">
              Address <span className="text-[#6b7280]">(optional)</span>
            </Label>
            <Input
              id="address" data-testid="alert-address-input"
              value={formData.address}
              onChange={(e) => setFormData({ ...formData, address: e.target.value })}
              placeholder="Street address or area name"
              className="mt-1 bg-[#111318] border-[rgba(255,255,255,0.08)] text-[#f0f0f0] placeholder:text-[#6b7280]"
            />
          </div>

          <div>
            <div className="flex items-center justify-between mb-1">
              <Label className="text-xs text-[#9ca3af] uppercase tracking-wider">Location</Label>
              <Button type="button" variant="ghost" size="sm" onClick={handleGetLocation}
                className="text-[10px] text-[#00e5ff] hover:text-[#00e5ff] hover:bg-[rgba(0,229,255,0.1)]">
                USE GPS
              </Button>
            </div>
            <div className="h-[180px] rounded-md overflow-hidden border border-[rgba(255,255,255,0.08)]">
              <MapContainer center={mapCenter} zoom={10} className="h-full w-full" zoomControl={false}>
                <TileLayer url="https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png" />
                <MapClickHandler onClick={handleMapClick} />
                {formData.latitude && formData.longitude && (
                  <>
                    <Marker position={[formData.latitude, formData.longitude]} icon={locationIcon} />
                    <Circle
                      center={[formData.latitude, formData.longitude]}
                      radius={formData.radius_km * 1000}
                      pathOptions={{ color: "#00e5ff", fillColor: "#00e5ff", fillOpacity: 0.1, weight: 1 }}
                    />
                  </>
                )}
              </MapContainer>
            </div>
            {formData.latitude && formData.longitude && (
              <p className="text-[10px] text-[#6b7280] mt-1">
                Selected: {formData.latitude.toFixed(4)}, {formData.longitude.toFixed(4)}
              </p>
            )}
          </div>

          <div>
            <div className="flex items-center justify-between mb-2">
              <Label className="text-xs text-[#9ca3af] uppercase tracking-wider">Radius</Label>
              <span className="text-xs text-[#f0f0f0]">{formData.radius_km} km</span>
            </div>
            <Slider
              data-testid="radius-slider"
              value={[formData.radius_km]}
              onValueChange={(value) => setFormData({ ...formData, radius_km: value[0] })}
              min={1} max={500} step={1} className="py-2"
            />
            <div className="flex justify-between text-[10px] text-[#6b7280]">
              <span>1 km</span>
              <span>500 km</span>
            </div>
          </div>

          <Button type="submit" data-testid="create-alert-btn" disabled={isSubmitting}
            className="w-full bg-[#00e5ff] text-black hover:bg-[#00c8e0] disabled:opacity-50">
            {isSubmitting ? "Creating..." : "CREATE SUBSCRIPTION"}
          </Button>
        </form>
      </div>

      {/* Active Subscriptions */}
      <div className="flex-1 p-4 md:p-6">
        <h2 className="text-lg font-semibold text-[#f0f0f0] mb-4" style={{ fontFamily: "'Epilogue', sans-serif" }}>
          Active Subscriptions
        </h2>

        <ScrollArea className="h-[calc(100%-40px)]">
          {subscriptions.length === 0 ? (
            <div className="text-center py-8 text-[#6b7280]">
              <p className="text-sm">No active subscriptions</p>
              <p className="text-xs mt-1">Create one to receive alerts</p>
            </div>
          ) : (
            <div className="space-y-3">
              {subscriptions.map((sub) => (
                <div key={sub.id} data-testid={`subscription-${sub.id}`}
                  className="p-3 bg-[#111318] border border-[rgba(255,255,255,0.08)] rounded-md">
                  <div className="flex items-start justify-between">
                    <div className="flex items-start gap-3">
                      <div className="w-8 h-8 rounded-full bg-[rgba(0,229,255,0.1)] flex items-center justify-center">
                        <svg className="w-4 h-4 text-[#00e5ff]" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                          <path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0 1 18 0z" />
                          <circle cx="12" cy="10" r="3" />
                        </svg>
                      </div>
                      <div>
                        <p className="text-sm font-medium text-[#f0f0f0]">{sub.name}</p>
                        <p className="text-[10px] text-[#6b7280]">{sub.email}</p>
                        {sub.address && <p className="text-[10px] text-[#9ca3af]">{sub.address}</p>}
                        <div className="flex items-center gap-3 mt-1.5 text-[10px] text-[#9ca3af]">
                          <span>{sub.radius_km} km radius</span>
                          {sub.latitude && sub.longitude && (
                            <>
                              <span>·</span>
                              <span>{sub.latitude.toFixed(2)}, {sub.longitude.toFixed(2)}</span>
                            </>
                          )}
                        </div>
                      </div>
                    </div>
                    <Button variant="ghost" size="sm" data-testid={`deactivate-${sub.id}`}
                      onClick={() => handleDeactivate(sub.id)}
                      className="text-[10px] text-[#ff2d2d] hover:text-[#ff2d2d] hover:bg-[rgba(255,45,45,0.1)]">
                      DEACTIVATE
                    </Button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </ScrollArea>
      </div>
    </div>
  );
};
