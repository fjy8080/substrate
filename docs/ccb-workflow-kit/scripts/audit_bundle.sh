#!/usr/bin/env bash
set -euo pipefail

bundle_dir=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
echo "Scanning $bundle_dir for likely secrets (heuristic only)."

pattern='(sk-[A-Za-z0-9_-]{16,}|AKIA[0-9A-Z]{16}|AIza[0-9A-Za-z_-]{20,}|api[_-]?key[[:space:]]*[:=][[:space:]]*[^<[:space:]][^[:space:]]+|authorization:[[:space:]]*bearer[[:space:]]+[^[:space:]]+)'
if rg -n -i -g '!scripts/audit_bundle.sh' -e "$pattern" "$bundle_dir"; then
  echo 'POTENTIAL SECRET FOUND: remove or replace it before sharing.' >&2
  exit 1
fi

if find "$bundle_dir" -type f \( -name '*.db' -o -name '*.sqlite*' -o -name '.env' -o -name '.env.*' -o -name 'auth.json' \) -print | grep -q .; then
  echo 'POTENTIAL SENSITIVE RUNTIME FILE FOUND: remove it before sharing.' >&2
  exit 1
fi

echo 'PASS: no obvious secret pattern or runtime database detected. Perform a manual review before sharing.'
