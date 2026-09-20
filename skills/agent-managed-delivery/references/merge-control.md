# 无分支保护仓库的人工合并控制

平台没有分支保护（或未启用）时，用以下人工流程替代平台自动阻断。它**不降低** CI、Review 或 DoD 标准，只是把阻断点从平台移到人的纪律上。有分支保护的仓库可不采用。

## 六步人工合并控制

1. **Draft PR**：以 Draft 状态开 PR，绑定关联 Issue 与 PR 基线元数据（base/commits/files，供 CI 校验）。
2. **CI 全绿**：等待当前 HEAD 的全部检查通过；新提交使旧检查作废，必须重跑。
3. **独立审查**：至少 1 名未参与实现者审查完整 exact-HEAD diff；高风险变更（鉴权/合规/迁移/文件安全/AI 真值/恢复）需 2 名。
4. **新提交作废旧核验**：任何新 HEAD 推送后，上一步的 CI 结论与审查结论全部作废，回到第 2 步。
5. **GO 留痕**：合并负责人在 PR 里留言 `GO / HEAD=<完整SHA> / CI=GREEN / REVIEW=<人数> / DOD=PASS`——留痕的 SHA 必须与合并时的 HEAD 逐字符一致。
6. **合并**：留言后立即合并，保护该 exact HEAD；合并后到目标分支验证（merge commit 存在、可拉取、可运行冒烟）。

## 禁止事项

- 禁止自审自批（实现者计入审查人数）。
- 禁止 CI 红灯合并，包括 admin bypass 与「重跑碰运气」。
- 禁止未留 GO 或留痕 SHA 与实际 HEAD 不符就合并。
- 禁止跳过 Draft→CI→审查的顺序「先合了再说」。

## 配套工具

- PR 模板与元数据 CI 校验脚本见仓库 `templates/`（`pull_request_template.md`、`ci/check-pr-metadata.sh`）。
- DoD 清单与禁止绕过门禁清单见 `templates/dod-checklist.md`。
