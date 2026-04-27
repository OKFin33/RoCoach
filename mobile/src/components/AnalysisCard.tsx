import React from "react";
import { StyleSheet, Text, View } from "react-native";

import type { PresentationResult } from "../api/types";
import { rnTokens } from "../styles/rnHandoffTokens";

type AnalysisCardProps = {
  presentation: PresentationResult;
  title: string;
};

export function AnalysisCard({ presentation, title }: AnalysisCardProps) {
  const visibleSections = presentation.detail_sections.filter((section) => section.content.trim().length > 0);
  const visibleWarnings = presentation.visible_warnings.filter((warning) => warning.message.trim().length > 0);
  return (
    <View style={styles.card}>
      <View style={styles.header}>
        <View style={styles.iconTile}>
          <Text style={styles.iconText}>R</Text>
        </View>
        <Text style={styles.title}>{title}</Text>
      </View>
      <View style={styles.body}>
        {presentation.why.trim().length > 0 ? (
          <View style={styles.section}>
            <Text style={styles.sectionLabel}>说明</Text>
            <Text style={styles.sectionText}>{presentation.why}</Text>
          </View>
        ) : null}
        {visibleWarnings.map((warning) => (
          <View key={warning.code} style={[styles.section, styles.warningSection]}>
            <Text style={styles.warningLabel}>{warning.severity.toUpperCase()}</Text>
            <Text style={styles.sectionText}>{warning.message}</Text>
          </View>
        ))}
        {visibleSections.map((section) => (
          <View key={section.section_id} style={styles.section}>
            <Text style={styles.sectionLabel}>{section.label}</Text>
            <Text style={styles.sectionText}>{section.content}</Text>
          </View>
        ))}
        {presentation.followup_prompts.length > 0 ? (
          <View style={styles.followups}>
            {presentation.followup_prompts.slice(0, 3).map((prompt) => (
              <View key={prompt} style={styles.followupChip}>
                <Text style={styles.followupText}>{prompt}</Text>
              </View>
            ))}
          </View>
        ) : null}
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  card: {
    backgroundColor: rnTokens.color.cardBody,
    borderColor: rnTokens.color.ink,
    borderRadius: rnTokens.radius.card,
    borderWidth: rnTokens.stroke.bold,
    overflow: "hidden",
    ...rnTokens.shadow.card.ios,
    elevation: rnTokens.shadow.card.androidElevation,
  },
  header: {
    alignItems: "center",
    backgroundColor: rnTokens.color.cardHeader,
    borderBottomColor: rnTokens.color.ink,
    borderBottomWidth: rnTokens.stroke.bold,
    flexDirection: "row",
    gap: 10,
    minHeight: 48,
    paddingHorizontal: 14,
  },
  iconTile: {
    alignItems: "center",
    backgroundColor: rnTokens.color.ink,
    borderRadius: 7,
    height: 30,
    justifyContent: "center",
    width: 30,
  },
  iconText: {
    color: rnTokens.color.shellYellow,
    fontSize: 14,
    fontWeight: "900",
  },
  title: {
    color: rnTokens.color.ink,
    flex: 1,
    fontSize: rnTokens.type.sizes.cardTitle,
    fontWeight: rnTokens.type.displayWeight,
    lineHeight: rnTokens.type.lineHeights.cardTitle,
  },
  body: {
    backgroundColor: rnTokens.color.cardBody,
    paddingHorizontal: 14,
    paddingVertical: 12,
  },
  section: {
    borderBottomColor: "rgba(23,23,23,0.1)",
    borderBottomWidth: 1,
    paddingVertical: rnTokens.space.sm,
  },
  warningSection: {
    backgroundColor: "rgba(216,137,46,0.1)",
    borderColor: "rgba(216,137,46,0.35)",
    borderRadius: 10,
    borderWidth: 2,
    marginVertical: rnTokens.space.xs,
    padding: rnTokens.space.sm,
  },
  sectionLabel: {
    color: rnTokens.color.ink,
    fontSize: 12,
    fontWeight: "900",
    marginBottom: 3,
  },
  warningLabel: {
    color: rnTokens.color.warning,
    fontSize: 11,
    fontWeight: "900",
    marginBottom: 3,
  },
  sectionText: {
    color: rnTokens.color.inkSoft,
    fontSize: 13,
    lineHeight: 19,
  },
  followups: {
    flexDirection: "row",
    flexWrap: "wrap",
    gap: rnTokens.space.xs,
    paddingTop: rnTokens.space.sm,
  },
  followupChip: {
    backgroundColor: rnTokens.color.paper,
    borderColor: rnTokens.color.ink,
    borderRadius: 999,
    borderWidth: 2,
    paddingHorizontal: rnTokens.space.sm,
    paddingVertical: 5,
  },
  followupText: {
    color: rnTokens.color.info,
    fontSize: 12,
    fontWeight: "800",
  },
});
