import pytest

from modules.passage_analyzer import analyse_passages, passage_analysis_json


def _paragraph(name: str, sentence_count: int = 8) -> str:
    return " ".join(
        f"{name} sentence {index} explains a practical learning decision in the classroom."
        for index in range(sentence_count)
    )


def test_creates_traceable_passages_from_paragraphs() -> None:
    text = "\n\n".join([_paragraph("Alpha"), _paragraph("Beta"), _paragraph("Gamma")])
    report = analyse_passages(text)
    assert report.source_paragraph_count == 3
    assert report.passage_count >= 2
    assert report.passages[0].passage_id == "P001"
    assert report.passages[0].paragraph_start == 1
    assert "Paragraph" in report.passages[0].reference


def test_splits_long_single_paragraph_into_referenced_parts() -> None:
    report = analyse_passages(_paragraph("Long", sentence_count=45))
    assert report.source_paragraph_count == 1
    assert report.passage_count >= 2
    assert all(passage.paragraph_start == 1 for passage in report.passages)
    assert report.passages[0].part_number == 1


def test_preserves_all_distinctive_content() -> None:
    text = "\n\n".join([_paragraph("Alpha"), _paragraph("Beta"), _paragraph("Gamma")])
    report = analyse_passages(text)
    combined = " ".join(passage.text for passage in report.passages)
    for marker in ("Alpha", "Beta", "Gamma"):
        assert marker in combined


def test_flags_strong_local_variation_without_ai_claim() -> None:
    regular = "\n\n".join(_paragraph(f"Regular{index}") for index in range(3))
    repetitive = " ".join(["Repeated words repeat the same pattern."] * 20)
    report = analyse_passages(regular + "\n\n" + repetitive)
    assert any(passage.variation_level != "TYPICAL" for passage in report.passages)
    assert "does not establish" in report.disclaimer


def test_export_contains_references_and_methodology() -> None:
    report = analyse_passages("\n\n".join([_paragraph("Alpha"), _paragraph("Beta")]))
    exported = passage_analysis_json(report)
    assert '"passage_id": "P001"' in exported
    assert '"methodology"' in exported


def test_rejects_short_documents() -> None:
    with pytest.raises(ValueError, match="at least 120 words"):
        analyse_passages("This document is too short for local comparison.")


@pytest.mark.parametrize(
    "minimum,maximum",
    [(10, 180), (50, 50), (100, 80)],
)
def test_rejects_invalid_passage_sizes(minimum: int, maximum: int) -> None:
    with pytest.raises(ValueError, match="limits are invalid"):
        analyse_passages(_paragraph("Long", 20), minimum_passage_words=minimum, maximum_passage_words=maximum)
