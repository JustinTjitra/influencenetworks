"""Person merge candidates and the human review file.

Nothing is merged automatically.  Pairs of board members from different companies
that might be the same person are listed for a person to accept or reject; only
pairs marked ``same`` in the review file are joined (see CLAUDE.md, hard rule 3).
"""

from __future__ import annotations

from itertools import combinations
from pathlib import Path

import pandas as pd

from influence.interlocks import names

CANDIDATE_COLUMNS = [
    "record_a", "record_b", "name_a", "name_b", "company_a", "company_b",
    "shared_tokens", "token_overlap", "same_printed", "suggestion",
]
REVIEW_COLUMNS = CANDIDATE_COLUMNS + ["decision", "decided_by"]
_SUGGESTION_ORDER = {"same": 0, "review": 1}


def candidates(people: pd.DataFrame) -> pd.DataFrame:
    """Pairs of records in different companies that share a block key."""
    recs = []
    for r in people.itertuples(index=False):
        recs.append((str(r.record_id), str(r.name), str(r.company),
                     names.tokens(r.name), names.block_keys(r.name)))
    rows = []
    for a, b in combinations(recs, 2):
        if a[2] == b[2] or not (a[4] & b[4]):
            continue
        if b[0] < a[0]:
            a, b = b, a
        tok_a, tok_b = a[3], b[3]
        shared = sorted(set(tok_a) & set(tok_b))
        shorter = min(len(set(tok_a)), len(set(tok_b)))
        overlap = len(shared) / shorter if shorter else 0.0
        same = names.same_printed(a[1], b[1])
        if same and len(tok_a) >= 2:
            suggestion = "same"
        elif overlap == 1.0 and (not same or len(tok_a) == 1):
            suggestion = "review"
        else:
            continue
        rows.append({
            "record_a": a[0], "record_b": b[0], "name_a": a[1], "name_b": b[1],
            "company_a": a[2], "company_b": b[2],
            "shared_tokens": " ".join(shared), "token_overlap": overlap,
            "same_printed": same, "suggestion": suggestion,
        })
    out = pd.DataFrame(rows, columns=CANDIDATE_COLUMNS)
    if out.empty:
        return out
    out["_order"] = out["suggestion"].map(_SUGGESTION_ORDER)
    out = out.sort_values(["_order", "name_a", "name_b", "record_a", "record_b"])
    return out.drop(columns="_order").reset_index(drop=True)


def _read_review(path: Path) -> pd.DataFrame:
    df = pd.read_csv(path, dtype=str, keep_default_na=False)
    for col in REVIEW_COLUMNS:
        if col not in df.columns:
            df[col] = ""
    return df[REVIEW_COLUMNS]


def write_review(cands: pd.DataFrame, path) -> pd.DataFrame:
    """Write the review file, keeping decisions already made for the same pair."""
    path = Path(path)
    out = cands.copy()
    out["record_a"] = out["record_a"].astype(str)
    out["record_b"] = out["record_b"].astype(str)
    out["decision"] = ""
    out["decided_by"] = ""
    out = out[REVIEW_COLUMNS]
    if path.exists():
        old = _read_review(path)
        old = old[old["decision"] != ""]
        prev = {(r.record_a, r.record_b): (r.decision, r.decided_by)
                for r in old.itertuples(index=False)}
        for i, r in out.iterrows():
            key = (r["record_a"], r["record_b"])
            if key in prev:
                out.at[i, "decision"], out.at[i, "decided_by"] = prev[key]
        # a decision made by a person is never dropped, even if the pair
        # is no longer a candidate
        current = set(zip(out["record_a"], out["record_b"]))
        kept = old[[(a, b) not in current
                    for a, b in zip(old["record_a"], old["record_b"])]]
        if not kept.empty:
            out = pd.concat([out, kept], ignore_index=True)
    out.to_csv(path, index=False)
    return out


def apply_decisions(people: pd.DataFrame, review: pd.DataFrame) -> pd.DataFrame:
    """Add ``person_key``; records joined by a ``same`` decision share one key."""
    ids = [str(x) for x in people["record_id"]]
    parent = {i: i for i in ids}

    def find(x: str) -> str:
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    for r in review.itertuples(index=False):
        if str(r.decision).strip().lower() != "same":
            continue
        a, b = str(r.record_a), str(r.record_b)
        if a not in parent or b not in parent:
            continue
        ra, rb = find(a), find(b)
        if ra != rb:
            # the smaller record id becomes the root, so keys are stable
            lo, hi = sorted((ra, rb))
            parent[hi] = lo
    out = people.copy()
    out["person_key"] = ["P:" + find(i) for i in ids]
    return out
