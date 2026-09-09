from pathlib import Path

from modules.config import APP_VERSION
from modules.document_reader import extract_document


ROOT = Path(__file__).resolve().parents[1]


def test_sample_assignment_is_safe_and_usable():
    sample = ROOT / "samples" / "sample_assignment.txt"
    document = extract_document(sample.read_bytes(), sample.name)
    assert document.word_count >= 100
    assert "student name" not in document.text.lower()


def test_router_uses_named_home_page():
    source = (ROOT / "app.py").read_text(encoding="utf-8")
    assert 'title="Home"' in source
    assert "default=True" in source
    assert APP_VERSION == "0.13.0"
