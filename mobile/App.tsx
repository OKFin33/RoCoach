import React, { useEffect, useState } from "react";
import { PanResponder, SafeAreaView, StyleSheet, View, useWindowDimensions } from "react-native";
import { StatusBar } from "expo-status-bar";

import { ProductApiClient } from "./src/api/client";
import { SettingsDrawer } from "./src/components/roco/SettingsDrawer";
import {
  DEFAULT_PERSONA_SELECTOR,
  DEFAULT_PERSONA_UI_ID,
} from "./src/roco/rocoPersona";
import type { PersonaSelector, RocoPersonaUiId } from "./src/roco/rocoTheme";
import {
  DEFAULT_RUNTIME_SETTINGS,
  clearProviderKey,
  loadRuntimeSettings,
  saveRuntimeSettings,
  type RuntimeSettings,
} from "./src/runtime/runtimeSettings";
import {
  EMPTY_TEAM_CONTEXT_STORE,
  loadTeamContextStore,
  saveTeamContextStore,
  type TeamContextStore,
} from "./src/roco/teamContext";
import { ChatScreen } from "./src/screens/ChatScreen";
import { rnTokens } from "./src/styles/rnHandoffTokens";

export default function App() {
  const { width } = useWindowDimensions();
  const [settingsOpen, setSettingsOpen] = useState(false);
  const [runtimeSettings, setRuntimeSettings] = useState<RuntimeSettings>(DEFAULT_RUNTIME_SETTINGS);
  const [settingsStatus, setSettingsStatus] = useState<string | null>("正在载入安全运行设置...");
  const [secureStoreAvailable, setSecureStoreAvailable] = useState(true);
  const [activePersonaUiId, setActivePersonaUiId] = useState<RocoPersonaUiId>(DEFAULT_PERSONA_UI_ID);
  const [activePersonaSelector, setActivePersonaSelector] = useState<PersonaSelector | null>(DEFAULT_PERSONA_SELECTOR);
  const [teamContextStore, setTeamContextStore] = useState<TeamContextStore>(EMPTY_TEAM_CONTEXT_STORE);
  const apiClient = new ProductApiClient(runtimeSettings.apiBaseUrl);

  useEffect(() => {
    void reloadSettings();
  }, []);

  async function reloadSettings() {
    try {
      const [result, teamStore] = await Promise.all([
        loadRuntimeSettings(),
        loadTeamContextStore(),
      ]);
      setRuntimeSettings(result.settings);
      setTeamContextStore(teamStore);
      setSecureStoreAvailable(result.secureStoreAvailable);
      setSettingsStatus(result.warning ?? "已从安全存储载入运行设置。");
    } catch {
      setRuntimeSettings(DEFAULT_RUNTIME_SETTINGS);
      setTeamContextStore(EMPTY_TEAM_CONTEXT_STORE);
      setSecureStoreAvailable(false);
      setSettingsStatus("运行设置无法载入，模型服务配置暂不可用。");
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
      setRuntimeSettings((current) => ({
      ...current,
      providerKey: "",
      runtimeMode: "deterministic",
    }));
    setSettingsStatus("Provider Key 已从安全存储清除。");
  }

  async function saveTeamStore(nextStore: TeamContextStore) {
    await saveTeamContextStore(nextStore);
    setTeamContextStore(nextStore);
    setSettingsStatus("编队已保存到本机。");
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
          activePersonaSelector={activePersonaSelector}
          activePersonaUiId={activePersonaUiId}
          apiClient={apiClient}
          onPersonaChange={(uiId, selector) => {
            setActivePersonaUiId(uiId);
            setActivePersonaSelector(selector);
          }}
          runtimeSettings={runtimeSettings}
          secureStoreAvailable={secureStoreAvailable}
          teamContextStore={teamContextStore}
        />
      </View>
      <SettingsDrawer
        activePersonaUiId={activePersonaUiId}
        apiClient={apiClient}
        draft={runtimeSettings}
        onChange={setRuntimeSettings}
        onClearProviderKey={clearSavedProviderKey}
        onClose={() => setSettingsOpen(false)}
        onOpen={() => setSettingsOpen(true)}
        onReload={reloadSettings}
        onSave={saveSettings}
        onTeamContextStoreChange={saveTeamStore}
        open={settingsOpen}
        secureStoreAvailable={secureStoreAvailable}
        statusMessage={settingsStatus}
        teamContextStore={teamContextStore}
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
