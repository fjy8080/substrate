---
name: ai-output-review
description: Acceptance review of LLM/AI-generated output quality — blind review protocol with dual reviewers, absolute element checklists, serious-factual-error thresholds, and evidence redaction. Use when the user asks to 验收/评审 AI 产出, review LLM output quality, judge AI content depth, or set up AI output acceptance criteria. Automated tests verify contracts only; this skill covers what tests cannot — content depth. Do not use for ordinary code review or PR review.
---

# AI Output Review（AI 产出质量验收）

Conventions: skill names are written `/name`; substitute your host's invocation prefix (Codex CLI uses `$name`). 本 skill 为纯文档 skill，无脚本依赖。

## Why this exists

「契约里有字段」「测试通过」「功能已实现」与「AI 真实输出达到要求的内容质量」之间**没有证据链**。自动化测试只覆盖契约与传输（Schema、错误码、结构），**从不覆盖内容深度**。本 skill 承载内容质量的验收方法。

## Three principles

1. **自动化默认不调真实模型**：测试用 Mock 适配器 + 依赖注入，按「固定场景 + Prompt 版本」组织保证可重复；真实模型验证在专门环境手动做。mock 夹具测不出真模型行为——mock 返回合法形状 ≠ 真模型会输出该形状；合入前对易触发形态跑一次真模型 smoke。
2. **绝对要素清单，不搞相对排名**：验收主模型产出用绝对要素清单逐项判定（达标线 100%，不适用项须写理由并经复核）；「相对基线 95%」式门槛用途是备选模型对比，两者口径与用途不同，不得互相替代。
3. **可见性硬约束**：产出要素必须在最终用户界面**实际渲染**可见；接口有字段、落库成功、响应非空均不算达标。

完整评审流程（角色、抽样、分歧裁决、严重事实错误认定）见 [review-protocol.md](references/review-protocol.md)。

## Core procedure（精简版）

1. **运行取证**：真实模型全量跑一次，产出脱敏证据（只存哈希/计数/阈值/通过率/布尔标记，禁存原文与模型原始输出）。
2. **脱敏与去偏**：去除模型标识 + 固定随机种子排序样本；原文只在受控环境留存，仓库只引位置与哈希。
3. **全量初评**：第一评审人对全量样本按要素清单逐项判定「通过/不通过/不适用」。
4. **抽样复评**：第二评审人按 ≥1/3 抽样独立背靠背复评（不得先看首评结论）；所有「不通过」「严重事实错误」「不适用」样本 100% 强制包含。
5. **分歧裁决**：首评与复评不一致的项交第三人裁决，裁决为终局；裁决前按「存在风险」计入。
6. **结论**：分项给出（每类产出各自达标/不达标 + 不通过要素 ID），禁止一句「整体达标」。

## Verdict discipline（结论纪律）

- 严重事实错误（结论性错误、捏造条件/幻觉、会误导下游决策的解释）**不因其余要素优秀而豁免**；达标线默认 <1%，且全部认定项 100% 双人复核。
- 未跑真实模型、仅有 Mock 结果时，结论只能写「未评审」，不得写「达标」。
- 第二评审人未到位、抽样未完成、分歧未裁决——任何「已达标」结论不成立。
- 「功能已实现」「测试通过」「契约已有字段」均不得代替质量达标结论。

## Evidence discipline（证据纪律）

- 每次评审一个独立 run-id 目录，已存在则拒绝覆盖。
- 允许存：哈希、计数、阈值、通过率、布尔标记、要素级判定结果。
- 禁存：用户输入原文、渲染后的 Prompt、模型原始输出、密钥、Provider 请求 ID。
- 记录实际服务的模型（取自服务端响应，可能与请求名不同——记录请求名与服务端回报两个字段）。

Templates: [acceptance-checklist-template.md](references/acceptance-checklist-template.md)、[evidence-record-template.md](references/evidence-record-template.md)。
