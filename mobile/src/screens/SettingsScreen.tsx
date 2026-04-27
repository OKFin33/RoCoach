import React, { useState } from "react";
import { Button, StyleSheet, Text, TextInput, View } from "react-native";

import { ProductApiClient } from "../api/client";
import type { HealthResponse, MetadataResponse } from "../api/types";
import { colors, spacing } from "../styles/theme";

type SettingsScreenProps = {
  apiBaseUrl: string;
  apiClient: ProductApiClient;
  onApiBaseUrlChange: (nextUrl: string) => void;
};

export function SettingsScreen({ apiBaseUrl, apiClient, onApiBaseUrlChange }: SettingsScreenProps) {
  const [draftUrl, setDraftUrl] = useState(apiBaseUrl);
  const [health, setHealth] = useState<HealthResponse | null>(null);
  const [metadata, setMetadata] = useState<MetadataResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  async function testConnection() {
    setLoading(true);
    setError(null);
    try {
      const [healthPayload, metadataPayload] = await Promise.all([
        apiClient.health(),
        apiClient.metadata(),
      ]);
      setHealth(healthPayload);
      setMetadata(metadataPayload);
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Request failed.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <View>
      <Text style={styles.heading}>Settings</Text>
      <Text style={styles.caption}>
        API base URL is process-local UI state. No provider keys are accepted here.
      </Text>
      <TextInput
        autoCapitalize="none"
        autoCorrect={false}
        onChangeText={setDraftUrl}
        placeholder="http://127.0.0.1:8000"
        style={styles.input}
        value={draftUrl}
      />
      <View style={styles.buttonRow}>
        <Button onPress={() => onApiBaseUrlChange(draftUrl)} title="Apply URL" />
      </View>
      <Button disabled={loading} onPress={testConnection} title={loading ? "Checking..." : "Test API"} />
      {error ? <Text style={styles.error}>{error}</Text> : null}
      {health ? (
        <View style={styles.panel}>
          <Text style={styles.sectionTitle}>Health</Text>
          <Text style={styles.body}>
            {health.status} · {health.service_name} · {health.release_stage}
          </Text>
          <Text style={styles.body}>
            {health.api_version} · {health.response_schema_version}
          </Text>
        </View>
      ) : null}
      {metadata ? (
        <View style={styles.panel}>
          <Text style={styles.sectionTitle}>Metadata</Text>
          <Text style={styles.body}>service: {metadata.service_name}</Text>
          <Text style={styles.body}>release_stage: {metadata.release_stage}</Text>
          <Text style={styles.body}>backend: {metadata.default_backend}</Text>
          <Text style={styles.body}>battle_dex_available: {String(metadata.battle_dex_available)}</Text>
          <Text style={styles.body}>provider_key_mode: {metadata.provider_key_mode}</Text>
          <Text style={styles.body}>rate_limit_mode: {metadata.rate_limit_mode}</Text>
          <Text style={styles.body}>features: {metadata.features.join(", ")}</Text>
          <Text style={styles.caption}>{metadata.unofficial_notice}</Text>
        </View>
      ) : null}
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
    lineHeight: 18,
    marginBottom: spacing.md,
  },
  input: {
    backgroundColor: colors.panel,
    borderColor: colors.border,
    borderRadius: 12,
    borderWidth: 1,
    color: colors.text,
    marginBottom: spacing.md,
    padding: spacing.md,
  },
  buttonRow: {
    marginBottom: spacing.sm,
  },
  panel: {
    backgroundColor: colors.panel,
    borderColor: colors.border,
    borderRadius: 16,
    borderWidth: 1,
    marginTop: spacing.md,
    padding: spacing.md,
  },
  sectionTitle: {
    color: colors.text,
    fontSize: 16,
    fontWeight: "700",
    marginBottom: spacing.sm,
  },
  body: {
    color: colors.text,
    fontSize: 14,
    lineHeight: 20,
  },
  error: {
    color: colors.danger,
    marginTop: spacing.sm,
  },
});
