# /// script
# requires-python = ">=3.10"
# dependencies = ["networkx>=3.0"]
# ///
"""
Argument-DAG structural analyzer — the deterministic half of the hybrid.

An LLM extracts the paper's argument dependency graph (nodes = claims/assumptions/
results, edges `from -> to` meaning "from DEPENDS ON to"). This script computes the
structural properties an LLM does unreliably but classical algorithms do exactly and
~free, and maps each property to the referee finding it predicts:

  load-bearing      = |ancestors(v)| (how many claims transitively depend on v)
                      -> central-result / severity prior
  articulation pt   = cut vertex on the undirected projection
                      -> single point of failure (critical assumption to attack)
  cycle             = directed cycle (acyclicity violation)
                      -> circular reasoning
  non-primitive sink= out_degree 0 but it's a substantive claim, not a primitive
                      -> gap (asserted, never supported)
  floating headline = headline/claim with no support path to any formal/data node
                      -> scope/framing overreach
  longest chain     = deepest dependency path
                      -> fragile derivation (where to point M8)

Usage:
  uv run experiments/argument-graph/analyze.py <graph.json> [--report out.json]

Edge convention: edge (u, v) means "u depends on v"; arrows point toward primitives.
"""
import argparse
import json
import sys

import networkx as nx

PRIMITIVE_TYPES = {"assumption", "identifying_assumption", "definition", "data", "equation"}
FORMAL_TYPES = {"proposition", "result", "estimate", "equation", "data", "mechanism"}


def load_graph(path):
    with open(path) as f:
        doc = json.load(f)
    G = nx.DiGraph()
    for n in doc["nodes"]:
        G.add_node(n["id"], **{k: n.get(k) for k in ("type", "label", "location", "role", "quote")})
    missing = []
    for e in doc["edges"]:
        if e["from"] not in G or e["to"] not in G:
            missing.append((e["from"], e["to"]))
            continue
        G.add_edge(e["from"], e["to"], type=e.get("type"), rationale=e.get("rationale"))
    return doc, G, missing


def label(G, nid):
    d = G.nodes[nid]
    return f'{nid} [{d.get("type")}] {d.get("label") or ""}'.strip()


def heat_buckets(load):
    """Ordinal heat tiers, NOT numeric severity. Centrality on a 40-60 node graph is
    a modeling artifact (one mis-drawn edge moves it), so we bucket rather than rank
    by raw number. Per codex review 2026-06-17."""
    if not load:
        return {}
    mx = max(d for _, d, _ in load) or 1
    out = {}
    for v, d, _ in load:
        frac = d / mx
        out[v] = ("critical" if d and frac >= 0.66 else
                  "high" if frac >= 0.33 else
                  "medium" if d else "low")
    return out


def critical_nodes(G):
    """Directed single-points-of-failure via DOMINATOR analysis, which respects edge
    direction (undirected articulation points throw the dependency direction away —
    codex review 2026-06-17). A node's strength = size of the support sub-tree it
    uniquely gates under a headline: remove it and that chunk of the headline's
    support is cut off."""
    from collections import defaultdict
    headlines = [n for n in G if G.nodes[n].get("role") == "headline"] or \
                [n for n in G if G.in_degree(n) == 0]
    strength = {}
    for h in headlines:
        reach = nx.descendants(G, h) | {h}
        sub = G.subgraph(reach)
        try:
            idom = nx.immediate_dominators(sub, h)
        except Exception:
            continue
        children = defaultdict(list)
        for n, d in idom.items():
            if n != d:
                children[d].append(n)

        def subtree(root):
            stack, cnt = list(children[root]), 0
            while stack:
                x = stack.pop()
                cnt += 1
                stack.extend(children[x])
            return cnt

        for n in reach:
            if n != h:
                strength[n] = max(strength.get(n, 0), subtree(n))
    crit = [(n, s) for n, s in strength.items()
            if s > 0 and G.nodes[n].get("role") != "headline"]
    crit.sort(key=lambda t: t[1], reverse=True)
    return crit


def analyze(doc, G, missing):
    out = {"paper": doc.get("paper"), "n_nodes": G.number_of_nodes(), "n_edges": G.number_of_edges()}
    rep = []
    rep.append(f"# Argument-DAG analysis — {doc.get('paper')}")
    rep.append(f"\nnodes: {G.number_of_nodes()}  edges: {G.number_of_edges()}"
               + (f"  (dropped {len(missing)} edges referencing unknown nodes)" if missing else ""))
    rep.append("\n> TARGETING HYPOTHESES from an LLM-extracted graph — NOT findings. Exact computation"
               "\n> on a noisy graph is not exact evidence; every flag below must be confirmed by semantic"
               "\n> calibration downstream. Centrality is an ordinal targeting prior, not severity.")

    # --- acyclicity / circular reasoning ---
    is_dag = nx.is_directed_acyclic_graph(G)
    cycles = [] if is_dag else list(nx.simple_cycles(G))
    out["is_dag"] = is_dag
    out["cycles"] = cycles
    rep.append(f"\n## Acyclic? {is_dag}")
    if cycles:
        rep.append("CIRCULAR REASONING candidates (directed cycles):")
        for c in cycles[:20]:
            rep.append("  - " + " -> ".join(c) + " -> " + c[0])

    # --- load-bearing: how many nodes transitively depend on v ---
    btw = nx.betweenness_centrality(G) if G.number_of_nodes() > 2 else {n: 0.0 for n in G}
    load = []
    for v in G.nodes:
        deps = len(nx.ancestors(G, v))  # nodes that can reach v == depend on v
        load.append((v, deps, round(btw.get(v, 0.0), 4)))
    load.sort(key=lambda t: (t[1], t[2]), reverse=True)
    buckets = heat_buckets(load)
    out["load_bearing"] = [{"id": v, "dependents": d, "betweenness": b, "tier": buckets[v]}
                           for v, d, b in load]
    rep.append("\n## Load-bearing nodes (ordinal targeting prior — NOT severity)")
    for tier in ("critical", "high"):
        ids = [v for v, d, b in load if buckets[v] == tier]
        if ids:
            rep.append(f"  [{tier}]")
            for v in ids[:8]:
                rep.append(f"     {label(G, v)}")

    # --- critical nodes: directed dominators (single points of failure) ---
    crit = critical_nodes(G)
    out["critical_nodes"] = [{"id": v, "gates": s} for v, s in crit]
    rep.append("\n## Critical nodes (directed dominators -> single points of failure / key assumptions)")
    for v, s in crit[:10]:
        rep.append(f"  gates {s:>3} support-nodes  {label(G, v)}")

    # --- gaps: non-primitive sinks (substantive claim depending on nothing) ---
    gaps = [v for v in G.nodes
            if G.out_degree(v) == 0
            and G.nodes[v].get("role") != "primitive"
            and G.nodes[v].get("type") not in PRIMITIVE_TYPES]
    out["gap_candidates"] = gaps
    rep.append("\n## Gap candidates (substantive claim with NO support edge)")
    for v in gaps:
        rep.append(f"  - {label(G, v)}   @ {G.nodes[v].get('location')}")

    # --- framing overreach: headline/claim that can't reach any formal/data node ---
    floaters = []
    for v in G.nodes:
        d = G.nodes[v]
        if d.get("role") == "headline" or d.get("type") == "claim":
            desc = nx.descendants(G, v)
            if not any(G.nodes[u].get("type") in FORMAL_TYPES for u in desc):
                floaters.append(v)
    out["framing_overreach_candidates"] = floaters
    rep.append("\n## Framing-overreach candidates (headline/claim with no path to formal evidence)")
    for v in floaters:
        rep.append(f"  - {label(G, v)}   @ {G.nodes[v].get('location')}")

    # --- disconnected components ---
    comps = sorted((sorted(c) for c in nx.weakly_connected_components(G)), key=len, reverse=True)
    out["n_components"] = len(comps)
    if len(comps) > 1:
        rep.append(f"\n## Disconnected: {len(comps)} weakly-connected components "
                   f"(sizes {[len(c) for c in comps]}) — argument is not one connected structure")

    # --- longest dependency chain (fragility / M8 target) ---
    if is_dag and G.number_of_nodes():
        path = nx.dag_longest_path(G)
        out["longest_chain"] = path
        rep.append(f"\n## Longest dependency chain (len {len(path)}  ->  fragile derivation / M8 target)")
        rep.append("  " + " -> ".join(path))

    return out, "\n".join(rep)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("graph")
    ap.add_argument("--report", help="write JSON report here")
    args = ap.parse_args()
    doc, G, missing = load_graph(args.graph)
    out, text = analyze(doc, G, missing)
    print(text)
    if args.report:
        with open(args.report, "w") as f:
            json.dump(out, f, indent=2)
        print(f"\n[report written: {args.report}]", file=sys.stderr)


if __name__ == "__main__":
    main()
