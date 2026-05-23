import * as Clipboard from "expo-clipboard";
import React, { useRef, useState } from "react";
import {
  KeyboardAvoidingView,
  Platform,
  Pressable,
  ScrollView,
  StyleSheet,
  Text,
  View,
  useWindowDimensions,
} from "react-native";

import { ProductApiClient } from "../api/client";
import { MessageActionMenu } from "../components/roco/MessageActionMenu";
import { MessageBubble } from "../components/roco/MessageBubble";
import { PaperSurface } from "../components/roco/PaperSurface";
import { PersonaWheel } from "../components/roco/PersonaWheel";
import { PromptComposer } from "../components/roco/PromptComposer";
import { AgentAvatar } from "../components/roco/AgentAvatar";
import {
  DEFAULT_PERSONA_SELECTOR,
  selectorForPersonaUiId,
} from "../roco/rocoPersona";
import {
  resolveVisibleReply,
} from "../roco/rocoPresentation";
import {
  ROCO_V1_COPY,
  ROCO_V1_PARITY,
  actionsForMessage,
  computeMessageActionMenuPosition,
  rocoColors,
  type PersonaSelector,
  type RocoChatMessage,
  type RocoMessageAction,
  type RocoMessageActionMenuState,
  type RocoPersonaUiId,
  type RocoPersonaWheelState,
  type RocoRect,
} from "../roco/rocoTheme";
import {
  activeChatContextAttachments,
  type TeamContextStore,
} from "../roco/teamContext";
import {
  buildNativeRuntimeHeaders,
  type RuntimeSettings,
} from "../runtime/runtimeSettings";

type ChatScreenProps = {
  activePersonaSelector: PersonaSelector | null;
  activePersonaUiId: RocoPersonaUiId;
  apiClient: ProductApiClient;
  onPersonaChange: (uiId: RocoPersonaUiId, selector: PersonaSelector | null) => void;
  runtimeSettings: RuntimeSettings;
  secureStoreAvailable: boolean;
  teamContextStore: TeamContextStore;
};

export function ChatScreen({
  activePersonaSelector,
  activePersonaUiId,
  apiClient,
  onPersonaChange,
  runtimeSettings,
  secureStoreAvailable,
  teamContextStore,
}: ChatScreenProps) {
  const rootRef = useRef<View>(null);
  const scrollRef = useRef<ScrollView>(null);
  const shouldScrollToBottomRef = useRef(false);
  const { width, height } = useWindowDimensions();
  const [message, setMessage] = useState("");
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [messages, setMessages] = useState<RocoChatMessage[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [notice, setNotice] = useState<string | null>(null);
  const [personaWheel, setPersonaWheel] = useState<RocoPersonaWheelState>({
    status: "closed",
  });
  const [actionMenu, setActionMenu] = useState<RocoMessageActionMenuState>({
    status: "closed",
  });
  const [editingMessageId, setEditingMessageId] = useState<string | null>(null);
  const [editingText, setEditingText] = useState("");

  const latestUserMessageId = findLatestUserMessageId(messages);
  const activeAgentPersona =
    activePersonaUiId === "ai_assistant" ? "ai_assistant" : "you_know_who";

  async function sendMessageFromComposer() {
    const text = message.trim();
    if (!text) {
      return;
    }
    setMessage("");
    await requestAgentReply(text, { appendUser: true });
  }

  async function requestAgentReply(
    text: string,
    options: { appendUser: boolean },
  ) {
    const trimmedText = text.trim();
    if (!trimmedText) {
      return;
    }

    const runtimeHeaders = buildNativeRuntimeHeaders(runtimeSettings, {
      secureStoreAvailable,
    });
    if (!runtimeHeaders.ok) {
      setError(runtimeHeaders.error);
      return;
    }

    setActionMenu({ status: "closed" });
    setError(null);
    setNotice(null);
    setLoading(true);

    if (options.appendUser) {
      shouldScrollToBottomRef.current = true;
      setMessages((current) => [
        ...current,
        {
          id: createMessageId("user"),
          role: "user",
          status: "sent",
          kind: "text",
          text: trimmedText,
          created_at: new Date().toISOString(),
        },
      ]);
    }

    try {
      const result = await apiClient.chat(
        {
          message: trimmedText,
          session_id: sessionId,
          persona_selector: activePersonaSelector ?? DEFAULT_PERSONA_SELECTOR,
          context_attachments: activeChatContextAttachments(teamContextStore),
        },
        runtimeHeaders.headers,
      );
      setSessionId(result.session_id);
      shouldScrollToBottomRef.current = true;
      setMessages((current) => [
        ...current,
        {
          id: createMessageId("agent"),
          role: "agent",
          status: "sent",
          kind: "text",
          text: resolveVisibleReply(result.response),
          created_at: new Date().toISOString(),
          persona_ui_id: activePersonaUiId,
        },
      ]);
    } catch {
      setError(ROCO_V1_COPY.retryError);
    } finally {
      setLoading(false);
    }
  }

  function openPersonaWheel(anchor: { x: number; y: number }) {
    setActionMenu({ status: "closed" });
    withRootPoint(anchor, (rootAnchor) => {
      setPersonaWheel({
        status: "open",
        anchor: rootAnchor,
        highlighted_id: null,
      });
    });
  }

  function selectPersona(uiId: RocoPersonaUiId) {
    if (uiId === "add_persona") {
      setPersonaWheel({ status: "closed" });
      setNotice("人格创建稍后接入。");
      return;
    }

    onPersonaChange(uiId, selectorForPersonaUiId(uiId));
    setPersonaWheel({ status: "closed" });
  }

  function openActionMenu(item: RocoChatMessage, rect: RocoRect) {
    if (editingMessageId) {
      return;
    }
    withRootRect(rect, (rootRect) => {
      const point = computeMessageActionMenuPosition({
        role: item.role,
        bubble_rect_in_root: rootRect,
        root_width: width,
        root_height: height,
      });
      setPersonaWheel({ status: "closed" });
      setActionMenu({
        status: "open",
        message_id: item.id,
        role: item.role,
        can_rewrite: item.role === "user" && item.id === latestUserMessageId,
        confirm_delete: false,
        anchor: point,
      });
    });
  }

  function withRootPoint(
    point: { x: number; y: number },
    callback: (rootPoint: { x: number; y: number }) => void,
  ) {
    rootRef.current?.measureInWindow((rootX, rootY) => {
      callback({ x: point.x - rootX, y: point.y - rootY });
    });
  }

  function withRootRect(rect: RocoRect, callback: (rootRect: RocoRect) => void) {
    rootRef.current?.measureInWindow((rootX, rootY) => {
      callback({
        left: rect.left - rootX,
        top: rect.top - rootY,
        right: rect.right - rootX,
        bottom: rect.bottom - rootY,
        width: rect.width,
        height: rect.height,
      });
    });
  }

  async function handleAction(action: RocoMessageAction) {
    if (actionMenu.status !== "open") {
      return;
    }
    const item = messages.find((candidate) => candidate.id === actionMenu.message_id);
    if (!item) {
      setActionMenu({ status: "closed" });
      return;
    }

    switch (action) {
      case "copy":
        await Clipboard.setStringAsync(item.text);
        setNotice("已复制。");
        setActionMenu({ status: "closed" });
        return;
      case "rewrite":
        if (item.role === "user" && item.id === latestUserMessageId) {
          setEditingMessageId(item.id);
          setEditingText(item.text);
        }
        setActionMenu({ status: "closed" });
        return;
      case "regenerate":
        return;
      case "delete":
        setActionMenu({ ...actionMenu, confirm_delete: true });
        return;
      case "confirm_delete":
        setMessages((current) => current.filter((candidate) => candidate.id !== item.id));
        setActionMenu({ status: "closed" });
        setNotice("已从当前聊天视图删除。");
        return;
      case "cancel_delete":
        setActionMenu({ status: "closed" });
        return;
    }
  }

  async function submitRewrite() {
    if (!editingMessageId) {
      return;
    }
    const text = editingText.trim();
    if (!text) {
      return;
    }
    const index = messages.findIndex((item) => item.id === editingMessageId);
    if (index < 0) {
      setEditingMessageId(null);
      return;
    }
    setEditingMessageId(null);
    setEditingText("");
    setMessages((current) =>
      current
        .slice(0, index + 1)
        .map((item) => (item.id === editingMessageId ? { ...item, text } : item)),
    );
    await requestAgentReply(text, { appendUser: false });
  }

  function cancelRewrite() {
    setEditingMessageId(null);
    setEditingText("");
  }

  function scrollToBottomIfRequested() {
    if (!shouldScrollToBottomRef.current) {
      return;
    }
    shouldScrollToBottomRef.current = false;
    requestAnimationFrame(() => scrollRef.current?.scrollToEnd({ animated: true }));
  }

  const disabledActions =
    actionMenu.status === "open"
      ? actionsForMessage({
          message:
            messages.find((item) => item.id === actionMenu.message_id) ??
            fallbackMessage(actionMenu.message_id, actionMenu.role),
          latest_user_message_id: latestUserMessageId,
          regenerate_available: false,
        }).disabled_actions
      : undefined;

  return (
    <KeyboardAvoidingView
      behavior={Platform.OS === "ios" ? "padding" : undefined}
      style={styles.root}
    >
      <View ref={rootRef} collapsable={false} style={styles.rootContent}>
        <PaperSurface>
          <ScrollView
            alwaysBounceVertical
            contentContainerStyle={[
              styles.chatList,
              messages.length === 0 && !loading && !error ? styles.emptyChatList : null,
            ]}
            keyboardShouldPersistTaps="handled"
            nestedScrollEnabled
            onContentSizeChange={scrollToBottomIfRequested}
            ref={scrollRef}
            scrollIndicatorInsets={styles.scrollIndicatorInsets}
            style={styles.chatScroll}
          >
            {messages.length === 0 && !loading && !error ? (
              <EmptyState onPromptPress={(prompt) => setMessage(prompt)} />
            ) : (
              messages.map((item) => (
                <MessageBubble
                  activePersona={activeAgentPersona}
                  editText={editingText}
                  editing={editingMessageId === item.id}
                  key={item.id}
                  message={item}
                  onAvatarLongPress={openPersonaWheel}
                  onBubbleLongPress={openActionMenu}
                  onCancelRewrite={cancelRewrite}
                  onChangeEditText={setEditingText}
                  onRetry={() => void requestAgentReply(lastUserText(messages), { appendUser: false })}
                  onSubmitRewrite={() => void submitRewrite()}
                />
              ))
            )}
            {loading ? (
              <MessageBubble
                activePersona={activeAgentPersona}
                editText=""
                editing={false}
                message={{
                  id: "thinking",
                  role: "agent",
                  status: "thinking",
                  kind: "text",
                  text: "...",
                  persona_ui_id: activePersonaUiId,
                }}
                onAvatarLongPress={openPersonaWheel}
                onBubbleLongPress={() => undefined}
                onCancelRewrite={cancelRewrite}
                onChangeEditText={setEditingText}
                onRetry={() => void requestAgentReply(lastUserText(messages), { appendUser: false })}
                onSubmitRewrite={() => void submitRewrite()}
              />
            ) : null}
            {error ? (
              <MessageBubble
                activePersona={activeAgentPersona}
                editText=""
                editing={false}
                message={{
                  id: "error",
                  role: "agent",
                  status: "failed",
                  kind: "text",
                  text: error,
                  persona_ui_id: activePersonaUiId,
                  error: {
                    code: "network_error",
                    user_message: error,
                    retryable: true,
                  },
                }}
                onAvatarLongPress={openPersonaWheel}
                onBubbleLongPress={() => undefined}
                onCancelRewrite={cancelRewrite}
                onChangeEditText={setEditingText}
                onRetry={() => void requestAgentReply(lastUserText(messages), { appendUser: false })}
                onSubmitRewrite={() => void submitRewrite()}
              />
            ) : null}
          </ScrollView>
          {notice ? <Text style={styles.notice}>{notice}</Text> : null}
          <PromptComposer
            disabled={loading || editingMessageId !== null}
            onChangeText={setMessage}
            onSend={() => void sendMessageFromComposer()}
            value={message}
          />
        </PaperSurface>
        <PersonaWheel
          activePersonaUiId={activePersonaUiId}
          onClose={() => setPersonaWheel({ status: "closed" })}
          onSelect={selectPersona}
          state={personaWheel}
        />
        <MessageActionMenu
          disabledActions={disabledActions}
          onAction={(action) => void handleAction(action)}
          onClose={() => setActionMenu({ status: "closed" })}
          state={actionMenu}
        />
      </View>
    </KeyboardAvoidingView>
  );
}

function EmptyState({ onPromptPress }: { onPromptPress: (prompt: string) => void }) {
  return (
    <View style={styles.emptyState}>
      <AgentAvatar size={ROCO_V1_PARITY.emptyState.avatarSize} variant="you_know_who" />
      <Text style={styles.emptyInvite}>{ROCO_V1_COPY.emptyInvite}</Text>
      <View style={styles.promptChips}>
        {ROCO_V1_COPY.emptyPromptChips.map((prompt) => (
          <Pressable
            accessibilityRole="button"
            key={prompt}
            onPress={() => onPromptPress(prompt)}
            style={styles.promptChip}
          >
            <Text style={styles.promptChipText}>{prompt}</Text>
          </Pressable>
        ))}
      </View>
    </View>
  );
}

function createMessageId(prefix: "user" | "agent") {
  return `${prefix}-${Date.now()}-${Math.round(Math.random() * 10000)}`;
}

function findLatestUserMessageId(messages: RocoChatMessage[]): string | null {
  for (let index = messages.length - 1; index >= 0; index -= 1) {
    if (messages[index].role === "user") {
      return messages[index].id;
    }
  }
  return null;
}

function lastUserText(messages: RocoChatMessage[]): string {
  for (let index = messages.length - 1; index >= 0; index -= 1) {
    const item = messages[index];
    if (item.role === "user") {
      return item.text;
    }
  }
  return "";
}

function fallbackMessage(id: string, role: RocoChatMessage["role"]): RocoChatMessage {
  return {
    id,
    role,
    status: "sent",
    kind: "text",
    text: "",
  };
}

const stack = ROCO_V1_PARITY.messageStack;
const empty = ROCO_V1_PARITY.emptyState;

const styles = StyleSheet.create({
  scrollIndicatorInsets: {
    right: -20,
  },
  root: {
    flex: 1,
  },
  rootContent: {
    flex: 1,
  },
  chatScroll: {
    flex: 1,
    flexShrink: 1,
  },
  chatList: {
    flexGrow: 1,
    gap: stack.gap,
    paddingBottom: 14,
    paddingHorizontal: 0,
    paddingTop: stack.topPadding,
  },
  emptyChatList: {
    flexGrow: 1,
    justifyContent: "center",
  },
  emptyState: {
    alignItems: "center",
    gap: empty.gap,
    paddingHorizontal: empty.paddingHorizontal,
    paddingVertical: empty.paddingVertical,
  },
  emptyInvite: {
    color: rocoColors.muted,
    fontSize: empty.inviteFontSize,
    lineHeight: empty.inviteFontSize * 1.6,
    maxWidth: empty.inviteMaxWidth,
    textAlign: "center",
  },
  promptChips: {
    gap: empty.promptChipGap,
    width: "100%",
  },
  promptChip: {
    alignItems: "center",
    backgroundColor: rocoColors.composerPaper,
    borderColor: rocoColors.ink,
    borderRadius: 999,
    borderWidth: 2,
    paddingHorizontal: 12,
    paddingVertical: 9,
  },
  promptChipText: {
    color: rocoColors.ink,
    fontSize: 13,
    fontWeight: "800",
    textAlign: "center",
  },
  notice: {
    color: rocoColors.muted,
    fontSize: 12,
    lineHeight: 18,
    paddingHorizontal: ROCO_V1_PARITY.composer.outerPaddingHorizontal,
    paddingTop: 5,
  },
});
