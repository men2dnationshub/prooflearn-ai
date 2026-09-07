"""Conservative, explainable authorship review risk framework."""

from __future__ import annotations

from dataclasses import asdict, dataclass
import json
from typing import Any

from modules.authorship_model import AuthorshipPrediction, EvaluationReport
from modules.feature_extractor import WritingAnalysis


@dataclass(frozen=True)
class RiskPolicy:
    """Versioned safeguards and experimental score thresholds."""

    version: str = "0.1-experimental"
    minimum_document_words: int = 150
    minimum_evaluation_rows: int = 30
    minimum_macro_f1: float = 0.60
    maximum_human_false_positive_rate: float = 0.15
    minimum_probability_margin: float = 0.10
    classifier_weight: float = 0.80
    writing_pattern_weight: float = 0.20
    moderate_threshold: float = 35.0
    high_threshold: float = 65.0

    def __post_init__(self) -> None:
        if abs(self.classifier_weight + self.writing_pattern_weight - 1.0) > 1e-9:
            raise ValueError("Risk component weights must total 1.0.")
        if not 0 <= self.moderate_threshold < self.high_threshold <= 100:
            raise ValueError("Risk thresholds must be ordered between 0 and 100.")
        probability_values = (
            self.minimum_macro_f1,
            self.maximum_human_false_positive_rate,
            self.minimum_probability_margin,
            self.classifier_weight,
            self.writing_pattern_weight,
        )
        if any(value < 0 or value > 1 for value in probability_values):
            raise ValueError("Probability thresholds and weights must be between 0 and 1.")
        if self.minimum_document_words < 1 or self.minimum_evaluation_rows < 1:
            raise ValueError("Minimum evidence sizes must be positive integers.")


@dataclass(frozen=True)
class RiskComponent:
    name: str
    value: float
    weight: float
    contribution: float
    explanation: str


@dataclass(frozen=True)
class RiskAssessment:
    outcome: str
    score: float | None
    evidence_quality: str
    components: tuple[RiskComponent, ...]
    safeguards_triggered: tuple[str, ...]
    observations: tuple[str, ...]
    recommended_action: str
    policy_version: str
    disclaimer: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


DISCLAIMER = (
    "This is an experimental authorship review signal, not proof that AI was used "
    "and not evidence of academic misconduct. Verify the student's understanding "
    "and follow institutional policy before making any decision."
)


def _probability_margin(prediction: AuthorshipPrediction) -> float:
    ordered = sorted(prediction.probabilities.values(), reverse=True)
    return ordered[0] - ordered[1] if len(ordered) > 1 else 0.0


def _writing_pattern_signal(analysis: WritingAnalysis) -> tuple[float, tuple[str, ...]]:
    """Calculate a small, capped signal from transparent structural patterns."""
    consistency = max(0.0, min(1.0, 1 - analysis.sentence_length_variation / 10))
    phrase_repetition = max(0.0, min(1.0, analysis.repeated_bigram_ratio / 0.20))
    opening_repetition = max(0.0, min(1.0, analysis.repeated_opening_ratio / 0.25))
    signal = (consistency + phrase_repetition + opening_repetition) / 3

    observations = []
    if consistency >= 0.70:
        observations.append("Sentence lengths are unusually consistent in this sample.")
    if phrase_repetition >= 0.50:
        observations.append("Repeated two-word phrasing contributes to the review signal.")
    if opening_repetition >= 0.50:
        observations.append("Several sentences begin with the same two-word pattern.")
    if not observations:
        observations.append("The selected structural repetition indicators are limited.")
    return signal, tuple(observations)


def assess_review_risk(
    prediction: AuthorshipPrediction,
    analysis: WritingAnalysis,
    evaluation: EvaluationReport,
    policy: RiskPolicy | None = None,
) -> RiskAssessment:
    """Return a review outcome or abstain when evidence safeguards fail."""
    policy = policy or RiskPolicy()
    safeguards = []

    if analysis.word_count < policy.minimum_document_words:
        safeguards.append(
            f"Document has {analysis.word_count} words; at least "
            f"{policy.minimum_document_words} are required."
        )
    if evaluation.evaluation_rows < policy.minimum_evaluation_rows:
        safeguards.append(
            f"Model evaluation used {evaluation.evaluation_rows} rows; at least "
            f"{policy.minimum_evaluation_rows} are required."
        )
    if evaluation.macro_f1 < policy.minimum_macro_f1:
        safeguards.append(
            f"Model macro F1 is {evaluation.macro_f1:.1%}, below the "
            f"{policy.minimum_macro_f1:.0%} experimental minimum."
        )
    if evaluation.human_false_positive_rate > policy.maximum_human_false_positive_rate:
        safeguards.append(
            f"Human false-positive rate is {evaluation.human_false_positive_rate:.1%}, "
            f"above the {policy.maximum_human_false_positive_rate:.0%} maximum."
        )
    margin = _probability_margin(prediction)
    if margin < policy.minimum_probability_margin:
        safeguards.append(
            f"The top model probabilities differ by only {margin:.1%}; "
            "the classification is too uncertain."
        )

    pattern_signal, observations = _writing_pattern_signal(analysis)
    if safeguards:
        return RiskAssessment(
            outcome="INSUFFICIENT_EVIDENCE",
            score=None,
            evidence_quality="INSUFFICIENT",
            components=(),
            safeguards_triggered=tuple(safeguards),
            observations=observations,
            recommended_action=(
                "Do not assign an authorship risk level. Gather stronger model evidence, "
                "use a longer writing sample, and verify the student's understanding."
            ),
            policy_version=policy.version,
            disclaimer=DISCLAIMER,
        )

    nonhuman_probability = prediction.probabilities.get("AI", 0.0) + prediction.probabilities.get(
        "AI_ASSISTED", 0.0
    )
    classifier_contribution = nonhuman_probability * policy.classifier_weight
    pattern_contribution = pattern_signal * policy.writing_pattern_weight
    score = round((classifier_contribution + pattern_contribution) * 100, 1)

    if score >= policy.high_threshold and nonhuman_probability >= 0.60:
        outcome = "HIGH"
        action = (
            "Prioritise a student verification conversation. Ask the student to explain "
            "their reasoning and reproduce key parts of the work. Do not treat this result as proof."
        )
    elif score >= policy.moderate_threshold:
        outcome = "MODERATE"
        action = (
            "Review the highlighted indicators and verify selected claims or methods with the student."
        )
    else:
        outcome = "LOW"
        action = (
            "No additional action is suggested from this signal alone. Continue normal academic review."
        )

    components = (
        RiskComponent(
            name="Classifier nonhuman probability",
            value=round(nonhuman_probability, 4),
            weight=policy.classifier_weight,
            contribution=round(classifier_contribution * 100, 1),
            explanation="Combined AI and AI_ASSISTED probabilities from the validated baseline model.",
        ),
        RiskComponent(
            name="Structural pattern signal",
            value=round(pattern_signal, 4),
            weight=policy.writing_pattern_weight,
            contribution=round(pattern_contribution * 100, 1),
            explanation=(
                "Capped combination of sentence-length consistency, repeated phrases and repeated openings."
            ),
        ),
    )
    evidence_quality = "MODERATE" if evaluation.evaluation_rows < 100 else "STRONGER"
    return RiskAssessment(
        outcome=outcome,
        score=score,
        evidence_quality=evidence_quality,
        components=components,
        safeguards_triggered=(),
        observations=observations,
        recommended_action=action,
        policy_version=policy.version,
        disclaimer=DISCLAIMER,
    )


def risk_assessment_json(assessment: RiskAssessment) -> str:
    return json.dumps(assessment.to_dict(), indent=2)
