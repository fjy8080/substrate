# Agent Managed Delivery 状态机与门禁

本文是 `agent-managed-delivery` 的正式状态机定义。主 Agent、子 Agent 和
`scripts/workflowctl.py` 都必须遵守本文，不得用 Review 结论、CI 绿灯或一般性授权
绕过任务范围。

## 一、核心原则

1. **WBS 决定做什么**：任务的独立输出、验收标准和测试要求定义实现边界。
2. **权威文档决定怎么做**：契约、架构、API、DDL 和安全文档约束实现方式，但引用整章
   文档不等于获得实现整章能力的授权。
3. **相邻 WBS 定义排除项**：前置、后续和并列任务已明确承接的能力，不得夹带到当前
   任务。
4. **发现真实不等于属于当前任务**：Reviewer 发现必须由主 Agent 复现、映射 WBS 并
   分类；只有 `IN_SCOPE_DEFECT` 且符合本轮严重度阈值时才可进入当前修复循环。
5. **范围变更必须由用户明确批准**：监督模式和委托批次模式都不能自行扩大范围、重写
   WBS 或重新设计重大契约。
6. **HEAD 证据与范围证据分离**：新 HEAD 会使测试、文档、CI、Review 和合并授权失效，
   但不会自动改变已批准的任务范围。
7. **PR 元数据属于 HEAD 门禁**：仓库若用 PR 正文中的动态字段校验 base、提交数、文件数
   或 HEAD，每次 PR 创建、Push、rebase、update branch 或基线统计变化后都必须重新同步并
   回读；不得把机械元数据失败留给 CI 再补救。
8. **Review 必须收敛**：每个发现同时记录 WBS 分类与 `P0`-`P4` 严重度；同一任务/PR
   的轮次跨 HEAD、Reviewer 和范围修订单调累计。第 1-3 轮按现有规则修复当前范围缺陷；
   第 4 轮起只有 `P0/P1` 可以阻塞或进入修复队列，P2-P4 只留作非阻塞观察。

## 二、公开状态总图

```text
CANDIDATE
  -> CLAIMED
  -> EXPLORING
       -> DEVELOPING
       -> SCOPE_BLOCKED

DEVELOPING
  -> SELF_TESTING
  -> SCOPE_BLOCKED

SELF_TESTING
  -> IMPLEMENTATION_READY_FOR_DOCS
  -> DEVELOPING
  -> SCOPE_BLOCKED

IMPLEMENTATION_READY_FOR_DOCS
  -> DOCUMENTING
  -> DEVELOPING
  -> SCOPE_BLOCKED

DOCUMENTING
  -> PR_CREATING
  -> DEVELOPING
  -> SCOPE_BLOCKED

PR_CREATING
  -> CI_PENDING
  -> DEVELOPING
  -> SCOPE_BLOCKED

CI_PENDING
  -> REVIEW_REQUESTED
  -> FIXING_CI
  -> DEVELOPING
  -> SCOPE_BLOCKED

FIXING_CI
  -> SELF_TESTING
  -> SCOPE_BLOCKED

REVIEW_REQUESTED
  -> REVIEWING
  -> DEVELOPING
  -> SCOPE_BLOCKED

REVIEWING
  -> FIXING_REVIEW
  -> MERGE_READY
  -> DEVELOPING
  -> SCOPE_BLOCKED

FIXING_REVIEW
  -> SELF_TESTING
  -> SCOPE_BLOCKED

MERGE_READY
  -> MERGING
  -> REVIEWING
  -> DEVELOPING
  -> SCOPE_BLOCKED

MERGING
  -> MERGED

MERGED
  -> VERIFYING_DEVELOP

VERIFYING_DEVELOP
  -> POST_MERGE_MEMORY

POST_MERGE_MEMORY
  -> COMPLETED

SCOPE_BLOCKED
  --用户明确决定并记录 scope-change--> EXPLORING
  --长期无法解决--> SERIOUSLY_BLOCKED

任意非终态
  --有证据的外部永久阻塞--> SERIOUSLY_BLOCKED
```

`COMPLETED` 与 `SERIOUSLY_BLOCKED` 是终态。`SCOPE_BLOCKED` 不是终态，它专门用于
等待用户处理 WBS、依赖或范围决策。

## 三、任务范围契约

### 3.1 记录时点

在 `EXPLORING -> DEVELOPING` 前，主 Agent 必须使用 `scope-record` 记录范围契约并
执行一次 exact-HEAD `scope-check PASS`。范围契约至少包含：

- WBS 权威来源；
- 独立输出；
- 验收标准；
- 测试要求；
- 权威输入；
- 明确包含的能力；
- 明确排除的能力；
- 前置任务及实时状态；
- 允许修改的仓库路径模式；
- 形成范围判断的证据。

缺少上述任一核心字段时不得进入 `DEVELOPING`。

### 3.2 路径与能力双重检查

`scope-check` 以领取任务时的基线 HEAD 与当前 HEAD 比较文件路径：

- 所有变更路径都匹配 `allowed_paths` 才能记录 `PASS`；
- 出现范围外路径时只能记录 `BLOCKED` 或先进入 `SCOPE_BLOCKED`；
- 不能为了让检查通过而自行扩展 `allowed_paths`；
- 文件路径仍在范围内但能力已经扩张时，主 Agent 必须在证据中记录能力漂移，并按
  本文第五节分诊。

以下信号触发增强范围审计，但不是简单的自动失败阈值：

- 第二轮及以后出现与上一轮无关的新问题类型；
- 新增初始范围外的生产模块或共享基础设施；
- 引入新的全局抽象、状态机、事务模型或 Provider 生命周期机制；
- 修复开始修改前置/后续 WBS 的核心所有权代码；
- 累计差异相对首次 Review 明显扩大；
- Reviewer 要求完成尚未合入的依赖能力。

增强审计必须说明新发现是上一轮修复的回归、此前遗漏的当前任务缺陷，还是跨任务问题。

### 3.3 范围变更

只有 `SCOPE_BLOCKED` 状态允许执行 `scope-change`。该命令必须记录用户明确批准证据，
范围修订号递增，并回到 `EXPLORING`。范围变更会使当前测试、文档、任务报告、PR HEAD
绑定、CI、Review 和合并授权全部失效；已有 PR 的身份可以保留，但必须重新验证新范围。

委托批次授权不包含范围变更权。即使处于 `DELEGATED_BATCH`，也必须等待用户本人明确
决定。

对于升级前已经在途、尚无范围契约的旧运行状态，必须先进入 `SCOPE_BLOCKED`。用户批准
后，`scope-change` 可采用 revision 1，但必须显式提供原始任务基线的完整 commit SHA，
且控制器验证该提交是当前 HEAD 的祖先。禁止使用当前 HEAD 伪造空历史差异。已有范围
契约的任务不得更换原始基线。

## 四、各状态职责与进入门禁

### 4.1 `CANDIDATE`

- 只表示待领取候选任务。
- 不允许开发、创建分支外写入、创建 PR 或推送业务改动。

### 4.2 `CLAIMED`

进入条件：

- 用户明确领取；或
- 任务位于用户明确授权的已领取委托批次中；
- 已绑定独立任务分支/worktree、基线 HEAD 和任务 ID。

### 4.3 `EXPLORING`

主 Agent 读取 WBS、相邻任务、权威契约、真实依赖状态、当前代码和风险，形成任务范围
契约。进入 `DEVELOPING` 前必须满足：

- `scope-record` 已完成；
- 当前 HEAD 的 `scope-check=PASS`；
- 硬前置和外部条件满足；
- 没有未解决的 WBS 冲突或依赖缺口。

### 4.4 `DEVELOPING`

Developer 只能实现范围契约中的能力。提交新 HEAD 后必须先 `sync-head`，再执行
`scope-check`。进入 `SELF_TESTING` 前必须有当前 HEAD、当前范围修订的
`scope-check=PASS`。

### 4.5 `SELF_TESTING`

- 执行与变更和 WBS 验收匹配的本地验证；
- 记录 exact-HEAD 测试证据；
- 若发现范围漂移，回到 `DEVELOPING` 收窄，或进入 `SCOPE_BLOCKED`；
- 只有 exact-HEAD `self_test=PASS` 且 `scope-check=PASS` 才能进入
  `IMPLEMENTATION_READY_FOR_DOCS`。

### 4.6 `IMPLEMENTATION_READY_FOR_DOCS`

表示实现与范围内自测已完成，Developer 停止写入。不得把该状态描述为 PR、CI 或审查
已经通过。

### 4.7 `DOCUMENTING`

Knowledge Keeper 审计范围内受影响的权威文档、索引、CHANGELOG、任务报告和记忆边界。
进入 `PR_CREATING` 前必须具备：

- exact-HEAD `scope-check=PASS`；
- exact-HEAD `self_test=PASS`；
- exact-HEAD `docs_gate=PASS`；
- 非空任务报告；
- 当前模式要求的创建 PR 授权。

若 PR 已经创建并由持久化 `pr_identity` 绑定，后续更新同一 PR 不重复消费“创建 PR”
授权，但仍须重新完成 exact-HEAD 范围、测试、文档和 CI 门禁。

### 4.8 `PR_CREATING`

- 创建或刷新既有 Ready PR；
- 绑定唯一 PR number、URL、base 和当前 HEAD；
- 不允许把同一任务切换到另一个 PR、URL 或 base；
- PR 模板必须完整，base 必须正确；
- 读取 PR 模板、workflow 和校验脚本，确定动态正文元数据契约；
- PR 创建或 Push 后，先等待 GitHub 的当前 HEAD/base/commits/files 稳定，再只更新所需
  机械字段并回读正文；不得改动叙述、范围、标签、标题或审查内容；
- 只有 exact-HEAD `metadata=PASS`，或有仓库契约审计证据的 `NOT_REQUIRED`，才能进入
  `CI_PENDING`。并发 HEAD、错误 base、重复歧义字段或回读不一致都留在本状态处理。

### 4.9 `CI_PENDING` 与 `FIXING_CI`

- `CI_PENDING` 只接受 GitHub live exact-HEAD CI 证据；
- metadata gate 未绑定当前 HEAD 时不得等待、记录或消费 CI PASS；
- 失败进入 `FIXING_CI`；
- CI 修复仍受原范围契约约束；
- 若 CI 暴露前置任务缺陷或 WBS 设计问题，不得夹带修复，进入 `SCOPE_BLOCKED`；
- CI 修复提交后重新执行 `scope-check -> SELF_TESTING -> DOCUMENTING -> PR refresh -> CI`。
- 上述 `PR refresh` 必须包含动态正文元数据同步与回读，不能只更新代码 HEAD。

### 4.10 `REVIEW_REQUESTED`

进入条件：

- Ready PR 与当前 HEAD 绑定；
- base、模板、exact-HEAD metadata、mergeable 状态正确；
- 当前 HEAD 的范围、文档和适用 CI 证据有效。

### 4.11 `REVIEWING`

Reviewer 在新鲜只读上下文中审查完整 exact-HEAD diff，但审查目标受范围契约约束。
Reviewer 可以报告系统级观察，不能自行决定把相邻任务能力纳入当前实现。

在发布 PR 审查评论前，主 Agent 必须执行 `review-triage`：

1. 第 1-3 轮逐项独立复现或用权威证据确认；第 4 轮起主动调查只聚焦潜在 P0/P1，偶然
   发现的 P2-P4 只做足以支持严重度与归属的有界核验，不扩展搜索或修复范围；
2. 给出 WBS/契约归属依据；
3. 按第五节分类；
4. 第二轮及以后说明与上一轮的差异；
5. 完成范围审计并记录 drift trigger；
6. 为每项发现按本节严重度定义记录 `P0`-`P4`；非缺陷证据项可用 `NA`；
7. 使公开 blocker 数量等于本轮“严重度可阻塞的 `IN_SCOPE_DEFECT`”数量，而不是原始
   Reviewer 发现总数。

分流规则：

- 第 1-3 轮有 `IN_SCOPE_DEFECT`，或第 4 轮起有 `P0/P1 + IN_SCOPE_DEFECT`，且无本轮
  严重度可阻塞的范围阻塞类别：发布
  `CHANGES_REQUIRED_BY_COMMENT`，进入 `FIXING_REVIEW`；
- 本轮严重度可阻塞的 `IN_SCOPE_DEFECT=0` 且无严重度可阻塞的范围阻塞类别：发布
  `APPROVED_FOR_MERGE_BY_COMMENT`，满足其他门禁后进入 `MERGE_READY`；
- 第 1-3 轮存在 `PREDECESSOR_DEFECT`、`UNMERGED_DEPENDENCY` 或 `WBS_AMBIGUITY`，
  或第 4 轮起这些类别达到 P0/P1：不得发布可继续修复/合并的 verdict，必须进入
  `SCOPE_BLOCKED` 请求用户决定。第 4 轮起的 P2-P4 范围观察不阻塞，但要注明归属与
  后续去向；如果 WBS 歧义确实使当前任务无法继续或无法判断 P0/P1 验收，它应按影响
  评为 P0/P1 并停止。
- `FUTURE_WBS_GAP` 达到 P0/P1 表示未来任务设计正在阻止当前安全验收，同样进入
  `SCOPE_BLOCKED`；不得以“未来任务”名义批准，也不得让当前 Developer 提前实现。

### 4.12 `FIXING_REVIEW`

Developer 只能接收本轮严重度可阻塞的 `IN_SCOPE_DEFECT` 条目。第 1-3 轮包括 P0-P4；
第 4 轮起只包括 P0/P1，P2-P4 即使确认真实也不得继续修复。禁止：

- 顺手修复前置任务；
- 提前实现后续 WBS；
- 根据 Reviewer 建议自行重设架构或 WBS；
- 把 hardening 建议升级为 blocker；
- 因为“问题真实”而跳过任务归属判断。

Main 在发布 `CHANGES_REQUIRED_BY_COMMENT` 时必须把允许修复的 Finding ID、严重度、审查
HEAD、范围修订和轮次固化为 repair whitelist。Developer Push 后先执行
`review-fix-record`，逐项回报的 ID 必须与白名单完全一致，并记录实际改变的能力；不能
多报 P2-P4、少报 P0/P1 或以同一路径为由顺手修改。白名单及完整 finding 会进入持久
历史，不因新 HEAD 清除。
该白名单从 changes-required verdict 起一直有效到下一次正式 Review 发布；在
`SELF_TESTING`、`DOCUMENTING`、CI 修复或 PR 刷新期间产生的任何额外 HEAD 都会把
authorization 重新置为 `PENDING_RECORD`。按第六节回退到 `DEVELOPING`（CI 修复可留在
`FIXING_CI`）后重新执行 `review-fix-record`；任何状态下，只要活动白名单存在，没有
当前 HEAD 的 exact record 就不能 `scope-check PASS`。

修复完成后必须执行：

`sync-head -> review-fix-record -> scope-check PASS -> SELF_TESTING -> DOCUMENTING -> PR refresh + metadata PASS -> CI -> 新鲜复审`

不设置最大 Review 轮数；但从第 4 轮开始强制进入 P0/P1 收敛模式。新 HEAD、换 Reviewer、
范围修订或重新请求 Review 都不得把累计轮次重置为 1。每轮仍须重新分诊，新范围信号
必须触发增强审计，但增强审计本身不授权修复低严重度或跨 WBS 问题。

### 4.13 `SCOPE_BLOCKED`

适用于：

- WBS 与权威契约边界冲突；
- 当前验收必须依赖未合入任务；
- 前置任务存在阻塞当前任务的真实缺陷；
- 修复要求扩大范围或重新设计；
- 无法判断问题属于当前任务还是相邻任务。

进入时必须提交决策包：

- 阻塞条件；
- 可复核证据；
- 已尝试的安全调查；
- 至少一个可选处理方案；
- 每个方案影响的 WBS/依赖/PR；
- 需要用户执行的明确动作。

主 Agent 可以给出推荐方案，但不得修改 WBS 或继续编码。用户决定后用 `scope-change`
记录新范围并返回 `EXPLORING`；若长期无法解决，可转 `SERIOUSLY_BLOCKED`。

### 4.14 `MERGE_READY`

进入条件：

- PR open、无冲突、base 正确；
- exact-HEAD scope/docs/PR metadata/CI 全部有效；
- exact-HEAD `review-triage` 无范围阻塞类别；
- Review verdict 为 `APPROVED_FOR_MERGE_BY_COMMENT`；
- 本轮严重度可阻塞的 `IN_SCOPE_DEFECT=0`；
- 当前模式下的合并授权有效。

### 4.15 `MERGING` 与 `MERGED`

- `MERGING` 只能通过受保护的 exact reviewed HEAD 合并命令进入；
- 禁止 admin bypass；
- `MERGED` 只表示合并操作已记录，不等于远端 base 已验证包含该提交。

### 4.16 `VERIFYING_DEVELOP`

重新 fetch 远端 base，验证 merge commit 是远端 base 的祖先，并核对实时 SHA。

### 4.17 `POST_MERGE_MEMORY`

在远端合并验证后更新项目记忆，输出非空持久摘要并完成 secrets check。

### 4.18 `COMPLETED`

仅当以下条件全部成立：

- 远端 base 已验证包含 merge commit；
- 项目记忆已更新；
- 持久摘要非空；
- secrets check PASS；
- 没有被错误吞并进当前任务的跨 WBS 改动。

### 4.19 `SERIOUSLY_BLOCKED`

仅用于已有具体证据、已尝试安全办法且确实需要外部长期动作的终止性阻塞。范围问题应
优先使用可恢复的 `SCOPE_BLOCKED`。

## 五、Review 发现分类与严重度

### 5.1 严重度

| 等级 | 定义 |
|---|---|
| `P0` | 可造成灾难性安全/合规事故、不可逆数据损坏、生产大面积不可用，必须立即阻断 |
| `P1` | 可复现的核心正确性、安全、契约或迁移缺陷，直接阻止当前 WBS 验收或造成严重回归 |
| `P2` | 真实且有影响，但影响有界、有规避方式或不阻止当前 WBS 核心验收 |
| `P3` | 次要健壮性、可维护性、测试或文档问题，不影响核心验收 |
| `P4` | 风格、措辞、偏好或可选优化 |
| `NA` | 仅用于 `INVALID`、`ALREADY_FIXED` 等不成立或已无缺陷影响的证据项 |

严重度必须由可复现触发、影响面和当前 WBS 验收决定，不能因为轮次已到第 4 轮就把
P2/P3 提升成 P1。`NA` 只允许 `NOT_REPRODUCIBLE`、`ALREADY_FIXED`、`INVALID`；这些
类别也只能用 `NA`。其余类别必须使用 P0-P4。`HARDENING_SUGGESTION` 不得标为 P0/P1；
若影响达到阻断级，必须改按真实 WBS 所有权分类。

### 5.2 WBS 分类

| 分类 | 是否计入当前 blocker | 当前任务动作 |
|---|---:|---|
| `IN_SCOPE_DEFECT` | 第 1-3 轮是；第 4 轮起仅 P0/P1 | 符合本轮阈值才复现、修复、回归；否则非阻塞留档 |
| `PREDECESSOR_DEFECT` | 否 | 停止夹带；请求修复前置任务或用户决定 |
| `UNMERGED_DEPENDENCY` | 否 | 等待依赖合入或请求用户协调 |
| `FUTURE_WBS_GAP` | 否 | 记录为后续任务门禁，不提前实现 |
| `WBS_AMBIGUITY` | 否 | 进入 `SCOPE_BLOCKED`，请求用户裁决 |
| `HARDENING_SUGGESTION` | 否 | 记录建议，不阻塞当前验收 |
| `NOT_REPRODUCIBLE` | 否 | 保存复现证据，不修改代码 |
| `ALREADY_FIXED` | 否 | 绑定已修复 HEAD/提交证据 |
| `INVALID` | 否 | 说明与权威契约冲突或错误前提 |

每个分诊条目必须包含：唯一 ID、来源、分类、严重度、摘要、复现证据和范围/WBS 依据。两个
Reviewer 得出相同结论只能增强真实性证据，不能替代主 Agent 的范围归属判断。

表中“停止/请求决定”的范围类别同样服从轮次阈值：第 1-3 轮全部触发；第 4 轮起只有
P0/P1 触发，P2-P4 作为非阻塞观察留档。
`FUTURE_WBS_GAP` 的 P0/P1 在所有轮次均进入 `SCOPE_BLOCKED`，因为它说明当前验收与
未来任务划分已冲突；P2-P4 仍按表中规则延后。

## 六、HEAD 与证据失效规则

任何 commit、rebase、update branch 或冲突解决产生新 HEAD 后，以下证据失效：

- `scope_check`；
- `review_triage`；
- self-test；
- docs gate；
- task report；
- 尚未消费的创建 PR 授权；
- 当前 PR HEAD 绑定；
- 当前 PR metadata 同步证据；
- CI；
- Review verdict；
- merge approval；
- merge record。

以下数据保留：

- 原始领取证据；
- 当前范围契约及历次已替换的完整范围契约；
- PR identity；
- 历史事件和评论 URL；
- 完整 `review_triage_history`、已发布 repair whitelist 和 `review_fix_history`；
- 已失效证据的审计事件。

新 HEAD 必须重新执行 `scope-check`。范围契约不会因 HEAD 变化自动扩大。

如果新 HEAD 出现在 `IMPLEMENTATION_READY_FOR_DOCS`、`DOCUMENTING`、`PR_CREATING`、
`CI_PENDING`、`REVIEW_REQUESTED`、`REVIEWING` 或 `MERGE_READY`，必须显式退回
`DEVELOPING`，再走完整的范围检查、自测、文档、PR refresh、CI 和 Review 流程。该回退
不需要伪造 CI 失败或 Review defect，也不能保留旧 verdict。

## 七、授权模式与范围的关系

### `SUPERVISED`

- 创建首个 PR 前等待用户批准任务报告；
- exact-HEAD Review 通过后等待用户批准合并；
- 范围变更始终等待用户明确批准。

### `DELEGATED_BATCH`

- 只在用户预先点名的已领取任务、仓库、base 和动作范围内自动推进；
- 可以按授权创建 PR/合并，但不能扩大任务列表或 WBS 范围；
- WBS 调整、重大架构/合规决定、生产发布和破坏性操作仍必须请求用户。

## 八、控制器强制门禁摘要

`workflowctl.py` 至少强制以下条件：

- 无范围契约或 exact-HEAD scope PASS，不得开发、自测、创建/刷新 PR、请求 Review 或
  合并；
- PR metadata 未对当前 HEAD 记录 `PASS` 或证据充分的 `NOT_REQUIRED`，不得进入 CI、
  请求 Review 或合并；
- 范围外文件不能记录 `scope-check PASS`；
- Review 未分诊不能发布 verdict；
- 同轮未发布 triage 的替换必须提供原因，旧 finding 全量保留在历史；
- published blocker 数在第 1-3 轮等于全部 `IN_SCOPE_DEFECT`，第 4 轮起只等于
  `P0/P1 + IN_SCOPE_DEFECT`；P2-P4 只能记录在 deferred non-blocking 区；
- Review 轮次必须跨 HEAD、Reviewer 和范围修订单调递增，不能重置以绕过收敛阈值；
- Review 修复必须先固化允许修复的 Finding ID 白名单；新 HEAD 的修复回报必须与白名单
  完全相等，并在 `scope-check PASS` 前记录 changed capabilities；
- 存在本轮严重度可阻塞的范围类别时不能进入 `FIXING_REVIEW` 或 `MERGE_READY`；
- `scope-change` 只能从 `SCOPE_BLOCKED` 执行且必须记录用户批准；
- scope revision 变化使旧范围检查、测试、CI、Review 和合并授权失效；
- 同一任务一旦绑定 PR identity，不得偷偷切换到另一个 PR。
