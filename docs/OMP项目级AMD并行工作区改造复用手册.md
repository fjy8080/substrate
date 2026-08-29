# OMP 项目级 AMD、LSP、Memory 与四并行工作区改造复用手册

> 生成日期：2026-08-25  
> 用途：把一个普通 Git 项目改造成可使用 OMP、项目级 AMD Agent、完整 LSP、本地高效记忆，以及 4 个可并行且状态互不覆盖的独立工作区。  
> 本文不包含任何真实 Token、密码、私钥、账号或生产 Secret。所有凭据都必须从 OMP 本地凭据库或环境变量读取，禁止写进脚本和项目文件。

---

## 1. 最终目标

改造完成后，单个项目具备：

1. 项目根目录 `.omp/`，包含项目模型路由、AMD Agent、LSP 和硬规则。
2. AMD 只能调用项目内六个 Agent：
   - `task-scout`
   - `explorer`
   - `developer`
   - `knowledge-keeper`
   - `reviewer`
   - `utility`
3. Main/default 和 Reviewer 使用 GPT-5.6 Sol high；其余 AMD Agent 使用 GPT-5.6 Luna max。
4. Java、JavaScript/TypeScript、Vue、HTML、CSS/SCSS、JSON、YAML、Bash、Dockerfile LSP。
5. `memory/` 只保留高频入口，过期快照进入 `memory/archive/`。
6. 4 个完整独立 clone，每个 clone 独立拥有：
   - `.git`
   - `.git/agent-managed-delivery/state.json`
   - `memory/`
   - `.omp/`
   - OMP cwd 会话
7. 四个工作区可以同时执行不同 AMD 任务，但单个工作区内部仍遵守 AMD 串行 writer 规则。

### 为什么并行工作区必须使用完整 clone

不要用同一 Git 仓库的普通 `git worktree` 承载多个独立 AMD batch。

AMD `workflowctl.py` 把 durable state 存在 Git common directory：

```text
.git/agent-managed-delivery/state.json
```

同一仓库的多个 worktree 共享 common directory，会造成：

- batch 相互覆盖；
- `active_task_id` 冲突；
- 一个 Agent 改变另一个 Agent 的状态机；
- memory 虽分开但 AMD durable state 不独立。

因此并行 AMD 工作区使用完整 clone，并使用 `--no-hardlinks` 和无 alternates 的独立对象库。

---

## 2. 变量与前置条件

在执行前设置自己的项目变量：

```bash
export PROJECT_ROOT="/absolute/path/to/current-project"
export PROJECT_NAME="your-project-name"
export REPO_URL="https://github.com/OWNER/REPO"
export BASE_BRANCH="develop"
export PARALLEL_ROOT="/absolute/path/to/${PROJECT_NAME}-agent-workspaces"
export TS_SDK="$(npm root -g)/typescript/lib"
```

要求：

```bash
omp --version
git --version
node --version
npm --version
java -version
python3 --version
```

Java LSP 运行时要求 JDK 21 或更高。业务项目自身可以继续编译到较低 Java target。

---

## 3. 首先审计现有 OMP

### 3.1 基础状态

```bash
omp --version
omp config path
omp config list --json
omp models --json
omp usage --json
omp plugin list --json
omp auth-broker status --json
```

### 3.2 当前凭据只看元数据，不输出 Secret

OMP 凭据通常在：

```text
~/.omp/agent/agent.db
```

只读取 provider、credential type、disabled state。不要读取或打印凭据正文。

### 3.3 检查启动日志

```bash
ls -lt ~/.omp/logs
```

重点检索：

```text
MCP tool load failed
model discovery failed
LSP
fallback
quota
```

两个常见典型问题：

1. z.ai MCP 仍使用旧 `open.bigmodel.cn` 地址；
2. MCP 配置里的旧 Authorization 已失效，但 OMP 凭据库中的 z.ai 凭据仍有效。

### 3.4 修改前备份

```bash
cp ~/.omp/agent/config.yml ~/.omp/agent/config.yml.before-optimization
chmod 600 ~/.omp/agent/config.yml.before-optimization
```

如需改 Claude/OpenCode MCP 配置：

```bash
cp ~/.claude.json ~/.claude.json.before-omp-optimization
cp ~/.config/opencode/opencode.json \
  ~/.config/opencode/opencode.json.before-omp-optimization
chmod 600 ~/.claude.json.before-omp-optimization
chmod 600 ~/.config/opencode/opencode.json.before-omp-optimization
```

---

## 4. 全局 OMP 基线

推荐全局基线：

- 默认/全局：Luna max；
- smol：Luna xhigh；
- 子 Agent 隔离自动选择；
- 最大并发 4；
- 子 Agent LSP 开启；
- Secret 脱敏开启；
- YOLO 完全放行；
- 不保留额外 Bash prompt/deny pattern。

可用命令设置：

```bash
omp config set modelRoles \
  '{"default":"openai-codex/gpt-5.6-luna:max","smol":"openai-codex/gpt-5.6-luna:xhigh"}'

omp config set task.isolation.mode auto
omp config set task.maxConcurrency 4
omp config set task.enableLsp true
omp config set secrets.enabled true

omp config set tools.approvalMode yolo
omp config set bash.patterns '[]'
omp config set tools.approval '{}'
```

验证：

```bash
omp config list --json | jq '{
  modelRoles: .modelRoles.value,
  approvalMode: ."tools.approvalMode".value,
  bashPatterns: ."bash.patterns".value,
  toolPolicies: ."tools.approval".value,
  isolation: ."task.isolation.mode".value,
  maxConcurrency: ."task.maxConcurrency".value,
  taskLsp: ."task.enableLsp".value,
  secrets: ."secrets.enabled".value
}'
```

### YOLO 风险

`yolo + bash.patterns=[] + tools.approval={}` 会允许 Shell、Git push、PR 创建、merge、API mutation 等执行操作。它只表示工具不弹确认，不表示业务授权自动存在。

必须继续由项目规则约束：

- 是否允许 commit/push；
- 是否允许创建/合并 PR；
- 是否允许部署生产；
- 是否允许真实支付、退款、数据恢复和破坏性操作。

---

## 5. 可选：修复 z.ai MCP

如果日志中出现：

```text
MCP tool load failed
undefined ... protocolVersion
```

先把旧地址替换成官方当前地址：

```text
https://api.z.ai/api/mcp/zread/mcp
https://api.z.ai/api/mcp/web_reader/mcp
https://api.z.ai/api/mcp/web_search_prime/mcp
```

不要在文档或命令历史中写真实 API Key。使用 OMP 已保存凭据：

```bash
TOKEN="$(omp token zai --raw)"
```

然后使用 `jq --arg` 原子更新需要的客户端配置：

```bash
TMP="$(mktemp)"
jq --arg auth "Bearer $TOKEN" '
  .mcpServers["zread"].headers.Authorization = $auth |
  .mcpServers["web-reader"].headers.Authorization = $auth |
  .mcpServers["web-search-prime"].headers.Authorization = $auth
' ~/.claude.json > "$TMP"
chmod 600 "$TMP"
mv "$TMP" ~/.claude.json
```

对 OpenCode 使用其 `.mcp` 路径做等价更新。更新后配置文件权限保持 `600`。

MCP 初始化探针：

```bash
TOKEN="$(omp token zai --raw)"
curl --silent --show-error --max-time 30 \
  -H "Authorization: Bearer $TOKEN" \
  -H 'Content-Type: application/json' \
  -H 'Accept: application/json, text/event-stream' \
  --data '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"omp-probe","version":"1"}}}' \
  https://api.z.ai/api/mcp/zread/mcp
```

期望返回 `protocolVersion: 2024-11-05`。完成后 `unset TOKEN`。

---

## 6. 建立项目级 `.omp`

### 6.1 本地排除，不污染团队 `.gitignore`

若 `.omp/` 是个人本地配置：

```bash
printf '\n/.omp/\n' >> "$PROJECT_ROOT/.git/info/exclude"
```

不要为了个人 OMP 配置修改团队 `.gitignore`。如果团队决定共享 `.omp/`，则改为正式评审、跟踪并提交。

目录结构：

```text
.omp/
├── AGENTS.md
├── config.yml
├── lsp.json
└── agents/
    ├── task-scout.md
    ├── explorer.md
    ├── developer.md
    ├── knowledge-keeper.md
    ├── reviewer.md
    └── utility.md
```

### 6.2 `.omp/config.yml`

```yaml
# Project-scoped OMP routing for Agent Managed Delivery.
modelRoles:
  default: openai-codex/gpt-5.6-sol:high
  plan: openai-codex/gpt-5.6-sol:high
  smol: openai-codex/gpt-5.6-luna:max
  amd_scout: openai-codex/gpt-5.6-luna:max
  amd_explorer: openai-codex/gpt-5.6-luna:max
  amd_developer: openai-codex/gpt-5.6-luna:max
  amd_knowledge: openai-codex/gpt-5.6-luna:max
  amd_reviewer: openai-codex/gpt-5.6-sol:high
  amd_utility: openai-codex/gpt-5.6-luna:max

task:
  isolation:
    mode: auto
  maxConcurrency: 4
  enableLsp: true
  agentModelOverrides:
    task-scout: "@amd_scout"
    explorer: "@amd_explorer"
    developer: "@amd_developer"
    knowledge-keeper: "@amd_knowledge"
    reviewer: "@amd_reviewer"
    utility: "@amd_utility"
```

项目配置优先于全局配置，因此在此项目启动 OMP 时 Main 会使用 Sol high。

### 6.3 `.omp/AGENTS.md`

```md
# PROJECT OMP rules

## AMD subagent boundary

When `/agent-managed-delivery` or Agent Managed Delivery is explicitly invoked, Main MUST dispatch only project agents under `.omp/agents/`:

- `task-scout`
- `explorer`
- `developer`
- `knowledge-keeper`
- `reviewer`
- `utility`

NEVER substitute bundled, user/global, marketplace, or similarly named agents from another source. Always pass the exact project `agent` name. If a required project agent is unavailable, stop and report configuration failure instead of falling back.

AMD business tasks remain serial. Parallelize only independent read-only reconnaissance. `developer` is the sole code writer; `knowledge-keeper` starts only after Developer stops; every review round uses a fresh `reviewer` context.

## Model policy

- Main/default and reviewer: `openai-codex/gpt-5.6-sol:high`.
- Other AMD agents: `openai-codex/gpt-5.6-luna:max`.
- Do not override routing from task calls.

## Project LSP

Use LSP for definitions, references, implementations, code actions, renames, and diagnostics whenever available. Never perform manual cross-file symbol renames.

## Repository rules

Read the repository's real guidance and local memory before work. Code and authoritative project docs win over local memory. Never treat a tag, merged PR, local test, or old memory snapshot as deployment evidence.
```

---

## 7. 六个项目 AMD Agent 模板

### 7.1 `task-scout.md`

```md
---
name: task-scout
description: AMD read-only task and dependency reconnaissance.
model: "@amd_scout"
autoloadSkills: agent-managed-delivery
tools: read, grep, glob, lsp, web_search
---

You are the AMD Task Scout for this repository.

Read-only responsibilities:
- Inspect task sources, dependencies, repository guidance, and live evidence.
- Recommend candidate tasks and identify predecessor/successor constraints.
- Distinguish evidence from assumptions and never claim work for the user.
- Preserve the WBS boundary; never redesign or silently expand scope.

Never edit files, mutate workflow state, claim tasks, commit, push, create or merge PRs. Return concise evidence to Main.
```

### 7.2 `explorer.md`

```md
---
name: explorer
description: AMD read-only code, contract, test, and risk mapping.
model: "@amd_explorer"
autoloadSkills: agent-managed-delivery
tools: read, grep, glob, lsp, bash
---

You are the AMD Explorer.

Read-only responsibilities:
- Map code, contracts, tests, configuration, and authoritative documents.
- Inspect the exact branch and HEAD supplied by Main.
- Identify symbols, callers, data flow, validation boundaries, and reproducible risks.
- Separate current-task ownership from predecessor, successor, and neighboring WBS work.

Use Bash only for read-only deterministic checks. Never edit, write, commit, push, mutate workflow state, or expand scope. Return paths, symbols, tests, exclusions, and blockers.
```

### 7.3 `developer.md`

```md
---
name: developer
description: AMD sole code writer for an already-scoped task worktree.
model: "@amd_developer"
autoloadSkills: agent-managed-delivery
tools: read, grep, glob, lsp, bash, edit, write
---

You are the AMD Developer and the only code-writing subagent for the assigned task worktree.

Responsibilities:
- Implement only locked WBS scope, acceptance criteria, allowed paths, and scope revision.
- Reuse existing patterns and inspect affected callers before exported changes.
- Run focused validation and report commands, results, and tested HEAD.
- Stop when implementation and self-test are complete.

Never broaden scope, repair adjacent WBS tasks, edit secrets, bypass gates, or perform production changes. Do not push/create/merge PRs unless Main explicitly delegates an already-authorized action.
```

### 7.4 `knowledge-keeper.md`

```md
---
name: knowledge-keeper
description: AMD post-development documentation and memory writer.
model: "@amd_knowledge"
autoloadSkills: agent-managed-delivery
tools: read, grep, glob, edit, write
---

You are the AMD Knowledge Keeper.

Start only after Developer stops.
- Audit affected authoritative docs, indexes, changelog, task report, and memory.
- Update only documentation/memory covered by locked scope.
- Preserve task ID, scope revision, HEAD, evidence, and limitations.
- Never claim unobserved CI, merge, deployment, or production evidence.

Do not modify application code, tests, migrations, secrets, workflow state, PRs, or external systems.
```

### 7.5 `reviewer.md`

```md
---
name: reviewer
description: AMD fresh read-only exact-HEAD reviewer.
model: "@amd_reviewer"
autoloadSkills: agent-managed-delivery
tools: read, grep, glob, lsp, bash
---

You are the AMD Reviewer.

- Review the complete exact-HEAD diff against WBS scope, acceptance, and contracts.
- Independently reproduce candidate defects.
- Report file/symbol evidence, P0-P4 severity, reproduction, and WBS ownership.
- Distinguish IN_SCOPE_DEFECT, PREDECESSOR_DEFECT, UNMERGED_DEPENDENCY, WBS_AMBIGUITY, FUTURE_WBS_GAP, and HARDENING_SUGGESTION.
- Rounds 1-3 inspect all confirmed findings; round 4 onward actively investigate only P0/P1.

Use Bash only for read-only validation. Never edit, write, commit, push, mutate state, or become Developer for your findings.
```

### 7.6 `utility.md`

```md
---
name: utility
description: AMD deterministic read-only extraction and validation helper.
model: "@amd_utility"
autoloadSkills: agent-managed-delivery
tools: read, grep, glob, bash
---

You are the AMD Utility agent.

- Run deterministic, bounded, read-only extraction or validation requested by Main.
- Return exact commands, exit status, relevant output, and checked HEAD/file set.
- Keep evidence mechanical and reproducible.

Never edit, mutate databases, commit, push, create/merge PRs, change workflow state, deploy, or operate production.
```

---

## 8. 安装项目 LSP

### 8.1 Web/配置语言服务器

```bash
npm install -g \
  typescript@6.0.3 \
  typescript-language-server@6.0.0 \
  @vue/language-server@2.2.12 \
  vscode-langservers-extracted@4.10.0 \
  yaml-language-server@1.24.0 \
  bash-language-server@5.6.0 \
  dockerfile-language-server-nodejs@0.15.0
```

为什么 Vue 使用 2.2.12：Vue Language Server 3.x 默认依赖 hybrid tsserver request forwarding。OMP 这类通用 LSP 客户端中可能完成 initialize，但 `documentSymbol` 长时间超时。2.2.12 配合 `hybridMode=false` 已验证可返回完整 Vue SFC template/script/style 符号树。

TypeScript 7 的全局包结构可能不包含传统 `lib/tsserver.js`，typescript-language-server 6 会报找不到 TypeScript。使用 TypeScript 6.0.3，并确认：

```bash
ls "$(npm root -g)/typescript/lib/tsserver.js"
```

### 8.2 Eclipse JDTLS 1.60.0

```bash
mkdir -p "$HOME/.local/share/jdtls/1.60.0"

curl -fL \
  -o /tmp/jdt-language-server-1.60.0.tar.gz \
  https://download.eclipse.org/jdtls/milestones/1.60.0/jdt-language-server-1.60.0-202606262232.tar.gz
```

官方 SHA-256：

```text
e94c303d8198f977930803582738771fd18c52c5492878410bf222b1aa81ef1d
```

验证：

```bash
printf '%s  %s\n' \
  'e94c303d8198f977930803582738771fd18c52c5492878410bf222b1aa81ef1d' \
  '/tmp/jdt-language-server-1.60.0.tar.gz' | sha256sum -c -
```

解压并放入 PATH：

```bash
tar -xzf /tmp/jdt-language-server-1.60.0.tar.gz \
  -C "$HOME/.local/share/jdtls/1.60.0"

mkdir -p "$HOME/.local/bin"
ln -sfn "$HOME/.local/share/jdtls/1.60.0/bin/jdtls" \
  "$HOME/.local/bin/jdtls"
rm /tmp/jdt-language-server-1.60.0.tar.gz
```

### 8.3 `.omp/lsp.json`

JSON 不会展开环境变量。创建文件时把 `__TS_SDK__` 替换为 `$(npm root -g)/typescript/lib` 的绝对路径。

```json
{
  "servers": {
    "jdtls": {
      "rootMarkers": [".git"],
      "warmupTimeoutMs": 60000
    },
    "typescript-language-server": {
      "rootMarkers": [".git"],
      "initOptions": {
        "hostInfo": "omp-coding-agent",
        "tsserver": {
          "path": "__TS_SDK__"
        },
        "preferences": {
          "includeInlayParameterNameHints": "all",
          "includeInlayVariableTypeHints": true,
          "includeInlayFunctionParameterTypeHints": true
        }
      }
    },
    "vue-language-server": {
      "rootMarkers": [".git"],
      "warmupTimeoutMs": 60000,
      "initOptions": {
        "typescript": {
          "tsdk": "__TS_SDK__"
        },
        "vue": {
          "hybridMode": false
        }
      }
    },
    "vscode-html-language-server": { "rootMarkers": [".git"] },
    "vscode-css-language-server": { "rootMarkers": [".git"] },
    "vscode-json-language-server": { "rootMarkers": [".git"] },
    "yamlls": { "rootMarkers": [".git"] },
    "bashls": { "rootMarkers": [".git"] },
    "dockerls": { "rootMarkers": [".git"] }
  },
  "idleTimeoutMs": 600000
}
```

这里把 monorepo 根 `.git` 作为 root marker，因为真实 `pom.xml`、`package.json` 可能位于 `backend/`、`web/` 等子目录，OMP 的启动检测是 cwd 根级检查，不递归寻找 marker。

### 8.4 重载与验证

安装后重启 OMP，并重启共享 mux：

```bash
omp ps restart omp.lsp.mux
```

OMP 内执行：

```text
lsp status
```

期望 9 个 server：

```text
typescript-language-server
vue-language-server
jdtls
vscode-html-language-server
vscode-css-language-server
vscode-json-language-server
yamlls
bashls
dockerls
```

至少验证：

- 一个 Java 文件 diagnostics；
- 一个 Vue 文件 diagnostics + document symbols；
- 一个 JS/TS 文件 diagnostics；
- 一个 workflow YAML；
- 一个 Shell 脚本；
- 一个 Dockerfile。

不要只看到 `configured` 就宣称正常；至少启动关键 server 并确认 `ready` 和真实请求返回。

---

## 9. 建立高效本地 Memory

### 9.1 建议结构

```text
memory/
├── README.md
├── AGENTS.md
├── MEMORY.md
├── session-log.md
├── tech-debts.md
├── pitfalls.md
├── authorization-boundaries.md
├── main-worktree-risks.md
└── archive/
```

### 9.2 最小读取顺序

1. `memory/AGENTS.md`：当前硬规则、开工顺序、Agent 路由。
2. `memory/MEMORY.md`：最新 Git/PR/Issue/release/Flyway 快照。
3. 任务相关时读取 `tech-debts.md` 或 `pitfalls.md`。
4. 默认不读 `archive/`。

### 9.3 活跃文件职责

- `README.md`：导航和权威源说明。
- `AGENTS.md`：只保留当前有效规则，不堆叠“最新覆盖旧最新”。
- `MEMORY.md`：单页动态快照，全面刷新时整体替换动态区。
- `session-log.md`：短事件，不复制完整 CI/PR 输出。
- `tech-debts.md`：只保留仍开放或需实时复核的风险。
- `pitfalls.md`：可复用工程经验，避免动态 SHA。
- `main-worktree-risks.md`：本地工作区实时风险。

### 9.4 归档流程

```bash
STAMP="$(date +%Y-%m-%d)"
mkdir -p "memory/archive/${STAMP}-pre-refresh"
```

将旧完整入口、已完成 Issue、旧 handoff、RC/batch 快照移动进去，然后创建新的精简入口。不要删除历史证据。

归档 README 必须明确：

- 归档内“当前”“最新”只对生成时点有效；
- 不恢复旧授权、旧排除清单、旧 active task；
- 当前状态先 live fetch/查询，再读活跃 `MEMORY.md`。

### 9.5 不同项目不能复制业务事实

将这套方案用于另一个不同项目时：

- 可以复制 memory 目录结构和写作规则；
- 不要复制原项目的 Issue、SHA、业务规则、服务器、Flyway 数值和发布结论；
- `MEMORY.md` 应从新项目的 live Git/GitHub/代码重新生成；
- `AGENTS.md` 应适配新项目自己的红线和权威文档。

---

## 10. 在复制工作区前同步基线

```bash
cd "$PROJECT_ROOT"
git status --short --branch
git fetch --prune origin
git rev-list --left-right --count HEAD...origin/$BASE_BRANCH
git merge-base --is-ancestor HEAD origin/$BASE_BRANCH
git merge --ff-only origin/$BASE_BRANCH
```

若 `merge-base --is-ancestor` 失败或工作区有未知修改，停止。不要强制 reset、clean 或覆盖用户文件。

记录基线：

```bash
BASELINE_SHA="$(git rev-parse HEAD)"
printf '%s\n' "$BASELINE_SHA"
```

---

## 11. 建立 4 个独立并行工作区

### 11.1 创建父目录

```bash
mkdir -p "$PARALLEL_ROOT"
```

### 11.2 每个工作区执行

下面脚本展示完整过程。首次使用前逐行确认路径；目标目录必须不存在。

```bash
set -euo pipefail

BASELINE_SHA="$(git -C "$PROJECT_ROOT" rev-parse HEAD)"

for N in 1 2 3 4; do
  ID="agent-$N"
  DEST="$PARALLEL_ROOT/$ID"

  test ! -e "$DEST"

  git clone --local --no-hardlinks \
    --branch "$BASE_BRANCH" \
    "$PROJECT_ROOT" \
    "$DEST"

  git -C "$DEST" remote set-url origin "$REPO_URL"

  cp -a "$PROJECT_ROOT/.omp" "$DEST/.omp"
  cp -a "$PROJECT_ROOT/memory" "$DEST/memory"

  {
    printf '\n/.omp/\n'
    printf '/start-omp.sh\n'
  } >> "$DEST/.git/info/exclude"

  cat > "$DEST/start-omp.sh" <<'SCRIPT'
#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")"
exec omp "$@"
SCRIPT
  chmod +x "$DEST/start-omp.sh"

  cat > "$DEST/memory/WORKSPACE.md" <<EOF
# Workspace Identity

- Workspace ID: \`$ID\`
- Workspace root: \`$DEST\`
- Maintain only this clone's \`memory/\` and \`.git/agent-managed-delivery\`; never touch sibling workspaces.
- Branch names must contain the workspace ID and use \`feature/$ID-...\` or \`fix/$ID-...\`.
EOF

  cat >> "$DEST/.omp/AGENTS.md" <<EOF

## Workspace identity and isolation

- Workspace ID: \`$ID\`
- Workspace root: \`$DEST\`
- Maintain only this clone's \`memory/\` and \`.git/agent-managed-delivery\`; never touch sibling workspaces.
- Branch names must contain the workspace ID and use \`feature/$ID-...\` or \`fix/$ID-...\`.
EOF

  test "$(git -C "$DEST" rev-parse HEAD)" = "$BASELINE_SHA"
  test "$(git -C "$DEST" branch --show-current)" = "$BASE_BRANCH"
  test "$(git -C "$DEST" remote get-url origin)" = "$REPO_URL"
  test ! -e "$DEST/.git/objects/info/alternates"
  test ! -e "$DEST/.git/agent-managed-delivery/state.json"
  test -x "$DEST/start-omp.sh"
  test -z "$(git -C "$DEST" status --short)"
done
```

`--local --no-hardlinks` 的目的：利用本地源快速 clone，但对象文件独立，不通过 hardlink 或 alternates 依赖原工作区。

### 11.3 为什么不复制 AMD state

不要复制：

```text
.git/agent-managed-delivery/
```

每个工作区第一次明确启动 AMD batch 时自行创建 state。旧项目的 completed batch、授权、active task 和范围不能进入新工作区。

---

## 12. 并行工作区启动

每个 clone 都有：

```bash
/path/to/agent-1/start-omp.sh
/path/to/agent-2/start-omp.sh
/path/to/agent-3/start-omp.sh
/path/to/agent-4/start-omp.sh
```

分别在四个终端或标签页运行。启动脚本会切换 cwd，保证加载对应的：

```text
.omp/config.yml
.omp/AGENTS.md
.omp/agents/
.omp/lsp.json
memory/
```

冒烟：

```bash
./start-omp.sh -p --no-session --no-title --tools=task \
  --max-time 1m 'Return exactly WORKSPACE_OMP_OK'
```

成功启动同时证明 cwd 项目配置可以解析；`task` 工具初始化时会发现项目 Agent 定义。

---

## 13. 四工作区运行纪律

### 13.1 任务去重

每个 workspace 领取任务前：

```bash
git fetch --prune origin
gh issue view ISSUE_NUMBER
gh pr list --state open --limit 100
git branch -r
```

确认：

- Issue 未被 sibling 或同事领取；
- 没有同任务开放 PR；
- 没有重复 Flyway 编号；
- 没有冲突 branch basename。

### 13.2 分支命名

```text
agent-1: feature/agent-1-* 或 fix/agent-1-*
agent-2: feature/agent-2-* 或 fix/agent-2-*
agent-3: feature/agent-3-* 或 fix/agent-3-*
agent-4: feature/agent-4-* 或 fix/agent-4-*
```

### 13.3 并行边界

允许：

```text
agent-1 → Task A
agent-2 → Task B
agent-3 → Task C
agent-4 → Task D
```

不允许：

- 两个 workspace 处理同一 Issue/WBS；
- 一个 workspace 修改另一个 workspace 的 memory/AMD state；
- 同一 AMD batch 并行两个 writer；
- Developer 与 Knowledge Keeper 同时写同一任务 worktree；
- Reviewer 直接修复自己发现的问题。

### 13.4 更新 develop

新任务前：

```bash
git fetch --prune origin
git switch "$BASE_BRANCH"
git merge --ff-only "origin/$BASE_BRANCH"
```

不能 fast-forward 时停止并调查，不强制覆盖。

---

## 14. 独立与共享边界

每个 clone 独立：

- Git objects 与 refs；
- AMD durable state；
- 项目 memory；
- `.omp` 项目 Agent/config/LSP；
- cwd 对应的 OMP session 存储；
- 任务分支和本地测试产物。

用户级共享：

- OMP 可执行文件；
- OpenAI/z.ai 认证；
- 模型额度和 rate limit；
- 用户级 Skill 实现；
- LSP 二进制；
- GitHub 账号和同一个远程仓库。

四 Agent 并发会共同消耗模型额度，并可能竞争远端 CI、GitHub API 和同一业务资源。

---

## 15. 验证清单

### 全局 OMP

- [ ] `omp --version` 正常。
- [ ] `secrets.enabled=true`。
- [ ] approval mode 符合预期；若 YOLO，明确接受风险。
- [ ] `task.isolation.mode=auto`。
- [ ] `task.maxConcurrency=4`。
- [ ] `task.enableLsp=true`。

### 项目 `.omp`

- [ ] Main/default = Sol high。
- [ ] Reviewer = Sol high。
- [ ] 其他 AMD Agent = Luna max。
- [ ] 六个 `.omp/agents/*.md` 均可解析。
- [ ] `.omp/AGENTS.md` 禁止全局/bundled fallback。
- [ ] `.omp/` 被本地 exclude 或经过团队评审后正式跟踪。

### LSP

- [ ] 9 个 server 被发现。
- [ ] JDTLS 使用 JDK 21+。
- [ ] `typescript/lib/tsserver.js` 存在。
- [ ] Vue 2.2.12 + `hybridMode=false`。
- [ ] Java diagnostics 返回。
- [ ] Vue document symbols 返回完整符号树。
- [ ] YAML/Bash/Docker diagnostics 返回。

### Memory

- [ ] 活跃入口简短。
- [ ] archive 不默认读取。
- [ ] 没有敏感信息。
- [ ] 动态 Git/Issue/PR/release 状态标明采集日期。
- [ ] 不同项目没有复制旧业务事实。

### 四并行工作区

- [ ] 四个目标都是完整 `.git` 目录。
- [ ] `git-common-dir` 各自指向自身 `.git`。
- [ ] 无 `objects/info/alternates`。
- [ ] 无初始 AMD state。
- [ ] HEAD/branch/origin 正确。
- [ ] tracked status clean。
- [ ] `.omp/config.yml` 与 `.omp/lsp.json` 复制一致。
- [ ] 六个项目 Agent 存在。
- [ ] `memory/WORKSPACE.md` ID 唯一。
- [ ] launcher 可执行并通过 OMP 冒烟。

---

## 16. 回滚

### 全局 OMP 配置

```bash
cp ~/.omp/agent/config.yml.before-optimization ~/.omp/agent/config.yml
```

重启 OMP。

### MCP 配置

```bash
cp ~/.claude.json.before-omp-optimization ~/.claude.json
cp ~/.config/opencode/opencode.json.before-omp-optimization \
  ~/.config/opencode/opencode.json
chmod 600 ~/.claude.json ~/.config/opencode/opencode.json
```

注意：旧备份可能包含失效 MCP 地址或旧凭据，只在确有必要时恢复。

### 项目本地 OMP

如果 `.omp/` 未跟踪且确认不再需要：先备份，再移走，不要直接删除未知用户修改。

```bash
mv "$PROJECT_ROOT/.omp" "$PROJECT_ROOT/.omp.disabled"
```

### 并行 clone

删除工作区是破坏性操作。先确认：

- 没有未提交修改；
- 没有未推送分支；
- AMD state 已归档；
- memory 已保存。

确认后再删除对应完整 clone。绝不对父目录直接执行未经检查的递归删除。

---

## 17. 应用于另一个项目时必须改的内容

1. `PROJECT_ROOT`、`PROJECT_NAME`、`REPO_URL`、`BASE_BRANCH`。
2. 项目语言与需要的 LSP server；不是 Java/Vue 项目就删掉无关 server。
3. `.omp/AGENTS.md` 的项目红线、权威文档、数据库和发布规则。
4. 六个 Agent 的工具边界；例如没有 GitHub 或没有 DB 时不要保留无关说明。
5. memory 只复制目录结构，不复制原项目事实。
6. 分支命名必须符合新仓库规范，并保留 workspace 唯一标识。
7. CI、PR、发布、生产、人工 Gate 的授权规则必须从新项目真实规则重新建立。
8. AMD skill 若依赖项目专用脚本，确认脚本在新项目可用；缺失时停止，不能使用旧项目路径。

---

## 18. 关键经验总结

1. **AMD 状态独立需要完整 clone，不是普通 worktree。**
2. **项目 Agent 使用同名覆盖并不够，必须在 `.omp/AGENTS.md` 明确禁止 fallback。**
3. **模型路由放在项目 `.omp/config.yml`，不要依赖当前会话手动选择。**
4. **LSP 的 root marker 对 monorepo 很关键；OMP 不递归寻找子目录 marker。**
5. **Vue LS 3.x initialize 成功不等于功能可用，必须实际测 `documentSymbol`。**
6. **Memory 要区分当前入口与历史归档，避免每次加载数百行过期状态。**
7. **YOLO 是工具授权，不是业务授权。**
8. **四个 clone 的 Git/AMD/memory 独立，但模型额度、GitHub 远端和 CI 仍共享。**
9. **复制到另一个项目时复制方法和模板，不复制旧项目业务事实。**
