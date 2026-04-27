import React from "react";
import { Dimensions, StyleSheet, Text, TouchableOpacity, View } from "react-native";

import {
  createBuiltInPersonaSelectorDraft,
  type PersonaSelectorDraft,
} from "../persona/personaSelector";
import { AgentAvatarArt, PersonaAddAvatar } from "./AgentAvatar";
import { rnTokens } from "../styles/rnHandoffTokens";

type PersonaSelectorPanelProps = {
  anchor: { x: number; y: number } | null;
  draft: PersonaSelectorDraft;
  onChange: (draft: PersonaSelectorDraft) => void;
  onClose?: () => void;
  onAddPersona?: () => void;
};

type WheelItem = {
  id: "enzo" | "default" | "add";
  label: string;
  description: string;
  angle: number;
  active: boolean;
  onPress: () => void;
};

const RADIUS = 92;

export function PersonaSelectorPanel({
  anchor,
  draft,
  onChange,
  onAddPersona,
  onClose,
}: PersonaSelectorPanelProps) {
  const close = onClose ?? (() => undefined);
  const addPersona = onAddPersona ?? (() => undefined);
  const screen = Dimensions.get("window");
  const center = clampAnchor(anchor, screen.width, screen.height);
  const items: WheelItem[] = [
    {
      id: "enzo",
      label: "You know who",
      description: "黑衣人默认人格",
      angle: -50,
      active: draft.mode === "built_in" && draft.personaId === "obsidian_tactical_coach",
      onPress: () => {
        onChange(createBuiltInPersonaSelectorDraft("obsidian_tactical_coach"));
        close();
      },
    },
    {
      id: "default",
      label: "默认AI助手",
      description: "直连后端默认人格",
      angle: 8,
      active: draft.mode === "built_in" && draft.personaId === "lattice_support_coach",
      onPress: () => {
        onChange(createBuiltInPersonaSelectorDraft("lattice_support_coach"));
        close();
      },
    },
    {
      id: "add",
      label: "添加人格",
      description: "预留创建入口",
      angle: 64,
      active: false,
      onPress: addPersona,
    },
  ];

  return (
    <View style={styles.overlay} pointerEvents="box-none">
      <TouchableOpacity accessibilityRole="button" onPress={close} style={styles.backdrop} />
      <View style={[styles.halo, { left: center.x - 44, top: center.y - 44 }]} />
      {items.map((item) => {
        const point = radialPoint(center, item.angle, RADIUS, screen.width, screen.height);
        return (
          <TouchableOpacity
            accessibilityRole="button"
            key={item.id}
            onPress={item.onPress}
            style={[styles.option, { left: point.x - 38, top: point.y - 38 }]}
          >
            <Medallion active={item.active} item={item} />
            <View style={styles.optionLabelWrap}>
              <Text style={styles.optionLabel}>{item.label}</Text>
              <Text style={styles.optionDescription}>{item.description}</Text>
            </View>
          </TouchableOpacity>
        );
      })}
    </View>
  );
}

function Medallion({ active, item }: { active: boolean; item: WheelItem }) {
  if (item.id === "add") {
    return <PersonaAddAvatar size={58} />;
  }
  if (item.id === "default") {
    return <AgentAvatarArt active={active} size={58} variant="ai_assistant" />;
  }
  return <AgentAvatarArt active={active} size={58} variant="you_know_who" />;
}

function clampAnchor(anchor: { x: number; y: number } | null, width: number, height: number) {
  const x = anchor?.x ?? 86;
  const y = anchor?.y ?? 190;
  return {
    x: Math.max(76, Math.min(width - 122, x)),
    y: Math.max(120, Math.min(height - 220, y)),
  };
}

function radialPoint(center: { x: number; y: number }, angleDeg: number, radius: number, width: number, height: number) {
  const radians = (angleDeg * Math.PI) / 180;
  return {
    x: Math.max(58, Math.min(width - 86, center.x + Math.cos(radians) * radius)),
    y: Math.max(96, Math.min(height - 150, center.y + Math.sin(radians) * radius)),
  };
}

const styles = StyleSheet.create({
  overlay: {
    bottom: 0,
    left: 0,
    position: "absolute",
    right: 0,
    top: 0,
    zIndex: 30,
  },
  backdrop: {
    backgroundColor: "rgba(17, 17, 17, 0.16)",
    bottom: 0,
    left: 0,
    position: "absolute",
    right: 0,
    top: 0,
  },
  halo: {
    backgroundColor: "rgba(247,207,69,0.1)",
    borderColor: "rgba(23,23,23,0.82)",
    borderRadius: 999,
    borderWidth: 3,
    height: 88,
    position: "absolute",
    shadowColor: rnTokens.color.ink,
    shadowOffset: { height: 8, width: 0 },
    shadowOpacity: 0.22,
    shadowRadius: 12,
    width: 88,
  },
  option: {
    alignItems: "center",
    position: "absolute",
    width: 102,
  },
  optionLabelWrap: {
    alignItems: "center",
    backgroundColor: rnTokens.color.paper,
    borderColor: "rgba(23,23,23,0.2)",
    borderRadius: 10,
    borderWidth: 1,
    marginTop: rnTokens.space.xs,
    paddingHorizontal: 6,
    paddingVertical: 4,
  },
  optionLabel: {
    color: rnTokens.color.ink,
    fontSize: 11,
    fontWeight: "900",
    textAlign: "center",
  },
  optionDescription: {
    color: rnTokens.color.muted,
    fontSize: 9,
    fontWeight: "700",
    marginTop: 1,
    textAlign: "center",
  },
});
