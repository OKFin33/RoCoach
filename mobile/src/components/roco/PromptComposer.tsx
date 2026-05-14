import React from "react";
import { Pressable, StyleSheet, TextInput, View } from "react-native";

import {
  ROCO_V1_COPY,
  ROCO_V1_PARITY,
  rocoColors,
} from "../../roco/rocoTheme";
import { SendIcon } from "./RocoIcons";

type PromptComposerProps = {
  disabled?: boolean;
  onChangeText: (text: string) => void;
  onSend: () => void;
  value: string;
};

export function PromptComposer({
  disabled = false,
  onChangeText,
  onSend,
  value,
}: PromptComposerProps) {
  const canSend = value.trim().length > 0 && !disabled;

  return (
    <View style={styles.wrap}>
      <View style={styles.inputPill}>
        <TextInput
          autoCapitalize="sentences"
          editable={!disabled}
          multiline
          onChangeText={onChangeText}
          placeholder={ROCO_V1_COPY.composerPlaceholder}
          placeholderTextColor={rocoColors.muted}
          style={styles.input}
          textAlignVertical="top"
          value={value}
        />
      </View>
      <Pressable
        accessibilityLabel="发送"
        accessibilityRole="button"
        disabled={!canSend}
        onPress={onSend}
        style={[styles.sendButton, canSend ? styles.sendButtonReady : styles.sendButtonDisabled]}
      >
        <SendIcon color={canSend ? rocoColors.shellYellow : rocoColors.composerPaper} />
      </Pressable>
    </View>
  );
}

const styles = StyleSheet.create({
  wrap: {
    alignItems: "flex-end",
    flexDirection: "row",
    gap: ROCO_V1_PARITY.composer.rowGap,
    marginBottom: -7,
    paddingBottom: 0,
    paddingHorizontal: 8,
    paddingTop: 0,
  },
  inputPill: {
    backgroundColor: rocoColors.composerPaper,
    borderColor: rocoColors.ink,
    borderRadius: ROCO_V1_PARITY.composer.inputRadius,
    borderWidth: ROCO_V1_PARITY.composer.inputBorderWidth,
    flex: 1,
    minHeight: ROCO_V1_PARITY.composer.inputMinHeight,
    paddingHorizontal: ROCO_V1_PARITY.composer.inputPaddingHorizontal,
    paddingVertical: ROCO_V1_PARITY.composer.inputPaddingVertical,
  },
  input: {
    color: rocoColors.ink,
    fontSize: ROCO_V1_PARITY.composer.inputFontSize,
    lineHeight: ROCO_V1_PARITY.composer.inputLineHeight,
    maxHeight: ROCO_V1_PARITY.composer.inputMaxTextHeight,
    minHeight: 24,
    padding: 0,
  },
  sendButton: {
    alignItems: "center",
    borderColor: rocoColors.ink,
    borderRadius: 999,
    borderWidth: ROCO_V1_PARITY.composer.inputBorderWidth,
    height: ROCO_V1_PARITY.composer.sendButtonSize,
    justifyContent: "center",
    width: ROCO_V1_PARITY.composer.sendButtonSize,
  },
  sendButtonReady: {
    backgroundColor: rocoColors.ink,
    shadowColor: rocoColors.ink,
    shadowOffset: { height: 3, width: 0 },
    shadowOpacity: 0.35,
    shadowRadius: 0,
    elevation: 2,
  },
  sendButtonDisabled: {
    backgroundColor: rocoColors.disabledFill,
    shadowOpacity: 0,
  },
});
