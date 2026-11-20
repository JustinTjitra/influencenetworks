import pandas as pd

from influence.interlocks import merges


def _people(rows):
    return pd.DataFrame(rows, columns=["record_id", "name", "company", "role", "as_of"])


def _row(rid, name, company):
    return (rid, name, company, "Commissioner", "2024-12-31")


def test_identical_two_token_names_are_same():
    c = merges.candidates(_people([
        _row("r1", "Budi Santoso", "AAAA"), _row("r2", "Dr. Budi Santoso, S.E.", "BBBB"),
    ]))
    assert len(c) == 1
    row = c.iloc[0]
    assert row["suggestion"] == "same"
    assert bool(row["same_printed"]) is True
    assert row["token_overlap"] == 1.0
    assert row["shared_tokens"] == "BUDI SANTOSO"
    assert (row["record_a"], row["record_b"]) == ("r1", "r2")


def test_subset_names_are_review():
    c = merges.candidates(_people([
        _row("r1", "Budi Santoso", "AAAA"), _row("r2", "Budi Santoso Wijaya", "BBBB"),
    ]))
    assert len(c) == 1
    assert c.iloc[0]["suggestion"] == "review"
    assert bool(c.iloc[0]["same_printed"]) is False
    assert c.iloc[0]["token_overlap"] == 1.0


def test_identical_single_token_is_review():
    c = merges.candidates(_people([_row("r1", "Suharto", "AAAA"), _row("r2", "Suharto", "BBBB")]))
    assert list(c["suggestion"]) == ["review"]


def test_partial_overlap_and_unrelated_give_no_row():
    c = merges.candidates(_people([
        _row("r1", "Budi Santoso", "AAAA"),
        _row("r2", "Budi Wijaya", "BBBB"),      # shares only one of two tokens
        _row("r3", "Siti Rahma", "CCCC"),       # unrelated
    ]))
    assert c.empty
    assert list(c.columns) == merges.CANDIDATE_COLUMNS


def test_same_company_gives_no_row():
    c = merges.candidates(_people([
        _row("r1", "Budi Santoso", "AAAA"), _row("r2", "Budi Santoso", "AAAA"),
    ]))
    assert c.empty


def test_output_is_sorted_and_stable():
    p = _people([
        _row("r1", "Budi Santoso", "AAAA"), _row("r2", "Budi Santoso Wijaya", "BBBB"),
        _row("r3", "Agus Salim", "AAAA"), _row("r4", "Agus Salim", "BBBB"),
    ])
    c = merges.candidates(p)
    assert list(c["suggestion"]) == ["same", "review"]
    pd.testing.assert_frame_equal(c, merges.candidates(p.iloc[::-1].reset_index(drop=True)))


def test_decisions_survive_rewrite(tmp_path):
    path = tmp_path / "person_merges.csv"
    p = _people([
        _row("r1", "Budi Santoso", "AAAA"), _row("r2", "Budi Santoso", "BBBB"),
        _row("r3", "Agus Salim", "AAAA"), _row("r4", "Agus Salim", "BBBB"),
    ])
    c = merges.candidates(p)
    first = merges.write_review(c, path)
    assert (first["decision"] == "").all()
    assert list(pd.read_csv(path, dtype=str, keep_default_na=False).columns) == merges.REVIEW_COLUMNS

    df = pd.read_csv(path, dtype=str, keep_default_na=False)
    df.loc[df["record_a"] == "r1", ["decision", "decided_by"]] = ["same", "justin"]
    df.to_csv(path, index=False)

    merges.write_review(c, path)
    again = pd.read_csv(path, dtype=str, keep_default_na=False).set_index("record_a")
    assert again.loc["r1", "decision"] == "same"
    assert again.loc["r1", "decided_by"] == "justin"
    assert again.loc["r3", "decision"] == ""


def test_undecided_pairs_stay_separate(tmp_path):
    p = _people([_row("r1", "Budi Santoso", "AAAA"), _row("r2", "Budi Santoso", "BBBB")])
    c = merges.candidates(p)
    assert c.iloc[0]["suggestion"] == "same"
    review = merges.write_review(c, tmp_path / "m.csv")
    out = merges.apply_decisions(p, review)
    assert out["person_key"].nunique() == 2
    review["decision"] = "different"
    assert merges.apply_decisions(p, review)["person_key"].nunique() == 2


def test_chained_same_decisions_share_one_key(tmp_path):
    p = _people([
        _row("r1", "Budi Santoso", "AAAA"), _row("r2", "Budi Santoso", "BBBB"),
        _row("r3", "Budi Santoso", "CCCC"), _row("r4", "Agus Salim", "AAAA"),
    ])
    review = merges.write_review(merges.candidates(p), tmp_path / "m.csv")
    assert len(review) == 3
    pairs = {(r.record_a, r.record_b) for r in review.itertuples()}
    assert pairs == {("r1", "r2"), ("r1", "r3"), ("r2", "r3")}
    review.loc[(review.record_a == "r1") & (review.record_b == "r2"), "decision"] = "same"
    review.loc[(review.record_a == "r2") & (review.record_b == "r3"), "decision"] = "same"
    out = merges.apply_decisions(p, review).set_index("record_id")
    assert out.loc["r1", "person_key"] == out.loc["r2", "person_key"] == out.loc["r3", "person_key"]
    assert out.loc["r4", "person_key"] != out.loc["r1", "person_key"]
