#!/usr/bin/env python3
"""
agent-ctl: Non-blocking controller for Codex and Gemini CLI sessions.

Lets Claude Code start, monitor, and kill agent processes without blocking.
Uses `script -q` on macOS to defeat output buffering so progress is visible
in real time. Supports multi-turn sessions via `send`.

Subcommands:
    start   codex|gemini "prompt" [--model M] [--cwd /path] [--timeout S] [--flags ...]
    send    <id> "follow-up message" [--timeout S]
    check   <id> [--tail N]
    result  <id>
    kill    <id>
    status
    cleanup [--agent codex|gemini]
"""

import argparse
import json
import os
import re
import shutil
import signal
import subprocess
import sys
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path

def _claude_config_dir() -> Path:
    """Resolve the active Claude config dir (honors CLAUDE_CONFIG_DIR)."""
    env = os.environ.get("CLAUDE_CONFIG_DIR")
    return Path(env).expanduser() if env else Path.home() / ".claude"


def _account_suffix() -> str:
    """Suffix derived from CLAUDE_CONFIG_DIR (e.g. '-vox' for ~/.claude-vox).

    Lets us route codex/gemini to matching homes (~/.codex-vox, ~/.gemini-vox)
    so secondary Claude accounts use secondary subagent accounts.
    """
    name = _claude_config_dir().name
    if name.startswith(".claude-"):
        return name[len(".claude"):]  # ".claude-vox" -> "-vox"
    return ""


STATE_FILE = _claude_config_dir() / "agent-sessions.json"
OUTPUT_DIR = Path("/tmp/agent-ctl")

# Env vars to unset per agent (conflict with OAuth auth)
UNSET_KEYS = {
    "codex": ("OPENAI_API_KEY", "OPENAI_BASE_URL", "CODEX_API_KEY"),
    "gemini": ("GOOGLE_API_KEY", "GEMINI_API_KEY"),
}

# Default models per agent
DEFAULT_MODELS = {
    "codex": "gpt-5.4",
    "gemini": "gemini-3.1-pro-preview",
}

# Fallback model on 429 capacity exhaustion. Empty by user preference: stay on
# the requested model (e.g. gemini-3.1-pro-preview) and let it retry/fail
# rather than silently downgrading to flash.
FALLBACK_MODELS: dict[str, str] = {}

# Default timeout (seconds) — 5 minutes
DEFAULT_TIMEOUT = 300

# Prompts larger than this are written to a temp file and piped via stdin
# to avoid shell argument limits and special-char escaping issues.
PROMPT_SIZE_THRESHOLD = 10240  # 10 KB


# ── State helpers ────────────────────────────────────────────────────────────

def load_state() -> dict:
    if STATE_FILE.exists():
        try:
            return json.loads(STATE_FILE.read_text())
        except json.JSONDecodeError:
            return {}
    return {}


def save_state(state: dict) -> None:
    STATE_FILE.write_text(json.dumps(state, indent=2))


def next_id(state: dict) -> str:
    """Return next sequential session ID like '01', '02', ..."""
    existing = [int(k) for k in state if k.isdigit()]
    return f"{max(existing, default=0) + 1:02d}"


def is_alive(pid: int) -> bool:
    """Check if a process is still running (and not a zombie)."""
    try:
        os.kill(pid, 0)
    except (ProcessLookupError, PermissionError):
        return False
    # On macOS/Linux, check for zombie state via ps.
    # A zombie still exists in the process table but has exited.
    try:
        result = subprocess.run(
            ["ps", "-p", str(pid), "-o", "state="],
            capture_output=True, text=True, timeout=2,
        )
        state = result.stdout.strip()
        if state and state[0].upper() == "Z":
            return False
    except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
        pass
    return True


def reap_finished(state: dict) -> dict:
    """Update status of sessions whose processes have exited."""
    for sid, meta in state.items():
        if meta["status"] == "running" and not is_alive(meta["pid"]):
            meta["status"] = "done"
            meta["ended"] = datetime.now(timezone.utc).isoformat()
    return state


# Regex to extract Gemini session UUID from --list-sessions output
GEMINI_UUID_RE = re.compile(
    r"\[([0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12})\]"
)


def gemini_latest_uuid(cwd: str) -> str | None:
    """Return the UUID of the most recently created Gemini session."""
    env = _clean_env()

    try:
        out = subprocess.run(
            ["gemini", "--list-sessions"],
            cwd=cwd, env=env,
            capture_output=True, text=True, timeout=15,
        )
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return None

    last_uuid = None
    for line in out.stdout.splitlines():
        m = GEMINI_UUID_RE.search(line)
        if m:
            last_uuid = m.group(1)
    return last_uuid


def _launch_background(shell_cmd: str, outfile: Path, timeout: int,
                       cwd: str, env: dict) -> int:
    """Launch a command in background with timeout. Returns PID.

    Historically wrapped the agent in `script -q /dev/null` to "defeat
    output buffering," but `script(1)` opens a pty and makes its child the
    leader of a *new* session — and gemini's node worker stays in that
    detached session, so when `script` later exits (e.g. because the child
    closed the pty) the gemini node gets reparented to init and survives
    every subsequent `kill -TERM -<our_pgid>`. From agent_ctl's POV the
    tracked bash PID is gone → is_alive() reports False → session marked
    done — meanwhile the real gemini node keeps running, holding OAuth
    state and polluting `gemini --list-sessions`. Dropping the wrapper
    keeps every descendant inside our process group, so the timeout's
    `kill -TERM -$$` (mirrored from cmd_kill's killpg) actually reaches
    them. Bonus: removes the `^D` + ripgrep-warning noise the pty replay
    injected at the head of every output. Codex emits its real answer
    through `--output-last-message`; gemini's `-o text` writes to stdout
    in a single batch, so we don't lose real-time progress that matters.
    """
    wrapper = (
        f"{shell_cmd} > {_quote(str(outfile))} 2>&1"
    )
    timed_wrapper = (
        f"( {wrapper} ) & CPID=$!; "
        f"( sleep {timeout}; "
        f"  kill -TERM -$$ 2>/dev/null; "
        f"  sleep 2; "
        f"  kill -KILL -$$ 2>/dev/null "
        f") & TPID=$!; "
        f"wait $CPID 2>/dev/null; "
        f"kill -TERM $TPID 2>/dev/null; "
        f"exit 0"
    )
    proc = subprocess.Popen(
        ["bash", "-c", timed_wrapper],
        cwd=cwd, env=env,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        start_new_session=True,
    )
    return proc.pid


def _gemini_trusted_dirs() -> list[Path]:
    """Return absolute paths of folders marked TRUST_FOLDER in Gemini config.

    Reads ~/.gemini/trustedFolders.json (or $GEMINI_CLI_HOME/trustedFolders.json
    when set). Missing/malformed file → empty list, which means we'll add
    --skip-trust everywhere. That's the safe default: failing-closed would
    silently break headless calls in any non-home cwd.
    """
    home = Path(os.environ.get("GEMINI_CLI_HOME", str(Path.home() / ".gemini")))
    cfg = home / "trustedFolders.json"
    if not cfg.exists():
        return []
    try:
        data = json.loads(cfg.read_text())
    except (json.JSONDecodeError, OSError):
        return []
    if not isinstance(data, dict):
        return []
    return [Path(p).expanduser().resolve()
            for p, v in data.items()
            if v == "TRUST_FOLDER"]


def _cwd_is_gemini_trusted(cwd: str) -> bool:
    """True if cwd (or any ancestor) is in the trusted-folders list."""
    try:
        cur = Path(cwd).expanduser().resolve()
    except (OSError, ValueError):
        return False
    trusted = _gemini_trusted_dirs()
    if not trusted:
        return False
    for ancestor in [cur, *cur.parents]:
        if ancestor in trusted:
            return True
    return False


def _clean_env() -> dict:
    """Build environment with all conflicting keys removed.

    When the parent Claude is running under a non-default CLAUDE_CONFIG_DIR
    (e.g. ~/.claude-vox), inject matching CODEX_HOME / GEMINI_CLI_HOME so the
    spawned subagent uses the parallel secondary account rather than the
    default one in ~/.codex / ~/.gemini.
    """
    all_unset = set()
    for keys in UNSET_KEYS.values():
        all_unset.update(keys)
    env = {k: v for k, v in os.environ.items() if k not in all_unset}

    suffix = _account_suffix()
    if suffix:
        home = Path.home()
        env.setdefault("CODEX_HOME", str(home / f".codex{suffix}"))
        env.setdefault("GEMINI_CLI_HOME", str(home / f".gemini{suffix}"))
    return env


# ── Command builders ─────────────────────────────────────────────────────────

def build_codex_cmd(prompt: str, model: str, result_file: Path, cwd: str,
                    extra_flags: list[str] | None) -> list[str]:
    """Build the codex exec command."""
    cmd = ["codex", "exec", "--full-auto"]

    # Check if cwd is a git repo; if not, add --skip-git-repo-check
    git_dir = Path(cwd) / ".git"
    if not git_dir.exists() and not git_dir.is_file():
        cmd.append("--skip-git-repo-check")

    cmd.extend(["-m", model])
    cmd.extend(["--output-last-message", str(result_file)])

    if extra_flags:
        cmd.extend(extra_flags)

    cmd.append(prompt)
    return cmd


def build_gemini_cmd(prompt: str, model: str, extra_flags: list[str] | None,
                     cwd: str | None = None) -> list[str]:
    """Build the gemini headless command.

    Defaults to --approval-mode auto_edit: lets Gemini auto-approve
    read/write/edit tools (so web_search, read_file, write_file work in
    headless mode) but does NOT auto-approve shell commands. This is the
    sweet spot for research/OCR/note-taking — Gemini can persist outputs
    without being able to execute arbitrary shell.

    Override via --flags -y / --flags --approval-mode {plan|yolo|...}.
    If extra_flags already specifies an approval mode (or --yolo/-y), we
    skip the default to avoid the "cannot use both" error from gemini CLI.

    Adds --skip-trust automatically when `cwd` isn't under a folder listed
    in ~/.gemini/trustedFolders.json. Gemini CLI ≥0.41 refuses headless
    operation in untrusted cwds (silently downgrades approval mode to
    'default' and then errors out), so without this guard /gemini hangs or
    returns the trust-error message instead of a real response.
    """
    cmd = ["gemini", "-p", prompt, "-m", model, "-o", "text"]

    extra = list(extra_flags) if extra_flags else []
    user_set_mode = any(
        f in ("-y", "--yolo", "--approval-mode") or f.startswith("--approval-mode=")
        for f in extra
    )
    if not user_set_mode:
        cmd.extend(["--approval-mode", "auto_edit"])

    user_set_trust = any(f == "--skip-trust" for f in extra)
    if not user_set_trust and cwd and not _cwd_is_gemini_trusted(cwd):
        cmd.append("--skip-trust")

    cmd.extend(extra)
    return cmd


def _build_shell_cmd(agent: str, agent_cmd: list[str], prompt: str,
                     ticket_id: str = "") -> str:
    """Build shell command string, using temp file + stdin for large prompts.

    For prompts under PROMPT_SIZE_THRESHOLD, quotes the prompt inline
    (existing behavior). For larger prompts, writes to a temp file and
    pipes via stdin to avoid shell argument limits and LaTeX escaping.
    """
    if len(prompt) <= PROMPT_SIZE_THRESHOLD:
        return " ".join(_quote(c) for c in agent_cmd)

    # Write prompt to temp file
    safe_id = re.sub(r"[^a-zA-Z0-9_-]", "_", ticket_id or "prompt")
    prompt_file = Path(f"/tmp/agent_ctl_{safe_id}_{int(time.time())}.md")
    prompt_file.write_text(prompt, encoding="utf-8")

    if agent == "codex":
        # Codex: remove the trailing prompt arg, pipe from file
        # cmd = ["codex", "exec", "--full-auto", ..., prompt]
        cmd_without_prompt = agent_cmd[:-1]
        quoted = " ".join(_quote(c) for c in cmd_without_prompt)
        return f"cat {_quote(str(prompt_file))} | {quoted}"
    else:
        # Gemini: remove the prompt value (index 2) but keep -p flag (index 1).
        # Gemini CLI: -p/--prompt "Appended to input on stdin (if any)."
        # So we pass -p "" and pipe the prompt file to stdin.
        # cmd = ["gemini", "-p", prompt, "-m", model, "-o", "text", "--yolo"]
        cmd_fixed = list(agent_cmd)
        cmd_fixed[2] = ""  # replace prompt text with empty string, keep -p at [1]
        quoted = " ".join(_quote(c) for c in cmd_fixed)
        return f"cat {_quote(str(prompt_file))} | {quoted}"


# ── Commands ─────────────────────────────────────────────────────────────────

def cmd_start(args) -> None:
    state = load_state()
    state = reap_finished(state)

    agent = args.agent
    sid = next_id(state)
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    outfile = OUTPUT_DIR / f"session-{sid}.txt"
    result_file = OUTPUT_DIR / f"session-{sid}-result.md"

    cwd = args.cwd or os.getcwd()
    model = args.model or DEFAULT_MODELS[agent]
    timeout = args.timeout or DEFAULT_TIMEOUT

    # Build agent-specific command. Only codex and gemini are launchable
    # subprocesses — other agents (notably "claude") are executed inline by
    # the orchestrator and should never reach this dispatch. Raising rather
    # than silently falling through to gemini avoids the misroute that
    # produced 404s when claude tickets were dispatched as gemini calls
    # against a `sonnet` model.
    if agent == "codex":
        agent_cmd = build_codex_cmd(prompt=args.prompt, model=model,
                                    result_file=result_file, cwd=cwd,
                                    extra_flags=args.flags)
    elif agent == "gemini":
        agent_cmd = build_gemini_cmd(prompt=args.prompt, model=model,
                                     extra_flags=args.flags, cwd=cwd)
    else:
        sys.exit(
            f"agent-ctl: unknown agent '{agent}'. "
            "Only 'codex' and 'gemini' are launchable via agent-ctl. "
            "Tickets with agent='claude' are executed inline by the "
            "orchestrator (Claude Code) — do not dispatch them here."
        )

    env = _clean_env()
    shell_cmd = _build_shell_cmd(agent, agent_cmd, args.prompt)
    pid = _launch_background(shell_cmd, outfile, timeout, cwd, env)

    state[sid] = {
        "pid": pid,
        "agent": agent,
        "status": "running",
        "model": model,
        "cwd": cwd,
        "prompt": args.prompt[:200],
        "outfile": str(outfile),
        "result_file": str(result_file),
        "timeout": timeout,
        "turn": 1,
        "gemini_uuid": None,  # populated after first turn completes
        "started": datetime.now(timezone.utc).isoformat(),
        "ended": None,
    }
    save_state(state)

    print(f"Session {sid} started ({agent})")
    print(f"  PID:     {pid}")
    print(f"  Model:   {model}")
    print(f"  Timeout: {timeout}s")
    print(f"  Output:  {outfile}")
    print(f"  CWD:     {cwd}")


def cmd_send(args) -> None:
    """Send a follow-up message to an existing session (multi-turn)."""
    state = load_state()
    state = reap_finished(state)

    sid = args.id
    if sid not in state:
        sys.exit(f"Unknown session '{sid}'. Use 'status' to list sessions.")

    meta = state[sid]

    # Session must be done before sending follow-up
    if is_alive(meta["pid"]):
        sys.exit(f"Session {sid} is still running. Wait for it to finish or kill it first.")

    agent = meta["agent"]
    cwd = meta["cwd"]
    model = meta["model"]
    timeout = args.timeout or meta.get("timeout", DEFAULT_TIMEOUT)
    turn = meta.get("turn", 1) + 1

    # For Gemini: capture UUID from previous turn if not yet captured
    if agent == "gemini" and not meta.get("gemini_uuid"):
        uuid = gemini_latest_uuid(cwd)
        if uuid:
            meta["gemini_uuid"] = uuid

    # Build resume command
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    outfile = OUTPUT_DIR / f"session-{sid}.txt"
    result_file = OUTPUT_DIR / f"session-{sid}-result.md"

    # Clear previous output files for this turn
    outfile.write_text("")
    if result_file.exists():
        result_file.write_text("")

    if agent == "gemini":
        uuid = meta.get("gemini_uuid")
        resume_flags = ["--resume", uuid] if uuid else ["-r", "latest"]
        # Reuse build_gemini_cmd so follow-ups keep --approval-mode auto_edit
        # and pick up --skip-trust when needed. Without this, every send-turn
        # silently downgraded to default approval and re-hit the trust check.
        cmd = build_gemini_cmd(prompt=args.msg, model=model,
                               extra_flags=resume_flags, cwd=cwd)
    elif agent == "codex":
        cmd = ["codex", "exec"]
        git_dir = Path(cwd) / ".git"
        if not git_dir.exists() and not git_dir.is_file():
            cmd.append("--skip-git-repo-check")
        cmd.extend(["-m", model])
        cmd.extend(["--output-last-message", str(result_file)])
        cmd.extend(["resume", "--last", args.msg])
    else:
        sys.exit(f"Unknown agent '{agent}'.")

    env = _clean_env()
    shell_cmd = _build_shell_cmd(agent, cmd, args.msg,
                                 ticket_id=f"send_{sid}_t{turn}")
    pid = _launch_background(shell_cmd, outfile, timeout, cwd, env)

    # Update session state
    meta["pid"] = pid
    meta["status"] = "running"
    meta["turn"] = turn
    meta["prompt"] = f"[turn {turn}] {args.msg[:180]}"
    meta["outfile"] = str(outfile)
    meta["result_file"] = str(result_file)
    meta["ended"] = None
    save_state(state)

    print(f"Session {sid} turn {turn} sent ({agent})")
    print(f"  PID:     {pid}")
    print(f"  Model:   {model}")
    print(f"  Timeout: {timeout}s")


def cmd_check(args) -> None:
    state = load_state()
    state = reap_finished(state)
    save_state(state)

    sid = args.id
    if sid not in state:
        sys.exit(f"Unknown session '{sid}'. Use 'status' to list sessions.")

    meta = state[sid]
    alive = is_alive(meta["pid"])
    outfile = Path(meta["outfile"])

    status = "RUNNING" if alive else "DONE"
    start = datetime.fromisoformat(meta["started"])
    delta = datetime.now(timezone.utc) - start
    elapsed = f" ({int(delta.total_seconds())}s elapsed)"

    print(f"[{sid}] {meta['agent'].upper()} {status}{elapsed}")
    print()

    if outfile.exists():
        content = outfile.read_text()
        if content.strip():
            lines = content.strip().splitlines()
            tail = args.tail or 50
            if len(lines) > tail:
                print(f"... ({len(lines) - tail} lines omitted) ...")
            for line in lines[-tail:]:
                print(line)
        else:
            print("(no output yet)")
    else:
        print("(output file not created yet)")


_RESULT_RIPGREP_NOISE = re.compile(
    r"Ripgrep is not available\. Falling back to GrepTool\.\s*"
)


def _clean_result(text: str) -> str:
    """Strip wrapper-induced noise from raw session output.

    `script -q /dev/null` runs the agent inside a pty and replays the
    typescript verbatim — leading `^D` (literal caret+D) plus `\\b`
    backspace characters appear on the first line, line endings are `\\r\\n`,
    and Gemini emits a 'Ripgrep is not available...' diagnostic during
    startup that has nothing to do with the answer. Normalize all of this
    so the user sees just the real response.
    """
    cleaned = text.replace("\r\n", "\n").replace("\r", "\n")
    cleaned = cleaned.lstrip()
    # Leading EOT in either raw (0x04) or printable (^D) form
    if cleaned.startswith("\x04"):
        cleaned = cleaned[1:]
    if cleaned.startswith("^D"):
        cleaned = cleaned[2:]
    # Backspaces emitted by the pty after the EOT marker
    cleaned = cleaned.lstrip("\b")
    cleaned = _RESULT_RIPGREP_NOISE.sub("", cleaned, count=1)
    return cleaned.strip()


def cmd_result(args) -> None:
    state = load_state()
    state = reap_finished(state)
    save_state(state)

    sid = args.id
    if sid not in state:
        sys.exit(f"Unknown session '{sid}'. Use 'status' to list sessions.")

    meta = state[sid]

    # For Codex: prefer --output-last-message result file (clean, no spinner noise)
    result_file = Path(meta.get("result_file", ""))
    if result_file.exists() and result_file.read_text().strip():
        print(_clean_result(result_file.read_text()))
        return

    # Fall back to raw output (also primary path for Gemini, which uses -o text)
    outfile = Path(meta["outfile"])
    if outfile.exists() and outfile.read_text().strip():
        content = _clean_result(outfile.read_text())
        if content:
            print(content)
            return

    if is_alive(meta["pid"]):
        print("(still running — no result yet)")
    else:
        print("(process finished but no output captured)")


def cmd_kill(args) -> None:
    state = load_state()
    sid = args.id
    if sid not in state:
        sys.exit(f"Unknown session '{sid}'. Use 'status' to list sessions.")

    meta = state[sid]
    pid = meta["pid"]

    if not is_alive(pid):
        print(f"Session {sid} already finished.")
        meta["status"] = "done"
        save_state(state)
        return

    # Kill the entire process group
    try:
        pgid = os.getpgid(pid)
        os.killpg(pgid, signal.SIGTERM)
        time.sleep(1)
        if is_alive(pid):
            os.killpg(pgid, signal.SIGKILL)
        print(f"Killed session {sid} (PID {pid}, PGID {pgid})")
    except ProcessLookupError:
        print(f"Session {sid} already exited.")
    except PermissionError:
        try:
            os.kill(pid, signal.SIGTERM)
            print(f"Killed session {sid} (PID {pid})")
        except ProcessLookupError:
            print(f"Session {sid} already exited.")

    meta["status"] = "killed"
    meta["ended"] = datetime.now(timezone.utc).isoformat()
    save_state(state)


def cmd_status(args) -> None:
    state = load_state()
    state = reap_finished(state)
    save_state(state)

    if getattr(args, "json", False):
        # Structured output — stable schema for programmatic routing.
        now = datetime.now(timezone.utc)
        records = []
        for sid, meta in sorted(state.items()):
            status = meta["status"]
            if status == "running" and not is_alive(meta["pid"]):
                status = "done"
                meta["status"] = "done"
            start = datetime.fromisoformat(meta["started"])
            end = datetime.fromisoformat(meta["ended"]) if meta.get("ended") else now
            records.append({
                "id": sid,
                "agent": meta["agent"],
                "status": status,
                "model": meta["model"],
                "cwd": meta.get("cwd", ""),
                "turn": meta.get("turn", 1),
                "started": meta.get("started", ""),
                "ended": meta.get("ended"),
                "elapsed_s": int((end - start).total_seconds()),
                "prompt": meta.get("prompt", ""),
            })
        save_state(state)
        print(json.dumps(records, indent=2))
        return

    if not state:
        print("No sessions.")
        return

    print(f"{'ID':<5} {'AGENT':<8} {'STATUS':<10} {'MODEL':<20} {'TURN':<6} {'ELAPSED':<10} PROMPT")
    print("-" * 110)

    now = datetime.now(timezone.utc)
    for sid, meta in sorted(state.items()):
        status = meta["status"].upper()
        if status == "RUNNING" and not is_alive(meta["pid"]):
            status = "DONE"
            meta["status"] = "done"

        start = datetime.fromisoformat(meta["started"])
        end = datetime.fromisoformat(meta["ended"]) if meta.get("ended") else now
        elapsed = f"{int((end - start).total_seconds())}s"

        turn = str(meta.get("turn", 1))
        prompt = meta.get("prompt", "")[:40]
        print(f"{sid:<5} {meta['agent']:<8} {status:<10} {meta['model']:<20} {turn:<6} {elapsed:<10} {prompt}")

    save_state(state)


def _candidate_sessions(state: dict, agent: str, cwd: str,
                        topic: str | None, max_age_hours: int) -> list[tuple[str, dict]]:
    """Return done sessions matching (agent, cwd), filtered by topic + age,
    sorted most-recent-first. Used by send-or-start to find resumable matches.
    """
    cutoff = datetime.now(timezone.utc) - timedelta(hours=max_age_hours)
    matches = []
    for sid, m in state.items():
        if m.get("agent") != agent:
            continue
        if m.get("cwd") != cwd:
            continue
        if m.get("status") != "done":
            # 'running' sessions can't accept a 'send' yet; 'killed' is dead.
            continue
        try:
            started = datetime.fromisoformat(m.get("started", ""))
        except (TypeError, ValueError):
            continue
        if started < cutoff:
            continue
        if topic:
            haystack = m.get("prompt", "").lower()
            if topic.lower() not in haystack:
                continue
        matches.append((sid, m))
    matches.sort(key=lambda kv: kv[1].get("started", ""), reverse=True)
    return matches


def cmd_send_or_start(args) -> None:
    """Route a message to an existing session if there is a unique match for
    (agent, cwd) within --max-age-hours; otherwise start a new session.

    On multiple matches, exit non-zero with the candidate list so the caller
    (Claude) can ask the user which session to resume — never resume silently.
    """
    state = load_state()
    state = reap_finished(state)

    agent = args.agent
    cwd = args.cwd or os.getcwd()
    topic = getattr(args, "topic", None)
    max_age = getattr(args, "max_age_hours", None) or 168  # 7 days default

    candidates = _candidate_sessions(state, agent, cwd, topic, max_age)

    if not candidates:
        print(f"send-or-start: no matching session ({agent}, cwd={cwd}); starting new.")
        new_args = argparse.Namespace(
            agent=agent, prompt=args.prompt, model=args.model,
            cwd=cwd, timeout=args.timeout, flags=args.flags,
        )
        cmd_start(new_args)
        return

    if len(candidates) == 1 or getattr(args, "latest", False):
        sid, _ = candidates[0]
        print(f"send-or-start: resuming session {sid} ({agent}, cwd={cwd}).")
        send_args = argparse.Namespace(
            id=sid, msg=args.prompt, timeout=args.timeout,
        )
        cmd_send(send_args)
        return

    # Ambiguous — never auto-resolve. Print candidates and exit non-zero so
    # the caller surfaces the choice to the user.
    print(
        f"send-or-start: ambiguous — {len(candidates)} matching sessions "
        f"({agent}, cwd={cwd}):",
        file=sys.stderr,
    )
    print(file=sys.stderr)
    for sid, m in candidates[:10]:
        started = m.get("started", "")[:19]
        prompt = m.get("prompt", "")[:70]
        print(f"  {sid}  turn={m.get('turn', 1)}  {started}  {prompt}", file=sys.stderr)
    print(file=sys.stderr)
    print(
        "Resume one with:  agent-ctl send <id> \"<your message>\"\n"
        "Start fresh with: agent-ctl start <agent> \"<your message>\"\n"
        "Auto-pick latest: agent-ctl send-or-start ... --latest",
        file=sys.stderr,
    )
    sys.exit(2)


def cmd_wait(args) -> None:
    """Block until one or more sessions finish.

    With --max-wait <s>, return early (exit 2) if not all sessions are done
    within that bound. Callers (Claude Code Bash tool defaults to 120s,
    max 600s) can use this to poll without busting their own timeout: pick
    --max-wait below the Bash cap, then re-call until done.
    """
    state = load_state()
    sids = args.ids
    poll_interval = 5
    max_wait = getattr(args, "max_wait", None)
    deadline = time.time() + max_wait if max_wait else None

    # Validate all session IDs exist
    for sid in sids:
        if sid not in state:
            print(f"Session {sid} not found.")
            sys.exit(1)

    pending = set(sids)
    while pending:
        state = load_state()
        state = reap_finished(state)
        save_state(state)
        done = set()
        for sid in pending:
            meta = state.get(sid, {})
            if not is_alive(meta.get("pid", -1)):
                done.add(sid)
                started = meta.get("started", 0)
                if isinstance(started, str):
                    started = datetime.fromisoformat(started).timestamp()
                elapsed = int(time.time() - started)
                agent = meta.get("agent", "?")
                print(f"[{sid}] {agent} finished ({elapsed}s)")
        pending -= done
        if not pending:
            break
        if deadline is not None and time.time() >= deadline:
            for sid in sorted(pending):
                meta = state.get(sid, {})
                started = meta.get("started", 0)
                if isinstance(started, str):
                    started = datetime.fromisoformat(started).timestamp()
                elapsed = int(time.time() - started)
                agent = meta.get("agent", "?")
                print(f"[{sid}] {agent} still running ({elapsed}s)")
            print(f"max-wait exceeded; still pending: {', '.join(sorted(pending))}")
            sys.exit(2)
        time.sleep(poll_interval)

    print(f"All sessions complete: {', '.join(sids)}")


# ── DAG runner ────────────────────────────────────────────────────────────────

def _load_tickets(path: Path) -> dict:
    """Load tickets.json as a dict {ticket_id: ticket}."""
    data = json.loads(path.read_text())
    if isinstance(data, list):
        return {t["id"]: t for t in data}
    return data.get("tickets", data)


def _save_tickets(path: Path, tickets: dict) -> None:
    """Persist tickets atomically. Preserves order by id."""
    ordered = {k: tickets[k] for k in sorted(tickets.keys())}
    tmp = path.with_suffix(".tmp")
    tmp.write_text(json.dumps(ordered, indent=2))
    tmp.replace(path)


def _ticket_ready(ticket: dict, tickets: dict) -> bool:
    """A ticket is ready if pending and all deps are done.

    Claude-typed tickets are executed inline by Claude Code (the orchestrator),
    not by run-dag. Skip them so they aren't misrouted through the Gemini CLI.
    """
    if ticket.get("status") != "pending":
        return False
    if ticket.get("agent") == "claude":
        return False
    for dep_id in ticket.get("depends_on", []):
        dep = tickets.get(dep_id)
        if not dep or dep.get("status") != "done":
            return False
    return True


def _outputs_exist(ticket: dict, cwd: str) -> bool:
    """Verify that every declared output path exists and is non-empty."""
    for out in ticket.get("outputs", []):
        p = Path(out)
        if not p.is_absolute():
            p = Path(cwd) / p
        if not p.exists():
            return False
        # For directories, require at least one file inside
        if p.is_dir():
            if not any(p.iterdir()):
                return False
        else:
            if p.stat().st_size == 0:
                return False
    return True


def _clean_json_text(raw: str) -> str:
    """Clean raw text for JSON parsing.

    Fixes common issues from Gemini's write_file output:
    - Control characters embedded in strings (from LaTeX in paper text)
    - Invalid backslash escapes (\\p, \\a, \\L, etc. from LaTeX notation)
    - Runaway backslash chains from the previous iterative cleaner
    - Trailing commas in arrays/objects

    Strategy: two-pass. First normalize any run of 2+ backslashes down to
    exactly two (one literal backslash in JSON). This kills the runaway
    `\\\\\\\\\\sum` patterns that the prior cleaner would produce by
    repeatedly doubling. Then double up any *remaining* lone backslashes
    that precede an invalid JSON escape character, using a negative
    lookbehind so we don't disturb already-escaped pairs.
    """
    cleaned = raw
    # Strip control chars except newline, carriage return, tab
    cleaned = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f]", "", cleaned)
    # Pass 1: collapse runs of 2+ backslashes to exactly 2.
    cleaned = re.sub(r"\\{2,}", r"\\\\", cleaned)
    # Pass 2: any remaining bare backslash followed by an invalid escape
    # char gets doubled. Negative lookbehind ensures we don't touch
    # backslashes that are already escaped.
    for _ in range(3):
        fixed = re.sub(r'(?<!\\)\\(?!["\\/bfnrtu])', r'\\\\', cleaned)
        if fixed == cleaned:
            break
        cleaned = fixed
    # Trailing commas
    cleaned = re.sub(r",\s*([}\]])", r"\1", cleaned)
    return cleaned


def _salvage_stdout_json(ticket: dict, session: dict, cwd: str) -> bool:
    """Salvage JSON output from a session's stdout log and write it to the
    ticket's first declared output path. Used for agents (like Gemini) that
    cannot write files directly. Returns True on success.

    Strategy: find ALL fenced ```json {...} ``` blocks, take the largest one
    (the final output, not intermediate tool calls). Falls back to finding
    the outermost { ... } pair. Cleans control characters and trailing commas
    before parsing.
    """
    outputs = ticket.get("outputs", [])
    if not outputs:
        return False
    out_path = Path(outputs[0])
    if not out_path.is_absolute():
        out_path = Path(cwd) / out_path
    if out_path.exists() and out_path.stat().st_size > 0:
        return True  # already present

    outfile = session.get("outfile")
    if not outfile or not Path(outfile).exists():
        return False
    text = Path(outfile).read_text(errors="replace")

    raw = None

    # Strategy 1: find ALL fenced ```json ... ``` blocks, take the largest
    matches = re.findall(r"```json\s*(\{.*?\})\s*```", text, re.DOTALL)
    if matches:
        # Sort by length descending, try each until one parses
        for candidate in sorted(matches, key=len, reverse=True):
            cleaned = _clean_json_text(candidate)
            try:
                json.loads(cleaned)
                raw = cleaned
                break
            except json.JSONDecodeError:
                continue

    # Strategy 2: find the outermost { ... } that balances
    if not raw:
        start = text.find("{")
        end = text.rfind("}")
        if 0 <= start < end:
            candidate = _clean_json_text(text[start:end + 1])
            try:
                json.loads(candidate)
                raw = candidate
            except json.JSONDecodeError:
                raw = None

    if not raw:
        return False

    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        return False

    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(data, indent=2))
    return True


def _archive_session_log(ticket: dict, session: dict, tickets_dir: Path) -> bool:
    """Copy a session's raw output log into the DAG's sessions/ archive so
    the agent's reasoning trace is preserved forever. Destination is:
        <tickets_dir>/sessions/<ticket_id>.log

    Where <tickets_dir> is the parent directory of tickets.json. This makes
    the archive location a pure convention — no ticket field needed.

    Returns True on success.
    """
    outfile = session.get("outfile")
    if not outfile or not Path(outfile).exists():
        return False
    archive_dir = tickets_dir / "sessions"
    archive_dir.mkdir(parents=True, exist_ok=True)
    archive_path = archive_dir / f"{ticket['id']}.log"
    try:
        shutil.copy2(outfile, archive_path)
        return True
    except (OSError, shutil.Error):
        return False


def _launch_ticket(ticket: dict, cwd: str, state: dict) -> str:
    """Launch a ticket as an agent-ctl session. Returns session ID."""
    agent = ticket["agent"]
    prompt_path = ticket.get("prompt_path")
    if prompt_path:
        pp = Path(prompt_path)
        if not pp.is_absolute():
            pp = Path(cwd) / pp
        prompt = pp.read_text()
    else:
        prompt = ticket.get("prompt", "")

    if not prompt:
        raise ValueError(f"Ticket {ticket['id']} has no prompt or prompt_path")

    timeout = ticket.get("timeout_s", DEFAULT_TIMEOUT)
    model = ticket.get("model") or DEFAULT_MODELS[agent]
    ticket_cwd = ticket.get("cwd", cwd)

    sid = next_id(state)
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    outfile = OUTPUT_DIR / f"session-{sid}.txt"
    result_file = OUTPUT_DIR / f"session-{sid}-result.md"

    if agent == "codex":
        agent_cmd = build_codex_cmd(prompt=prompt, model=model,
                                    result_file=result_file, cwd=ticket_cwd,
                                    extra_flags=None)
    else:
        agent_cmd = build_gemini_cmd(prompt=prompt, model=model,
                                     extra_flags=None, cwd=ticket_cwd)

    env = _clean_env()
    shell_cmd = _build_shell_cmd(agent, agent_cmd, prompt,
                                 ticket_id=ticket["id"])
    pid = _launch_background(shell_cmd, outfile, timeout, ticket_cwd, env)

    state[sid] = {
        "pid": pid,
        "agent": agent,
        "status": "running",
        "model": model,
        "cwd": ticket_cwd,
        "prompt": prompt[:200],
        "outfile": str(outfile),
        "result_file": str(result_file),
        "timeout": timeout,
        "turn": 1,
        "gemini_uuid": None,
        "started": datetime.now(timezone.utc).isoformat(),
        "ended": None,
        "ticket_id": ticket["id"],
    }
    save_state(state)
    return sid


def cmd_run_dag(args) -> None:
    """Execute a ticket DAG until no more ready tickets remain."""
    tickets_path = Path(args.tickets).resolve()
    if not tickets_path.exists():
        sys.exit(f"Tickets file not found: {tickets_path}")

    cwd = args.cwd or str(tickets_path.parent)
    tickets_dir = tickets_path.parent
    max_concurrent = args.concurrent
    poll_interval = 5

    print(f"Running DAG: {tickets_path}")
    print(f"  CWD: {cwd}")
    print(f"  Max concurrent: {max_concurrent}")
    print()

    while True:
        tickets = _load_tickets(tickets_path)
        state = load_state()
        state = reap_finished(state)
        save_state(state)

        # Finalize tickets whose sessions have finished
        finalized = 0
        for tid, ticket in tickets.items():
            if ticket.get("status") != "running":
                continue
            sid = ticket.get("session_id")
            if not sid or sid not in state:
                continue
            sess = state[sid]
            if sess.get("status") == "done":
                # Try to fix JSON files that exist but have encoding issues
                # (common with Gemini's write_file embedding raw LaTeX).
                for out in ticket.get("outputs", []):
                    p = Path(out) if Path(out).is_absolute() else Path(cwd) / out
                    if p.exists() and p.suffix == ".json" and p.stat().st_size > 0:
                        try:
                            json.loads(p.read_text())
                        except (json.JSONDecodeError, UnicodeDecodeError):
                            raw = p.read_text(errors="replace")
                            cleaned = _clean_json_text(raw)
                            try:
                                data = json.loads(cleaned)
                                p.write_text(json.dumps(data, indent=2))
                                print(f"[{tid}] fixed JSON encoding in {p.name}")
                            except json.JSONDecodeError:
                                pass  # will be caught by _outputs_exist

                # If the ticket declares json_stdout fallback, try to salvage
                # stdout content into the first output path when the file is
                # missing. This is required for agents like Gemini that cannot
                # write files directly (or when write_file fails).
                if (not _outputs_exist(ticket, cwd)
                        and ticket.get("output_format") == "json_stdout"):
                    if _salvage_stdout_json(ticket, sess, cwd):
                        print(f"[{tid}] salvaged json_stdout output")

                # Archive the session log into sessions/<ticket_id>.log so
                # the agent's reasoning trace is preserved forever. Runs on
                # both success and failure so failed attempts are auditable.
                if _archive_session_log(ticket, sess, tickets_dir):
                    print(f"[{tid}] archived session log")

                if _outputs_exist(ticket, cwd):
                    ticket["status"] = "done"
                    ticket["finished_at"] = datetime.now(timezone.utc).isoformat()
                    print(f"[{tid}] done")
                    finalized += 1
                else:
                    # Before deciding whether to retry, sniff the session log
                    # for hard-stop conditions that retrying cannot fix.
                    agent = ticket.get("agent", "")
                    outfile = sess.get("outfile", "")
                    log_text = ""
                    if outfile and Path(outfile).exists():
                        log_text = Path(outfile).read_text(errors="replace")

                    # Gemini OAuth expired silently. Retrying just produces
                    # the same FatalCancellationError. Halt the whole DAG
                    # with an actionable message so the user can re-auth.
                    if agent == "gemini" and (
                        "FatalCancellationError" in log_text
                        or "Authentication cancelled" in log_text
                        or "Opening authentication page" in log_text
                    ):
                        _save_tickets(tickets_path, tickets)
                        sys.exit(
                            f"\n[{tid}] Gemini OAuth has expired or was "
                            f"cancelled.\n\n"
                            f"  Session log: {outfile}\n\n"
                            f"  Fix: open a terminal and run\n"
                            f"      gemini -p 'ping'\n"
                            f"  to trigger the OAuth flow. Once you have "
                            f"signed in, re-run this skill — the DAG will "
                            f"resume from the failed ticket."
                        )

                    attempt = ticket.get("attempt", 0) + 1
                    max_att = ticket.get("max_attempts", 2)
                    if attempt < max_att:
                        ticket["status"] = "pending"
                        ticket["attempt"] = attempt
                        ticket.pop("session_id", None)

                        # If Gemini hit 429s, fall back to a more available model
                        if agent == "gemini" and agent in FALLBACK_MODELS:
                            if log_text and (
                                "MODEL_CAPACITY_EXHAUSTED" in log_text
                                or log_text.count("429") > 5
                            ):
                                fallback = FALLBACK_MODELS[agent]
                                ticket["model"] = fallback
                                print(f"[{tid}] 429 capacity exhaustion detected, falling back to {fallback}")

                        # Backoff delay before retry to avoid hammering
                        # rate-limited APIs (e.g., Gemini 429s)
                        delay = min(30 * attempt, 120)
                        print(f"[{tid}] outputs missing, retry {attempt}/{max_att} (backoff {delay}s)")
                        time.sleep(delay)
                    else:
                        ticket["status"] = "failed"
                        ticket["finished_at"] = datetime.now(timezone.utc).isoformat()
                        ticket["failure_reason"] = "outputs missing after max attempts"
                        print(f"[{tid}] FAILED (outputs missing)")
                    finalized += 1
        if finalized:
            _save_tickets(tickets_path, tickets)

        # Count current running
        running = [t for t in tickets.values() if t.get("status") == "running"]
        ready = [t for t in tickets.values() if _ticket_ready(t, tickets)]

        # Check for completion
        terminal = ("done", "failed")
        unfinished = [t for t in tickets.values()
                      if t.get("status") not in terminal]
        if not unfinished:
            print()
            n_done = sum(1 for t in tickets.values() if t.get("status") == "done")
            n_failed = sum(1 for t in tickets.values() if t.get("status") == "failed")
            print(f"DAG complete: {n_done} done, {n_failed} failed")
            return

        # If nothing ready and nothing running, we are stuck
        if not ready and not running:
            stuck = [t["id"] for t in tickets.values()
                     if t.get("status") == "pending"]
            print()
            print(f"DAG stuck: {len(stuck)} pending tickets with unmet dependencies")
            for tid in stuck:
                deps = tickets[tid].get("depends_on", [])
                missing = [d for d in deps
                           if tickets.get(d, {}).get("status") != "done"]
                print(f"  {tid}: waiting on {missing}")
            return

        # Launch new tickets up to concurrency cap
        slots = max_concurrent - len(running)
        launched = 0
        for ticket in ready[:slots]:
            try:
                sid = _launch_ticket(ticket, cwd, state)
            except Exception as e:
                ticket["status"] = "failed"
                ticket["failure_reason"] = f"launch error: {e}"
                print(f"[{ticket['id']}] LAUNCH FAILED: {e}")
                continue
            ticket["status"] = "running"
            ticket["session_id"] = sid
            ticket["started_at"] = datetime.now(timezone.utc).isoformat()
            print(f"[{ticket['id']}] launched (session {sid})")
            launched += 1
        if launched:
            _save_tickets(tickets_path, tickets)

        # Sleep only if we launched nothing new (otherwise loop immediately)
        if launched == 0 and running:
            time.sleep(poll_interval)


def cmd_dag_status(args) -> None:
    """Print a progress view of a ticket DAG."""
    tickets_path = Path(args.tickets).resolve()
    if not tickets_path.exists():
        sys.exit(f"Tickets file not found: {tickets_path}")

    tickets = _load_tickets(tickets_path)
    by_status = {"pending": [], "running": [], "done": [], "failed": []}
    for tid, ticket in sorted(tickets.items()):
        st = ticket.get("status", "pending")
        by_status.setdefault(st, []).append(ticket)

    total = len(tickets)
    print(f"DAG: {tickets_path}")
    print(f"Total tickets: {total}")
    for st in ("done", "running", "pending", "failed"):
        count = len(by_status.get(st, []))
        print(f"  {st:8s}: {count}")
    print()

    header = f"{'ID':<40s} {'STATUS':<10s} {'AGENT':<8s} {'DEPS':<20s}"
    print(header)
    print("-" * len(header))
    for tid, ticket in sorted(tickets.items()):
        deps = ",".join(ticket.get("depends_on", [])) or "-"
        if len(deps) > 18:
            deps = deps[:15] + "..."
        print(f"{tid:<40s} {ticket.get('status','pending'):<10s} "
              f"{ticket.get('agent','-'):<8s} {deps:<20s}")


def cmd_cleanup(args) -> None:
    state = load_state()

    agent_filter = getattr(args, "agent", None)

    # Kill running sessions (optionally filtered by agent)
    killed = 0
    for sid, meta in state.items():
        if agent_filter and meta.get("agent") != agent_filter:
            continue
        if is_alive(meta["pid"]):
            try:
                pgid = os.getpgid(meta["pid"])
                os.killpg(pgid, signal.SIGTERM)
                killed += 1
            except (ProcessLookupError, PermissionError):
                pass

    # Also find and kill orphaned agent processes
    patterns = []
    if not agent_filter or agent_filter == "codex":
        patterns.append("codex exec")
    if not agent_filter or agent_filter == "gemini":
        patterns.append("gemini -p")

    for pattern in patterns:
        try:
            result = subprocess.run(
                ["pgrep", "-f", pattern],
                capture_output=True, text=True
            )
            for line in result.stdout.strip().splitlines():
                pid = int(line.strip())
                try:
                    os.kill(pid, signal.SIGTERM)
                    killed += 1
                except (ProcessLookupError, PermissionError):
                    pass
        except (FileNotFoundError, ValueError):
            pass

    # Clear state and output files
    if agent_filter:
        # Only clear sessions for the specified agent
        state = {k: v for k, v in state.items() if v.get("agent") != agent_filter}
        save_state(state)
    else:
        save_state({})

    if OUTPUT_DIR.exists():
        for f in OUTPUT_DIR.glob("session-*"):
            f.unlink(missing_ok=True)

    label = agent_filter or "all agents"
    print(f"Killed {killed} processes for {label}, cleared sessions and output files.")


# ── Helpers ──────────────────────────────────────────────────────────────────

def _quote(s: str) -> str:
    """Shell-quote a string."""
    if not s or any(c in s for c in " \t\n\"'\\$`!#&|;(){}[]<>?*~"):
        return "'" + s.replace("'", "'\"'\"'") + "'"
    return s


# ── CLI ──────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="agent-ctl: Non-blocking controller for Codex and Gemini CLI sessions"
    )
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_start = sub.add_parser("start", help="Start a new agent session")
    p_start.add_argument("agent", choices=["codex", "gemini"], help="Agent to use")
    p_start.add_argument("prompt", help="The prompt to send")
    p_start.add_argument("-m", "--model", help="Model override")
    p_start.add_argument("--cwd", help="Working directory")
    p_start.add_argument("--timeout", type=int, help=f"Timeout in seconds (default: {DEFAULT_TIMEOUT})")
    p_start.add_argument("--flags", nargs=argparse.REMAINDER,
                         help="Extra flags to pass to the agent CLI")

    p_send = sub.add_parser("send", help="Send a follow-up to an existing session")
    p_send.add_argument("id", help="Session ID")
    p_send.add_argument("msg", help="Follow-up message")
    p_send.add_argument("--timeout", type=int, help="Timeout override for this turn")

    p_check = sub.add_parser("check", help="Check progress of a session")
    p_check.add_argument("id", help="Session ID")
    p_check.add_argument("--tail", type=int, default=50, help="Lines to show (default: 50)")

    p_result = sub.add_parser("result", help="Get final result of a session")
    p_result.add_argument("id", help="Session ID")

    p_kill = sub.add_parser("kill", help="Kill a running session")
    p_kill.add_argument("id", help="Session ID")

    p_status = sub.add_parser("status", help="Show all sessions")
    p_status.add_argument("--json", action="store_true",
                          help="Emit machine-readable JSON instead of a table")

    p_sos = sub.add_parser(
        "send-or-start",
        help="Resume a unique matching session if one exists, else start new",
    )
    p_sos.add_argument("agent", choices=["codex", "gemini"])
    p_sos.add_argument("prompt")
    p_sos.add_argument("-m", "--model", help="Model override (start path only)")
    p_sos.add_argument("--cwd", help="Working directory (defaults to $PWD)")
    p_sos.add_argument("--timeout", type=int)
    p_sos.add_argument("--topic",
                       help="Substring filter on stored prompt for matching")
    p_sos.add_argument("--max-age-hours", type=int, default=168,
                       help="Only consider sessions younger than this (default: 168 = 7d)")
    p_sos.add_argument("--latest", action="store_true",
                       help="On ambiguity, pick the most recent match instead of failing")
    p_sos.add_argument("--flags", nargs=argparse.REMAINDER,
                       help="Extra flags forwarded to start path")

    p_wait = sub.add_parser("wait", help="Block until sessions finish")
    p_wait.add_argument("ids", nargs="+", help="Session IDs to wait for")
    p_wait.add_argument("--max-wait", type=int, default=None,
                        help="Max seconds to wait before printing "
                             "'still running' and exiting 2 (lets callers "
                             "poll without busting their own timeout)")

    p_rundag = sub.add_parser("run-dag", help="Execute a ticket DAG until no ready tickets remain")
    p_rundag.add_argument("tickets", help="Path to tickets.json")
    p_rundag.add_argument("--cwd", help="Working directory for ticket execution (default: tickets.json parent)")
    p_rundag.add_argument("--concurrent", type=int, default=3,
                          help="Max concurrent running tickets (default: 3)")

    p_dagstatus = sub.add_parser("dag-status", help="Show progress of a ticket DAG")
    p_dagstatus.add_argument("tickets", help="Path to tickets.json")

    p_cleanup = sub.add_parser("cleanup", help="Kill sessions and clear state")
    p_cleanup.add_argument("--agent", choices=["codex", "gemini"],
                           help="Only clean up sessions for this agent")

    args = parser.parse_args()

    if args.cmd == "start":
        cmd_start(args)
    elif args.cmd == "send":
        cmd_send(args)
    elif args.cmd == "check":
        cmd_check(args)
    elif args.cmd == "result":
        cmd_result(args)
    elif args.cmd == "kill":
        cmd_kill(args)
    elif args.cmd == "status":
        cmd_status(args)
    elif args.cmd == "wait":
        cmd_wait(args)
    elif args.cmd == "run-dag":
        cmd_run_dag(args)
    elif args.cmd == "dag-status":
        cmd_dag_status(args)
    elif args.cmd == "send-or-start":
        cmd_send_or_start(args)
    elif args.cmd == "cleanup":
        cmd_cleanup(args)


if __name__ == "__main__":
    main()
