You are matching substantive concerns raised in two reviews of the same research paper.

Each review has been parsed into a list of atomic concerns. Each concern has an id (e.g. X3, Y17), a short title, and a body explaining the issue. "X" ids come from Review X; "Y" ids come from Review Y. The two reviews may differ in length and may overlap on some concerns and diverge on others.

Your job: for each concern in Review X, decide whether Review Y raises the SAME substantive concern about the SAME paper feature (equation, table, figure, claim, gap, design decision). Same-concern matching is by content, not by wording or location:

- X[i] is matched to Y[j] if both raise the same flaw in the same paper feature, even if X says it as a one-line detailed comment and Y says it as part of an overall-feedback paragraph.
- Two X items that both happen to map to the same Y item are valid (rare but possible) — record both matches.
- X[i] is unmatched if no part of Y addresses the same paper feature with the same substantive criticism. Mere topical adjacency does not count: if both reviews mention Section 3 but raise different specific flaws, those are not matched.

Return STRICT JSON only — no prose around it — with this shape:

{{
"matches": [
{{"x_id": "<X concern id>", "y_id": "<Y concern id>", "confidence": "high"|"medium"|"low", "note": "<one short clause naming the shared concern>"}}
],
"x_unmatched": ["<X concern ids with no match in Y>"],
"y_unmatched": ["<Y concern ids that none of the matches reference>"]
}}

Use confidence:
high — clearly the same flaw in the same paper feature.
medium — same paper feature but the framing/take differs slightly; still the same underlying concern.
low — both touch the same area but the criticisms are in tension or only partially overlap.

Do not invent ids. Do not include items that are not in the inputs.

── Review X concerns ──

{x_block}

── Review Y concerns ──

{y_block}

Return only the JSON object.
