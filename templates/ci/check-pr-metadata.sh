#!/usr/bin/env bash
# check-pr-metadata.sh —— 校验 PR 正文隐藏元数据与 GitHub API 实际值一致
#
# 防「追加提交后正文漂移」：PR 模板要求正文含三行隐藏 HTML 注释
#   <!-- base:<分支> --> / <!-- commits:<N> --> / <!-- files:<N> -->
# 本脚本从 API 取实际 base/commits/files 与注释值逐一比对，不一致即失败。
#
# 环境变量：GITHUB_REPOSITORY、PR_NUMBER（CI 提供）；依赖 gh、jq。
# 可配置：ALLOWED_BASES（逗号分隔的允许 base 分支列表，默认 "develop,main"）。
set -euo pipefail

ALLOWED_BASES="${ALLOWED_BASES:-develop,main}"

if [ -z "${GITHUB_REPOSITORY:-}" ] || [ -z "${PR_NUMBER:-}" ]; then
  echo "ℹ️ 非 GitHub PR 环境，跳过 PR 元数据检查"
  exit 0
fi

payload="$(gh api "repos/${GITHUB_REPOSITORY}/pulls/${PR_NUMBER}")"
base="$(jq -r '.base.ref' <<<"$payload")"
commits="$(jq -r '.commits' <<<"$payload")"
files="$(jq -r '.changed_files' <<<"$payload")"
body="$(jq -r '.body // ""' <<<"$payload")"

expected_base="$(grep -oE '<!-- base:[^ ]+ -->' <<<"$body" | sed -E 's/<!-- base:([^ ]+) -->/\1/' | tail -1)"
expected_commits="$(grep -oE '<!-- commits:[0-9]+ -->' <<<"$body" | sed -E 's/[^0-9]//g' | tail -1)"
expected_files="$(grep -oE '<!-- files:[0-9]+ -->' <<<"$body" | sed -E 's/[^0-9]//g' | tail -1)"

if ! grep -qE "(^|,)$base(,|$)" <<<"$ALLOWED_BASES" || [ "$expected_base" != "$base" ]; then
  echo "❌ PR 基线不一致：实际=$base，描述=$expected_base，允许值=$ALLOWED_BASES"
  exit 1
fi
if [ "$expected_commits" != "$commits" ]; then
  echo "❌ PR 提交数不一致：实际=$commits，描述=$expected_commits（追加提交后需同步正文）"
  exit 1
fi
if [ "$expected_files" != "$files" ]; then
  echo "❌ PR 文件数不一致：实际=$files，描述=$expected_files"
  exit 1
fi

echo "✅ PR 元数据一致：base=$base, commits=$commits, files=$files"
