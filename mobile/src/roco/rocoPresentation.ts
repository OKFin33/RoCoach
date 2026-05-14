import type { AgentResponse, AnalysisType } from "../api/types";
import type { RocoAnalysisCardModel } from "./rocoTheme";

export function resolveVisibleReply(response: AgentResponse): string {
  if (response.analysis_type === "runtime_failure" || response.status === "failed") {
    return runtimeFailureReply(response);
  }

  return chatBubbleReply(response);
}

export function buildAnalysisCardModel(response: AgentResponse): RocoAnalysisCardModel | null {
  // V1 chat temporarily hides analysis cards. Raw evidence, confidence notes,
  // and tool traces made the main chat feel like internal telemetry instead of
  // a product reply; keep the contract type but do not surface it in UI.
  return null;
}

export function titleForAnalysisType(analysisType: AnalysisType): string {
  switch (analysisType) {
    case "chat_response":
      return "Roco 回复";
    case "team_analysis":
      return "分析摘要";
    case "species_analysis":
      return "精灵判断";
    default:
      return "Roco 摘要";
  }
}

function runtimeFailureReply(response: AgentResponse): string {
  const answer = response.answer.trim();
  if (answer.includes("missing") || answer.includes("not configured") || answer.includes("Provider key")) {
    return "模型服务还没配置完整。打开右侧设置 → API 设置，填写 Provider API key、Provider base URL 和 Model，保存后先点“测试模型服务”。";
  }
  return "模型服务调用失败。打开右侧设置 → API 设置，先点“测试模型服务”；如果测试失败，请检查 API key、base URL、模型名和思考模式配置。";
}

function chatBubbleReply(response: AgentResponse): string {
  const personaAnswer = response.persona?.rendered_answer?.trim();
  const candidate =
    personaAnswer &&
    response.persona?.public_safe === true &&
    response.persona.facts_locked === true &&
    response.persona.fact_policy === "persona_may_not_alter_facts"
      ? personaAnswer
      : response.presentation?.reply ?? response.answer;

  const compacted = compactInternalReply(candidate, response.analysis_type);
  return compacted || candidate.trim();
}

function compactInternalReply(reply: string, analysisType: AnalysisType): string {
  let text = stripInternalPrefixes(reply.trim());
  text = stripInternalTails(text);
  text = stripSoftwareMeta(text);

  if (analysisType === "team_analysis") {
    const partialTeamReply = partialTeamBubbleReply(text);
    if (partialTeamReply) {
      return partialTeamReply;
    }
  }

  return normalizeWhitespace(text);
}

function partialTeamBubbleReply(text: string): string | null {
  const slotMatch = text.match(/当前只识别到\s*(\d+)\s*个队伍槽位/);
  if (!slotMatch) {
    return null;
  }

  const speciesMatch = text.match(/已读取队伍成员：([^。]+)。/);
  const species = speciesMatch?.[1]?.trim();
  const slotCount = slotMatch[1];

  if (species) {
    return `${species} 现在只能按已填的 ${slotCount} 个槽位做初判：它更像待定功能位，是否能当主轴、补洞位或联防位，要等你补齐队友和技能后再定。`;
  }

  return `我现在只看到 ${slotCount} 个队伍槽位，所以只能做初步判断；补齐队友和技能后，才能给出可靠的完整队伍结论。`;
}

function stripInternalPrefixes(text: string): string {
  return text
    .replace(/^答复（暂定）：/, "")
    .replace(/^答复：/, "")
    .replace(/^硬结论：/, "")
    .replace(/^暂定判断：/, "")
    .replace(/^You know who｜收口结论\s*/i, "")
    .replace(/^主答复：/, "")
    .trim();
}

function stripInternalTails(text: string): string {
  return text
    .replace(/先收束真实瓶颈，不要把装饰性选项当成解法。?/g, "")
    .replace(/结论必须保持 grounded，不要把解释伪装成新事实。?/g, "")
    .replace(/角色判断要围绕主职能收束，不要把边角能力抬成主定位。?/g, "")
    .trim();
}

function normalizeWhitespace(text: string): string {
  return text.replace(/\s+/g, " ").trim();
}

function stripSoftwareMeta(text: string): string {
  return text
    .replace(/Partial team context remains visible; the judgment only covers the supplied slots\.?/gi, "目前只看到了部分队伍槽位。")
    .replace(/The requested scope remains unsupported by the current product boundary\.?/gi, "这个问题现在还不能可靠回答。")
    .replace(/\bgrounded\b/gi, "可靠")
    .replace(/\bprovisional\b/gi, "初步")
    .replace(/\bconfidence\b/gi, "把握")
    .replace(/\bbackend\b/gi, "")
    .replace(/\bruntime\b/gi, "")
    .replace(/\bdoctrine\b/gi, "")
    .replace(/\btool(?:s)?\b/gi, "")
    .replace(/\bevidence\b/gi, "依据")
    .replace(/\bpartial-team\b/gi, "部分队伍")
    .replace(/\bproduct boundary\b/gi, "当前限制")
    .replace(/ev_\d+\s*\|\s*[^。；\n]+/g, "")
    .replace(/^[^\n：:]*\|\s*(confirmed|provisional|low_confidence|insufficient_evidence)\s*\|.*$/gim, "")
    .replace(/^\s*(分析基底|证据|置信说明|工具轨迹|后续建议)\s*$/gim, "")
    .trim();
}
