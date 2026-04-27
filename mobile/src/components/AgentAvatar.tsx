import React from "react";
import { GestureResponderEvent, StyleSheet, TouchableOpacity, View } from "react-native";
import Svg, { Circle, Ellipse, G, Path, Rect } from "react-native-svg";

import { rnTokens } from "../styles/rnHandoffTokens";

type AgentAvatarVariant = "you_know_who" | "ai_assistant";

type AgentAvatarProps = {
  active?: boolean;
  fallback?: boolean;
  onLongPress?: (anchor: { x: number; y: number }) => void;
  size?: "small" | "large";
  thinking?: boolean;
  variant?: AgentAvatarVariant;
};

export function AgentAvatar({
  active = false,
  fallback = false,
  onLongPress,
  size = "small",
  thinking = false,
  variant = "you_know_who",
}: AgentAvatarProps) {
  const avatarSize = size === "large" ? 58 : 34;
  function handleLongPress(event: GestureResponderEvent) {
    onLongPress?.({
      x: event.nativeEvent.pageX,
      y: event.nativeEvent.pageY,
    });
  }

  return (
    <TouchableOpacity
      accessibilityHint="Long press to open persona wheel."
      accessibilityLabel="Agent persona avatar"
      accessibilityRole="button"
      activeOpacity={0.82}
      delayLongPress={rnTokens.motion.longPressMs}
      onLongPress={handleLongPress}
      style={[styles.avatarPressable, { height: avatarSize, width: avatarSize }]}
    >
      <AgentAvatarArt active={active} fallback={fallback} size={avatarSize} thinking={thinking} variant={variant} />
    </TouchableOpacity>
  );
}

export function AgentAvatarArt({
  active = false,
  fallback = false,
  size,
  thinking = false,
  variant,
}: {
  active?: boolean;
  fallback?: boolean;
  size: number;
  thinking?: boolean;
  variant: AgentAvatarVariant;
}) {
  return (
    <Svg height={size} viewBox="0 0 96 96" width={size}>
      {variant === "ai_assistant" ? <AiAssistantAvatar /> : <YouKnowWhoAvatar />}
      {thinking ? <Circle cx="48" cy="48" fill="none" opacity={0.75} r="44" stroke={rnTokens.color.info} strokeDasharray="8 6" strokeWidth="4" /> : null}
      {active ? (
        <G>
          <Circle cx="76" cy="20" fill={rnTokens.color.shellYellow} r="11" stroke={rnTokens.color.ink} strokeWidth="3" />
          <Path d="M70 20 L74 24 L82 15" fill="none" stroke={rnTokens.color.ink} strokeLinecap="round" strokeLinejoin="round" strokeWidth="3" />
        </G>
      ) : null}
      {fallback ? <Circle cx="76" cy="20" fill={rnTokens.color.warning} r="8" stroke={rnTokens.color.ink} strokeWidth="2" /> : null}
    </Svg>
  );
}

// Mechanical RN conversion of mobile/assets/rn_handoff/avatars/persona_add.svg.
export function PersonaAddAvatar({ size }: { size: number }) {
  return (
    <Svg height={size} viewBox="0 0 96 96" width={size}>
      <Circle cx="48" cy="48" fill="#FFF9EB" fillOpacity="0.72" r="42" stroke={rnTokens.color.ink} strokeDasharray="8 7" strokeWidth="4" />
      <Path d="M48 30 L48 66 M30 48 L66 48" stroke={rnTokens.color.ink} strokeLinecap="round" strokeWidth="7" />
    </Svg>
  );
}

// Mechanical RN conversion of mobile/assets/rn_handoff/avatars/agent_you_know_who.svg.
function YouKnowWhoAvatar() {
  return (
    <G>
      <Circle cx="48" cy="48" fill={rnTokens.color.shellYellow} r="44" stroke={rnTokens.color.ink} strokeWidth="5" />
      <Circle cx="48" cy="49" fill={rnTokens.color.ink} r="35" />
      <Path d="M20 49 C22 25 35 14 48 14 C62 14 76 26 76 50 C68 43 59 39 48 39 C37 39 28 43 20 49Z" fill="#272727" />
      <Path d="M18 56 C25 66 34 72 48 72 C62 72 72 66 78 56 C70 79 58 87 48 87 C37 87 24 78 18 56Z" fill="#101010" />
      <Ellipse cx="37" cy="52" fill="#F7D957" rx="5" ry="3" />
      <Ellipse cx="59" cy="52" fill="#F7D957" rx="5" ry="3" />
      <Path d="M31 70 C42 76 55 76 66 70" stroke="#2D2A23" strokeLinecap="round" strokeWidth="3" />
    </G>
  );
}

// Mechanical RN conversion of mobile/assets/rn_handoff/avatars/agent_ai_assistant.svg.
function AiAssistantAvatar() {
  return (
    <G>
      <Circle cx="48" cy="48" fill={rnTokens.color.paper} r="44" stroke={rnTokens.color.ink} strokeWidth="5" />
      <Rect fill="#4B8FD8" height="42" rx="15" stroke={rnTokens.color.ink} strokeWidth="4" width="48" x="24" y="27" />
      <Circle cx="39" cy="47" fill={rnTokens.color.paper} r="4" />
      <Circle cx="57" cy="47" fill={rnTokens.color.paper} r="4" />
      <Path d="M39 59 C45 63 51 63 57 59" stroke={rnTokens.color.paper} strokeLinecap="round" strokeWidth="4" />
      <Path d="M48 18 L48 27" stroke={rnTokens.color.ink} strokeLinecap="round" strokeWidth="4" />
      <Circle cx="48" cy="15" fill={rnTokens.color.shellYellow} r="5" stroke={rnTokens.color.ink} strokeWidth="3" />
    </G>
  );
}

// Mechanical RN conversion of mobile/assets/rn_handoff/avatars/user_default.svg.
export function UserAvatar() {
  return (
    <View style={styles.userAvatar}>
      <Svg height={30} viewBox="0 0 96 96" width={30}>
        <Circle cx="48" cy="48" fill="#F7D957" r="44" stroke={rnTokens.color.ink} strokeWidth="5" />
        <Circle cx="48" cy="43" fill="#FFE3A2" r="24" stroke={rnTokens.color.ink} strokeWidth="4" />
        <Path d="M27 37 C34 22 53 16 69 31 C64 27 55 28 50 34 C43 28 33 29 27 37Z" fill="#6A4B2D" />
        <Path d="M32 22 C42 10 61 13 67 29 C57 22 44 21 32 22Z" fill="#7A42C7" stroke={rnTokens.color.ink} strokeWidth="4" />
        <Circle cx="39" cy="46" fill={rnTokens.color.ink} r="3" />
        <Circle cx="57" cy="46" fill={rnTokens.color.ink} r="3" />
        <Path d="M40 57 C45 61 52 61 57 57" stroke={rnTokens.color.ink} strokeLinecap="round" strokeWidth="3" />
      </Svg>
    </View>
  );
}

const styles = StyleSheet.create({
  avatarPressable: {
    alignItems: "center",
    justifyContent: "center",
  },
  userAvatar: {
    height: 30,
    width: 30,
  },
});
