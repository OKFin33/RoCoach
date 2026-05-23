import React, { useEffect, useRef, useState } from "react";
import {
  Animated,
  PanResponder,
  Platform,
  Pressable,
  ScrollView,
  StyleSheet,
  Text,
  TextInput,
  View,
  useWindowDimensions,
} from "react-native";

import { ProductApiClient } from "../../api/client";
import type { HealthResponse, MetadataResponse, ModelDiagnosticResponse } from "../../api/types";
import {
  buildNativeRuntimeHeaders,
  type RuntimeSettings,
  type RuntimeReasoningEffort,
  type RuntimeModelProfile,
  type RuntimeThinkingMode,
} from "../../runtime/runtimeSettings";
import type { TeamContextStore } from "../../roco/teamContext";
import { getActiveTeamContext } from "../../roco/teamContext";
import {
  ROCO_V1_PARITY,
  rocoColors,
  type RocoPersonaUiId,
} from "../../roco/rocoTheme";
import { EyeIcon } from "./RocoIcons";
import { TeamContextBuilder } from "./TeamContextBuilder";

type SettingsView = "home" | "api" | "team";

type SettingsDrawerProps = {
  activePersonaUiId: RocoPersonaUiId;
  apiClient: ProductApiClient;
  draft: RuntimeSettings;
  onChange: (draft: RuntimeSettings) => void;
  onClearProviderKey: () => Promise<void>;
  onClose: () => void;
  onOpen: () => void;
  onReload: () => Promise<void>;
  onSave: (draft: RuntimeSettings) => Promise<void>;
  onTeamContextStoreChange: (store: TeamContextStore) => Promise<void>;
  open: boolean;
  secureStoreAvailable: boolean;
  statusMessage: string | null;
  teamContextStore: TeamContextStore;
};

export function SettingsDrawer({
  activePersonaUiId,
  apiClient,
  draft,
  onChange,
  onClearProviderKey,
  onClose,
  onOpen,
  onReload,
  onSave,
  onTeamContextStoreChange,
  open,
  secureStoreAvailable,
  statusMessage,
  teamContextStore,
}: SettingsDrawerProps) {
  const { width } = useWindowDimensions();
  const drawerWidth = width * ROCO_V1_PARITY.drawer.widthRatio;
  const translateX = useRef(new Animated.Value(open ? 0 : drawerWidth)).current;
  const dragStartOffset = useRef(open ? 0 : drawerWidth);
  const [showApiKey, setShowApiKey] = useState(false);
  const [health, setHealth] = useState<HealthResponse | null>(null);
  const [metadata, setMetadata] = useState<MetadataResponse | null>(null);
  const [modelDiagnostic, setModelDiagnostic] = useState<ModelDiagnosticResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [view, setView] = useState<SettingsView>("home");
  const activeTeamContext = getActiveTeamContext(teamContextStore);

  useEffect(() => {
    Animated.timing(translateX, {
      duration: 220,
      toValue: open ? 0 : drawerWidth,
      useNativeDriver: true,
    }).start();
  }, [drawerWidth, open, translateX]);

  const railPanResponder = PanResponder.create({
    onMoveShouldSetPanResponder: (_event, gestureState) => Math.abs(gestureState.dx) > 4,
    onPanResponderGrant: () => {
      translateX.stopAnimation((value) => {
        dragStartOffset.current = clamp(
          typeof value === "number" ? value : open ? 0 : drawerWidth,
          0,
          drawerWidth,
        );
      });
    },
    onPanResponderMove: (_event, gestureState) => {
      const next = clamp(dragStartOffset.current + gestureState.dx, 0, drawerWidth);
      translateX.setValue(next);
    },
    onPanResponderRelease: (_event, gestureState) => {
      const next = clamp(dragStartOffset.current + gestureState.dx, 0, drawerWidth);
      const startedOpen = dragStartOffset.current < drawerWidth / 2;
      const passedOpenThreshold = gestureState.dx < -ROCO_V1_PARITY.drawer.dragThreshold;
      const passedCloseThreshold = gestureState.dx > ROCO_V1_PARITY.drawer.dragThreshold;

      if (startedOpen && (passedCloseThreshold || next > drawerWidth / 2)) {
        onClose();
        return;
      }
      if (!startedOpen && (passedOpenThreshold || next < drawerWidth / 2)) {
        onOpen();
        return;
      }
      startedOpen ? onOpen() : onClose();
    },
    onPanResponderTerminate: () => {
      if (open) {
        onOpen();
      } else {
        onClose();
      }
    },
  });

  function setField(field: keyof RuntimeSettings, value: string | boolean) {
    onChange({ ...draft, [field]: value });
  }

  async function clearSecrets() {
    setError(null);
    await onClearProviderKey();
    setShowApiKey(false);
  }

  async function saveSettings() {
    setLoading(true);
    setError(null);
    try {
      const runtimeMode = hasCompleteProviderConfig(draft) ? "native" : "deterministic";
      const nextDraft: RuntimeSettings = { ...draft, runtimeMode };
      await onSave(nextDraft);
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "设置未保存。");
    } finally {
      setLoading(false);
    }
  }

  async function reloadSettings() {
    setLoading(true);
    setError(null);
    try {
      await onReload();
      setShowApiKey(false);
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "设置未重新载入。");
    } finally {
      setLoading(false);
    }
  }

  function closeDrawer() {
    setView("home");
    onClose();
  }

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
      setModelDiagnostic(null);
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "请求失败。");
    } finally {
      setLoading(false);
    }
  }

  async function testModelService() {
    const runtimeHeaders = buildNativeRuntimeHeaders(draft, { secureStoreAvailable });
    if (!runtimeHeaders.ok) {
      setError(runtimeHeaders.error);
      return;
    }

    setLoading(true);
    setError(null);
    try {
      const diagnostic = await apiClient.modelDiagnostic(
        { prompt: "用一句中文回答：Roco 模型服务连接是否成功？" },
        runtimeHeaders.headers,
      );
      setModelDiagnostic(diagnostic);
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "模型服务测试失败。");
    } finally {
      setLoading(false);
    }
  }

  return (
    <View pointerEvents="box-none" style={styles.root}>
      {open ? <Pressable accessibilityRole="button" onPress={closeDrawer} style={styles.backdrop} /> : null}
      <Animated.View
        pointerEvents="box-none"
        style={[
          styles.rail,
          {
            top: drawerTopInset,
            transform: [{ translateX }],
            width: drawerWidth,
          },
        ]}
      >
        <Pressable
          accessibilityLabel={open ? "关闭设置" : "打开设置"}
          accessibilityRole="button"
          onPress={open ? closeDrawer : onOpen}
          style={styles.handle}
          {...railPanResponder.panHandlers}
        >
          <View style={styles.handleDot} />
          <View style={styles.handleDot} />
          <View style={styles.handleDot} />
        </Pressable>
        <ScrollView
          contentContainerStyle={styles.drawerContent}
          keyboardShouldPersistTaps="handled"
          nestedScrollEnabled
          style={styles.drawer}
        >
          <View style={styles.header}>
            {view !== "home" ? (
              <Pressable accessibilityRole="button" onPress={() => setView("home")} style={styles.backButton}>
                <Text style={styles.backButtonText}>‹</Text>
              </Pressable>
            ) : null}
            <Text style={styles.heading}>{view === "api" ? "API 设置" : view === "team" ? "队伍设置" : "设置"}</Text>
          </View>

          {view === "home" ? (
            <HomeSettings
              activePersonaUiId={activePersonaUiId}
              apiConfigured={hasCompleteProviderConfig(draft)}
              activeTeamSize={activeTeamContext?.slots.length ?? 0}
              onOpenApi={() => setView("api")}
              onOpenTeam={() => setView("team")}
            />
          ) : null}

          {view === "team" ? (
            <TeamContextBuilder
              apiClient={apiClient}
              onStoreChange={onTeamContextStoreChange}
              store={teamContextStore}
            />
          ) : null}

          {view === "api" ? (
            <ApiSettings
              draft={draft}
              error={error}
              health={health}
              loading={loading}
              metadata={metadata}
              modelDiagnostic={modelDiagnostic}
              onClearSecrets={() => void clearSecrets()}
              onReload={() => void reloadSettings()}
              onSave={() => void saveSettings()}
              onSetField={setField}
              onShowApiKey={() => setShowApiKey((current) => !current)}
              onTestConnection={() => void testConnection()}
              onTestModelService={() => void testModelService()}
              secureStoreAvailable={secureStoreAvailable}
              showApiKey={showApiKey}
              statusMessage={statusMessage}
            />
          ) : null}
        </ScrollView>
      </Animated.View>
    </View>
  );
}

function HomeSettings({
  activePersonaUiId,
  activeTeamSize,
  apiConfigured,
  onOpenApi,
  onOpenTeam,
}: {
  activePersonaUiId: RocoPersonaUiId;
  activeTeamSize: number;
  apiConfigured: boolean;
  onOpenApi: () => void;
  onOpenTeam: () => void;
}) {
  return (
    <View style={styles.homeStack}>
      <SettingsCard
        body={activeTeamSize > 0 ? `默认编队 ${activeTeamSize}/6。` : "教练可以直接根据你的编队提供建议"}
        label="队伍设置"
        onPress={onOpenTeam}
        status={activeTeamSize > 0 ? "已启用" : "未设置"}
      />
      <SettingsCard
        body={apiConfigured ? "模型服务已配置。" : "填写 API Key、模型与接入点。"}
        label="API 设置"
        onPress={onOpenApi}
        status={apiConfigured ? "已配置" : "未完成"}
      />
      <View style={styles.personaCard}>
        <Text style={styles.cardLabel}>人格设置</Text>
        <Text style={styles.personaName}>{personaLabel(activePersonaUiId)}</Text>
        <Text style={styles.cardBody}>长按聊天头像可以切换人格</Text>
      </View>
    </View>
  );
}

function SettingsCard({
  body,
  label,
  onPress,
  status,
}: {
  body: string;
  label: string;
  onPress: () => void;
  status: string;
}) {
  return (
    <Pressable accessibilityRole="button" onPress={onPress} style={styles.settingsCard}>
      <View style={styles.cardHeaderLine}>
        <Text style={styles.cardLabel}>{label}</Text>
        <Text style={styles.cardArrow}>›</Text>
      </View>
      <Text style={styles.cardBody}>{body}</Text>
      <Text style={styles.cardStatus}>{status}</Text>
    </Pressable>
  );
}

function ApiSettings({
  draft,
  error,
  health,
  loading,
  metadata,
  modelDiagnostic,
  onClearSecrets,
  onReload,
  onSave,
  onSetField,
  onShowApiKey,
  onTestConnection,
  onTestModelService,
  secureStoreAvailable,
  showApiKey,
  statusMessage,
}: {
  draft: RuntimeSettings;
  error: string | null;
  health: HealthResponse | null;
  loading: boolean;
  metadata: MetadataResponse | null;
  modelDiagnostic: ModelDiagnosticResponse | null;
  onClearSecrets: () => void;
  onReload: () => void;
  onSave: () => void;
  onSetField: (field: keyof RuntimeSettings, value: string | boolean) => void;
  onShowApiKey: () => void;
  onTestConnection: () => void;
  onTestModelService: () => void;
  secureStoreAvailable: boolean;
  showApiKey: boolean;
  statusMessage: string | null;
}) {
  return (
    <View>
      <View style={styles.securityBox}>
        <Text style={styles.securityTitle}>API 密钥安全提示</Text>
        <Text style={styles.securityBody}>
          填写 API Key 后，Roco 会通过你配置的模型服务生成回复。密钥只保存在本机安全存储中，不会进入聊天内容、日志或人格资料。
        </Text>
      </View>
      {!secureStoreAvailable ? <Text style={styles.error}>SecureStore 不可用时，不保存密钥。</Text> : null}
      {statusMessage ? <Text style={styles.caption}>{statusMessage}</Text> : null}

      <FieldLabel label="Product API base URL" />
      <DrawerInput
        onChangeText={(value) => onSetField("apiBaseUrl", value)}
        placeholder="http://127.0.0.1:8000"
        value={draft.apiBaseUrl}
      />

      <FieldLabel label="Provider API key" />
      <View style={styles.secretRow}>
        <TextInput
          autoCapitalize="none"
          autoCorrect={false}
          onChangeText={(value) => onSetField("providerKey", value)}
          placeholder="sk-..."
          placeholderTextColor={rocoColors.muted}
          secureTextEntry={!showApiKey}
          style={[styles.input, styles.secretInput]}
          value={draft.providerKey}
        />
        <Pressable accessibilityLabel="显示或隐藏密钥" accessibilityRole="button" onPress={onShowApiKey} style={styles.eyeButton}>
          <EyeIcon />
        </Pressable>
      </View>
      <Text style={styles.caption}>密钥仅保存在本机安全存储。</Text>
      <View style={styles.singleButtonStack}>
        <DrawerButton danger label="清除密钥" onPress={onClearSecrets} />
      </View>

      <FieldLabel label="Provider base URL" />
      <DrawerInput
        onChangeText={(value) => onSetField("providerBaseUrl", value)}
        placeholder="https://api.openai.com/v1"
        value={draft.providerBaseUrl}
      />

      <FieldLabel label="Model" />
      <DrawerInput
        onChangeText={(value) => onSetField("model", value)}
        placeholder="gpt-4o"
        value={draft.model}
      />

      <FieldLabel label="模型配置" />
      <ModelProfileRow
        current={draft.modelProfile}
        onSelect={(profile) => applyModelProfile(profile, draft, onSetField)}
      />
      <Text style={styles.caption}>
        自定义单模型会把所有调用交给你填写的同一个模型。DeepSeek v4 快速配置只是填入推荐接入点和默认模型，不代表后端已启用按任务自动切换模型。
      </Text>

      <FieldLabel label="思考模式" />
      <ToggleRow
        current={draft.thinkingMode}
        labels={{ disabled: "关闭", enabled: "开启" }}
        onSelect={(mode) => onSetField("thinkingMode", mode)}
      />
      {draft.thinkingMode === "enabled" ? (
        <ToggleRow
          current={draft.reasoningEffort === "max" ? "max" : "high"}
          labels={{ high: "High", max: "Max" }}
          onSelect={(effort) => onSetField("reasoningEffort", effort)}
        />
      ) : null}
      <Text style={styles.caption}>Product API 测试不发送密钥；模型服务测试会消耗少量 provider token。</Text>

      <View style={styles.buttonStack}>
        <DrawerButton disabled={loading} label="保存设置" onPress={onSave} />
        <DrawerButton disabled={loading} label="重新载入" onPress={onReload} />
        <DrawerButton disabled={loading} label={loading ? "检查中..." : "测试 Product API"} onPress={onTestConnection} />
        <DrawerButton disabled={loading || !hasCompleteProviderConfig(draft)} label={loading ? "检查中..." : "测试模型服务"} onPress={onTestModelService} />
      </View>
      {error ? <Text style={styles.error}>{error}</Text> : null}
      {health ? <Text style={styles.caption}>Health: {health.status} · {health.service_name}</Text> : null}
      {metadata ? <Text style={styles.caption}>Backend: {metadata.default_backend}</Text> : null}
      {modelDiagnostic ? (
        <Text style={styles.caption}>
          Model: {modelDiagnostic.status} · {modelDiagnostic.diagnostic_code} · {modelDiagnostic.message}
        </Text>
      ) : null}
    </View>
  );
}

function ModelProfileRow({
  current,
  onSelect,
}: {
  current: RuntimeModelProfile;
  onSelect: (profile: RuntimeModelProfile) => void;
}) {
  return (
    <View style={styles.toggleRow}>
      {(["custom_single_model", "deepseek_v4_quick_setup"] as RuntimeModelProfile[]).map((profile) => (
        <Pressable
          accessibilityRole="button"
          key={profile}
          onPress={() => onSelect(profile)}
          style={[styles.togglePill, current === profile ? styles.togglePillActive : null]}
        >
          <Text style={[styles.togglePillText, current === profile ? styles.togglePillTextActive : null]}>
            {modelProfileLabel(profile)}
          </Text>
        </Pressable>
      ))}
    </View>
  );
}

function ToggleRow<T extends string>({
  current,
  labels,
  onSelect,
}: {
  current: T;
  labels: Record<T, string>;
  onSelect: (value: T) => void;
}) {
  return (
    <View style={styles.toggleRow}>
      {(Object.keys(labels) as T[]).map((key) => (
        <Pressable
          accessibilityRole="button"
          key={key}
          onPress={() => onSelect(key)}
          style={[styles.togglePill, current === key ? styles.togglePillActive : null]}
        >
          <Text style={[styles.togglePillText, current === key ? styles.togglePillTextActive : null]}>
            {labels[key]}
          </Text>
        </Pressable>
      ))}
    </View>
  );
}

function applyModelProfile(
  profile: RuntimeModelProfile,
  draft: RuntimeSettings,
  onSetField: (field: keyof RuntimeSettings, value: string | boolean) => void,
) {
  onSetField("modelProfile", profile);
  if (profile === "custom_single_model") {
    return;
  }
  onSetField("providerBaseUrl", "https://api.deepseek.com");
  if (!draft.model || !draft.model.startsWith("deepseek-v4-")) {
    onSetField("model", "deepseek-v4-flash");
  }
  onSetField("thinkingMode", "disabled" satisfies RuntimeThinkingMode);
  onSetField("reasoningEffort", "none" satisfies RuntimeReasoningEffort);
}

function modelProfileLabel(profile: RuntimeModelProfile): string {
  switch (profile) {
    case "deepseek_v4_quick_setup":
      return "DeepSeek 快速配置";
    case "custom_single_model":
    default:
      return "自定义单模型";
  }
}

function FieldLabel({ label }: { label: string }) {
  return <Text style={styles.label}>{label}</Text>;
}

function DrawerInput({
  onChangeText,
  placeholder,
  value,
}: {
  onChangeText: (value: string) => void;
  placeholder: string;
  value: string;
}) {
  return (
    <TextInput
      autoCapitalize="none"
      autoCorrect={false}
      onChangeText={onChangeText}
      placeholder={placeholder}
      placeholderTextColor={rocoColors.muted}
      style={styles.input}
      value={value}
    />
  );
}

function DrawerButton({
  danger = false,
  disabled = false,
  label,
  onPress,
}: {
  danger?: boolean;
  disabled?: boolean;
  label: string;
  onPress: () => void;
}) {
  return (
    <Pressable
      accessibilityRole="button"
      disabled={disabled}
      onPress={onPress}
      style={[styles.drawerButton, danger ? styles.drawerButtonDanger : null, disabled ? styles.drawerButtonDisabled : null]}
    >
      <Text style={[styles.drawerButtonText, danger ? styles.drawerButtonTextDanger : null]}>{label}</Text>
    </Pressable>
  );
}

function clamp(value: number, min: number, max: number) {
  return Math.min(Math.max(value, min), max);
}

function hasCompleteProviderConfig(settings: RuntimeSettings): boolean {
  return (
    settings.providerKey.trim().length > 0 &&
    settings.providerBaseUrl.trim().length > 0 &&
    settings.model.trim().length > 0
  );
}

function personaLabel(uiId: RocoPersonaUiId): string {
  switch (uiId) {
    case "ai_assistant":
      return "默认AI助手";
    case "add_persona":
      return "添加人格";
    case "you_know_who":
    default:
      return "You know who";
  }
}

const drawer = ROCO_V1_PARITY.drawer;
const drawerTopInset = Platform.OS === "ios" ? 54 : 10;

const styles = StyleSheet.create({
  root: {
    ...StyleSheet.absoluteFillObject,
    zIndex: 50,
  },
  backdrop: {
    ...StyleSheet.absoluteFillObject,
    backgroundColor: "rgba(17,17,17,0.20)",
  },
  rail: {
    bottom: 0,
    position: "absolute",
    right: 0,
  },
  handle: {
    alignItems: "center",
    backgroundColor: rocoColors.shellYellow,
    borderBottomLeftRadius: drawer.handle.radius,
    borderColor: rocoColors.ink,
    borderRightWidth: 0,
    borderTopLeftRadius: drawer.handle.radius,
    borderWidth: drawer.handle.borderWidth,
    gap: drawer.handle.gripGap,
    height: drawer.handle.height,
    justifyContent: "center",
    left: drawer.handle.leftOffset,
    position: "absolute",
    top: "50%",
    width: drawer.handle.width,
    zIndex: 2,
  },
  handleDot: {
    backgroundColor: rocoColors.ink,
    borderRadius: 999,
    height: drawer.handle.gripDotSize,
    width: drawer.handle.gripDotSize,
  },
  drawer: {
    backgroundColor: "#FFFCF2",
    borderColor: rocoColors.ink,
    borderLeftWidth: drawer.handle.borderWidth,
    height: "100%",
    shadowColor: rocoColors.ink,
    shadowOffset: { height: 0, width: -8 },
    shadowOpacity: 0.22,
    shadowRadius: 16,
    elevation: 8,
  },
  drawerContent: {
    padding: 0,
    paddingBottom: 42,
  },
  header: {
    alignItems: "center",
    backgroundColor: rocoColors.shellYellow,
    borderBottomColor: "rgba(23,23,23,0.18)",
    borderBottomWidth: 2,
    flexDirection: "row",
    minHeight: 86,
    paddingHorizontal: 18,
    paddingTop: 4,
  },
  backButton: {
    alignItems: "center",
    height: 44,
    justifyContent: "center",
    marginRight: 4,
    width: 34,
  },
  backButtonText: {
    color: rocoColors.ink,
    fontSize: 34,
    fontWeight: "800",
    lineHeight: 38,
  },
  heading: {
    color: rocoColors.ink,
    fontSize: 28,
    fontWeight: "900",
  },
  homeStack: {
    gap: 14,
    padding: 18,
    paddingTop: 24,
  },
  settingsCard: {
    backgroundColor: "#FFFDF7",
    borderColor: "rgba(23,23,23,0.14)",
    borderRadius: 16,
    borderWidth: 2,
    padding: 16,
  },
  personaCard: {
    backgroundColor: "#FFFDF7",
    borderColor: "rgba(23,23,23,0.14)",
    borderRadius: 16,
    borderWidth: 2,
    padding: 16,
  },
  cardHeaderLine: {
    alignItems: "center",
    flexDirection: "row",
    justifyContent: "space-between",
  },
  cardLabel: {
    color: rocoColors.ink,
    fontSize: 18,
    fontWeight: "900",
  },
  cardArrow: {
    color: rocoColors.inkSoft,
    fontSize: 30,
    fontWeight: "700",
    lineHeight: 30,
  },
  cardBody: {
    color: rocoColors.inkSoft,
    fontSize: 14,
    lineHeight: 21,
    marginTop: 8,
  },
  cardStatus: {
    color: rocoColors.muted,
    fontSize: 12,
    fontWeight: "800",
    marginTop: 12,
  },
  personaName: {
    color: rocoColors.ink,
    fontSize: 18,
    fontWeight: "900",
    marginTop: 12,
  },
  placeholderPanel: {
    backgroundColor: "#FFFDF7",
    borderColor: "rgba(23,23,23,0.14)",
    borderRadius: 16,
    borderWidth: 2,
    margin: 18,
    padding: 16,
  },
  securityBox: {
    backgroundColor: "rgba(229,154,45,0.10)",
    borderColor: rocoColors.warning,
    borderRadius: 14,
    borderWidth: 2,
    margin: 18,
    marginBottom: 16,
    padding: 14,
  },
  securityTitle: {
    color: rocoColors.ink,
    fontSize: 13,
    fontWeight: "900",
    marginBottom: 4,
  },
  securityBody: {
    color: rocoColors.inkSoft,
    fontSize: 12,
    lineHeight: 18,
  },
  caption: {
    color: rocoColors.muted,
    fontSize: 12,
    lineHeight: 18,
    marginBottom: 10,
    marginHorizontal: 18,
  },
  label: {
    color: rocoColors.ink,
    fontSize: 13,
    fontWeight: "900",
    marginBottom: 5,
    marginHorizontal: 18,
  },
  input: {
    backgroundColor: "#FFFDF7",
    borderColor: "rgba(23,23,23,0.18)",
    borderRadius: 14,
    borderWidth: 2,
    color: rocoColors.ink,
    fontSize: 15,
    marginBottom: 12,
    marginHorizontal: 18,
    paddingHorizontal: 10,
    paddingVertical: 12,
  },
  secretRow: {
    flexDirection: "row",
    gap: 8,
    marginHorizontal: 18,
  },
  secretInput: {
    flex: 1,
    marginHorizontal: 0,
  },
  eyeButton: {
    alignItems: "center",
    backgroundColor: "#FFFDF7",
    borderColor: "rgba(23,23,23,0.18)",
    borderRadius: 14,
    borderWidth: 2,
    height: 48,
    justifyContent: "center",
    width: 48,
  },
  buttonStack: {
    gap: 6,
    marginHorizontal: 18,
    marginTop: 8,
  },
  toggleRow: {
    flexDirection: "row",
    flexWrap: "wrap",
    gap: 8,
    marginBottom: 12,
    paddingHorizontal: 18,
  },
  togglePill: {
    backgroundColor: "#FFFDF7",
    borderColor: "rgba(23,23,23,0.20)",
    borderRadius: 999,
    borderWidth: 2,
    paddingHorizontal: 12,
    paddingVertical: 8,
  },
  togglePillActive: {
    backgroundColor: rocoColors.shellYellow,
    borderColor: rocoColors.ink,
  },
  togglePillText: {
    color: rocoColors.inkSoft,
    fontSize: 13,
    fontWeight: "800",
  },
  togglePillTextActive: {
    color: rocoColors.ink,
  },
  singleButtonStack: {
    marginBottom: 12,
    marginHorizontal: 18,
  },
  drawerButton: {
    alignItems: "center",
    backgroundColor: rocoColors.shellYellow,
    borderColor: rocoColors.ink,
    borderRadius: 13,
    borderWidth: 2,
    justifyContent: "center",
    minHeight: 40,
    paddingHorizontal: 10,
    paddingVertical: 0,
  },
  drawerButtonDanger: {
    backgroundColor: "rgba(184,58,75,0.12)",
  },
  drawerButtonDisabled: {
    opacity: 0.5,
  },
  drawerButtonText: {
    color: rocoColors.ink,
    fontSize: 14,
    fontWeight: "900",
    textAlign: "center",
  },
  drawerButtonTextDanger: {
    color: rocoColors.danger,
  },
  error: {
    color: rocoColors.danger,
    fontSize: 12,
    lineHeight: 18,
    marginBottom: 10,
    marginHorizontal: 18,
  },
});
