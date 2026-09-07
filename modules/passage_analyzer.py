"""Paragraph-referenced local writing variation analysis."""

from __future__ import annotations

from dataclasses import asdict, dataclass
import json
import re
from typing import Any

from modules.feature_extractor import WritingAnalysis, analyse_writing


@dataclass(frozen=True)
class Passage:
    passage_id: str
    reference: str
    paragraph_start: int
    paragraph_end: int
    part_number: int | None
    text: str
    word_count: int
    variation_score: float
    variation_level: str
    observations: tuple[str, ...]
    metrics: dict[str, float]


@dataclass(frozen=True)
class PassageAnalysisReport:
    document_word_count: int
    source_paragraph_count: int
    passage_count: int
    passages: tuple[Passage, ...]
    methodology: str
    disclaimer: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


DISCLAIMER = (
    "Passage variation shows where writing patterns differ within this document. "
    "It does not establish that a passage was written by AI or by another person."
)


def _word_count(text: str) -> int:
    return len(re.findall(r"\b[A-Za-z]+(?:['’-][A-Za-z]+)?\b", text))


def _split_sentences(text: str) -> list[str]:
    sentences = re.split(r"(?<=[.!?])\s+", re.sub(r"\s+", " ", text).strip())
    return [sentence.strip() for sentence in sentences if sentence.strip()]


def _split_long_paragraph(text: str, maximum_words: int) -> list[str]:
    sentences = _split_sentences(text)
    if not sentences:
        return [text]
    chunks: list[str] = []
    current: list[str] = []
    current_words = 0
    for sentence in sentences:
        sentence_words = _word_count(sentence)
        if current and current_words + sentence_words > maximum_words:
            chunks.append(" ".join(current))
            current = []
            current_words = 0
        current.append(sentence)
        current_words += sentence_words
    if current:
        chunks.append(" ".join(current))
    return chunks


def _segment_text(
    text: str,
    minimum_words: int,
    maximum_words: int,
) -> tuple[list[tuple[int, int, int | None, str]], int]:
    paragraphs = [part.strip() for part in re.split(r"\n\s*\n", text) if part.strip()]
    units: list[tuple[int, int | None, str]] = []
    for paragraph_number, paragraph in enumerate(paragraphs, start=1):
        if _word_count(paragraph) > maximum_words:
            chunks = _split_long_paragraph(paragraph, maximum_words)
            for part_number, chunk in enumerate(chunks, start=1):
                units.append((paragraph_number, part_number, chunk))
        else:
            units.append((paragraph_number, None, paragraph))

    passages: list[tuple[int, int, int | None, str]] = []
    pending: list[tuple[int, int | None, str]] = []
    pending_words = 0
    for unit in units:
        unit_words = _word_count(unit[2])
        if pending and pending_words + unit_words > maximum_words:
            start = pending[0][0]
            end = pending[-1][0]
            part = pending[0][1] if len(pending) == 1 else None
            passages.append((start, end, part, "\n\n".join(item[2] for item in pending)))
            pending = []
            pending_words = 0
        pending.append(unit)
        pending_words += unit_words
        if pending_words >= minimum_words:
            start = pending[0][0]
            end = pending[-1][0]
            part = pending[0][1] if len(pending) == 1 else None
            passages.append((start, end, part, "\n\n".join(item[2] for item in pending)))
            pending = []
            pending_words = 0

    if pending:
        if passages and _word_count(passages[-1][3]) + pending_words <= maximum_words:
            previous = passages.pop()
            passages.append(
                (previous[0], pending[-1][0], None, previous[3] + "\n\n" + "\n\n".join(item[2] for item in pending))
            )
        else:
            passages.append(
                (pending[0][0], pending[-1][0], pending[0][1] if len(pending) == 1 else None,
                 "\n\n".join(item[2] for item in pending))
            )
    return passages, len(paragraphs)


def _relative_difference(value: float, baseline: float, floor: float) -> float:
    return min(1.0, abs(value - baseline) / max(abs(baseline), floor))


def _compare_passage(passage: WritingAnalysis, document: WritingAnalysis) -> tuple[float, str, tuple[str, ...]]:
    differences = (
        _relative_difference(passage.average_sentence_length, document.average_sentence_length, 5.0),
        _relative_difference(passage.sentence_length_variation, document.sentence_length_variation, 3.0),
        _relative_difference(passage.punctuation_per_100_words, document.punctuation_per_100_words, 2.0),
        min(1.0, abs(passage.repeated_bigram_ratio - document.repeated_bigram_ratio) / 0.10),
    )
    score = round(sum(differences) / len(differences) * 100, 1)
    level = "TYPICAL" if score < 25 else "NOTABLE" if score < 50 else "STRONG_VARIATION"

    observations = []
    if passage.average_sentence_length > document.average_sentence_length * 1.30:
        observations.append("Sentences are longer than the document average.")
    elif passage.average_sentence_length < document.average_sentence_length * 0.70:
        observations.append("Sentences are shorter than the document average.")
    if passage.sentence_length_variation > document.sentence_length_variation + 4:
        observations.append("Sentence lengths vary more than in the document overall.")
    elif passage.sentence_length_variation + 4 < document.sentence_length_variation:
        observations.append("Sentence lengths are more consistent than in the document overall.")
    if passage.punctuation_per_100_words > document.punctuation_per_100_words * 1.50 + 1:
        observations.append("Punctuation is more frequent than the document average.")
    if passage.repeated_bigram_ratio > document.repeated_bigram_ratio + 0.05:
        observations.append("Repeated two-word phrasing is more frequent in this passage.")
    if not observations:
        observations.append("Selected writing patterns are close to the document baseline.")
    return score, level, tuple(observations)


def analyse_passages(
    text: str,
    minimum_document_words: int = 120,
    minimum_passage_words: int = 50,
    maximum_passage_words: int = 180,
) -> PassageAnalysisReport:
    """Segment a document and compare local patterns with its overall baseline."""
    if minimum_passage_words < 20 or maximum_passage_words <= minimum_passage_words:
        raise ValueError("Passage word limits are invalid.")
    if _word_count(text) < minimum_document_words:
        raise ValueError(
            f"Passage analysis requires at least {minimum_document_words} words."
        )

    document_analysis = analyse_writing(text)
    segments, paragraph_count = _segment_text(text, minimum_passage_words, maximum_passage_words)
    passages = []
    for index, (start, end, part, passage_text) in enumerate(segments, start=1):
        passage_analysis = analyse_writing(passage_text)
        score, level, observations = _compare_passage(passage_analysis, document_analysis)
        if start == end and part is not None:
            reference = f"Paragraph {start}, Part {part}"
        elif start == end:
            reference = f"Paragraph {start}"
        else:
            reference = f"Paragraphs {start}–{end}"
        passages.append(
            Passage(
                passage_id=f"P{index:03d}",
                reference=reference,
                paragraph_start=start,
                paragraph_end=end,
                part_number=part,
                text=passage_text,
                word_count=passage_analysis.word_count,
                variation_score=score,
                variation_level=level,
                observations=observations,
                metrics={
                    "average_sentence_length": passage_analysis.average_sentence_length,
                    "sentence_length_variation": passage_analysis.sentence_length_variation,
                    "punctuation_per_100_words": passage_analysis.punctuation_per_100_words,
                    "repeated_bigram_ratio": passage_analysis.repeated_bigram_ratio,
                },
            )
        )

    return PassageAnalysisReport(
        document_word_count=document_analysis.word_count,
        source_paragraph_count=paragraph_count,
        passage_count=len(passages),
        passages=tuple(passages),
        methodology=(
            "Passages are grouped from paragraph-referenced text and compared with the "
            "same document's sentence length, variation, punctuation and phrase repetition baseline."
        ),
        disclaimer=DISCLAIMER,
    )


def passage_analysis_json(report: PassageAnalysisReport) -> str:
    return json.dumps(report.to_dict(), indent=2, ensure_ascii=False)
