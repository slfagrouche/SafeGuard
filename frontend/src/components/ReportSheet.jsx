import React, { useState, useRef } from "react";
import { Sheet, SheetContent, SheetHeader, SheetTitle } from "@/components/ui/sheet";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { toast } from "sonner";
import { MapContainer, TileLayer, Marker, useMapEvents } from "react-leaflet";
import "leaflet/dist/leaflet.css";
import L from "leaflet";
import axios from "axios";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const locationIcon = L.divIcon({
  className: "location-marker",
  html: `<div style="width:12px;height:12px;background-color:#ff2d2d;border-radius:50%;border:2px solid #0a0c10;box-shadow:0 0 8px rgba(255,45,45,0.5);"></div>`,
  iconSize: [12, 12], iconAnchor: [6, 6],
});

const MapClickHandler = ({ onClick }) => {
  useMapEvents({ click: (e) => onClick(e.latlng) });
  return null;
};

const MapViewportUpdater = ({ center }) => {
  const map = useMapEvents({});
  React.useEffect(() => {
    if (Array.isArray(center) && center.length === 2) {
      map.setView(center, map.getZoom(), { animate: true });
    }
  }, [center, map]);
  return null;
};

export const ReportSheet = ({ open, onOpenChange, onSubmit }) => {
  const [formData, setFormData] = useState({
    lat: null, lng: null,
    dateTime: new Date().toISOString().slice(0, 16),
    description: "", severity: "medium", source: "",
  });
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState(null);
  const [mapCenter, setMapCenter] = useState([20, 0]);
  const [photoFile, setPhotoFile] = useState(null);
  const [photoPreview, setPhotoPreview] = useState(null);
  const [isUploading, setIsUploading] = useState(false);
  const fileInputRef = useRef(null);

  const handleMapClick = (latlng) => {
    setFormData((prev) => ({ ...prev, lat: latlng.lat, lng: latlng.lng }));
    setMapCenter([latlng.lat, latlng.lng]);
    setError(null);
  };

  const handleGetLocation = () => {
    if (!navigator.geolocation) {
      toast.error("Geolocation is not supported by this browser");
      return;
    }
    navigator.geolocation.getCurrentPosition(
      (pos) => {
        const { latitude, longitude } = pos.coords;
        setFormData((prev) => ({ ...prev, lat: latitude, lng: longitude }));
        setMapCenter([latitude, longitude]);
        setError(null);
        toast.success("Location detected");
      },
      (geoErr) => {
        const msg = geoErr?.code === 1
          ? "Location permission denied"
          : "Could not get your location";
        toast.error(msg);
      },
      { enableHighAccuracy: true, timeout: 12000, maximumAge: 0 }
    );
  };

  const handlePhotoSelect = (e) => {
    const file = e.target.files[0];
    if (!file) return;
    
    const allowed = ["image/jpeg", "image/png", "image/webp", "image/gif"];
    if (!allowed.includes(file.type)) {
      toast.error("Invalid file type. Use JPG, PNG, WebP, or GIF");
      return;
    }
    if (file.size > 10 * 1024 * 1024) {
      toast.error("File too large. Max 10MB");
      return;
    }
    
    setPhotoFile(file);
    const reader = new FileReader();
    reader.onloadend = () => setPhotoPreview(reader.result);
    reader.readAsDataURL(file);
  };

  const removePhoto = () => {
    setPhotoFile(null);
    setPhotoPreview(null);
    if (fileInputRef.current) fileInputRef.current.value = "";
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError(null);

    if (formData.lat == null || formData.lng == null) {
      setError("Please select a location on the map or use GPS");
      return;
    }
    if (!formData.description.trim()) {
      setError("Please provide a description");
      return;
    }

    setIsSubmitting(true);
    try {
      let imageFileId = "";
      
      // Upload photo first if present
      if (photoFile) {
        setIsUploading(true);
        const uploadData = new FormData();
        uploadData.append("file", photoFile);
        
        try {
          const uploadRes = await axios.post(`${API}/upload/`, uploadData, {
            headers: { "Content-Type": "multipart/form-data" },
          });
          imageFileId = uploadRes.data.id;
        } catch (uploadErr) {
          console.error("Photo upload failed:", uploadErr);
          toast.error("Photo upload failed, submitting without photo");
        }
        setIsUploading(false);
      }

      await onSubmit({ ...formData, image_file_id: imageFileId });
      toast.success("Report submitted successfully");
      setFormData({ lat: null, lng: null, dateTime: new Date().toISOString().slice(0, 16), description: "", severity: "medium", source: "" });
      removePhoto();
    } catch (err) {
      setError("Failed to submit report. Please try again.");
    } finally {
      setIsSubmitting(false);
    }
  };

  const severityOptions = [
    { value: "critical", label: "CRITICAL", color: "#ff2d2d" },
    { value: "high", label: "HIGH", color: "#ffb800" },
    { value: "medium", label: "MEDIUM", color: "#3b82f6" },
    { value: "low", label: "LOW", color: "#00d26a" },
  ];

  return (
    <Sheet open={open} onOpenChange={onOpenChange}>
      <SheetContent
        side="bottom"
        className="bg-[#111318] border-t border-[rgba(255,255,255,0.08)] rounded-t-lg max-h-[90vh] overflow-y-auto md:max-w-lg md:mx-auto"
        data-testid="report-sheet">
        <SheetHeader className="border-b border-[rgba(255,255,255,0.08)] pb-4 mb-4">
          <SheetTitle className="text-[#f0f0f0] text-lg" style={{ fontFamily: "'Epilogue', sans-serif" }}>
            Report Incident
          </SheetTitle>
        </SheetHeader>

        <form onSubmit={handleSubmit} className="space-y-4">
          {error && (
            <div className="p-3 bg-[rgba(255,45,45,0.1)] border border-[#ff2d2d] rounded text-sm text-[#ff2d2d]">{error}</div>
          )}

          {/* Location */}
          <div>
            <div className="flex items-center justify-between mb-1">
              <Label className="text-xs text-[#9ca3af] uppercase tracking-wider">Location *</Label>
              <Button type="button" variant="ghost" size="sm" onClick={handleGetLocation}
                className="text-[10px] text-[#00e5ff] hover:text-[#00e5ff] hover:bg-[rgba(0,229,255,0.1)]">
                USE GPS
              </Button>
            </div>
            <div className="h-[140px] rounded-md overflow-hidden border border-[rgba(255,255,255,0.08)]">
              <MapContainer center={mapCenter} zoom={2} className="h-full w-full" zoomControl={false}>
                <TileLayer url="https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png" />
                <MapViewportUpdater center={mapCenter} />
                <MapClickHandler onClick={handleMapClick} />
                {formData.lat != null && formData.lng != null && <Marker position={[formData.lat, formData.lng]} icon={locationIcon} />}
              </MapContainer>
            </div>
            {formData.lat != null && formData.lng != null && (
              <p className="text-[10px] text-[#6b7280] mt-1">Selected: {formData.lat.toFixed(4)}, {formData.lng.toFixed(4)}</p>
            )}
          </div>

          {/* Date/Time */}
          <div>
            <Label className="text-xs text-[#9ca3af] uppercase tracking-wider">Date & Time</Label>
            <Input type="datetime-local" data-testid="report-datetime"
              value={formData.dateTime} onChange={(e) => setFormData({ ...formData, dateTime: e.target.value })}
              className="mt-1 bg-[#181c24] border-[rgba(255,255,255,0.08)] text-[#f0f0f0]" />
          </div>

          {/* Description */}
          <div>
            <Label className="text-xs text-[#9ca3af] uppercase tracking-wider">Description *</Label>
            <Textarea data-testid="report-description"
              value={formData.description} onChange={(e) => setFormData({ ...formData, description: e.target.value })}
              placeholder="Describe the incident..." rows={3}
              className="mt-1 bg-[#181c24] border-[rgba(255,255,255,0.08)] text-[#f0f0f0] placeholder:text-[#6b7280] resize-none" />
          </div>

          {/* Severity */}
          <div>
            <Label className="text-xs text-[#9ca3af] uppercase tracking-wider mb-2 block">Severity *</Label>
            <div className="flex gap-1">
              {severityOptions.map((option) => (
                <button key={option.value} type="button" data-testid={`severity-${option.value}`}
                  onClick={() => setFormData({ ...formData, severity: option.value })}
                  className={`flex-1 py-2 text-xs font-medium rounded transition-colors ${
                    formData.severity === option.value ? "text-white" : "bg-[#181c24] text-[#6b7280] hover:text-[#9ca3af]"
                  }`}
                  style={{ backgroundColor: formData.severity === option.value ? option.color : undefined }}>
                  {option.label}
                </button>
              ))}
            </div>
          </div>

          {/* Photo Upload */}
          <div>
            <Label className="text-xs text-[#9ca3af] uppercase tracking-wider mb-1 block">
              Photo <span className="text-[#6b7280]">(optional)</span>
            </Label>
            {photoPreview ? (
              <div className="relative">
                <img src={photoPreview} alt="Preview" className="w-full h-32 object-cover rounded-md border border-[rgba(255,255,255,0.08)]" />
                <button type="button" onClick={removePhoto}
                  className="absolute top-2 right-2 w-6 h-6 bg-[#ff2d2d] text-white rounded-full flex items-center justify-center text-xs">
                  X
                </button>
                {isUploading && (
                  <div className="absolute inset-0 bg-[rgba(0,0,0,0.7)] flex items-center justify-center rounded-md">
                    <span className="text-xs text-[#00e5ff] animate-thinking">Uploading...</span>
                  </div>
                )}
              </div>
            ) : (
              <button type="button" data-testid="photo-upload-btn"
                onClick={() => fileInputRef.current?.click()}
                className="w-full p-4 border border-dashed border-[rgba(255,255,255,0.16)] rounded-md text-center hover:border-[#00e5ff] transition-colors">
                <svg className="w-6 h-6 mx-auto text-[#6b7280] mb-1" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <rect x="3" y="3" width="18" height="18" rx="2" />
                  <circle cx="8.5" cy="8.5" r="1.5" />
                  <polyline points="21 15 16 10 5 21" />
                </svg>
                <p className="text-xs text-[#6b7280]">Tap to add photo</p>
                <p className="text-[10px] text-[#6b7280] mt-0.5">JPG, PNG, WebP, GIF — Max 10MB</p>
              </button>
            )}
            <input ref={fileInputRef} type="file" accept="image/jpeg,image/png,image/webp,image/gif"
              onChange={handlePhotoSelect} className="hidden" />
          </div>

          {/* Source URL */}
          <div>
            <Label className="text-xs text-[#9ca3af] uppercase tracking-wider">
              Source URL <span className="text-[#6b7280]">(optional)</span>
            </Label>
            <Input data-testid="report-source" value={formData.source}
              onChange={(e) => setFormData({ ...formData, source: e.target.value })}
              placeholder="https://..." className="mt-1 bg-[#181c24] border-[rgba(255,255,255,0.08)] text-[#f0f0f0] placeholder:text-[#6b7280]" />
          </div>

          {/* Submit */}
          <Button type="submit" data-testid="submit-report-btn" disabled={isSubmitting}
            className="w-full bg-[#ff2d2d] text-white hover:bg-[#e62626] disabled:opacity-50">
            {isSubmitting ? (isUploading ? "Uploading photo..." : "Submitting...") : "SUBMIT REPORT"}
          </Button>
        </form>
      </SheetContent>
    </Sheet>
  );
};
