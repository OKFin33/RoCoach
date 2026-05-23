import React from "react";
import { Pressable, StyleSheet, Text, View } from "react-native";

import {
  ROCO_V1_PARITY,
  rocoColors,
  type RocoMessageAction,
  type RocoMessageActionMenuState,
} from "../../roco/rocoTheme";
import {
  CopyIcon,
  DeleteIcon,
  RegenerateIcon,
  RewriteIcon,
  XIcon,
  CheckIcon,
} from "./RocoIcons";

type MessageActionMenuProps = {
  disabledActions?: Partial<Record<RocoMessageAction, string>>;
  onAction: (action: RocoMessageAction) => void;
  onClose: () => void;
  state: RocoMessageActionMenuState;
};

const labels: Record<RocoMessageAction, string> = {
  copy: "复制",
  rewrite: "改写",
  regenerate: "重新生成",
  delete: "删除",
  confirm_delete: "确认删除",
  cancel_delete: "取消",
};

export function MessageActionMenu({
  disabledActions,
  onAction,
  onClose,
  state,
}: MessageActionMenuProps) {
  if (state.status !== "open") {
    return null;
  }

  const actions: RocoMessageAction[] = state.confirm_delete
    ? ["confirm_delete", "cancel_delete"]
    : state.role === "user"
      ? state.can_rewrite
        ? ["copy", "rewrite", "delete"]
        : ["copy", "delete"]
      : ["copy", "regenerate", "delete"];

  return (
    <View pointerEvents="box-none" style={styles.root}>
      <Pressable accessibilityRole="button" onPress={onClose} style={styles.backdrop} />
      <View style={[styles.menu, { left: state.anchor.x, top: state.anchor.y }]}>
        {actions.map((action) => (
          <ActionButton
            action={action}
            disabled={Boolean(disabledActions?.[action])}
            key={action}
            onPress={() => onAction(action)}
          />
        ))}
      </View>
    </View>
  );
}

function ActionButton({
  action,
  disabled,
  onPress,
}: {
  action: RocoMessageAction;
  disabled: boolean;
  onPress: () => void;
}) {
  const danger = action === "delete" || action === "confirm_delete";
  const minWidth =
    action === "confirm_delete"
      ? ROCO_V1_PARITY.messageActionMenu.confirmDeleteMinWidth
      : ROCO_V1_PARITY.messageActionMenu.buttonMinWidth;
  const color = danger ? rocoColors.danger : disabled ? rocoColors.muted : rocoColors.ink;

  return (
    <Pressable
      accessibilityLabel={labels[action]}
      accessibilityRole="button"
      disabled={disabled}
      onPress={onPress}
      style={[
        styles.button,
        { minWidth },
        danger ? styles.dangerButton : null,
        disabled ? styles.disabledButton : null,
      ]}
    >
      {iconForAction(action, color)}
      <Text style={[styles.buttonText, danger ? styles.dangerText : null, disabled ? styles.disabledText : null]}>
        {labels[action]}
      </Text>
    </Pressable>
  );
}

function iconForAction(action: RocoMessageAction, color: string) {
  switch (action) {
    case "copy":
      return <CopyIcon color={color} />;
    case "rewrite":
      return <RewriteIcon color={color} />;
    case "regenerate":
      return <RegenerateIcon color={color} />;
    case "delete":
      return <DeleteIcon color={color} />;
    case "confirm_delete":
      return <CheckIcon color={color} size={15} />;
    case "cancel_delete":
      return <XIcon color={color} />;
  }
}

const menu = ROCO_V1_PARITY.messageActionMenu;

const styles = StyleSheet.create({
  root: {
    ...StyleSheet.absoluteFillObject,
    elevation: 50,
    zIndex: 40,
  },
  backdrop: {
    ...StyleSheet.absoluteFillObject,
    backgroundColor: menu.backdrop,
    elevation: 51,
    zIndex: 1,
  },
  menu: {
    alignItems: "center",
    backgroundColor: rocoColors.composerPaper,
    borderColor: rocoColors.ink,
    borderRadius: menu.radius,
    borderWidth: menu.borderWidth,
    flexDirection: "row",
    gap: menu.gap,
    padding: menu.padding,
    position: "absolute",
    shadowColor: rocoColors.ink,
    shadowOffset: { height: 8, width: 0 },
    shadowOpacity: 0.16,
    shadowRadius: 0,
    elevation: 52,
    zIndex: 2,
  },
  button: {
    alignItems: "center",
    borderRadius: menu.buttonRadius,
    flexDirection: "row",
    gap: menu.buttonGap,
    height: menu.buttonHeight,
    justifyContent: "center",
    paddingHorizontal: 8,
  },
  dangerButton: {
    backgroundColor: "rgba(184,58,75,0.12)",
  },
  disabledButton: {
    backgroundColor: "rgba(216,208,190,0.42)",
    opacity: 0.72,
  },
  buttonText: {
    color: rocoColors.ink,
    fontSize: menu.buttonFontSize,
    fontWeight: menu.buttonFontWeight,
  },
  dangerText: {
    color: rocoColors.danger,
  },
  disabledText: {
    color: rocoColors.muted,
  },
});
