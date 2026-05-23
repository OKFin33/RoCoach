import React from "react";
import Svg, { Circle, Path, Rect } from "react-native-svg";

import { rocoColors } from "../../roco/rocoTheme";

type IconProps = {
  color?: string;
  size?: number;
  strokeWidth?: number;
};

export function SendIcon({ color = rocoColors.shellYellow, size = 22, strokeWidth = 2.4 }: IconProps) {
  return (
    <Svg height={size} viewBox="0 0 24 24" width={size}>
      <Path
        d="M4 12 L20 4 L15 20 L11 13 L4 12Z"
        fill="none"
        stroke={color}
        strokeLinejoin="round"
        strokeWidth={strokeWidth}
      />
      <Path d="M11 13 L20 4" stroke={color} strokeLinecap="round" strokeWidth={strokeWidth} />
    </Svg>
  );
}

export function CopyIcon({ color = rocoColors.ink, size = 16, strokeWidth = 2.2 }: IconProps) {
  return (
    <Svg height={size} viewBox="0 0 24 24" width={size}>
      <Rect fill="none" height="12" rx="2.5" stroke={color} strokeWidth={strokeWidth} width="12" x="8" y="8" />
      <Path d="M5 15 H4 A2 2 0 0 1 2 13 V4 A2 2 0 0 1 4 2 H13 A2 2 0 0 1 15 4 V5" fill="none" stroke={color} strokeLinecap="round" strokeWidth={strokeWidth} />
    </Svg>
  );
}

export function RewriteIcon({ color = rocoColors.ink, size = 16, strokeWidth = 2.2 }: IconProps) {
  return (
    <Svg height={size} viewBox="0 0 24 24" width={size}>
      <Path d="M4 20 H20" stroke={color} strokeLinecap="round" strokeWidth={strokeWidth} />
      <Path d="M6 16 L16.5 5.5 L19 8 L8.5 18.5 H6 V16Z" fill="none" stroke={color} strokeLinejoin="round" strokeWidth={strokeWidth} />
    </Svg>
  );
}

export function RegenerateIcon({ color = rocoColors.ink, size = 16, strokeWidth = 2.2 }: IconProps) {
  return (
    <Svg height={size} viewBox="0 0 24 24" width={size}>
      <Path d="M18.5 9 A7 7 0 0 0 6 6.5 L4 9" fill="none" stroke={color} strokeLinecap="round" strokeLinejoin="round" strokeWidth={strokeWidth} />
      <Path d="M4 4 V9 H9" fill="none" stroke={color} strokeLinecap="round" strokeLinejoin="round" strokeWidth={strokeWidth} />
      <Path d="M5.5 15 A7 7 0 0 0 18 17.5 L20 15" fill="none" stroke={color} strokeLinecap="round" strokeLinejoin="round" strokeWidth={strokeWidth} />
      <Path d="M20 20 V15 H15" fill="none" stroke={color} strokeLinecap="round" strokeLinejoin="round" strokeWidth={strokeWidth} />
    </Svg>
  );
}

export function DeleteIcon({ color = rocoColors.danger, size = 16, strokeWidth = 2.2 }: IconProps) {
  return (
    <Svg height={size} viewBox="0 0 24 24" width={size}>
      <Path d="M4 7 H20" stroke={color} strokeLinecap="round" strokeWidth={strokeWidth} />
      <Path d="M9 7 V5 H15 V7" fill="none" stroke={color} strokeLinejoin="round" strokeWidth={strokeWidth} />
      <Path d="M7 7 L8 20 H16 L17 7" fill="none" stroke={color} strokeLinejoin="round" strokeWidth={strokeWidth} />
      <Path d="M10 11 V16 M14 11 V16" stroke={color} strokeLinecap="round" strokeWidth={strokeWidth} />
    </Svg>
  );
}

export function CheckIcon({ color = rocoColors.ink, size = 14, strokeWidth = 2.5 }: IconProps) {
  return (
    <Svg height={size} viewBox="0 0 24 24" width={size}>
      <Path d="M5 12.5 L10 17.5 L19 6.5" fill="none" stroke={color} strokeLinecap="round" strokeLinejoin="round" strokeWidth={strokeWidth} />
    </Svg>
  );
}

export function XIcon({ color = rocoColors.ink, size = 16, strokeWidth = 2.4 }: IconProps) {
  return (
    <Svg height={size} viewBox="0 0 24 24" width={size}>
      <Path d="M7 7 L17 17 M17 7 L7 17" stroke={color} strokeLinecap="round" strokeWidth={strokeWidth} />
    </Svg>
  );
}

export function WarningIcon({ color = rocoColors.warning, size = 18, strokeWidth = 2.2 }: IconProps) {
  return (
    <Svg height={size} viewBox="0 0 24 24" width={size}>
      <Path d="M12 3 L22 20 H2 L12 3Z" fill="none" stroke={color} strokeLinejoin="round" strokeWidth={strokeWidth} />
      <Path d="M12 9 V13" stroke={color} strokeLinecap="round" strokeWidth={strokeWidth} />
      <Circle cx="12" cy="17" fill={color} r="1.3" />
    </Svg>
  );
}

export function EyeIcon({ color = rocoColors.ink, size = 16, strokeWidth = 2.2 }: IconProps) {
  return (
    <Svg height={size} viewBox="0 0 24 24" width={size}>
      <Path d="M3 12 C5.5 7.5 8.5 5.5 12 5.5 C15.5 5.5 18.5 7.5 21 12 C18.5 16.5 15.5 18.5 12 18.5 C8.5 18.5 5.5 16.5 3 12Z" fill="none" stroke={color} strokeLinejoin="round" strokeWidth={strokeWidth} />
      <Circle cx="12" cy="12" fill="none" r="3" stroke={color} strokeWidth={strokeWidth} />
    </Svg>
  );
}
