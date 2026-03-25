import React, { useState, useEffect, useCallback } from "react";
import axios from "axios";
import { Input } from "@/components/ui/input";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Badge } from "@/components/ui/badge";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const RESOURCE_TYPES = [
  { id: "all", label: "ALL" },
  { id: "hospital", label: "HOSPITAL" },
  { id: "shelter", label: "SHELTER" },
  { id: "aid", label: "AID" },
  { id: "pharmacy", label: "PHARMACY" },
  { id: "water", label: "WATER" },
];

const TYPE_COLORS = {
  hospital: { bg: "bg-[rgba(255,45,45,0.15)]", text: "text-[#ff2d2d]" },
  shelter: { bg: "bg-[rgba(0,229,255,0.15)]", text: "text-[#00e5ff]" },
  aid: { bg: "bg-[rgba(255,184,0,0.15)]", text: "text-[#ffb800]" },
  pharmacy: { bg: "bg-[rgba(0,210,106,0.15)]", text: "text-[#00d26a]" },
  water: { bg: "bg-[rgba(59,130,246,0.15)]", text: "text-[#3b82f6]" },
};

export const ResourcesView = ({ resources: initialResources, onRefresh }) => {
  const [resources, setResources] = useState(initialResources || []);
  const [activeType, setActiveType] = useState("all");
  const [searchQuery, setSearchQuery] = useState("");
  const [expandedResource, setExpandedResource] = useState(null);
  const [isLoading, setIsLoading] = useState(false);

  const fetchResources = useCallback(async () => {
    setIsLoading(true);
    try {
      const params = new URLSearchParams();
      if (activeType !== "all") params.append("type", activeType);
      if (searchQuery) params.append("search", searchQuery);
      
      const response = await axios.get(`${API}/resources/?${params.toString()}`);
      setResources(response.data);
    } catch (error) {
      console.error("Error fetching resources:", error);
    } finally {
      setIsLoading(false);
    }
  }, [activeType, searchQuery]);

  useEffect(() => {
    fetchResources();
  }, [fetchResources]);

  useEffect(() => {
    if (initialResources) {
      setResources(initialResources);
    }
  }, [initialResources]);

  const filteredResources = resources.filter((resource) => {
    if (activeType !== "all" && resource.type !== activeType) return false;
    if (searchQuery && !resource.name.toLowerCase().includes(searchQuery.toLowerCase())) return false;
    return true;
  });

  const handleResourceClick = (resourceId) => {
    setExpandedResource(expandedResource === resourceId ? null : resourceId);
  };

  return (
    <div className="h-full flex flex-col bg-[#0a0c10]" data-testid="resources-view">
      {/* Search Bar */}
      <div className="p-4 border-b border-[rgba(255,255,255,0.08)]">
        <div className="relative">
          <svg
            className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-[#6b7280]"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="2"
          >
            <circle cx="11" cy="11" r="8" />
            <line x1="21" y1="21" x2="16.65" y2="16.65" />
          </svg>
          <Input
            data-testid="resource-search"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Search resources..."
            className="pl-10 bg-[#111318] border-[rgba(255,255,255,0.08)] text-[#f0f0f0] placeholder:text-[#6b7280]"
          />
        </div>
      </div>

      {/* Filter Tabs */}
      <div className="border-b border-[rgba(255,255,255,0.08)] overflow-x-auto">
        <div className="flex p-2 gap-1 min-w-max">
          {RESOURCE_TYPES.map((type) => (
            <button
              key={type.id}
              data-testid={`filter-${type.id}`}
              onClick={() => setActiveType(type.id)}
              className={`
                px-3 py-1.5 text-xs font-medium rounded transition-colors
                ${activeType === type.id
                  ? "bg-[rgba(0,229,255,0.15)] text-[#00e5ff]"
                  : "text-[#6b7280] hover:text-[#9ca3af] hover:bg-[#181c24]"
                }
              `}
            >
              {type.label}
            </button>
          ))}
        </div>
      </div>

      {/* Resource List */}
      <ScrollArea className="flex-1">
        <div className="p-4 space-y-2">
          {isLoading ? (
            // Skeleton loading
            Array.from({ length: 5 }).map((_, i) => (
              <div key={i} className="p-3 bg-[#111318] rounded-md animate-pulse">
                <div className="flex items-start gap-3">
                  <div className="w-16 h-5 bg-[#181c24] rounded" />
                  <div className="flex-1">
                    <div className="w-3/4 h-4 bg-[#181c24] rounded mb-2" />
                    <div className="w-1/2 h-3 bg-[#181c24] rounded" />
                  </div>
                </div>
              </div>
            ))
          ) : filteredResources.length === 0 ? (
            <div className="text-center py-12 text-[#6b7280]">
              <p className="text-sm">No resources found</p>
              {searchQuery && (
                <p className="text-xs mt-1">Try adjusting your search or filters</p>
              )}
            </div>
          ) : (
            filteredResources.map((resource) => {
              const typeStyle = TYPE_COLORS[resource.type] || { bg: "bg-[#181c24]", text: "text-[#9ca3af]" };
              const isExpanded = expandedResource === resource.id;

              return (
                <div
                  key={resource.id}
                  data-testid={`resource-${resource.id}`}
                  onClick={() => handleResourceClick(resource.id)}
                  className={`
                    p-3 bg-[#111318] border border-[rgba(255,255,255,0.08)] rounded-md cursor-pointer
                    transition-colors hover:bg-[#181c24]
                    ${isExpanded ? "border-[rgba(255,255,255,0.16)]" : ""}
                  `}
                >
                  {/* Compact Row */}
                  <div className="flex items-start gap-3">
                    <Badge
                      variant="outline"
                      className={`text-[10px] uppercase shrink-0 ${typeStyle.bg} ${typeStyle.text} border-none`}
                    >
                      {resource.type}
                    </Badge>
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2">
                        <p className="text-sm font-medium text-[#f0f0f0] truncate">
                          {resource.name}
                        </p>
                        {resource.verified && (
                          <span className="w-1.5 h-1.5 rounded-full bg-[#00d26a] shrink-0" title="Verified" />
                        )}
                      </div>
                      <div className="flex items-center gap-3 mt-1 text-[10px] text-[#6b7280]">
                        {resource.hours && <span>{resource.hours}</span>}
                      </div>
                    </div>
                    <svg
                      className={`w-4 h-4 text-[#6b7280] transition-transform ${isExpanded ? "rotate-180" : ""}`}
                      viewBox="0 0 24 24"
                      fill="none"
                      stroke="currentColor"
                      strokeWidth="2"
                    >
                      <polyline points="6 9 12 15 18 9" />
                    </svg>
                  </div>

                  {/* Expanded Details */}
                  {isExpanded && (
                    <div className="mt-3 pt-3 border-t border-[rgba(255,255,255,0.08)] space-y-2 text-xs panel-expand">
                      {resource.contact && (
                        <div>
                          <span className="text-[#6b7280]">Contact: </span>
                          <a
                            href={`tel:${resource.contact}`}
                            className="text-[#00e5ff] hover:underline"
                            onClick={(e) => e.stopPropagation()}
                          >
                            {resource.contact}
                          </a>
                        </div>
                      )}
                      <div>
                        <span className="text-[#6b7280]">Coordinates: </span>
                        <button
                          onClick={(e) => {
                            e.stopPropagation();
                            navigator.clipboard.writeText(`${resource.lat}, ${resource.lng}`);
                          }}
                          className="text-[#00e5ff] hover:underline"
                        >
                          {resource.lat.toFixed(4)}, {resource.lng.toFixed(4)}
                        </button>
                      </div>
                      {resource.services && resource.services.length > 0 && (
                        <div>
                          <span className="text-[#6b7280]">Services: </span>
                          <div className="flex flex-wrap gap-1 mt-1">
                            {resource.services.map((service, i) => (
                              <span
                                key={i}
                                className="px-1.5 py-0.5 bg-[#181c24] text-[#9ca3af] rounded text-[10px]"
                              >
                                {service}
                              </span>
                            ))}
                          </div>
                        </div>
                      )}
                    </div>
                  )}
                </div>
              );
            })
          )}
        </div>
      </ScrollArea>
    </div>
  );
};
