"""Baseline authorship classifier training, evaluation and persistence."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
from typing import Any

import joblib
import pandas as pd
import sklearn
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix, f1_score
from sklearn.pipeline import FeatureUnion, Pipeline

from modules.dataset_manager import LABELS, prepare_training_data


MODEL_FORMAT_VERSION = "1"
LABEL_ORDER = ("HUMAN", "AI_ASSISTED", "AI")


class ModelTrainingError(ValueError):
    """Raised when data cannot support a valid baseline experiment."""


@dataclass(frozen=True)
class EvaluationReport:
    evaluation_split: str
    training_rows: int
    evaluation_rows: int
    accuracy: float
    macro_f1: float
    human_false_positive_rate: float
    nonhuman_false_negative_rate: float
    per_class: dict[str, dict[str, float]]
    confusion_matrix: tuple[tuple[int, ...], ...]
    labels: tuple[str, ...]
    disclaimer: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class ModelBundle:
    pipeline: Pipeline
    metadata: dict[str, Any]
    evaluation: EvaluationReport


@dataclass(frozen=True)
class AuthorshipPrediction:
    predicted_label: str
    probabilities: dict[str, float]
    model_version: str
    disclaimer: str


def _build_pipeline() -> Pipeline:
    features = FeatureUnion(
        [
            (
                "word_tfidf",
                TfidfVectorizer(
                    lowercase=True,
                    ngram_range=(1, 2),
                    min_df=1,
                    max_df=1.0,
                    sublinear_tf=True,
                ),
            ),
            (
                "character_tfidf",
                TfidfVectorizer(
                    analyzer="char_wb",
                    lowercase=True,
                    ngram_range=(3, 5),
                    min_df=1,
                    max_features=25_000,
                    sublinear_tf=True,
                ),
            ),
        ]
    )
    classifier = LogisticRegression(
        class_weight="balanced",
        max_iter=1_500,
        random_state=42,
        solver="lbfgs",
    )
    return Pipeline([("features", features), ("classifier", classifier)])


def _dataset_fingerprint(frame: pd.DataFrame) -> str:
    values = frame[["record_id", "text_sha256", "label", "split"]].sort_values("record_id")
    serialised = values.to_csv(index=False, lineterminator="\n")
    return hashlib.sha256(serialised.encode("utf-8")).hexdigest()


def _require_class_coverage(frame: pd.DataFrame, split: str, minimum: int) -> None:
    counts = frame.loc[frame["split"].eq(split), "label"].value_counts()
    missing = [label for label in LABELS if int(counts.get(label, 0)) < minimum]
    if missing:
        raise ModelTrainingError(
            f"The {split} split needs at least {minimum} record(s) for every label. "
            f"Insufficient labels: {', '.join(sorted(missing))}."
        )


def train_baseline(
    dataframe: pd.DataFrame,
    evaluation_split: str = "test",
    minimum_training_rows_per_label: int = 2,
) -> ModelBundle:
    """Train and evaluate a reproducible three-class baseline experiment."""
    if evaluation_split not in {"validation", "test"}:
        raise ModelTrainingError("Evaluation split must be validation or test.")

    try:
        prepared = prepare_training_data(dataframe)
    except ValueError as exc:
        raise ModelTrainingError(str(exc)) from exc

    _require_class_coverage(prepared, "train", minimum_training_rows_per_label)
    _require_class_coverage(prepared, evaluation_split, 1)

    training = prepared[prepared["split"].eq("train")]
    evaluation = prepared[prepared["split"].eq(evaluation_split)]
    pipeline = _build_pipeline()
    pipeline.fit(training["text"], training["label"])
    predicted = pipeline.predict(evaluation["text"])
    actual = evaluation["label"].to_numpy()

    class_report = classification_report(
        actual,
        predicted,
        labels=list(LABEL_ORDER),
        output_dict=True,
        zero_division=0,
    )
    per_class = {
        label: {
            metric: round(float(class_report[label][metric]), 4)
            for metric in ("precision", "recall", "f1-score", "support")
        }
        for label in LABEL_ORDER
    }

    human_mask = actual == "HUMAN"
    nonhuman_mask = actual != "HUMAN"
    human_false_positive_rate = float((predicted[human_mask] != "HUMAN").mean())
    nonhuman_false_negative_rate = float((predicted[nonhuman_mask] == "HUMAN").mean())
    matrix = confusion_matrix(actual, predicted, labels=list(LABEL_ORDER))
    disclaimer = (
        "Experimental model output is a screening signal, not proof of AI authorship "
        "or academic misconduct. Independent validation and student verification are required."
    )
    report = EvaluationReport(
        evaluation_split=evaluation_split,
        training_rows=len(training),
        evaluation_rows=len(evaluation),
        accuracy=round(float(accuracy_score(actual, predicted)), 4),
        macro_f1=round(float(f1_score(actual, predicted, average="macro", zero_division=0)), 4),
        human_false_positive_rate=round(human_false_positive_rate, 4),
        nonhuman_false_negative_rate=round(nonhuman_false_negative_rate, 4),
        per_class=per_class,
        confusion_matrix=tuple(tuple(int(value) for value in row) for row in matrix),
        labels=LABEL_ORDER,
        disclaimer=disclaimer,
    )
    trained_at = datetime.now(timezone.utc).isoformat()
    metadata = {
        "model_format_version": MODEL_FORMAT_VERSION,
        "model_name": "ProofLearn TF-IDF Logistic Regression Baseline",
        "trained_at_utc": trained_at,
        "dataset_sha256": _dataset_fingerprint(prepared),
        "labels": list(LABEL_ORDER),
        "scikit_learn_version": sklearn.__version__,
        "production_approved": False,
    }
    return ModelBundle(pipeline=pipeline, metadata=metadata, evaluation=report)


def predict_authorship(bundle: ModelBundle, text: str) -> AuthorshipPrediction:
    """Return transparent class probabilities from a trained experiment."""
    if len(str(text).split()) < 20:
        raise ValueError("Prediction requires at least 20 words of readable text.")
    probabilities = bundle.pipeline.predict_proba([text])[0]
    classes = bundle.pipeline.classes_
    probability_map = {
        str(label): round(float(probability), 4)
        for label, probability in sorted(zip(classes, probabilities), key=lambda item: item[1], reverse=True)
    }
    return AuthorshipPrediction(
        predicted_label=max(probability_map, key=probability_map.get),
        probabilities=probability_map,
        model_version=str(bundle.metadata["model_format_version"]),
        disclaimer=bundle.evaluation.disclaimer,
    )


def save_model(bundle: ModelBundle, path: str | Path) -> Path:
    """Persist a versioned model bundle and its evaluation evidence."""
    target = Path(path)
    if target.suffix != ".joblib":
        raise ValueError("Model files must use the .joblib extension.")
    target.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(bundle, target)
    return target


def load_model(path: str | Path) -> ModelBundle:
    """Load a compatible bundle from a trusted local path only.

    Joblib files can execute code while loading and must never be accepted from
    an untrusted user upload.
    """
    bundle = joblib.load(Path(path))
    if not isinstance(bundle, ModelBundle):
        raise ValueError("The file is not a ProofLearn model bundle.")
    if bundle.metadata.get("model_format_version") != MODEL_FORMAT_VERSION:
        raise ValueError("The model format is not compatible with this application version.")
    return bundle


def evaluation_json(bundle: ModelBundle) -> str:
    """Serialise model metadata and metrics for audit and download."""
    return json.dumps(
        {"metadata": bundle.metadata, "evaluation": bundle.evaluation.to_dict()},
        indent=2,
    )
