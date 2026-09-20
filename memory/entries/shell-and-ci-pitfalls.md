---
name: shell-and-ci-pitfalls
description: Shell 与 CI 实战坑——管道吞退出码、反引号命令替换、gh 用 --body-file、CI 磁盘守卫用绝对量、手测与 hook 同解释器、.env.local 污染对照实验、Docker daemon 前置检查
metadata:
  type: reference
---

# Shell 与 CI 实战坑合集

- **管道吞退出码**：`pytest ... 2>&1 | tail -1` 的退出码是 `tail` 的，测试红了 `&& git commit` 照走，会提交带红测试的提交。判绿必须显式取 `RC=$?`（命令重定向到文件后取 `$?`）或 `set -o pipefail`。
- **双引号里的反引号是命令替换**：`gh issue comment --body "...\`path\`..."` 会把反引号内当命令执行，正文出现空洞。含反引号/`$` 的评论与提交信息一律写临时文件：gh 用 `--body-file`（heredoc 用 `<<'EOF'` 防展开），commit 用 `git commit -F <file>`；已发布的评论可用 `gh api -X PATCH .../comments/<id> -F body=@文件` 修复。
- **CI 磁盘守卫用绝对空闲量，自愈清理也用绝对量**：相对使用率阈值（如 85%）与绝对守卫线（如 10GiB 空闲）之间有空档，会出现「红灯但不自愈」。CI runner 的三类隐性垃圾源：遗留 docker 容器/卷、未轮转的构建与诊断日志、孤儿缓存。runner「假活」：`systemctl status` 显示 active ≠ 正常派发，看 journal 里的真实报错。
- **CI 全部 queued ≠ 慢**：先查 runner 磁盘与存活，再怀疑单个 job。
- **手测和 hook/自动化必须用同一个解释器**：如 python3.9 与 3.12 的 f-string 规则不同（3.9 表达式部分禁反斜杠），bash 里全角标点紧贴 `$var` 会被并进变量名（用 `${var}${var:+；}` 规避）。用不同解释器测试等于没测。
- **gitignored 的 `.env.local` 会污染全量测试/构建**：跑测试前把它移开，跑完校验 sha256 再还原。判定「失败是不是我引起的」时先做这个对照实验，再下结论。
- **`.env.example` 与 config 校验可能脱节**：照 example 配置后启动 fail-fast 报缺键，且中间层（如 alembic）会吞异常导致报错严重失真——诊断时绕过中间层直连真实报错源（如 `python -c "from app.core.config import settings"`）。
- **集成测试前先确认 Docker daemon 已起**：daemon down 时 testcontainers/Redis 类用例直接 ERROR（不是 FAIL/SKIP），成百上千的 error 不是代码问题。旧「经验数字」（剔除几个固有失败）不可迁移到新环境。
- **「测试通过」先确认测的字符串真的是你以为的字符串**：mock 夹具、环境差异都可能让测试与生产行为脱节；单测全绿 ≠ e2e 同步。
- **Docker/Testcontainers 跳过、浏览器限制都是未验证门**：报告里要与通过项分开陈述，不得当 pass。

关联 [[git-pitfalls]]、[[llm-output-acceptance]]。
