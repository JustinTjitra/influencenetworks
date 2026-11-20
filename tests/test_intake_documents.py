import csv
import shutil

import pytest

from influence.intake import documents as d


def _pdf(tmp_path, name="a.pdf", data=b"%PDF-fake one"):
    p = tmp_path / "raw" / "docs" / name
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_bytes(data)
    return p


def _reg(tmp_path, pdf, doc_id="doc_a", **kw):
    return d.register(tmp_path / "raw" / "documents.csv", pdf, doc_id, "T", "P", 2025, "src", **kw)


def test_sha256_of(tmp_path):
    p = _pdf(tmp_path, data=b"abc")
    assert d.sha256_of(p) == "ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad"


def test_register_and_noop(tmp_path):
    p = _pdf(tmp_path)
    row = _reg(tmp_path, p)
    assert row["filename"] == "docs/a.pdf"
    _reg(tmp_path, p)
    with open(tmp_path / "raw" / "documents.csv", newline="") as f:
        rows = list(csv.DictReader(f))
    assert len(rows) == 1 and rows[0]["doc_id"] == "doc_a"
    assert "text layer" in rows[0]["note"]


def test_refusals(tmp_path):
    p = _pdf(tmp_path)
    with pytest.raises(ValueError):
        _reg(tmp_path, p, doc_id="Bad-Id")
    with pytest.raises(ValueError):
        _reg(tmp_path, tmp_path / "missing.pdf")
    _reg(tmp_path, p)
    other = _pdf(tmp_path, "b.pdf", b"different")
    with pytest.raises(ValueError):
        _reg(tmp_path, other, doc_id="doc_a")  # same id, different hash
    with pytest.raises(ValueError):
        _reg(tmp_path, p, doc_id="doc_b")  # same hash, other id


def test_verify(tmp_path):
    p = _pdf(tmp_path)
    _reg(tmp_path, p)
    reg, root = tmp_path / "raw" / "documents.csv", tmp_path / "raw"
    assert d.verify(reg, root) == ([], [])
    p.write_bytes(b"changed")
    errors, _ = d.verify(reg, root)
    assert len(errors) == 1
    p.unlink()
    errors, warnings = d.verify(reg, root)
    assert errors == [] and len(warnings) == 1


def test_cli(tmp_path):
    p = _pdf(tmp_path)
    reg = str(tmp_path / "raw" / "documents.csv")
    assert d.main(["register", "--pdf", str(p), "--id", "x1", "--title", "T",
                   "--publisher", "P", "--year", "2025", "--from", "owner",
                   "--registry", reg]) == 0
    assert d.main(["verify", "--registry", reg, "--root", str(tmp_path / "raw")]) == 0


@pytest.mark.skipif(shutil.which("pdfinfo") is None, reason="pdfinfo missing")
def test_page_count_fake_file(tmp_path):
    assert d.page_count(_pdf(tmp_path)) is None


@pytest.mark.skipif(shutil.which("pdftotext") is None, reason="pdftotext missing")
def test_text_layer_fake_file(tmp_path):
    assert d.has_text_layer(_pdf(tmp_path)) in (False, None)


def test_missing_binaries_return_none(tmp_path, monkeypatch):
    p = _pdf(tmp_path)
    monkeypatch.setattr(shutil, "which", lambda *a, **k: None)
    assert d.page_count(p) is None
    assert d.has_text_layer(p) is None
