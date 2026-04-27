import React, { useRef, useState } from "react";
import { SendHorizonal } from "lucide-react";

interface PromptComposerProps {
  onSend: (text: string) => void;
  disabled?: boolean;
}

export function PromptComposer({ onSend, disabled }: PromptComposerProps) {
  const [text, setText] = useState("");
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  const handleSend = () => {
    const trimmed = text.trim();
    if (!trimmed || disabled) return;
    onSend(trimmed);
    setText("");
    if (textareaRef.current) {
      textareaRef.current.style.height = "auto";
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const handleInput = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    setText(e.target.value);
    const el = textareaRef.current;
    if (el) {
      el.style.height = "auto";
      el.style.height = Math.min(el.scrollHeight, 100) + "px";
    }
  };

  return (
    <div
      style={{
        padding: "0 14px 7px",
        background: "transparent",
        flexShrink: 0,
        position: "relative",
        zIndex: 2,
      }}
    >
      <div
        style={{
          display: "flex",
          alignItems: "flex-end",
          gap: 9,
        }}
      >
        {/* Input pill */}
        <div
          style={{
            flex: 1,
            background: "#FFF8E8",
            border: "2.5px solid #171717",
            borderRadius: 22,
            padding: "8px 14px",
            display: "flex",
            alignItems: "flex-end",
            boxShadow: "0 2px 6px rgba(17,17,17,0.08)",
          }}
        >
          <textarea
            ref={textareaRef}
            value={text}
            onChange={handleInput}
            onKeyDown={handleKeyDown}
            placeholder="问问 Roco..."
            rows={1}
            style={{
              flex: 1,
              background: "transparent",
              border: "none",
              outline: "none",
              resize: "none",
              fontSize: 15,
              color: "#171717",
              lineHeight: "22px",
              fontFamily: "inherit",
              maxHeight: 100,
              overflowY: "auto",
              paddingRight: 4,
            }}
          />
        </div>

        {/* Send button */}
        <button
          onClick={handleSend}
          disabled={!text.trim() || disabled}
          style={{
            width: 44,
            height: 44,
            borderRadius: 999,
            background: text.trim() && !disabled ? "#171717" : "rgba(23,23,23,0.25)",
            border: "2.5px solid #171717",
            cursor: text.trim() && !disabled ? "pointer" : "not-allowed",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            flexShrink: 0,
            transition: "background 0.2s, transform 0.1s",
            boxShadow: text.trim() && !disabled ? "0 3px 0 rgba(17,17,17,0.35)" : "none",
            transform: "translateY(0)",
          }}
          onMouseDown={(e) => {
            if (text.trim() && !disabled) {
              (e.currentTarget as HTMLElement).style.transform = "translateY(2px)";
              (e.currentTarget as HTMLElement).style.boxShadow = "none";
            }
          }}
          onMouseUp={(e) => {
            (e.currentTarget as HTMLElement).style.transform = "translateY(0)";
            (e.currentTarget as HTMLElement).style.boxShadow = text.trim() && !disabled ? "0 3px 0 rgba(17,17,17,0.35)" : "none";
          }}
        >
          <SendHorizonal
            size={17}
            color={text.trim() && !disabled ? "#F7CF45" : "#FFF8E8"}
            strokeWidth={2.5}
          />
        </button>
      </div>
    </div>
  );
}
