import datetime as dt

import pandas as pd

from influence.interlocks.graph import active, interlocks, summary, to_networkx

D = dt.date
ON = D(2024, 6, 30)

COMPANIES = pd.DataFrame(
    [
        ("A", "S1", "G1"),
        ("B", "S1", "G1"),  # same group and same sub-industry as A
        ("C", "S1", ""),
        ("D", "S3", "G2"),
        ("E", "S4", ""),
    ],
    columns=["company", "sub_industry", "group"],
)

SEATS = pd.DataFrame(
    [
        ("p1", "A", "director", D(2020, 1, 1), None),
        ("p1", "B", "director", D(2021, 1, 1), None),
        ("p4", "A", "commissioner", D(2022, 1, 1), D(2024, 6, 30)),  # ends on the date
        ("p4", "B", "commissioner", D(2024, 6, 30), None),  # starts on the date
        ("p2", "A", "director", None, None),
        ("p2", "C", "director", D(2019, 1, 1), D(2025, 1, 1)),
        ("p3", "C", "director", D(2023, 1, 1), None),
        ("p3", "D", "director", D(2023, 1, 1), None),
        ("p3", "E", "director", D(2023, 1, 1), None),
        ("p5", "B", "director", D(2018, 1, 1), D(2024, 6, 29)),  # ended the day before
        ("p5", "D", "director", D(2018, 1, 1), None),
        ("p6", "A", "director", D(2024, 7, 1), None),  # starts the day after
        ("p6", "E", "director", D(2020, 1, 1), None),
    ],
    columns=["person_key", "company", "role", "start", "end"],
)

# Links on 2024-06-30, worked out by hand:
#   A-B: p1 and p4 (p4's seats touch the date at both ends)   -> n_shared 2, intra_group
#   A-C: p2                                                   -> 1, horizontal (S1, no group)
#   C-D, C-E, D-E: p3 sits on C, D and E (three boards)       -> 1 each, other
#   not linked: B-D (p5's B seat ended 06-29), A-E (p6's A seat starts 07-01)
# 5 links; all 5 companies appear; possible pairs = 5*4/2 = 10; density = 5/10 = 0.5
# kinds: intra_group 1, horizontal 1, other 3.


def links():
    return interlocks(SEATS, COMPANIES, ON)


def pairs(df):
    return set(zip(df.company_a, df.company_b))


def test_active_is_inclusive_and_open_ended():
    got = active(SEATS, ON)
    kept = set(zip(got.person_key, got.company))
    assert ("p4", "A") in kept and ("p4", "B") in kept  # both boundaries
    assert ("p2", "A") in kept  # both ends open
    assert ("p5", "B") not in kept  # ended the day before
    assert ("p6", "A") not in kept  # starts the day after
    assert len(got) == 11


def test_seat_ended_day_before_does_not_link():
    assert ("B", "D") not in pairs(links())
    earlier = interlocks(SEATS, COMPANIES, D(2024, 6, 29))
    assert ("B", "D") in pairs(earlier)


def test_seat_starting_after_date_does_not_link():
    assert ("A", "E") not in pairs(links())
    later = interlocks(SEATS, COMPANIES, D(2024, 7, 1))
    assert ("A", "E") in pairs(later)


def test_kinds():
    kind = {(r.company_a, r.company_b): r.kind for r in links().itertuples()}
    assert kind[("A", "B")] == "intra_group"  # same group wins over same sub-industry
    assert kind[("A", "C")] == "horizontal"
    assert kind[("C", "D")] == "other"
    assert kind[("C", "E")] == "other"
    assert kind[("D", "E")] == "other"


def test_person_on_three_boards_gives_three_links():
    only = SEATS[SEATS.person_key == "p3"]
    got = interlocks(only, COMPANIES, ON)
    assert pairs(got) == {("C", "D"), ("C", "E"), ("D", "E")}
    assert list(got.n_shared) == [1, 1, 1]


def test_shared_people_and_alphabetical_pairs():
    df = links()
    assert len(df) == 5
    assert all(a < b for a, b in zip(df.company_a, df.company_b))
    ab = df[(df.company_a == "A") & (df.company_b == "B")].iloc[0]
    assert ab.n_shared == 2
    assert ab.shared_people == "p1;p4"


def test_summary_numbers():
    s = summary(links(), COMPANIES)
    assert s["n_companies"] == 5
    assert s["n_linked_companies"] == 5
    assert s["by_kind"] == {"intra_group": 1, "horizontal": 1, "other": 3}
    assert s["density"] == 0.5


def test_summary_counts_unlinked_company():
    s = summary(interlocks(SEATS[SEATS.person_key == "p2"], COMPANIES, ON), COMPANIES)
    assert s["n_linked_companies"] == 2  # only A and C
    assert s["density"] == 1 / 10


def test_to_networkx_edge_attributes():
    g = to_networkx(links())
    assert g.number_of_nodes() == 5 and g.number_of_edges() == 5
    assert g["A"]["B"]["n_shared"] == 2
    assert g["A"]["B"]["kind"] == "intra_group"
    assert g["C"]["D"]["kind"] == "other"


def test_empty_result():
    got = interlocks(SEATS, COMPANIES, D(1990, 1, 1))
    assert got.empty
    assert list(got.columns) == ["company_a", "company_b", "n_shared", "shared_people", "kind"]
