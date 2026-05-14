import React, { useRef } from "react";
import {
  Pressable,
  StyleSheet,
  Text,
  TextInput,
  View,
} from "react-native";

import {
  ROCO_V1_PARITY,
  rocoColors,
  type RocoChatMessage,
  type RocoRect,
} from "../../roco/rocoTheme";
import { AgentAvatar } from "./AgentAvatar";
import { CheckIcon, XIcon } from "./RocoIcons";
import { UserAvatar } from "./UserAvatar";

type MessageBubbleProps = {
  activePersona: "you_know_who" | "ai_assistant";
  editText: string;
  editing: boolean;
  message: RocoChatMessage;
  onAvatarLongPress: (anchor: { x: number; y: number }) => void;
  onBubbleLongPress: (message: RocoChatMessage, rect: RocoRect) => void;
  onCancelRewrite: () => void;
  onChangeEditText: (text: string) => void;
  onRetry?: () => void;
  onSubmitRewrite: () => void;
};

export function MessageBubble(props: MessageBubbleProps) {
  if (props.message.role === "user") {
    return <UserMessageBubble {...props} />;
  }
  return <AgentMessageBubble {...props} />;
}

function AgentMessageBubble({
  activePersona,
  message,
  onAvatarLongPress,
  onBubbleLongPress,
  onRetry,
}: MessageBubbleProps) {
  const bubbleRef = useRef<View>(null);

  return (
    <View style={styles.agentBlock}>
      <View style={styles.agentSpokenRow}>
        <AgentAvatar onLongPress={onAvatarLongPress} thinking={message.status === "thinking"} variant={message.persona_ui_id === "ai_assistant" ? "ai_assistant" : activePersona} />
        <MeasuredPressable
          refView={bubbleRef}
          onLongPress={(rect) => onBubbleLongPress(message, rect)}
          style={[styles.bubbleBase, styles.agentBubble, message.status === "failed" ? styles.failedBubble : null]}
          wrapperStyle={styles.agentBubbleWrap}
        >
          <View style={[styles.tail, styles.agentTail]} />
          <Text style={styles.messageText}>{message.text}</Text>
          {message.error?.retryable && onRetry ? (
            <Pressable accessibilityRole="button" onPress={onRetry} style={styles.retryButton}>
              <Text style={styles.retryText}>重试</Text>
            </Pressable>
          ) : null}
        </MeasuredPressable>
      </View>
    </View>
  );
}

function UserMessageBubble({
  editText,
  editing,
  message,
  onBubbleLongPress,
  onCancelRewrite,
  onChangeEditText,
  onSubmitRewrite,
}: MessageBubbleProps) {
  const bubbleRef = useRef<View>(null);

  return (
    <View style={styles.userSpokenRow}>
      <MeasuredPressable
        refView={bubbleRef}
        onLongPress={(rect) => onBubbleLongPress(message, rect)}
        style={[styles.bubbleBase, styles.userBubble]}
        wrapperStyle={styles.userBubbleWrap}
      >
        <View style={[styles.tail, styles.userTail]} />
        {editing ? (
          <View>
            <TextInput
              autoFocus
              multiline
              onChangeText={onChangeEditText}
              style={styles.editInput}
              textAlignVertical="top"
              value={editText}
            />
            <View style={styles.editActions}>
              <Pressable accessibilityLabel="取消改写" accessibilityRole="button" onPress={onCancelRewrite} style={styles.editIconButton}>
                <XIcon size={15} />
              </Pressable>
              <Pressable accessibilityLabel="提交改写" accessibilityRole="button" onPress={onSubmitRewrite} style={[styles.editIconButton, styles.editConfirmButton]}>
                <CheckIcon color={rocoColors.shellYellow} size={15} />
              </Pressable>
            </View>
          </View>
        ) : (
          <Text style={styles.messageText}>{message.text}</Text>
        )}
      </MeasuredPressable>
      <UserAvatar />
    </View>
  );
}

function MeasuredPressable({
  children,
  onLongPress,
  refView,
  style,
  wrapperStyle,
}: {
  children: React.ReactNode;
  onLongPress: (rect: RocoRect) => void;
  refView: React.RefObject<View | null>;
  style: object;
  wrapperStyle?: object;
}) {
  function measure() {
    refView.current?.measureInWindow((x, y, width, height) => {
      onLongPress({
        left: x,
        top: y,
        right: x + width,
        bottom: y + height,
        width,
        height,
      });
    });
  }

  return (
    <View ref={refView} collapsable={false} style={wrapperStyle}>
      <Pressable accessibilityRole="button" onLongPress={measure} style={style}>
        {children}
      </Pressable>
    </View>
  );
}

const row = ROCO_V1_PARITY.messageRow;
const lane = {
  avatarEdgeInset: 8,
} as const;

const styles = StyleSheet.create({
  agentBlock: {
    alignSelf: "stretch",
    marginLeft: lane.avatarEdgeInset,
    marginRight: row.userAvatarSize + lane.avatarEdgeInset,
  },
  agentSpokenRow: {
    alignItems: "flex-end",
    flexDirection: "row",
    gap: row.avatarGap,
    width: "100%",
  },
  userSpokenRow: {
    alignItems: "flex-end",
    alignSelf: "stretch",
    flexDirection: "row",
    gap: row.avatarGap,
    justifyContent: "flex-end",
    marginLeft: row.agentAvatarSize + lane.avatarEdgeInset,
    marginRight: lane.avatarEdgeInset,
  },
  bubbleBase: {
    borderColor: rocoColors.ink,
    borderWidth: row.bubbleBorderWidth,
    paddingHorizontal: row.bubblePaddingHorizontal,
    paddingVertical: row.bubblePaddingVertical,
    shadowColor: rocoColors.ink,
    shadowOffset: { height: 3, width: 0 },
    shadowOpacity: 0.14,
    shadowRadius: 0,
    elevation: 2,
  },
  agentBubble: {
    alignSelf: "flex-start",
    backgroundColor: rocoColors.agentBubble,
    borderBottomLeftRadius: row.bubbleRadius.tailCorner,
    borderBottomRightRadius: row.bubbleRadius.large,
    borderTopLeftRadius: row.bubbleRadius.large,
    borderTopRightRadius: row.bubbleRadius.large,
    flexShrink: 1,
    maxWidth: "100%",
  },
  userBubble: {
    alignSelf: "flex-end",
    backgroundColor: rocoColors.userBubbleBottom,
    borderBottomLeftRadius: row.bubbleRadius.large,
    borderBottomRightRadius: row.bubbleRadius.tailCorner,
    borderTopLeftRadius: row.bubbleRadius.large,
    borderTopRightRadius: row.bubbleRadius.large,
    flexShrink: 1,
    maxWidth: "100%",
  },
  failedBubble: {
    borderColor: rocoColors.danger,
  },
  tail: {
    height: row.bubbleTail.height,
    position: "absolute",
    width: row.bubbleTail.width,
  },
  agentTail: {
    backgroundColor: rocoColors.agentBubble,
    borderBottomColor: rocoColors.ink,
    borderBottomWidth: row.bubbleBorderWidth,
    borderLeftColor: rocoColors.ink,
    borderLeftWidth: row.bubbleBorderWidth,
    borderRadius: 2,
    bottom: row.bubbleTail.bottom,
    left: -7,
    transform: [{ skewX: "-24deg" }, { rotate: "8deg" }],
  },
  userTail: {
    backgroundColor: rocoColors.userBubbleBottom,
    borderBottomColor: rocoColors.ink,
    borderBottomWidth: row.bubbleBorderWidth,
    borderRadius: 2,
    borderRightColor: rocoColors.ink,
    borderRightWidth: row.bubbleBorderWidth,
    bottom: row.bubbleTail.bottom,
    right: -7,
    transform: [{ skewX: "24deg" }, { rotate: "-8deg" }],
  },
  messageText: {
    color: rocoColors.ink,
    fontSize: row.text.fontSize,
    lineHeight: row.text.lineHeight,
  },
  retryButton: {
    alignSelf: "flex-start",
    backgroundColor: rocoColors.shellYellow,
    borderColor: rocoColors.ink,
    borderRadius: 999,
    borderWidth: 2,
    marginTop: 8,
    paddingHorizontal: 12,
    paddingVertical: 5,
  },
  retryText: {
    color: rocoColors.ink,
    fontSize: 12,
    fontWeight: "900",
  },
  agentBubbleWrap: {
    flex: 1,
    flexShrink: 1,
    maxWidth: "100%",
  },
  userBubbleWrap: {
    flexShrink: 1,
    maxWidth: "100%",
  },
  editInput: {
    color: rocoColors.ink,
    fontSize: row.text.fontSize,
    lineHeight: row.text.lineHeight,
    minWidth: 160,
    padding: 0,
  },
  editActions: {
    flexDirection: "row",
    gap: 6,
    justifyContent: "flex-end",
    marginTop: 8,
  },
  editIconButton: {
    alignItems: "center",
    backgroundColor: rocoColors.paper,
    borderColor: rocoColors.ink,
    borderRadius: 999,
    borderWidth: 2,
    height: 28,
    justifyContent: "center",
    width: 28,
  },
  editConfirmButton: {
    backgroundColor: rocoColors.ink,
  },
});
