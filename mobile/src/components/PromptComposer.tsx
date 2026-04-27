import React from "react";
import { StyleSheet, Text, TextInput, TouchableOpacity, View } from "react-native";

import { rnTokens } from "../styles/rnHandoffTokens";

type PromptComposerProps = {
  disabled?: boolean;
  onChangeText: (text: string) => void;
  onSend: () => void;
  value: string;
};

export function PromptComposer({ disabled = false, onChangeText, onSend, value }: PromptComposerProps) {
  const canSend = value.trim().length > 0 && !disabled;
  return (
    <View style={styles.wrap}>
      <View style={styles.inputPill}>
        <TextInput
          autoCapitalize="sentences"
          multiline
          onChangeText={onChangeText}
          placeholder="问问 Roco..."
          placeholderTextColor={rnTokens.color.muted}
          style={styles.input}
          value={value}
        />
      </View>
      <TouchableOpacity
        accessibilityRole="button"
        disabled={!canSend}
        onPress={onSend}
        style={[styles.sendButton, canSend ? styles.sendButtonReady : styles.sendButtonDisabled]}
      >
        <Text style={[styles.sendText, canSend ? styles.sendTextReady : null]}>发送</Text>
      </TouchableOpacity>
    </View>
  );
}

const styles = StyleSheet.create({
  wrap: {
    alignItems: "flex-end",
    flexDirection: "row",
    gap: rnTokens.space.sm,
    paddingHorizontal: 2,
    paddingTop: rnTokens.space.sm,
  },
  inputPill: {
    backgroundColor: "#FFFDF3",
    borderColor: rnTokens.color.ink,
    borderRadius: rnTokens.radius.composer,
    borderWidth: rnTokens.stroke.bold,
    flex: 1,
    minHeight: rnTokens.space.composerHeightMin,
    paddingHorizontal: 18,
    paddingVertical: 12,
  },
  input: {
    color: rnTokens.color.ink,
    fontSize: rnTokens.type.sizes.bodyLarge,
    lineHeight: rnTokens.type.lineHeights.bodyLarge,
    maxHeight: rnTokens.space.composerHeightMax,
    minHeight: 24,
    padding: 0,
    textAlignVertical: "top",
  },
  sendButton: {
    alignItems: "center",
    borderColor: rnTokens.color.ink,
    borderRadius: rnTokens.radius.buttonRound,
    borderWidth: rnTokens.stroke.bold,
    height: rnTokens.space.composerHeightMin,
    justifyContent: "center",
    shadowColor: rnTokens.color.ink,
    shadowOffset: { height: 3, width: 0 },
    shadowOpacity: 0.28,
    shadowRadius: 0,
    width: rnTokens.space.composerHeightMin,
  },
  sendButtonReady: {
    backgroundColor: "#D2B640",
  },
  sendButtonDisabled: {
    backgroundColor: rnTokens.color.disabled,
    opacity: 0.72,
    shadowOpacity: 0,
  },
  sendText: {
    color: rnTokens.color.ink,
    fontSize: 12,
    fontWeight: "900",
  },
  sendTextReady: {
    color: rnTokens.color.ink,
  },
});
