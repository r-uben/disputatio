# /// script
# requires-python = ">=3.10"
# dependencies = []
# ///
"""
Generate the disputatio v9 architecture as an Obsidian .canvas — one board to read the
whole flow. Colour = model tier (red=frontier/judgment, green=mechanical/cheap-able,
yellow=opt-in/dev). Encodes the v9 target from docs/log/2026-06-18_v9-architecture.md.

  uv run experiments/architecture-canvas/build.py [out.canvas]
"""
import json
import sys

# Obsidian canvas preset colours: 1 red, 2 orange, 3 yellow, 4 green, 5 cyan, 6 purple
RED, ORANGE, YELLOW, GREEN, CYAN, PURPLE = "1", "2", "3", "4", "5", "6"
TIER = {"front": RED, "mech": GREEN, "optin": YELLOW, "gate": PURPLE}

# (id, level, label, tier, x-slot)  — level = vertical order; x-slot spreads a parallel row
SPINE = [
    ("init",     0, "0 · Init / OCR / preflight\nsocr; copy worker manuals", "mech", 1),
    ("orient",   1, "0 · Orientation\n3 independent paper maps (parallel)", "mech", 1),
    ("holistic", 2, "1 · Holistic pass\nspine + attack-surface index · 3 families", "front", 1),
    ("graph_x",  3, "1.25 · Argument-graph extraction  [NEW]\n>=2 extractors, evidence-anchored nodes/edges", "front", 1),
    ("graph_a",  4, "1.3 · Graph analysis  [NEW]\ndominators + ordinal heat buckets (networkx, ~free)", "mech", 1),
    ("lit",      5, "1.75 · Literature-lite\ncapped frontier+web, soft-fail, non-blocking", "front", 1),
    ("disc_hc",  6, "2 · holistic_candidates\nconceptual-scope concerns", "mech", 0),
    ("disc_bc",  6, "2 · broad_critic + scope/framing\ncontradictions, overreach", "front", 1),
    ("disc_ne",  6, "2 · narrow_evidence + M8 + obligations + validity\nTARGETED at graph dominators", "front", 2),
    ("evid",     7, "2 · Evidence compiler\nverbatim-quote validation (deterministic)", "mech", 1),
    ("merge",    8, "3 · Merge / rank / web-verify\ncarry graph_prior as metadata", "front", 1),
    ("calib",    9, "· Unified contract calibration\nsmall bulk + frontier re-annotator on material\nREPLACES 3g/3v/3s/3e/5a", "front", 1),
    ("gate",    10, "4 · Escalation gate\nRoute A (4 conds) · Route B (consensus) · skip", "gate", 1),
    ("debate",  11, "4 · Debate\nprosecute->defend->synthesize / red-team", "front", 0),
    ("final",   12, "5b · Finalize\ncapture surviving_text -> final_findings.json", "mech", 1),
    ("render",  13, "6 · Panel + render + Canvas heatmap\nrenderer cannot invent findings", "mech", 1),
]

EDGES = [
    ("init", "orient"), ("orient", "holistic"), ("holistic", "graph_x"),
    ("graph_x", "graph_a"), ("graph_a", "lit"),
    ("lit", "disc_hc"), ("lit", "disc_bc"), ("lit", "disc_ne"),
    ("graph_a", "disc_ne", "targets dominators"),
    ("disc_hc", "evid"), ("disc_bc", "evid"), ("disc_ne", "evid"),
    ("evid", "merge"), ("merge", "calib"), ("calib", "gate"),
    ("gate", "debate", "Route A / B"), ("gate", "final", "skip / no escalation"),
    ("debate", "final"), ("final", "render"),
]

W, H, COLW, ROWH, X0, Y0 = 330, 120, 380, 210, 0, 0


def build():
    nodes, pos = [], {}
    for nid, level, label, tier, slot in SPINE:
        x, y = X0 + slot * COLW, Y0 + level * ROWH
        pos[nid] = (x, y)
        nodes.append({"id": nid, "type": "text", "text": f"**{label}**",
                      "x": x, "y": y, "width": W, "height": H, "color": TIER[tier]})
    edges = []
    for i, e in enumerate(EDGES):
        u, v = e[0], e[1]
        ed = {"id": f"e{i}", "fromNode": u, "toNode": v, "fromSide": "bottom", "toSide": "top"}
        if len(e) == 3:
            ed["label"] = e[2]
            ed["color"] = ORANGE
        edges.append(ed)
    # legend + side cards
    nodes.append({"id": "legend", "type": "text",
                  "text": "**disputatio v9 — target architecture**\n\nColour = model tier:\n"
                          "\U0001F534 frontier / judgment (cost targets)\n"
                          "\U0001F7E2 mechanical / cheap-able (small/local)\n"
                          "\U0001F7E1 opt-in / dev\n\U0001F7E3 decision gate\n\n"
                          "Arrows point in flow order. Source: docs/log/2026-06-18_v9-architecture.md",
                  "x": X0 - 460, "y": Y0, "width": 420, "height": 280, "color": CYAN})
    nodes.append({"id": "bench", "type": "text",
                  "text": "**_benchmark harness (dev)**\n8-stage head-to-head + cost ledger\nthe dual ruler — measures quality + EUR/paper",
                  "x": X0 - 460, "y": Y0 + 3 * ROWH, "width": 420, "height": 120, "color": YELLOW})
    nodes.append({"id": "cut", "type": "text",
                  "text": "**Folded in / cut (v9):**\nv8 audit tracks 1.5/2.5/2.6 -> discovery sub-tasks (checks kept)\n2.7 exposition -> cut from default (gated on benchmark)\n5 calibrators -> 1 unified node",
                  "x": X0 + 3 * COLW, "y": Y0 + 9 * ROWH, "width": 420, "height": 150, "color": ORANGE})
    return {"nodes": nodes, "edges": edges}


if __name__ == "__main__":
    out = sys.argv[1] if len(sys.argv) > 1 else "disputatio_v9_architecture.canvas"
    with open(out, "w") as f:
        json.dump(build(), f, indent=2)
    print(f"wrote {out}")
