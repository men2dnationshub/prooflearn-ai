import pandas as pd
import pytest

from modules.dataset_manager import (
    REQUIRED_COLUMNS,
    empty_dataset_template,
    prepare_training_data,
    text_fingerprint,
    validate_dataset,
)


def _row(record_id: str, label: str, split: str, author: str) -> dict[str, object]:
    model = "documented-test-model" if label in {"AI", "AI_ASSISTED"} else ""
    editing = "moderate" if label == "AI_ASSISTED" else "none"
    text = " ".join([f"Distinct educational sample {record_id} supports careful dataset testing."] * 10)
    return {
        "record_id": record_id,
        "text": text,
        "label": label,
        "source_type": "synthetic_ai" if label == "AI" else "researcher_created",
        "source_reference": "test-batch",
        "subject": "education",
        "education_level": "tertiary",
        "language": "English",
        "author_group_id": author,
        "model_name": model,
        "generation_prompt_id": "prompt-01" if model else "",
        "editing_level": editing,
        "consent_status": "not_applicable",
        "license_or_permission": "internal test fixture",
        "collection_date": "2026-09-07",
        "split": split,
        "exclude_from_training": False,
        "notes": "test only",
    }


def test_empty_template_has_canonical_columns() -> None:
    assert tuple(empty_dataset_template().columns) == REQUIRED_COLUMNS


def test_valid_dataset_passes_and_prepares_derived_fields() -> None:
    frame = pd.DataFrame([
        _row("H-001", "HUMAN", "train", "author-1"),
        _row("A-001", "AI", "validation", "ai-run-1"),
        _row("M-001", "AI_ASSISTED", "test", "author-2"),
    ])
    report = validate_dataset(frame)
    assert report.is_valid
    assert report.eligible_row_count == 3
    prepared = prepare_training_data(frame)
    assert {"text_sha256", "word_count", "character_count"}.issubset(prepared.columns)


def test_rejects_duplicate_text_and_ids() -> None:
    row = _row("H-001", "HUMAN", "train", "author-1")
    frame = pd.DataFrame([row, row])
    report = validate_dataset(frame)
    assert not report.is_valid
    assert any("Duplicate record IDs" in error for error in report.errors)
    assert any("duplicate-text" in error for error in report.errors)


def test_detects_author_leakage_between_splits() -> None:
    frame = pd.DataFrame([
        _row("H-001", "HUMAN", "train", "same-author"),
        _row("H-002", "HUMAN", "test", "same-author"),
    ])
    report = validate_dataset(frame)
    assert any("leakage" in error for error in report.errors)


def test_requires_model_for_ai_and_edit_level_for_assisted() -> None:
    ai_row = _row("A-001", "AI", "train", "ai-run")
    ai_row["model_name"] = ""
    assisted_row = _row("M-001", "AI_ASSISTED", "test", "author-2")
    assisted_row["editing_level"] = "none"
    report = validate_dataset(pd.DataFrame([ai_row, assisted_row]))
    assert any("model name" in error for error in report.errors)
    assert any("editing level" in error for error in report.errors)


def test_warns_about_possible_personal_information() -> None:
    row = _row("H-001", "HUMAN", "train", "author-1")
    row["text"] += " Contact learner@example.com for further details."
    report = validate_dataset(pd.DataFrame([row]))
    assert any("email address or phone" in warning for warning in report.warnings)


def test_excluded_rows_are_removed_during_preparation() -> None:
    keep = _row("H-001", "HUMAN", "train", "author-1")
    remove = _row("A-001", "AI", "validation", "ai-run-1")
    remove["exclude_from_training"] = True
    prepared = prepare_training_data(pd.DataFrame([keep, remove]))
    assert prepared["record_id"].tolist() == ["H-001"]


def test_fingerprint_ignores_case_and_whitespace() -> None:
    assert text_fingerprint("Learning   matters") == text_fingerprint(" learning matters ")


def test_missing_columns_block_validation() -> None:
    report = validate_dataset(pd.DataFrame({"text": ["sample"]}))
    assert not report.is_valid
    assert report.errors[0].startswith("Missing required columns")


def test_invalid_date_and_blank_provenance_block_validation() -> None:
    row = _row("H-001", "HUMAN", "train", "author-1")
    row["collection_date"] = "07/09/2026"
    row["source_reference"] = ""
    report = validate_dataset(pd.DataFrame([row]))
    assert any("Missing required values" in error for error in report.errors)
    assert any("YYYY-MM-DD" in error for error in report.errors)


def test_warns_when_label_categories_are_absent() -> None:
    report = validate_dataset(pd.DataFrame([_row("H-001", "HUMAN", "train", "author-1")]))
    assert any("no records for labels" in warning for warning in report.warnings)


def test_invalid_dataset_cannot_be_prepared() -> None:
    with pytest.raises(ValueError, match="pass validation"):
        prepare_training_data(pd.DataFrame({"text": ["sample"]}))
