from modules.authorship_model import AuthorshipPrediction, EvaluationReport
from modules.feature_extractor import analyse_writing
import pytest

from modules.risk_engine import RiskPolicy, assess_review_risk, risk_assessment_json


def _analysis(repetitive: bool = False):
    if repetitive:
        sentence = "The system provides a structured educational response."
        text = " ".join([sentence] * 30)
    else:
        sentences = []
        for index in range(24):
            extra = " with a practical classroom example" if index % 3 == 0 else ""
            sentences.append(
                f"Student reflection number {index} explains an educational decision{extra}."
            )
        text = " ".join(sentences)
    return analyse_writing(text)


def _evaluation(
    rows: int = 90,
    macro_f1: float = 0.82,
    human_false_positive_rate: float = 0.05,
) -> EvaluationReport:
    return EvaluationReport(
        evaluation_split="test",
        training_rows=300,
        evaluation_rows=rows,
        accuracy=0.84,
        macro_f1=macro_f1,
        human_false_positive_rate=human_false_positive_rate,
        nonhuman_false_negative_rate=0.10,
        per_class={},
        confusion_matrix=((28, 1, 1), (2, 26, 2), (1, 3, 26)),
        labels=("HUMAN", "AI_ASSISTED", "AI"),
        disclaimer="experimental",
    )


def _prediction(human: float, assisted: float, ai: float) -> AuthorshipPrediction:
    probabilities = {"HUMAN": human, "AI_ASSISTED": assisted, "AI": ai}
    return AuthorshipPrediction(
        predicted_label=max(probabilities, key=probabilities.get),
        probabilities=probabilities,
        model_version="1",
        disclaimer="experimental",
    )


def test_abstains_for_short_document() -> None:
    analysis = analyse_writing("This sample is much too short for a responsible decision.")
    result = assess_review_risk(_prediction(0.1, 0.2, 0.7), analysis, _evaluation())
    assert result.outcome == "INSUFFICIENT_EVIDENCE"
    assert result.score is None
    assert any("words" in reason for reason in result.safeguards_triggered)


def test_abstains_for_small_or_weak_evaluation() -> None:
    result = assess_review_risk(
        _prediction(0.1, 0.2, 0.7),
        _analysis(),
        _evaluation(rows=12, macro_f1=0.40, human_false_positive_rate=0.30),
    )
    assert result.outcome == "INSUFFICIENT_EVIDENCE"
    assert len(result.safeguards_triggered) == 3


def test_abstains_for_uncertain_probabilities() -> None:
    result = assess_review_risk(_prediction(0.34, 0.33, 0.33), _analysis(), _evaluation())
    assert result.outcome == "INSUFFICIENT_EVIDENCE"
    assert any("uncertain" in reason for reason in result.safeguards_triggered)


def test_low_review_outcome() -> None:
    result = assess_review_risk(_prediction(0.85, 0.10, 0.05), _analysis(), _evaluation())
    assert result.outcome == "LOW"
    assert result.score is not None and result.score < 35


def test_moderate_review_outcome() -> None:
    result = assess_review_risk(_prediction(0.50, 0.30, 0.20), _analysis(), _evaluation())
    assert result.outcome == "MODERATE"
    assert result.score is not None


def test_high_review_outcome_and_explainable_components() -> None:
    result = assess_review_risk(_prediction(0.08, 0.22, 0.70), _analysis(True), _evaluation())
    assert result.outcome == "HIGH"
    assert len(result.components) == 2
    assert sum(component.contribution for component in result.components) == result.score
    assert "not proof" in result.disclaimer


def test_custom_policy_can_require_more_evidence() -> None:
    policy = RiskPolicy(minimum_evaluation_rows=500)
    result = assess_review_risk(_prediction(0.1, 0.2, 0.7), _analysis(), _evaluation(), policy)
    assert result.outcome == "INSUFFICIENT_EVIDENCE"
    assert result.policy_version == "0.1-experimental"


def test_assessment_can_be_exported() -> None:
    result = assess_review_risk(_prediction(0.85, 0.10, 0.05), _analysis(), _evaluation())
    exported = risk_assessment_json(result)
    assert '"outcome": "LOW"' in exported
    assert '"policy_version"' in exported


def test_policy_rejects_invalid_weights_and_thresholds() -> None:
    with pytest.raises(ValueError, match="weights"):
        RiskPolicy(classifier_weight=0.90, writing_pattern_weight=0.20)
    with pytest.raises(ValueError, match="thresholds"):
        RiskPolicy(moderate_threshold=75, high_threshold=60)
