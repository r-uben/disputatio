#!/usr/bin/env bash
# install.sh — wire the disputatio skill into Claude Code.
#
# Symlinks the disputatio skill into ~/.claude/skills/. Existing files at the
# destination are backed up with a .bak.<timestamp> suffix; nothing is
# overwritten silently.
#
# Modes:
#   install            symlink ONLY the disputatio skill into ~/.claude/skills/.
#   install --minimal  alias for `install` (kept for backwards compatibility).
#   uninstall          remove the symlinks this script created (incl. legacy
#                      vendored links) and restore the most recent .bak file.
#   --help             usage.
#
# Note: codex/gemini/agent_ctl.py are NO LONGER bundled here — they are
# git-ignored symlinks to their canonical homes (~/.config/ai-skills/ and
# ~/.claude/skills/). A clone does not ship them; provide your own. See
# vendor/README.md.

set -euo pipefail

REPO_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
CLAUDE_SKILLS="${HOME}/.claude/skills"
TS="$(date +%Y%m%d-%H%M%S)"
MODE="${1:-install}"
SUBMODE="${2:-}"

cyan()  { printf "\033[36m%s\033[0m\n" "$*"; }
green() { printf "\033[32m%s\033[0m\n" "$*"; }
yellow(){ printf "\033[33m%s\033[0m\n" "$*"; }
red()   { printf "\033[31m%s\033[0m\n" "$*" >&2; }

# Always-installed link.
CORE_LINKS=(
    "disputatio:${REPO_DIR}"
)

# Vendored helpers — installed by default, skipped under --minimal.
VENDOR_LINKS=(
    "codex:${REPO_DIR}/vendor/skills/codex"
    "gemini:${REPO_DIR}/vendor/skills/gemini"
    "agent_ctl.py:${REPO_DIR}/vendor/agent_ctl.py"
)

require_dir() {
    if [[ ! -d "$1" ]]; then
        mkdir -p "$1"
        cyan "  created $1"
    fi
}

backup_then_link() {
    local name="$1" src="$2" dest="${CLAUDE_SKILLS}/$1"
    if [[ -L "$dest" ]]; then
        local existing
        existing="$(readlink "$dest")"
        if [[ "$existing" == "$src" ]]; then
            green "  ✓ $name already linked to $src"
            return 0
        fi
        yellow "  ! $name is a symlink to $existing — replacing"
        rm "$dest"
    elif [[ -e "$dest" ]]; then
        local backup="${dest}.bak.${TS}"
        yellow "  ! $name exists — backing up to $(basename "$backup")"
        mv "$dest" "$backup"
    fi
    ln -s "$src" "$dest"
    green "  ✓ $name → $src"
}

remove_link() {
    local name="$1" dest="${CLAUDE_SKILLS}/$1"
    if [[ -L "$dest" ]]; then
        rm "$dest"
        green "  ✓ removed symlink $name"
    elif [[ -e "$dest" ]]; then
        yellow "  ! $name is not a symlink — leaving alone"
    else
        cyan "  · $name not present"
    fi
    local newest_bak
    newest_bak="$(ls -1t "${dest}.bak."* 2>/dev/null | head -n1 || true)"
    if [[ -n "${newest_bak}" ]]; then
        mv "$newest_bak" "$dest"
        green "  ✓ restored backup $(basename "$newest_bak") → $name"
    fi
}

verify_clis() {
    cyan "verifying prerequisites..."
    local missing=0
    for cli in claude codex gemini; do
        if command -v "$cli" >/dev/null 2>&1; then
            green "  ✓ $cli available"
        else
            red   "  ✗ $cli not found in PATH"
            missing=1
        fi
    done
    if (( missing )); then
        yellow "Some prerequisites are missing. See README for install instructions."
    fi
}

usage() {
    cat <<EOF
usage: ./install.sh [install|install --minimal|uninstall]

  install              symlink ONLY the disputatio skill into ~/.claude/skills/.
                       Existing files are backed up first. codex/gemini/agent_ctl.py
                       are not bundled — provide your own (see vendor/README.md).
  install --minimal    alias for install (kept for backwards compatibility).
  uninstall            remove the symlinks this script created (incl. legacy
                       vendored links) and restore the most recent .bak file.
EOF
}

case "$MODE" in
    install)
        require_dir "$CLAUDE_SKILLS"
        # Vendored helpers (codex/gemini/agent_ctl.py) are no longer shipped —
        # they live at their canonical homes and are git-ignored here. install
        # links ONLY the disputatio skill; bring your own helpers. --minimal is
        # accepted as a no-op alias for the previous behaviour.
        cyan "installing the disputatio skill into ${CLAUDE_SKILLS}"
        cyan "  (codex/gemini/agent_ctl.py are not bundled — provide your own; see vendor/README.md)"
        LINKS=("${CORE_LINKS[@]}")
        for pair in "${LINKS[@]}"; do
            backup_then_link "${pair%%:*}" "${pair#*:}"
        done
        echo
        verify_clis
        echo
        green "Done. Restart Claude Code to pick up the skill, then try:"
        echo "  /disputatio /path/to/paper.pdf --mode author"
        ;;
    --uninstall|uninstall)
        cyan "uninstalling disputatio symlinks from ${CLAUDE_SKILLS}"
        for pair in "${CORE_LINKS[@]}" "${VENDOR_LINKS[@]}"; do
            remove_link "${pair%%:*}"
        done
        echo
        green "Uninstalled. Backups (if any) were restored to their original locations."
        ;;
    --help|-h|help)
        usage
        ;;
    *)
        red "unknown mode: $MODE"
        echo
        usage
        exit 1
        ;;
esac
