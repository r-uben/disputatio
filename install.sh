#!/usr/bin/env bash
# install.sh — wire disputatio + bundled second-opinion skills into Claude Code.
#
# Symlinks the repo's skill files into ~/.claude/skills/ so the repo is the
# single source of truth. Existing files at the destination are backed up
# with a .bak.<timestamp> suffix; nothing is overwritten silently.
#
# Run again with --uninstall to remove symlinks and restore .bak files.

set -euo pipefail

REPO_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
CLAUDE_SKILLS="${HOME}/.claude/skills"
TS="$(date +%Y%m%d-%H%M%S)"
MODE="${1:-install}"

cyan()  { printf "\033[36m%s\033[0m\n" "$*"; }
green() { printf "\033[32m%s\033[0m\n" "$*"; }
yellow(){ printf "\033[33m%s\033[0m\n" "$*"; }
red()   { printf "\033[31m%s\033[0m\n" "$*" >&2; }

# (target, source) pairs — target is under ~/.claude/skills/, source is in this repo.
LINKS=(
    "disputatio:${REPO_DIR}"
    "codex:${REPO_DIR}/skills/codex"
    "gemini:${REPO_DIR}/skills/gemini"
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
    # Restore most recent .bak if any
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

case "$MODE" in
    install)
        cyan "installing disputatio skills into ${CLAUDE_SKILLS}"
        require_dir "$CLAUDE_SKILLS"
        for pair in "${LINKS[@]}"; do
            backup_then_link "${pair%%:*}" "${pair#*:}"
        done
        echo
        verify_clis
        echo
        green "Done. Restart Claude Code to pick up the skills, then try:"
        echo "  /disputatio /path/to/paper.pdf --mode author"
        ;;
    --uninstall|uninstall)
        cyan "uninstalling disputatio skills from ${CLAUDE_SKILLS}"
        for pair in "${LINKS[@]}"; do
            remove_link "${pair%%:*}"
        done
        echo
        green "Uninstalled. Backups (if any) were restored to their original locations."
        ;;
    --help|-h|help)
        cat <<EOF
usage: ./install.sh [install|uninstall]

  install    (default) symlink the repo's skills into ~/.claude/skills/.
             existing files at the destination are backed up first.
  uninstall  remove the symlinks and restore the most recent backup, if any.
EOF
        ;;
    *)
        red "unknown mode: $MODE"
        echo "run ./install.sh --help for usage"
        exit 1
        ;;
esac
