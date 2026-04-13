#!/usr/bin/env bash
# Sync the vendored agent_ctl.py from the maintainer's source of truth.
#
# Source of truth: ~/.claude/skills/agent_ctl.py
# Destination:     vendor/agent_ctl.py (committed; public-facing copy)
#
# Run after editing the source. Commit the resulting diff.

set -euo pipefail

SRC="$HOME/.claude/skills/agent_ctl.py"
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DST="$ROOT/vendor/agent_ctl.py"

if [[ ! -f "$SRC" ]]; then
  echo "error: source not found at $SRC" >&2
  echo "  this script syncs from the maintainer's Claude Code skills dir." >&2
  echo "  if you are a public user installing disputatio, you want the" >&2
  echo "  reverse direction: cp vendor/agent_ctl.py \$SRC" >&2
  exit 1
fi

cp "$SRC" "$DST"
chmod +x "$DST"

echo "synced: $SRC → $DST"
echo
git -C "$ROOT" diff --stat -- vendor/agent_ctl.py || true
