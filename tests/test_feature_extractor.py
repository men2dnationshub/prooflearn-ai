import pytest

from modules.feature_extractor import analyse_writing


SAMPLE = (
    "Data helps teachers understand learning outcomes. "
    "However, evidence must be interpreted carefully.\n\n"
    "Students use data to test ideas and explain results. "
    "How can teachers support this process?"
)


def test_counts_document_structure() -> None:
    result = analyse_writing(SAMPLE)
    assert result.word_count == 27
    assert result.sentence_count == 4
    assert result.paragraph_count == 2
    assert result.unique_word_count > 20


def test_calculates_bounded_ratios() -> None:
    result = analyse_writing(SAMPLE)
    assert 0 <= result.lexical_diversity <= 1
    assert 0 <= result.hapax_ratio <= 1
    assert 0 <= result.repeated_bigram_ratio <= 1
    assert result.questions_per_100_sentences == 25.0


def test_detects_transitions_and_repeated_terms() -> None:
    result = analyse_writing("However, data matters. Data supports decisions. Therefore, data helps.")
    assert result.transitions_per_100_sentences > 0
    assert ("data", 3) in result.top_repeated_content_words


def test_detects_repeated_bigrams() -> None:
    result = analyse_writing("Students analyse data. Students analyse data carefully.")
    assert result.repeated_bigram_ratio > 0
    assert result.repeated_opening_ratio > 0


def test_readability_outputs_are_numeric() -> None:
    result = analyse_writing(SAMPLE)
    assert isinstance(result.flesch_reading_ease, float)
    assert result.flesch_kincaid_grade >= 0
    assert len(result.interpretation) == 4


@pytest.mark.parametrize("text", ["", "   ", "1234 !!!"])
def test_rejects_text_without_words(text: str) -> None:
    with pytest.raises(ValueError, match="readable text|readable word"):
        analyse_writing(text)
