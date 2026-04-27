import React, { useRef, useState } from "react";
import { motion, AnimatePresence } from "motion/react";
import { Eye, EyeOff, X, AlertTriangle, ChevronDown, Cpu } from "lucide-react";

interface SettingsDrawerProps {
  open: boolean;
  onOpen: () => void;
  onClose: () => void;
  personaLabel: string;
}

export function SettingsDrawer({ open, onOpen, onClose, personaLabel }: SettingsDrawerProps) {
  const [apiKey, setApiKey] = useState("");
  const [revealed, setRevealed] = useState(false);
  const [provider, setProvider] = useState("openai");
  const [model, setModel] = useState("gpt-4o");
  const [endpoint, setEndpoint] = useState("");
  const [dragOffset, setDragOffset] = useState(0);
  const [dragging, setDragging] = useState(false);
  const dragStartXRef = useRef(0);
  const dragOffsetRef = useRef(0);
  const dragMovedRef = useRef(false);

  const inputStyle: React.CSSProperties = {
    width: "100%",
    background: "#FFFDF3",
    border: "2px solid rgba(23,23,23,0.18)",
    borderRadius: 10,
    padding: "9px 12px",
    fontSize: 13.5,
    color: "#171717",
    outline: "none",
    boxSizing: "border-box",
    fontFamily: "inherit",
  };

  const labelStyle: React.CSSProperties = {
    fontSize: 11.5,
    fontWeight: 700,
    color: "#2D2D2A",
    letterSpacing: "0.5px",
    textTransform: "uppercase",
    marginBottom: 5,
    display: "block",
  };

  const sectionStyle: React.CSSProperties = {
    marginBottom: 20,
  };

  return (
    <div style={{ position: "absolute", inset: 0, zIndex: 40, pointerEvents: "none" }}>
      <AnimatePresence>
        {open && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            transition={{ duration: 0.2 }}
            onClick={onClose}
            style={{
              position: "absolute",
              inset: 0,
              background: "rgba(17,17,17,0.28)",
              zIndex: 40,
              backdropFilter: "blur(1px)",
              pointerEvents: "auto",
            }}
          />
        )}
      </AnimatePresence>

      {/* Drawer rail: panel and pull handle move as one object. */}
      <div
        style={{
          position: "absolute",
          top: 0,
          right: 0,
          bottom: 0,
          width: "88%",
          zIndex: 45,
          pointerEvents: "auto",
          touchAction: "pan-y",
          transform: `translate3d(calc(${open ? "0%" : "100%"} + ${dragOffset}px), 0, 0)`,
          transition: dragging ? "none" : "transform 360ms cubic-bezier(0.22, 1, 0.36, 1)",
          willChange: "transform",
        }}
      >
        <button
          aria-label={open ? "关闭设置" : "打开设置"}
          onPointerDown={(event) => {
            dragStartXRef.current = event.clientX;
            dragMovedRef.current = false;
            setDragging(true);
            event.currentTarget.setPointerCapture(event.pointerId);
          }}
          onPointerMove={(event) => {
            if (!dragging) return;
            const delta = event.clientX - dragStartXRef.current;
            if (Math.abs(delta) > 2) {
              dragMovedRef.current = true;
            }
            const nextOffset = open
              ? Math.max(0, Math.min(360, delta))
              : Math.min(0, Math.max(-360, delta));
            dragOffsetRef.current = nextOffset;
            setDragOffset(nextOffset);
          }}
          onPointerUp={() => {
            if (!open && dragOffsetRef.current < -34) {
              onOpen();
            }
            if (open && dragOffsetRef.current > 34) {
              onClose();
            }
            setDragging(false);
            dragOffsetRef.current = 0;
            setDragOffset(0);
            window.setTimeout(() => {
              dragMovedRef.current = false;
            }, 0);
          }}
          onPointerCancel={() => {
            setDragging(false);
            dragOffsetRef.current = 0;
            setDragOffset(0);
            window.setTimeout(() => {
              dragMovedRef.current = false;
            }, 0);
          }}
          onClick={() => {
            if (dragMovedRef.current) return;
            if (open) {
              onClose();
            } else {
              onOpen();
            }
          }}
          style={{
            position: "absolute",
            left: -22,
            top: "50%",
            transform: "translateY(-50%)",
            width: 22,
            height: 58,
            background: "linear-gradient(180deg, #F7CF45 0%, #E7B72C 100%)",
            border: "3px solid #171717",
            borderRight: "none",
            borderRadius: "12px 0 0 12px",
            cursor: "pointer",
            display: "flex",
            flexDirection: "column",
            alignItems: "center",
            justifyContent: "center",
            gap: 4,
            zIndex: 2,
            boxShadow: open
              ? "-4px 0 0 rgba(17,17,17,0.08)"
              : "-2px 0 0 rgba(255,255,255,0.18)",
            touchAction: "none",
          }}
        >
          {[0, 1, 2].map((i) => (
            <div
              key={i}
              style={{
                width: 4,
                height: 4,
                borderRadius: 999,
                background: "#171717",
              }}
            />
          ))}
        </button>

        {/* Drawer panel */}
        <div
            style={{
              position: "absolute",
              top: 0,
              right: 0,
              bottom: 0,
              width: "100%",
              background: "#FFF8E8",
              border: "2.5px solid #171717",
              borderRight: "none",
              borderTopLeftRadius: 22,
              borderBottomLeftRadius: 22,
              zIndex: 45,
              overflowY: "auto",
              boxShadow: "0 18px 60px rgba(17,17,17,0.24)",
              display: "flex",
              flexDirection: "column",
              pointerEvents: open ? "auto" : "none",
            }}
          >
            {/* Header */}
            <div
              style={{
                padding: "18px 18px 14px",
                borderBottom: "2px solid rgba(23,23,23,0.12)",
                display: "flex",
                alignItems: "center",
                background: "#F7CF45",
                flexShrink: 0,
              }}
            >
              <div
                style={{
                  fontFamily: "'Nunito', sans-serif",
                  fontWeight: 900,
                  fontSize: 19,
                  color: "#171717",
                  letterSpacing: "-0.5px",
                }}
              >
                设置
              </div>
            </div>

            {/* Content */}
            <div style={{ padding: "18px 18px", flex: 1 }}>
              {/* Security warning */}
              <div
                style={{
                  background: "rgba(216,137,46,0.10)",
                  border: "2px solid rgba(216,137,46,0.4)",
                  borderRadius: 10,
                  padding: "10px 12px",
                  marginBottom: 20,
                  display: "flex",
                  gap: 9,
                }}
              >
                <AlertTriangle size={15} color="#D8892E" style={{ flexShrink: 0, marginTop: 2 }} />
                <div>
                  <div style={{ fontSize: 12, fontWeight: 700, color: "#D8892E", marginBottom: 3 }}>
                    API 密钥安全提示
                  </div>
                  <div style={{ fontSize: 11.5, color: "#5A4A2A", lineHeight: 1.5 }}>
                    你的 API Key 由你自己管理，仅限本次会话使用。请勿截图或粘贴到聊天中分享。
                  </div>
                </div>
              </div>

              {/* API Key */}
              <div style={sectionStyle}>
                <label style={labelStyle}>API 密钥</label>
                <div style={{ position: "relative" }}>
                  <input
                    type={revealed ? "text" : "password"}
                    value={apiKey}
                    onChange={(e) => setApiKey(e.target.value)}
                    placeholder="sk-..."
                    style={{ ...inputStyle, paddingRight: 76 }}
                  />
                  <div
                    style={{
                      position: "absolute",
                      right: 8,
                      top: "50%",
                      transform: "translateY(-50%)",
                      display: "flex",
                      gap: 4,
                    }}
                  >
                    <button
                      onClick={() => setRevealed((v) => !v)}
                      style={{
                        background: "none",
                        border: "none",
                        cursor: "pointer",
                        padding: 4,
                        color: "#2D2D2A",
                      }}
                    >
                      {revealed ? <EyeOff size={14} /> : <Eye size={14} />}
                    </button>
                    {apiKey && (
                      <button
                        onClick={() => setApiKey("")}
                        style={{
                          background: "none",
                          border: "none",
                          cursor: "pointer",
                          padding: 4,
                          color: "#B83A4B",
                        }}
                      >
                        <X size={14} />
                      </button>
                    )}
                  </div>
                </div>
                <div style={{ fontSize: 11, color: "#8A8070", marginTop: 5, lineHeight: 1.5 }}>
                  当前为内存存储，刷新后失效。
                </div>
              </div>

              {/* Provider */}
              <div style={sectionStyle}>
                <label style={labelStyle}>模型提供商</label>
                <div style={{ position: "relative" }}>
                  <select
                    value={provider}
                    onChange={(e) => setProvider(e.target.value)}
                    style={{
                      ...inputStyle,
                      appearance: "none",
                      paddingRight: 32,
                      cursor: "pointer",
                    }}
                  >
                    <option value="openai">OpenAI</option>
                    <option value="anthropic">Anthropic</option>
                    <option value="gemini">Google Gemini</option>
                  </select>
                  <ChevronDown
                    size={14}
                    color="#2D2D2A"
                    style={{ position: "absolute", right: 12, top: "50%", transform: "translateY(-50%)", pointerEvents: "none" }}
                  />
                </div>
              </div>

              {/* Model */}
              <div style={sectionStyle}>
                <label style={labelStyle}>模型</label>
                <input
                  type="text"
                  value={model}
                  onChange={(e) => setModel(e.target.value)}
                  placeholder="gpt-4o"
                  style={inputStyle}
                />
              </div>

              {/* Endpoint */}
              <div style={sectionStyle}>
                <label style={labelStyle}>接入点（可选）</label>
                <input
                  type="text"
                  value={endpoint}
                  onChange={(e) => setEndpoint(e.target.value)}
                  placeholder="https://api.openai.com/v1"
                  style={inputStyle}
                />
                <div style={{ fontSize: 11, color: "#8A8070", marginTop: 5, lineHeight: 1.5 }}>
                  仅用于兼容代理网关或 OpenAI-compatible 云端服务。
                </div>
              </div>

              {/* Current persona section */}
              <div
                style={{
                  background: "#FFFDF3",
                  border: "2px solid rgba(23,23,23,0.12)",
                  borderRadius: 12,
                  padding: "12px 14px",
                  marginBottom: 20,
                }}
              >
                <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 6 }}>
                  <Cpu size={14} color="#171717" />
                  <span style={{ fontSize: 12, fontWeight: 700, color: "#171717", textTransform: "uppercase", letterSpacing: "0.4px" }}>
                    当前人格
                  </span>
                </div>
                <div style={{ fontSize: 14, fontWeight: 700, color: "#171717" }}>{personaLabel}</div>
                <div style={{ fontSize: 11.5, color: "#6A6A5A", marginTop: 3 }}>
                  长按聊天头像可以切换人格
                </div>
              </div>

              {/* Save button */}
              <button
                style={{
                  width: "100%",
                  background: "#F7CF45",
                  border: "2.5px solid #171717",
                  borderRadius: 14,
                  padding: "12px 0",
                  fontSize: 15,
                  fontWeight: 800,
                  color: "#171717",
                  cursor: "pointer",
                  boxShadow: "0 4px 0 rgba(17,17,17,0.2)",
                  fontFamily: "'Nunito', sans-serif",
                }}
              >
                保存设置
              </button>
            </div>
        </div>
      </div>
    </div>
  );
}
