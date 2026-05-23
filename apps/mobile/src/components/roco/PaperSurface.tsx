import React, { ReactNode, useState } from "react";
import {
  Image,
  ImageBackground,
  LayoutChangeEvent,
  StyleSheet,
  View,
  type ImageSourcePropType,
} from "react-native";

import {
  ROCO_V1_PARITY,
  computePaperContentInset,
  rocoColors,
} from "../../roco/rocoTheme";

const paperShellSource: ImageSourcePropType = require("../../../assets/paper/paper_shell.png");
const paperOutlineSource: ImageSourcePropType = require("../../../assets/paper/paper_outline.png");

type PaperSurfaceProps = {
  children: ReactNode;
};

export function PaperSurface({ children }: PaperSurfaceProps) {
  const [paperSize, setPaperSize] = useState<{ width: number; height: number }>({
    width: ROCO_V1_PARITY.paper.sourceWidth,
    height: ROCO_V1_PARITY.paper.sourceHeight,
  });
  const insets = computePaperContentInset({
    rendered_width: paperSize.width,
    rendered_height: paperSize.height,
  });
  const contentInsets = {
    ...insets,
    top: Math.max(10, insets.top - 20),
  };

  function onLayout(event: LayoutChangeEvent) {
    const { width, height } = event.nativeEvent.layout;
    if (width > 0 && height > 0) {
      setPaperSize({ width, height });
    }
  }

  return (
    <View style={styles.shell}>
      <ImageBackground
        imageStyle={styles.paperImage}
        onLayout={onLayout}
        resizeMode={ROCO_V1_PARITY.paper.resizeMode}
        source={paperShellSource}
        style={styles.paper}
      >
        <View
          style={[
            styles.content,
            {
              paddingBottom: contentInsets.bottom,
              paddingLeft: contentInsets.left,
              paddingRight: contentInsets.right,
              paddingTop: contentInsets.top,
            },
          ]}
        >
          {children}
        </View>
        <View pointerEvents="none" style={styles.paperOutlineLayer}>
          <Image
            resizeMode={ROCO_V1_PARITY.paper.resizeMode}
            source={paperOutlineSource}
            style={styles.paperOutline}
          />
        </View>
      </ImageBackground>
    </View>
  );
}

const styles = StyleSheet.create({
  shell: {
    backgroundColor: rocoColors.shellYellow,
    flex: 1,
    paddingBottom: 10,
    paddingHorizontal: 10,
    paddingTop: 10,
  },
  paper: {
    flex: 1,
  },
  paperImage: {
    height: "100%",
    width: "100%",
  },
  content: {
    flex: 1,
    zIndex: 1,
  },
  paperOutline: {
    height: "100%",
    width: "100%",
  },
  paperOutlineLayer: {
    ...StyleSheet.absoluteFillObject,
    height: "100%",
    width: "100%",
    zIndex: 2,
  },
});
