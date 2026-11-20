import shutil

import pytest

from influence.intake import pdf_pages as pp


TEXTS = [
    "Cover page",
    "Board of Commissioners\nPresident Commissioner: A\nKomisaris Independen: B\n" + "x" * 200,
    "Direksi\nBoard of Directors\nPresident Director\nappointed at the General Meeting",
    "Pemegang Saham\nShareholder table\nShare ownership",
    "Dewan Komisaris diangkat oleh RUPS, masa jabatan 5 tahun",
]


def test_score_pages_counts_keywords():
    s = pp.score_pages(TEXTS)
    assert list(s["page"]) == [1, 2, 3, 4, 5]
    assert list(s.columns) == [
        "page", "chars", "commissioners", "directors", "shareholders", "appointment",
    ]
    row2 = s[s.page == 2].iloc[0]
    assert row2.commissioners == 3
    assert row2.directors == 0
    row3 = s[s.page == 3].iloc[0]
    assert row3.directors == 3
    assert row3.appointment == 2
    row4 = s[s.page == 4].iloc[0]
    assert row4.shareholders == 3
    assert s[s.page == 1].iloc[0].chars == len("Cover page")


def test_likely_pages_ranking_and_ties():
    s = pp.score_pages(TEXTS)
    # page 2: 3 hits; page 5: 1 hit + 0.5*3 appointment = 2.5; page 3: 0 + 1 = 1
    assert pp.likely_pages(s, "commissioners") == [2, 5, 3]
    assert pp.likely_pages(s, "commissioners", top=1) == [2]
    assert pp.likely_pages(s, "shareholders")[0] == 4


def test_likely_pages_tie_broken_by_page_number():
    s = pp.score_pages(["direksi", "nothing", "direksi", "direksi"])
    assert pp.likely_pages(s, "directors") == [1, 3, 4]


def test_likely_pages_rejects_unknown_kind():
    with pytest.raises(ValueError):
        pp.likely_pages(pp.score_pages(TEXTS), "appointment")


def test_is_scanned():
    assert pp.is_scanned(["", "ab", "x" * 500]) is True
    assert pp.is_scanned(["x" * 150, "y" * 300, ""]) is False
    assert pp.is_scanned(["x" * 100] * 3) is False


def test_page_texts_from_real_pdf(tmp_path):
    if shutil.which("pdftotext") is None:
        pytest.skip("pdftotext not installed")
    canvas = pytest.importorskip("reportlab.pdfgen.canvas")
    path = tmp_path / "two.pdf"
    c = canvas.Canvas(str(path))
    c.drawString(72, 700, "Board of Commissioners")
    c.showPage()
    c.drawString(72, 700, "Pemegang Saham")
    c.showPage()
    c.save()
    texts = pp.page_texts(path)
    assert len(texts) == 2
    assert "Board of Commissioners" in texts[0]
    assert "Pemegang Saham" in texts[1]
