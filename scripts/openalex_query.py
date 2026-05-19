#!/usr/bin/env python3
"""Thin OpenAlex query helper for the literature_engagement track (v2).

No API key required. Uses the "polite pool" (mailto query param) for
priority. All endpoints documented at https://docs.openalex.org/.

Subcommands:
  resolve <author> <title-fragment>       → top Work ID for a paper
  intersect <W_A> <W_B> [--max N]         → works citing both ancestors
  single <W_A> --concept <C_id> [--max N] → fallback: cites W_A + concept filter
  abstract <W_id>                          → reconstruct abstract text from inverted index
  concept-search <term>                    → search OpenAlex concept IDs

Output: JSON to stdout.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
import urllib.parse
import urllib.request

BASE = "https://api.openalex.org"
DEFAULT_MAILTO = os.environ.get("OPENALEX_MAILTO", "")


def _get(path: str, params: dict) -> dict:
    if DEFAULT_MAILTO:
        params.setdefault("mailto", DEFAULT_MAILTO)
    qs = urllib.parse.urlencode(params, safe=":,")
    url = f"{BASE}{path}?{qs}"
    for attempt in range(4):
        try:
            with urllib.request.urlopen(url, timeout=30) as resp:
                return json.loads(resp.read().decode())
        except urllib.error.HTTPError as e:
            if e.code == 429 and attempt < 3:
                time.sleep(60 * (2 ** attempt))
                continue
            raise


def resolve(author: str, title_fragment: str) -> dict:
    """Return the top OpenAlex Work matching an author surname + title-fragment.

    Uses `filter=raw_author_name.search:<author>` to constrain by author and
    `search=<title_fragment>` for relevance-ranked text match — combining a
    bare `search=author title` query is much noisier (the relevance ranker
    favors highly-cited unrelated papers when the author surname is common).
    """
    data = _get("/works", {
        "search": title_fragment.strip(),
        "filter": f"raw_author_name.search:{author.strip().split()[-1]}",
        "per-page": "3",
    })
    results = data.get("results", [])
    if not results:
        return {"ok": False, "reason": "no_results", "query": q}
    top = results[0]
    return {
        "ok": True,
        "openalex_id": top["id"].rsplit("/", 1)[-1],
        "title": top.get("title"),
        "authors": [a["author"]["display_name"]
                    for a in top.get("authorships", [])[:5]],
        "year": top.get("publication_year"),
        "venue": ((top.get("primary_location") or {}).get("source") or {}).get("display_name"),
        "doi": top.get("doi"),
        "cited_by_count": top.get("cited_by_count"),
        "alternatives": [
            {"openalex_id": r["id"].rsplit("/", 1)[-1], "title": r.get("title"),
             "year": r.get("publication_year")}
            for r in results[1:]
        ],
    }


def intersect(work_a: str, work_b: str, max_n: int = 50) -> dict:
    """Return works citing both Work IDs, sorted by cited_by_count desc."""
    data = _get("/works", {
        "filter": f"cites:{work_a},cites:{work_b}",
        "per-page": str(min(max_n, 200)),
        "sort": "cited_by_count:desc",
    })
    return {
        "ok": True,
        "ancestor_pair": [work_a, work_b],
        "n_results": data.get("meta", {}).get("count"),
        "works": [_summarise(w) for w in data.get("results", [])[:max_n]],
    }


def single(work_a: str, concept_id: str, max_n: int = 50) -> dict:
    """Fallback: works citing W_A + concept filter, sorted by cited_by_count desc."""
    data = _get("/works", {
        "filter": f"cites:{work_a},concepts.id:{concept_id}",
        "per-page": str(min(max_n, 200)),
        "sort": "cited_by_count:desc",
    })
    return {
        "ok": True,
        "ancestor": work_a,
        "concept": concept_id,
        "n_results": data.get("meta", {}).get("count"),
        "works": [_summarise(w) for w in data.get("results", [])[:max_n]],
    }


def abstract(work_id: str) -> dict:
    """Reconstruct abstract text from OpenAlex's inverted-index format."""
    data = _get(f"/works/{work_id}", {})
    inv = data.get("abstract_inverted_index") or {}
    if not inv:
        return {"ok": False, "reason": "no_abstract", "openalex_id": work_id}
    positions: list[tuple[int, str]] = []
    for word, pos_list in inv.items():
        for p in pos_list:
            positions.append((p, word))
    positions.sort()
    return {
        "ok": True,
        "openalex_id": work_id,
        "title": data.get("title"),
        "abstract": " ".join(w for _, w in positions),
    }


def concept_search(term: str) -> dict:
    """Look up OpenAlex concept IDs matching a search term."""
    data = _get("/concepts", {"search": term, "per-page": "5"})
    return {
        "ok": True,
        "query": term,
        "concepts": [
            {"id": c["id"].rsplit("/", 1)[-1],
             "name": c["display_name"],
             "level": c.get("level"),
             "works_count": c.get("works_count")}
            for c in data.get("results", [])
        ],
    }


SS_BASE = "https://api.semanticscholar.org"


def _ss_get(path: str, params: dict | None = None) -> dict:
    qs = ("?" + urllib.parse.urlencode(params, safe=":,")) if params else ""
    url = f"{SS_BASE}{path}{qs}"
    for attempt in range(4):
        try:
            with urllib.request.urlopen(url, timeout=30) as resp:
                return json.loads(resp.read().decode())
        except urllib.error.HTTPError as e:
            if e.code == 429 and attempt < 3:
                time.sleep(30 * (2 ** attempt))
                continue
            raise


def ss_resolve(doi_or_query: str) -> dict:
    """Resolve a paper on Semantic Scholar. Accepts DOI:..., openalex:W..., or free-text."""
    if doi_or_query.lower().startswith("doi:"):
        return _ss_get(f"/graph/v1/paper/{doi_or_query}",
                       {"fields": "title,year,citationCount,referenceCount,authors,externalIds,venue"})
    data = _ss_get("/graph/v1/paper/search",
                   {"query": doi_or_query, "limit": "3",
                    "fields": "title,year,citationCount,authors,externalIds,venue"})
    return {"ok": True, "candidates": data.get("data", [])}


def ss_intersect(paper_a: str, paper_b: str, max_per_side: int = 200, max_out: int = 30) -> dict:
    """Fetch citations of both papers from Semantic Scholar and intersect client-side.

    Semantic Scholar has denser citation coverage than OpenAlex for older econ
    papers (e.g. Hirshleifer 1990: 181 cites on SS vs 41 on OpenAlex) but does
    not support native AND-filter — so we paginate both citation sets and
    intersect by paperId locally.
    """
    def _fetch_citations(pid: str) -> list[dict]:
        out: list[dict] = []
        offset = 0
        while len(out) < max_per_side:
            data = _ss_get(f"/graph/v1/paper/{pid}/citations",
                           {"fields": "title,year,citationCount,venue,externalIds",
                            "limit": "100", "offset": str(offset)})
            page = data.get("data", [])
            if not page:
                break
            out.extend(page)
            offset += len(page)
            if len(page) < 100:
                break
        return out

    cites_a = _fetch_citations(paper_a)
    cites_b = _fetch_citations(paper_b)
    ids_b = {c["citingPaper"]["paperId"] for c in cites_b
             if c.get("citingPaper", {}).get("paperId")}
    intersection = [c["citingPaper"] for c in cites_a
                    if c.get("citingPaper", {}).get("paperId") in ids_b]
    intersection.sort(key=lambda p: p.get("citationCount") or 0, reverse=True)
    return {
        "ok": True,
        "engine": "semantic_scholar",
        "ancestor_pair": [paper_a, paper_b],
        "n_cites_a": len(cites_a),
        "n_cites_b": len(cites_b),
        "n_intersection": len(intersection),
        "works": [
            {"paper_id": p.get("paperId"),
             "title": p.get("title"),
             "year": p.get("year"),
             "venue": p.get("venue"),
             "cited_by_count": p.get("citationCount"),
             "external_ids": p.get("externalIds")}
            for p in intersection[:max_out]
        ],
    }


def _summarise(work: dict) -> dict:
    return {
        "openalex_id": work["id"].rsplit("/", 1)[-1],
        "title": work.get("title"),
        "authors": [a["author"]["display_name"]
                    for a in work.get("authorships", [])[:5]],
        "year": work.get("publication_year"),
        "venue": ((work.get("primary_location") or {}).get("source") or {}).get("display_name"),
        "doi": work.get("doi"),
        "cited_by_count": work.get("cited_by_count"),
    }


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest="cmd", required=True)

    r = sub.add_parser("resolve", help="resolve an author+title-fragment to a Work ID")
    r.add_argument("author")
    r.add_argument("title_fragment")

    i = sub.add_parser("intersect", help="works citing both ancestors")
    i.add_argument("work_a")
    i.add_argument("work_b")
    i.add_argument("--max", type=int, default=50)

    s = sub.add_parser("single", help="fallback: cites W_A + concept filter")
    s.add_argument("work_a")
    s.add_argument("--concept", required=True)
    s.add_argument("--max", type=int, default=50)

    a = sub.add_parser("abstract", help="reconstruct a work's abstract text")
    a.add_argument("work_id")

    cs = sub.add_parser("concept-search", help="search for OpenAlex concept IDs")
    cs.add_argument("term")

    ssr = sub.add_parser("ss-resolve", help="resolve a paper on Semantic Scholar (denser citation graph for econ)")
    ssr.add_argument("doi_or_query", help="'DOI:10.xxxx' or free-text title/author")

    ssi = sub.add_parser("ss-intersect", help="client-side citation intersection via Semantic Scholar (denser than OpenAlex)")
    ssi.add_argument("paper_a", help="Semantic Scholar paperId (40-char hex) OR DOI:...")
    ssi.add_argument("paper_b", help="Semantic Scholar paperId OR DOI:...")
    ssi.add_argument("--max-per-side", type=int, default=200)
    ssi.add_argument("--max", type=int, default=30, dest="max_out")

    args = p.parse_args()
    if args.cmd == "resolve":
        out = resolve(args.author, args.title_fragment)
    elif args.cmd == "intersect":
        out = intersect(args.work_a, args.work_b, args.max)
    elif args.cmd == "single":
        out = single(args.work_a, args.concept, args.max)
    elif args.cmd == "abstract":
        out = abstract(args.work_id)
    elif args.cmd == "concept-search":
        out = concept_search(args.term)
    elif args.cmd == "ss-resolve":
        out = ss_resolve(args.doi_or_query)
    elif args.cmd == "ss-intersect":
        out = ss_intersect(args.paper_a, args.paper_b, args.max_per_side, args.max_out)
    else:
        p.error("unknown subcommand")
    json.dump(out, sys.stdout, indent=2)
    print()
    return 0


if __name__ == "__main__":
    sys.exit(main())
