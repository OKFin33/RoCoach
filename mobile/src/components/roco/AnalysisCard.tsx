import React from "react";
import { StyleSheet, Text, View } from "react-native";

import {
  ROCO_V1_PARITY,
  rocoColors,
  type RocoAnalysisCardModel,
} from "../../roco/rocoTheme";
import { WarningIcon } from "./RocoIcons";

type AnalysisCardProps = {
  card: RocoAnalysisCardModel;
};

export function AnalysisCard({ card }: AnalysisCardProps) {
  const rows = [
    card.summary
      ? {
          id: "summary",
          label: "说明",
          content: card.summary,
          warning: false,
        }
      : null,
    ...card.warnings.map((warning) => ({
      id: `warning-${warning.code}`,
      label: warning.severity.toUpperCase(),
      content: warning.message,
      warning: true,
    })),
    ...card.sections.map((section) => ({
      id: section.id,
      label: section.label,
      content: section.content,
      warning: false,
    })),
  ].filter((row): row is { id: string; label: string; content: string; warning: boolean } => row !== null);

  return (
    <View style={styles.card}>
      <View style={styles.header}>
        <View style={styles.iconTile}>
          <Text style={styles.iconText}>R</Text>
        </View>
        <Text numberOfLines={2} style={styles.title}>
          {card.title}
        </Text>
      </View>
      <View style={styles.body}>
        {rows.map((row, index) => (
          <View
            key={row.id}
            style={[
              styles.row,
              index === 0 ? styles.firstRow : null,
              index === rows.length - 1 && card.followup_prompts.length === 0 ? styles.lastRow : null,
              row.warning ? styles.warningRow : null,
            ]}
          >
            <View style={styles.rowTitleLine}>
              {row.warning ? <WarningIcon size={15} /> : null}
              <Text style={[styles.rowTitle, row.warning ? styles.warningTitle : null]}>{row.label}</Text>
            </View>
            <Text style={styles.rowBody}>{row.content}</Text>
          </View>
        ))}
        {card.followup_prompts.length > 0 ? (
          <View style={[styles.followups, rows.length === 0 ? styles.firstRow : null]}>
            {card.followup_prompts.slice(0, 3).map((prompt) => (
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

const card = ROCO_V1_PARITY.analysisCard;

const styles = StyleSheet.create({
  card: {
    backgroundColor: rocoColors.cardBody,
    borderColor: rocoColors.ink,
    borderRadius: card.radius,
    borderWidth: card.borderWidth,
    marginTop: card.topMargin,
    overflow: "hidden",
    shadowColor: rocoColors.ink,
    shadowOffset: { height: 5, width: 0 },
    shadowOpacity: 0.18,
    shadowRadius: 0,
    elevation: 3,
  },
  header: {
    alignItems: "center",
    backgroundColor: rocoColors.cardHeader,
    borderBottomColor: rocoColors.ink,
    borderBottomWidth: card.headerBorderBottomWidth,
    flexDirection: "row",
    gap: card.headerGap,
    paddingHorizontal: card.headerPaddingHorizontal,
    paddingVertical: card.headerPaddingVertical,
  },
  iconTile: {
    alignItems: "center",
    backgroundColor: rocoColors.ink,
    borderRadius: card.headerIconRadius,
    height: card.headerIconSize,
    justifyContent: "center",
    width: card.headerIconSize,
  },
  iconText: {
    color: rocoColors.shellYellow,
    fontSize: 13,
    fontWeight: "900",
  },
  title: {
    color: rocoColors.ink,
    flex: 1,
    fontSize: card.titleFontSize,
    fontWeight: card.titleFontWeight,
  },
  body: {
    backgroundColor: rocoColors.cardBody,
    paddingHorizontal: card.bodyPaddingHorizontal,
    paddingVertical: card.bodyPaddingVertical,
  },
  row: {
    borderBottomColor: rocoColors.divider,
    borderBottomWidth: 1,
    paddingBottom: card.rowPaddingBottom,
    paddingTop: card.rowPaddingTop,
  },
  firstRow: {
    paddingTop: 0,
  },
  lastRow: {
    borderBottomWidth: 0,
    paddingBottom: 0,
  },
  warningRow: {
    backgroundColor: "rgba(229,154,45,0.10)",
    borderColor: "rgba(229,154,45,0.35)",
    borderRadius: 9,
    borderWidth: 1.5,
    marginBottom: 4,
    paddingHorizontal: 8,
  },
  rowTitleLine: {
    alignItems: "center",
    flexDirection: "row",
    gap: 5,
    marginBottom: 3,
  },
  rowTitle: {
    color: rocoColors.ink,
    fontSize: card.rowTitleFontSize,
    fontWeight: card.rowTitleFontWeight,
  },
  warningTitle: {
    color: rocoColors.warning,
  },
  rowBody: {
    color: rocoColors.inkSoft,
    fontSize: card.rowBodyFontSize,
    lineHeight: card.rowBodyFontSize * card.rowBodyLineHeightMultiplier,
  },
  followups: {
    flexDirection: "row",
    flexWrap: "wrap",
    gap: 6,
    paddingTop: card.rowPaddingTop,
  },
  followupChip: {
    backgroundColor: rocoColors.paper,
    borderColor: rocoColors.ink,
    borderRadius: 999,
    borderWidth: 1.8,
    paddingHorizontal: 8,
    paddingVertical: 5,
  },
  followupText: {
    color: rocoColors.info,
    fontSize: 12,
    fontWeight: "800",
  },
});
