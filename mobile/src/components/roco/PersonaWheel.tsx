import React, { useEffect, useRef } from "react";
import {
  Animated,
  Pressable,
  StyleSheet,
  View,
  useWindowDimensions,
} from "react-native";

import {
  ROCO_V1_PARITY,
  personaWheelOffsets,
  rocoColors,
  type RocoPersonaUiId,
  type RocoPersonaWheelState,
} from "../../roco/rocoTheme";
import { PERSONA_WHEEL_OPTIONS } from "../../roco/rocoPersona";
import { AgentAvatarArt, PersonaAddAvatar, SelectionBadge } from "./AgentAvatar";

const AnimatedPressable = Animated.createAnimatedComponent(Pressable);

type PersonaWheelProps = {
  activePersonaUiId: RocoPersonaUiId;
  onClose: () => void;
  onSelect: (uiId: RocoPersonaUiId) => void;
  state: RocoPersonaWheelState;
};

export function PersonaWheel({
  activePersonaUiId,
  onClose,
  onSelect,
  state,
}: PersonaWheelProps) {
  const screen = useWindowDimensions();
  const backdropOpacity = useRef(new Animated.Value(0)).current;
  const haloProgress = useRef(new Animated.Value(0)).current;
  const optionProgress = useRef(
    ROCO_V1_PARITY.personaWheel.positions.map(() => new Animated.Value(0)),
  ).current;

  useEffect(() => {
    if (state.status !== "open") {
      return;
    }

    backdropOpacity.setValue(0);
    haloProgress.setValue(0);
    optionProgress.forEach((progress) => progress.setValue(0));

    Animated.parallel([
      Animated.timing(backdropOpacity, {
        duration: ROCO_V1_PARITY.personaWheel.backdropFadeMs,
        toValue: 1,
        useNativeDriver: true,
      }),
      Animated.timing(haloProgress, {
        duration: ROCO_V1_PARITY.personaWheel.haloScaleMs,
        toValue: 1,
        useNativeDriver: true,
      }),
      Animated.stagger(
        ROCO_V1_PARITY.personaWheel.optionStaggerMs,
        optionProgress.map((progress) =>
          Animated.spring(progress, {
            damping: ROCO_V1_PARITY.personaWheel.optionSpringDamping,
            mass: 1,
            stiffness: ROCO_V1_PARITY.personaWheel.optionSpringStiffness,
            toValue: 1,
            useNativeDriver: true,
          }),
        ),
      ),
    ]).start();
  }, [backdropOpacity, haloProgress, optionProgress, state.status]);

  if (state.status !== "open") {
    return null;
  }

  const anchor = state.anchor;
  const offsets = personaWheelOffsets();

  return (
    <View pointerEvents="box-none" style={styles.root}>
      <AnimatedPressable
        accessibilityRole="button"
        onPress={onClose}
        style={[styles.backdrop, { opacity: backdropOpacity }]}
      />
      <Animated.View
        pointerEvents="none"
        style={[
          styles.haloOuter,
          {
            left: anchor.x - ROCO_V1_PARITY.personaWheel.haloOuterSize / 2,
            opacity: haloProgress,
            top: anchor.y - ROCO_V1_PARITY.personaWheel.haloOuterSize / 2,
            transform: [
              {
                scale: haloProgress.interpolate({
                  inputRange: [0, 1],
                  outputRange: [0.82, 1],
                }),
              },
            ],
          },
        ]}
      >
        <View style={styles.haloInner} />
      </Animated.View>
      {offsets.map((offset, index) => {
        const option = PERSONA_WHEEL_OPTIONS.find((item) => item.ui_id === offset.ui_id);
        if (!option) {
          return null;
        }
        const left = clamp(
          anchor.x + offset.x - ROCO_V1_PARITY.personaWheel.itemSize / 2,
          10,
          screen.width - ROCO_V1_PARITY.personaWheel.itemSize - 10,
        );
        const top = clamp(
          anchor.y + offset.y - ROCO_V1_PARITY.personaWheel.itemSize / 2,
          34,
          screen.height - ROCO_V1_PARITY.personaWheel.itemSize - 34,
        );
        const selected = activePersonaUiId === option.ui_id;
        const progress = optionProgress[index] ?? optionProgress[0];
        return (
          <AnimatedPressable
            accessibilityLabel={option.label}
            accessibilityRole="button"
            key={option.ui_id}
            onPress={() => onSelect(option.ui_id)}
            style={[
              styles.option,
              {
                left,
                opacity: progress,
                top,
                transform: [
                  {
                    translateX: progress.interpolate({
                      inputRange: [0, 1],
                      outputRange: [-offset.x, 0],
                    }),
                  },
                  {
                    translateY: progress.interpolate({
                      inputRange: [0, 1],
                      outputRange: [-offset.y, 0],
                    }),
                  },
                  { scale: progress },
                ],
              },
            ]}
          >
            <View style={[styles.optionInner, selected ? styles.selectedOption : null]}>
              {option.ui_id === "add_persona" ? (
                <PersonaAddAvatar selected={selected} size={ROCO_V1_PARITY.personaWheel.itemSize} />
              ) : (
                <AgentAvatarArt
                  selected={selected}
                  size={ROCO_V1_PARITY.personaWheel.itemSize}
                  variant={option.ui_id}
                />
              )}
              {selected ? <SelectionBadge /> : null}
            </View>
          </AnimatedPressable>
        );
      })}
    </View>
  );
}

function clamp(value: number, min: number, max: number) {
  return Math.min(Math.max(value, min), max);
}

const styles = StyleSheet.create({
  root: {
    ...StyleSheet.absoluteFillObject,
    elevation: 40,
    zIndex: 30,
  },
  backdrop: {
    ...StyleSheet.absoluteFillObject,
    backgroundColor: "rgba(17,17,17,0.16)",
    elevation: 41,
    zIndex: 1,
  },
  haloOuter: {
    alignItems: "center",
    backgroundColor: "transparent",
    borderColor: "rgba(23,23,23,0.80)",
    borderRadius: 999,
    borderWidth: 3,
    height: ROCO_V1_PARITY.personaWheel.haloOuterSize,
    justifyContent: "center",
    position: "absolute",
    shadowColor: rocoColors.ink,
    shadowOffset: { height: 8, width: 0 },
    shadowOpacity: 0.24,
    shadowRadius: 22,
    width: ROCO_V1_PARITY.personaWheel.haloOuterSize,
    elevation: 42,
    zIndex: 2,
  },
  haloInner: {
    borderColor: "rgba(247,207,69,0.95)",
    borderRadius: 999,
    borderWidth: 3,
    height: ROCO_V1_PARITY.personaWheel.haloSize,
    width: ROCO_V1_PARITY.personaWheel.haloSize,
  },
  option: {
    height: ROCO_V1_PARITY.personaWheel.itemSize,
    elevation: 43,
    position: "absolute",
    width: ROCO_V1_PARITY.personaWheel.itemSize,
    zIndex: 3,
  },
  optionInner: {
    borderRadius: 999,
    height: ROCO_V1_PARITY.personaWheel.itemSize,
    shadowColor: rocoColors.ink,
    shadowOffset: { height: 4, width: 0 },
    shadowOpacity: 0.24,
    shadowRadius: 12,
    width: ROCO_V1_PARITY.personaWheel.itemSize,
    elevation: 4,
  },
  selectedOption: {
    shadowColor: rocoColors.shellYellow,
    shadowOffset: { height: 6, width: 0 },
    shadowOpacity: 0.5,
    shadowRadius: 14,
    elevation: 6,
  },
});
