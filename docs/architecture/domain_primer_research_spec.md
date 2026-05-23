# 洛克王国世界 PvP Domain Primer 调研执行规范

## Title

洛克王国世界 PvP 基础认知与对战党语境调研执行规范

## Purpose

本规范用于指导一个外部调研 Agent 产出一份可供后续产品、算法、Agent 与工程实现共同使用的 `Domain Primer`。该 Primer 的目标不是做玩家百科，而是让一个没有 `洛克王国世界` 对战背景的外部人类或 Agent 在阅读后，能够理解 PvP 分析系统所依赖的基本战斗认知、术语体系、队伍构成逻辑与环境认知边界。

## Executor / Intended User

执行者：具备网页检索能力的通用研究型 Agent。  
假设能力：

- 可访问互联网并检索中文网页
- 能区分事实、推断、争议信息
- 能阅读中文游戏 wiki、社区帖子、攻略、视频简介页、公告页
- 能输出结构化 Markdown 报告

执行者不应假设自己知道本项目的聊天上下文，也不应假设自己熟悉 `洛克王国世界` 与其他同名或近似游戏之间的差异。

## Scope

本规范要求完成以下内容：

1. 识别并说明 `洛克王国世界` PvP 的最小战斗框架
2. 解释属性、联防、换入、压制、队伍角色、队伍风格等核心概念
3. 归纳对战党常用术语与语境
4. 区分哪些知识是 Phase 1 属性联防分析所必需，哪些是后续 Phase 2 / Phase 3 才需要
5. 识别当前公开资料中哪些内容是稳定事实，哪些只是社区经验或推断
6. 给出一份能让后续工程或 Agent 直接引用的术语表与认知框架

## Non-goals

以下内容明确不在本次调研范围内：

- 不建立精灵数据库
- 不抓取或整理全量图鉴
- 不整理全量技能、特性、精灵数值明细
- 不做自动化爬虫实施方案
- 不直接设计最终评分函数或代码实现
- 不做完整环境使用率统计，除非公开资料中已有高可信摘要

## Definitions and Assumptions

### Definitions

- `Domain Primer`：面向后续产品与工程实现的领域入门文档，要求结构化、可引用、可交接，不等同于面向普通玩家的科普文章。
- `对战党`：在本规范中，指围绕 PvP 对战进行讨论、配队、分析、术语交流的玩家群体。
- `联防`：通过属性、耐久、换入关系与功能分工，使队伍成员互相覆盖弱点、承接威胁并维持防守与换人节奏的能力。
- `Phase 1`：仅基于属性关系进行队伍联防结构分析的系统阶段。
- `Phase 2`：引入精灵个体信息，如种族值、技能池、特性、功能招、速度档等，进行角色与队伍构成分析的系统阶段。
- `Phase 3`：引入环境信息，如常见队伍、流行精灵、使用率、针对关系、信息差等，进行环境上下文分析的系统阶段。

### Assumptions

1. 本调研对象是 `洛克王国世界`，不是经典 `洛克王国`。若资料混杂，必须明确标注并分离。
2. 公开资料可能不完整，尤其是 PvP 机制、meta 讨论、术语约定可能分散在 wiki、社区、视频与攻略中。
3. 如果某项 PvP 结论无法得到高可信公开证据，只能以“社区经验”或“待验证推断”表述，不得包装成事实。

## Inputs / Preconditions

### Mandatory Inputs

- 可用的互联网检索能力
- 可访问的中文网页浏览能力
- 能访问至少以下类型的数据源：
  - 官方公告、官方说明页、官方账号内容
  - `洛克王国世界` wiki 页面
  - 社区讨论页、攻略帖、问答帖
  - 视频平台页面中的文字简介、评论区高价值讨论、UP 主配文

### Optional Inputs

- 玩家编队示例
- 社区术语整理帖
- 实机对战演示或解说内容

### If Inputs Are Missing

- 若官方来源不足：允许使用社区高质量来源补充，但必须降低结论强度
- 若存在互相矛盾的说法：必须并列呈现冲突点，并说明当前无法定论
- 若 PvP 资料稀缺：应优先建立“可确认事实 + 明确未知项”框架，而不是为了完整性编造结论

## Workflow / Required Process

### Stage 1: Establish Game Boundary and Evidence Baseline

Objective:

确认研究对象、信息边界与证据等级，避免把其他游戏或旧版本规则混入结论。

Actions:

1. 确认 `洛克王国世界` 的对象范围与名称边界
2. 优先检索官方与 wiki 中关于对战、属性、精灵、队伍、玩法的基础信息
3. 建立来源分层：
   - Tier A：官方说明、官方公告、官方演示
   - Tier B：wiki 结构化页面
   - Tier C：社区高质量总结、攻略、配队分析
   - Tier D：零散讨论、评论区经验
4. 对每个关键结论标注来源等级

Intermediate Outputs:

- 研究对象定义
- 来源分层说明
- 初步可确认事实清单

Quality Criteria:

- 必须明确区分 `洛克王国世界` 与其他近似对象
- 不允许把低质量社区猜测直接当成事实基线

Good example:

- “属性克制关系可由 wiki 页面和结构化图鉴页交叉确认，因此可视为较高可信事实。”

Bad example:

- “玩家常说某队很强，因此可视为当前稳定 meta。”
  - 错误原因：把零散经验直接提升为环境事实，会污染后续系统建模。

### Stage 2: Build the PvP Minimum Mental Model

Objective:

提炼后续分析系统所需的最小 PvP 认知框架。

Actions:

1. 说明 PvP 分析到底在分析什么：
   - 属性克制
   - 换入承伤
   - 角色分工
   - 节奏
   - 队伍风格
   - 环境针对
2. 说明属性关系在对战中扮演什么角色
3. 说明为什么仅靠属性不足以解释完整战斗价值
4. 将 Phase 1 / Phase 2 / Phase 3 所需知识分层

Intermediate Outputs:

- 最小战斗认知框架
- 分层知识地图

Quality Criteria:

- 必须让无背景读者理解“属性分析只是整体分析的一层”
- 必须解释后续为何需要数值、技能、特性与环境信息

### Stage 3: Build a Battle Glossary

Objective:

产出一份后续系统可复用的术语表，减少歧义。

Actions:

1. 收集并定义核心术语
2. 对每个术语给出：
   - 简明定义
   - 所在语境
   - 对系统设计的意义
3. 优先覆盖以下术语簇：
   - 联防、抗性、弱点、换入、压制、check、counter
   - 主C、副C、收割、辅助、联防核心、受盾、输出位
   - 受队、平衡、对攻、换转、展开、针对、信息差

Intermediate Outputs:

- 术语表

Quality Criteria:

- 定义必须简洁、可工程化引用
- 不要把多个近义词混成一团不加区分

Good example:

- “联防：队伍通过抗性、耐久与功能互补，分担关键威胁换入压力的能力。”

Bad example:

- “联防就是比较肉、能扛。”
  - 错误原因：定义过于粗糙，无法支持后续系统建模。

### Stage 4: Identify Team-Building Logic and Tactical Archetypes

Objective:

整理对战党如何理解队伍构成，以及这些理解如何映射到系统能力。

Actions:

1. 归纳常见队伍思路和风格
2. 对每种风格说明：
   - 核心目标
   - 典型构成
   - 常见优点
   - 常见弱点
3. 区分“理论定义”和“社区常用口语定义”

Intermediate Outputs:

- 队伍风格摘要
- 战术认知框架

Quality Criteria:

- 至少覆盖受队、平衡、对攻/高速换命、换转/节奏型、展开型
- 明确哪些只是经验性概括，哪些有较清晰共识

### Stage 5: Translate Findings into System-Relevant Guidance

Objective:

将领域知识转写成后续产品与工程可直接使用的设计输入。

Actions:

1. 总结 Phase 1 系统必须理解的概念
2. 总结 Phase 2 才必须引入的精灵级信息
3. 总结 Phase 3 才必须引入的环境级信息
4. 列出当前公开资料不足、需要后续人工确认或持续跟踪的空白点

Intermediate Outputs:

- 建模映射清单
- 后续研究空白清单

Quality Criteria:

- 必须清楚回答“为什么现在先做属性联防分析是合理的”
- 必须清楚回答“为什么后面一定会需要种族值、技能池、特性与环境数据”

## Tool / Resource Policy

### Web Search

- 必须使用，用于获取当前可用公开信息
- 不得只依赖搜索摘要，必须打开页面核验
- 对关键结论至少交叉验证两类来源

### Source Priority

优先级从高到低：

1. 官方说明与官方演示
2. wiki 结构化页面
3. 高质量社区分析
4. 零散玩家讨论

若低优先级来源与高优先级来源冲突，默认以高优先级来源为准，并在报告中注明冲突。

### Evidence Handling

- 每条重要结论必须标注来源
- 若为推断，必须明确标注为 `推断`
- 若存在争议，必须明确标注为 `争议`

### Out-of-Scope Resource Use

- 不需要自行编写爬虫
- 不需要下载大规模数据集
- 不需要生成图像或可视化资产，除非文本解释必须依赖图示

## Output Contract

执行者必须输出一份 Markdown 报告，标题固定为：

`洛克王国世界 PvP Domain Primer`

报告必须包含以下固定章节，禁止随意改名：

1. `Overview`
2. `Game Boundary`
3. `Evidence Model`
4. `PvP Minimum Mental Model`
5. `Attribute and Defensive Core Concepts`
6. `Team Roles and Tactical Archetypes`
7. `Glossary`
8. `What Phase 1 Needs`
9. `What Phase 2 Needs`
10. `What Phase 3 Needs`
11. `Open Questions and Unverified Areas`
12. `Source Inventory`

### Required Content Rules

- `Overview`：用 5 到 10 句话总结报告结论
- `Game Boundary`：说明对象范围，明确与其他近似对象区分
- `Evidence Model`：解释来源等级与可信度处理方式
- `Glossary`：至少 15 个术语
- `Source Inventory`：至少 10 个来源，其中至少：
  - 2 个较高可信来源
  - 3 个 wiki 或结构化来源
  - 3 个社区或攻略来源
- `Open Questions and Unverified Areas`：至少列 5 条未完全确认的点或资料空白

### Citation Rules

- 每个核心小节至少带来源引用
- 引用格式统一使用 Markdown 链接
- 不得只给站点名，不给具体 URL

### Fact / Interpretation / Assumption Separation

报告中必须显式区分：

- `事实`
- `推断`
- `争议/未确认`

推荐写法：

- `事实：...`
- `推断：...`
- `争议：...`

## Quality Bar / Success Criteria

本次调研结果可接受的标准为：

- 一个没有该游戏 PvP 背景的工程师或 Agent 能读懂报告
- 报告能支撑后续 Phase 1 到 Phase 3 的系统分层理解
- 术语表足够稳定，后续可直接引用
- 关键结论都有来源支撑或明确的不确定性标记
- 不把社区经验包装成官方事实
- 能清楚解释“属性联防分析为什么是合理的第一步”

## Failure Modes and Recovery

### External Failures

- 若官方资料稀缺：
  - 使用 wiki 与高质量社区资料补充
  - 明确降低结论强度
- 若搜索结果高度碎片化：
  - 先构建事实框架，再填补例证
- 若页面无法访问：
  - 更换来源，不要依赖单点页面

### Judgement Dilemmas

- 若某术语在不同社区语境下含义不同：
  - 并列给出差异，并说明本项目后续建议采用的较稳定义
- 若某队伍风格分类边界模糊：
  - 允许使用“偏向于”或“混合型”表述
  - 不要强行一刀切

### Structural Failures

- 如果报告写成普通玩家科普而无法服务系统建模：
  - 视为失败，必须重写
- 如果报告只堆来源、不提炼认知框架：
  - 视为失败，必须补齐结构化结论

## Escalation / Handoff Rules

在以下情况下，执行者应停止继续扩展并明确报告问题：

- 无法区分 `洛克王国世界` 与其他相近对象的资料边界
- 关键 PvP 认知只能找到零散主观讨论，无法形成最小共识
- 来源之间存在重大冲突，且无法确定优先级

若调研已完成主体但仍存在上述问题，应返回部分完成结果，并在 `Open Questions and Unverified Areas` 中集中说明。

## Evaluation Checklist

- 是否明确界定了研究对象边界？
- 是否解释了 PvP 分析系统依赖的最小认知框架？
- 是否把 Phase 1 / 2 / 3 所需知识分层？
- 是否给出了至少 15 个可复用术语？
- 是否清楚区分事实、推断与争议？
- 是否至少提供了 10 个具体来源链接？
- 是否列出了至少 5 个未确认或待补充的问题？
- 是否让一个无背景执行者读完后能知道后续系统为什么要分阶段建设？
