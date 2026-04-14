# V6 upstream plan

## Pushback first

The framing is mostly right, but two parts need discipline:

1. Do not sell a raw `0-100 confidence` number unless it is backed by observed calibration on held-out papers. Internally we can keep a continuous score, but the UI should treat it as a calibrated estimate with provenance, not as fake precision.
2. Do not let "panel of 3 models" drift into "majority vote truth." Cross-family agreement is a strong signal, not a verdict. The decisive object is still the evidence-backed finding after drop / narrowing / defense.

The wedge is upstream decision support for authors and referees. That is a materially better product definition than "R&R copilot."

## Product target

Primary use cases:

- Pre-submission author review: "what will a serious referee catch, and what should I fix before I submit?"
- Referee assistance: "which concerns are worth endorsing in my own report, which are real but overstated, and which should I drop?"

Primary deliverable:

- A finding panel with evidence, cross-architecture support, verdict history, and action routing.

Secondary deliverables:

- A prose summary memo
- An optional revision plan for authors
- An optional referee-letter draft for referees

## Two-week implementation plan

### Week 1

#### Day 1: lock spec and stop building the wrong deliverable

- Freeze the v6 product spec around the two upstream modes: `author` and `referee`.
- Replace "referee report is the primary output" language in `README.md`, `CLAUDE.md`, `SKILL.md`, and templates with "finding panel is primary, prose memo is secondary."
- Define the new `final.json` replacement schema and its compatibility story.
- Write one sample panel output for one existing paper in both modes to expose missing fields early.

#### Day 2: add holistic pass before discovery

- Add a new phase before method discovery: `holistic_map`.
- Output should include:
  - paper spine
  - main claims
  - empirical / theoretical attack surfaces
  - likely referee questions
  - sections requiring evidence-heavy scrutiny
- Feed this map into downstream discovery and ranking. Do not merge away per-model maps; add a single orchestrator-level canonical attack-surface index derived from them.

#### Day 3: simplify discovery and reduce sweep count

- Cut broad discovery from the current 18-ticket shape to a smaller set centered on coverage, not method theater.
- Keep one broad critic pass per family, using the holistic map as context.
- Keep only the narrow methods that produce distinct signal. Drop methods whose output is mostly correlated prose duplication.
- Add explicit "candidate finding" typing so downstream stages know whether a concern is:
  - claim-scope mismatch
  - proof / derivation flaw
  - identification / empirical design weakness
  - robustness / missing check
  - framing / literature / interpretation overreach
  - notation / presentation local issue

#### Day 4: targeted evidence compiler

- Add a per-concern evidence compiler that:
  - pulls exact quotes
  - pins locations
  - assembles minimal supporting context
  - records which parts of the concern are directly evidenced vs inferred
- Make this the only source for evidence used in merge, debate, calibration, and rendering.
- Extend the existing verbatim validator so a finding cannot progress without exact quote support or an explicit "inference" tag.

#### Day 5: new merge and panel object

- Replace merge output centered on "issue register for later prose" with merged atomic findings centered on the panel row.
- Preserve all losing and narrowed variants in verdict history rather than flattening them away.
- Implement mode-aware routing:
  - author mode: `fix_before_submit`, `watch_in_review`, `can_ignore`
  - referee mode: `endorse`, `verify_before_endorsing`, `skip`

### Week 2

#### Day 6: debate as escalation only

- Change debate trigger from rank-driven default to contested-finding escalation.
- Debate should fire only when:
  - cross-family disagreement is real
  - evidence exists on both sides
  - severity would change if the claim survives
  - the finding would otherwise be shown to the user
- Keep prosecution / defense / synthesis, but cap it to one escalation round by default with a second round only if the synthesizer explicitly cannot resolve.

#### Day 7: calibration and drop transparency

- Rework calibration output so it writes directly onto each finding panel row:
  - supported
  - overclaimed_narrowed
  - dropped
- Add `drop_reason` and `narrowing_notes`.
- Preserve hidden dropped rows in the audit trail, but expose user-visible drop summaries so the panel demonstrates restraint rather than pretending every candidate survived.

#### Day 8: writer and mode renderers

- Build one single-writer renderer that consumes the finding panel and produces:
  - author summary memo
  - referee summary memo
  - optional referee-letter draft
- The writer should never invent findings. It can only summarize rows that survived calibration.
- Ensure the primary UI surfaces the panel first, not the prose.

#### Day 9: evaluation harness for the real wedge

- Add cheap release-gate evaluation scripts for:
  - finding-level support rate
  - overclaim rate
  - author actionability
  - referee endorsement utility
  - coarse comparison on same-paper same-mode outputs
- Reuse existing compare assets where possible, but add panel-aware evaluators rather than forcing everything through referee-letter adapters.

#### Day 10: landing page, one-page editor pitch, and pilot packaging

- Rewrite homepage copy around upstream use cases and panel differentiation.
- Produce a one-page PDF / markdown pitch for editors and a short product explainer for authors.
- Prepare a pilot package with 2-3 benchmark papers rendered in both modes from the same engine.

## New output schema

This replaces the current final report centered `final.json`. The top-level object is a review run with finding rows as the core unit.

```json
{
  "run_id": "string",
  "paper": {
    "title": "string",
    "authors": ["string"],
    "year": 2026,
    "paper_id": "string",
    "source_path": "string"
  },
  "engine": {
    "version": "v6",
    "mode": "author | referee",
    "families": ["anthropic", "openai", "google"]
  },
  "holistic_pass": {
    "paper_spine": "string",
    "main_claims": ["string"],
    "attack_surfaces": [
      {
        "id": "AS1",
        "type": "theory | empirics | identification | framing | robustness | exposition",
        "description": "string",
        "priority": "high | medium | low"
      }
    ]
  },
  "findings": [
    {
      "finding_id": "F001",
      "concern": "string",
      "category": "proof | empirics | identification | framing | robustness | interpretation | notation | other",
      "severity": "material | local | nit",
      "confidence": {
        "score": 0,
        "band": "high | medium | low",
        "source": "calibrated_model_score"
      },
      "priority": {
        "author": "fix_before_submit | watch_in_review | can_ignore",
        "referee": "endorse | verify_before_endorsing | skip"
      },
      "evidence": [
        {
          "quote": "string",
          "location": "string",
          "why": "string",
          "support_type": "direct_quote | derived_inference"
        }
      ],
      "architecture_support": {
        "anthropic": {
          "supports": true,
          "methods": ["M2", "M5"],
          "notes": "string"
        },
        "openai": {
          "supports": true,
          "methods": ["M2"],
          "notes": "string"
        },
        "google": {
          "supports": false,
          "methods": [],
          "notes": "string"
        },
        "cross_family_score": {
          "support_count": 2,
          "family_count": 3
        }
      },
      "debate": {
        "triggered": true,
        "reason": "cross_family_disagreement | severity_check | evidence_conflict | none",
        "verdict": "prosecution_wins | defense_wins | split | not_run",
        "defender_response": "string",
        "what_survived": "string",
        "history": [
          {
            "stage": "candidate | merged | debated | calibrated",
            "claim": "string",
            "outcome": "kept | narrowed | dropped"
          }
        ]
      },
      "calibration": {
        "verdict": "supported | overclaimed_narrowed | dropped",
        "quote_verified": "yes | partial | no",
        "annotator_notes": "string",
        "narrowing_notes": "string",
        "drop_reason": "string"
      },
      "suggested_action": {
        "author": {
          "fix": "string"
        },
        "referee": {
          "how_to_use": "string"
        }
      },
      "audit": {
        "source_candidate_ids": ["string"],
        "prompt_trace_ids": ["string"],
        "status": "survived | dropped"
      }
    }
  ],
  "summary": {
    "counts": {
      "material": 0,
      "local": 0,
      "nit": 0,
      "dropped": 0
    },
    "top_priorities": ["F001", "F004"],
    "author_memo": "string",
    "referee_memo": "string"
  }
}
```

### Schema notes

- `confidence.score` should exist internally, but user-facing display can round or bucket it until calibration quality is proven.
- `priority` is mode-specific rendering from one engine, not two separate discovery pipelines.
- `debate.history` is important. The differentiator is not "three models talked"; it is "you can see what got narrowed or killed."

## Pipeline diffs

### Remove

- The current method-heavy discovery theater as the center of the product.
- Debate on a fixed top-N cohort by default.
- Final deliverable centered on a monolithic referee letter.
- Any stage that forces all findings into polished prose before they are evidence-checked.

### Reduce

- Discovery sweeps from 18 to 9 total tickets:
  - 3 holistic passes, one per family
  - 3 broad critic passes, one per family
  - 3 narrow evidence-judgment passes, one per family

This is the right simplification unless measurement later shows a dropped coverage tail. The current 18-pass design is too expensive relative to the distinct signal it adds.

### Add

- Holistic conceptual pass first
- Canonical attack-surface index
- Targeted evidence compiler per concern
- Panel-row-native merge object
- Debate as escalation court only
- Finding-level verdict history
- Mode-specific priority renderer
- Panel-aware evaluation harness

### Keep

- Three-family architecture
- Atomic merge discipline
- Verbatim quote validator
- Pre-publication calibration
- Status routing
- Single-writer final rendering
- Full audit trail on disk

## Evaluation metrics

You need two layers: cheap release gates every run, and slower external validation.

### Cheap enough for every release

- Finding support rate: share of surfaced findings marked `supported`.
- Overclaim rate: share marked `overclaimed_narrowed` or `dropped` after initial candidate stage.
- Final overclaim escape rate: share of user-visible findings later judged overclaimed in post-hoc audit.
- Quote verification rate: exact quote + correct location.
- Coverage against reference set: on benchmark papers with expert reference reviews, how many reference concerns are matched.
- Coarse overlap and improvement:
  - matched concerns
  - disputatio-only validated concerns
  - coarse-only validated concerns
- Author utility proxy: share of author-mode top-priority findings judged "worth fixing before submit" by an external annotator.
- Referee utility proxy: share of referee-mode `endorse` findings judged usable in a real referee report without material rewrite.

### Slower but necessary

- Blind side-by-side study with economists:
  - authors judge which system better helps them improve a near-submission paper
  - active referees judge which system better sharpens a first-round review
- Expert panel annotation:
  - senior PhD / postdoc / faculty annotators score findings for correctness, novelty, severity calibration, and actionability
- Pilot field test:
  - small set of real authors and referees use the product on live papers, then rate whether surfaced findings changed decisions or text

### Recommendation

For each release, run the cheap suite on 3-5 benchmark papers. Once every major version, run a human blind study on a smaller sample. That is the only credible way to claim advantage on the two real use cases.

## Landing-page positioning copy

Disputatio is for the two moments that matter before publication: before an author submits, and before a referee writes the report. Coarse gives you one polished model opinion; disputatio gives you a cross-model finding panel with exact quotes, support by architecture, contested-point debate, and explicit dropped claims. The point is not prettier prose. The point is knowing which concerns are real, which are stretched, and which are worth acting on before an editor or referee sees the paper. If you are deciding what to fix before submission, or what to endorse in your own review, that difference is worth much more than the price gap.

## One-page pitch to a senior editor

### Why this matters

Referee quality is uneven for a simple reason: most referees are time-constrained, and the first-pass review often mixes strong concerns with weaker speculative ones. Disputatio is a referee-assistance tool designed to improve that first pass. It does not replace the referee's judgment. It helps the referee separate concerns that are well-supported by the paper from concerns that only sound plausible on first reading.

### What is different

Most review assistants produce one polished opinion from one model. That is useful for drafting prose, but weak for calibration. Disputatio runs a panel across model families, compiles exact textual evidence for each candidate concern, escalates contested points into a structured challenge-response step, and records which claims were narrowed or dropped before the user sees the final panel. The output is not just a draft report. It is an auditable list of findings with evidence, support, and verdict history.

### Why referees would use it

For a referee, the practical value is speed with restraint. The system helps surface issues worth endorsing, flags concerns that should be verified before entering the report, and discards weaker claims that would otherwise dilute the review. That can improve signal quality in first-round reports without pushing referees toward generic, overconfident boilerplate.

### Why an editor should care

Editors do not need longer referee reports. They need reports with better calibrated judgment. A tool that helps referees write fewer stretched claims and more evidence-backed ones improves the usefulness of the review process even when the referee remains fully responsible for the final report. That is the narrow claim we would want to pilot and measure.
