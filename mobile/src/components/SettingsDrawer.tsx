import React, { useEffect, useRef, useState } from "react";
import {
  Animated,
  PanResponder,
  ScrollView,
  StyleSheet,
  Text,
  TextInput,
  TouchableOpacity,
  View,
  useWindowDimensions,
} from "react-native";

import { ProductApiClient } from "../api/client";
import type { HealthResponse, MetadataResponse } from "../api/types";
import type { RuntimeExecutionMode, RuntimeSettings } from "../runtime/runtimeSettings";
import { rnTokens } from "../styles/rnHandoffTokens";

type SettingsDrawerProps = {
  apiClient: ProductApiClient;
  draft: RuntimeSettings;
  onChange: (draft: RuntimeSettings) => void;
  onClearProviderKey: () => Promise<void>;
  onClose: () => void;
  onOpen: () => void;
  onReload: () => Promise<void>;
  onSave: (draft: RuntimeSettings) => Promise<void>;
  open: boolean;
  secureStoreAvailable: boolean;
  statusMessage: string | null;
};

const HANDLE_WIDTH = 26;

export function SettingsDrawer({
  apiClient,
  draft,
  onChange,
  onClearProviderKey,
  onClose,
  onOpen,
  onReload,
  onSave,
  open,
  secureStoreAvailable,
  statusMessage,
}: SettingsDrawerProps) {
  const { width } = useWindowDimensions();
  const drawerWidth = Math.min(width * 0.82, 340);
  const translateX = useRef(new Animated.Value(drawerWidth)).current;
  const dragStartOffset = useRef(drawerWidth);
  const [showApiKey, setShowApiKey] = useState(false);
  const [health, setHealth] = useState<HealthResponse | null>(null);
  const [metadata, setMetadata] = useState<MetadataResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    Animated.timing(translateX, {
      duration: 260,
      toValue: open ? 0 : drawerWidth,
      useNativeDriver: true,
    }).start();
  }, [drawerWidth, open, translateX]);

  const railPanResponder = PanResponder.create({
    onMoveShouldSetPanResponder: (_event, gestureState) => Math.abs(gestureState.dx) > 3,
    onPanResponderGrant: () => {
      dragStartOffset.current = open ? 0 : drawerWidth;
      translateX.stopAnimation();
    },
    onPanResponderMove: (_event, gestureState) => {
      const next = Math.max(0, Math.min(drawerWidth, dragStartOffset.current + gestureState.dx));
      translateX.setValue(next);
    },
    onPanResponderRelease: (_event, gestureState) => {
      const next = Math.max(0, Math.min(drawerWidth, dragStartOffset.current + gestureState.dx));
      if (next < drawerWidth * 0.72 || gestureState.dx < -42) {
        onOpen();
      } else {
        onClose();
      }
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

  function setRuntimeMode(runtimeMode: RuntimeExecutionMode) {
    onChange({ ...draft, runtimeMode });
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
      await onSave(draft);
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
      setError(caught instanceof Error ? caught.message : "请求失败。");
    } finally {
      setLoading(false);
    }
  }

  return (
    <View pointerEvents="box-none" style={styles.root}>
      {open ? (
        <TouchableOpacity accessibilityRole="button" onPress={onClose} style={styles.backdrop} />
      ) : null}
      <Animated.View
        pointerEvents="box-none"
        style={[
          styles.rail,
          {
            transform: [{ translateX }],
            width: drawerWidth,
          },
        ]}
      >
        <TouchableOpacity
          accessibilityLabel={open ? "关闭设置" : "打开设置"}
          accessibilityRole="button"
          activeOpacity={0.9}
          onPress={() => {
            if (open) {
              onClose();
            } else {
              onOpen();
            }
          }}
          style={styles.handle}
          {...railPanResponder.panHandlers}
        >
          <View style={styles.handleDot} />
          <View style={styles.handleDot} />
          <View style={styles.handleDot} />
        </TouchableOpacity>

        <ScrollView
          contentContainerStyle={styles.drawerContent}
          keyboardShouldPersistTaps="handled"
          style={styles.drawer}
          {...railPanResponder.panHandlers}
        >
          <View style={styles.headerStrip}>
            <Text style={styles.heading}>设置</Text>
            <Text style={styles.headerCaption}>请求级模型运行配置</Text>
          </View>
          <Text style={styles.warning}>
            API Key 只属于你。密钥通过平台安全存储保存，不写入仓库、请求正文、日志或截图。
          </Text>
          {!secureStoreAvailable ? <Text style={styles.error}>安全存储不可用，Native 模式密钥不会持久化。</Text> : null}
          {statusMessage ? <Text style={styles.caption}>{statusMessage}</Text> : null}

          <Text style={styles.label}>产品 API 地址</Text>
          <TextInput
            autoCapitalize="none"
            autoCorrect={false}
            onChangeText={(value) => setField("apiBaseUrl", value)}
            placeholder="http://127.0.0.1:8000"
            placeholderTextColor={rnTokens.color.muted}
            style={styles.input}
            value={draft.apiBaseUrl}
          />

          <Text style={styles.label}>Provider API Key</Text>
          <TextInput
            autoCapitalize="none"
            autoCorrect={false}
            onChangeText={(value) => setField("providerKey", value)}
            placeholder="仅存入平台安全存储"
            placeholderTextColor={rnTokens.color.muted}
            secureTextEntry={!showApiKey}
            style={styles.input}
            value={draft.providerKey}
          />
          <View style={styles.buttonRow}>
            <DrawerButton label={showApiKey ? "隐藏密钥" : "显示密钥"} onPress={() => setShowApiKey((current) => !current)} />
            <DrawerButton danger label="清除密钥" onPress={clearSecrets} />
          </View>

          <Text style={styles.label}>模型</Text>
          <TextInput
            autoCapitalize="none"
            autoCorrect={false}
            onChangeText={(value) => setField("model", value)}
            placeholder="model name"
            placeholderTextColor={rnTokens.color.muted}
            style={styles.input}
            value={draft.model}
          />

          <Text style={styles.label}>Provider Base URL</Text>
          <TextInput
            autoCapitalize="none"
            autoCorrect={false}
            onChangeText={(value) => setField("providerBaseUrl", value)}
            placeholder="https://provider.example/v1"
            placeholderTextColor={rnTokens.color.muted}
            style={styles.input}
            value={draft.providerBaseUrl}
          />

          <Text style={styles.label}>LLM Runtime</Text>
          <View style={styles.modeRow}>
            <TouchableOpacity
              onPress={() => setRuntimeMode("deterministic")}
              style={[styles.modeButton, draft.runtimeMode === "deterministic" ? styles.modeButtonActive : null]}
            >
              <Text style={styles.modeText}>确定性</Text>
            </TouchableOpacity>
            <TouchableOpacity
              onPress={() => setRuntimeMode("native")}
              style={[styles.modeButton, draft.runtimeMode === "native" ? styles.modeButtonActive : null]}
            >
              <Text style={styles.modeText}>Native</Text>
            </TouchableOpacity>
          </View>

          <TouchableOpacity
            onPress={() => setField("allowUnsafeLanHttp", !draft.allowUnsafeLanHttp)}
            style={[styles.unsafeToggle, draft.allowUnsafeLanHttp ? styles.unsafeToggleActive : null]}
          >
            <Text style={styles.unsafeText}>{draft.allowUnsafeLanHttp ? "已开启非安全 LAN HTTP 调试" : "非安全 LAN HTTP 调试关闭"}</Text>
          </TouchableOpacity>
          {draft.allowUnsafeLanHttp ? <Text style={styles.error}>仅限开发：Provider Key 可能经过非 HTTPS LAN。</Text> : null}

          <View style={styles.buttonStack}>
            <DrawerButton disabled={loading} label="保存设置" onPress={saveSettings} />
            <DrawerButton disabled={loading} label="重新载入" onPress={reloadSettings} />
            <DrawerButton disabled={loading} label={loading ? "检查中..." : "测试 API"} onPress={testConnection} />
            <DrawerButton label="关闭设置" onPress={onClose} />
          </View>

          {error ? <Text style={styles.error}>{error}</Text> : null}
          {health ? <Text style={styles.caption}>Health: {health.status} · {health.service_name}</Text> : null}
          {metadata ? <Text style={styles.caption}>Backend: {metadata.default_backend}</Text> : null}
        </ScrollView>
      </Animated.View>
    </View>
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
    <TouchableOpacity
      accessibilityRole="button"
      disabled={disabled}
      onPress={onPress}
      style={[styles.drawerButton, danger ? styles.drawerButtonDanger : null, disabled ? styles.drawerButtonDisabled : null]}
    >
      <Text style={[styles.drawerButtonText, danger ? styles.drawerButtonTextDanger : null]}>{label}</Text>
    </TouchableOpacity>
  );
}

const styles = StyleSheet.create({
  root: {
    bottom: 0,
    left: 0,
    position: "absolute",
    right: 0,
    top: 0,
    zIndex: 40,
  },
  backdrop: {
    backgroundColor: "rgba(17,17,17,0.28)",
    bottom: 0,
    left: 0,
    position: "absolute",
    right: 0,
    top: 0,
  },
  rail: {
    bottom: 0,
    position: "absolute",
    right: 0,
    top: 0,
  },
  handle: {
    alignItems: "center",
    backgroundColor: rnTokens.color.shellYellow,
    borderBottomLeftRadius: 13,
    borderColor: rnTokens.color.ink,
    borderRightWidth: 0,
    borderTopLeftRadius: 13,
    borderWidth: 3,
    gap: 4,
    height: 62,
    justifyContent: "center",
    left: -HANDLE_WIDTH,
    position: "absolute",
    top: "50%",
    width: HANDLE_WIDTH,
    zIndex: 2,
  },
  handleDot: {
    backgroundColor: rnTokens.color.ink,
    borderRadius: 999,
    height: 4,
    width: 4,
  },
  drawer: {
    backgroundColor: rnTokens.color.paper,
    borderBottomLeftRadius: 24,
    borderColor: rnTokens.color.ink,
    borderLeftWidth: 3,
    borderTopLeftRadius: 24,
    height: "100%",
    shadowColor: rnTokens.color.ink,
    shadowOffset: { height: 0, width: -8 },
    shadowOpacity: 0.22,
    shadowRadius: 18,
  },
  drawerContent: {
    padding: rnTokens.space.lg,
    paddingBottom: rnTokens.space.xl * 2,
  },
  headerStrip: {
    backgroundColor: rnTokens.color.shellYellow,
    borderColor: rnTokens.color.ink,
    borderRadius: 16,
    borderWidth: 3,
    marginBottom: rnTokens.space.md,
    padding: rnTokens.space.md,
  },
  heading: {
    color: rnTokens.color.ink,
    fontSize: 22,
    fontWeight: "900",
  },
  headerCaption: {
    color: rnTokens.color.inkSoft,
    fontSize: 11,
    fontWeight: "800",
    letterSpacing: 0.8,
    marginTop: 2,
  },
  warning: {
    backgroundColor: "rgba(216,137,46,0.1)",
    borderColor: rnTokens.color.warning,
    borderRadius: 12,
    borderWidth: 2,
    color: rnTokens.color.warning,
    fontSize: 12,
    lineHeight: 18,
    marginBottom: rnTokens.space.md,
    padding: rnTokens.space.sm,
  },
  label: {
    color: rnTokens.color.ink,
    fontSize: 13,
    fontWeight: "900",
    marginBottom: rnTokens.space.xs,
  },
  input: {
    backgroundColor: rnTokens.color.paperWarm,
    borderColor: rnTokens.color.ink,
    borderRadius: 10,
    borderWidth: 2,
    color: rnTokens.color.ink,
    marginBottom: rnTokens.space.md,
    padding: rnTokens.space.sm,
  },
  buttonRow: {
    flexDirection: "row",
    gap: rnTokens.space.sm,
    marginBottom: rnTokens.space.md,
  },
  modeRow: {
    flexDirection: "row",
    marginBottom: rnTokens.space.md,
  },
  modeButton: {
    borderColor: rnTokens.color.ink,
    borderRadius: 999,
    borderWidth: 2,
    marginRight: rnTokens.space.sm,
    paddingHorizontal: rnTokens.space.md,
    paddingVertical: rnTokens.space.sm,
  },
  modeButtonActive: {
    backgroundColor: rnTokens.color.shellYellow,
  },
  modeText: {
    color: rnTokens.color.ink,
    fontSize: 12,
    fontWeight: "900",
  },
  unsafeToggle: {
    borderColor: rnTokens.color.ink,
    borderRadius: 12,
    borderWidth: 2,
    marginBottom: rnTokens.space.sm,
    padding: rnTokens.space.sm,
  },
  unsafeToggleActive: {
    backgroundColor: "rgba(184,58,75,0.1)",
    borderColor: rnTokens.color.danger,
  },
  unsafeText: {
    color: rnTokens.color.ink,
    fontSize: 12,
    fontWeight: "800",
    lineHeight: 18,
  },
  buttonStack: {
    gap: rnTokens.space.sm,
    marginTop: rnTokens.space.sm,
  },
  drawerButton: {
    alignItems: "center",
    backgroundColor: rnTokens.color.ink,
    borderColor: rnTokens.color.ink,
    borderRadius: 14,
    borderWidth: 2,
    paddingHorizontal: rnTokens.space.sm,
    paddingVertical: 10,
  },
  drawerButtonDanger: {
    backgroundColor: "rgba(184,58,75,0.12)",
  },
  drawerButtonDisabled: {
    opacity: 0.48,
  },
  drawerButtonText: {
    color: rnTokens.color.shellYellow,
    fontSize: 12,
    fontWeight: "900",
    textAlign: "center",
  },
  drawerButtonTextDanger: {
    color: rnTokens.color.danger,
  },
  caption: {
    color: rnTokens.color.muted,
    fontSize: 12,
    lineHeight: 18,
    marginTop: rnTokens.space.sm,
  },
  error: {
    color: rnTokens.color.danger,
    fontSize: 12,
    lineHeight: 18,
    marginBottom: rnTokens.space.sm,
    marginTop: rnTokens.space.xs,
  },
});
