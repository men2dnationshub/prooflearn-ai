"""Grounded verification questions and educator scoring for ProofLearn AI."""

from __future__ import annotations

from collections import Counter
from dataclasses import asdict, dataclass
import hashlib
import json
import re
from typing import Any


CATEGORIES = (
    "KNOWLEDGE",
    "UNDERSTANDING",
    "METHOD",
    "REASONING",
    "APPLICATION",
    "CRITIQUE",
)

METHOD_TERMS = re.compile(
    r"\b(?:analysed|analyzed|calculated|collected|compared|created|measured|method|"
    r"survey|sample|used|using|formula|query|dataset|data)\b",
    re.IGNORECASE,
)
CLAIM_TERMS = re.compile(
    r"\b(?:because|conclude|conclusion|demonstrate|evidence|found|indicate|result|"
    r"show|suggest|therefore|thus)\b|\b\d+(?:\.\d+)?%?\b",
    re.IGNORECASE,
)
STOP_WORDS = {
    "about", "after", "also", "and", "are", "because", "been", "before", "being",
    "between", "both", "but", "can", "could", "did", "does", "each", "for", "from",
    "had", "has", "have", "into", "its", "more", "most", "not", "only", "other",
    "our", "should", "that", "the", "their", "there", "these", "they", "this", "those",
    "through", "using", "was", "were", "which", "will", "with", "would", "your",
}


@dataclass(frozen=True)
class VerificationQuestion:
    question_id: str
    category: str
    question: str
    source_reference: str
    source_excerpt: str
    purpose: str
    scoring_guide: str


@dataclass(frozen=True)
class QuestionBank:
    document_sha256: str
    questions: tuple[VerificationQuestion, ...]
    methodology: str
    disclaimer: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class VerificationResult:
    document_sha256: str
    total_questions: int
    assessed_questions: int
    completion_rate: float
    score: float | None
    level: str
    ratings: dict[str, int | None]
    notes: dict[str, str]
    interpretation: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class _SentenceRecord:
    paragraph: int
    sentence: int
    text: str

    @property
    def reference(self) -> str:
        return f"Paragraph {self.paragraph}, Sentence {self.sentence}"


def _document_fingerprint(text: str) -> str:
    normalised = re.sub(r"\s+", " ", text).strip().lower()
    return hashlib.sha256(normalised.encode("utf-8")).hexdigest()


def _sentence_records(text: str) -> list[_SentenceRecord]:
    paragraphs = [part.strip() for part in re.split(r"\n\s*\n", text) if part.strip()]
    records = []
    for paragraph_number, paragraph in enumerate(paragraphs, start=1):
        sentences = re.split(r"(?<=[.!?])\s+", re.sub(r"\s+", " ", paragraph))
        for sentence_number, sentence in enumerate(sentences, start=1):
            cleaned = sentence.strip()
            if cleaned.endswith((".", "!", "?")) and len(re.findall(r"\b\w+\b", cleaned)) >= 5:
                records.append(_SentenceRecord(paragraph_number, sentence_number, cleaned))
    return records


def _excerpt(text: str, maximum: int = 180) -> str:
    return text if len(text) <= maximum else text[: maximum - 1].rstrip() + "…"


def _key_term(text: str) -> str:
    words = [word.lower() for word in re.findall(r"\b[A-Za-z]{4,}\b", text)]
    content = [word for word in words if word not in STOP_WORDS]
    return Counter(content).most_common(1)[0][0] if content else "the main concept"


def _select_record(
    records: list[_SentenceRecord],
    preferred_pattern: re.Pattern[str] | None,
    used: set[tuple[int, int]],
) -> _SentenceRecord:
    preferred = [record for record in records if preferred_pattern and preferred_pattern.search(record.text)]
    candidates = preferred or records
    for record in candidates:
        key = (record.paragraph, record.sentence)
        if key not in used:
            used.add(key)
            return record
    record = candidates[len(used) % len(candidates)]
    return record


def generate_verification_questions(text: str, maximum_questions: int = 6) -> QuestionBank:
    """Generate deterministic questions whose source remains visible."""
    if maximum_questions < 3 or maximum_questions > 6:
        raise ValueError("Generate between 3 and 6 verification questions.")
    records = _sentence_records(text)
    if not records:
        raise ValueError("The document does not contain enough complete sentences for verification.")
    if len(re.findall(r"\b\w+\b", text)) < 60:
        raise ValueError("Question generation requires at least 60 words.")

    term = _key_term(text)
    used: set[tuple[int, int]] = set()
    definitions = [
        (
            "KNOWLEDGE",
            None,
            lambda record: f"In the context of your assignment, what does “{term}” mean?",
            "Checks whether the student understands a recurring concept in the submission.",
        ),
        (
            "UNDERSTANDING",
            None,
            lambda record: "Explain this point in your own words and connect it to your main argument.",
            "Checks comprehension of a specific submitted statement.",
        ),
        (
            "METHOD",
            METHOD_TERMS,
            lambda record: "Walk me through the method, process, calculation or evidence behind this statement.",
            "Checks whether the student can reproduce or explain how the result was produced.",
        ),
        (
            "REASONING",
            CLAIM_TERMS,
            lambda record: "What evidence or reasoning supports this claim, and why did you find it convincing?",
            "Checks the reasoning that connects evidence to a submitted claim.",
        ),
        (
            "APPLICATION",
            CLAIM_TERMS,
            lambda record: "If one important condition behind this statement changed, how might your answer change?",
            "Checks whether the student can transfer the idea to a changed situation.",
        ),
        (
            "CRITIQUE",
            CLAIM_TERMS,
            lambda record: "What limitation or alternative explanation could weaken this statement?",
            "Checks whether the student can evaluate limitations in their own work.",
        ),
    ]

    questions = []
    for index, (category, pattern, builder, purpose) in enumerate(definitions[:maximum_questions], start=1):
        record = _select_record(records, pattern, used)
        questions.append(
            VerificationQuestion(
                question_id=f"Q{index:02d}",
                category=category,
                question=builder(record),
                source_reference=record.reference,
                source_excerpt=_excerpt(record.text),
                purpose=purpose,
                scoring_guide=(
                    "0 Unable to explain · 1 Partial understanding · "
                    "2 Adequate understanding · 3 Strong understanding"
                ),
            )
        )

    return QuestionBank(
        document_sha256=_document_fingerprint(text),
        questions=tuple(questions),
        methodology=(
            "Questions are generated from complete sentences in the submission using "
            "documented knowledge, method, claim, application and critique patterns."
        ),
        disclaimer=(
            "A verification score records demonstrated understanding during review. "
            "It does not independently prove or disprove AI use."
        ),
    )


def score_verification(
    bank: QuestionBank,
    ratings: dict[str, int | None],
    notes: dict[str, str] | None = None,
) -> VerificationResult:
    """Score a completed educator review without treating missing ratings as zero."""
    question_ids = {question.question_id for question in bank.questions}
    unknown = set(ratings) - question_ids
    if unknown:
        raise ValueError("Ratings contain unknown question IDs: " + ", ".join(sorted(unknown)))
    normalised = {question_id: ratings.get(question_id) for question_id in question_ids}
    for question_id, rating in normalised.items():
        if rating is not None and rating not in {0, 1, 2, 3}:
            raise ValueError(f"Rating for {question_id} must be 0, 1, 2, 3 or not assessed.")

    assessed = [rating for rating in normalised.values() if rating is not None]
    total = len(bank.questions)
    completion_rate = len(assessed) / total if total else 0.0
    clean_notes = {
        question_id: str((notes or {}).get(question_id, "")).strip()
        for question_id in question_ids
    }

    if len(assessed) < total:
        score = None
        level = "INCOMPLETE"
        interpretation = (
            "Complete every question rating before calculating a Learning Verification Score."
        )
    else:
        score = round(sum(assessed) / (3 * total) * 100, 1)
        if score >= 85:
            level = "STRONG"
            interpretation = "The student demonstrated strong understanding of the reviewed submission."
        elif score >= 65:
            level = "ADEQUATE"
            interpretation = "The student demonstrated adequate understanding, with some areas to review."
        elif score >= 40:
            level = "DEVELOPING"
            interpretation = "The student demonstrated partial understanding and needs follow-up support."
        else:
            level = "LIMITED"
            interpretation = "The student could not yet demonstrate sufficient understanding of the reviewed work."

    return VerificationResult(
        document_sha256=bank.document_sha256,
        total_questions=total,
        assessed_questions=len(assessed),
        completion_rate=round(completion_rate, 4),
        score=score,
        level=level,
        ratings=normalised,
        notes=clean_notes,
        interpretation=interpretation,
    )


def verification_report_json(bank: QuestionBank, result: VerificationResult) -> str:
    return json.dumps(
        {"question_bank": bank.to_dict(), "verification_result": result.to_dict()},
        indent=2,
        ensure_ascii=False,
    )
