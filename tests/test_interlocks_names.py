import pytest

from influence.interlocks.names import (
    TITLES,
    block_keys,
    normalise,
    same_printed,
    tokens,
)


@pytest.mark.parametrize(
    "raw, expected",
    [
        ("Ir. H. Joko Widodo", "JOKO WIDODO"),
        ("Dr. (H.C.) Ir. Airlangga Hartarto, M.B.A., M.M.T.", "AIRLANGGA HARTARTO"),
        ("Sri Mulyani Indrawati, S.E., M.Sc., Ph.D.", "SRI MULYANI INDRAWATI"),
        ("Suharto", "SUHARTO"),
        ("Irawan", "IRAWAN"),
        ("Ir. Irawan", "IRAWAN"),
        ("Ir", "IR"),
        ("Ir.", "IR"),
        ("  Joko   Widodo  ", "JOKO WIDODO"),
        ("Joko  Widodo,", "JOKO WIDODO"),
        ("Joko Widodo, , ,", "JOKO WIDODO"),
        ("joko widodo", "JOKO WIDODO"),
        ("ir. h. joko widodo, s.e.", "JOKO WIDODO"),
        ("Hj. Siti Nurbaya", "SITI NURBAYA"),
        ("Prof. Dr. Drs. Bambang Brodjonegoro", "BAMBANG BRODJONEGORO"),
        ("KH Ma'ruf Amin", "MA'RUF AMIN"),
        ("Raden Ajeng Kartini", "AJENG KARTINI"),
        ("Budi Gunadi Sadikin, Ak., CA, CPA", "BUDI GUNADI SADIKIN"),
        ("Anne-Marie O'Connor, LL.B., LL.M.", "ANNE-MARIE O'CONNOR"),
        ("Andi SE", "ANDI"),
        ("Andi S.E., M.Si.", "ANDI"),
        ("Dewi, SH, MKn", "DEWI"),
        ("Ir.H. Joko", "JOKO"),
        ("Hartono Hadi, B.Sc., CFA", "HARTONO HADI"),
        ("Dr. Ir.", "DR IR"),
        ("", ""),
        ("   ", ""),
        ("Erick Thohir, B.A., M.B.A.", "ERICK THOHIR"),
        ("Andi, BBA", "ANDI"),
        ("M. Arsjad Rasjid P.M.", "M ARSJAD RASJID PM"),
        ("Jean-Pierre O'Neil", "JEAN-PIERRE O'NEIL"),
        ("Muhammad Ma'ruf Amin", "MUHAMMAD MA'RUF AMIN"),
        ("Ｊｏｋｏ　Ｗｉｄｏｄｏ", "JOKO WIDODO"),
    ],
)
def test_normalise(raw, expected):
    assert normalise(raw) == expected


def test_tokens():
    assert tokens("Ir. H. Joko Widodo") == ("JOKO", "WIDODO")
    assert tokens("Suharto") == ("SUHARTO",)
    assert tokens("") == ()


def test_block_keys_min_length_three():
    assert block_keys("Ir. H. Joko Widodo") == {"JOKO", "WIDODO"}
    assert block_keys("Sri Mulyani Indrawati") == {"SRI", "MULYANI", "INDRAWATI"}
    assert block_keys("Li Wu Tan") == {"TAN"}
    assert block_keys("") == set()


def test_same_printed_true_and_false():
    assert same_printed("Ir. H. Joko Widodo", "joko  widodo")
    assert not same_printed("Joko Widodo", "Joko Widodoo")
    assert not same_printed("Joko Widodo", "Widodo Joko")
    assert not same_printed("", "")


def test_titles_constant_is_normalised_form():
    assert all(t == t.upper() and "." not in t and " " not in t for t in TITLES)
    assert {"IR", "SE", "MBA", "PHD", "KH", "RADEN"} <= TITLES


def test_known_loss_title_like_initial_is_dropped():
    # Known loss recorded for the owner: a separate "R" is treated as a title (Raden).
    assert normalise("A. R. Baswedan") == "A BASWEDAN"


def test_known_loss_title_like_surname_is_dropped():
    # Known loss recorded for the owner: surname "Ma" equals the degree MA.
    assert normalise("Ma Jun") == "JUN"
