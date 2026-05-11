# [v8] Build adversarial benchmark of known formal gaps before committing v8

**Type**: process / methodology
**Priority**: high (gating)
**Origin**: 2026-04-25 codex 5.5 critique

## Problem

The v8 design proposal (issues #01–#04) is anchored on **one paper**: Stephens & Donnelly (2000), where coarse caught 8 spec gaps and disputatio caught 0. If we redesign v8 against that one data point, we tune for popgen-style methodological-statistics specification gaps and miss the next failure mode.

## Proposal

Before merging any v8 changes, assemble an **adversarial benchmark** of papers with **known formal gaps across domains**. Target ≥6 papers spanning:

- Methodological statistics (already have: Stephens & Donnelly 2000)
- Network economics (already have: Galeotti, Golub & Goyal 2020)
- Computational neuroscience (already have: van Vreeswijk & Sompolinsky 1998)
- Information theory / coding (already have: Forney 1988)
- Plus 2 more in domains where gap-style critiques are common: causal inference (e.g., a known-flawed identification paper), and applied econometrics (e.g., a paper with known instrument-validity gaps).

For each paper, **manually compile the ground-truth gap list** from:
- Published comments / errata / replies
- Citation network of corrections
- coarse.ink's review where available
- Domain-expert spot-check (us)

Score v7 baseline + each v8 candidate (issues #01–#04) against this set:

- **Recall on known gaps** — what fraction did the system surface?
- **Precision** — among findings, what fraction are real gaps vs. noise?
- **Calibration discipline** — drops surface, no false ground truth shipped.

Only commit a v8 design that improves recall *without* tanking precision. If the proposed obligation-extraction (issue #01) works on Stephens but blows up noise on Forney, we don't ship it.

## Why this matters more than it sounds

The Stephens 0/8 result is alarming but it's a single observation. We don't know:

- Is v7 also at 0/8 on van Vreeswijk's spec gaps? Or 5/8 because the conceptual-scope tracks happen to fire there too?
- Does coarse get 8/8 across domains, or is it strong specifically on methodological statistics?
- Are the gap categories transferable? An MH-needs-complete-data-density gap is statistics-specific. An information-theory paper's gaps look different (e.g., "lattice partition normalization unspecified for n=odd").

Codex's warning: "you may be over-indexing on Stephens & Donnelly. Build a small adversarial benchmark of known formal gaps across domains before redesigning v8."

## Concrete next steps

1. Finish v7 bench on van Vreeswijk + Forney (in flight). Compare to coarse on each.
2. Pick 2 more papers in causal inference / applied econometrics with known formal gaps. Suggested candidates: TBD with user input — papers from the AEA "comments and replies" stream are a good source.
3. OCR them via socr `--unified`.
4. Run v7 baseline on all 6.
5. Compile ground-truth gap list per paper (manually).
6. Score v7 baseline.
7. **Then** prototype v8 on a single paper (Stephens), measure delta vs baseline. If positive, prototype on the others. If recall improves and precision holds, ship v8.

## Tradeoff

This delays v8 by ~1–2 weeks (depending on bench-building time). Codex's argument: cheaper than the alternative (shipping a v8 that overfits to one paper and fails elsewhere).

## Related

- Issue #01–#04 are gated on this issue's bench landing first

## Source critique

> "You may be over-indexing on Stephens & Donnelly. Build a small adversarial benchmark of known formal gaps across domains before redesigning v8. Otherwise you risk tuning for one paper/type of failure." — codex/gpt-5.5, 2026-04-25
