# 任意宿主（generic 模式）

任何能读 Markdown、能跑 shell 的 AI 编程 agent 都可以使用本仓库资产，即使它没有一等支持。

```bash
bash install.sh --host generic --dest <目录>
```

产物：`<目录>/skills/`（全部 skill）+ `<目录>/GLOBAL.md`（全局必读判据）。

## 手动接线清单

1. **技能加载**：把 `<dest>/skills/` 下需要的 skill 目录登记/拷贝到你的 agent 的技能加载位置：
   - 支持 Agent Skills 规范（SKILL.md frontmatter）的宿主（OpenCode、Gemini CLI、Goose 等）：直接放入其技能目录即可；
   - 不支持技能机制的宿主：把 SKILL.md 当作**可注入的 runbook**——需要执行对应流程时，把该 SKILL.md 全文作为指令注入上下文。
2. **全局指令**：把 `GLOBAL.md` 的内容并入你的 agent 的全局指令文件（`CLAUDE.md` / `AGENTS.md` / 系统提示词 / 项目规则文件）。
3. **触发语法**：SKILL.md 内 `/name` 为通用书写形式；按你的宿主的调用语法替换（Codex CLI 用 `$name`）。
4. **脚本**：skill 内的 python 脚本只依赖标准库 + `gh` CLI；`$SKILL_DIR` 指该 skill 安装目录，按你的宿主路径解析。
5. **记忆**：`memory/entries/` 按需放进你的 agent 记忆目录或项目 memory（见 memory/README.md）。

## 新增一等宿主

在 `install.sh` 注册表加一个 `install_<name>` 函数并加入 `ALL_HOSTS`（目标路径、指令文件名、是否支持 hooks），即可让该宿主获得与其他宿主相同的一键安装体验。
