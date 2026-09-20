# templates —— GitHub 协作治理模板

从真实项目打磨出来的 PR/Issue 治理链：**无分支保护仓库的人工合并控制**（平台没有分支保护时，用模板 + CI 校验 + GO 留痕替代平台自动阻断，不降低任何质量标准）。

## 内容

| 文件 | 用途 |
|---|---|
| `github/pull_request_template.md` | 13 节 PR 模板：关联语义、基线元数据（隐藏 HTML 注释供 CI 核对）、测试情况、契约变更、Gate 与独立审查、合并前人工核验、GO 留痕格式 |
| `github/ISSUE_TEMPLATE/bug_report.md` | Bug 模板：观察事实先于根因推测、In/Out of scope、追溯字段、可验证 AC、关闭记录段 |
| `github/ISSUE_TEMPLATE/feature_request.md` | Feature 模板：优先级 P0~P3/NA、契约影响三值、AC 写法守则 |
| `ci/check-pr-metadata.sh` | CI 脚本：校验 PR 正文隐藏元数据与 API 实际 base/commits/files 一致，防「追加提交后正文漂移」 |
| `dod-checklist.md` | DoD 清单（11 条，缺一不可） |

## 使用方式

```bash
cp templates/github/pull_request_template.md  <你的项目>/.github/pull_request_template.md
cp templates/github/ISSUE_TEMPLATE/*.md       <你的项目>/.github/ISSUE_TEMPLATE/
cp templates/ci/check-pr-metadata.sh          <你的项目>/scripts/
```

然后把模板里的占位符替换成你的项目事实：

1. `pull_request_template.md`：默认 base 分支名（`develop`）、涉及模块清单（按你的项目改）；
2. `check-pr-metadata.sh`：`ALLOWED_BASES` 环境变量或脚本内默认值（允许的 base 分支列表）；
3. CI 里挂一个 job 运行 `check-pr-metadata.sh`（需要 `GITHUB_REPOSITORY`、`PR_NUMBER` 环境变量与 `gh`、`jq`），每个 PR 强制执行。

配套阅读：`skills/agent-managed-delivery/references/merge-control.md`（无分支保护仓库的人工合并控制六步）、`docs/security-gates.md`（门禁禁令清单）。
