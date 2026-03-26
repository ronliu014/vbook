# tests/test_glossary.py
from pathlib import Path
from vbook.utils.glossary import load_glossary

def test_load_glossary(tmp_path):
    glossary_file = tmp_path / "test.yaml"
    glossary_file.write_text(
        "domain: 投资\nterms:\n  - term: PE比\n    description: 市盈率\n  - term: 底背离\n    description: 技术形态\n",
        encoding="utf-8",
    )
    glossary = load_glossary(str(glossary_file))
    assert glossary["domain"] == "投资"
    assert len(glossary["terms"]) == 2
    assert glossary["terms"][0]["term"] == "PE比"

def test_load_glossary_returns_none_for_missing():
    result = load_glossary("/nonexistent/path.yaml")
    assert result is None

def test_load_glossary_returns_none_for_none():
    result = load_glossary(None)
    assert result is None

def test_glossary_hotwords(tmp_path):
    from vbook.utils.glossary import extract_hotwords
    glossary_file = tmp_path / "test.yaml"
    glossary_file.write_text(
        "domain: 投资\nterms:\n  - term: PE比\n    description: 市盈率\n  - term: 满仓\n    description: 全部资金投入\n",
        encoding="utf-8",
    )
    glossary = load_glossary(str(glossary_file))
    hotwords = extract_hotwords(glossary)
    assert hotwords == ["PE比", "满仓"]

def test_extract_hotwords_none_glossary():
    from vbook.utils.glossary import extract_hotwords
    assert extract_hotwords(None) == []
