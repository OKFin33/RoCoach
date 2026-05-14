import React from "react";
import Svg, { Circle, Path } from "react-native-svg";

import { ROCO_V1_PARITY, rocoColors } from "../../roco/rocoTheme";

export function UserAvatar({ size = ROCO_V1_PARITY.messageRow.userAvatarSize }: { size?: number }) {
  return (
    <Svg height={size} viewBox="0 0 96 96" width={size}>
      <Circle cx="48" cy="48" fill="#F7D957" r="44" stroke={rocoColors.ink} strokeWidth="5" />
      <Circle cx="48" cy="43" fill="#FFE3A2" r="24" stroke={rocoColors.ink} strokeWidth="4" />
      <Path d="M27 37 C34 22 53 16 69 31 C64 27 55 28 50 34 C43 28 33 29 27 37Z" fill="#6A4B2D" />
      <Path d="M32 22 C42 10 61 13 67 29 C57 22 44 21 32 22Z" fill="#7A42C7" stroke={rocoColors.ink} strokeWidth="4" />
      <Circle cx="39" cy="46" fill={rocoColors.ink} r="3" />
      <Circle cx="57" cy="46" fill={rocoColors.ink} r="3" />
      <Path d="M40 57 C45 61 52 61 57 57" stroke={rocoColors.ink} strokeLinecap="round" strokeWidth="3" />
    </Svg>
  );
}
