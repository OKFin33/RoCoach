import React, { useState } from "react";
import { Button, StyleSheet, Text, TextInput, View } from "react-native";

import { ProductApiClient } from "../api/client";
import type { AgentResponse, TeamSlotInput } from "../api/types";
import { ResponsePanel } from "../components/ResponsePanel";
import { colors, spacing } from "../styles/theme";

type TeamEditorScreenProps = {
  apiClient: ProductApiClient;
  onResponse: (response: AgentResponse) => void;
};

type SlotField = "primary_type" | "secondary_type";

const EMPTY_TEAM: TeamSlotInput[] = Array.from({ length: 6 }, () => ({
  primary_type: "",
  secondary_type: "",
}));

export function TeamEditorScreen({ apiClient, onResponse }: TeamEditorScreenProps) {
  const [slots, setSlots] = useState<TeamSlotInput[]>(EMPTY_TEAM);
  const [response, setResponse] = useState<AgentResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  function updateSlot(index: number, field: SlotField, value: string) {
    setSlots((current) =>
      current.map((slot, slotIndex) =>
        slotIndex === index ? { ...slot, [field]: value } : slot,
      ),
    );
  }

  async function analyzeTeam() {
    const team = slots
      .map((slot) => ({
        primary_type: slot.primary_type.trim(),
        secondary_type: slot.secondary_type?.trim() || null,
      }))
      .filter((slot) => slot.primary_type.length > 0);

    if (team.length === 0) {
      setError("Enter at least one primary type.");
      return;
    }

    setLoading(true);
    setError(null);
    try {
      const result = await apiClient.analyzeTeam({
        team,
      });
      setResponse(result);
      onResponse(result);
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Request failed.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <View>
      <Text style={styles.heading}>Team Editor</Text>
      <Text style={styles.caption}>Enter local type labels and let the API handle analysis.</Text>
      {slots.map((slot, index) => (
        <View key={`slot-${index}`} style={styles.slot}>
          <Text style={styles.slotLabel}>Slot {index + 1}</Text>
          <TextInput
            onChangeText={(value) => updateSlot(index, "primary_type", value)}
            placeholder="primary_type"
            style={styles.input}
            value={slot.primary_type}
          />
          <TextInput
            onChangeText={(value) => updateSlot(index, "secondary_type", value)}
            placeholder="secondary_type optional"
            style={styles.input}
            value={slot.secondary_type ?? ""}
          />
        </View>
      ))}
      <Button disabled={loading} onPress={analyzeTeam} title={loading ? "Analyzing..." : "Analyze Team"} />
      {error ? <Text style={styles.error}>{error}</Text> : null}
      <ResponsePanel response={response} title="Team Analysis" />
    </View>
  );
}

const styles = StyleSheet.create({
  heading: {
    color: colors.text,
    fontSize: 24,
    fontWeight: "800",
    marginBottom: spacing.xs,
  },
  caption: {
    color: colors.muted,
    fontSize: 12,
    marginBottom: spacing.md,
  },
  slot: {
    backgroundColor: colors.panel,
    borderColor: colors.border,
    borderRadius: 12,
    borderWidth: 1,
    marginBottom: spacing.sm,
    padding: spacing.sm,
  },
  slotLabel: {
    color: colors.accentDark,
    fontWeight: "700",
    marginBottom: spacing.xs,
  },
  input: {
    borderColor: colors.border,
    borderRadius: 8,
    borderWidth: 1,
    color: colors.text,
    marginTop: spacing.xs,
    padding: spacing.sm,
  },
  error: {
    color: colors.danger,
    marginTop: spacing.sm,
  },
});
