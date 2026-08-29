#!/usr/bin/env bash
set -euo pipefail

if [ "$#" -ne 1 ]; then
  echo "Usage: $0 /absolute/path/to/git-project" >&2
  exit 64
fi

bundle_dir=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
project_dir=$1

if [ ! -d "$project_dir" ]; then
  echo "Target directory does not exist: $project_dir" >&2
  exit 1
fi

if ! git -C "$project_dir" rev-parse --show-toplevel >/dev/null 2>&1; then
  echo "Target is not a Git worktree: $project_dir" >&2
  exit 1
fi

project_root=$(git -C "$project_dir" rev-parse --show-toplevel)
if [ "$project_dir" != "$project_root" ]; then
  echo "Use the repository root instead: $project_root" >&2
  exit 1
fi

protected=(
  "$project_root/.ccb/ccb.config"
  "$project_root/.ccb/ccb_memory.md"
  "$project_root/.codex/config.toml"
  "$project_root/AGENTS.md"
)

for destination in "${protected[@]}"; do
  if [ -e "$destination" ]; then
    echo "Refusing to overwrite existing file: $destination" >&2
    echo 'Compare the matching template manually and merge only intentional changes.' >&2
    exit 2
  fi
done

mkdir -p "$project_root/.ccb" "$project_root/.codex"
cp "$bundle_dir/templates/ccb/ccb.config" "$project_root/.ccb/ccb.config"
cp "$bundle_dir/templates/ccb/ccb_memory.md" "$project_root/.ccb/ccb_memory.md"
cp "$bundle_dir/templates/codex/config.toml.example" "$project_root/.codex/config.toml"
cp "$bundle_dir/templates/project/AGENTS.md" "$project_root/AGENTS.md"

if [ -e "$project_root/.gitignore" ]; then
  if ! grep -Fqx '.ccb/*' "$project_root/.gitignore"; then
    printf '\n# CCB runtime/session state — do not commit.\n.ccb/*\n' >> "$project_root/.gitignore"
  fi
else
  cp "$bundle_dir/templates/ccb/gitignore.snippet" "$project_root/.gitignore"
fi

echo "Created safe CCB templates in: $project_root"
echo 'Next: replace every <FILL_ME>, verify model access in .ccb/ccb.config, review git diff, then run ccb from the project root.'
