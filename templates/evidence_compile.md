# Evidence compiler (v6, inline)

Every candidate finding produced by any Phase 2 discovery ticket passes through the **evidence compiler** before it is written to the discovery JSON. The compiler is a deterministic pre-write gate that enforces verbatim-quote discipline at candidate-generation time, not at merge time.

This is NOT a model call. It is an orchestrator-side validator implemented in Python inside the discovery subagent, fired once per candidate just before the candidate is appended to the output array.

## Contract

Input: one candidate finding object produced by the discovery agent, shape per `templates/discover_holistic.md` / `discover_broad.md` / `discover_narrow.md`.

Output: either the candidate is **kept** (passes gate) or **rejected** (does not appear in the output JSON). Rejected candidates are recorded in the ticket's session log with the rejection reason so the evidence compiler's behaviour is auditable.

## Rules

The compiler applies these rules in order. First failure = rejection.

### Rule 1 — evidence array exists and is non-empty

```
if not candidate.evidence or len(candidate.evidence) == 0:
    reject("no evidence entries")
```

A candidate with no evidence array is unverifiable and inadmissible.

### Rule 2 — at least one direct_quote OR explicit derived_inference justification

```
has_direct = any(e.support_type == "direct_quote" for e in candidate.evidence)
has_derived = any(e.support_type == "derived_inference" for e in candidate.evidence)

if not has_direct and not has_derived:
    reject("no valid support_type on any evidence entry")

if has_derived and not has_direct:
    # derived-only findings need an explicit inference step in the why field
    derived = next(e for e in candidate.evidence if e.support_type == "derived_inference")
    if len(derived.why) < 40 or "infer" not in derived.why.lower() and "imply" not in derived.why.lower() and "follow" not in derived.why.lower():
        reject("derived_inference evidence requires explicit inference step in 'why' field")
```

Rationale: findings that do not anchor on a real paper quote must at least articulate the inference step that connects a real quote to the claim. Calibration catches the weak ones; the compiler catches the empty ones.

### Rule 3 — quote substring-match on paper.md

```
paper = open("_paper/paper.md").read()

def norm(s):
    return " ".join(s.split())  # collapse whitespace

for e in candidate.evidence:
    if e.support_type == "direct_quote":
        if norm(e.quote) not in norm(paper):
            reject(f"quote not a substring of paper.md: {e.quote[:60]}...")
```

Rationale: v5 had a post-merge validator that caught non-verbatim quotes after the fact. v6 moves this pre-write so the agent cannot even produce a candidate without a real quote. Derived-inference entries are exempt from substring-match (by definition the quote anchors adjacent text, not the claim itself) but must still pass Rule 2.

### Rule 4 — location anchor non-empty

```
for e in candidate.evidence:
    if not e.location or e.location.strip() in ("", "various", "multiple locations", "see paper", "section unknown"):
        reject(f"location anchor missing or placeholder: {e.location}")
```

Rationale: the v5 merge atomicity rules banned summary locations. v6 enforces at write time.

### Rule 5 — claim is a single falsifiable sentence

```
claim = candidate.claim.strip()
if len(claim) < 20:
    reject("claim too short to be falsifiable")
if claim.count(".") > 2 and not claim.endswith("."):
    reject("claim spans multiple sentences; use 'and' test from merge_and_rank.md Rule 4 to split")
```

Rationale: multi-sentence claims bundle two concerns and create merge over-aggregation downstream. The compiler catches obvious cases; merge atomicity handles edge cases.

### Rule 6 — category is in the canonical vocabulary

```
VALID_CATEGORIES = {
    "proof", "empirics", "identification", "framing",
    "robustness", "interpretation", "notation", "other"
}
if candidate.category not in VALID_CATEGORIES:
    reject(f"category '{candidate.category}' not in canonical vocabulary")
```

## Implementation location

The evidence compiler is invoked at the END of each discovery subagent's run, inside the subagent (not in the orchestrator), just before the JSON is written to disk. Subagent pseudocode:

```python
candidates = agent.run_discovery_method(paper, paper_map, holistic_pass, attack_surface_index)
kept = []
rejection_log = []
for c in candidates:
    result = evidence_compiler.validate(c, paper_text)
    if result.ok:
        kept.append(c)
    else:
        rejection_log.append({"candidate": c, "reason": result.reason})

output = {"track": "<track>", "agent": "<family>", "issues": kept}
write_json(output_path, output)
write_log(session_log_path, rejection_log)
```

The rejection log is mandatory. Audit requires knowing which candidates the compiler killed and why.

## Expected rejection rate

On papers with good evidence hygiene (typical theory papers after socr-OCR), rejection rate is 0–10%. Rates above 25% indicate the discovery prompt is insufficiently constrained or the model is hallucinating quotes; investigate the prompt.

## Relationship to merge atomicity

Merge's post-merge validator (`templates/merge_and_rank.md` Step 2b) still runs. It catches cases where the evidence compiler passed an individual candidate but merge clustered it in a way that introduces a bundled claim. The two validators are complementary, not redundant:

- **Evidence compiler**: catches per-candidate quote fabrication and category drift at write time.
- **Merge validator**: catches cluster-level atomicity violations at merge time.

Both run. Both block progression on violation.

## What the compiler does NOT do

- Does not judge whether the claim is correct — that is merge / debate / calibration's job.
- Does not assess severity or confidence — those are the agent's self-reports.
- Does not infer category from content — the agent must supply a valid category; the compiler only validates membership.
- Does not rewrite rejected candidates — rejection is terminal within the discovery ticket. A rewrite would require re-running discovery with a tightened prompt.
