import React, { useState } from "react";
import { Button, ScrollView, StyleSheet, Text, TextInput, TouchableOpacity, View } from "react-native";

import { ProductApiClient } from "../api/client";
import type { SpeciesSearchItem } from "../api/types";
import { colors, spacing } from "../styles/theme";

type SpeciesSearchScreenProps = {
  apiClient: ProductApiClient;
};

export function SpeciesSearchScreen({ apiClient }: SpeciesSearchScreenProps) {
  const [query, setQuery] = useState("豆丁鱼");
  const [results, setResults] = useState<SpeciesSearchItem[]>([]);
  const [profile, setProfile] = useState<Record<string, unknown> | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  async function search() {
    if (!query.trim()) {
      setError("Search query cannot be empty.");
      return;
    }
    setLoading(true);
    setError(null);
    try {
      const payload = await apiClient.searchSpecies(query.trim());
      setResults(payload.results);
      setProfile(null);
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Request failed.");
    } finally {
      setLoading(false);
    }
  }

  async function loadProfile(speciesId: string) {
    setLoading(true);
    setError(null);
    try {
      const payload = await apiClient.speciesProfile(speciesId);
      setProfile(payload.profile);
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Request failed.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <View>
      <Text style={styles.heading}>Species Search</Text>
      <Text style={styles.caption}>Search and profile data are loaded from the Product API.</Text>
      <TextInput onChangeText={setQuery} placeholder="species name" style={styles.input} value={query} />
      <Button disabled={loading} onPress={search} title={loading ? "Loading..." : "Search"} />
      {error ? <Text style={styles.error}>{error}</Text> : null}

      <View style={styles.panel}>
        <Text style={styles.sectionTitle}>Results</Text>
        {results.length === 0 ? <Text style={styles.caption}>No results loaded.</Text> : null}
        {results.map((item) => (
          <TouchableOpacity key={item.species_id} onPress={() => loadProfile(item.species_id)} style={styles.result}>
            <Text style={styles.resultTitle}>{item.display_name}</Text>
            <Text style={styles.caption}>
              {item.species_id} · {item.primary_type}/{item.secondary_type ?? "-"}
            </Text>
          </TouchableOpacity>
        ))}
      </View>

      <View style={styles.panel}>
        <Text style={styles.sectionTitle}>Profile</Text>
        {profile === null ? (
          <Text style={styles.caption}>Select a result to inspect its API profile payload.</Text>
        ) : (
          <ScrollView horizontal>
            <Text style={styles.code}>{JSON.stringify(profile, null, 2)}</Text>
          </ScrollView>
        )}
      </View>
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
  result: {
    borderColor: colors.border,
    borderRadius: 10,
    borderWidth: 1,
    marginBottom: spacing.sm,
    padding: spacing.sm,
  },
  resultTitle: {
    color: colors.accentDark,
    fontSize: 15,
    fontWeight: "700",
  },
  code: {
    color: colors.text,
    fontFamily: "Courier",
    fontSize: 12,
    lineHeight: 16,
  },
  error: {
    color: colors.danger,
    marginTop: spacing.sm,
  },
});
