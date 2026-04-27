import React, { useState } from "react";
import { ChevronRight, ChevronDown, BookOpen, Swords, Shield, Target, Zap, FlaskConical } from "lucide-react";

export interface ArtifactRow {
  id: string;
  icon: "problem" | "adjust" | "risk" | "sword" | "shield" | "target" | "speed" | "flask";
  label: string;
  body: string;
}

export interface ArtifactData {
  type: "strategy" | "species" | "calc";
  title: string;
  rows: ArtifactRow[];
  expandLabel?: string;
}

const ICON_MAP = {
  problem: (
    <svg width="20" height="20" viewBox="0 0 20 20" fill="none">
      <circle cx="10" cy="10" r="9" fill="#171717" />
      <text x="10" y="15" textAnchor="middle" fill="#F7CF45" fontSize="12" fontWeight="700">?</text>
    </svg>
  ),
  adjust: (
    <svg width="20" height="20" viewBox="0 0 20 20" fill="none">
      <circle cx="10" cy="10" r="9" fill="#171717" />
      <circle cx="10" cy="10" r="3" fill="#F7CF45" />
      <line x1="10" y1="2" x2="10" y2="5" stroke="#F7CF45" strokeWidth="1.8" strokeLinecap="round" />
      <line x1="10" y1="15" x2="10" y2="18" stroke="#F7CF45" strokeWidth="1.8" strokeLinecap="round" />
      <line x1="2" y1="10" x2="5" y2="10" stroke="#F7CF45" strokeWidth="1.8" strokeLinecap="round" />
      <line x1="15" y1="10" x2="18" y2="10" stroke="#F7CF45" strokeWidth="1.8" strokeLinecap="round" />
    </svg>
  ),
  risk: (
    <svg width="20" height="20" viewBox="0 0 20 20" fill="none">
      <path d="M10 2 L18 17 L2 17 Z" fill="#171717" stroke="#171717" strokeWidth="1" strokeLinejoin="round" />
      <rect x="9" y="9" width="2" height="4" rx="1" fill="#F7CF45" />
      <circle cx="10" cy="15" r="1" fill="#F7CF45" />
    </svg>
  ),
  sword: (
    <svg width="20" height="20" viewBox="0 0 20 20" fill="none">
      <circle cx="10" cy="10" r="9" fill="#B83A4B" />
      <path d="M10 3 L13 10 L10 17 L7 10 Z" fill="white" opacity="0.9" />
      <rect x="6" y="9" width="8" height="2" rx="1" fill="white" opacity="0.9" />
    </svg>
  ),
  shield: (
    <svg width="20" height="20" viewBox="0 0 20 20" fill="none">
      <circle cx="10" cy="10" r="9" fill="#65B96A" />
      <path d="M10 4 L15 6.5 L15 11.5 Q15 15.5 10 18 Q5 15.5 5 11.5 L5 6.5 Z" fill="white" opacity="0.9" />
    </svg>
  ),
  target: (
    <svg width="20" height="20" viewBox="0 0 20 20" fill="none">
      <circle cx="10" cy="10" r="9" fill="#4B8FD8" />
      <circle cx="10" cy="10" r="5.5" fill="none" stroke="white" strokeWidth="1.5" />
      <circle cx="10" cy="10" r="2" fill="white" />
    </svg>
  ),
  speed: (
    <svg width="20" height="20" viewBox="0 0 20 20" fill="none">
      <circle cx="10" cy="10" r="9" fill="#D8892E" />
      <path d="M7 10 L13 6 L12 10 L16 10 L10 15 L11 10 Z" fill="white" />
    </svg>
  ),
  flask: (
    <svg width="20" height="20" viewBox="0 0 20 20" fill="none">
      <circle cx="10" cy="10" r="9" fill="#7B5FC8" />
      <path d="M8 4 L8 9 L5 15 L15 15 L12 9 L12 4 Z" fill="white" opacity="0.85" />
      <rect x="7" y="4" width="6" height="1.5" rx="0.75" fill="white" />
    </svg>
  ),
};

export function ArtifactCard({ data }: { data: ArtifactData }) {
  const [expanded, setExpanded] = useState(true);

  return (
    <div
      style={{
        border: "2.5px solid #171717",
        borderRadius: 12,
        overflow: "hidden",
        boxShadow: "0 5px 0 rgba(17,17,17,0.18)",
        marginTop: 8,
      }}
    >
      {/* Yellow header strip */}
      <div
        style={{
          background: "#F7CF45",
          padding: "9px 12px",
          display: "flex",
          alignItems: "center",
          gap: 8,
          borderBottom: "2px solid #171717",
        }}
      >
        <div
          style={{
            width: 28,
            height: 28,
            background: "#171717",
            borderRadius: 6,
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
          }}
        >
          <BookOpen size={15} color="#F7CF45" strokeWidth={2.5} />
        </div>
        <span
          style={{
            fontWeight: 800,
            fontSize: 15,
            color: "#171717",
            letterSpacing: "-0.2px",
            flex: 1,
          }}
        >
          {data.title}
        </span>
        <button
          onClick={() => setExpanded((v) => !v)}
          style={{ background: "none", border: "none", cursor: "pointer", padding: 2 }}
        >
          {expanded ? (
            <ChevronDown size={16} color="#171717" />
          ) : (
            <ChevronRight size={16} color="#171717" />
          )}
        </button>
      </div>

      {/* Body */}
      {expanded && (
        <div style={{ background: "#FFF8E8", padding: "10px 12px" }}>
          {data.rows.map((row, i) => (
            <div
              key={row.id}
              style={{
                display: "flex",
                gap: 10,
                alignItems: "flex-start",
                paddingTop: i > 0 ? 9 : 0,
                paddingBottom: 9,
                borderBottom: i < data.rows.length - 1 ? "1px solid rgba(23,23,23,0.10)" : "none",
              }}
            >
              <div style={{ flexShrink: 0, marginTop: 1 }}>{ICON_MAP[row.icon]}</div>
              <div>
                <div style={{ fontWeight: 700, fontSize: 13, color: "#171717", marginBottom: 2 }}>
                  {row.label}
                </div>
                <div style={{ fontSize: 12.5, color: "#4A4A42", lineHeight: 1.5 }}>{row.body}</div>
              </div>
            </div>
          ))}
          {data.expandLabel && (
            <button
              style={{
                width: "100%",
                background: "none",
                border: "none",
                padding: "8px 0 2px",
                display: "flex",
                alignItems: "center",
                justifyContent: "space-between",
                cursor: "pointer",
                fontSize: 12.5,
                color: "#4B8FD8",
                fontWeight: 600,
              }}
            >
              {data.expandLabel}
              <ChevronRight size={14} color="#4B8FD8" />
            </button>
          )}
        </div>
      )}
    </div>
  );
}
