# substrate

> 多 agent 开发环境的**基底**：把个人开发中沉淀的通用 skill、跨项目记忆、hooks 与各 agent 全局配置收进一个 git 仓库，换机器 / 多机同步时一条脚本恢复。

覆盖 agent：**Claude Code、Codex、OMP**（Grok Build 配置待定位补充，见「已知缺口」）。

## 快速恢复（新机器）

```bash
# 0. 装好 CLI 本体：claude / codex / omp / gh（npm 或各官方渠道），Claude Code 首次运行一次生成 ~/.claude.json
git clone <本仓库> ~/substrate && cd ~/substrate

bash install.sh                    # 1. 无损项：skills / 全局必读指令 / hook 脚本 / OMP 配置（覆盖前自动备份）
# 2. 按 docs/secrets-checklist.md 把 mcp-servers.json.tpl 和 config.toml 里的 <ZAI_*> 占位符填上真实凭据
bash install.sh --merge-mcp        # 3. 合并全局 MCP 到 ~/.claude.json（需 jq）
bash install.sh --with-config      # 4. （可选）覆盖 ~/.claude/settings.json 与 ~/.codex/config.toml
bash install.sh --with-memory      # 5. （可选）部署 codex 记忆

# 手动收尾：codex 重新登录、OMP oauth 授权、gh auth login、重装官方插件 marketplace（见下）
```

## ★ 必读 Skill（两个 agent 各一份，全局指令强制加载）

| Skill | 来源 | 作用 | 模式 |
|---|---|---|---|
| `lean-mode`（节制工程） | [Timefiles404/lean-mode-skill](https://github.com/Timefiles404/lean-mode-skill)（MIT） | 防御性代码/校验/抽象的信任边界判据（只在四处信任边界做一次校验）；构建测试从几十分钟压到几十秒 | 纯 prompt skill |
| `stop-that-shit`（别再造史了） | [lennney/stop-that-shit](https://github.com/lennney/stop-that-shit)（MIT, v0.1.0） | 只做用户点名的事：Stop Ladder 四问拦截范围膨胀、顺手加固、无需求的哈希/依赖/兼容层 | advisory skill（本仓库默认）；hook 强制模式见 `agents/vendor/stop-that-shit/INSTALL.md`，经 plugin marketplace 安装并本人确认 Hook 信任 |

- **必读机制**：`agents/claude-code/CLAUDE.md` 与 `agents/codex/AGENTS.md` 由 install.sh 部署为全局指令文件（`~/.claude/CLAUDE.md`、`~/.codex/AGENTS.md`），每次会话自动加载两个 skill 的核心判据，正文细节在各自 `skills/<name>/SKILL.md`。
- **上游真源**：`agents/vendor/` 保存两个项目的完整上游副本（源码 + 测试 + LICENSE），`skills/` 下是部署拷贝——升级时从 vendor 重新同步。收录时 stop-that-shit 测试套件 181/182 绿（唯一失败的 `opencode-smoke` 是 OpenCode 平台环境测试，与本仓库使用的 claude/codex 路径无关）。

## 目录结构

```
substrate/
├── install.sh                 # 恢复脚本（幂等，覆盖前备份，--dry-run 预演）
├── agents/                    # 各 agent 全局配置（已脱敏、已清理路径残留）
│   ├── claude-code/
│   │   ├── skills/            # 11 个 skill：自建 9 个（agent-managed-delivery、ask、ccb-*、github-*）+ ★必读 2 个
│   │   ├── CLAUDE.md          # ★全局必读指令（必读 skill 载体 → ~/.claude/CLAUDE.md）
│   │   ├── settings.json      # hooks/permissions/env（含 3 处 Windows 路径残留的修正）
│   │   ├── config.json
│   │   ├── mcp-servers.json.tpl  # 全局 MCP 模板（z.ai 系 ×4，凭据占位）
│   │   └── scripts/           # notification.js（跨平台系统通知）、check-memory-links.sh（记忆断链检查）
│   ├── codex/
│   │   ├── skills/            # 8 个 skill：自建 6 个（与 Claude 侧同源）+ ★必读 2 个
│   │   ├── AGENTS.md          # ★全局必读指令（→ ~/.codex/AGENTS.md）
│   │   ├── hooks.json         # 与 Claude 同源的 4 类 hook
│   │   └── config.toml        # 脱敏模板（删 Windows trust 残留/hooks.state 信任哈希）
│   ├── omp/
│   │   ├── config.yml         # 模型角色、任务并发、approval 模式（无密钥，原样）
│   │   └── models.yml         # zai provider 模型定义（oauth 认证，无密钥）
│   └── vendor/                # 第三方必读 skill 的上游完整副本（MIT；源码+测试+LICENSE）
│       ├── lean-mode-skill/
│       └── stop-that-shit/
├── memory/                    # 通用记忆（详见 memory/README.md）
│   ├── claude/                # 13 条跨项目方法论/环境记忆（从各项目 auto-memory 精选）
│   └── codex/                 # 记忆脱敏精选版（偏好与通用技巧，快照与敏感段已移除）
└── docs/                      # 文档与杂项（与配置严格分开）
    ├── secrets-checklist.md   # ★ 密钥恢复清单：哪些占位符要填、哪些要重新登录
    ├── OMP项目级AMD并行工作区改造复用手册.md
    ├── ccb-workflow-kit/      # CCB 多 Agent 协作工作流搭建包（原桌面 zip）
    └── misc/gitconfig.template
```

## 日常维护（本机 → 仓库）

```bash
# 改了 ~/.claude/skills 或 ~/.codex/skills 之后同步回仓库：
rsync -a --delete --exclude='__pycache__' ~/.claude/skills/ ~/Desktop/project/substrate/agents/claude-code/skills/
rsync -a --exclude='__pycache__' --exclude='.system' ~/.codex/skills/agent-managed-delivery \
      ~/.codex/skills/github-issue-create ~/.codex/skills/github-issue-debug \
      ~/.codex/skills/github-issue-review ~/.codex/skills/github-pr-fix \
      ~/.codex/skills/github-pr-review ~/Desktop/project/substrate/agents/codex/skills/
# 同步前确认必读 skill（lean-mode / stop-that-shit）未被 --delete 误删（本机也装了它们则无碍）。
```

注意：仓库里的 `settings.json` / `config.toml` / `mcp-servers.json.tpl` 是**脱敏版**，从本机同步配置文件时先 diff，别把真实密钥带进来。

## 相对原机器配置的清理记录

| 位置 | 改动 | 原因 |
|---|---|---|
| `settings.json` Notification hook | `C:\Users\<旧Windows用户>\...\notification.js` → `$HOME/.claude/scripts/notification.js` | Windows 残留路径在本机失效，hook 一直静默失败；脚本已重写为跨平台版 |
| `settings.json` SessionStart hook | 硬编码旧 Windows memory 路径 → 脚本内自动按 `$CLAUDE_PROJECT_DIR` 推导 | 同上 |
| `settings.json` extraKnownMarketplaces | 删除 `zai-coding-plugins`（Windows npx 缓存路径）及 `glm-plan-*` 两个插件启用项 | 路径失效不可移植；重装方式见「已知缺口」 |
| `config.toml` | 删 13 个 `C:\...` trust 残留、`[hooks.state]` 信任哈希、`node_repl` MCP 与 openai-bundled 插件条目；trust 段注释化占位 | Linux 无效 / 新机自动重建 / 首次运行会重新弹 hook 信任确认（正常现象） |
| 全部 MCP 配置 | token → `<ZAI_BEARER_TOKEN>`、key → `<ZAI_API_KEY>` | 真实凭据永不入库 |
| `memory/codex/` | 重写为脱敏精选版：删 16 个项目快照 Task Group 与 VPS/私钥/代理/法律段落，路径统一写 `~` | 按用户 2026-08-30 脱敏决定（S1-S9、S12，明细见 memory/README.md） |
| `agents/codex/rules/` + settings.json `ssh <prod>*` | 整目录移除 + 删两条 ssh 权限 | 历史命令白名单无迁移价值且含业务细节；生产服务器别名不外泄 |

## 已知缺口与手动项

- **已知测试失败（预先存在）**：`agents/claude-code/skills/agent-managed-delivery/scripts/test_workflowctl.py` 32 用例中 1 个失败（scope-drift 用例，git 测试沙盒找不到 origin/develop）。本机原版同样失败，非搬运/脱敏引入；codex 侧同款测试全绿，说明 claude 侧 workflowctl.py 落后于 codex 侧，待在源头修复后按「日常维护」同步回仓库。
- **Grok Build**：本机未找到 `grok` 命令与 `~/.grok` 配置目录，暂未收录——定位到配置位置后补 `agents/grok/`。
- **`~/.claude/agents/`（AMD 6 个 subagent 定义）**：原机器上有、本机不存在（Windows 迁移丢失）。AMD skill 在 Claude Code 下可直接运行，如需 subagent 定义可参照 `agents/codex/skills/agent-managed-delivery/` 内的 agents 定义重建（model 按 [[subagent-model-opus-only]] 约定全用 opus）。
- **glm-plan-*（@z_ai/coding-helper）插件**：重新安装智谱 coding-helper 后由其注册 marketplace。
- **Codex 官方插件**：`codex` 首次运行后按 `config.toml` 中保留的 `claude-plugins-official` marketplace 重装即可。
- **stop-that-shit hook 强制模式（可选）**：本仓库默认安装 advisory skill；如需运行时强制（UserPromptSubmit/PreToolUse hook 拦截），按 `agents/vendor/stop-that-shit/INSTALL.md` 经 plugin marketplace 安装，Hook 信任必须由本人确认，agent 不得代确认。
- **opencode / Cursor**：未列入常用 agent，其配置（`~/.config/opencode/opencode.json`、`~/.cursor/cli-config.json`）未收录；opencode 配置含明文 key，若将来收录必须先脱敏。
- **项目级记忆**（各项目 CLAUDE.md、memory/、.omp/、.ccb/）不在本仓库范围，由项目自身 / workspace-migration tar 包负责。

## 与 workspace-migration tar 包的关系

`workspace-migration-2026-08-29.tar.gz`（桌面）是当时的**一次性全量快照**（含项目记忆与状态）；本仓库是**长期维护的通用资产层**——换机时：先 clone 本仓库恢复 agent 环境底座，再按需从快照恢复项目级数据。
