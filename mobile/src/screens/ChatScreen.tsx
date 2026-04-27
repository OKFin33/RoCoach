import * as Clipboard from "expo-clipboard";
import React, { useRef, useState } from "react";
import {
  ImageBackground,
  KeyboardAvoidingView,
  LayoutChangeEvent,
  Platform,
  ScrollView,
  StyleSheet,
  Text,
  TextInput,
  TouchableOpacity,
  View,
  type ImageSourcePropType,
} from "react-native";

import { ProductApiClient } from "../api/client";
import type { AgentResponse } from "../api/types";
import { AgentAvatar, UserAvatar } from "../components/AgentAvatar";
import { AnalysisCard } from "../components/AnalysisCard";
import { PersonaSelectorPanel } from "../components/PersonaSelectorPanel";
import { PromptComposer } from "../components/PromptComposer";
import {
  buildPersonaSelectorPayload,
  createDefaultPersonaSelectorDraft,
  personaSelectorDraftError,
  type PersonaSelectorDraft,
} from "../persona/personaSelector";
import { buildNativeRuntimeHeaders, type RuntimeSettings } from "../runtime/runtimeSettings";
import { rnTokens } from "../styles/rnHandoffTokens";

type ChatScreenProps = {
  apiClient: ProductApiClient;
  runtimeSettings: RuntimeSettings;
  secureStoreAvailable: boolean;
};

type ChatMessage =
  | { id: string; role: "user"; text: string }
  | { id: string; role: "agent"; response: AgentResponse };

type ActionMenuState = {
  confirmDelete: boolean;
  messageId: string;
  role: ChatMessage["role"];
};

type PaperSize = {
  width: number;
  height: number;
};

const paperShellSource: ImageSourcePropType = require("../../assets/roco-paper-shell.png");
const PAPER_ASSET_SIZE = { height: 1616, width: 915 };
const PAPER_SAFE_AREA = {
  bottom: 118,
  left: 102,
  right: 102,
  top: 176,
};

export function ChatScreen({ apiClient, runtimeSettings, secureStoreAvailable }: ChatScreenProps) {
  const scrollRef = useRef<ScrollView>(null);
  const [message, setMessage] = useState("");
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [personaDraft, setPersonaDraft] = useState<PersonaSelectorDraft>(createDefaultPersonaSelectorDraft);
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [notice, setNotice] = useState<string | null>(null);
  const [personaSelectorOpen, setPersonaSelectorOpen] = useState(false);
  const [personaAnchor, setPersonaAnchor] = useState<{ x: number; y: number } | null>(null);
  const [loading, setLoading] = useState(false);
  const [actionMenu, setActionMenu] = useState<ActionMenuState | null>(null);
  const [editingMessageId, setEditingMessageId] = useState<string | null>(null);
  const [editingText, setEditingText] = useState("");
  const [paperSize, setPaperSize] = useState<PaperSize>(PAPER_ASSET_SIZE);

  const latestUserMessageId = findLatestUserMessageId(messages);
  const personaVariant = personaDraft.personaId === "lattice_support_coach" ? "ai_assistant" : "you_know_who";

  function onPaperLayout(event: LayoutChangeEvent) {
    setPaperSize(event.nativeEvent.layout);
  }

  function openActionMenu(item: ChatMessage) {
    if (editingMessageId) {
      return;
    }
    setActionMenu({ confirmDelete: false, messageId: item.id, role: item.role });
  }

  function openPersonaSelector(anchor: { x: number; y: number }) {
    setPersonaAnchor(anchor);
    setPersonaSelectorOpen(true);
  }

  async function sendMessage() {
    const text = message.trim();
    if (!text) {
      setError("消息不能为空。");
      return;
    }
    setMessage("");
    await requestAgentReply(text, { appendUser: true });
  }

  async function requestAgentReply(text: string, options: { appendUser: boolean }) {
    const personaError = personaSelectorDraftError(personaDraft);
    if (personaError) {
      setError(personaError);
      return;
    }
    const runtimeHeaders = buildNativeRuntimeHeaders(runtimeSettings, { secureStoreAvailable });
    if (!runtimeHeaders.ok) {
      setError(runtimeHeaders.error);
      return;
    }

    const trimmedText = text.trim();
    if (!trimmedText) {
      setError("消息不能为空。");
      return;
    }

    setActionMenu(null);
    setError(null);
    setNotice(null);
    setLoading(true);

    if (options.appendUser) {
      const userMessage: ChatMessage = {
        id: `user-${Date.now()}`,
        role: "user",
        text: trimmedText,
      };
      setMessages((current) => [...current, userMessage]);
    }

    try {
      const result = await apiClient.chat(
        {
          message: trimmedText,
          session_id: sessionId,
          ...buildPersonaSelectorPayload(personaDraft),
        },
        runtimeHeaders.headers,
      );
      setSessionId(result.session_id);
      setMessages((current) => [
        ...current,
        {
          id: `agent-${Date.now()}`,
          role: "agent",
          response: result.response,
        },
      ]);
      requestAnimationFrame(() => scrollRef.current?.scrollToEnd({ animated: true }));
    } catch {
      setError("连接或模型请求失败。");
    } finally {
      setLoading(false);
    }
  }

  async function copyMessage(item: ChatMessage) {
    const text = item.role === "user" ? item.text : visibleAgentAnswer(item.response);
    await Clipboard.setStringAsync(text);
    setActionMenu(null);
    setNotice("已复制。");
  }

  function deleteMessage(messageId: string) {
    setMessages((current) => current.filter((item) => item.id !== messageId));
    setActionMenu(null);
    setNotice("已从当前聊天视图删除。");
  }

  function beginRewrite(item: Extract<ChatMessage, { role: "user" }>) {
    if (item.id !== latestUserMessageId) {
      return;
    }
    setEditingMessageId(item.id);
    setEditingText(item.text);
    setActionMenu(null);
  }

  async function submitRewrite(messageId: string) {
    const text = editingText.trim();
    if (!text) {
      return;
    }
    const index = messages.findIndex((item) => item.id === messageId);
    if (index < 0) {
      return;
    }
    setEditingMessageId(null);
    setMessages((current) =>
      current.slice(0, index + 1).map((item) => (item.id === messageId && item.role === "user" ? { ...item, text } : item)),
    );
    await requestAgentReply(text, { appendUser: false });
  }

  function cancelRewrite() {
    setEditingMessageId(null);
    setEditingText("");
  }

  const insets = scaledPaperInsets(paperSize);

  return (
    <KeyboardAvoidingView behavior={Platform.OS === "ios" ? "padding" : undefined} style={styles.shell}>
      <ImageBackground
        imageStyle={styles.paperImage}
        onLayout={onPaperLayout}
        resizeMode="stretch"
        source={paperShellSource}
        style={styles.paperWrap}
      >
        <View style={[styles.paperContent, { paddingBottom: insets.bottom, paddingLeft: insets.left, paddingRight: insets.right, paddingTop: insets.top }]}>
          <ScrollView
            contentContainerStyle={styles.chatList}
            keyboardShouldPersistTaps="handled"
            onContentSizeChange={() => scrollRef.current?.scrollToEnd({ animated: true })}
            ref={scrollRef}
          >
            {messages.length === 0 ? (
              <Text style={styles.emptyText}>问问 Roco...</Text>
            ) : (
              messages.map((item) =>
                item.role === "user" ? (
                  <UserBubble
                    actionMenu={actionMenu}
                    editing={editingMessageId === item.id}
                    editText={editingText}
                    isLatest={item.id === latestUserMessageId}
                    key={item.id}
                    message={item}
                    onAskDelete={() => setActionMenu({ confirmDelete: true, messageId: item.id, role: item.role })}
                    onCancelDelete={() => setActionMenu(null)}
                    onCancelRewrite={cancelRewrite}
                    onChangeEditText={setEditingText}
                    onConfirmDelete={() => deleteMessage(item.id)}
                    onCopy={() => void copyMessage(item)}
                    onLongPress={() => openActionMenu(item)}
                    onRewrite={() => beginRewrite(item)}
                    onSubmitRewrite={() => void submitRewrite(item.id)}
                  />
                ) : (
                  <AgentBubble
                    actionMenu={actionMenu}
                    key={item.id}
                    message={item}
                    onAskDelete={() => setActionMenu({ confirmDelete: true, messageId: item.id, role: item.role })}
                    onAvatarLongPress={openPersonaSelector}
                    onCancelDelete={() => setActionMenu(null)}
                    onConfirmDelete={() => deleteMessage(item.id)}
                    onCopy={() => void copyMessage(item)}
                    onLongPress={() => openActionMenu(item)}
                    variant={personaVariant}
                  />
                ),
              )
            )}
            {loading ? (
              <View style={styles.agentRow}>
                <AgentAvatar onLongPress={openPersonaSelector} thinking variant={personaVariant} />
                <View style={styles.thinkingBubble}>
                  <Text style={styles.messageText}>...</Text>
                </View>
              </View>
            ) : null}
            {error ? (
              <View style={styles.agentRow}>
                <AgentAvatar onLongPress={openPersonaSelector} variant={personaVariant} />
                <View style={[styles.agentBubble, styles.errorBubble]}>
                  <Text style={styles.messageText}>{error}</Text>
                  <TouchableOpacity onPress={() => void requestAgentReply(lastUserText(messages), { appendUser: false })} style={styles.retryButton}>
                    <Text style={styles.retryText}>重试</Text>
                  </TouchableOpacity>
                </View>
              </View>
            ) : null}
          </ScrollView>
          {notice ? <Text style={styles.notice}>{notice}</Text> : null}
          <PromptComposer disabled={loading || editingMessageId !== null} onChangeText={setMessage} onSend={sendMessage} value={message} />
        </View>
      </ImageBackground>

      {personaSelectorOpen ? (
        <PersonaSelectorPanel
          anchor={personaAnchor}
          draft={personaDraft}
          onAddPersona={() => {
            setNotice("人格创建稍后接入。");
            setPersonaSelectorOpen(false);
          }}
          onChange={setPersonaDraft}
          onClose={() => setPersonaSelectorOpen(false)}
        />
      ) : null}
    </KeyboardAvoidingView>
  );
}

function UserBubble({
  actionMenu,
  editing,
  editText,
  isLatest,
  message,
  onAskDelete,
  onCancelDelete,
  onCancelRewrite,
  onChangeEditText,
  onConfirmDelete,
  onCopy,
  onLongPress,
  onRewrite,
  onSubmitRewrite,
}: {
  actionMenu: ActionMenuState | null;
  editing: boolean;
  editText: string;
  isLatest: boolean;
  message: Extract<ChatMessage, { role: "user" }>;
  onAskDelete: () => void;
  onCancelDelete: () => void;
  onCancelRewrite: () => void;
  onChangeEditText: (text: string) => void;
  onConfirmDelete: () => void;
  onCopy: () => void;
  onLongPress: () => void;
  onRewrite: () => void;
  onSubmitRewrite: () => void;
}) {
  return (
    <View style={styles.userBlock}>
      <View style={styles.userRow}>
        <TouchableOpacity activeOpacity={0.88} onLongPress={onLongPress} style={styles.userBubble}>
          {editing ? (
            <View>
              <TextInput multiline onChangeText={onChangeEditText} style={styles.editInput} value={editText} />
              <View style={styles.rewriteActions}>
                <TouchableOpacity onPress={onCancelRewrite} style={[styles.rewriteButton, styles.cancelButton]}>
                  <Text style={styles.rewriteButtonText}>×</Text>
                </TouchableOpacity>
                <TouchableOpacity onPress={onSubmitRewrite} style={[styles.rewriteButton, styles.confirmButton]}>
                  <Text style={[styles.rewriteButtonText, styles.confirmButtonText]}>✓</Text>
                </TouchableOpacity>
              </View>
            </View>
          ) : (
            <Text style={styles.messageText}>{message.text}</Text>
          )}
        </TouchableOpacity>
        <UserAvatar />
      </View>
      {actionMenu?.messageId === message.id ? (
        <MessageActions
          confirmDelete={actionMenu.confirmDelete}
          enablePrimary={isLatest}
          primaryLabel="改写"
          onAskDelete={onAskDelete}
          onCancelDelete={onCancelDelete}
          onConfirmDelete={onConfirmDelete}
          onCopy={onCopy}
          onPrimary={onRewrite}
        />
      ) : null}
    </View>
  );
}

function AgentBubble({
  actionMenu,
  message,
  onAskDelete,
  onAvatarLongPress,
  onCancelDelete,
  onConfirmDelete,
  onCopy,
  onLongPress,
  variant,
}: {
  actionMenu: ActionMenuState | null;
  message: Extract<ChatMessage, { role: "agent" }>;
  onAskDelete: () => void;
  onAvatarLongPress: (anchor: { x: number; y: number }) => void;
  onCancelDelete: () => void;
  onConfirmDelete: () => void;
  onCopy: () => void;
  onLongPress: () => void;
  variant: "you_know_who" | "ai_assistant";
}) {
  const { response } = message;
  const hasRichPresentation =
    response.presentation !== null &&
    response.presentation !== undefined &&
    (response.presentation.detail_sections.length > 0 ||
      response.presentation.visible_warnings.length > 0 ||
      response.presentation.why.trim().length > 0);

  return (
    <View style={styles.agentBlock}>
      <View style={styles.agentRow}>
        <AgentAvatar
          active={Boolean(response.persona?.persona_id)}
          fallback={Boolean(response.persona?.sanitized)}
          onLongPress={onAvatarLongPress}
          variant={variant}
        />
        <TouchableOpacity activeOpacity={0.88} onLongPress={onLongPress} style={styles.agentBubble}>
          <View style={styles.agentTail} />
          <Text style={styles.messageText}>{visibleAgentAnswer(response)}</Text>
          {response.persona?.sanitized ? <Text style={styles.safeNote}>已安全调整人格表达</Text> : null}
        </TouchableOpacity>
      </View>
      {hasRichPresentation && response.presentation ? (
        <View style={styles.cardIndent}>
          <AnalysisCard presentation={response.presentation} title={analysisCardTitle(response.analysis_type)} />
        </View>
      ) : null}
      {actionMenu?.messageId === message.id ? (
        <MessageActions
          confirmDelete={actionMenu.confirmDelete}
          enablePrimary={false}
          primaryLabel="重新生成"
          onAskDelete={onAskDelete}
          onCancelDelete={onCancelDelete}
          onConfirmDelete={onConfirmDelete}
          onCopy={onCopy}
          onPrimary={() => undefined}
        />
      ) : null}
    </View>
  );
}

function MessageActions({
  confirmDelete,
  enablePrimary,
  onAskDelete,
  onCancelDelete,
  onConfirmDelete,
  onCopy,
  onPrimary,
  primaryLabel,
}: {
  confirmDelete: boolean;
  enablePrimary: boolean;
  onAskDelete: () => void;
  onCancelDelete: () => void;
  onConfirmDelete: () => void;
  onCopy: () => void;
  onPrimary: () => void;
  primaryLabel: string;
}) {
  if (confirmDelete) {
    return (
      <View style={styles.actionMenu}>
        <ActionChip danger label="确认删除" onPress={onConfirmDelete} />
        <ActionChip label="取消" onPress={onCancelDelete} />
      </View>
    );
  }
  return (
    <View style={styles.actionMenu}>
      <ActionChip label="复制" onPress={onCopy} />
      <ActionChip disabled={!enablePrimary} label={primaryLabel} onPress={onPrimary} />
      <ActionChip danger label="删除" onPress={onAskDelete} />
    </View>
  );
}

function ActionChip({
  danger = false,
  disabled = false,
  label,
  onPress,
}: {
  danger?: boolean;
  disabled?: boolean;
  label: string;
  onPress: () => void;
}) {
  return (
    <TouchableOpacity disabled={disabled} onPress={onPress} style={[styles.actionChip, danger ? styles.actionChipDanger : null, disabled ? styles.actionChipDisabled : null]}>
      <Text style={[styles.actionText, danger ? styles.actionTextDanger : null, disabled ? styles.actionTextDisabled : null]}>{label}</Text>
    </TouchableOpacity>
  );
}

function visibleAgentAnswer(response: AgentResponse): string {
  return response.persona?.rendered_answer ?? response.presentation?.reply ?? response.answer;
}

function analysisCardTitle(analysisType: AgentResponse["analysis_type"]): string {
  if (analysisType === "team_analysis") {
    return "分析摘要";
  }
  if (analysisType === "species_analysis") {
    return "精灵判断";
  }
  return "Roco 摘要";
}

function findLatestUserMessageId(messages: ChatMessage[]): string | null {
  for (let index = messages.length - 1; index >= 0; index -= 1) {
    const item = messages[index];
    if (item.role === "user") {
      return item.id;
    }
  }
  return null;
}

function lastUserText(messages: ChatMessage[]): string {
  for (let index = messages.length - 1; index >= 0; index -= 1) {
    const item = messages[index];
    if (item.role === "user") {
      return item.text;
    }
  }
  return "";
}

function scaledPaperInsets(size: PaperSize) {
  const xScale = size.width / PAPER_ASSET_SIZE.width;
  const yScale = size.height / PAPER_ASSET_SIZE.height;
  return {
    bottom: Math.max(38, Math.round(PAPER_SAFE_AREA.bottom * yScale)),
    left: Math.max(34, Math.round(PAPER_SAFE_AREA.left * xScale)),
    right: Math.max(34, Math.round(PAPER_SAFE_AREA.right * xScale)),
    top: Math.max(54, Math.round(PAPER_SAFE_AREA.top * yScale)),
  };
}

const styles = StyleSheet.create({
  shell: {
    backgroundColor: rnTokens.color.shellYellow,
    flex: 1,
    paddingBottom: rnTokens.space.sm,
    paddingHorizontal: rnTokens.space.screenX,
    paddingTop: rnTokens.space.sm,
  },
  paperWrap: {
    flex: 1,
    position: "relative",
  },
  paperImage: {
    height: "100%",
    width: "100%",
  },
  paperContent: {
    flex: 1,
  },
  chatList: {
    gap: 12,
    paddingBottom: rnTokens.space.md,
    paddingHorizontal: rnTokens.space.sm,
    paddingTop: rnTokens.space.sm,
  },
  emptyText: {
    alignSelf: "center",
    color: rnTokens.color.muted,
    fontSize: rnTokens.type.sizes.bodyLarge,
    fontWeight: rnTokens.type.captionWeight,
    marginTop: rnTokens.space.xl,
  },
  agentBlock: {
    alignSelf: "stretch",
  },
  agentRow: {
    alignItems: "flex-end",
    alignSelf: "flex-start",
    flexDirection: "row",
    gap: rnTokens.space.sm,
    maxWidth: "88%",
  },
  userBlock: {
    alignSelf: "flex-end",
    maxWidth: "88%",
  },
  userRow: {
    alignItems: "flex-end",
    alignSelf: "flex-end",
    flexDirection: "row",
    gap: rnTokens.space.sm,
    justifyContent: "flex-end",
  },
  agentBubble: {
    backgroundColor: rnTokens.color.agentBubble,
    borderBottomLeftRadius: rnTokens.radius.bubbleTail,
    borderBottomRightRadius: rnTokens.radius.bubble,
    borderColor: rnTokens.color.ink,
    borderTopLeftRadius: rnTokens.radius.bubble,
    borderTopRightRadius: rnTokens.radius.bubble,
    borderWidth: rnTokens.stroke.bold,
    paddingHorizontal: 14,
    paddingVertical: 10,
    ...rnTokens.shadow.bubble.ios,
    elevation: rnTokens.shadow.bubble.androidElevation,
  },
  userBubble: {
    backgroundColor: rnTokens.color.userBubbleBottom,
    borderBottomLeftRadius: rnTokens.radius.bubble,
    borderBottomRightRadius: rnTokens.radius.bubbleTail,
    borderColor: rnTokens.color.ink,
    borderTopLeftRadius: rnTokens.radius.bubble,
    borderTopRightRadius: rnTokens.radius.bubble,
    borderWidth: rnTokens.stroke.bold,
    paddingHorizontal: 14,
    paddingVertical: 10,
    ...rnTokens.shadow.bubble.ios,
    elevation: rnTokens.shadow.bubble.androidElevation,
  },
  agentTail: {
    backgroundColor: rnTokens.color.agentBubble,
    borderBottomColor: rnTokens.color.ink,
    borderBottomWidth: rnTokens.stroke.bold,
    borderLeftColor: rnTokens.color.ink,
    borderLeftWidth: rnTokens.stroke.bold,
    borderRadius: 2,
    bottom: 9,
    height: 12,
    left: -7,
    position: "absolute",
    transform: [{ skewX: "-24deg" }, { rotate: "8deg" }],
    width: 11,
  },
  messageText: {
    color: rnTokens.color.ink,
    fontSize: rnTokens.type.sizes.body,
    lineHeight: rnTokens.type.lineHeights.body,
  },
  thinkingBubble: {
    backgroundColor: rnTokens.color.agentBubble,
    borderBottomLeftRadius: rnTokens.radius.bubbleTail,
    borderColor: rnTokens.color.ink,
    borderRadius: rnTokens.radius.bubble,
    borderWidth: rnTokens.stroke.bold,
    paddingHorizontal: 14,
    paddingVertical: 10,
  },
  errorBubble: {
    borderColor: rnTokens.color.danger,
  },
  retryButton: {
    alignSelf: "flex-start",
    backgroundColor: rnTokens.color.shellYellow,
    borderColor: rnTokens.color.ink,
    borderRadius: rnTokens.radius.buttonRound,
    borderWidth: rnTokens.stroke.regular,
    marginTop: rnTokens.space.sm,
    paddingHorizontal: rnTokens.space.md,
    paddingVertical: rnTokens.space.xs,
  },
  retryText: {
    color: rnTokens.color.ink,
    fontSize: rnTokens.type.sizes.meta,
    fontWeight: rnTokens.type.strongWeight,
  },
  safeNote: {
    color: rnTokens.color.muted,
    fontSize: rnTokens.type.sizes.meta,
    lineHeight: rnTokens.type.lineHeights.meta,
    marginTop: rnTokens.space.xs,
  },
  cardIndent: {
    marginLeft: 42,
    marginTop: rnTokens.space.sm,
  },
  notice: {
    color: rnTokens.color.muted,
    fontSize: rnTokens.type.sizes.meta,
    lineHeight: rnTokens.type.lineHeights.meta,
    paddingHorizontal: rnTokens.space.sm,
    paddingTop: rnTokens.space.xs,
  },
  actionMenu: {
    alignSelf: "center",
    backgroundColor: rnTokens.color.settingsPanel,
    borderColor: rnTokens.color.ink,
    borderRadius: rnTokens.radius.menu,
    borderWidth: 2.5,
    flexDirection: "row",
    gap: rnTokens.space.xs,
    marginTop: rnTokens.space.xs,
    padding: 6,
  },
  actionChip: {
    alignItems: "center",
    borderRadius: 9,
    height: 34,
    justifyContent: "center",
    minWidth: 54,
    paddingHorizontal: rnTokens.space.sm,
  },
  actionChipDanger: {
    backgroundColor: "rgba(184,58,75,0.12)",
  },
  actionChipDisabled: {
    backgroundColor: "rgba(216,208,190,0.42)",
  },
  actionText: {
    color: rnTokens.color.ink,
    fontSize: rnTokens.type.sizes.meta,
    fontWeight: rnTokens.type.strongWeight,
  },
  actionTextDanger: {
    color: rnTokens.color.danger,
  },
  actionTextDisabled: {
    color: rnTokens.color.muted,
  },
  editInput: {
    color: rnTokens.color.ink,
    fontSize: rnTokens.type.sizes.body,
    lineHeight: rnTokens.type.lineHeights.body,
    minWidth: 160,
    padding: 0,
  },
  rewriteActions: {
    alignItems: "center",
    flexDirection: "row",
    gap: rnTokens.space.xs,
    justifyContent: "flex-end",
    marginTop: rnTokens.space.sm,
  },
  rewriteButton: {
    alignItems: "center",
    borderColor: rnTokens.color.ink,
    borderRadius: rnTokens.radius.buttonRound,
    borderWidth: rnTokens.stroke.regular,
    height: 28,
    justifyContent: "center",
    width: 28,
  },
  cancelButton: {
    backgroundColor: rnTokens.color.paper,
  },
  confirmButton: {
    backgroundColor: rnTokens.color.ink,
  },
  rewriteButtonText: {
    color: rnTokens.color.ink,
    fontSize: 16,
    fontWeight: rnTokens.type.displayWeight,
  },
  confirmButtonText: {
    color: rnTokens.color.shellYellow,
  },
});
