#!/usr/bin/env bash
set -u

echo 'CCB multi-agent preflight (read-only)'
echo "Directory: $(pwd)"
echo

required=(git tmux node npm ccb codex claude)
optional=(opencode cc-switch)
failed=0

show_version() {
  local command_name="$1"
  local version
  version=$("$command_name" --version 2>/dev/null | head -n 1 || true)
  if [ -n "$version" ]; then
    printf '  %-10s %s\n' "$command_name" "$version"
  else
    printf '  %-10s found (version output unavailable)\n' "$command_name"
  fi
}

echo 'Required commands:'
for command_name in "${required[@]}"; do
  if command -v "$command_name" >/dev/null 2>&1; then
    show_version "$command_name"
  else
    printf '  %-10s MISSING\n' "$command_name"
    failed=1
  fi
done

echo
echo 'Optional commands:'
for command_name in "${optional[@]}"; do
  if command -v "$command_name" >/dev/null 2>&1; then
    show_version "$command_name"
  else
    printf '  %-10s not installed (optional)\n' "$command_name"
  fi
done

echo
if [ "$failed" -eq 0 ]; then
  echo 'PASS: required commands are on PATH. Complete each provider login before starting CCB.'
else
  echo 'FAIL: install or fix each missing required command, then run this script again.'
fi

exit "$failed"
