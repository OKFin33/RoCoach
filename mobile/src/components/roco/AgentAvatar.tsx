import React, { useRef } from "react";
import { Pressable, StyleSheet, View } from "react-native";
import Svg, { Circle, Ellipse, G, Path, Rect } from "react-native-svg";

import {
  ROCO_V1_PARITY,
  rocoColors,
  type RocoPersonaUiId,
} from "../../roco/rocoTheme";
import { CheckIcon } from "./RocoIcons";

type AgentAvatarProps = {
  active?: boolean;
  onLongPress?: (anchor: { x: number; y: number }) => void;
  ringColor?: "neutral" | "yellow" | "blue";
  selected?: boolean;
  size?: number;
  thinking?: boolean;
  variant?: Exclude<RocoPersonaUiId, "add_persona">;
};

export function AgentAvatar({
  active = true,
  onLongPress,
  ringColor,
  selected = false,
  size = ROCO_V1_PARITY.messageRow.agentAvatarSize,
  thinking = false,
  variant = "you_know_who",
}: AgentAvatarProps) {
  const ref = useRef<View>(null);

  function handleLongPress() {
    ref.current?.measureInWindow((x, y, width, height) => {
      onLongPress?.({ x: x + width / 2, y: y + height / 2 });
    });
  }

  return (
    <View ref={ref} collapsable={false} style={{ height: size, width: size }}>
      <Pressable
        accessibilityLabel={variant === "ai_assistant" ? "默认AI助手" : "You know who"}
        accessibilityRole="button"
        delayLongPress={ROCO_V1_PARITY.personaWheel.longPressMs}
        onLongPress={onLongPress ? handleLongPress : undefined}
        style={styles.pressable}
      >
        <AgentAvatarArt
          active={active}
          ringColor={ringColor ?? (thinking || variant === "ai_assistant" ? "blue" : "yellow")}
          selected={selected}
          size={size}
          thinking={thinking}
          variant={variant}
        />
      </Pressable>
    </View>
  );
}

export function AgentAvatarArt({
  active = true,
  ringColor,
  selected = false,
  size,
  thinking = false,
  variant,
}: {
  active?: boolean;
  ringColor?: "neutral" | "yellow" | "blue";
  selected?: boolean;
  size: number;
  thinking?: boolean;
  variant: Exclude<RocoPersonaUiId, "add_persona">;
}) {
  return (
    <Svg height={size} viewBox="0 0 48 48" width={size}>
      {variant === "ai_assistant" ? (
        <AiAssistantAvatar ringColor={ringColorForAvatar(selected, ringColor)} />
      ) : (
        <YouKnowWhoAvatar ringColor={ringColorForAvatar(selected, ringColor)} />
      )}
      {thinking ? (
        <Circle
          cx="24"
          cy="24"
          fill="none"
          opacity={0.7}
          r="22.5"
          stroke={rocoColors.info}
          strokeDasharray="6 4"
          strokeWidth="2.5"
        />
      ) : null}
    </Svg>
  );
}

export function PersonaAddAvatar({ selected = false, size }: { selected?: boolean; size: number }) {
  return (
    <Svg height={size} viewBox="0 0 48 48" width={size}>
      <Circle
        cx="24"
        cy="24"
        fill="#FFF8E8"
        fillOpacity="0.72"
        r="21"
        stroke={selected ? rocoColors.shellYellow : "rgba(23,23,23,0.44)"}
        strokeDasharray="5 4"
        strokeWidth={selected ? "3" : "2.5"}
      />
      <Path d="M24 15 L24 33 M15 24 L33 24" stroke="rgba(23,23,23,0.62)" strokeLinecap="round" strokeWidth="2.6" />
    </Svg>
  );
}

export function SelectionBadge() {
  const size = ROCO_V1_PARITY.personaWheel.selectionBadgeSize;
  return (
    <View style={[styles.badge, { height: size, width: size }]}>
      <CheckIcon size={11} strokeWidth={3} />
    </View>
  );
}

function ringColorForAvatar(
  selected: boolean,
  ringColor?: "neutral" | "yellow" | "blue",
): string {
  if (ringColor === "yellow") {
    return rocoColors.shellYellow;
  }
  if (ringColor === "blue") {
    return rocoColors.info;
  }
  if (ringColor === "neutral") {
    return rocoColors.ink;
  }
  return selected ? rocoColors.shellYellow : rocoColors.ink;
}

function YouKnowWhoAvatar({ ringColor }: { ringColor: string }) {
  return (
    <G>
      <Circle cx="24" cy="24" fill="#1A1A18" r="22" stroke={ringColor} strokeWidth={ringColor === rocoColors.ink ? "2.5" : "3"} />
      <Circle cx="24" cy="24" fill="#252520" r="15" />
      <Ellipse cx="24" cy="25.5" fill="#1E1E1C" rx="10.5" ry="9" />
      <Rect fill="#111110" height="5" rx="2.5" width="19" x="14.5" y="20.5" />
      <Ellipse cx="19.5" cy="23" fill="#F7CF45" rx="2.2" ry="1.6" />
      <Ellipse cx="19.5" cy="23" fill="#FFEC80" rx="0.9" ry="0.7" />
      <Ellipse cx="28.5" cy="23" fill="#F7CF45" rx="2.2" ry="1.6" />
      <Ellipse cx="28.5" cy="23" fill="#FFEC80" rx="0.9" ry="0.7" />
      <Rect fill="#1E1E1C" height="5" rx="2.5" width="14" x="17" y="28" />
    </G>
  );
}

function AiAssistantAvatar({ ringColor }: { ringColor: string }) {
  return (
    <G>
      <Circle cx="24" cy="24" fill="#4B8FD8" r="22" stroke={ringColor} strokeWidth={ringColor === rocoColors.ink ? "2.5" : "3"} />
      <Circle cx="24" cy="24" fill="#6EA9E7" opacity={0.55} r="15" />
      <Path d="M12 31 Q24 39 36 31 L36 36 Q30 43 24 43 Q18 43 12 36 Z" fill="#2F6FB6" opacity={0.7} />
      <Path d="M18 28 L24 16 L30 28 M20 24 L28 24" fill="none" stroke="#FFFDF3" strokeLinecap="round" strokeLinejoin="round" strokeWidth="2.8" />
      <Path d="M32 17 L32 31" stroke="#FFFDF3" strokeLinecap="round" strokeWidth="2.8" />
    </G>
  );
}

const styles = StyleSheet.create({
  pressable: {
    alignItems: "center",
    height: "100%",
    justifyContent: "center",
    width: "100%",
  },
  badge: {
    alignItems: "center",
    backgroundColor: rocoColors.shellYellow,
    borderColor: rocoColors.ink,
    borderRadius: 999,
    borderWidth: 2,
    justifyContent: "center",
    position: "absolute",
    bottom: -2,
    right: -2,
  },
});
