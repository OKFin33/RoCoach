import React, { useRef, useEffect, useState } from "react";
import { motion, AnimatePresence } from "motion/react";
import { AgentAvatar, UserAvatar } from "./AgentAvatar";
import { ArtifactCard, ArtifactData } from "./ArtifactCard";
import { PersonaWheel, PersonaOption } from "./PersonaWheel";
import { SettingsDrawer } from "./SettingsDrawer";
import { PromptComposer } from "./PromptComposer";
import { RefreshCcw, AlertCircle, ArrowLeft, Plus, Copy, WandSparkles, Trash2, Check, X } from "lucide-react";

// ─── Types ────────────────────────────────────────────────────────────────────

type MessageState = "sent" | "thinking" | "failed";

interface Message {
  id: string;
  role: "user" | "agent";
  text: string;
  state: MessageState;
  artifact?: ArtifactData;
  personaId?: string;
}

type MessageActionMenuState = {
  messageId: string;
  role: Message["role"];
  x: number;
  y: number;
  confirmDelete?: boolean;
};

// ─── Personas ─────────────────────────────────────────────────────────────────

const PERSONAS: PersonaOption[] = [
  {
    id: "you_know_who",
    label: "You know who",
    description: "黑衣人默认人格",
    category: "built_in",
    availability: "available",
    color: "#1A1A18",
  },
  {
    id: "ai_assistant",
    label: "默认AI助手",
    description: "直连用户 LLM",
    category: "default",
    availability: "available",
    initials: "AI",
    color: "#4B8FD8",
  },
  {
    id: "add",
    label: "添加人格",
    description: "创建入口",
    category: "add",
    availability: "available",
  },
];

// ─── Mock initial messages ─────────────────────────────────────────────────────

const STRATEGY_ARTIFACT: ArtifactData = {
  type: "strategy",
  title: "策略摘要",
  rows: [
    {
      id: "r1",
      icon: "problem",
      label: "核心问题",
      body: "输出不足，缺乏稳定的收割点。",
    },
    {
      id: "r2",
      icon: "adjust",
      label: "推荐调整",
      body: "替换弱输出位，补充穿透与控场。",
    },
    {
      id: "r3",
      icon: "risk",
      label: "风险点",
      body: "面对高速先手队时容错较低。",
    },
  ],
  expandLabel: "查看详细分析",
};

const INITIAL_MESSAGES: Message[] = [
  {
    id: "m1",
    role: "agent",
    text: "我先帮你拆一下阵容思路。",
    state: "sent",
  },
  {
    id: "m2",
    role: "user",
    text: "这套队伍怎么优化？",
    state: "sent",
  },
  {
    id: "m3",
    role: "agent",
    text: "好的，这是我的分析结果：",
    state: "sent",
    artifact: STRATEGY_ARTIFACT,
  },
  {
    id: "m4",
    role: "user",
    text: "明白了，感谢！",
    state: "sent",
  },
  {
    id: "m5",
    role: "agent",
    text: "不客气，有问题随时来问我。",
    state: "sent",
  },
];

// ─── Prompt suggestion chips ──────────────────────────────────────────────────

const PROMPT_CHIPS = [
  "这套队伍先手够用吗？",
  "推荐我几只穿透系精灵",
  "对战火系队有没有克制？",
];

// ─── Subcomponents ────────────────────────────────────────────────────────────

function MessageActionMenu({
  menu,
  canRewrite,
  onCopy,
  onRewrite,
  onRegenerate,
  onAskDelete,
  onConfirmDelete,
  onClose,
}: {
  menu: MessageActionMenuState;
  canRewrite: boolean;
  onCopy: () => void;
  onRewrite: () => void;
  onRegenerate: () => void;
  onAskDelete: () => void;
  onConfirmDelete: () => void;
  onClose: () => void;
}) {
  const isUser = menu.role === "user";
  const baseActions = [
    {
      label: "复制",
      icon: <Copy size={14} strokeWidth={2.5} />,
      tone: "neutral" as const,
      onClick: onCopy,
    },
    ...(isUser && !canRewrite
      ? []
      : [
          {
            label: isUser ? "改写" : "重新生成",
            icon: isUser ? (
              <WandSparkles size={14} strokeWidth={2.5} />
            ) : (
              <RefreshCcw size={14} strokeWidth={2.5} />
            ),
            tone: "neutral" as const,
            onClick: isUser ? onRewrite : onRegenerate,
          },
        ]),
    {
      label: "删除",
      icon: <Trash2 size={14} strokeWidth={2.5} />,
      tone: "danger" as const,
      onClick: onAskDelete,
    },
  ];

  const actions = menu.confirmDelete
    ? [
        {
          label: "确认删除",
          icon: <Trash2 size={14} strokeWidth={2.5} />,
          tone: "danger" as const,
          onClick: onConfirmDelete,
        },
        {
          label: "取消",
          icon: null,
          tone: "neutral" as const,
          onClick: onClose,
        },
      ]
    : baseActions;

  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.96, y: 4 }}
      animate={{ opacity: 1, scale: 1, y: 0 }}
      exit={{ opacity: 0, scale: 0.96, y: 4 }}
      transition={{ duration: 0.14 }}
      style={{
        position: "absolute",
        left: `clamp(12px, ${menu.x}px, calc(100% - 212px))`,
        top: `clamp(20px, ${menu.y}px, calc(100% - 66px))`,
        zIndex: 62,
        background: "#FFF8E8",
        border: "2.5px solid #171717",
        borderRadius: 14,
        boxShadow: "0 8px 0 rgba(17,17,17,0.16), 0 18px 36px rgba(17,17,17,0.22)",
        padding: 6,
        display: "flex",
        gap: 4,
      }}
      onPointerDown={(event) => event.stopPropagation()}
    >
      {actions.map((action) => (
        <button
          key={action.label}
          onClick={action.onClick}
          style={{
            minWidth: action.label === "确认删除" ? 78 : 54,
            height: 34,
            border: "none",
            borderRadius: 9,
            background: action.tone === "danger" ? "rgba(184,58,75,0.12)" : "transparent",
            color: action.tone === "danger" ? "#B83A4B" : "#171717",
            display: "inline-flex",
            alignItems: "center",
            justifyContent: "center",
            gap: 5,
            cursor: "pointer",
            fontFamily: "inherit",
            fontSize: 12.5,
            fontWeight: 800,
            whiteSpace: "nowrap",
          }}
        >
          {action.icon}
          {action.label}
        </button>
      ))}
    </motion.div>
  );
}

function SessionDivider({ label }: { label: string }) {
  return (
    <div
      style={{
        display: "flex",
        alignItems: "center",
        gap: 10,
        padding: "4px 0 8px",
      }}
    >
      <div style={{ flex: 1, height: 1, background: "rgba(23,23,23,0.10)" }} />
      <span
        style={{
          fontSize: 11,
          color: "#8A8070",
          fontWeight: 600,
          letterSpacing: "0.3px",
        }}
      >
        {label}
      </span>
      <div style={{ flex: 1, height: 1, background: "rgba(23,23,23,0.10)" }} />
    </div>
  );
}

function AgentBubble({
  message,
  thinking,
  onRetry,
  onAvatarLongPress,
  onMessageLongPress,
  ringColor = "neutral",
  avatarVariant = "you_know_who",
}: {
  message: Message;
  thinking?: boolean;
  onRetry?: () => void;
  onAvatarLongPress?: (anchor: { x: number; y: number }) => void;
  onMessageLongPress?: (message: Message, element: HTMLElement) => void;
  ringColor?: string;
  avatarVariant?: "you_know_who" | "ai_assistant";
}) {
  const messagePressTimer = useRef<number | undefined>(undefined);

  const startMessagePress = (event: React.PointerEvent<HTMLElement>) => {
    if (thinking) return;
    const element = event.currentTarget;
    window.clearTimeout(messagePressTimer.current);
    messagePressTimer.current = window.setTimeout(() => {
      onMessageLongPress?.(message, element);
    }, 430);
  };

  const cancelMessagePress = () => {
    window.clearTimeout(messagePressTimer.current);
  };

  const openMessageMenu = (event: React.MouseEvent<HTMLElement>) => {
    event.preventDefault();
    if (thinking) return;
    onMessageLongPress?.(message, event.currentTarget);
  };

  const agentBubbleStyle = {
    position: "relative" as const,
    background: "linear-gradient(180deg, #FFFDF5 0%, #FFF8E9 100%)",
    border: "2.6px solid #171717",
    borderRadius: "17px 17px 17px 6px",
    padding: "10px 14px",
    boxShadow: "0 3px 0 rgba(17,17,17,0.12), inset 0 1px 0 rgba(255,255,255,0.8)",
  };

  const agentTail = (
    <div
      aria-hidden
      style={{
        position: "absolute",
        left: -7,
        bottom: 9,
        width: 11,
        height: 12,
        background: "#FFF9EA",
        borderLeft: "2.6px solid #171717",
        borderBottom: "2.6px solid #171717",
        transform: "skewX(-26deg) rotate(8deg)",
        borderRadius: "0 0 0 3px",
      }}
    />
  );

  return (
    <motion.div
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ type: "spring", stiffness: 340, damping: 28 }}
      style={{ display: "flex", flexDirection: "column", alignItems: "flex-start", maxWidth: "88%" }}
    >
      <div style={{ display: "flex", gap: 8, alignItems: "flex-end", maxWidth: "100%" }}>
        {/* Avatar anchors to the spoken bubble, not to follow-up artifact cards. */}
        <AgentAvatar
          size={34}
          ringColor={thinking ? "blue" : ringColor}
          variant={avatarVariant}
          thinking={thinking}
          onLongPress={onAvatarLongPress}
          showBadge={false}
        />

        {thinking ? (
          <div
            style={{
              ...agentBubbleStyle,
              padding: "10px 14px",
              display: "inline-flex",
              alignItems: "center",
              gap: 5,
            }}
          >
            {agentTail}
            {[0, 1, 2].map((i) => (
              <motion.div
                key={i}
                animate={{ y: [0, -5, 0] }}
                transition={{ repeat: Infinity, duration: 0.8, delay: i * 0.18 }}
                style={{
                  width: 7,
                  height: 7,
                  borderRadius: 999,
                  background: "#4B8FD8",
                }}
              />
            ))}
          </div>
        ) : message.state === "failed" ? (
          <div>
            <div
              onPointerDown={startMessagePress}
              onPointerUp={cancelMessagePress}
              onPointerCancel={cancelMessagePress}
              onPointerLeave={cancelMessagePress}
              onContextMenu={openMessageMenu}
              style={{
                ...agentBubbleStyle,
                border: "2.6px solid #B83A4B",
              }}
            >
              {agentTail}
              <div
                style={{
                  display: "flex",
                  alignItems: "center",
                  gap: 6,
                  marginBottom: 4,
                }}
              >
                <AlertCircle size={13} color="#B83A4B" />
                <span
                  style={{ fontSize: 12, fontWeight: 700, color: "#B83A4B" }}
                >
                  回复失败
                </span>
              </div>
              <p
                style={{
                  fontSize: 13,
                  color: "#4A4A42",
                  margin: 0,
                  lineHeight: 1.5,
                }}
              >
                连接或模型请求出错，请重试。
              </p>
            </div>
            <button
              onClick={onRetry}
              style={{
                marginTop: 6,
                display: "flex",
                alignItems: "center",
                gap: 5,
                background: "#F7CF45",
                border: "2px solid #171717",
                borderRadius: 20,
                padding: "5px 12px",
                cursor: "pointer",
                fontSize: 12,
                fontWeight: 700,
                color: "#171717",
                boxShadow: "0 2px 0 rgba(17,17,17,0.2)",
              }}
            >
              <RefreshCcw size={11} strokeWidth={2.5} />
              重试
            </button>
          </div>
        ) : (
          <div
            onPointerDown={startMessagePress}
            onPointerUp={cancelMessagePress}
            onPointerCancel={cancelMessagePress}
            onPointerLeave={cancelMessagePress}
            onContextMenu={openMessageMenu}
            style={{
              ...agentBubbleStyle,
            }}
          >
            {agentTail}
            <p
              style={{
                fontSize: 15,
                color: "#171717",
                margin: 0,
                lineHeight: "23px",
              }}
            >
              {message.text}
            </p>
          </div>
        )}
      </div>
      {!thinking && message.state !== "failed" && message.artifact && (
        <div style={{ marginLeft: 42, marginTop: 8, width: "calc(100% - 42px)" }}>
          <ArtifactCard data={message.artifact} />
        </div>
      )}
    </motion.div>
  );
}

function UserBubble({
  message,
  editing,
  onMessageLongPress,
  onSubmitEdit,
  onCancelEdit,
}: {
  message: Message;
  editing?: boolean;
  onMessageLongPress?: (message: Message, element: HTMLElement) => void;
  onSubmitEdit?: (messageId: string, text: string) => void;
  onCancelEdit?: () => void;
}) {
  const messagePressTimer = useRef<number | undefined>(undefined);
  const [editText, setEditText] = useState(message.text);
  const editTextareaRef = useRef<HTMLTextAreaElement>(null);

  useEffect(() => {
    setEditText(message.text);
  }, [message.text, editing]);

  useEffect(() => {
    if (!editing) return;
    requestAnimationFrame(() => {
      const el = editTextareaRef.current;
      if (!el) return;
      el.focus();
      el.setSelectionRange(el.value.length, el.value.length);
      el.style.height = "auto";
      el.style.height = Math.min(el.scrollHeight, 96) + "px";
    });
  }, [editing]);

  const startMessagePress = (event: React.PointerEvent<HTMLElement>) => {
    if (editing) return;
    const element = event.currentTarget;
    window.clearTimeout(messagePressTimer.current);
    messagePressTimer.current = window.setTimeout(() => {
      onMessageLongPress?.(message, element);
    }, 430);
  };

  const cancelMessagePress = () => {
    window.clearTimeout(messagePressTimer.current);
  };

  const openMessageMenu = (event: React.MouseEvent<HTMLElement>) => {
    event.preventDefault();
    if (editing) return;
    onMessageLongPress?.(message, event.currentTarget);
  };

  const submitEdit = () => {
    const trimmed = editText.trim();
    if (!trimmed) return;
    onSubmitEdit?.(message.id, trimmed);
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ type: "spring", stiffness: 340, damping: 28 }}
      style={{
        display: "flex",
        gap: 8,
        alignItems: "flex-end",
        justifyContent: "flex-end",
        maxWidth: "88%",
        alignSelf: "flex-end",
      }}
    >
      <div
        onPointerDown={startMessagePress}
        onPointerUp={cancelMessagePress}
        onPointerCancel={cancelMessagePress}
        onPointerLeave={cancelMessagePress}
        onContextMenu={openMessageMenu}
        style={{
          position: "relative",
          background: "linear-gradient(180deg, #F9D84D 0%, #F5C93A 100%)",
          border: "2.6px solid #171717",
          borderRadius: "17px 17px 6px 17px",
          padding: "10px 14px",
          boxShadow: "0 3px 0 rgba(17,17,17,0.14), inset 0 1px 0 rgba(255,255,255,0.35)",
        }}
      >
        <div
          aria-hidden
          style={{
            position: "absolute",
            right: -7,
            bottom: 9,
            width: 11,
            height: 12,
            background: "#F5C93A",
            borderRight: "2.6px solid #171717",
            borderBottom: "2.6px solid #171717",
            transform: "skewX(26deg) rotate(-8deg)",
            borderRadius: "0 0 3px 0",
          }}
        />
        {editing ? (
          <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
            <textarea
              ref={editTextareaRef}
              value={editText}
              onChange={(event) => {
                setEditText(event.target.value);
                const el = event.currentTarget;
                el.style.height = "auto";
                el.style.height = Math.min(el.scrollHeight, 96) + "px";
              }}
              onKeyDown={(event) => {
                if (event.key === "Enter" && !event.shiftKey) {
                  event.preventDefault();
                  submitEdit();
                }
                if (event.key === "Escape") {
                  onCancelEdit?.();
                }
              }}
              rows={1}
              style={{
                width: "100%",
                minWidth: 150,
                maxWidth: 220,
                background: "transparent",
                border: "none",
                outline: "none",
                resize: "none",
                color: "#171717",
                fontFamily: "inherit",
                fontSize: 15,
                lineHeight: "23px",
                padding: 0,
                display: "block",
              }}
            />
            <div style={{ display: "flex", justifyContent: "flex-end", gap: 6 }}>
              <button
                aria-label="取消改写"
                onClick={onCancelEdit}
                style={{
                  width: 28,
                  height: 28,
                  borderRadius: 999,
                  border: "2px solid #171717",
                  background: "#FFF8E8",
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "center",
                  cursor: "pointer",
                }}
              >
                <X size={13} strokeWidth={2.7} />
              </button>
              <button
                aria-label="提交改写"
                onClick={submitEdit}
                style={{
                  width: 28,
                  height: 28,
                  borderRadius: 999,
                  border: "2px solid #171717",
                  background: "#171717",
                  color: "#F7CF45",
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "center",
                  cursor: "pointer",
                }}
              >
                <Check size={14} strokeWidth={2.9} />
              </button>
            </div>
          </div>
        ) : (
          <p
            style={{
              fontSize: 15,
              color: "#171717",
              margin: 0,
              lineHeight: "23px",
            }}
          >
            {message.text}
          </p>
        )}
      </div>
      <UserAvatar size={30} />
    </motion.div>
  );
}

// ─── Suggestion chips (empty state) ──────────────────────────────────────────

function EmptyState({ onChip }: { onChip: (text: string) => void }) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 16 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.4 }}
      style={{
        flex: 1,
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        justifyContent: "center",
        padding: "32px 24px",
        gap: 20,
      }}
    >
      {/* Large agent avatar */}
      <AgentAvatar size={72} ringColor="yellow" showBadge={false} />

      {/* Invite text */}
      <p
        style={{
          fontSize: 14.5,
          color: "#6A6A5A",
          textAlign: "center",
          margin: 0,
          lineHeight: 1.6,
          maxWidth: 200,
        }}
      >
        向 Roco 提问队伍策略、精灵搭配，或对战技巧
      </p>

      {/* Prompt chips */}
      <div style={{ display: "flex", flexDirection: "column", gap: 9, width: "100%" }}>
        {PROMPT_CHIPS.map((chip) => (
          <button
            key={chip}
            onClick={() => onChip(chip)}
            style={{
              background: "#FFFDF3",
              border: "2px solid rgba(23,23,23,0.2)",
              borderRadius: 20,
              padding: "9px 16px",
              fontSize: 13.5,
              color: "#2D2D2A",
              cursor: "pointer",
              textAlign: "left",
              fontFamily: "inherit",
              fontWeight: 500,
              boxShadow: "0 2px 0 rgba(17,17,17,0.1)",
              transition: "transform 0.1s",
            }}
            onMouseDown={(e) => (e.currentTarget.style.transform = "translateY(1px)")}
            onMouseUp={(e) => (e.currentTarget.style.transform = "translateY(0)")}
          >
            {chip}
          </button>
        ))}
      </div>
    </motion.div>
  );
}

function AddPersonaPage({ onBack }: { onBack: () => void }) {
  return (
    <motion.div
      initial={{ x: "100%" }}
      animate={{ x: 0 }}
      exit={{ x: "100%" }}
      transition={{ type: "spring", stiffness: 320, damping: 34 }}
      style={{
        position: "absolute",
        inset: 0,
        zIndex: 70,
        background: "#F7CF45",
        display: "flex",
        flexDirection: "column",
        overflow: "hidden",
      }}
    >
      <div
        style={{
          padding: "14px 14px 10px",
          display: "flex",
          alignItems: "center",
          gap: 10,
        }}
      >
        <button
          onClick={onBack}
          style={{
            width: 36,
            height: 36,
            borderRadius: 999,
            border: "2.5px solid #171717",
            background: "#FFF8E8",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            cursor: "pointer",
            boxShadow: "0 2px 0 rgba(17,17,17,0.18)",
          }}
        >
          <ArrowLeft size={17} color="#171717" strokeWidth={2.6} />
        </button>
        <div
          style={{
            fontSize: 20,
            fontWeight: 900,
            color: "#171717",
            letterSpacing: "-0.4px",
          }}
        >
          添加人格
        </div>
      </div>

      <div
        style={{
          flex: 1,
          margin: "0 10px 10px",
          background: "#FFF8E8",
          border: "3px solid #171717",
          borderRadius: 20,
          padding: 20,
          display: "flex",
          flexDirection: "column",
          alignItems: "center",
          justifyContent: "center",
          textAlign: "center",
          gap: 14,
        }}
      >
        <div
          style={{
            width: 76,
            height: 76,
            borderRadius: 999,
            border: "2.5px dashed rgba(23,23,23,0.35)",
            background: "rgba(247,207,69,0.25)",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
          }}
        >
          <Plus size={26} color="rgba(23,23,23,0.55)" strokeWidth={2.6} />
        </div>
        <div style={{ fontSize: 18, fontWeight: 900, color: "#171717" }}>
          Persona 创建入口
        </div>
        <p
          style={{
            margin: 0,
            maxWidth: 230,
            color: "#6A6256",
            fontSize: 13.5,
            lineHeight: 1.55,
            fontWeight: 600,
          }}
        >
          V1 先保留入口和占位，不在这里展开完整创建流程。
        </p>
      </div>
    </motion.div>
  );
}

// ─── Main component ───────────────────────────────────────────────────────────

export function ChatScreen() {
  const [messages, setMessages] = useState<Message[]>(INITIAL_MESSAGES);
  const [thinking, setThinking] = useState(false);
  const [wheelOpen, setWheelOpen] = useState(false);
  const [wheelAnchor, setWheelAnchor] = useState<{ x: number; y: number } | undefined>();
  const [drawerOpen, setDrawerOpen] = useState(false);
  const [addPersonaOpen, setAddPersonaOpen] = useState(false);
  const [selectedPersonaId, setSelectedPersonaId] = useState("you_know_who");
  const [messageActionMenu, setMessageActionMenu] = useState<MessageActionMenuState | null>(null);
  const [editingUserMessageId, setEditingUserMessageId] = useState<string | null>(null);

  const rootRef = useRef<HTMLDivElement>(null);
  const scrollRef = useRef<HTMLDivElement>(null);

  const selectedPersona =
    PERSONAS.find((p) => p.id === selectedPersonaId) ?? PERSONAS[0];
  const agentRingColor = selectedPersonaId === "you_know_who" ? "yellow" : "blue";
  const agentAvatarVariant =
    selectedPersonaId === "ai_assistant" ? "ai_assistant" : "you_know_who";
  const latestUserMessageId = [...messages].reverse().find((message) => message.role === "user")?.id;

  // Scroll to bottom whenever messages change
  useEffect(() => {
    const el = scrollRef.current;
    if (el) {
      el.scrollTop = el.scrollHeight;
    }
  }, [messages, thinking]);

  const handleSend = (text: string) => {
    const userMsg: Message = {
      id: Date.now().toString(),
      role: "user",
      text,
      state: "sent",
    };
    setMessages((prev) => [...prev, userMsg]);
    setThinking(true);

    // Simulate agent response
    setTimeout(() => {
      setThinking(false);
      const agentMsg: Message = {
        id: (Date.now() + 1).toString(),
        role: "agent",
        text: getMockReply(text),
        state: "sent",
      };
      setMessages((prev) => [...prev, agentMsg]);
    }, 1600 + Math.random() * 800);
  };

  const handleRetry = (id: string) => {
    setMessages((prev) =>
      prev.map((m) => (m.id === id ? { ...m, state: "sent", text: "已重新获取，请稍候…" } : m))
    );
  };

  const findMessage = (id: string) => messages.find((message) => message.id === id);

  const openMessageActionMenu = (message: Message, element: HTMLElement) => {
    const rootRect = rootRef.current?.getBoundingClientRect();
    const rect = element.getBoundingClientRect();
    const leftInRoot = rootRect ? rect.left - rootRect.left : rect.left;
    const rightInRoot = rootRect ? rect.right - rootRect.left : rect.right;
    const topInRoot = rootRect ? rect.top - rootRect.top : rect.top;

    setMessageActionMenu({
      messageId: message.id,
      role: message.role,
      x: message.role === "user" ? rightInRoot - 192 : leftInRoot,
      y: topInRoot - 48,
    });
  };

  const closeMessageActionMenu = () => {
    setMessageActionMenu(null);
  };

  const handleCopyMessage = async () => {
    if (!messageActionMenu) return;
    const message = findMessage(messageActionMenu.messageId);
    if (!message) return;
    try {
      await navigator.clipboard?.writeText(message.text);
    } catch {
      // Clipboard can be unavailable in previews; the action still closes cleanly.
    }
    closeMessageActionMenu();
  };

  const handleRewriteMessage = () => {
    if (!messageActionMenu) return;
    const message = findMessage(messageActionMenu.messageId);
    if (!message || message.role !== "user") return;
    if (message.id !== latestUserMessageId) return;
    setEditingUserMessageId(message.id);
    closeMessageActionMenu();
  };

  const handleSubmitUserRewrite = (messageId: string, text: string) => {
    const targetIndex = messages.findIndex((message) => message.id === messageId);
    if (targetIndex < 0) return;

    setEditingUserMessageId(null);
    setMessages((prev) => [
      ...prev.slice(0, targetIndex),
      { ...prev[targetIndex], text },
    ]);
    setThinking(true);

    window.setTimeout(() => {
      setThinking(false);
      const agentMsg: Message = {
        id: (Date.now() + 1).toString(),
        role: "agent",
        text: getMockReply(text),
        state: "sent",
      };
      setMessages((prev) => [...prev, agentMsg]);
    }, 900);
  };

  const handleRegenerateMessage = () => {
    if (!messageActionMenu) return;
    const targetId = messageActionMenu.messageId;
    const targetIndex = messages.findIndex((message) => message.id === targetId);
    const previousUser = [...messages]
      .slice(0, targetIndex)
      .reverse()
      .find((message) => message.role === "user");

    setMessages((prev) =>
      prev.map((message) =>
        message.id === targetId ? { ...message, text: "我重新整理一下这条回复…" } : message
      )
    );
    closeMessageActionMenu();

    window.setTimeout(() => {
      setMessages((prev) =>
        prev.map((message) =>
          message.id === targetId
            ? {
                ...message,
                text: getMockReply(previousUser?.text ?? message.text),
                state: "sent",
              }
            : message
        )
      );
    }, 900);
  };

  const askDeleteMessage = () => {
    if (!messageActionMenu) return;
    setMessageActionMenu({ ...messageActionMenu, confirmDelete: true });
  };

  const confirmDeleteMessage = () => {
    if (!messageActionMenu) return;
    setMessages((prev) => prev.filter((message) => message.id !== messageActionMenu.messageId));
    if (editingUserMessageId === messageActionMenu.messageId) {
      setEditingUserMessageId(null);
    }
    closeMessageActionMenu();
  };

  const handlePersonaSelect = (persona: PersonaOption) => {
    if (persona.category === "add") {
      setWheelOpen(false);
      setAddPersonaOpen(true);
      return;
    }
    setSelectedPersonaId(persona.id);
    setWheelOpen(false);
  };

  const openPersonaWheel = (viewportAnchor: { x: number; y: number }) => {
    const rootRect = rootRef.current?.getBoundingClientRect();
    setWheelAnchor(
      rootRect
        ? {
            x: viewportAnchor.x - rootRect.left,
            y: viewportAnchor.y - rootRect.top,
          }
        : viewportAnchor
    );
    setWheelOpen(true);
  };

  const isEmpty = messages.length === 0;

  return (
    <div
      ref={rootRef}
      style={{
        width: "100%",
        height: "100%",
        background: "#F7CF45",
        display: "flex",
        flexDirection: "column",
        position: "relative",
        overflow: "hidden",
        minHeight: 0,
        fontFamily:
          "'Nunito', -apple-system, 'PingFang SC', 'Hiragino Sans GB', 'Microsoft YaHei', sans-serif",
      }}
    >
      {/* ── Yellow background pattern ── */}
      <div
        style={{
          position: "absolute",
          inset: 0,
          backgroundImage: `radial-gradient(circle, rgba(255,255,255,0.18) 1px, transparent 1px)`,
          backgroundSize: "22px 22px",
          pointerEvents: "none",
        }}
      />

      {/* ── Chat sheet (handwritten paper path) ── */}
      <div
        style={{
          flex: 1,
          margin: "8px 9px 8px",
          position: "relative",
          zIndex: 2,
          minHeight: 0,
        }}
      >
        <img
          src="/assets/roco-paper-shell.png"
          aria-hidden
          alt=""
          style={{
            position: "absolute",
            inset: 0,
            width: "100%",
            height: "100%",
            objectFit: "fill",
            pointerEvents: "none",
            userSelect: "none",
            filter: "sepia(0.16) saturate(1.08) brightness(1.01)",
          }}
        />
        <div
          aria-hidden
          style={{
            position: "absolute",
            inset: "18px 16px 18px 16px",
            background:
              "radial-gradient(circle at 48% 42%, rgba(247,207,69,0.12), rgba(247,207,69,0.04) 44%, transparent 74%)",
            mixBlendMode: "multiply",
            pointerEvents: "none",
          }}
        />
        <img
          src="/assets/roco-paper-outline.png"
          aria-hidden
          alt=""
          style={{
            position: "absolute",
            inset: 0,
            width: "100%",
            height: "100%",
            objectFit: "fill",
            pointerEvents: "none",
            userSelect: "none",
            zIndex: 8,
          }}
        />

        <div
          style={{
            position: "relative",
            height: "100%",
            display: "flex",
            flexDirection: "column",
            overflow: "hidden",
            minHeight: 0,
            padding: "12px 7px 13px",
          }}
        >
        {/* Message scroll area */}
        <div
          ref={scrollRef}
          style={{
            flex: 1,
            minHeight: 0,
            overflowY: "auto",
            overscrollBehavior: "contain",
            WebkitOverflowScrolling: "touch",
            padding: "18px 12px 6px",
            display: "flex",
            flexDirection: "column",
            gap: 12,
            maskImage: "linear-gradient(to bottom, transparent 0, #000 24px, #000 100%)",
            WebkitMaskImage: "linear-gradient(to bottom, transparent 0, #000 24px, #000 100%)",
          }}
        >
          {isEmpty ? (
            <EmptyState onChip={handleSend} />
          ) : (
            <>
              <SessionDivider label="今天" />

              {messages.map((msg) =>
                msg.role === "agent" ? (
                  <AgentBubble
                    key={msg.id}
                    message={msg}
                    onRetry={() => handleRetry(msg.id)}
                    onAvatarLongPress={openPersonaWheel}
                    onMessageLongPress={openMessageActionMenu}
                    ringColor={agentRingColor}
                    avatarVariant={agentAvatarVariant}
                  />
                ) : (
                  <UserBubble
                    key={msg.id}
                    message={msg}
                    editing={editingUserMessageId === msg.id}
                    onMessageLongPress={openMessageActionMenu}
                    onSubmitEdit={handleSubmitUserRewrite}
                    onCancelEdit={() => setEditingUserMessageId(null)}
                  />
                )
              )}

              {/* Thinking bubble */}
              <AnimatePresence>
                {thinking && (
                  <AgentBubble
                    key="thinking"
                    message={{ id: "thinking", role: "agent", text: "", state: "thinking" }}
                    thinking
                    onAvatarLongPress={openPersonaWheel}
                    onMessageLongPress={openMessageActionMenu}
                    ringColor={agentRingColor}
                    avatarVariant={agentAvatarVariant}
                  />
                )}
              </AnimatePresence>
            </>
          )}
        </div>
        <PromptComposer onSend={handleSend} disabled={thinking || editingUserMessageId !== null} />
        </div>
      </div>

      <AnimatePresence>
        {messageActionMenu && (
          <>
            <motion.div
              key="message-action-backdrop"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              onPointerDown={closeMessageActionMenu}
              style={{
                position: "absolute",
                inset: 0,
                zIndex: 61,
                background: "rgba(17,17,17,0.08)",
                backdropFilter: "blur(0.5px)",
              }}
            />
            <MessageActionMenu
              key={`${messageActionMenu.messageId}-${messageActionMenu.confirmDelete ? "confirm" : "actions"}`}
              menu={messageActionMenu}
              canRewrite={messageActionMenu.messageId === latestUserMessageId}
              onCopy={handleCopyMessage}
              onRewrite={handleRewriteMessage}
              onRegenerate={handleRegenerateMessage}
              onAskDelete={askDeleteMessage}
              onConfirmDelete={confirmDeleteMessage}
              onClose={closeMessageActionMenu}
            />
          </>
        )}
      </AnimatePresence>

      {/* ── Persona wheel overlay ── */}
      <div style={{ position: "absolute", inset: 0, zIndex: 50, pointerEvents: wheelOpen ? "auto" : "none" }}>
        <PersonaWheel
          open={wheelOpen}
          personas={PERSONAS}
          selectedId={selectedPersonaId}
          anchor={wheelAnchor}
          onSelect={handlePersonaSelect}
          onClose={() => setWheelOpen(false)}
        />
      </div>

      {/* ── Settings drawer ── */}
      <SettingsDrawer
        open={drawerOpen}
        onOpen={() => setDrawerOpen(true)}
        onClose={() => setDrawerOpen(false)}
        personaLabel={selectedPersona.label}
      />

      <AnimatePresence>
        {addPersonaOpen && <AddPersonaPage onBack={() => setAddPersonaOpen(false)} />}
      </AnimatePresence>
    </div>
  );
}

// ─── Mock reply helper ────────────────────────────────────────────────────────

function getMockReply(input: string): string {
  const lower = input.toLowerCase();
  if (lower.includes("穿透") || lower.includes("克制")) {
    return "水系和草系精灵对大部分火系队有不错的克制效果，同时可以搭配一只高速干扰位来压制先手。";
  }
  if (lower.includes("先手")) {
    return "先手压制的关键是让速度差达到 10 点以上，同时配置「快攻」技能链，让对方无法换场应对。";
  }
  if (lower.includes("感谢") || lower.includes("谢谢")) {
    return "不客气，随时来找我！有新的精灵数据也可以告诉我。";
  }
  return "明白，这个方向我来分析一下。你目前的阵容结构整体偏稳健，可以在输出端再做一些调整。";
}
