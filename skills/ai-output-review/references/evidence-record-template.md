# 证据记录模板

每次评审运行一个独立目录 `<evidence-root>/<run-id>/`，已存在则拒绝覆盖。

## 必交文件

- `summary.redacted.json` — 汇总判定结果
- `case-manifest.redacted.json` — 样本清单（ID、类别、判定，不含原文）
- `run-configuration.redacted.json` — 运行配置快照

## summary.redacted.json 字段

```json
{
  "run_id": "<RUN-ID>",
  "list_version": "<要素清单版本>",
  "requested_model": "<请求名>",
  "served_model": "<服务端响应回报的实际模型>",
  "prompt_version": "<Prompt 版本>",
  "sample_count": 0,
  "elements": {
    "total": 0,
    "passed": 0,
    "failed": 0,
    "not_applicable": 0,
    "pass_rate": "0.00",
    "failed_element_ids": ["E-xx"]
  },
  "serious_factual_errors": {
    "count": 0,
    "rate": "0.00",
    "threshold": "0.01",
    "double_reviewed": true
  },
  "second_reviewer": {
    "sampling_ratio": "0.34",
    "completed": true,
    "disputes_adjudicated": true
  },
  "verdict": {
    "per_category": { "<类别>": "PASS|FAIL" },
    "overall": "PASS|FAIL|NOT_REVIEWED"
  }
}
```

## 脱敏规则

**允许存**：哈希、计数、阈值、通过率、布尔标记、要素 ID 级判定结果。

**禁存**：用户输入原文、渲染后的 Prompt、模型原始输出、密钥/令牌、Provider 请求 ID。

原文只在受控环境（仓库外）留存，记录里只引其存放位置与内容哈希；`sha256` 锚定原始审计/运行数据，保证证据可复核而不可读。

## 结论表述纪律

- `verdict.per_category` 分项给出；`overall` 只是分项的汇总，不得出现「分项 FAIL 但 overall PASS」。
- 未跑真实模型时 `overall` 只能是 `NOT_REVIEWED`。
- `overall: PASS` 的前提：抽样完成、分歧已裁决、复核人已覆盖 100% 严重事实错误项。
