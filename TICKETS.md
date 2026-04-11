# Tickets: End-to-End Orchestration

## Context

The templates, methods, and ticket schema are proven (comparison run beat a human referee on material issues). The gap is orchestration: making `/disputatio paper.pdf` work without manual intervention.

**Architecture**: Claude Code is the runtime. State lives on disk (tickets.json). SKILL.md describes a decision function, not a sequential protocol. agent-ctl handles external agents. Everything is logged to the Obsidian workspace.

**Design principle** (from Codex/Gemini review): no 13-step sequential protocol. Instead, a single-page decision table Claude reads fresh each iteration. Read state → match pattern → do one thing → write state → loop.

---

## Tickets

### [T1] agent-ctl: prompt delivery via temp file and stdin
- **Status:** pending
- **Priority:** high (blocks everything)
- **Files:** `~/.claude/skills/agent_ctl.py`
- **Description:** When prompt exceeds 10KB, write it to a temp file and deliver via stdin (not shell argument expansion). `$(cat /tmp/file)` is fragile with LaTeX special chars (Codex/Gemini both flagged this). Instead: pipe the file content via stdin to the agent process.
- **Implementation:**
  - Add a `PROMPT_SIZE_THRESHOLD = 10240` constant
  - In `_launch_ticket`: if `len(prompt) > PROMPT_SIZE_THRESHOLD`, write prompt to `/tmp/agent_ctl_prompt_{ticket_id}.md`
  - For Codex: use `codex exec ... < /tmp/prompt_file` (stdin delivery)
  - For Gemini: use `cat /tmp/prompt_file | gemini -p ""` (stdin + empty -p, since Gemini appends stdin to -p)
  - Apply same fix to the `start` subcommand (used by `/codex` and `/gemini` skills)
  - Clean up temp files after process launch
- **Backward compatibility:** The `start` codepath only changes behavior for prompts >10KB. Short prompts (the common case for `/codex` and `/gemini`) use the existing inline path unchanged.
- **Acceptance Criteria:**
  - [ ] Prompts >100KB delivered correctly to Codex (test with a real paper)
  - [ ] Prompts >100KB delivered correctly to Gemini
  - [ ] `/codex "short prompt"` still works (regression test)
  - [ ] `/gemini "short prompt"` still works
  - [ ] LaTeX content with backslashes, dollars, braces survives round-trip
  - [ ] Temp files cleaned up after launch

---

### [T2] SKILL.md: decision-table orchestration + full logging
- **Status:** pending
- **Priority:** high
- **Files:** `SKILL.md`
- **Description:** Replace the current descriptive protocol with an executable decision table. Claude reads tickets.json, matches the current state, does ONE thing, writes results, and loops. Every action writes output to the Obsidian workspace. Nothing lives only in Claude's context.
- **Implementation:**
  - Add `## Execution` section with the decision table:
    ```
    LOOP until final_report is done:
      1. Read $PAPER/_artifacts/tickets.json
      2. Match state:
         - no tickets.json → run INIT (create workspace, copy paper, emit wave 1)
         - orient tickets pending → execute orient_claude inline, run agent-ctl for others
         - all orient done, no discover tickets → RENDER orientation, emit wave 2
         - discover tickets pending → execute discover_claude_* inline, run agent-ctl for others
         - all discover done, no merge_rank → RENDER discovery, execute merge_rank inline
         - merge_rank done, no verify → emit verify ticket, run agent-ctl
         - verify done, no debate tickets → RENDER ranking, emit debate round 1
         - debate round N done → read synthesis, decide: emit round N+1 or mark terminal
         - all debates terminal, no final_report → execute final_report inline
         - final_report done → EXIT
      3. After each action: update tickets.json, render to Obsidian, log to _artifacts/
    ```
  - Add `## INIT procedure` section: exact commands for workspace creation
  - Add `## Prompt generation` section: exact substitution rules for each template type (which vars, where the content comes from, where to write)
  - Add `## Inline execution` section: how Claude runs orient_claude, merge_rank, final_report (read inputs, do the work, write JSON output, write Obsidian markdown, mark done)
  - Add `## Rendering` section: after each wave, render JSON → Obsidian markdown per obsidian_render.md
  - Add `## Logging contract`: every action writes to disk:
    - Prompts → `_artifacts/prompts/<ticket_id>.md`
    - Raw JSON output → `_artifacts/json/<ticket_id>.json`
    - Session logs → `_artifacts/sessions/<ticket_id>.log` (agent-ctl handles this for external agents; Claude writes its own reasoning summary for inline tickets)
    - Curated markdown → numbered folders (20_orientation/, 30_discovery/, etc.)
    - Status updates → tickets.json + 00_review.md frontmatter
  - Add `## Resumability`: on re-invocation, read tickets.json, skip done tickets, resume from first non-terminal state
- **What gets removed from SKILL.md:** The current `## Protocol` section (steps 0-4) is replaced by the decision table. The phase descriptions stay as reference but are no longer the execution path.
- **Acceptance Criteria:**
  - [ ] Decision table fits on one page (no scrolling to find the next action)
  - [ ] Each state transition is self-contained (Claude doesn't need to remember previous iterations)
  - [ ] Every Claude action writes at least one file to disk before proceeding
  - [ ] tickets.json is updated after every action (not batched)
  - [ ] 00_review.md phase field updated at each major transition
  - [ ] Inline ticket execution logs a reasoning summary to `_artifacts/sessions/<ticket_id>.log`
  - [ ] Re-invoking `/disputatio` on a paper folder with existing tickets.json resumes correctly

---

### [T3] M0 close-reading method template
- **Status:** pending
- **Priority:** medium
- **Files:** `templates/methods/m0_close_reading.md`
- **Description:** Mechanical line-by-line proofreading method. Addresses the gap vs coarse.ink: they catch 11 unique typos/notation errors we miss. This is NOT conceptual critique (M2-M6 handle that). This is surface-level error detection.
- **Implementation:**
  - Procedure:
    1. Read every equation: verify LHS matches RHS after claimed operations
    2. Check subscripts/superscripts: does the index match its definition?
    3. Check cross-references: does "equation (N)" actually say what the text claims?
    4. Check notation consistency: same symbol means same thing throughout
    5. Check proof steps: does each step follow from the previous? Any missing squares, sign errors, wrong exponents?
    6. Check wording: "maximizer" vs "minimizer", "increasing" vs "decreasing", "greater" vs "less"
    7. Check Lagrangian/FOC consistency: does differentiating the stated Lagrangian produce the stated FOC?
  - Output: same issue JSON schema as M2-M6, with `method: "m0"`
  - Impact guidance: typos = minor, sign errors in proofs = local or material, notation inconsistencies = local
  - Explicit instruction: do NOT flag OCR artifacts, do NOT flag stylistic preferences
- **Acceptance Criteria:**
  - [ ] Template follows the same structure as m2-m6 templates
  - [ ] Procedure is mechanical (no creativity needed, just completeness)
  - [ ] Would catch: Lagrangian missing square, Footnote 16 sign error, maximizer/minimizer slip, $\alpha_\ell$ definition inconsistency (all issues from the comparison run)

---

### [T4] emit_tickets.md: add M0 to Wave 2
- **Status:** pending
- **Priority:** medium
- **Files:** `templates/emit_tickets.md`
- **Description:** Update the ticket emission protocol to include M0 close-reading tickets in the discovery wave.
- **Implementation:**
  - Change "3 agents x 5 methods = 15 discovery sweeps" to "3 agents x 6 methods = 18 discovery sweeps"
  - Add `discover_<agent>_m0` to Wave 2 ticket examples
  - Add m0 to the ticket ID naming convention
  - Update merge_rank depends_on list to include the 3 extra m0 tickets
  - Update merge_and_rank.md input list reference (15 → 18 files)
- **Acceptance Criteria:**
  - [ ] Wave 2 emits 18 tickets (not 15)
  - [ ] merge_rank depends_on includes all 18 discovery tickets
  - [ ] Ticket ID convention includes m0 examples

---

### [T5] Verification gates (from Codex review)
- **Status:** pending
- **Priority:** medium
- **Files:** `SKILL.md`
- **Description:** Codex flagged that Claude will "self-certify weak work" without verification gates. Add explicit output validation between phases.
- **Implementation:**
  - After orientation: verify each JSON has `main_claims` with >=5 entries and `propositions` with >=3 entries. If not, flag and retry.
  - After discovery: verify each JSON has `issues` array with >=1 entry. Empty outputs get retried once.
  - After merge_rank: verify `ranked_issues.json` has >=5 merged issues. If fewer, log a warning (paper may genuinely have few issues).
  - After each debate synthesis: verify the JSON has `refined_claim`, `impact`, and `status` fields. Malformed outputs get retried.
  - Gate logic is part of the decision table (a state transition only fires if the output validation passes).
- **Acceptance Criteria:**
  - [ ] Each phase transition includes an output validation check
  - [ ] Failed validations trigger retry (up to max_attempts from ticket schema)
  - [ ] Validation criteria are written in SKILL.md, not hardcoded elsewhere

---

### [T6] Dev log for comparison run
- **Status:** pending
- **Priority:** low
- **Files:** `docs/log/2026-04-11_comparison-run.md`
- **Description:** Document the comparison run decisions, findings, and lessons learned. This is the dev log entry per the branching workflow in CLAUDE.md.
- **Acceptance Criteria:**
  - [ ] Documents: what was done, why, key decisions, blockers hit, lessons learned
  - [ ] Links to compare/README.md for results
  - [ ] Notes the CLI failure modes and their fixes
