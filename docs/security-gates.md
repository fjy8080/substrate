# 安全门禁模式（供应链固定 / 漏洞豁免生命周期 / 审计基线）

从真实项目打磨的三类可复用安全门禁模式。不是脚本库，而是模式说明——落地时按你的 CI 体系实现，或把目标项目中对应脚本拷来复用。

## 一、CI 供应链输入固定

原则：**CI 的第三方输入必须可从 Git tree 单独重建**。

- workflow 引用的第三方 Action 一律固定完整 commit SHA：`uses: owner/repo@<40位SHA> # vX.Y.Z`（注释保留可读版本号），不得使用可移动的 major tag；
- 外部容器镜像（Dockerfile `FROM`、compose/workflow 的 `image:`）一律用可读 tag + `@sha256` digest（本地构建的镜像除外）；
- **未扫描生态检测**：仓库内出现新的锁定文件（pip/pnpm/go/cargo/composer 等各生态 lockfile）时，必须已被依赖扫描审计覆盖，或在检查脚本内显式白名单并注明不审理由——防止新生态绕过 SCA 准入；
- **豁免参数硬编码禁止**：扫描 workflow 的配置/命令行里字面出现豁免参数（如 `--ignore-vuln`）即拦截，豁免只能从唯一真值源文件渲染注入（见下），整行注释提及不判违规；
- 全部检查配**负向自测**（构造违规样板树，断言检查器确实报红）。

## 二、漏洞豁免生命周期（fail-closed）

豁免不是 ignore，是一个有到期日的跟踪项：

- **唯一真值源**：所有豁免登记在一个机器可读文件里（如 `security/audit-exemptions.json`），每条含：公告 ID、包与锁定版本、理由、跟进 issue、**到期日**、reachability；
- **渲染注入**：扫描 job 的豁免参数由检查器从真值源文件渲染生成（如 `check-audit-exemptions.py --render-args`），workflow 不手写；
- **到期自动化**：过期条目 fail-closed（到期日一过扫描直接红，渲染同时拒绝）；临期（如 ≤14 天）打 warning annotation；到期未消除必须修复或显式续期（改真值源随 PR 审查），不得静默保留；
- **可达性三值**：每条豁免标注 `dev-only`（仅开发/测试工具链）/ `build-only`（参与构建不进交付产物）/ `runtime-reachable`（生产运行时可加载）——审计报告区分可达性，不把公告一律宣称为生产可利用；`runtime-reachable` 的豁免理由与跟进优先级最严；字段缺失/非法一律 fail-closed。

## 三、存量基线过渡门

接手一个有历史债务的仓库时，一次性 fail-closed 会被存量公告淹没：

- 「**存量基线 + 新增 fail-closed**」：基线文件登记存量公告（同上格式），扫描只拦截基线之外的新增公告；
- **已消除条目必须同步收缩基线**（随消除 PR 审查），存量清零后基线为空，即等效全量 fail-closed；
- 基线条目不适用到期日字段（事件驱动收缩），但豁免理由仍必须登记。

## 四、审计摘要工件

审计结论不能只存在于运行日志：

- 每次扫描生成**脱敏审计摘要工件**：字段白名单法脱敏 + 原始审计 JSON 的 sha256 锚定；
- `if: always()` 下失败运行也归档——「这次跑过什么、发现了什么」在 exact HEAD 上可复核；
- 摘要按公告 ID 关联 reachability 字段并聚合计数，未登记的新增公告如实记 `unclassified`。

## 五、门禁纪律（与 templates/dod-checklist.md 配套）

- CI 优化只改执行编排，不删测试内容、不降质量门槛；同 Job 串步骤省分钟计费，失败仍使 Job 失败；
- 同一 PR 新提交取消旧 workflow（cancel-in-progress），不对过期 HEAD 重复计费；
- 失败时优先只重跑失败 Job；无基础设施理由不重跑全部；
- 条件 Job 显示 `skipped` 仅表示改动路径不涉及对应契约，不等于缺失检查——合并负责人必须确认路径分类正确。
