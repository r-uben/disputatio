#!/usr/bin/env python3
"""
agent-ctl: Non-blocking controller for Codex and Gemini CLI sessions.

Lets Claude Code start, monitor, and kill agent processes without blocking.
Uses `script -q` on macOS to defeat output buffering so progress is visible
in real time. Supports multi-turn sessions via `send`.

Subcommands:
    start   <agent> "prompt" [--model M] [--cwd /path] [--timeout S] [--flags ...]
    send    <id> "follow-up message" [--timeout S]
    check   <id> [--tail N]
    result  <id>
    kill    <id>
    status
    cleanup [--agent <agent>]

Launchable agents are defined in the AGENTS registry (see `class AgentSpec`).
Adding a new agent is one build_<name>_cmd function plus one AGENTS entry.
"""

import argparse
import contextlib
import fcntl
import json
import os
import re
import shutil
import signal
import subprocess
import sys
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable

STATE_FILE = Path.home() / ".claude" / "agent-sessions.json"
OUTPUT_DIR = Path("/tmp/agent-ctl")

# Per-agent defaults (models, OAuth-conflicting env vars, fallback on 429)
# live on each AgentSpec in the AGENTS registry below. See `class AgentSpec`
# and adding-agents.md for how to register a new agent.

# Default timeout (seconds) — 5 minutes
DEFAULT_TIMEOUT = 300

# Prompts larger than this are written to a temp file and piped via stdin
# to avoid shell argument limits and special-char escaping issues.
PROMPT_SIZE_THRESHOLD = 10240  # 10 KB


# ── State helpers ────────────────────────────────────────────────────────────

_LOCK_FILE = STATE_FILE.with_suffix(".lock")


@contextlib.contextmanager
def _state_lock():
    """Hold an advisory exclusive lock on ~/.claude/agent-sessions.lock
    for the duration of state read+write. Concurrent agent-ctl
    invocations (start, run-dag, status, cleanup) serialise here
    instead of racing on next_id() and clobbering each other's
    session entries on save_state(). Lock file is per-user; the
    state file is also per-user, so cross-user races do not arise."""
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(_LOCK_FILE, "w") as fh:
        fcntl.flock(fh.fileno(), fcntl.LOCK_EX)
        try:
            yield
        finally:
            fcntl.flock(fh.fileno(), fcntl.LOCK_UN)


def load_state() -> dict:
    """Read the state file. Callers that mutate must hold _state_lock()
    and use save_state(). Single read-only callers (status, check) can
    skip the lock; they may see a momentary stale read but never
    corruption because save_state() writes atomically."""
    if STATE_FILE.exists():
        try:
            return json.loads(STATE_FILE.read_text())
        except json.JSONDecodeError:
            return {}
    return {}


def save_state(state: dict) -> None:
    """Write the state file atomically: write to a sibling temp path
    and rename over the target. POSIX rename is atomic on the same
    filesystem, so a concurrent reader either sees the old file or
    the new one — never a half-written one."""
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    tmp = STATE_FILE.with_suffix(".tmp")
    tmp.write_text(json.dumps(state, indent=2))
    tmp.replace(STATE_FILE)


def next_id(state: dict) -> str:
    """Return next sequential session ID like '01', '02', ...

    Caller must hold _state_lock() between this call and the
    subsequent save_state(state), otherwise two concurrent starts
    can compute the same ID and clobber each other.
    """
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


def _all_unset_keys() -> set[str]:
    """Union of env vars to strip across every registered agent."""
    keys: set[str] = set()
    for spec in AGENTS.values():
        keys.update(spec.unset_env_keys)
    return keys


def gemini_latest_uuid(cwd: str) -> str | None:
    """Return the UUID of the most recently created Gemini session."""
    env = {k: v for k, v in os.environ.items() if k not in _all_unset_keys()}

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
    """Launch a command in background with timeout. Returns PID."""
    wrapper = (
        f"script -q /dev/null {shell_cmd} > {_quote(str(outfile))} 2>&1"
    )
    timed_wrapper = (
        f"( {wrapper} ) & CPID=$!; "
        f"( sleep {timeout} && kill -TERM $CPID 2>/dev/null ) & TPID=$!; "
        f"wait $CPID 2>/dev/null; kill -TERM $TPID 2>/dev/null; exit 0"
    )
    proc = subprocess.Popen(
        ["bash", "-c", timed_wrapper],
        cwd=cwd, env=env,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        start_new_session=True,
    )
    return proc.pid


def _clean_env() -> dict:
    """Build environment with all conflicting keys removed."""
    return {k: v for k, v in os.environ.items() if k not in _all_unset_keys()}


# ── Command builders ─────────────────────────────────────────────────────────

def build_codex_cmd(prompt: str, model: str, result_file: Path, cwd: str,
                    extra_flags: list[str] | None,
                    flags: dict | None = None,
                    **_unused) -> list[str]:
    """Build the codex exec command.

    Known flag translations from `flags`:
      - reasoning_effort -> -c model_reasoning_effort=<value>
    Unknown keys in flags warn and are ignored.

    NOTE on stdin rewriting: `prompt` MUST stay as the trailing
    positional argument so _codex_stdin_rewrite (which drops the last
    element when piping) keeps working. Do not append flags AFTER the
    prompt.
    """
    cmd = ["codex", "exec", "--full-auto"]

    # Check if cwd is a git repo; if not, add --skip-git-repo-check
    git_dir = Path(cwd) / ".git"
    if not git_dir.exists() and not git_dir.is_file():
        cmd.append("--skip-git-repo-check")

    cmd.extend(["-m", model])
    cmd.extend(["--output-last-message", str(result_file)])

    flags = flags or {}
    if "reasoning_effort" in flags:
        cmd.extend(["-c", f"model_reasoning_effort={flags['reasoning_effort']}"])

    for key in flags:
        if key not in {"reasoning_effort"}:
            print(
                f"agent-ctl: codex ignoring unknown flag {key!r} "
                f"(promote to a translation in build_codex_cmd if load-bearing)",
                file=sys.stderr,
            )

    if extra_flags:
        cmd.extend(extra_flags)

    cmd.append(prompt)  # MUST stay last — see docstring
    return cmd


def build_gemini_cmd(prompt: str, model: str,
                     extra_flags: list[str] | None = None,
                     **_unused) -> list[str]:
    """Build the gemini headless command.

    Always passes --yolo so Gemini can write files directly via write_file
    tool. Without --yolo, Gemini blocks on tool approval in headless mode
    and falls back to dumping JSON to stdout.

    Accepts extra kwargs (result_file, cwd) for signature uniformity with
    other build_*_cmd functions in the AGENTS registry, but ignores them.
    """
    cmd = ["gemini", "-p", prompt, "-m", model, "-o", "text", "--yolo"]

    if extra_flags:
        cmd.extend(extra_flags)

    return cmd


# ── Per-agent stdin rewriters ────────────────────────────────────────────────
#
# When a prompt exceeds PROMPT_SIZE_THRESHOLD it is piped via stdin from a
# temp file instead of passed as a shell argument. Each agent's CLI has a
# different expectation for what the command looks like when the prompt is
# on stdin, so each AgentSpec carries its own rewriter.

def _codex_stdin_rewrite(cmd: list[str]) -> list[str]:
    """Codex takes the prompt as a trailing positional; drop it when piping."""
    return cmd[:-1]


def _gemini_stdin_rewrite(cmd: list[str]) -> list[str]:
    """Gemini takes the prompt as `-p <text>`; keep the flag, blank the value.

    `-p/--prompt` is documented as "appended to input on stdin (if any)",
    so setting `-p ""` and piping the file to stdin makes Gemini treat the
    piped content as the prompt.
    """
    fixed = list(cmd)
    fixed[2] = ""
    return fixed


def build_opencode_cmd(prompt: str, model: str,
                       extra_flags: list[str] | None = None,
                       flags: dict | None = None,
                       **_unused) -> list[str]:
    """Build the opencode run command.

    `opencode run --prompt <text> -m <provider>/<model> [extra]` is the
    non-interactive entry point. Model is REQUIRED in disputatio usage
    (never rely on the default) so the caller supplies it explicitly.

    Known flag translations from `flags`:
      - agent            -> --agent <name>
      - log_level        -> --log-level <debug|info|warn|error>
      - pure             -> --pure (bool)
    Unknown keys produce a stderr warning and are ignored. Promote to
    explicit translations here when a flag proves load-bearing.

    See templates/agents/opencode.md for ticket shape and conventions.
    """
    cmd = ["opencode", "run", "--prompt", prompt, "-m", model]

    flags = flags or {}
    if "agent" in flags:
        cmd.extend(["--agent", str(flags["agent"])])
    if "log_level" in flags:
        cmd.extend(["--log-level", str(flags["log_level"])])
    if flags.get("pure"):
        cmd.append("--pure")

    for key in flags:
        if key not in {"agent", "log_level", "pure"}:
            print(
                f"agent-ctl: opencode ignoring unknown flag {key!r} "
                f"(promote to a translation in build_opencode_cmd if load-bearing)",
                file=sys.stderr,
            )

    if extra_flags:
        cmd.extend(extra_flags)

    return cmd


def _opencode_stdin_rewrite(cmd: list[str]) -> list[str]:
    """OpenCode takes the prompt as `--prompt <text>` at indices 2-3;
    drop both and pipe the prompt on stdin instead."""
    return [c for i, c in enumerate(cmd) if i not in (2, 3)]


def build_ollama_cmd(prompt: str, model: str,
                     extra_flags: list[str] | None = None,
                     flags: dict | None = None,
                     **_unused) -> list[str]:
    """Build the ollama run command.

    `ollama run <model> "<prompt>"` runs a local model in one shot.
    Large prompts are piped on stdin; see _ollama_stdin_rewrite.

    Ollama expects per-call options via `--options key=value` pairs or
    a JSON object. For simplicity we currently support:
      - temperature   -> --options temperature=<float>
      - num_ctx       -> --options num_ctx=<int>
      - num_predict   -> --options num_predict=<int>

    Unknown keys warn and are ignored. See templates/agents/ollama.md
    for ticket conventions and preflight checks.
    """
    cmd = ["ollama", "run", model, prompt]

    flags = flags or {}
    ollama_opts = {}
    for key in ("temperature", "num_ctx", "num_predict"):
        if key in flags:
            ollama_opts[key] = flags[key]
    for key, value in ollama_opts.items():
        cmd.extend(["--options", f"{key}={value}"])

    for key in flags:
        if key not in {"temperature", "num_ctx", "num_predict"}:
            print(
                f"agent-ctl: ollama ignoring unknown flag {key!r} "
                f"(promote to a translation in build_ollama_cmd if load-bearing)",
                file=sys.stderr,
            )

    if extra_flags:
        cmd.extend(extra_flags)

    return cmd


def _ollama_stdin_rewrite(cmd: list[str]) -> list[str]:
    """Ollama takes the prompt as a trailing positional arg; drop it
    and pipe from stdin instead. `ollama run` treats stdin as the
    prompt when the positional is absent."""
    # Prompt is always at cmd[3] because cmd = ["ollama", "run", model, prompt, ...opts]
    return [c for i, c in enumerate(cmd) if i != 3]


# ── AgentSpec registry ───────────────────────────────────────────────────────
#
# Adding a new launchable agent is now a matter of writing one build_<name>_cmd
# function (and a stdin rewriter if the CLI has a non-trivial prompt shape)
# and adding one AgentSpec entry below. Dispatch sites look up the spec by
# name and call spec.build_cmd / spec.stdin_rewrite — no new if/elif branches.
#
# `implicit_family` marks transports whose family is fixed by the CLI
# itself (codex always hits OpenAI, gemini always hits Google). The
# orchestrator still writes `family` into every ticket for schema
# uniformity, but the launcher can fill it in from the spec if the
# ticket omits it. Gateway transports (opencode, ollama) leave this
# None; their tickets MUST carry family.
#
# `supports_multi_turn` gates cmd_send. Transports that set False are
# refused explicitly instead of silently falling through to hardcoded
# resume logic.
#
# `inline_only=True` marks agents the orchestrator (Claude Code) runs
# itself rather than through agent-ctl. These must never reach the
# launch path — the old else-fallthrough misrouted claude tickets to
# Gemini with a sonnet model ID, producing 404s.
#
# Per-CLI behavior (invocation, model-string conventions, flag
# translation) is documented in markdown under templates/agents/,
# because Claude-as-orchestrator reads those files at emit time to
# pick the right family and model for each ticket. See
# docs/transport-model-family.md for why the semantics live there
# rather than in this file.

@dataclass(frozen=True)
class AgentSpec:
    name: str
    default_model: str
    fallback_model: str | None = None
    unset_env_keys: tuple[str, ...] = ()
    inline_only: bool = False
    supports_multi_turn: bool = False
    build_cmd: Callable[..., list[str]] | None = None
    stdin_rewrite: Callable[[list[str]], list[str]] | None = None
    implicit_family: str | None = None


AGENTS: dict[str, AgentSpec] = {
    "claude": AgentSpec(
        name="claude",
        default_model="opus-4.6",
        inline_only=True,
        implicit_family="anthropic",
    ),
    "codex": AgentSpec(
        name="codex",
        default_model="gpt-5.4",
        fallback_model="gpt-5.4-mini",
        unset_env_keys=("OPENAI_API_KEY", "OPENAI_BASE_URL", "CODEX_API_KEY"),
        supports_multi_turn=True,
        build_cmd=build_codex_cmd,
        stdin_rewrite=_codex_stdin_rewrite,
        implicit_family="openai",
    ),
    "gemini": AgentSpec(
        name="gemini",
        default_model="gemini-3.1-pro-preview",
        fallback_model="gemini-3-flash-preview",
        unset_env_keys=("GOOGLE_API_KEY", "GEMINI_API_KEY"),
        supports_multi_turn=True,
        build_cmd=build_gemini_cmd,
        stdin_rewrite=_gemini_stdin_rewrite,
        implicit_family="google",
    ),
    "opencode": AgentSpec(
        name="opencode",
        default_model="anthropic/claude-sonnet-4-6",
        supports_multi_turn=False,
        build_cmd=build_opencode_cmd,
        stdin_rewrite=_opencode_stdin_rewrite,
        implicit_family=None,  # gateway: ticket must supply family
    ),
    "ollama": AgentSpec(
        name="ollama",
        default_model="qwen2.5:32b",
        supports_multi_turn=False,
        build_cmd=build_ollama_cmd,
        stdin_rewrite=_ollama_stdin_rewrite,
        implicit_family=None,  # gateway: ticket must supply family
    ),
}


# ── Canonical family vocabulary ──────────────────────────────────────────────
#
# The launcher refuses gateway-transport tickets whose family is missing
# or outside this set. Vocabulary lives in templates/agents/families.md;
# this list mirrors it. Keep the two in sync when a new architecture
# lands — the markdown file is the source of truth Claude reads when
# emitting tickets.

_CANONICAL_FAMILIES: frozenset[str] = frozenset({
    "alibaba", "anthropic", "cohere", "deepseek", "google",
    "meta", "microsoft", "mistral", "moonshot", "openai", "xai",
})


def _validate_ticket_family(ticket: dict, spec: AgentSpec) -> None:
    """Refuse to launch a ticket whose family is missing or unknown.

    For single-family transports (implicit_family set), the field may
    be absent (the launcher fills it in) but if present must match.
    For gateway transports (implicit_family None), the field is
    required and must be in _CANONICAL_FAMILIES.
    """
    fam = ticket.get("family")
    tid = ticket.get("id", "<unknown>")
    if spec.implicit_family is not None:
        if fam is None:
            return  # orchestrator elided; launcher will fill from spec
        if fam != spec.implicit_family:
            sys.exit(
                f"ticket {tid}: family={fam!r} conflicts with transport "
                f"{spec.name!r} (implicit family: {spec.implicit_family!r})"
            )
        return
    if not fam:
        sys.exit(
            f"ticket {tid}: gateway transport {spec.name!r} requires an "
            "explicit 'family' field. See templates/agents/families.md."
        )
    if fam not in _CANONICAL_FAMILIES:
        sys.exit(
            f"ticket {tid}: unknown family {fam!r}. "
            f"Canonical set: {sorted(_CANONICAL_FAMILIES)}."
        )


def _launchable_spec(agent: str) -> AgentSpec:
    """Return the spec for a launchable (non-inline) agent, or exit."""
    spec = AGENTS.get(agent)
    if spec is None:
        sys.exit(
            f"agent-ctl: unknown agent '{agent}'. "
            f"Known agents: {', '.join(sorted(AGENTS))}."
        )
    if spec.inline_only:
        sys.exit(
            f"agent-ctl: agent '{agent}' is inline-only and must be executed "
            "by the orchestrator (Claude Code), not dispatched to agent-ctl."
        )
    return spec


def _build_shell_cmd(agent: str, agent_cmd: list[str], prompt: str,
                     ticket_id: str = "") -> str:
    """Build shell command string, using temp file + stdin for large prompts.

    For prompts under PROMPT_SIZE_THRESHOLD, quotes the prompt inline
    (existing behavior). For larger prompts, writes to a temp file and
    pipes via stdin to avoid shell argument limits and LaTeX escaping.
    The per-agent stdin shape is carried by the AgentSpec.
    """
    if len(prompt) <= PROMPT_SIZE_THRESHOLD:
        return " ".join(_quote(c) for c in agent_cmd)

    safe_id = re.sub(r"[^a-zA-Z0-9_-]", "_", ticket_id or "prompt")
    prompt_file = Path(f"/tmp/agent_ctl_{safe_id}_{int(time.time())}.md")
    prompt_file.write_text(prompt, encoding="utf-8")

    spec = AGENTS.get(agent)
    if spec is None or spec.stdin_rewrite is None:
        # Fall back to inline quoting for unknown agents or agents that do
        # not declare a stdin rewriter. Upstream callers should never reach
        # this branch in practice — cmd_start / _launch_ticket guard first.
        return " ".join(_quote(c) for c in agent_cmd)

    cmd_for_stdin = spec.stdin_rewrite(agent_cmd)
    quoted = " ".join(_quote(c) for c in cmd_for_stdin)
    return f"cat {_quote(str(prompt_file))} | {quoted}"


# ── Commands ─────────────────────────────────────────────────────────────────

def cmd_start(args) -> None:
    agent = args.agent
    spec = _launchable_spec(agent)
    cwd = args.cwd or os.getcwd()
    model = args.model or spec.default_model
    timeout = args.timeout or DEFAULT_TIMEOUT

    # Hold the state lock across read+next_id+launch+save so two
    # concurrent `start` invocations cannot compute the same ID.
    with _state_lock():
        state = load_state()
        state = reap_finished(state)
        sid = next_id(state)
        OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        outfile = OUTPUT_DIR / f"session-{sid}.txt"
        result_file = OUTPUT_DIR / f"session-{sid}-result.md"

        agent_cmd = spec.build_cmd(
            prompt=args.prompt, model=model,
            result_file=result_file, cwd=cwd,
            extra_flags=args.flags,
            flags={},
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

    # Refuse multi-turn for transports that have not opted in. The
    # codex/gemini resume blocks below are agent-specific (different
    # CLI shapes for resume), and silently falling through for new
    # transports would either produce wrong commands or attempt the
    # gemini path against an unrelated CLI. Each new transport must
    # set supports_multi_turn=True AND grow an explicit branch here
    # before send works for it.
    spec = AGENTS.get(agent)
    if spec is None or not spec.supports_multi_turn:
        sys.exit(
            f"agent-ctl: transport {agent!r} does not support multi-turn "
            "sessions. Start a new session instead, or set "
            "supports_multi_turn=True on the AgentSpec and add a resume "
            "branch in cmd_send."
        )

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
        cmd = ["gemini", "-p", args.msg, "-m", model, "-o", "text"]
        if uuid:
            cmd.extend(["--resume", uuid])
        else:
            cmd.extend(["-r", "latest"])
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
        print(result_file.read_text())
        return

    # Fall back to raw output (also primary path for Gemini, which uses -o text)
    outfile = Path(meta["outfile"])
    if outfile.exists() and outfile.read_text().strip():
        content = outfile.read_text().strip()
        # For gemini, -o text already gives clean output; for codex fallback,
        # the raw output includes headers but is better than nothing
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


def cmd_wait(args) -> None:
    """Block until one or more sessions finish."""
    state = load_state()
    sids = args.ids
    poll_interval = 5

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
        if pending:
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

    Inline-only agents (claude and any other spec with inline_only=True)
    are executed by the orchestrator, not run-dag, so they never enter
    the ready pool here.
    """
    if ticket.get("status") != "pending":
        return False
    spec = AGENTS.get(ticket.get("agent", ""))
    if spec is None or spec.inline_only:
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

    spec = _launchable_spec(agent)
    _validate_ticket_family(ticket, spec)
    timeout = ticket.get("timeout_s", DEFAULT_TIMEOUT)
    model = ticket.get("model") or spec.default_model
    ticket_cwd = ticket.get("cwd", cwd)

    # Re-acquire the state lock and refresh from disk so we see any
    # session entries written by concurrent agent-ctl processes since
    # the run-dag loop last loaded state. Without this, two run-dag
    # invocations (or a run-dag + a manual `start`) would compute the
    # same next_id and overwrite each other's session record.
    with _state_lock():
        state = load_state()
        state = reap_finished(state)
        sid = next_id(state)
        OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        outfile = OUTPUT_DIR / f"session-{sid}.txt"
        result_file = OUTPUT_DIR / f"session-{sid}-result.md"

        agent_cmd = spec.build_cmd(
            prompt=prompt, model=model,
            result_file=result_file, cwd=ticket_cwd,
            extra_flags=None,
            flags=ticket.get("flags") or {},
        )

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

                        # If this agent defines a fallback model and the log
                        # shows capacity exhaustion (the Gemini 429 pattern),
                        # switch to the fallback on the next attempt.
                        fallback_spec = AGENTS.get(agent)
                        fallback = fallback_spec.fallback_model if fallback_spec else None
                        if fallback and log_text and (
                            "MODEL_CAPACITY_EXHAUSTED" in log_text
                            or log_text.count("429") > 5
                        ):
                            ticket["model"] = fallback
                            print(f"[{tid}] capacity exhaustion detected, falling back to {fallback}")

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
    p_start.add_argument("agent", choices=sorted(n for n, s in AGENTS.items() if not s.inline_only), help="Agent to use")
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

    sub.add_parser("status", help="Show all sessions")

    p_wait = sub.add_parser("wait", help="Block until sessions finish")
    p_wait.add_argument("ids", nargs="+", help="Session IDs to wait for")

    p_rundag = sub.add_parser("run-dag", help="Execute a ticket DAG until no ready tickets remain")
    p_rundag.add_argument("tickets", help="Path to tickets.json")
    p_rundag.add_argument("--cwd", help="Working directory for ticket execution (default: tickets.json parent)")
    p_rundag.add_argument("--concurrent", type=int, default=3,
                          help="Max concurrent running tickets (default: 3)")

    p_dagstatus = sub.add_parser("dag-status", help="Show progress of a ticket DAG")
    p_dagstatus.add_argument("tickets", help="Path to tickets.json")

    p_cleanup = sub.add_parser("cleanup", help="Kill sessions and clear state")
    p_cleanup.add_argument("--agent", choices=sorted(n for n, s in AGENTS.items() if not s.inline_only),
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
    elif args.cmd == "cleanup":
        cmd_cleanup(args)


if __name__ == "__main__":
    main()
