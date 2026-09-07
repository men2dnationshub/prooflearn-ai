from pathlib import Path

import pandas as pd
import pytest

from modules.authorship_model import (
    ModelTrainingError,
    evaluation_json,
    load_model,
    predict_authorship,
    save_model,
    train_baseline,
)


def _record(record_id: str, label: str, split: str, author: str, theme: str) -> dict[str, object]:
    model = "test-model" if label in {"AI", "AI_ASSISTED"} else ""
    editing = "moderate" if label == "AI_ASSISTED" else "none"
    text = " ".join(
        [
            f"Record {record_id} uses {theme} evidence to explain learning outcomes through classroom reflection",
            f"{theme} examples show how a student develops and reviews an original argument",
            f"{theme} conclusions connect the stated method with the reported educational result",
        ]
    )
    return {
        "record_id": record_id,
        "text": text,
        "label": label,
        "source_type": "synthetic_ai" if label == "AI" else "researcher_created",
        "source_reference": "automated-test-batch",
        "subject": "education",
        "education_level": "tertiary",
        "language": "English",
        "author_group_id": author,
        "model_name": model,
        "generation_prompt_id": "prompt-test" if model else "",
        "editing_level": editing,
        "consent_status": "not_applicable",
        "license_or_permission": "automated test fixture",
        "collection_date": "2026-09-07",
        "split": split,
        "exclude_from_training": False,
        "notes": "not real training data",
    }


def _dataset() -> pd.DataFrame:
    rows = []
    themes = {
        "HUMAN": ("personal", "reflection"),
        "AI_ASSISTED": ("revised", "collaboration"),
        "AI": ("generated", "structured"),
    }
    for label, words in themes.items():
        prefix = label.replace("_", "")
        rows.append(_record(f"{prefix}-T1", label, "train", f"{prefix}-author-1", words[0]))
        rows.append(_record(f"{prefix}-T2", label, "train", f"{prefix}-author-2", words[1]))
        rows.append(_record(f"{prefix}-E1", label, "test", f"{prefix}-author-3", words[0]))
    return pd.DataFrame(rows)


def test_trains_and_evaluates_three_class_baseline() -> None:
    bundle = train_baseline(_dataset())
    assert bundle.evaluation.training_rows == 6
    assert bundle.evaluation.evaluation_rows == 3
    assert 0 <= bundle.evaluation.accuracy <= 1
    assert 0 <= bundle.evaluation.human_false_positive_rate <= 1
    assert set(bundle.evaluation.per_class) == {"HUMAN", "AI", "AI_ASSISTED"}
    assert bundle.metadata["production_approved"] is False


def test_prediction_returns_probabilities_that_sum_to_one() -> None:
    bundle = train_baseline(_dataset())
    prediction = predict_authorship(
        bundle,
        "Personal evidence explains learning outcomes through careful classroom reflection "
        "and shows how a student develops an original argument in a real lesson experience.",
    )
    assert set(prediction.probabilities) == {"HUMAN", "AI", "AI_ASSISTED"}
    assert sum(prediction.probabilities.values()) == pytest.approx(1.0, abs=0.001)
    assert "not proof" in prediction.disclaimer


def test_model_round_trip(tmp_path: Path) -> None:
    bundle = train_baseline(_dataset())
    path = save_model(bundle, tmp_path / "baseline.joblib")
    restored = load_model(path)
    assert restored.metadata["dataset_sha256"] == bundle.metadata["dataset_sha256"]


def test_evaluation_report_is_downloadable_json() -> None:
    report = evaluation_json(train_baseline(_dataset()))
    assert '"human_false_positive_rate"' in report
    assert '"production_approved": false' in report


def test_training_requires_all_labels_in_train_split() -> None:
    frame = _dataset()
    frame = frame[~((frame["label"] == "AI") & (frame["split"] == "train"))]
    with pytest.raises(ModelTrainingError, match="Insufficient labels"):
        train_baseline(frame)


def test_prediction_rejects_short_text() -> None:
    bundle = train_baseline(_dataset())
    with pytest.raises(ValueError, match="at least 20 words"):
        predict_authorship(bundle, "Too short")


def test_model_extension_is_enforced(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match=".joblib"):
        save_model(train_baseline(_dataset()), tmp_path / "baseline.bin")
