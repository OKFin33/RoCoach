import React, { useEffect, useState } from "react";
import { PanResponder, SafeAreaView, StyleSheet, View, useWindowDimensions } from "react-native";
import { StatusBar } from "expo-status-bar";

import { ProductApiClient } from "./src/api/client";
import { SettingsDrawer } from "./src/components/SettingsDrawer";
import {
  DEFAULT_RUNTIME_SETTINGS,
  clearProviderKey,
  loadRuntimeSettings,
  saveRuntimeSettings,
  type RuntimeSettings,
} from "./src/runtime/runtimeSettings";
import { ChatScreen } from "./src/screens/ChatScreen";
import { rnTokens } from "./src/styles/rnHandoffTokens";

export default function App() {
  const { width } = useWindowDimensions();
  const [settingsOpen, setSettingsOpen] = useState(false);
  const [runtimeSettings, setRuntimeSettings] = useState<RuntimeSettings>(DEFAULT_RUNTIME_SETTINGS);
  const [settingsStatus, setSettingsStatus] = useState<string | null>("正在载入安全运行设置...");
  const [secureStoreAvailable, setSecureStoreAvailable] = useState(true);
  const apiClient = new ProductApiClient(runtimeSettings.apiBaseUrl);

  useEffect(() => {
    void reloadSettings();
  }, []);

  async function reloadSettings() {
    try {
      const result = await loadRuntimeSettings();
      setRuntimeSettings(result.settings);
      setSecureStoreAvailable(result.secureStoreAvailable);
      setSettingsStatus(result.warning ?? "已从安全存储载入运行设置。");
    } catch {
      setRuntimeSettings(DEFAULT_RUNTIME_SETTINGS);
      setSecureStoreAvailable(false);
      setSettingsStatus("运行设置无法载入，Native 模式已禁用。");
    }
  }

  async function saveSettings(nextSettings: RuntimeSettings) {
    await saveRuntimeSettings(nextSettings);
    setRuntimeSettings(nextSettings);
    setSecureStoreAvailable(true);
    setSettingsStatus("设置已保存，Provider Key 已进入平台安全存储。");
  }

  async function clearSavedProviderKey() {
    await clearProviderKey();
    setRuntimeSettings((current) => ({ ...current, providerKey: "" }));
    setSettingsStatus("Provider Key 已从安全存储清除。");
  }

  const edgeSwipeResponder = PanResponder.create({
    onMoveShouldSetPanResponder: (event, gestureState) =>
      !settingsOpen && event.nativeEvent.pageX > width - 36 && gestureState.dx < -24,
    onPanResponderRelease: (_event, gestureState) => {
      if (gestureState.dx < -48) {
        setSettingsOpen(true);
      }
    },
  });

  return (
    <SafeAreaView style={styles.safeArea} {...edgeSwipeResponder.panHandlers}>
      <StatusBar style="dark" />
      <View style={styles.content}>
        <ChatScreen
          apiClient={apiClient}
          runtimeSettings={runtimeSettings}
          secureStoreAvailable={secureStoreAvailable}
        />
      </View>
      <SettingsDrawer
        apiClient={apiClient}
        draft={runtimeSettings}
        onChange={setRuntimeSettings}
        onClearProviderKey={clearSavedProviderKey}
        onClose={() => setSettingsOpen(false)}
        onOpen={() => setSettingsOpen(true)}
        onReload={reloadSettings}
        onSave={saveSettings}
        open={settingsOpen}
        secureStoreAvailable={secureStoreAvailable}
        statusMessage={settingsStatus}
      />
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  safeArea: {
    backgroundColor: rnTokens.color.shellYellow,
    flex: 1,
  },
  content: {
    flex: 1,
  },
});
