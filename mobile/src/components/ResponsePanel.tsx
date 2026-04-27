import React from "react";
import { ScrollView, StyleSheet, Text, View } from "react-native";

import type { AgentResponse } from "../api/types";
import { colors, spacing } from "../styles/theme";

type ResponsePanelProps = {
  response: AgentResponse | null;
  title?: string;
};

export function ResponsePanel({ response, title = "Response" }: ResponsePanelProps) {
  if (response === null) {
    return (
      <View style={styles.panel}>
        <Text style={styles.title}>{title}</Text>
        <Text style={styles.muted}>No response loaded.</Text>
      </View>
    );
  }

  return (
    <View style={styles.panel}>
      <Text style={styles.title}>{title}</Text>
      <Text style={styles.meta}>
        {response.status} · {response.analysis_type} · {response.backend}
      </Text>

      {response.presentation ? (
        <Section label="Presentation">
          <Text style={styles.body}>{response.presentation.reply}</Text>
          <Text style={styles.body}>{response.presentation.why}</Text>
          <Text style={styles.muted}>
            canonical persona_id=
            {response.presentation.presentation_metadata.persona_id ?? "none"} · facts_locked=
            {String(response.presentation.presentation_metadata.facts_locked)}
          </Text>
          {response.presentation.visible_warnings.length > 0 ? (
            <View style={styles.warningBlock}>
              {response.presentation.visible_warnings.map((warning) => (
                <Text key={warning.code} style={styles.warningText}>
                  {warning.severity} · {warning.code} · {warning.message}
                </Text>
              ))}
            </View>
          ) : null}
        </Section>
      ) : null}

      <Section label="Base Answer">
        <Text style={styles.body}>{response.answer}</Text>
      </Section>

      {response.persona ? (
        <Section label="Persona State">
          <Text style={styles.muted}>
            effective_persona={response.persona.persona_id ?? "none"} · display=
            {response.persona.display_name ?? "none"} · style={response.persona.display_style ?? "none"}
          </Text>
          <Text style={styles.muted}>
            fallback_or_sanitized={String(response.persona.sanitized)} · facts_locked=
            {String(response.persona.facts_locked)} · {response.persona.fact_policy} ·
            public_safe={String(response.persona.public_safe)} · sanitized=
            {String(response.persona.sanitized)}
          </Text>
          {response.persona.rendered_answer ? (
            <Text style={styles.body}>{response.persona.rendered_answer}</Text>
          ) : null}
        </Section>
      ) : null}

      <Section label={`Evidence (${response.evidence.length})`}>
        {response.evidence.length === 0 ? (
          <Text style={styles.muted}>No evidence attached.</Text>
        ) : (
          response.evidence.map((item) => (
            <View key={item.id} style={styles.item}>
              <Text style={styles.itemTitle}>
                {item.id} · {item.source_type} · {item.confidence}
              </Text>
              <Text style={styles.body}>{item.content}</Text>
              <Text style={styles.muted}>{item.source_label}</Text>
            </View>
          ))
        )}
      </Section>

      <Section label={`Confidence (${response.confidence_notes.length})`}>
        {response.confidence_notes.length === 0 ? (
          <Text style={styles.muted}>No confidence notes attached.</Text>
        ) : (
          response.confidence_notes.map((note, index) => (
            <View key={`${note.claim_scope}-${index}`} style={styles.item}>
              <Text style={styles.itemTitle}>
                {note.claim_scope} · {note.confidence}
              </Text>
              <Text style={styles.body}>{note.note}</Text>
            </View>
          ))
        )}
      </Section>

      {response.presentation ? (
        <Section label={`Detail Sections (${response.presentation.detail_sections.length})`}>
          {response.presentation.detail_sections.map((section) => (
            <View key={section.section_id} style={styles.item}>
              <Text style={styles.itemTitle}>
                {section.label} · {section.content_kind} · {section.default_visibility}
              </Text>
              <Text style={styles.body}>{section.content}</Text>
            </View>
          ))}
        </Section>
      ) : null}
    </View>
  );
}

function Section({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <View style={styles.section}>
      <Text style={styles.sectionTitle}>{label}</Text>
      {children}
    </View>
  );
}

const styles = StyleSheet.create({
  panel: {
    backgroundColor: colors.panel,
    borderColor: colors.border,
    borderRadius: 16,
    borderWidth: 1,
    marginTop: spacing.md,
    padding: spacing.md,
  },
  title: {
    color: colors.text,
    fontSize: 18,
    fontWeight: "700",
  },
  meta: {
    color: colors.accentDark,
    fontSize: 12,
    marginTop: spacing.xs,
  },
  section: {
    marginTop: spacing.md,
  },
  sectionTitle: {
    color: colors.text,
    fontSize: 14,
    fontWeight: "700",
    marginBottom: spacing.xs,
  },
  body: {
    color: colors.text,
    fontSize: 14,
    lineHeight: 20,
  },
  muted: {
    color: colors.muted,
    fontSize: 12,
    lineHeight: 18,
  },
  item: {
    borderColor: colors.border,
    borderRadius: 10,
    borderWidth: 1,
    marginBottom: spacing.sm,
    padding: spacing.sm,
  },
  itemTitle: {
    color: colors.accentDark,
    fontSize: 13,
    fontWeight: "700",
    marginBottom: spacing.xs,
  },
  warningBlock: {
    marginTop: spacing.sm,
  },
  warningText: {
    color: colors.accentDark,
    fontSize: 12,
    lineHeight: 18,
  },
  code: {
    color: colors.text,
    fontFamily: "Courier",
    fontSize: 12,
    lineHeight: 16,
  },
});
