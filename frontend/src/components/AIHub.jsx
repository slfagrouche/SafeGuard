import React, { useState, useRef, useEffect, useCallback } from "react";
import axios from "axios";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { toast } from "sonner";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

// Agent definitions
const AGENTS = [
  {
    id: "general",
    name: "General Help",
    icon: "◈",
    description: "Broad crisis guidance and support",
    color: "#00e5ff",
  },
  {
    id: "medical",
    name: "Medical",
    icon: "✚",
    description: "First aid, triage, referral",
    color: "#00d26a",
  },
  {
    id: "recommendation",
    name: "Recommendations",
    icon: "◎",
    description: "Nearby resources & routes",
    color: "#ffb800",
  },
  {
    id: "situational",
    name: "Situational Intel",
    icon: "⊕",
    description: "Live news, ground reports",
    color: "#3b82f6",
  },
];

// Offline packs
const OFFLINE_PACKS = [
  { id: "first_aid", name: "First Aid Guide", size: "~100 KB" },
  { id: "emergency_procedures", name: "Emergency Procedures", size: "~8 KB" },
  { id: "resource_directory", name: "Resource Directory", size: "~50 KB" },
];

export const AIHub = () => {
  const [selectedAgent, setSelectedAgent] = useState(AGENTS[0]);
  const [messages, setMessages] = useState([]);
  const [inputValue, setInputValue] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [currentTaskId, setCurrentTaskId] = useState(null);
  const [toolCalls, setToolCalls] = useState([]);
  const [sessionId] = useState(() => `session-${Date.now()}`);
  const [downloadedPacks, setDownloadedPacks] = useState([]);
  const [downloadingPack, setDownloadingPack] = useState(null);
  const messagesEndRef = useRef(null);
  const pollIntervalRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  // Cleanup polling on unmount
  useEffect(() => {
    return () => {
      if (pollIntervalRef.current) {
        clearInterval(pollIntervalRef.current);
      }
    };
  }, []);

  const pollForResponse = useCallback(async (taskId) => {
    try {
      const response = await axios.get(`${API}/ai/status/${taskId}/`);
      const data = response.data;

      if (data.tool_calls && data.tool_calls.length > 0) {
        setToolCalls(data.tool_calls);
      }

      if (data.status === "success") {
        clearInterval(pollIntervalRef.current);
        setMessages((prev) => [
          ...prev,
          {
            role: "assistant",
            content: data.content,
            agent: selectedAgent,
            toolCalls: data.tool_calls || [],
          },
        ]);
        setIsLoading(false);
        setCurrentTaskId(null);
        setToolCalls([]);
      } else if (data.status === "error") {
        clearInterval(pollIntervalRef.current);
        setMessages((prev) => [
          ...prev,
          {
            role: "assistant",
            content: data.content || "An error occurred. Please try again.",
            agent: selectedAgent,
            isError: true,
          },
        ]);
        setIsLoading(false);
        setCurrentTaskId(null);
        setToolCalls([]);
      }
    } catch (error) {
      console.error("Poll error:", error);
    }
  }, [selectedAgent]);

  useEffect(() => {
    if (currentTaskId && isLoading) {
      pollIntervalRef.current = setInterval(() => {
        pollForResponse(currentTaskId);
      }, 2000);

      return () => {
        if (pollIntervalRef.current) {
          clearInterval(pollIntervalRef.current);
        }
      };
    }
  }, [currentTaskId, isLoading, pollForResponse]);

  const handleSendMessage = async () => {
    if (!inputValue.trim() || isLoading) return;

    const userMessage = inputValue.trim();
    setInputValue("");
    setMessages((prev) => [...prev, { role: "user", content: userMessage }]);
    setIsLoading(true);
    setToolCalls([]);

    try {
      const response = await axios.post(`${API}/ai/chat/`, {
        agent_type: selectedAgent.id,
        message: userMessage,
        session_id: sessionId,
      });

      if (response.data.task_id) {
        setCurrentTaskId(response.data.task_id);
      }
    } catch (error) {
      console.error("Chat error:", error);
      setMessages((prev) => [
        ...prev,
        {
          role: "assistant",
          content: "Sorry, I encountered an error. Please try again.",
          agent: selectedAgent,
          isError: true,
        },
      ]);
      setIsLoading(false);
    }
  };

  const handleKeyPress = (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  const handleAgentChange = (agent) => {
    setSelectedAgent(agent);
    setMessages([]);
    setToolCalls([]);
  };

  const handleDownloadPack = async (pack) => {
    setDownloadingPack(pack.id);
    try {
      const res = await axios.get(`${API}/offline/packs/${pack.id}`);
      const content = res.data.content;
      
      // Create downloadable blob
      const blob = new Blob([content], { type: "text/markdown" });
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `${pack.id}.md`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
      
      setDownloadedPacks((prev) => [...prev, pack.id]);
      toast.success(`${pack.name} downloaded`);
    } catch (e) {
      toast.error(`Failed to download ${pack.name}`);
    }
    setDownloadingPack(null);
  };

  // Simple markdown-like rendering
  const renderContent = (content) => {
    if (!content) return null;
    
    // Split by code blocks
    const parts = content.split(/(```[\s\S]*?```)/g);
    
    return parts.map((part, i) => {
      if (part.startsWith("```")) {
        const code = part.replace(/```\w*\n?/g, "").replace(/```$/, "");
        return (
          <pre key={i} className="bg-[#181c24] p-2 rounded text-xs overflow-x-auto my-2">
            <code>{code}</code>
          </pre>
        );
      }
      
      // Handle bold, lists, and headers
      const lines = part.split("\n").map((line, j) => {
        // Headers
        if (line.startsWith("### ")) {
          return <h4 key={j} className="font-bold text-sm mt-2">{line.slice(4)}</h4>;
        }
        if (line.startsWith("## ")) {
          return <h3 key={j} className="font-bold text-base mt-2">{line.slice(3)}</h3>;
        }
        if (line.startsWith("# ")) {
          return <h2 key={j} className="font-bold text-lg mt-2">{line.slice(2)}</h2>;
        }
        
        // Lists
        if (line.startsWith("- ") || line.startsWith("* ")) {
          return <li key={j} className="ml-4">{line.slice(2)}</li>;
        }
        if (/^\d+\.\s/.test(line)) {
          return <li key={j} className="ml-4 list-decimal">{line.replace(/^\d+\.\s/, "")}</li>;
        }
        
        // Bold
        const boldLine = line.replace(/\*\*(.*?)\*\*/g, "<strong>$1</strong>");
        
        if (line.trim() === "") return <br key={j} />;
        return <p key={j} dangerouslySetInnerHTML={{ __html: boldLine }} />;
      });
      
      return <div key={i}>{lines}</div>;
    });
  };

  return (
    <div className="h-full flex" data-testid="ai-hub">
      {/* Agent Selector - Desktop */}
      <aside className="hidden md:flex flex-col w-[260px] bg-[#111318] border-r border-[rgba(255,255,255,0.08)]">
        <div className="p-3 border-b border-[rgba(255,255,255,0.08)]">
          <h2 className="text-xs font-medium text-[#9ca3af] uppercase tracking-wider">
            AI Agents
          </h2>
        </div>

        <ScrollArea className="flex-1">
          <div className="p-2 space-y-1">
            {AGENTS.map((agent) => (
              <button
                key={agent.id}
                data-testid={`agent-${agent.id}`}
                onClick={() => handleAgentChange(agent)}
                className={`
                  relative w-full p-2 rounded text-left transition-colors
                  ${selectedAgent.id === agent.id 
                    ? "bg-[rgba(0,229,255,0.1)]" 
                    : "hover:bg-[#181c24]"
                  }
                `}
              >
                {selectedAgent.id === agent.id && (
                  <div className="absolute left-0 top-1/2 -translate-y-1/2 w-0.5 h-6 bg-[#00e5ff]" />
                )}
                <div className="flex items-start gap-2 pl-2">
                  <span 
                    className="text-lg" 
                    style={{ color: agent.color }}
                  >
                    {agent.icon}
                  </span>
                  <div>
                    <p className="text-xs font-medium text-[#f0f0f0]">{agent.name}</p>
                    <p className="text-[10px] text-[#6b7280]">{agent.description}</p>
                  </div>
                  <span className="ml-auto w-2 h-2 rounded-full bg-[#00d26a]" title="Online" />
                </div>
              </button>
            ))}
          </div>
        </ScrollArea>

        {/* Offline Packs */}
        <div className="border-t border-[rgba(255,255,255,0.08)] p-3">
          <h3 className="text-xs font-medium text-[#9ca3af] uppercase tracking-wider mb-2">
            Offline Packs
          </h3>
          <div className="space-y-2">
            {OFFLINE_PACKS.map((pack) => {
              const isDownloaded = downloadedPacks.includes(pack.id);
              const isDownloading = downloadingPack === pack.id;
              return (
                <div
                  key={pack.id}
                  className="flex items-center justify-between p-2 bg-[#181c24] rounded"
                >
                  <div>
                    <p className="text-xs text-[#f0f0f0]">{pack.name}</p>
                    <p className="text-[10px] text-[#6b7280]">{pack.size}</p>
                  </div>
                  {isDownloaded ? (
                    <span className="flex items-center gap-1 text-[10px] text-[#00d26a]">
                      <span className="w-1.5 h-1.5 rounded-full bg-[#00d26a]" />
                      OFFLINE
                    </span>
                  ) : (
                    <button
                      onClick={() => handleDownloadPack(pack)}
                      disabled={isDownloading}
                      className="text-[10px] text-[#00e5ff] hover:underline disabled:opacity-50"
                    >
                      {isDownloading ? "..." : "DOWNLOAD"}
                    </button>
                  )}
                </div>
              );
            })}
          </div>
        </div>
      </aside>

      {/* Mobile Agent Selector */}
      <div className="md:hidden absolute top-0 left-0 right-0 z-10 bg-[#111318] border-b border-[rgba(255,255,255,0.08)] overflow-x-auto">
        <div className="flex p-2 gap-2">
          {AGENTS.map((agent) => (
            <button
              key={agent.id}
              onClick={() => handleAgentChange(agent)}
              className={`
                flex items-center gap-1.5 px-3 py-1.5 rounded whitespace-nowrap
                ${selectedAgent.id === agent.id 
                  ? "bg-[rgba(0,229,255,0.1)] text-[#00e5ff]" 
                  : "text-[#6b7280]"
                }
              `}
            >
              <span style={{ color: agent.color }}>{agent.icon}</span>
              <span className="text-xs">{agent.name}</span>
            </button>
          ))}
        </div>
      </div>

      {/* Chat Area */}
      <div className="flex-1 flex flex-col bg-[#0a0c10] pt-12 md:pt-0">
        {/* Messages */}
        <ScrollArea className="flex-1 p-4">
          <div className="space-y-4 max-w-2xl mx-auto">
            {messages.length === 0 && (
              <div className="text-center py-12">
                <span className="text-4xl" style={{ color: selectedAgent.color }}>
                  {selectedAgent.icon}
                </span>
                <h3 className="mt-4 text-lg font-semibold text-[#f0f0f0]">
                  {selectedAgent.name}
                </h3>
                <p className="mt-1 text-sm text-[#6b7280]">
                  {selectedAgent.description}
                </p>
                <p className="mt-4 text-xs text-[#6b7280]">
                  Type a message to begin
                </p>
              </div>
            )}

            {messages.map((message, index) => (
              <div
                key={index}
                data-testid={`message-${index}`}
                className={`flex ${message.role === "user" ? "justify-end" : "justify-start"}`}
              >
                {message.role === "assistant" && (
                  <span 
                    className="w-6 h-6 flex items-center justify-center mr-2 mt-1"
                    style={{ color: message.agent?.color || "#00e5ff" }}
                  >
                    {message.agent?.icon || "◈"}
                  </span>
                )}
                <div
                  className={`
                    max-w-[80%] p-3 rounded-md text-sm
                    ${message.role === "user" 
                      ? "bg-[#181c24] text-[#f0f0f0]" 
                      : message.isError 
                        ? "bg-[rgba(255,45,45,0.1)] text-[#ff2d2d]"
                        : "bg-[#111318] text-[#f0f0f0] border border-[rgba(255,255,255,0.08)]"
                    }
                  `}
                >
                  {message.role === "assistant" 
                    ? renderContent(message.content)
                    : message.content
                  }
                  {message.toolCalls && message.toolCalls.length > 0 && (
                    <div className="mt-2 flex flex-wrap gap-1">
                      {message.toolCalls.map((tool, i) => (
                        <span
                          key={i}
                          className="text-[10px] px-1.5 py-0.5 bg-[rgba(0,229,255,0.1)] text-[#00e5ff] rounded"
                        >
                          [{tool}]
                        </span>
                      ))}
                    </div>
                  )}
                </div>
              </div>
            ))}

            {/* Thinking State */}
            {isLoading && (
              <div className="flex justify-start">
                <span 
                  className="w-6 h-6 flex items-center justify-center mr-2 mt-1"
                  style={{ color: selectedAgent.color }}
                >
                  {selectedAgent.icon}
                </span>
                <div className="bg-[#111318] border border-[rgba(255,255,255,0.08)] p-3 rounded-md">
                  <span 
                    className="animate-thinking text-sm"
                    style={{ fontFamily: "'IBM Plex Mono', monospace" }}
                  >
                    ░░░
                  </span>
                  {toolCalls.length > 0 && (
                    <div className="mt-2 flex flex-wrap gap-1">
                      {toolCalls.map((tool, i) => (
                        <span
                          key={i}
                          className="text-[10px] px-1.5 py-0.5 bg-[rgba(0,229,255,0.1)] text-[#00e5ff] rounded"
                        >
                          [{tool}]
                        </span>
                      ))}
                    </div>
                  )}
                </div>
              </div>
            )}

            <div ref={messagesEndRef} />
          </div>
        </ScrollArea>

        {/* Emergency Connect Bar */}
        <div className="bg-[rgba(255,45,45,0.1)] border-t border-[#ff2d2d] p-3">
          <div className="flex items-center justify-between max-w-2xl mx-auto">
            <div className="flex items-center gap-2">
              <span className="w-2 h-2 rounded-full bg-[#ff2d2d] animate-critical-pulse" />
              <span className="text-xs font-medium text-[#ff2d2d] uppercase tracking-wider">
                Emergency Connect
              </span>
            </div>
            <Button
              data-testid="emergency-connect-btn"
              variant="outline"
              size="sm"
              className="text-[10px] h-7 border-[#ff2d2d] text-[#ff2d2d] hover:bg-[rgba(255,45,45,0.2)] hover:text-[#ff2d2d]"
              onClick={async () => {
                try {
                  const res = await axios.get(`${API}/emergency/regions/`);
                  const regions = res.data.regions || [];
                  const regionNames = regions.map(r => r.name).join(", ");
                  toast.info(`Emergency calling not configured. Available regions: ${regionNames}. Please call emergency services directly.`);
                } catch (e) {
                  toast.info("Emergency calling not configured. Please call emergency services directly.");
                }
              }}
            >
              CALL SERVICES
            </Button>
          </div>
        </div>

        {/* Input Area */}
        <div className="border-t border-[rgba(255,255,255,0.08)] p-4">
          <div className="max-w-2xl mx-auto flex gap-2">
            <Input
              data-testid="chat-input"
              value={inputValue}
              onChange={(e) => setInputValue(e.target.value)}
              onKeyPress={handleKeyPress}
              placeholder={`Message ${selectedAgent.name}...`}
              disabled={isLoading}
              className="flex-1 bg-[#111318] border-[rgba(255,255,255,0.08)] text-[#f0f0f0] placeholder:text-[#6b7280] focus:border-[#00e5ff]"
            />
            <Button
              data-testid="send-message-btn"
              onClick={handleSendMessage}
              disabled={isLoading || !inputValue.trim()}
              className="bg-[#00e5ff] text-black hover:bg-[#00c8e0] disabled:opacity-50"
            >
              <svg className="w-4 h-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <line x1="22" y1="2" x2="11" y2="13" />
                <polygon points="22 2 15 22 11 13 2 9 22 2" />
              </svg>
            </Button>
          </div>
        </div>
      </div>
    </div>
  );
};
