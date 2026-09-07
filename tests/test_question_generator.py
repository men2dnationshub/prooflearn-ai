import json

import pytest

from modules.question_generator import (
    generate_verification_questions,
    score_verification,
    verification_report_json,
)


TEXT = """Customer retention measures how many customers continue buying from a business. The analysis used monthly sales data from January to June. The retention rate was calculated by dividing returning customers by eligible customers.

The results showed that retention decreased by 17 percent in the final quarter. This decline may have occurred because delivery delays increased during the same period. Therefore, the business should review fulfilment times before changing its marketing strategy.

The dataset contained only six months of transactions, which limits the conclusion. A longer observation period could show whether the decline was temporary. Future analysis should compare customer groups and investigate product availability."""


def test_generates_six_grounded_question_types() -> None:
    bank = generate_verification_questions(TEXT)
    assert len(bank.questions) == 6
    assert {question.category for question in bank.questions} == {
        "KNOWLEDGE", "UNDERSTANDING", "METHOD", "REASONING", "APPLICATION", "CRITIQUE"
    }
    assert all(question.source_reference.startswith("Paragraph") for question in bank.questions)
    assert all(question.source_excerpt in TEXT for question in bank.questions)


def test_question_ids_and_output_are_deterministic() -> None:
    first = generate_verification_questions(TEXT)
    second = generate_verification_questions(TEXT)
    assert first == second
    assert [question.question_id for question in first.questions] == [
        "Q01", "Q02", "Q03", "Q04", "Q05", "Q06"
    ]


def test_scores_complete_verification() -> None:
    bank = generate_verification_questions(TEXT)
    ratings = {question.question_id: 3 for question in bank.questions}
    result = score_verification(bank, ratings)
    assert result.score == 100.0
    assert result.level == "STRONG"
    assert result.completion_rate == 1.0


def test_incomplete_ratings_do_not_become_zero_scores() -> None:
    bank = generate_verification_questions(TEXT)
    result = score_verification(bank, {"Q01": 3})
    assert result.score is None
    assert result.level == "INCOMPLETE"
    assert result.assessed_questions == 1


@pytest.mark.parametrize(
    "ratings,expected_level",
    [
        ([0, 0, 0, 0, 0, 0], "LIMITED"),
        ([1, 1, 1, 1, 2, 2], "DEVELOPING"),
        ([2, 2, 2, 2, 2, 2], "ADEQUATE"),
        ([3, 3, 3, 3, 3, 2], "STRONG"),
    ],
)
def test_interprets_score_levels(ratings: list[int], expected_level: str) -> None:
    bank = generate_verification_questions(TEXT)
    mapped = {
        question.question_id: rating
        for question, rating in zip(bank.questions, ratings)
    }
    assert score_verification(bank, mapped).level == expected_level


def test_rejects_invalid_ratings_and_unknown_questions() -> None:
    bank = generate_verification_questions(TEXT)
    with pytest.raises(ValueError, match="must be 0"):
        score_verification(bank, {"Q01": 4})
    with pytest.raises(ValueError, match="unknown question IDs"):
        score_verification(bank, {"Q99": 2})


def test_report_preserves_questions_ratings_and_notes() -> None:
    bank = generate_verification_questions(TEXT)
    ratings = {question.question_id: 2 for question in bank.questions}
    result = score_verification(bank, ratings, {"Q01": "Student gave a clear definition."})
    report = json.loads(verification_report_json(bank, result))
    assert len(report["question_bank"]["questions"]) == 6
    assert report["verification_result"]["notes"]["Q01"] == "Student gave a clear definition."


def test_rejects_short_or_unstructured_text() -> None:
    with pytest.raises(ValueError, match="at least 60 words"):
        generate_verification_questions("This short sentence has enough structure but not enough content.")
    with pytest.raises(ValueError, match="complete sentences"):
        generate_verification_questions("word " * 80)


@pytest.mark.parametrize("maximum", [2, 7])
def test_rejects_question_count_outside_supported_range(maximum: int) -> None:
    with pytest.raises(ValueError, match="between 3 and 6"):
        generate_verification_questions(TEXT, maximum_questions=maximum)
