import React, { useCallback, useEffect, useRef, useState } from "react";
import {
  Bot,
  ChevronLeft,
  Eye,
  EyeOff,
  KeyRound,
  Loader2,
  Plus,
  SendHorizonal,
  Shield,
  Trash2,
  Users,
  X,
} from "lucide-react";
import paperShell from "./assets/paper_shell.png";
import paperOutline from "./assets/paper_outline.png";
import { ProductApiClient } from "./api/client";
import type {
  AgentResponse,
  ChatResponse,
  PersonaSelector,
  SpeciesMoveRecord,
  SpeciesSearchItem,
  TeamContextAttachment,
  TeamContextSlot,
  TeamMoveSelection,
  TeamStatKey,
} from "./api/types";
import {
  buildNativeRuntimeHeaders,
  clearProviderKey,
  DEFAULT_RUNTIME_SETTINGS,
  hasCompleteProviderConfig,
  loadRuntimeSettings,
  saveRuntimeSettings,
  type RuntimeSettings,
} from "./runtime/runtimeSettings";

type PersonaUiId = "you_know_who" | "ai_assistant";
type DrawerView = "home" | "api" | "team";
type PersonaWheelState =
  | { status: "closed" }
  | { status: "open"; anchor: { x: number; y: number } };
type Message = {
  id: string;
  role: "user" | "agent";
  text: string;
  status: "sent" | "thinking" | "failed";
  personaUiId?: PersonaUiId;
  stale?: boolean;
};

const apiClient = new ProductApiClient();
const TEAM_STORE_KEY = "roco.desktop.team_context.v1";
const PERSONA_KEY = "roco.desktop.persona_ui_id.v1";
const SESSION_KEY = "roco.desktop.active_session_id.v1";
const MESSAGES_KEY_PREFIX = "roco.desktop.visible_messages.v1:";

const PERSONA_SELECTORS: Record<PersonaUiId, PersonaSelector> = {
  you_know_who: {
    kind: "managed",
    persona_id: "you_know_who",
    version: "draft.v1",
    revision: 1,
  },
  ai_assistant: {
    kind: "built_in",
    persona_id: "lattice_support_coach",
  },
};

type TeamPickerState =
  | { kind: "closed" }
  | { kind: "species"; slotIndex: number }
  | { kind: "moves"; activeCell: number; slotIndex: number };
type TeamPanelMode = "board" | "detail";
type TeamInlinePanel = "closed" | "nature" | "iv";

type NatureOption = {
  label: string;
  minus: TeamStatKey;
  plus: TeamStatKey;
};

const STAT_KEYS: TeamStatKey[] = ["hp", "atk", "defense", "spa", "spd", "spe"];
const STAT_LABELS: Record<TeamStatKey, string> = {
  hp: "生命",
  atk: "物攻",
  defense: "物防",
  spa: "魔攻",
  spd: "魔防",
  spe: "速度",
};
const IV_VALUES = [7, 8, 9, 10] as const;
const NATURE_OPTIONS: NatureOption[] = [
  { label: "沉默", plus: "hp", minus: "atk" },
  { label: "平和", plus: "hp", minus: "spa" },
  { label: "理智", plus: "hp", minus: "defense" },
  { label: "忧郁", plus: "hp", minus: "spd" },
  { label: "紧张", plus: "hp", minus: "spe" },
  { label: "保守", plus: "spa", minus: "atk" },
  { label: "冷静", plus: "spa", minus: "spe" },
  { label: "稳重", plus: "spa", minus: "defense" },
  { label: "马虎", plus: "spa", minus: "spd" },
  { label: "认真", plus: "spa", minus: "hp" },
  { label: "沉着", plus: "spd", minus: "atk" },
  { label: "慎重", plus: "spd", minus: "spa" },
  { label: "温顺", plus: "spd", minus: "defense" },
  { label: "狂妄", plus: "spd", minus: "spe" },
  { label: "实干", plus: "spd", minus: "hp" },
  { label: "胆小", plus: "spe", minus: "atk" },
  { label: "开朗", plus: "spe", minus: "spa" },
  { label: "急躁", plus: "spe", minus: "defense" },
  { label: "天真", plus: "spe", minus: "spd" },
  { label: "浮躁", plus: "spe", minus: "hp" },
  { label: "固执", plus: "atk", minus: "spa" },
  { label: "勇敢", plus: "atk", minus: "spe" },
  { label: "孤僻", plus: "atk", minus: "defense" },
  { label: "调皮", plus: "atk", minus: "spd" },
  { label: "坦率", plus: "atk", minus: "hp" },
  { label: "大胆", plus: "defense", minus: "atk" },
  { label: "淘气", plus: "defense", minus: "spa" },
  { label: "懒散", plus: "defense", minus: "spd" },
  { label: "悠闲", plus: "defense", minus: "spe" },
  { label: "害羞", plus: "defense", minus: "hp" },
];
const DEFAULT_NATURE = NATURE_OPTIONS.find((nature) => nature.label === "浮躁") ?? NATURE_OPTIONS[0];

export function App() {
  const [backend, setBackend] = useState<RocoBackendStatus | null>(null);
  const [drawerOpen, setDrawerOpen] = useState(false);
  const [drawerView, setDrawerView] = useState<DrawerView>("home");
  const [teamPanelMode, setTeamPanelMode] = useState<TeamPanelMode>("board");
  const [personaWheel, setPersonaWheel] = useState<PersonaWheelState>({ status: "closed" });
  const [runtimeSettings, setRuntimeSettings] = useState<RuntimeSettings>(DEFAULT_RUNTIME_SETTINGS);
  const [settingsDraft, setSettingsDraft] = useState<RuntimeSettings>(DEFAULT_RUNTIME_SETTINGS);
  const [personaUiId, setPersonaUiId] = useState<PersonaUiId>(() => loadPersonaUiId());
  const [teamContext, setTeamContext] = useState<TeamContextAttachment>(() => loadTeamContext());
  const [sessionId, setSessionId] = useState<string | null>(() => loadActiveSessionId());
  const [messages, setMessages] = useState<Message[]>(() => loadVisibleMessages(loadActiveSessionId()));
  const [composer, setComposer] = useState("");
  const [loading, setLoading] = useState(false);
  const [notice, setNotice] = useState<string | null>(null);
  const frameRef = useRef<HTMLElement | null>(null);
  const scrollRef = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    void window.rocoDesktop.ensureBackendStarted().then(setBackend).catch((error) => {
      setBackend({
        status: "failed",
        baseUrl: "http://127.0.0.1:8000",
        managedByDesktop: false,
        message: error instanceof Error ? error.message : "Backend failed to start.",
      });
    });
    void loadRuntimeSettings().then((loaded) => {
      setRuntimeSettings(loaded);
      setSettingsDraft(loaded);
    });
  }, []);

  useEffect(() => {
    scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight, behavior: "smooth" });
  }, [messages, loading]);

  useEffect(() => {
    if (sessionId) {
      saveVisibleMessages(sessionId, messages);
    }
  }, [messages, sessionId]);

  async function sendMessage(text: string) {
    const trimmed = text.trim();
    if (!trimmed || loading) {
      return;
    }
    setComposer("");
    setNotice(null);
    setLoading(true);
    const userMessage: Message = {
      id: createMessageId("user"),
      role: "user",
      status: "sent",
      text: trimmed,
    };
    const thinkingMessage: Message = {
      id: "thinking",
      role: "agent",
      status: "thinking",
      text: "...",
      personaUiId,
    };
    setMessages((current) => [...current, userMessage, thinkingMessage]);

    try {
      const response = await apiClient.chat(
        {
          message: trimmed,
          session_id: sessionId,
          persona_selector: PERSONA_SELECTORS[personaUiId],
          context_attachments: teamContext.slots.length > 0 ? [teamContext] : [],
        },
        buildNativeRuntimeHeaders(runtimeSettings),
      );
      saveActiveSessionId(response.session_id);
      setSessionId(response.session_id);
      applySessionEvent(response);
      setMessages((current) => [
        ...current.filter((item) => item.id !== "thinking"),
        {
          id: createMessageId("agent"),
          role: "agent",
          status: "sent",
          text: resolveVisibleReply(response),
          personaUiId,
        },
      ]);
    } catch (caught) {
      setMessages((current) => [
        ...current.filter((item) => item.id !== "thinking"),
        {
          id: createMessageId("agent"),
          role: "agent",
          status: "failed",
          text: caught instanceof Error ? normalizeError(caught.message) : "模型服务调用失败。",
          personaUiId,
        },
      ]);
    } finally {
      setLoading(false);
    }
  }

  function applySessionEvent(response: ChatResponse) {
    const event = response.session_event;
    if (!event) {
      return;
    }
    if (event.diagnostic.visible_messages === "clear") {
      setMessages([]);
      setNotice(event.message);
      return;
    }
    if (event.diagnostic.visible_messages === "mark_stale") {
      setMessages((current) =>
        current.map((message) =>
          message.id === "thinking" ? message : { ...message, stale: true },
        ),
      );
      setNotice(event.message);
    }
  }

  async function clearCurrentChat() {
    if (loading) {
      return;
    }
    if (messages.length > 0 && !window.confirm("清空当前对话？队伍、人设和 API 设置会保留。")) {
      return;
    }
    setLoading(true);
    setNotice(null);
    try {
      const response = await apiClient.clearSession();
      saveActiveSessionId(response.session_id);
      saveVisibleMessages(response.session_id, []);
      setSessionId(response.session_id);
      setMessages([]);
      setNotice(response.session_event.message);
      setDrawerOpen(false);
    } catch (caught) {
      setNotice(caught instanceof Error ? normalizeError(caught.message) : "清空当前对话失败。");
    } finally {
      setLoading(false);
    }
  }

  async function saveSettings(next: RuntimeSettings) {
    await saveRuntimeSettings(next);
    const loaded = await loadRuntimeSettings();
    setRuntimeSettings(loaded);
    setSettingsDraft(loaded);
    setNotice("API 设置已保存。");
  }

  function savePersona(next: PersonaUiId) {
    localStorage.setItem(PERSONA_KEY, next);
    setPersonaUiId(next);
    setPersonaWheel({ status: "closed" });
    setNotice(`已切换人格：${personaLabel(next)}。`);
  }

  function openPersonaWheel(point: { clientX: number; clientY: number }) {
    const rect = frameRef.current?.getBoundingClientRect();
    if (!rect) {
      return;
    }
    setDrawerOpen(false);
    setPersonaWheel({
      status: "open",
      anchor: {
        x: point.clientX - rect.left,
        y: point.clientY - rect.top,
      },
    });
  }

  const saveTeam = useCallback((next: TeamContextAttachment) => {
    localStorage.setItem(TEAM_STORE_KEY, JSON.stringify(next));
    setTeamContext(next);
  }, []);

  return (
    <main className="app-shell">
      <section className="phone-frame" ref={frameRef}>
        <div className="paper-shell">
          <img className="paper-bg" src={paperShell} alt="" />
          <img className="paper-outline" src={paperOutline} alt="" />
          <div className="chat-content">
            <BackendStrip backend={backend} />
            <div ref={scrollRef} className={`message-list ${messages.length === 0 ? "empty" : ""}`}>
              {messages.length === 0 ? (
                <EmptyState
                  currentPersona={personaUiId}
                  onPersonaLongPress={openPersonaWheel}
                  onUsePrompt={setComposer}
                />
              ) : (
                messages.map((message) => (
                  <MessageBubble
                    activePersona={personaUiId}
                    key={message.id}
                    message={message}
                    onPersonaLongPress={openPersonaWheel}
                  />
                ))
              )}
            </div>
            {notice ? <div className="notice">{notice}</div> : null}
            <PromptComposer
              disabled={loading}
              onChange={setComposer}
              onSend={() => void sendMessage(composer)}
              value={composer}
            />
          </div>
        </div>
        <SettingsDrawer
          apiClient={apiClient}
          currentPersona={personaUiId}
          draft={settingsDraft}
          onChangeDraft={setSettingsDraft}
          onClearProviderKey={async () => {
            await clearProviderKey();
            const next = { ...settingsDraft, providerKey: "" };
            setSettingsDraft(next);
            await saveSettings(next);
          }}
          onClearSession={clearCurrentChat}
          onClose={() => setDrawerOpen(false)}
          onOpen={() => setDrawerOpen(true)}
          onSaveSettings={saveSettings}
          onSaveTeam={saveTeam}
          open={drawerOpen}
          teamContext={teamContext}
          teamPanelMode={teamPanelMode}
          view={drawerView}
          setTeamPanelMode={setTeamPanelMode}
          setView={setDrawerView}
        />
        <PersonaWheel
          currentPersona={personaUiId}
          onClose={() => setPersonaWheel({ status: "closed" })}
          onSavePersona={savePersona}
          onUnavailable={() => {
            setPersonaWheel({ status: "closed" });
            setNotice("人格创建稍后接入。");
          }}
          state={personaWheel}
        />
      </section>
    </main>
  );
}

function BackendStrip({ backend }: { backend: RocoBackendStatus | null }) {
  if (!backend) {
    return <div className="backend-strip">正在连接本地 RoCoach backend...</div>;
  }
  if (backend.status === "running") {
    return null;
  }
  return <div className="backend-strip error">{backend.message}</div>;
}

function EmptyState({
  currentPersona,
  onPersonaLongPress,
  onUsePrompt,
}: {
  currentPersona: PersonaUiId;
  onPersonaLongPress: (point: { clientX: number; clientY: number }) => void;
  onUsePrompt: (prompt: string) => void;
}) {
  const prompts = ["这套队伍怎么优化？", "我该怎么判断首发？", "帮我分析这只精灵的定位"];
  return (
    <div className="empty-state">
      <AgentAvatar onLongPress={onPersonaLongPress} variant={currentPersona} size={72} />
      <p>向 RoCoach 提问队伍策略、精灵搭配，或对战技巧。</p>
      <div className="prompt-chips">
        {prompts.map((prompt) => (
          <button key={prompt} onClick={() => onUsePrompt(prompt)}>
            {prompt}
          </button>
        ))}
      </div>
    </div>
  );
}

function MessageBubble({
  activePersona,
  message,
  onPersonaLongPress,
}: {
  activePersona: PersonaUiId;
  message: Message;
  onPersonaLongPress: (point: { clientX: number; clientY: number }) => void;
}) {
  const isUser = message.role === "user";
  return (
    <div className={`message-row ${isUser ? "user" : "agent"}`}>
      {!isUser ? (
        <AgentAvatar
          onLongPress={onPersonaLongPress}
          size={38}
          thinking={message.status === "thinking"}
          variant={message.personaUiId ?? activePersona}
        />
      ) : null}
      <div
        className={`bubble ${isUser ? "user" : "agent"} ${message.status === "failed" ? "failed" : ""} ${
          message.stale ? "stale" : ""
        }`}
      >
        <span className="bubble-tail" />
        {message.text}
      </div>
      {isUser ? <UserAvatar /> : null}
    </div>
  );
}

function AgentAvatar({
  highlighted = false,
  size,
  ring = true,
  variant,
  thinking = false,
  onLongPress,
}: {
  highlighted?: boolean;
  size: number;
  ring?: boolean;
  variant: PersonaUiId;
  thinking?: boolean;
  onLongPress?: (point: { clientX: number; clientY: number }) => void;
}) {
  const timerRef = useRef<number | null>(null);
  const longPressPointRef = useRef<{ clientX: number; clientY: number } | null>(null);

  function clearTimer() {
    if (timerRef.current) {
      window.clearTimeout(timerRef.current);
      timerRef.current = null;
    }
  }

  return (
    <button
      aria-label="Agent persona"
      className={`avatar agent ${variant} ${ring ? "ringed" : ""} ${highlighted ? "highlighted" : ""} ${thinking ? "thinking" : ""}`}
      onPointerDown={(event) => {
        if (onLongPress) {
          longPressPointRef.current = { clientX: event.clientX, clientY: event.clientY };
          event.currentTarget.setPointerCapture(event.pointerId);
          timerRef.current = window.setTimeout(() => {
            if (longPressPointRef.current) {
              onLongPress(longPressPointRef.current);
            }
          }, 430);
        }
      }}
      onPointerCancel={clearTimer}
      onPointerLeave={clearTimer}
      onPointerUp={() => {
        clearTimer();
      }}
      style={{ "--avatar-size": `${size}px`, width: size, height: size } as React.CSSProperties}
    >
      {variant === "ai_assistant" ? <span>AI</span> : <span className="eyes" />}
    </button>
  );
}

function UserAvatar() {
  return (
    <div className="avatar user-avatar">
      <span>☺</span>
    </div>
  );
}

function PromptComposer({
  disabled,
  onChange,
  onSend,
  value,
}: {
  disabled: boolean;
  onChange: (value: string) => void;
  onSend: () => void;
  value: string;
}) {
  return (
    <div className="composer">
      <textarea
        disabled={disabled}
        onChange={(event) => onChange(event.target.value)}
        onKeyDown={(event) => {
          if (event.key === "Enter" && !event.shiftKey) {
            event.preventDefault();
            onSend();
          }
        }}
        placeholder="问问 RoCoach..."
        rows={1}
        value={value}
      />
      <button disabled={disabled || !value.trim()} onClick={onSend}>
        {disabled ? <Loader2 className="spin" size={19} /> : <SendHorizonal size={19} />}
      </button>
    </div>
  );
}

function SettingsDrawer({
  apiClient,
  currentPersona,
  draft,
  onChangeDraft,
  onClearProviderKey,
  onClearSession,
  onClose,
  onOpen,
  onSaveSettings,
  onSaveTeam,
  open,
  teamContext,
  teamPanelMode,
  view,
  setTeamPanelMode,
  setView,
}: {
  apiClient: ProductApiClient;
  currentPersona: PersonaUiId;
  draft: RuntimeSettings;
  onChangeDraft: (draft: RuntimeSettings) => void;
  onClearProviderKey: () => Promise<void>;
  onClearSession: () => Promise<void>;
  onClose: () => void;
  onOpen: () => void;
  onSaveSettings: (draft: RuntimeSettings) => Promise<void>;
  onSaveTeam: (team: TeamContextAttachment) => void;
  open: boolean;
  teamContext: TeamContextAttachment;
  teamPanelMode: TeamPanelMode;
  view: DrawerView;
  setTeamPanelMode: (mode: TeamPanelMode) => void;
  setView: (view: DrawerView) => void;
}) {
  const showingTeamDetail = view === "team" && teamPanelMode === "detail";
  return (
    <div className={`drawer-rail ${open ? "open" : ""}`}>
      <button className="drawer-handle" onClick={open ? onClose : onOpen} aria-label={open ? "关闭设置" : "打开设置"}>
        <span />
        <span />
        <span />
      </button>
      {open ? <button className="drawer-backdrop" aria-label="关闭设置遮罩" onClick={onClose} /> : null}
      <aside className="drawer-panel">
        <header className="drawer-header">
          {view !== "home" ? (
            <button
              className="back-button"
              onClick={() => {
                if (showingTeamDetail) {
                  setTeamPanelMode("board");
                } else {
                  setView("home");
                }
              }}
              aria-label={showingTeamDetail ? "返回牌组" : "返回设置首页"}
            >
              <ChevronLeft size={24} />
            </button>
          ) : null}
          <h2>{showingTeamDetail ? "返回牌组" : viewTitle(view)}</h2>
          <button className="close-button" onClick={onClose} aria-label="关闭设置">
            <X size={19} />
          </button>
        </header>
        {view === "home" ? (
          <SettingsHome
            apiConfigured={hasCompleteProviderConfig(draft)}
            currentPersona={currentPersona}
            onClearSession={onClearSession}
            onNavigate={(nextView) => {
              if (nextView === "team") {
                setTeamPanelMode("board");
              }
              setView(nextView);
            }}
            teamSize={teamContext.slots.length}
          />
        ) : null}
        {view === "api" ? (
          <ApiSettings
            apiClient={apiClient}
            draft={draft}
            onChange={onChangeDraft}
            onClearProviderKey={onClearProviderKey}
            onSave={onSaveSettings}
          />
        ) : null}
        {view === "team" ? (
          <TeamSettings
            apiClient={apiClient}
            onPanelModeChange={setTeamPanelMode}
            onSave={onSaveTeam}
            panelMode={teamPanelMode}
            teamContext={teamContext}
          />
        ) : null}
      </aside>
    </div>
  );
}

function SettingsHome({
  apiConfigured,
  currentPersona,
  onClearSession,
  onNavigate,
  teamSize,
}: {
  apiConfigured: boolean;
  currentPersona: PersonaUiId;
  onClearSession: () => Promise<void>;
  onNavigate: (view: DrawerView) => void;
  teamSize: number;
}) {
  return (
    <div className="drawer-body home-grid">
      <SettingsCard
        icon={<Users size={19} />}
        label="队伍设置"
        meta={teamSize > 0 ? `当前队伍上下文 ${teamSize}/6` : "可选：为 Agent 提供结构化队伍上下文"}
        onClick={() => onNavigate("team")}
      />
      <SettingsCard
        icon={<KeyRound size={19} />}
        label="API 设置"
        meta={apiConfigured ? "模型服务已配置" : "填写你的 provider key / base URL / model"}
        onClick={() => onNavigate("api")}
      />
      <SettingsCard
        icon={<Bot size={19} />}
        label="人格设置"
        meta={`当前：${personaLabel(currentPersona)} · 长按聊天页面头像切换人格`}
      />
      <SettingsCard
        danger
        icon={<Trash2 size={19} />}
        label="清空当前对话"
        meta="归档并重置当前会话；队伍、人设和 API 设置保留"
        onClick={() => void onClearSession()}
      />
    </div>
  );
}

function SettingsCard({
  danger = false,
  icon,
  label,
  meta,
  onClick,
}: {
  danger?: boolean;
  icon: React.ReactNode;
  label: string;
  meta: string;
  onClick?: () => void;
}) {
  if (!onClick) {
    return (
      <div className="settings-card informational">
        <div className="settings-card-icon">{icon}</div>
        <div>
          <strong>{label}</strong>
          <span>{meta}</span>
        </div>
      </div>
    );
  }

  return (
    <button className={`settings-card ${danger ? "danger" : ""}`} onClick={onClick}>
      <div className="settings-card-icon">{icon}</div>
      <div>
        <strong>{label}</strong>
        <span>{meta}</span>
      </div>
    </button>
  );
}

function ApiSettings({
  apiClient,
  draft,
  onChange,
  onClearProviderKey,
  onSave,
}: {
  apiClient: ProductApiClient;
  draft: RuntimeSettings;
  onChange: (draft: RuntimeSettings) => void;
  onClearProviderKey: () => Promise<void>;
  onSave: (draft: RuntimeSettings) => Promise<void>;
}) {
  const [showKey, setShowKey] = useState(false);
  const [status, setStatus] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  async function testProductApi() {
    setBusy(true);
    setStatus(null);
    try {
      const [health, metadata] = await Promise.all([apiClient.health(), apiClient.metadata()]);
      setStatus(`Product API ok · ${health.release_stage} · battle dex ${metadata.battle_dex_available ? "ready" : "missing"}`);
    } catch (caught) {
      setStatus(caught instanceof Error ? caught.message : "Product API 测试失败。");
    } finally {
      setBusy(false);
    }
  }

  async function testModelService() {
    setBusy(true);
    setStatus(null);
    try {
      const result = await apiClient.modelDiagnostic(buildNativeRuntimeHeaders(draft));
      setStatus(`${result.status === "ok" ? "模型服务 ok" : "模型服务失败"} · ${result.message}`);
    } catch (caught) {
      setStatus(caught instanceof Error ? caught.message : "模型服务测试失败。");
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="drawer-body form">
      <div className="warning-box">
        <Shield size={18} />
        <p>API Key 只保存在本机 Electron 安全存储中，不写入聊天内容，不进 URL，不进仓库。别截图，别粘给模型。基础安全，别拿来献祭。</p>
      </div>
      <label>
        <span>Provider API Key</span>
        <div className="secret-field">
          <input
            autoComplete="off"
            onChange={(event) => onChange({ ...draft, providerKey: event.target.value })}
            placeholder="sk-..."
            type={showKey ? "text" : "password"}
            value={draft.providerKey}
          />
          <button onClick={() => setShowKey((value) => !value)} type="button">
            {showKey ? <EyeOff size={17} /> : <Eye size={17} />}
          </button>
        </div>
      </label>
      <label>
        <span>Provider Base URL</span>
        <input
          onChange={(event) => onChange({ ...draft, providerBaseUrl: event.target.value })}
          placeholder="https://api.deepseek.com"
          value={draft.providerBaseUrl}
        />
      </label>
      <label>
        <span>Model</span>
        <input
          onChange={(event) => onChange({ ...draft, model: event.target.value })}
          placeholder="deepseek-v4-pro"
          value={draft.model}
        />
      </label>
      <div className="inline-fields">
        <label>
          <span>思考模式</span>
          <select
            onChange={(event) =>
              onChange({ ...draft, thinkingMode: event.target.value === "enabled" ? "enabled" : "disabled" })
            }
            value={draft.thinkingMode}
          >
            <option value="enabled">enabled</option>
            <option value="disabled">disabled</option>
          </select>
        </label>
        <label>
          <span>Reasoning</span>
          <select
            disabled={draft.thinkingMode !== "enabled"}
            onChange={(event) =>
              onChange({
                ...draft,
                reasoningEffort: event.target.value === "max" ? "max" : event.target.value === "high" ? "high" : "none",
              })
            }
            value={draft.reasoningEffort}
          >
            <option value="high">high</option>
            <option value="max">max</option>
            <option value="none">none</option>
          </select>
        </label>
      </div>
      <div className="button-row">
        <button className="primary-button" disabled={busy} onClick={() => void onSave(draft)}>
          保存设置
        </button>
        <button disabled={busy} onClick={() => void testProductApi()}>
          测 Product API
        </button>
      </div>
      <div className="button-row">
        <button disabled={busy} onClick={() => void testModelService()}>
          测模型服务
        </button>
        <button className="danger-button" disabled={busy} onClick={() => void onClearProviderKey()}>
          清除 Key
        </button>
      </div>
      {status ? <p className="settings-status">{status}</p> : null}
    </div>
  );
}

function PersonaWheel({
  currentPersona,
  onClose,
  onSavePersona,
  onUnavailable,
  state,
}: {
  currentPersona: PersonaUiId;
  onClose: () => void;
  onSavePersona: (persona: PersonaUiId) => void;
  onUnavailable: () => void;
  state: PersonaWheelState;
}) {
  const [hoveredPersona, setHoveredPersona] = useState<PersonaUiId | "add_persona" | null>(null);

  if (state.status === "closed") {
    return null;
  }

  return (
    <div className="persona-wheel-layer" onClick={onClose}>
      <div
        className="persona-wheel-halo"
        style={{
          left: state.anchor.x - 46,
          top: state.anchor.y - 46,
        }}
      />
      <WheelButton
        active={currentPersona === "you_know_who"}
        angle={-42}
        anchor={state.anchor}
        highlighted={hoveredPersona === "you_know_who"}
        label="You know who"
        onHover={setHoveredPersona}
        onClick={() => onSavePersona("you_know_who")}
        variant="you_know_who"
      />
      <WheelButton
        active={currentPersona === "ai_assistant"}
        angle={8}
        anchor={state.anchor}
        highlighted={hoveredPersona === "ai_assistant"}
        label="默认AI助手"
        onHover={setHoveredPersona}
        onClick={() => onSavePersona("ai_assistant")}
        variant="ai_assistant"
      />
      <button
        className={`persona-wheel-button add ${hoveredPersona === "add_persona" ? "highlighted" : ""}`}
        onClick={(event) => {
          event.stopPropagation();
          onUnavailable();
        }}
        onPointerEnter={() => setHoveredPersona("add_persona")}
        onPointerLeave={() => setHoveredPersona(null)}
        style={positionFromAngle(state.anchor, 58)}
        title="新增人格"
      >
        <Plus size={24} />
      </button>
    </div>
  );
}

function WheelButton({
  active,
  angle,
  anchor,
  highlighted,
  label,
  onHover,
  onClick,
  variant,
}: {
  active: boolean;
  angle: number;
  anchor: { x: number; y: number };
  highlighted: boolean;
  label: string;
  onHover: (persona: PersonaUiId | null) => void;
  onClick: () => void;
  variant: PersonaUiId;
}) {
  return (
    <button
      className={`persona-wheel-button ${highlighted ? "highlighted" : ""}`}
      onClick={(event) => {
        event.stopPropagation();
        onClick();
      }}
      onPointerEnter={() => onHover(variant)}
      onPointerLeave={() => onHover(null)}
      style={positionFromAngle(anchor, angle)}
      title={label}
    >
      <AgentAvatar highlighted={highlighted} ring={false} size={52} variant={variant} />
      {active ? <span className="wheel-check">✓</span> : null}
    </button>
  );
}

function TeamSettings({
  apiClient,
  onPanelModeChange,
  onSave,
  panelMode,
  teamContext,
}: {
  apiClient: ProductApiClient;
  onPanelModeChange: (mode: TeamPanelMode) => void;
  onSave: (team: TeamContextAttachment) => void;
  panelMode: TeamPanelMode;
  teamContext: TeamContextAttachment;
}) {
  const [draft, setDraft] = useState<TeamContextAttachment>(teamContext);
  const [selectedSlotIndex, setSelectedSlotIndex] = useState<number>(teamContext.slots[0]?.slot_index ?? 1);
  const [inlinePanel, setInlinePanel] = useState<TeamInlinePanel>("closed");
  const [picker, setPicker] = useState<TeamPickerState>({ kind: "closed" });
  const [speciesQuery, setSpeciesQuery] = useState("");
  const [speciesResults, setSpeciesResults] = useState<SpeciesSearchItem[]>([]);
  const [movePools, setMovePools] = useState<Record<string, SpeciesMoveRecord[]>>({});
  const [moveQueries, setMoveQueries] = useState<Record<number, string>>({});
  const [status, setStatus] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const lastSavedTeamRef = useRef(JSON.stringify(normalizeDraft(teamContext)));
  const selectedSlot = draft.slots.find((slot) => slot.slot_index === selectedSlotIndex) ?? null;

  useEffect(() => {
    lastSavedTeamRef.current = JSON.stringify(normalizeDraft(teamContext));
    setDraft(teamContext);
    setSelectedSlotIndex((current) => Math.min(Math.max(current, 1), 6));
  }, [teamContext]);

  useEffect(() => {
    const normalized = normalizeDraft(draft);
    const serialized = JSON.stringify(normalized);
    if (serialized === lastSavedTeamRef.current) {
      return;
    }
    const timer = window.setTimeout(() => {
      lastSavedTeamRef.current = serialized;
      onSave(normalized);
      setStatus(normalized.slots.length > 0 ? "已实时保存。" : "已清空。");
    }, 120);
    return () => window.clearTimeout(timer);
  }, [draft, onSave]);

  useEffect(() => {
    let active = true;
    const query = speciesQuery.trim();
    if (picker.kind !== "species") {
      return () => {
        active = false;
      };
    }
    if (!query) {
      setSpeciesResults([]);
      setStatus(null);
      return () => {
        active = false;
      };
    }
    const timer = window.setTimeout(() => {
      void searchSpeciesForQuery(query, () => active);
    }, 260);
    return () => {
      active = false;
      window.clearTimeout(timer);
    };
  }, [picker.kind, speciesQuery]);

  async function searchSpeciesForQuery(query: string, isActive: () => boolean) {
    setLoading(true);
    setStatus(null);
    try {
      const payload = await apiClient.searchSpecies(query, 50, "team_builder");
      if (!isActive()) {
        return;
      }
      setSpeciesResults(payload.results);
    } catch (caught) {
      if (isActive()) {
        setStatus(caught instanceof Error ? caught.message : "精灵搜索失败。");
      }
    } finally {
      if (isActive()) {
        setLoading(false);
      }
    }
  }

  async function ensureMovePool(speciesId: string) {
    if (movePools[speciesId]) {
      return;
    }
    try {
      const payload = await apiClient.speciesMoves(speciesId);
      setMovePools((current) => ({ ...current, [speciesId]: payload.moves }));
    } catch (caught) {
      setStatus(caught instanceof Error ? caught.message : "技能列表载入失败。");
    }
  }

  async function selectSpecies(item: SpeciesSearchItem) {
    const slotIndex = picker.kind === "species" ? picker.slotIndex : selectedSlotIndex;
    if (draft.slots.length >= 6 && !draft.slots.some((slot) => slot.slot_index === slotIndex)) {
      setStatus("队伍最多 6 只。");
      return;
    }
    setLoading(true);
    setStatus(null);
    try {
      const [profileResponse, movesResponse] = await Promise.all([
        apiClient.speciesProfile(item.species_id),
        apiClient.speciesMoves(item.species_id),
      ]);
      const profile = profileResponse.profile;
      const slot: TeamContextSlot = {
        slot_index: slotIndex,
        species_id: asString(profile.species_id, item.species_id),
        display_name: speciesDisplayLabel({
          display_name: asString(profile.display_name, item.display_name),
          regional_form_name: asOptionalString(profile.regional_form_name ?? item.regional_form_name),
        }),
        primary_type: asString(profile.primary_type, item.primary_type),
        secondary_type: asOptionalString(profile.secondary_type ?? item.secondary_type),
        fixed_ability: abilityFromProfile(profile),
        selected_moves: [],
        nature: {
          label: DEFAULT_NATURE.label,
          plus_stat: DEFAULT_NATURE.plus,
          minus_stat: DEFAULT_NATURE.minus,
        },
        individual_value_bonuses: [],
        notes: null,
      };
      setMovePools((current) => ({ ...current, [slot.species_id]: movesResponse.moves }));
      setDraft((current) => replaceSlot(current, slot));
      setSelectedSlotIndex(slotIndex);
      setPicker({ kind: "closed" });
      setSpeciesQuery("");
      setSpeciesResults([]);
    } catch (caught) {
      setStatus(caught instanceof Error ? caught.message : "载入精灵资料失败。");
    } finally {
      setLoading(false);
    }
  }

  function removeSlot(slotIndex: number) {
    setDraft((current) => ({
      ...current,
      slots: current.slots.filter((slot) => slot.slot_index !== slotIndex),
    }));
    setSelectedSlotIndex(slotIndex);
    setPicker({ kind: "closed" });
  }

  function updateSlot(slot: TeamContextSlot) {
    setDraft((current) => replaceSlot(current, slot));
  }

  function openSlotDetail(slotIndex: number) {
    const slot = draft.slots.find((item) => item.slot_index === slotIndex);
    setSelectedSlotIndex(slotIndex);
    onPanelModeChange("detail");
    setInlinePanel("closed");
    setPicker({ kind: "closed" });
    setSpeciesQuery("");
    setSpeciesResults([]);
    if (slot) {
      void ensureMovePool(slot.species_id);
    }
  }

  function openSpeciesPicker(slotIndex: number) {
    setInlinePanel("closed");
    setSelectedSlotIndex(slotIndex);
    setSpeciesQuery("");
    setSpeciesResults([]);
    setPicker({ kind: "species", slotIndex });
  }

  function updateSpeciesQuery(slotIndex: number, value: string) {
    setSelectedSlotIndex(slotIndex);
    setPicker({ kind: "species", slotIndex });
    setSpeciesQuery(value);
  }

  async function openMovePicker(slot: TeamContextSlot, activeCell = Math.min(slot.selected_moves.length, 3)) {
    await ensureMovePool(slot.species_id);
    setInlinePanel("closed");
    setMoveQueries((current) => ({ ...current, [slot.slot_index]: current[slot.slot_index] ?? "" }));
    setPicker({ kind: "moves", slotIndex: slot.slot_index, activeCell });
  }

  function updateNatureLabel(slot: TeamContextSlot, label: string) {
    const option = NATURE_OPTIONS.find((item) => item.label === label) ?? DEFAULT_NATURE;
    updateSlot({
      ...slot,
      nature: { label: option.label, plus_stat: option.plus, minus_stat: option.minus },
    });
  }

  function updateNatureStat(slot: TeamContextSlot, side: "plus" | "minus", value: string) {
    const current = resolveNatureOption(slot);
    const nextPlus = side === "plus" ? (value as TeamStatKey) : current.plus;
    const nextMinus = side === "minus" ? (value as TeamStatKey) : current.minus;
    const exact = NATURE_OPTIONS.find((nature) => nature.plus === nextPlus && nature.minus === nextMinus);
    const fallback =
      side === "plus"
        ? NATURE_OPTIONS.find((nature) => nature.plus === nextPlus)
        : NATURE_OPTIONS.find((nature) => nature.minus === nextMinus);
    const option = exact ?? fallback ?? current;
    updateSlot({
      ...slot,
      nature: {
        label: option.label,
        plus_stat: option.plus,
        minus_stat: option.minus,
      },
    });
  }

  function updateBonusStat(slot: TeamContextSlot, rowIndex: number, value: string) {
    const current = [...slot.individual_value_bonuses.slice(0, 3)];
    if (!value) {
      current.splice(rowIndex, 1);
    } else {
      const stat = value as TeamStatKey;
      const existingValue = current[rowIndex]?.value ?? 8;
      current[rowIndex] = { stat, value: existingValue };
    }
    const deduped = current.filter((bonus, index) => {
      if (!bonus) {
        return false;
      }
      return current.findIndex((candidate) => candidate?.stat === bonus.stat) === index;
    });
    updateSlot({ ...slot, individual_value_bonuses: deduped.slice(0, 3) });
  }

  function updateBonusValue(slot: TeamContextSlot, rowIndex: number, value: number) {
    const current = [...slot.individual_value_bonuses.slice(0, 3)];
    if (!current[rowIndex]) {
      return;
    }
    current[rowIndex] = { ...current[rowIndex], value };
    updateSlot({ ...slot, individual_value_bonuses: current });
  }

  function updateMove(slot: TeamContextSlot, cellIndex: number, move: SpeciesMoveRecord) {
    const nextMoves = [...slot.selected_moves];
    nextMoves[cellIndex] = moveSelectionFromRecord(move);
    updateSlot({ ...slot, selected_moves: nextMoves.slice(0, 4).filter(Boolean) });
    setPicker({ kind: "closed" });
  }

  function clearMove(slot: TeamContextSlot, cellIndex: number) {
    updateSlot({
      ...slot,
      selected_moves: slot.selected_moves.filter((_, index) => index !== cellIndex),
    });
    setPicker({ kind: "closed" });
  }

  if (panelMode === "board") {
    return (
      <div className="drawer-body form team-builder team-builder-board-mode">
        <TeamCardBoard
          onOpenSlot={openSlotDetail}
          selectedSlotIndex={selectedSlotIndex}
          slots={draft.slots}
        />
        {status ? <p className="settings-status">{status}</p> : null}
      </div>
    );
  }

  return (
    <div className="drawer-body form team-builder team-builder-detail-mode">
      {selectedSlot ? (
        <div className="team-editor creature-card-stage">
          <section className="creature-config-card" aria-label={`${selectedSlot.display_name} 单卡配置`}>
          <button
            className="creature-title-field editable-card-field"
            onClick={() => openSpeciesPicker(selectedSlot.slot_index)}
            type="button"
          >
            <span className="slot-mark">Slot {String(selectedSlot.slot_index).padStart(2, "0")}</span>
            <span className="creature-name-row">
              <strong>{selectedSlot.display_name}</strong>
              <span className="type-pill">{selectedSlot.primary_type}</span>
              {selectedSlot.secondary_type ? <span className="type-pill muted-type">{selectedSlot.secondary_type}</span> : null}
            </span>
          </button>

          <div className="creature-art-frame">
            <span className="creature-silhouette" aria-hidden="true" />
            <span className="ability-hang">
              <span>特性</span>
              <strong>{selectedSlot.fixed_ability?.ability_name ?? "未提供"}</strong>
            </span>
          </div>

          <div className="creature-info-band">
            <button
              className="nature-summary editable-card-field"
              onClick={() => {
                setPicker({ kind: "closed" });
                setInlinePanel(inlinePanel === "nature" ? "closed" : "nature");
              }}
              type="button"
            >
              <span>性格</span>
              <strong>{resolveNatureOption(selectedSlot).label}</strong>
            </button>
            <button
              className="iv-summary editable-card-field"
              onClick={() => {
                setPicker({ kind: "closed" });
                setInlinePanel(inlinePanel === "iv" ? "closed" : "iv");
              }}
              type="button"
            >
              {Array.from({ length: 3 }, (_, index) => {
                const bonus = selectedSlot.individual_value_bonuses[index];
                return bonus ? (
                  <span className="iv-token" key={`${bonus.stat}-${index}`}>
                    <span>{STAT_LABELS[bonus.stat]}</span>
                    <IvGlyph value={bonus.value} />
                  </span>
                ) : (
                  <span className="iv-token empty" key={`empty-iv-${index}`}>
                    <span>空</span>
                    <IvGlyph value={null} />
                  </span>
                );
              })}
            </button>
          </div>

          <div className="creature-skills">
            <span className="creature-section-label">技能</span>
            <div className="creature-skill-grid">
              {Array.from({ length: 4 }, (_, index) => {
                const move = selectedSlot.selected_moves[index] ?? null;
                return (
                  <button
                    className={`creature-skill-cell editable-card-field ${
                      picker.kind === "moves" && picker.activeCell === index ? "active" : ""
                    }`}
                    key={`skill-${index}`}
                    onClick={() => void openMovePicker(selectedSlot, index)}
                    type="button"
                  >
                    <span className="move-type-dot">{move?.move_type ?? "—"}</span>
                    <strong>{move?.move_name ?? "空技能"}</strong>
                    <MoveCategoryIcon category={move?.category_raw} />
                  </button>
                );
              })}
            </div>
          </div>
          </section>

          {inlinePanel !== "closed" || picker.kind !== "closed" ? (
            <div className="card-config-overlay" onClick={() => {
              setInlinePanel("closed");
              setPicker({ kind: "closed" });
            }}>
              <div className="card-config-modal" onClick={(event) => event.stopPropagation()}>
          {inlinePanel === "nature" ? (
            <div className="mini-config-panel">
              <div className="mini-config-header">
                <strong>性格</strong>
                <button onClick={() => setInlinePanel("closed")} type="button">
                  <X size={14} />
                </button>
              </div>
            <div className="nature-linked-row">
              <select
                aria-label="增益属性"
                onChange={(event) => updateNatureStat(selectedSlot, "plus", event.target.value)}
                value={resolveNatureOption(selectedSlot).plus}
              >
                {STAT_KEYS.map((stat) => (
                  <option key={stat} value={stat}>
                    + {STAT_LABELS[stat]}
                  </option>
                ))}
              </select>
              <select
                aria-label="性格"
                onChange={(event) => updateNatureLabel(selectedSlot, event.target.value)}
                value={resolveNatureOption(selectedSlot).label}
              >
                {NATURE_OPTIONS.map((nature) => (
                  <option key={nature.label} value={nature.label}>
                    {nature.label}
                  </option>
                ))}
              </select>
              <select
                aria-label="减益属性"
                onChange={(event) => updateNatureStat(selectedSlot, "minus", event.target.value)}
                value={resolveNatureOption(selectedSlot).minus}
              >
                {STAT_KEYS.map((stat) => (
                  <option key={stat} value={stat}>
                    - {STAT_LABELS[stat]}
                  </option>
                ))}
              </select>
            </div>
            </div>
          ) : null}

          {inlinePanel === "iv" ? (
            <div className="mini-config-panel">
              <div className="mini-config-header">
                <strong>个体</strong>
                <button onClick={() => setInlinePanel("closed")} type="button">
                  <X size={14} />
                </button>
              </div>
              <p className="mini-config-tip">填入初始个体即可，PvP 系统会自动调整。</p>
            <div className="bonus-column">
              {Array.from({ length: 3 }, (_, index) => {
                const bonus = selectedSlot.individual_value_bonuses[index];
                return (
                  <div className="bonus-picker-row" key={`bonus-${index}`}>
                    <select
                      aria-label={`个体增益属性 ${index + 1}`}
                      onChange={(event) => updateBonusStat(selectedSlot, index, event.target.value)}
                      value={bonus?.stat ?? ""}
                    >
                      <option value="">无</option>
                      {STAT_KEYS.map((stat) => (
                        <option key={stat} value={stat}>
                          {STAT_LABELS[stat]}
                        </option>
                      ))}
                    </select>
                    <select
                      aria-label={`个体增益数值 ${index + 1}`}
                      disabled={!bonus}
                      onChange={(event) => updateBonusValue(selectedSlot, index, Number(event.target.value))}
                      value={bonus?.value ?? 8}
                    >
                      {IV_VALUES.map((value) => (
                        <option key={value} value={value}>
                          +{value}
                        </option>
                      ))}
                    </select>
                  </div>
                );
              })}
            </div>
            </div>
          ) : null}

          {picker.kind === "moves" ? (
            <MovePicker
              activeCell={picker.activeCell}
              movePool={movePools[selectedSlot.species_id] ?? []}
              onActiveCellChange={(activeCell) => setPicker({ ...picker, activeCell })}
              onClear={() => clearMove(selectedSlot, picker.activeCell)}
              onClose={() => setPicker({ kind: "closed" })}
              onMoveQueryChange={(value) =>
                setMoveQueries((current) => ({ ...current, [selectedSlot.slot_index]: value }))
              }
              onSelectMove={(move) => updateMove(selectedSlot, picker.activeCell, move)}
              query={moveQueries[selectedSlot.slot_index] ?? ""}
              selectedMoves={selectedSlot.selected_moves}
            />
          ) : null}

          {picker.kind === "species" ? (
            <SpeciesSearchPanel
              loading={loading}
              onClose={() => setPicker({ kind: "closed" })}
              onQueryChange={setSpeciesQuery}
              onSelect={(item) => void selectSpecies(item)}
              query={speciesQuery}
              results={speciesResults}
              title={`更换精灵 · 槽位 ${picker.slotIndex}`}
            />
          ) : null}
              </div>
            </div>
          ) : null}
        </div>
      ) : (
        <div className="empty-slot-editor creature-card-stage">
          <section className="creature-config-card empty-creature-card">
            <button
              className="creature-title-field empty-title-field editable-card-field"
              onClick={() => openSpeciesPicker(selectedSlotIndex)}
              type="button"
            >
              <span className="slot-mark">Slot {String(selectedSlotIndex).padStart(2, "0")}</span>
              <span className="creature-name-row">
                <strong>选择精灵</strong>
              </span>
            </button>
            <div className="creature-art-frame">
              <span className="creature-silhouette empty" aria-hidden="true" />
            </div>
            <div className="empty-card-hint">点击精灵名，从本地数据库检索并插入一张精灵卡。</div>
          </section>
          {picker.kind === "species" ? (
            <div className="card-config-overlay" onClick={() => setPicker({ kind: "closed" })}>
              <div className="card-config-modal" onClick={(event) => event.stopPropagation()}>
                <SpeciesSearchPanel
                  loading={loading}
                  onClose={() => setPicker({ kind: "closed" })}
                  onQueryChange={(value) => updateSpeciesQuery(selectedSlotIndex, value)}
                  onSelect={(item) => void selectSpecies(item)}
                  query={picker.slotIndex === selectedSlotIndex ? speciesQuery : ""}
                  results={picker.slotIndex === selectedSlotIndex ? speciesResults : []}
                  title={`选择精灵 · 槽位 ${selectedSlotIndex}`}
                />
              </div>
            </div>
          ) : null}
        </div>
      )}

      {status ? <p className="settings-status">{status}</p> : null}
    </div>
  );
}

function TeamCardBoard({
  onOpenSlot,
  selectedSlotIndex,
  slots,
}: {
  onOpenSlot: (slotIndex: number) => void;
  selectedSlotIndex: number;
  slots: TeamContextSlot[];
}) {
  return (
    <section className="team-card-board" aria-label="队伍卡组">
      <div className="team-board-hero">
        <span>Battle Loadout</span>
      </div>
      <div className="team-card-grid" role="list">
        {Array.from({ length: 6 }, (_, index) => {
          const slotIndex = index + 1;
          const slot = slots.find((item) => item.slot_index === slotIndex);
          return (
            <button
              className={`team-card-slot ${slot ? "filled" : "empty"} ${
                slot && selectedSlotIndex === slotIndex ? "active" : ""
              }`}
              key={slotIndex}
              onClick={() => onOpenSlot(slotIndex)}
              role="listitem"
              type="button"
            >
              <span className="team-card-art" aria-hidden="true">
                <span />
              </span>
              <span className="team-card-meta">
                <strong>{slot?.display_name ?? "空卡位"}</strong>
                <small>
                  {slot
                    ? `${slot.primary_type}${slot.secondary_type ? ` / ${slot.secondary_type}` : ""}`
                    : ""}
                </small>
              </span>
            </button>
          );
        })}
      </div>
      <p className="team-board-footer">点击任意卡位进入单卡配置</p>
    </section>
  );
}

function IvGlyph({ value }: { value: number | null }) {
  const filled = value == null ? 0 : Math.max(0, Math.min(4, value - 6));
  return (
    <span className="iv-glyph" aria-label={value == null ? "未设置" : `个体 ${value}`}>
      {[4, 3, 2, 1].map((level) => (
        <span className={filled >= level ? "filled" : ""} key={level} />
      ))}
    </span>
  );
}

function MoveCategoryIcon({ category }: { category: string | null | undefined }) {
  const icon = moveCategoryClass(category);
  return (
    <span className={`move-category-icon ${icon}`} aria-hidden="true">
      {icon === "physical" ? (
        <svg viewBox="0 0 24 24">
          <path d="M4.7 19.7a1.4 1.4 0 1 0 2.8 0 1.4 1.4 0 0 0-2.8 0" />
          <path d="M7.1 17.9l2.1-2.1" />
          <path d="M6.2 13.8l4.2 4.2" />
          <path d="M8.8 14.9l7.4-10 3.6-.8-.8 3.6-10 7.4" />
          <path className="gold-stroke" d="M15.3 7.7l-4.9 4.9" />
        </svg>
      ) : null}
      {icon === "magical" ? (
        <svg viewBox="0 0 24 24">
          <path d="M4.5 20L14.7 9.8" />
          <path d="M16.7 2.5l1.7 3.4 3.6.7-2.7 2.7.6 3.7-3.2-1.7-3.3 1.7.7-3.7-2.7-2.7 3.6-.7z" />
          <path className="gold-fill" d="M16.7 6.2l.7 1.3 1.4.3-1 .9.2 1.5-1.3-.7-1.3.7.2-1.5-1-.9 1.4-.3z" />
        </svg>
      ) : null}
      {icon === "defense" ? (
        <svg viewBox="0 0 24 24">
          <path d="M12 3.3l6.2 2.6v5.4c0 4.2-2.3 7.2-6.2 9.1-3.9-1.9-6.2-4.9-6.2-9.1V5.9z" />
          <path className="gold-stroke" d="M9 7.9v4.4c0 2 .8 3.5 2.2 4.7" />
        </svg>
      ) : null}
      {icon === "status" ? (
        <svg viewBox="0 0 24 24">
          <path d="M18.7 18.1c-2 1.7-5.3 2.1-8 .8-3.6-1.8-4.7-5.9-2.5-8.8 2.2-3 6.5-3.8 9.1-1.7 2.3 1.8 2.6 5 .6 6.9-1.7 1.6-4.3 1.5-5.6-.1-1-1.2-.7-2.8.5-3.4.9-.5 2-.2 2.4.6" />
        </svg>
      ) : null}
    </span>
  );
}

function moveCategoryClass(category: string | null | undefined) {
  const normalized = category ?? "";
  if (normalized.includes("物")) {
    return "physical";
  }
  if (normalized.includes("魔")) {
    return "magical";
  }
  if (normalized.includes("防")) {
    return "defense";
  }
  if (normalized.includes("状态") || normalized.includes("变化")) {
    return "status";
  }
  return "status";
}

function SpeciesSearchPanel({
  loading,
  onClose,
  onQueryChange,
  onSelect,
  query,
  results,
  title,
}: {
  loading: boolean;
  onClose: (() => void) | null;
  onQueryChange: (value: string) => void;
  onSelect: (item: SpeciesSearchItem) => void;
  query: string;
  results: SpeciesSearchItem[];
  title: string | null;
}) {
  return (
    <div className="selection-card species-search-card">
      {title || onClose ? (
        <div className="selection-card-header">
          <strong>{title ?? "选择精灵"}</strong>
          {onClose ? (
            <button onClick={onClose} type="button">
              <X size={15} />
            </button>
          ) : null}
        </div>
      ) : null}
      <input
        autoFocus
        onChange={(event) => onQueryChange(event.target.value)}
        placeholder="搜索精灵名称 / 初始形态"
        value={query}
      />
      <p className="muted">搜索规则：精灵名或其初始形态包含关键词。</p>
      {loading ? <p className="settings-status">搜索中...</p> : null}
      <div className="search-results">
        {query.trim() && !loading && results.length === 0 ? (
          <p className="empty-result">数据库没有匹配精灵。</p>
        ) : null}
        {results.map((item) => (
          <button key={item.species_id} onClick={() => onSelect(item)} type="button">
            <strong>{speciesDisplayLabel(item)}</strong>
            <span>{speciesResultMeta(item)}</span>
          </button>
        ))}
      </div>
    </div>
  );
}

function MovePicker({
  activeCell,
  movePool,
  onActiveCellChange,
  onClear,
  onClose,
  onMoveQueryChange,
  onSelectMove,
  query,
  selectedMoves,
}: {
  activeCell: number;
  movePool: SpeciesMoveRecord[];
  onActiveCellChange: (cell: number) => void;
  onClear: () => void;
  onClose: () => void;
  onMoveQueryChange: (value: string) => void;
  onSelectMove: (move: SpeciesMoveRecord) => void;
  query: string;
  selectedMoves: TeamMoveSelection[];
}) {
  const filteredMoves = movePool
    .filter((move) => move.move_id)
    .filter((move) => !query.trim() || move.move_name.includes(query.trim()))
    .slice(0, 24);

  return (
    <div className="selection-card move-search-card">
      <div className="selection-card-header">
        <strong>修改技能</strong>
        <button onClick={onClose} type="button">
          <X size={15} />
        </button>
      </div>
      <div className="move-edit-strip">
        {Array.from({ length: 4 }, (_, index) => (
          <button
            className={`move-edit-tab ${activeCell === index ? "active" : ""}`}
            key={`move-cell-${index}`}
            onClick={() => onActiveCellChange(index)}
            type="button"
          >
            {selectedMoves[index]?.move_name ?? "空技能"}
          </button>
        ))}
      </div>
      <div className="search-row">
        <input
          onChange={(event) => onMoveQueryChange(event.target.value)}
          placeholder="搜索该精灵可用技能"
          value={query}
        />
        <button onClick={onClear} type="button">
          清空
        </button>
      </div>
      <div className="search-results">
        {filteredMoves.length === 0 ? <p className="empty-result">没有匹配技能。</p> : null}
        {filteredMoves.map((move) => (
          <button
            key={`${move.move_id ?? move.move_name}-${move.access_channel}`}
            onClick={() => onSelectMove(move)}
            type="button"
          >
            <strong>{move.move_name}</strong>
            <span>
              {move.move_type ?? "-"} · {move.category_raw ?? "-"} · {move.access_channel}
            </span>
          </button>
        ))}
      </div>
    </div>
  );
}

function resolveNatureOption(slot: TeamContextSlot): NatureOption {
  return (
    NATURE_OPTIONS.find((nature) => nature.label === slot.nature.label) ??
    NATURE_OPTIONS.find(
      (nature) => nature.plus === slot.nature.plus_stat && nature.minus === slot.nature.minus_stat,
    ) ??
    DEFAULT_NATURE
  );
}

function normalizeDraft(draft: TeamContextAttachment): TeamContextAttachment {
  return {
    ...draft,
    slots: draft.slots
      .slice(0, 6)
      .sort((left, right) => left.slot_index - right.slot_index)
      .map((slot) => ({
        ...slot,
        selected_moves: slot.selected_moves.slice(0, 4),
        individual_value_bonuses: slot.individual_value_bonuses.slice(0, 3),
      })),
  };
}

function replaceSlot(team: TeamContextAttachment, slot: TeamContextSlot): TeamContextAttachment {
  return {
    ...team,
    slots: [...team.slots.filter((item) => item.slot_index !== slot.slot_index), slot].sort(
      (left, right) => left.slot_index - right.slot_index,
    ),
  };
}

function moveSelectionFromRecord(move: SpeciesMoveRecord): TeamMoveSelection {
  return {
    move_id: move.move_id ?? "",
    move_name: move.move_name,
    access_channel: move.access_channel,
    move_type: move.move_type,
    category_raw: move.category_raw,
  };
}

function abilityFromProfile(profile: Record<string, unknown>) {
  const abilityName = asOptionalString(profile.ability_name);
  if (!abilityName) {
    return null;
  }
  return {
    ability_name: abilityName,
    effect_text: asOptionalString(profile.ability_effect_text),
  };
}

function speciesDisplayLabel(
  species: Pick<SpeciesSearchItem, "display_name" | "regional_form_name">,
) {
  const regional = species.regional_form_name?.trim();
  return regional ? `${species.display_name}（${regional}）` : species.display_name;
}

function speciesResultMeta(result: SpeciesSearchItem) {
  const parts = [
    result.initial_species_name ? `初始形态 ${result.initial_species_name}` : null,
    result.form_name,
    result.primary_type + (result.secondary_type ? ` / ${result.secondary_type}` : ""),
  ];
  return parts.filter(Boolean).join(" · ");
}

function asString(value: unknown, fallback: string): string {
  return typeof value === "string" && value.trim() ? value : fallback;
}

function asOptionalString(value: unknown): string | null {
  return typeof value === "string" && value.trim() ? value : null;
}

function resolveVisibleReply(response: ChatResponse): string {
  const agentResponse: AgentResponse = response.response;
  if (agentResponse.status === "failed" || agentResponse.analysis_type === "runtime_failure") {
    return "模型服务调用失败。打开右侧设置，先测试 Product API 和模型服务。";
  }
  const personaAnswer = agentResponse.persona?.rendered_answer?.trim();
  const candidate =
    personaAnswer &&
    agentResponse.persona?.public_safe === true &&
    agentResponse.persona.facts_locked === true &&
    agentResponse.persona.fact_policy === "persona_may_not_alter_facts"
      ? personaAnswer
      : agentResponse.presentation?.reply ?? agentResponse.answer;
  return compactReply(candidate);
}

function compactReply(reply: string): string {
  return reply
    .replace(/^答复（暂定）：/, "")
    .replace(/^答复：/, "")
    .replace(/^硬结论：/, "")
    .replace(/^You know who｜收口结论\s*/i, "")
    .replace(/\bbackend\b/gi, "")
    .replace(/\bruntime\b/gi, "")
    .replace(/\bdoctrine\b/gi, "")
    .replace(/\bgrounded\b/gi, "可靠")
    .replace(/\s+/g, " ")
    .trim();
}

function normalizeError(message: string): string {
  if (message.includes("Provider") || message.includes("not configured") || message.includes("missing")) {
    return "模型服务还没配置完整。打开右侧设置 → API 设置，填写 Provider API key、Provider base URL 和 Model，保存后先测试模型服务。";
  }
  return message || "模型服务调用失败。";
}

function loadPersonaUiId(): PersonaUiId {
  return localStorage.getItem(PERSONA_KEY) === "ai_assistant" ? "ai_assistant" : "you_know_who";
}

function loadActiveSessionId(): string | null {
  const stored = localStorage.getItem(SESSION_KEY);
  return stored && stored.trim() ? stored : null;
}

function saveActiveSessionId(sessionId: string) {
  localStorage.setItem(SESSION_KEY, sessionId);
}

function loadVisibleMessages(sessionId: string | null): Message[] {
  if (!sessionId) {
    return [];
  }
  const raw = localStorage.getItem(MESSAGES_KEY_PREFIX + sessionId);
  if (!raw) {
    return [];
  }
  try {
    const parsed = JSON.parse(raw) as Message[];
    if (Array.isArray(parsed)) {
      return parsed.filter(isPersistableMessage);
    }
  } catch {
    return [];
  }
  return [];
}

function saveVisibleMessages(sessionId: string, messages: Message[]) {
  const persistable = messages.filter((message) => message.status !== "thinking");
  localStorage.setItem(MESSAGES_KEY_PREFIX + sessionId, JSON.stringify(persistable));
}

function isPersistableMessage(value: unknown): value is Message {
  if (!value || typeof value !== "object") {
    return false;
  }
  const message = value as Partial<Message>;
  return (
    typeof message.id === "string" &&
    (message.role === "user" || message.role === "agent") &&
    typeof message.text === "string" &&
    (message.status === "sent" || message.status === "failed")
  );
}

function loadTeamContext(): TeamContextAttachment {
  const fallback: TeamContextAttachment = {
    kind: "team_context",
    schema_version: "team_context.v1",
    source: "team_builder",
    team_id: createTeamId(),
    active: true,
    slots: [],
  };
  const raw = localStorage.getItem(TEAM_STORE_KEY);
  if (!raw) {
    return fallback;
  }
  try {
    const parsed = JSON.parse(raw) as TeamContextAttachment;
    if (parsed.kind === "team_context" && Array.isArray(parsed.slots)) {
      return parsed;
    }
  } catch {
    return fallback;
  }
  return fallback;
}

function createTeamId(): string {
  return `team-${Date.now()}-${Math.round(Math.random() * 10000)}`;
}

function createMessageId(prefix: "user" | "agent") {
  return `${prefix}-${Date.now()}-${Math.round(Math.random() * 10000)}`;
}

function personaLabel(persona: PersonaUiId) {
  return persona === "ai_assistant" ? "默认AI助手" : "You know who";
}

function viewTitle(view: DrawerView) {
  switch (view) {
    case "api":
      return "API 设置";
    case "team":
      return "队伍设置";
    default:
      return "设置";
  }
}

function positionFromAngle(anchor: { x: number; y: number }, angleDeg: number): React.CSSProperties {
  const radius = 86;
  const rad = (angleDeg * Math.PI) / 180;
  return {
    left: anchor.x + Math.cos(rad) * radius - 28,
    top: anchor.y + Math.sin(rad) * radius - 28,
  };
}
