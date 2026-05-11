# Design notes

Per-feature design rationales. These started as GitHub-issue-style design briefs (`[v8] …`, `[v8.1] …`) that got committed alongside the corresponding code. They are kept here as the record of *why* each pipeline phase or audit layer exists in its current shape — what failure mode it addresses, what alternatives were rejected, what was deferred.

They are not active work items. Where a note describes "v8.x design," that work is now implemented; the note remains for the design rationale.

## Index

| Note | What it addresses |
|---|---|
| [01 obligation extraction](01_obligation_extraction.md) | v8.0 — per-family extraction of required-but-missing objects (kernels without initial conditions, MCMCs without complete-data densities). |
| [02 section extract → global integrate](02_section_extract_global_integrate.md) | v8.0 — clustering equivalent obligations across families without collapsing disagreement. |
| [03 gap-claim calibration](03_gap_claim_calibration.md) | v8.0 — two-stage rubric that fires only on disputed obligations and requires five components to ship a gap finding. |
| [04 drop mini](04_drop_mini_for_discovery.md) | v7.1 — replacing `gpt-5.4-mini` and `gemini-3-flash-preview` on the discovery tracks with frontier models. |
| [05 adversarial bench](05_adversarial_bench_before_redesign.md) | v8.0 process — building a known-formal-gaps benchmark before committing the v8 redesign. |
| [06 formal claim audit](06_formal_claim_audit.md) | v8.1 — wrong-but-present errors: the formal object exists but is wrong under the paper's own definitions. |
| [07 scope/framing overclaim audit](07_scope_framing_overclaim_audit.md) | v8.2 — narrative claim overstating what the formal evidence delivers. |

## How to read these

Each note follows roughly: problem observed → decision → rejected alternatives → validation plan. Most reference dated dev log entries under [`../log/`](../log/) for the surrounding context (what bench failures motivated the design, what reviews shaped it).

For active future work, prefer GitHub Issues over adding new files here. This folder is the *historical* design record.
