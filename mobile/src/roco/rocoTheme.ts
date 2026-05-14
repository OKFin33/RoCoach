export type RocoPersonaUiId = "you_know_who" | "ai_assistant" | "add_persona";

export type BackendBuiltInPersonaId =
  | "you_know_who"
  | "lattice_support_coach";

export type PersonaSelector =
  | {
      kind: "built_in";
      persona_id: BackendBuiltInPersonaId;
    }
  | {
      kind: "managed";
      persona_id: string;
      version: string;
      revision: number;
    };

export type RocoMessageRole = "user" | "agent";
export type RocoMessageStatus = "sent" | "thinking" | "failed";
export type RocoMessageKind = "text" | "analysis";

export type RocoVisibleWarning = {
  code: string;
  severity: "high" | "medium" | "low";
  message: string;
};

export type RocoAnalysisSection = {
  id: string;
  label: string;
  content: string;
  default_expanded: boolean;
  content_kind:
    | "evidence"
    | "confidence"
    | "tool_trace"
    | "analytical_base"
    | "followup"
    | "raw";
};

export type RocoAnalysisCardModel = {
  title: string;
  summary?: string;
  warnings: RocoVisibleWarning[];
  sections: RocoAnalysisSection[];
  followup_prompts: string[];
};

export type RocoMessageError = {
  code: "network_error" | "model_error" | "api_error" | "unknown";
  user_message: string;
  retryable: boolean;
};

export type RocoChatMessage = {
  id: string;
  role: RocoMessageRole;
  status: RocoMessageStatus;
  kind: RocoMessageKind;
  text: string;
  created_at?: string;
  persona_ui_id?: RocoPersonaUiId | null;
  analysis_card?: RocoAnalysisCardModel | null;
  error?: RocoMessageError | null;
};

export type RocoInsets = {
  top: number;
  right: number;
  bottom: number;
  left: number;
};

export type RocoPoint = {
  x: number;
  y: number;
};

export type RocoRect = {
  left: number;
  top: number;
  right: number;
  bottom: number;
  width: number;
  height: number;
};

export type RocoMessageAction =
  | "copy"
  | "rewrite"
  | "delete"
  | "confirm_delete"
  | "cancel_delete"
  | "regenerate";

export type RocoMessageActionAvailability = {
  message_id: string;
  actions: RocoMessageAction[];
  disabled_actions?: Partial<Record<RocoMessageAction, string>>;
};

export type RocoPersonaWheelState =
  | { status: "closed" }
  | {
      status: "open";
      anchor: RocoPoint;
      highlighted_id: RocoPersonaUiId | null;
    };

export type RocoMessageActionMenuState =
  | { status: "closed" }
  | {
      status: "open";
      message_id: string;
      role: RocoMessageRole;
      can_rewrite: boolean;
      confirm_delete: boolean;
      anchor: RocoPoint;
    };

export const ROCO_V1_ASSETS = {
  paperShell: "assets/paper/paper_shell.png",
  paperOutline: "assets/paper/paper_outline.png",
  paperFrameReferenceOnly: "assets/paper/paper_frame.svg",
  avatars: {
    youKnowWho: "assets/avatars/agent_you_know_who.svg",
    aiAssistant: "assets/avatars/agent_ai_assistant.svg",
    addPersona: "assets/avatars/persona_add.svg",
    userDefault: "assets/avatars/user_default.svg",
  },
} as const;

export const ROCO_V1_COPY = {
  composerPlaceholder: "问问 Roco...",
  emptyInvite: "向 Roco 提问队伍策略、精灵搭配，或对战技巧",
  emptyPromptChips: [
    "这套队伍先手够用吗？",
    "推荐我几只穿透系精灵",
    "对战火系队有没有克制？",
  ],
  apiKeySecurityTitle: "API 密钥安全提示",
  apiKeySecurityBody:
    "填写 API Key 后，Roco 会通过你配置的模型服务生成回复。密钥只保存在本机安全存储中，不会进入聊天内容、日志或人格资料。",
  secureStoreUnavailable: "SecureStore 不可用时，不保存密钥。",
  retryError: "连接或模型请求失败。",
} as const;

export const ROCO_V1_PARITY = {
  paper: {
    sourceWidth: 915,
    sourceHeight: 1616,
    sourceInset: {
      top: 72,
      right: 52,
      bottom: 58,
      left: 52,
    },
    minInset: {
      top: 30,
      right: 20,
      bottom: 24,
      left: 20,
    },
    resizeMode: "stretch",
  },
  messageStack: {
    gap: 16,
    horizontalPadding: 8,
    topPadding: 10,
  },
  messageRow: {
    maxWidthPercent: 0.88,
    avatarGap: 8,
    agentAvatarSize: 38,
    userAvatarSize: 38,
    agentCardLaneOffset: 46,
    bubblePaddingHorizontal: 14,
    bubblePaddingVertical: 10,
    bubbleBorderWidth: 2.6,
    bubbleRadius: {
      large: 17,
      tailCorner: 6,
    },
    bubbleTail: {
      width: 11,
      height: 12,
      bottom: 9,
    },
    text: {
      fontSize: 15,
      lineHeight: 23,
    },
  },
  composer: {
    outerPaddingHorizontal: 14,
    outerPaddingBottom: 7,
    rowGap: 9,
    inputBorderWidth: 2.5,
    inputRadius: 22,
    inputPaddingHorizontal: 14,
    inputPaddingVertical: 8,
    inputMinHeight: 44,
    inputMaxTextHeight: 100,
    inputFontSize: 15,
    inputLineHeight: 22,
    sendButtonSize: 44,
  },
  emptyState: {
    paddingHorizontal: 24,
    paddingVertical: 32,
    gap: 20,
    avatarSize: 72,
    inviteMaxWidth: 200,
    inviteFontSize: 14.5,
    promptChipGap: 9,
  },
  personaWheel: {
    longPressMs: 430,
    radius: 86,
    itemSize: 52,
    haloSize: 86,
    haloOuterSize: 92,
    selectionBadgeSize: 16,
    highlightDistance: 46,
    backdropFadeMs: 180,
    haloScaleMs: 160,
    optionStaggerMs: 50,
    optionSpringStiffness: 380,
    optionSpringDamping: 26,
    positions: [
      { ui_id: "you_know_who", angle: -42 },
      { ui_id: "ai_assistant", angle: 8 },
      { ui_id: "add_persona", angle: 58 },
    ],
  },
  drawer: {
    widthRatio: 0.88,
    dragThreshold: 34,
    handle: {
      width: 22,
      height: 58,
      leftOffset: -22,
      borderWidth: 3,
      radius: 12,
      gripDotSize: 4,
      gripGap: 4,
    },
  },
  messageActionMenu: {
    backdrop: "rgba(17,17,17,0.08)",
    userXOffset: 192,
    yOffset: 48,
    clampLeft: 12,
    clampTop: 20,
    clampRightMenuWidth: 212,
    clampBottomMenuHeight: 66,
    borderWidth: 2.5,
    radius: 14,
    padding: 6,
    gap: 4,
    buttonMinWidth: 54,
    confirmDeleteMinWidth: 78,
    buttonHeight: 34,
    buttonRadius: 9,
    buttonGap: 5,
    buttonFontSize: 12.5,
    buttonFontWeight: "800",
  },
  analysisCard: {
    borderWidth: 2.5,
    radius: 12,
    topMargin: 16,
    headerPaddingHorizontal: 12,
    headerPaddingVertical: 9,
    headerGap: 8,
    headerBorderBottomWidth: 2,
    headerIconSize: 28,
    headerIconRadius: 6,
    titleFontSize: 15,
    titleFontWeight: "800",
    bodyPaddingHorizontal: 12,
    bodyPaddingVertical: 10,
    rowGap: 10,
    rowPaddingTop: 9,
    rowPaddingBottom: 9,
    rowTitleFontSize: 13,
    rowTitleFontWeight: "700",
    rowBodyFontSize: 12.5,
    rowBodyLineHeightMultiplier: 1.5,
  },
} as const;

export const rocoColors = {
  shellYellow: "#F6D246",
  shellYellowDeep: "#E8BE26",
  paper: "#FFF9EB",
  composerPaper: "#FFF8E8",
  ink: "#171717",
  inkSoft: "#3A3427",
  muted: "#8A8070",
  agentBubble: "#FFF9EA",
  userBubbleTop: "#F9D84D",
  userBubbleBottom: "#F5C93A",
  cardHeader: "#F7CF45",
  cardBody: "#FFF8E8",
  danger: "#B83A4B",
  warning: "#E59A2D",
  info: "#4B8FD8",
  divider: "rgba(23,23,23,0.10)",
  disabledFill: "rgba(23,23,23,0.25)",
} as const;

export const PUBLIC_ANALYSIS_SECTION_KINDS: ReadonlySet<
  RocoAnalysisSection["content_kind"]
> = new Set(["evidence", "confidence", "analytical_base", "followup"]);

export function computePaperContentInset(params: {
  rendered_width: number;
  rendered_height: number;
}): RocoInsets {
  const { paper } = ROCO_V1_PARITY;
  const xScale = params.rendered_width / paper.sourceWidth;
  const yScale = params.rendered_height / paper.sourceHeight;

  return {
    top: Math.max(paper.minInset.top, Math.round(paper.sourceInset.top * yScale)),
    right: Math.max(paper.minInset.right, Math.round(paper.sourceInset.right * xScale)),
    bottom: Math.max(paper.minInset.bottom, Math.round(paper.sourceInset.bottom * yScale)),
    left: Math.max(paper.minInset.left, Math.round(paper.sourceInset.left * xScale)),
  };
}

export function computePersonaWheelOffset(angle: number): RocoPoint {
  const radians = (angle * Math.PI) / 180;
  return {
    x: Math.cos(radians) * ROCO_V1_PARITY.personaWheel.radius,
    y: Math.sin(radians) * ROCO_V1_PARITY.personaWheel.radius,
  };
}

export function personaWheelOffsets(): Array<{
  ui_id: RocoPersonaUiId;
  x: number;
  y: number;
}> {
  return ROCO_V1_PARITY.personaWheel.positions.map((position) => ({
    ui_id: position.ui_id as RocoPersonaUiId,
    ...computePersonaWheelOffset(position.angle),
  }));
}

export function computeMessageActionMenuPosition(params: {
  role: RocoMessageRole;
  bubble_rect_in_root: RocoRect;
  root_width: number;
  root_height: number;
}): RocoPoint {
  const { messageActionMenu } = ROCO_V1_PARITY;
  const menuX =
    params.role === "user"
      ? params.bubble_rect_in_root.right - messageActionMenu.userXOffset
      : params.bubble_rect_in_root.left;
  const menuY = params.bubble_rect_in_root.top - messageActionMenu.yOffset;

  return {
    x: clamp(
      menuX,
      messageActionMenu.clampLeft,
      params.root_width - messageActionMenu.clampRightMenuWidth,
    ),
    y: clamp(
      menuY,
      messageActionMenu.clampTop,
      params.root_height - messageActionMenu.clampBottomMenuHeight,
    ),
  };
}

export function actionsForMessage(params: {
  message: RocoChatMessage;
  latest_user_message_id: string | null;
  regenerate_available: boolean;
}): RocoMessageActionAvailability {
  const { message, latest_user_message_id, regenerate_available } = params;
  if (message.role === "user") {
    const actions: RocoMessageAction[] = ["copy"];
    if (message.id === latest_user_message_id) {
      actions.push("rewrite");
    }
    actions.push("delete");
    return { message_id: message.id, actions };
  }

  return {
    message_id: message.id,
    actions: ["copy", "regenerate", "delete"],
    disabled_actions: regenerate_available
      ? undefined
      : {
          regenerate: "后端暂未提供重新生成接口",
        },
  };
}

function clamp(value: number, min: number, max: number): number {
  return Math.min(Math.max(value, min), max);
}
