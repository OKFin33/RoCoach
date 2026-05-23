import React, { useEffect, useState } from "react";
import { Modal, Pressable, ScrollView, StyleSheet, Text, TextInput, View } from "react-native";

import type { ProductApiClient } from "../../api/client";
import type {
  SpeciesMoveRecord,
  SpeciesSearchItem,
  TeamContextAttachment,
  TeamContextSlot,
  TeamMoveSelection,
  TeamStatKey,
} from "../../api/types";
import {
  createTeamId,
  getActiveTeamContext,
  upsertActiveTeamContext,
  type TeamContextStore,
} from "../../roco/teamContext";
import { rocoColors } from "../../roco/rocoTheme";
import { RewriteIcon, XIcon } from "./RocoIcons";

type TeamContextBuilderProps = {
  apiClient: ProductApiClient;
  onStoreChange: (store: TeamContextStore) => Promise<void>;
  store: TeamContextStore;
};

type PickerState =
  | { kind: "closed" }
  | { kind: "species"; slotIndex: number }
  | { kind: "moves"; activeCell: number; slotIndex: number };

type SelectOption<T extends string | number> = {
  label: string;
  meta?: string;
  value: T;
};

type NatureOption = {
  label: string;
  minus: TeamStatKey | null;
  plus: TeamStatKey | null;
};

const STAT_KEYS: TeamStatKey[] = ["hp", "atk", "defense", "spa", "spd", "spe"];
const STAT_LABELS: Record<TeamStatKey, string> = {
  hp: "生命",
  atk: "物攻",
  defense: "物防",
  spa: "魔攻",
  spd: "魔防",
  spe: "速度",
};
const IV_VALUES = [7, 8, 9, 10] as const;
const NATURE_OPTIONS: NatureOption[] = [
  { label: "沉默", plus: "hp", minus: "atk" },
  { label: "平和", plus: "hp", minus: "spa" },
  { label: "理智", plus: "hp", minus: "defense" },
  { label: "忧郁", plus: "hp", minus: "spd" },
  { label: "紧张", plus: "hp", minus: "spe" },
  { label: "保守", plus: "spa", minus: "atk" },
  { label: "冷静", plus: "spa", minus: "spe" },
  { label: "稳重", plus: "spa", minus: "defense" },
  { label: "马虎", plus: "spa", minus: "spd" },
  { label: "认真", plus: "spa", minus: "hp" },
  { label: "沉着", plus: "spd", minus: "atk" },
  { label: "慎重", plus: "spd", minus: "spa" },
  { label: "温顺", plus: "spd", minus: "defense" },
  { label: "狂妄", plus: "spd", minus: "spe" },
  { label: "实干", plus: "spd", minus: "hp" },
  { label: "胆小", plus: "spe", minus: "atk" },
  { label: "开朗", plus: "spe", minus: "spa" },
  { label: "急躁", plus: "spe", minus: "defense" },
  { label: "天真", plus: "spe", minus: "spd" },
  { label: "浮躁", plus: "spe", minus: "hp" },
  { label: "固执", plus: "atk", minus: "spa" },
  { label: "勇敢", plus: "atk", minus: "spe" },
  { label: "孤僻", plus: "atk", minus: "defense" },
  { label: "调皮", plus: "atk", minus: "spd" },
  { label: "坦率", plus: "atk", minus: "hp" },
  { label: "大胆", plus: "defense", minus: "atk" },
  { label: "淘气", plus: "defense", minus: "spa" },
  { label: "懒散", plus: "defense", minus: "spd" },
  { label: "悠闲", plus: "defense", minus: "spe" },
  { label: "害羞", plus: "defense", minus: "hp" },
];
const STAT_SELECT_OPTIONS: SelectOption<TeamStatKey>[] = STAT_KEYS.map((stat) => ({
  label: STAT_LABELS[stat],
  value: stat,
}));
const NATURE_SELECT_OPTIONS: SelectOption<string>[] = NATURE_OPTIONS.map((nature) => ({
  label: nature.label,
  meta:
    nature.plus && nature.minus
      ? `+${STAT_LABELS[nature.plus]} / -${STAT_LABELS[nature.minus]}`
      : "无修正",
  value: nature.label,
}));
const IV_SELECT_OPTIONS: SelectOption<number>[] = IV_VALUES.map((value) => ({
  label: String(value),
  value,
}));

export function TeamContextBuilder({
  apiClient,
  onStoreChange,
  store,
}: TeamContextBuilderProps) {
  const activeTeam = getActiveTeamContext(store) ?? createEmptyTeam();
  const [draft, setDraft] = useState<TeamContextAttachment>(activeTeam);
  const [speciesQuery, setSpeciesQuery] = useState("");
  const [speciesResults, setSpeciesResults] = useState<SpeciesSearchItem[]>([]);
  const [movePools, setMovePools] = useState<Record<string, SpeciesMoveRecord[]>>({});
  const [moveQueries, setMoveQueries] = useState<Record<number, string>>({});
  const [selectedSlotIndex, setSelectedSlotIndex] = useState<number>(
    draft.slots[0]?.slot_index ?? 1,
  );
  const [picker, setPicker] = useState<PickerState>({ kind: "closed" });
  const [status, setStatus] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const selectedSlot = draft.slots.find((slot) => slot.slot_index === selectedSlotIndex) ?? null;

  useEffect(() => {
    let active = true;
    const query = speciesQuery.trim();
    if (picker.kind !== "species") {
      return () => {
        active = false;
      };
    }
    if (!query) {
      setSpeciesResults([]);
      setStatus(null);
      return () => {
        active = false;
      };
    }
    const timer = setTimeout(() => {
      void searchSpeciesForQuery(query, () => active);
    }, 260);
    return () => {
      active = false;
      clearTimeout(timer);
    };
  }, [apiClient, picker.kind, speciesQuery]);

  async function searchSpeciesForQuery(query: string, isActive: () => boolean) {
    setLoading(true);
    setStatus(null);
    try {
      const response = await apiClient.searchSpecies(query, 12);
      if (!isActive()) {
        return;
      }
      setSpeciesResults(response.results);
      if (response.results.length === 0) {
        setStatus("数据库没有匹配精灵。");
      }
    } catch {
      if (!isActive()) {
        return;
      }
      setStatus("精灵搜索失败。");
    } finally {
      if (isActive()) {
        setLoading(false);
      }
    }
  }

  async function ensureMovePool(speciesId: string) {
    if (movePools[speciesId]) {
      return;
    }
    try {
      const movesResponse = await apiClient.speciesMoves(speciesId);
      setMovePools((current) => ({ ...current, [speciesId]: movesResponse.moves }));
    } catch {
      setStatus("技能列表载入失败。");
    }
  }

  async function selectSpecies(result: SpeciesSearchItem) {
    const slotIndex = picker.kind === "species" ? picker.slotIndex : selectedSlotIndex;
    if (draft.slots.length >= 6 && !draft.slots.some((slot) => slot.slot_index === slotIndex)) {
      setStatus("队伍已满，最多 6 只精灵。");
      return;
    }
    setLoading(true);
    setStatus(null);
    try {
      const [profileResponse, movesResponse] = await Promise.all([
        apiClient.speciesProfile(result.species_id),
        apiClient.speciesMoves(result.species_id),
      ]);
      const profile = profileResponse.profile;
      const slot: TeamContextSlot = {
        slot_index: slotIndex,
        species_id: asString(profile.species_id, result.species_id),
        display_name: speciesDisplayLabel({
          display_name: asString(profile.display_name, result.display_name),
          regional_form_name: asOptionalString(profile.regional_form_name ?? result.regional_form_name),
        }),
        primary_type: asString(profile.primary_type, result.primary_type),
        secondary_type: asOptionalString(profile.secondary_type ?? result.secondary_type),
        fixed_ability: abilityFromProfile(profile),
        selected_moves: [],
        nature: { label: "默认", plus_stat: null, minus_stat: null },
        individual_value_bonuses: [],
        notes: null,
      };
      setMovePools((current) => ({ ...current, [slot.species_id]: movesResponse.moves }));
      setDraft((current) => replaceSlot(current, slot));
      setSelectedSlotIndex(slotIndex);
      setPicker({ kind: "closed" });
      setSpeciesResults([]);
      setSpeciesQuery("");
    } catch {
      setStatus("载入精灵资料失败。");
    } finally {
      setLoading(false);
    }
  }

  async function openSpeciesPicker(slotIndex: number) {
    setSelectedSlotIndex(slotIndex);
    setSpeciesQuery("");
    setSpeciesResults([]);
    setPicker({ kind: "species", slotIndex });
  }

  async function openMovePicker(slot: TeamContextSlot) {
    await ensureMovePool(slot.species_id);
    setMoveQueries((current) => ({ ...current, [slot.slot_index]: "" }));
    setPicker({
      kind: "moves",
      slotIndex: slot.slot_index,
      activeCell: Math.min(slot.selected_moves.length, 3),
    });
  }

  async function saveDraft() {
    setLoading(true);
    setStatus(null);
    try {
      await onStoreChange(upsertActiveTeamContext(store, normalizeDraft(draft)));
      setStatus("编队已保存，会随下一次聊天发送。");
    } catch {
      setStatus("编队保存失败。");
    } finally {
      setLoading(false);
    }
  }

  async function clearDraft() {
    const nextTeam = createEmptyTeam();
    setDraft(nextTeam);
    setSelectedSlotIndex(1);
    await onStoreChange({
      schema_version: "team_context_store.v1",
      active_team_id: null,
      teams: store.teams.filter((team) => team.team_id !== draft.team_id),
    });
    setStatus("已清空当前编队。");
  }

  function updateSlot(slot: TeamContextSlot) {
    setDraft((current) => replaceSlot(current, slot));
  }

  function updateMove(slot: TeamContextSlot, cellIndex: number, move: SpeciesMoveRecord) {
    if (!move.move_id) {
      return;
    }
    const boundedIndex = Math.min(cellIndex, slot.selected_moves.length);
    const nextMoves = [...slot.selected_moves];
    nextMoves[boundedIndex] = moveSelectionFromRecord(move);
    updateSlot({ ...slot, selected_moves: nextMoves.slice(0, 4) });
    setPicker({ kind: "closed" });
  }

  return (
    <View style={styles.root}>
      <Text style={styles.title}>默认编队</Text>
      <Text style={styles.body}>教练可以直接根据你的编队提供建议</Text>

      <View style={styles.slotGrid}>
        {Array.from({ length: 6 }, (_, index) => {
          const slotIndex = index + 1;
          const slot = draft.slots.find((item) => item.slot_index === slotIndex);
          return (
            <Pressable
              accessibilityRole="button"
              key={slotIndex}
              onPress={() => {
                setSelectedSlotIndex(slotIndex);
                if (slot) {
                  void ensureMovePool(slot.species_id);
                }
              }}
              style={[
                styles.slotChip,
                selectedSlotIndex === slotIndex ? styles.slotChipActive : null,
              ]}
            >
              <Text style={styles.slotChipTitle}>{slotIndex}</Text>
              <Text numberOfLines={1} style={styles.slotChipText}>{slot?.display_name ?? "空位"}</Text>
            </Pressable>
          );
        })}
      </View>

      {selectedSlot ? (
        <SlotEditor
          onOpenMovePicker={() => void openMovePicker(selectedSlot)}
          onOpenSpeciesPicker={() => void openSpeciesPicker(selectedSlot.slot_index)}
          onUpdate={updateSlot}
          slot={selectedSlot}
        />
      ) : (
        <EmptySlotEditor
          onOpenSpeciesPicker={() => void openSpeciesPicker(selectedSlotIndex)}
          slotIndex={selectedSlotIndex}
        />
      )}

      <View style={styles.buttonRow}>
        <Pressable accessibilityRole="button" disabled={loading} onPress={() => void saveDraft()} style={styles.button}>
          <Text style={styles.buttonText}>保存编队</Text>
        </Pressable>
        <Pressable accessibilityRole="button" disabled={loading} onPress={() => void clearDraft()} style={[styles.button, styles.secondaryButton]}>
          <Text style={styles.buttonText}>清空</Text>
        </Pressable>
      </View>
      {status ? <Text style={styles.status}>{status}</Text> : null}

      <SpeciesPickerModal
        loading={loading}
        onClose={() => setPicker({ kind: "closed" })}
        onQueryChange={setSpeciesQuery}
        onSelect={(result) => void selectSpecies(result)}
        open={picker.kind === "species"}
        query={speciesQuery}
        results={speciesResults}
      />
      <MovePickerModal
        activeCell={picker.kind === "moves" ? picker.activeCell : 0}
        movePool={selectedSlot ? movePools[selectedSlot.species_id] ?? [] : []}
        onActiveCellChange={(activeCell) =>
          setPicker((current) =>
            current.kind === "moves" ? { ...current, activeCell } : current,
          )
        }
        onClose={() => setPicker({ kind: "closed" })}
        onMoveQueryChange={(value) =>
          selectedSlot
            ? setMoveQueries((current) => ({ ...current, [selectedSlot.slot_index]: value }))
            : undefined
        }
        onSelectMove={(move) =>
          selectedSlot && picker.kind === "moves"
            ? updateMove(selectedSlot, picker.activeCell, move)
            : undefined
        }
        open={picker.kind === "moves" && Boolean(selectedSlot)}
        query={selectedSlot ? moveQueries[selectedSlot.slot_index] ?? "" : ""}
        selectedMoves={selectedSlot?.selected_moves ?? []}
      />
    </View>
  );
}

function EmptySlotEditor({
  onOpenSpeciesPicker,
  slotIndex,
}: {
  onOpenSpeciesPicker: () => void;
  slotIndex: number;
}) {
  return (
    <View style={styles.editor}>
      <View style={styles.editorTitleRow}>
        <View style={styles.speciesTag}>
          <Text style={styles.speciesTagText}>空位 {slotIndex}</Text>
        </View>
        <PenButton accessibilityLabel="选择精灵" onPress={onOpenSpeciesPicker} />
      </View>
      <Text style={styles.body}>选择一只精灵加入当前空位。</Text>
    </View>
  );
}

function SlotEditor({
  onOpenMovePicker,
  onOpenSpeciesPicker,
  onUpdate,
  slot,
}: {
  onOpenMovePicker: () => void;
  onOpenSpeciesPicker: () => void;
  onUpdate: (slot: TeamContextSlot) => void;
  slot: TeamContextSlot;
}) {
  const [selector, setSelector] = useState<
    | { kind: "closed" }
    | { kind: "nature_label" }
    | { kind: "nature_plus" }
    | { kind: "nature_minus" }
    | { kind: "bonus_stat"; rowIndex: number }
    | { kind: "bonus_value"; rowIndex: number }
  >({ kind: "closed" });

  const bonusRows = Array.from({ length: 3 }, (_, index) => slot.individual_value_bonuses[index] ?? null);

  function setNatureLabel(label: string) {
    const nature = NATURE_OPTIONS.find((option) => option.label === label);
    applyNature(nature ?? { label, plus: null, minus: null });
  }

  function setNatureStat(kind: "plus" | "minus", stat: TeamStatKey | null) {
    const nextPlus = kind === "plus" ? stat : slot.nature.plus_stat;
    const nextMinus = kind === "minus" ? stat : slot.nature.minus_stat;
    const exact = NATURE_OPTIONS.find(
      (option) => option.plus === nextPlus && option.minus === nextMinus,
    );
    const fallback =
      kind === "plus"
        ? NATURE_OPTIONS.find((option) => option.plus === nextPlus)
        : NATURE_OPTIONS.find((option) => option.minus === nextMinus);
    applyNature(exact ?? fallback ?? NATURE_OPTIONS.find((option) => !option.plus && !option.minus));
  }

  function applyNature(nature: NatureOption | undefined) {
    if (!nature) {
      return;
    }
    onUpdate({
      ...slot,
      nature: {
        label: nature.label,
        plus_stat: nature.plus,
        minus_stat: nature.minus,
      },
    });
  }

  function setBonusStat(rowIndex: number, stat: TeamStatKey | null) {
    const next = [...slot.individual_value_bonuses];
    if (!stat) {
      next.splice(rowIndex, 1);
      onUpdate({ ...slot, individual_value_bonuses: next.slice(0, 3) });
      return;
    }
    const duplicateIndex = next.findIndex((bonus, index) => index !== rowIndex && bonus.stat === stat);
    if (duplicateIndex >= 0) {
      next.splice(duplicateIndex, 1);
    }
    next[rowIndex] = { stat, value: next[rowIndex]?.value ?? 8 };
    onUpdate({ ...slot, individual_value_bonuses: next.filter(Boolean).slice(0, 3) });
  }

  function setBonusValue(rowIndex: number, value: number) {
    const current = slot.individual_value_bonuses[rowIndex];
    if (!current) {
      return;
    }
    const next = [...slot.individual_value_bonuses];
    next[rowIndex] = { ...current, value };
    onUpdate({ ...slot, individual_value_bonuses: next.slice(0, 3) });
  }

  const selectorConfig = buildSlotSelectorConfig(selector, slot);

  return (
    <View style={styles.editor}>
      <View style={styles.editorTitleRow}>
        <View style={styles.speciesTag}>
          <Text style={styles.speciesTagText}>{slot.display_name}</Text>
        </View>
        <PenButton accessibilityLabel="更换精灵" onPress={onOpenSpeciesPicker} />
      </View>
      <Text style={styles.body}>
        {slot.primary_type}{slot.secondary_type ? ` / ${slot.secondary_type}` : ""} · 特性 {slot.fixed_ability?.ability_name ?? "数据库未提供"}
      </Text>

      <Text style={styles.label}>性格</Text>
      <View style={styles.natureLinkedRow}>
        <Pressable
          accessibilityRole="button"
          onPress={() => setSelector({ kind: "nature_plus" })}
          style={styles.natureStatField}
        >
          <Text style={styles.natureSign}>+</Text>
          <Text numberOfLines={1} style={styles.natureStatText}>
            {slot.nature.plus_stat ? STAT_LABELS[slot.nature.plus_stat] : "无"}
          </Text>
        </Pressable>
        <Pressable
          accessibilityRole="button"
          onPress={() => setSelector({ kind: "nature_label" })}
          style={styles.natureNameField}
        >
          <Text style={styles.natureNameText}>{slot.nature.label || "默认"}</Text>
        </Pressable>
        <Pressable
          accessibilityRole="button"
          onPress={() => setSelector({ kind: "nature_minus" })}
          style={styles.natureStatField}
        >
          <Text style={styles.natureSign}>-</Text>
          <Text numberOfLines={1} style={styles.natureStatText}>
            {slot.nature.minus_stat ? STAT_LABELS[slot.nature.minus_stat] : "无"}
          </Text>
        </Pressable>
      </View>
      <Text style={styles.label}>个体增益</Text>
      <View style={styles.bonusColumn}>
        {bonusRows.map((bonus, index) => (
          <View key={`bonus-row-${index}`} style={styles.bonusPickerRow}>
            <Pressable
              accessibilityRole="button"
              onPress={() => setSelector({ kind: "bonus_stat", rowIndex: index })}
              style={styles.bonusStatField}
            >
              <Text style={styles.fieldValueText}>{bonus ? STAT_LABELS[bonus.stat] : "选择属性"}</Text>
            </Pressable>
            <Pressable
              accessibilityRole="button"
              disabled={!bonus}
              onPress={() => setSelector({ kind: "bonus_value", rowIndex: index })}
              style={[styles.bonusNumberField, bonus ? null : styles.disabledField]}
            >
              <Text style={styles.bonusNumberText}>{bonus?.value ?? "-"}</Text>
            </Pressable>
          </View>
        ))}
      </View>

      {selectorConfig ? (
        <SelectionSheet
          onClose={() => setSelector({ kind: "closed" })}
          onSelect={(value) => {
            if (selector.kind === "nature_label" && typeof value === "string") {
              setNatureLabel(value);
            } else if (selector.kind === "nature_plus" && typeof value === "string") {
              setNatureStat("plus", value as TeamStatKey);
            } else if (selector.kind === "nature_minus" && typeof value === "string") {
              setNatureStat("minus", value as TeamStatKey);
            } else if (selector.kind === "bonus_stat" && typeof value === "string") {
              setBonusStat(selector.rowIndex, value === "none" ? null : (value as TeamStatKey));
            } else if (selector.kind === "bonus_value" && typeof value === "number") {
              setBonusValue(selector.rowIndex, value);
            }
            setSelector({ kind: "closed" });
          }}
          options={selectorConfig.options}
          selectedValue={selectorConfig.selectedValue}
          subtitle={selectorConfig.subtitle}
          title={selectorConfig.title}
        />
      ) : null}

      <View style={styles.skillHeaderRow}>
        <Text style={styles.label}>技能</Text>
        <PenButton accessibilityLabel="修改技能" onPress={onOpenMovePicker} />
      </View>
      <SkillGrid selectedMoves={slot.selected_moves} />
    </View>
  );
}

function buildSlotSelectorConfig(
  selector:
    | { kind: "closed" }
    | { kind: "nature_label" }
    | { kind: "nature_plus" }
    | { kind: "nature_minus" }
    | { kind: "bonus_stat"; rowIndex: number }
    | { kind: "bonus_value"; rowIndex: number },
  slot: TeamContextSlot,
):
  | {
      options: SelectOption<string | number>[];
      selectedValue: string | number | null;
      subtitle?: string;
      title: string;
    }
  | null {
  switch (selector.kind) {
    case "nature_label":
      return {
        options: NATURE_SELECT_OPTIONS,
        selectedValue: slot.nature.label ?? null,
        title: "选择性格",
      };
    case "nature_plus":
      return {
        options: STAT_SELECT_OPTIONS,
        selectedValue: slot.nature.plus_stat ?? null,
        title: "选择增益属性",
      };
    case "nature_minus":
      return {
        options: STAT_SELECT_OPTIONS,
        selectedValue: slot.nature.minus_stat ?? null,
        title: "选择减益属性",
      };
    case "bonus_stat":
      return {
        options: [{ label: "无", value: "none" }, ...STAT_SELECT_OPTIONS],
        selectedValue: slot.individual_value_bonuses[selector.rowIndex]?.stat ?? "none",
        title: `选择栏位 ${selector.rowIndex + 1}`,
      };
    case "bonus_value":
      return {
        options: IV_SELECT_OPTIONS,
        selectedValue: slot.individual_value_bonuses[selector.rowIndex]?.value ?? null,
        subtitle: "填入初始个体即可，PvP 系统会自动调整数值",
        title: "选择个体数值",
      };
    case "closed":
      return null;
  }
}

function SelectionSheet<T extends string | number>({
  onClose,
  onSelect,
  options,
  selectedValue,
  subtitle,
  title,
}: {
  onClose: () => void;
  onSelect: (value: T) => void;
  options: SelectOption<T>[];
  selectedValue: T | null;
  subtitle?: string;
  title: string;
}) {
  return (
    <Modal animationType="fade" transparent visible>
      <View style={styles.modalBackdrop}>
        <View style={styles.selectionCard}>
          <View style={styles.modalHeader}>
            <Text style={styles.modalTitle}>{title}</Text>
            <Pressable accessibilityRole="button" onPress={onClose} style={styles.closeButton}>
              <XIcon />
            </Pressable>
          </View>
          {subtitle ? <Text style={styles.selectionSubtitle}>{subtitle}</Text> : null}
          <ScrollView contentContainerStyle={styles.selectionList} nestedScrollEnabled>
            {options.map((option) => (
              <Pressable
                accessibilityRole="button"
                key={`${option.value}`}
                onPress={() => onSelect(option.value)}
                style={[
                  styles.selectionRow,
                  selectedValue === option.value ? styles.slotChipActive : null,
                ]}
              >
                <Text style={styles.selectionTitle}>{option.label}</Text>
                {option.meta ? <Text style={styles.resultMeta}>{option.meta}</Text> : null}
              </Pressable>
            ))}
          </ScrollView>
        </View>
      </View>
    </Modal>
  );
}

function SpeciesPickerModal({
  loading,
  onClose,
  onQueryChange,
  onSelect,
  open,
  query,
  results,
}: {
  loading: boolean;
  onClose: () => void;
  onQueryChange: (value: string) => void;
  onSelect: (result: SpeciesSearchItem) => void;
  open: boolean;
  query: string;
  results: SpeciesSearchItem[];
}) {
  return (
    <Modal animationType="fade" transparent visible={open}>
      <View style={styles.modalBackdrop}>
        <View style={styles.modalCard}>
          <View style={styles.modalHeader}>
            <Text style={styles.modalTitle}>选择精灵</Text>
            <Pressable accessibilityRole="button" onPress={onClose} style={styles.closeButton}>
              <XIcon />
            </Pressable>
          </View>
          <TextInput
            autoCapitalize="none"
            autoCorrect={false}
            onChangeText={onQueryChange}
            placeholder="搜索精灵名称"
            placeholderTextColor={rocoColors.muted}
            style={styles.input}
            value={query}
          />
          <Text style={styles.searchRuleText}>搜索规则：精灵名或其初始形态带有搜索关键词</Text>
          {loading ? <Text style={styles.status}>搜索中...</Text> : null}
          <ScrollView contentContainerStyle={styles.modalResultList} nestedScrollEnabled>
            {results.map((result) => (
              <Pressable
                accessibilityRole="button"
                key={result.species_id}
                onPress={() => onSelect(result)}
                style={styles.resultRow}
              >
                <Text style={styles.resultTitle}>{speciesDisplayLabel(result)}</Text>
                <Text style={styles.resultMeta}>{speciesResultMeta(result)}</Text>
              </Pressable>
            ))}
          </ScrollView>
        </View>
      </View>
    </Modal>
  );
}

function MovePickerModal({
  activeCell,
  movePool,
  onActiveCellChange,
  onClose,
  onMoveQueryChange,
  onSelectMove,
  open,
  query,
  selectedMoves,
}: {
  activeCell: number;
  movePool: SpeciesMoveRecord[];
  onActiveCellChange: (cell: number) => void;
  onClose: () => void;
  onMoveQueryChange: (value: string) => void;
  onSelectMove: (move: SpeciesMoveRecord) => void;
  open: boolean;
  query: string;
  selectedMoves: TeamMoveSelection[];
}) {
  const filteredMoves = movePool
    .filter((move) => move.move_id)
    .filter((move) => !query.trim() || move.move_name.includes(query.trim()))
    .slice(0, 24);

  return (
    <Modal animationType="fade" transparent visible={open}>
      <View style={styles.modalBackdrop}>
        <View style={styles.modalCard}>
          <View style={styles.modalHeader}>
            <Text style={styles.modalTitle}>修改技能</Text>
            <Pressable accessibilityRole="button" onPress={onClose} style={styles.closeButton}>
              <XIcon />
            </Pressable>
          </View>
          <View style={styles.largeSkillGrid}>
            {Array.from({ length: 4 }, (_, index) => (
              <Pressable
                accessibilityRole="button"
                key={`modal-skill-${index}`}
                onPress={() => onActiveCellChange(index)}
                style={[
                  styles.largeSkillCell,
                  activeCell === index ? styles.slotChipActive : null,
                ]}
              >
                <Text numberOfLines={2} style={styles.skillCellText}>
                  {selectedMoves[index]?.move_name ?? "空技能"}
                </Text>
              </Pressable>
            ))}
          </View>
          <TextInput
            autoCapitalize="none"
            autoCorrect={false}
            onChangeText={onMoveQueryChange}
            placeholder="搜索该精灵可用技能"
            placeholderTextColor={rocoColors.muted}
            style={styles.input}
            value={query}
          />
          <ScrollView contentContainerStyle={styles.modalResultList} nestedScrollEnabled>
            {filteredMoves.length === 0 ? <Text style={styles.status}>该精灵暂无可用技能数据。</Text> : null}
            {filteredMoves.map((move) => (
              <Pressable
                accessibilityRole="button"
                key={`${move.move_id ?? move.move_name}-${move.access_channel}`}
                onPress={() => onSelectMove(move)}
                style={styles.moveRow}
              >
                <Text style={styles.resultTitle}>{move.move_name}</Text>
                <Text style={styles.resultMeta}>{move.move_type ?? "-"} · {move.category_raw ?? "-"} · {move.access_channel}</Text>
              </Pressable>
            ))}
          </ScrollView>
        </View>
      </View>
    </Modal>
  );
}

function PenButton({
  accessibilityLabel,
  onPress,
}: {
  accessibilityLabel: string;
  onPress: () => void;
}) {
  return (
    <Pressable accessibilityLabel={accessibilityLabel} accessibilityRole="button" onPress={onPress} style={styles.penButton}>
      <RewriteIcon color="#FFFDF7" size={15} strokeWidth={2.2} />
    </Pressable>
  );
}

function SkillGrid({ selectedMoves }: { selectedMoves: TeamMoveSelection[] }) {
  return (
    <View style={styles.skillGrid}>
      {Array.from({ length: 4 }, (_, index) => (
        <View key={`skill-${index}`} style={styles.skillCell}>
          <Text numberOfLines={2} style={styles.skillCellText}>{selectedMoves[index]?.move_name ?? "空技能"}</Text>
        </View>
      ))}
    </View>
  );
}

function speciesDisplayLabel(
  species: Pick<SpeciesSearchItem, "display_name" | "regional_form_name">,
) {
  const regional = species.regional_form_name?.trim();
  return regional ? `${species.display_name}（${regional}）` : species.display_name;
}

function speciesResultMeta(result: SpeciesSearchItem) {
  const parts = [
    result.initial_species_name ? `初始形态 ${result.initial_species_name}` : null,
    result.form_name,
    result.primary_type + (result.secondary_type ? ` / ${result.secondary_type}` : ""),
  ];
  return parts.filter(Boolean).join(" · ");
}

function createEmptyTeam(): TeamContextAttachment {
  return {
    kind: "team_context",
    schema_version: "team_context.v1",
    source: "team_builder",
    team_id: createTeamId(),
    active: true,
    slots: [],
  };
}

function normalizeDraft(draft: TeamContextAttachment): TeamContextAttachment {
  return {
    ...draft,
    slots: draft.slots
      .slice(0, 6)
      .sort((left, right) => left.slot_index - right.slot_index)
      .map((slot) => ({
        ...slot,
        selected_moves: slot.selected_moves.slice(0, 4),
        individual_value_bonuses: slot.individual_value_bonuses.slice(0, 3),
      })),
  };
}

function replaceSlot(team: TeamContextAttachment, slot: TeamContextSlot): TeamContextAttachment {
  return {
    ...team,
    slots: [...team.slots.filter((item) => item.slot_index !== slot.slot_index), slot].sort(
      (left, right) => left.slot_index - right.slot_index,
    ),
  };
}

function moveSelectionFromRecord(move: SpeciesMoveRecord): TeamMoveSelection {
  return {
    move_id: move.move_id ?? "",
    move_name: move.move_name,
    access_channel: move.access_channel,
    move_type: move.move_type,
    category_raw: move.category_raw,
  };
}

function abilityFromProfile(profile: Record<string, unknown>) {
  const abilityName = asOptionalString(profile.ability_name);
  if (!abilityName) {
    return null;
  }
  return {
    ability_name: abilityName,
    effect_text: asOptionalString(profile.ability_effect_text),
  };
}

function asString(value: unknown, fallback: string): string {
  return typeof value === "string" && value.trim() ? value : fallback;
}

function asOptionalString(value: unknown): string | null {
  return typeof value === "string" && value.trim() ? value : null;
}

const styles = StyleSheet.create({
  root: {
    gap: 12,
    padding: 18,
  },
  title: {
    color: rocoColors.ink,
    fontSize: 18,
    fontWeight: "900",
  },
  body: {
    color: rocoColors.inkSoft,
    fontSize: 13,
    lineHeight: 19,
  },
  label: {
    color: rocoColors.ink,
    fontSize: 13,
    fontWeight: "900",
    marginTop: 8,
  },
  input: {
    backgroundColor: "#FFFDF7",
    borderColor: "rgba(23,23,23,0.18)",
    borderRadius: 14,
    borderWidth: 2,
    color: rocoColors.ink,
    fontSize: 14,
    paddingHorizontal: 10,
    paddingVertical: 10,
  },
  button: {
    alignItems: "center",
    backgroundColor: rocoColors.shellYellow,
    borderColor: rocoColors.ink,
    borderRadius: 13,
    borderWidth: 2,
    justifyContent: "center",
    minHeight: 40,
    paddingHorizontal: 10,
  },
  secondaryButton: {
    backgroundColor: "#FFFDF7",
  },
  buttonText: {
    color: rocoColors.ink,
    fontSize: 14,
    fontWeight: "900",
  },
  buttonRow: {
    flexDirection: "row",
    gap: 8,
  },
  slotGrid: {
    flexDirection: "row",
    flexWrap: "wrap",
    gap: 8,
    justifyContent: "space-between",
  },
  slotChip: {
    backgroundColor: "#FFFDF7",
    borderColor: "rgba(23,23,23,0.18)",
    borderRadius: 12,
    borderWidth: 2,
    minHeight: 62,
    padding: 9,
    width: "48%",
  },
  slotChipActive: {
    backgroundColor: "rgba(255,210,60,0.55)",
    borderColor: rocoColors.ink,
  },
  slotChipTitle: {
    color: rocoColors.ink,
    fontSize: 12,
    fontWeight: "900",
  },
  slotChipText: {
    color: rocoColors.inkSoft,
    fontSize: 13,
    marginTop: 5,
  },
  resultRow: {
    backgroundColor: "#FFFDF7",
    borderColor: "rgba(23,23,23,0.14)",
    borderRadius: 12,
    borderWidth: 2,
    padding: 10,
  },
  resultTitle: {
    color: rocoColors.ink,
    fontSize: 14,
    fontWeight: "900",
  },
  resultMeta: {
    color: rocoColors.muted,
    fontSize: 12,
    marginTop: 3,
  },
  searchRuleText: {
    color: rocoColors.muted,
    fontSize: 11,
    lineHeight: 16,
    marginTop: -4,
  },
  editor: {
    backgroundColor: "rgba(255,253,247,0.72)",
    borderColor: "rgba(23,23,23,0.14)",
    borderRadius: 16,
    borderWidth: 2,
    gap: 8,
    padding: 12,
  },
  editorTitleRow: {
    alignItems: "center",
    flexDirection: "row",
    gap: 8,
  },
  speciesTag: {
    backgroundColor: "#FFFDF7",
    borderColor: rocoColors.ink,
    borderRadius: 999,
    borderWidth: 2,
    flex: 1,
    paddingHorizontal: 12,
    paddingVertical: 8,
  },
  speciesTagText: {
    color: rocoColors.ink,
    fontSize: 15,
    fontWeight: "900",
  },
  penButton: {
    alignItems: "center",
    backgroundColor: rocoColors.ink,
    borderColor: rocoColors.ink,
    borderRadius: 999,
    borderWidth: 2,
    height: 34,
    justifyContent: "center",
    width: 34,
  },
  natureNameField: {
    alignItems: "center",
    backgroundColor: "#FFFDF7",
    borderColor: "rgba(23,23,23,0.16)",
    borderRadius: 14,
    borderWidth: 2,
    flex: 1,
    justifyContent: "center",
    minHeight: 58,
    paddingHorizontal: 10,
    paddingVertical: 9,
  },
  natureNameText: {
    color: rocoColors.ink,
    fontSize: 18,
    fontWeight: "900",
    textAlign: "center",
  },
  natureLinkedRow: {
    alignItems: "stretch",
    flexDirection: "row",
    gap: 8,
  },
  natureStatField: {
    alignItems: "center",
    backgroundColor: "#FFFDF7",
    borderColor: "rgba(23,23,23,0.16)",
    borderRadius: 14,
    borderWidth: 2,
    justifyContent: "center",
    minHeight: 58,
    paddingHorizontal: 8,
    paddingVertical: 9,
    width: 70,
  },
  natureSign: {
    color: rocoColors.ink,
    fontSize: 17,
    fontWeight: "900",
    lineHeight: 19,
  },
  natureStatText: {
    color: rocoColors.ink,
    fontSize: 13,
    fontWeight: "900",
    marginTop: 2,
    textAlign: "center",
  },
  fieldValueText: {
    color: rocoColors.ink,
    fontSize: 14,
    fontWeight: "900",
    marginTop: 3,
  },
  bonusColumn: {
    gap: 8,
  },
  bonusPickerRow: {
    alignItems: "stretch",
    flexDirection: "row",
    gap: 8,
  },
  bonusStatField: {
    backgroundColor: "#FFFDF7",
    borderColor: "rgba(23,23,23,0.16)",
    borderRadius: 14,
    borderWidth: 2,
    flex: 1,
    paddingHorizontal: 10,
    paddingVertical: 9,
  },
  bonusNumberField: {
    alignItems: "center",
    backgroundColor: rocoColors.shellYellow,
    borderColor: rocoColors.ink,
    borderRadius: 14,
    borderWidth: 2,
    justifyContent: "center",
    width: 48,
  },
  bonusNumberText: {
    color: rocoColors.ink,
    fontSize: 16,
    fontWeight: "900",
  },
  disabledField: {
    backgroundColor: "rgba(216,208,190,0.4)",
    borderColor: "rgba(23,23,23,0.14)",
  },
  skillHeaderRow: {
    alignItems: "center",
    flexDirection: "row",
    justifyContent: "space-between",
  },
  skillGrid: {
    flexDirection: "row",
    flexWrap: "wrap",
    gap: 8,
  },
  skillCell: {
    alignItems: "center",
    backgroundColor: "#FFFDF7",
    borderColor: "rgba(23,23,23,0.14)",
    borderRadius: 12,
    borderWidth: 2,
    justifyContent: "center",
    minHeight: 50,
    padding: 8,
    width: "48%",
  },
  skillCellText: {
    color: rocoColors.ink,
    fontSize: 12,
    fontWeight: "800",
    textAlign: "center",
  },
  modalBackdrop: {
    alignItems: "center",
    backgroundColor: "rgba(17,17,17,0.28)",
    flex: 1,
    justifyContent: "center",
    padding: 18,
  },
  modalCard: {
    backgroundColor: rocoColors.paper,
    borderColor: rocoColors.ink,
    borderRadius: 18,
    borderWidth: 3,
    gap: 10,
    maxHeight: "86%",
    padding: 14,
    width: "100%",
  },
  selectionCard: {
    backgroundColor: rocoColors.paper,
    borderColor: rocoColors.ink,
    borderRadius: 18,
    borderWidth: 3,
    gap: 10,
    maxHeight: "72%",
    padding: 14,
    width: "82%",
  },
  selectionList: {
    gap: 8,
    paddingBottom: 4,
  },
  selectionRow: {
    backgroundColor: "#FFFDF7",
    borderColor: "rgba(23,23,23,0.14)",
    borderRadius: 14,
    borderWidth: 2,
    paddingHorizontal: 12,
    paddingVertical: 11,
  },
  selectionTitle: {
    color: rocoColors.ink,
    fontSize: 15,
    fontWeight: "900",
  },
  selectionSubtitle: {
    color: rocoColors.inkSoft,
    fontSize: 12,
    lineHeight: 18,
  },
  modalResultList: {
    gap: 8,
    paddingBottom: 4,
  },
  modalHeader: {
    alignItems: "center",
    flexDirection: "row",
    justifyContent: "space-between",
  },
  modalTitle: {
    color: rocoColors.ink,
    fontSize: 17,
    fontWeight: "900",
  },
  closeButton: {
    alignItems: "center",
    backgroundColor: "#FFFDF7",
    borderColor: rocoColors.ink,
    borderRadius: 999,
    borderWidth: 2,
    height: 32,
    justifyContent: "center",
    width: 32,
  },
  largeSkillGrid: {
    flexDirection: "row",
    flexWrap: "wrap",
    gap: 8,
    justifyContent: "space-between",
  },
  largeSkillCell: {
    alignItems: "center",
    backgroundColor: "#FFFDF7",
    borderColor: "rgba(23,23,23,0.16)",
    borderRadius: 14,
    borderWidth: 2,
    justifyContent: "center",
    minHeight: 70,
    padding: 10,
    width: "48%",
  },
  moveRow: {
    backgroundColor: "#FFFDF7",
    borderColor: "rgba(23,23,23,0.12)",
    borderRadius: 12,
    borderWidth: 2,
    padding: 9,
  },
  status: {
    color: rocoColors.muted,
    fontSize: 12,
    lineHeight: 18,
  },
});
