"""Explainable, deterministic writing features for ProofLearn AI."""

from __future__ import annotations

from collections import Counter
from dataclasses import asdict, dataclass
import re
import statistics


WORD_PATTERN = re.compile(r"\b[A-Za-z]+(?:['’-][A-Za-z]+)?\b")
SENTENCE_PATTERN = re.compile(r"(?<=[.!?])\s+")

STOP_WORDS = {
    "a", "an", "and", "are", "as", "at", "be", "been", "but", "by", "for",
    "from", "had", "has", "have", "he", "her", "his", "i", "in", "is", "it",
    "its", "of", "on", "or", "our", "she", "that", "the", "their", "they",
    "this", "to", "was", "we", "were", "which", "with", "you", "your",
}

TRANSITIONS = (
    "additionally", "also", "consequently", "finally", "firstly", "furthermore",
    "however", "in addition", "in conclusion", "in contrast", "moreover",
    "nevertheless", "on the other hand", "secondly", "therefore", "thus",
)


@dataclass(frozen=True)
class WritingAnalysis:
    """A transparent set of statistics, not an AI authorship judgement."""

    word_count: int
    sentence_count: int
    paragraph_count: int
    unique_word_count: int
    average_sentence_length: float
    sentence_length_variation: float
    average_word_length: float
    lexical_diversity: float
    hapax_ratio: float
    flesch_reading_ease: float
    flesch_kincaid_grade: float
    punctuation_per_100_words: float
    questions_per_100_sentences: float
    transitions_per_100_sentences: float
    passive_indicators_per_100_sentences: float
    repeated_opening_ratio: float
    repeated_bigram_ratio: float
    top_repeated_content_words: tuple[tuple[str, int], ...]
    interpretation: tuple[str, ...]

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


def _sentences(text: str) -> list[str]:
    compact = re.sub(r"\s+", " ", text).strip()
    if not compact:
        return []
    sentences = [part.strip() for part in SENTENCE_PATTERN.split(compact) if part.strip()]
    return sentences or [compact]


def _paragraphs(text: str) -> list[str]:
    return [part.strip() for part in re.split(r"\n\s*\n", text) if part.strip()]


def _syllable_count(word: str) -> int:
    """Estimate English syllables without requiring a downloaded NLP model."""
    word = re.sub(r"[^a-z]", "", word.lower())
    if not word:
        return 0
    groups = re.findall(r"[aeiouy]+", word)
    count = len(groups)
    if word.endswith("e") and not word.endswith(("le", "ye")) and count > 1:
        count -= 1
    return max(1, count)


def _safe_rate(numerator: float, denominator: float, scale: float = 1.0) -> float:
    return numerator / denominator * scale if denominator else 0.0


def _level_notes(
    sentence_variation: float,
    lexical_diversity: float,
    reading_ease: float,
    repeated_bigram_ratio: float,
) -> tuple[str, ...]:
    variation = (
        "Sentence lengths show low variation."
        if sentence_variation < 4
        else "Sentence lengths show moderate variation."
        if sentence_variation < 9
        else "Sentence lengths show high variation."
    )
    vocabulary = (
        "Vocabulary diversity is limited for this sample."
        if lexical_diversity < 0.35
        else "Vocabulary diversity is moderate for this sample."
        if lexical_diversity < 0.60
        else "Vocabulary diversity is high for this sample."
    )
    readability = (
        "The text is generally easy to read."
        if reading_ease >= 60
        else "The text has moderate reading difficulty."
        if reading_ease >= 30
        else "The text is difficult to read and may contain complex sentences or words."
    )
    repetition = (
        "Repeated two-word phrasing is limited."
        if repeated_bigram_ratio < 0.08
        else "Some repeated two-word phrasing is present."
        if repeated_bigram_ratio < 0.18
        else "Frequent repeated two-word phrasing is present."
    )
    return variation, vocabulary, readability, repetition


def analyse_writing(text: str) -> WritingAnalysis:
    """Calculate explainable document-level writing features.

    These values describe a text. They must not be interpreted as proof of AI
    authorship and are intentionally independent of any machine learning model.
    """
    if not text or not text.strip():
        raise ValueError("Text analysis requires readable text.")

    original_words = WORD_PATTERN.findall(text)
    words = [word.lower().replace("’", "'") for word in original_words]
    sentences = _sentences(text)
    paragraphs = _paragraphs(text)

    if not words:
        raise ValueError("Text analysis requires at least one readable word.")

    frequencies = Counter(words)
    sentence_lengths = [len(WORD_PATTERN.findall(sentence)) for sentence in sentences]
    average_sentence_length = statistics.mean(sentence_lengths)
    sentence_variation = statistics.pstdev(sentence_lengths) if len(sentence_lengths) > 1 else 0.0

    syllables = sum(_syllable_count(word) for word in words)
    words_per_sentence = _safe_rate(len(words), len(sentences))
    syllables_per_word = _safe_rate(syllables, len(words))
    reading_ease = 206.835 - 1.015 * words_per_sentence - 84.6 * syllables_per_word
    grade = 0.39 * words_per_sentence + 11.8 * syllables_per_word - 15.59

    bigrams = list(zip(words, words[1:]))
    repeated_bigram_occurrences = sum(
        count - 1 for count in Counter(bigrams).values() if count > 1
    )

    openings = []
    for sentence in sentences:
        opening_words = [word.lower() for word in WORD_PATTERN.findall(sentence)[:2]]
        if opening_words:
            openings.append(" ".join(opening_words))
    repeated_openings = sum(count - 1 for count in Counter(openings).values() if count > 1)

    lower_text = text.lower()
    transition_count = sum(
        len(re.findall(rf"\b{re.escape(transition)}\b", lower_text))
        for transition in TRANSITIONS
    )
    passive_pattern = re.compile(
        r"\b(?:am|are|is|was|were|be|been|being)\s+\w+(?:ed|en)\b",
        flags=re.IGNORECASE,
    )
    passive_count = len(passive_pattern.findall(text))
    punctuation_count = len(re.findall(r"[,;:!?—–-]", text))

    content_words = Counter(word for word in words if word not in STOP_WORDS and len(word) > 2)
    top_repeated = tuple(
        (word, count) for word, count in content_words.most_common(8) if count > 1
    )

    lexical_diversity = _safe_rate(len(frequencies), len(words))
    hapax_ratio = _safe_rate(sum(count == 1 for count in frequencies.values()), len(frequencies))
    repeated_bigram_ratio = _safe_rate(repeated_bigram_occurrences, len(bigrams))

    return WritingAnalysis(
        word_count=len(words),
        sentence_count=len(sentences),
        paragraph_count=len(paragraphs),
        unique_word_count=len(frequencies),
        average_sentence_length=round(average_sentence_length, 2),
        sentence_length_variation=round(sentence_variation, 2),
        average_word_length=round(statistics.mean(len(word) for word in words), 2),
        lexical_diversity=round(lexical_diversity, 3),
        hapax_ratio=round(hapax_ratio, 3),
        flesch_reading_ease=round(reading_ease, 1),
        flesch_kincaid_grade=round(max(0.0, grade), 1),
        punctuation_per_100_words=round(_safe_rate(punctuation_count, len(words), 100), 2),
        questions_per_100_sentences=round(
            _safe_rate(sum(sentence.rstrip().endswith("?") for sentence in sentences), len(sentences), 100),
            2,
        ),
        transitions_per_100_sentences=round(
            _safe_rate(transition_count, len(sentences), 100), 2
        ),
        passive_indicators_per_100_sentences=round(
            _safe_rate(passive_count, len(sentences), 100), 2
        ),
        repeated_opening_ratio=round(_safe_rate(repeated_openings, len(openings)), 3),
        repeated_bigram_ratio=round(repeated_bigram_ratio, 3),
        top_repeated_content_words=top_repeated,
        interpretation=_level_notes(
            sentence_variation, lexical_diversity, reading_ease, repeated_bigram_ratio
        ),
    )
