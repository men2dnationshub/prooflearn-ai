"""Training dataset schema, validation and preparation for ProofLearn AI."""

from __future__ import annotations

from dataclasses import dataclass, field
import hashlib
import re

import pandas as pd


LABELS = {"HUMAN", "AI", "AI_ASSISTED"}
SPLITS = {"train", "validation", "test", "unassigned"}
SOURCE_TYPES = {
    "student_consented",
    "public_licensed",
    "synthetic_ai",
    "researcher_created",
}
CONSENT_STATUSES = {"consented", "licensed", "not_applicable"}
EDITING_LEVELS = {"none", "light", "moderate", "substantial", "unknown"}

REQUIRED_COLUMNS = (
    "record_id",
    "text",
    "label",
    "source_type",
    "source_reference",
    "subject",
    "education_level",
    "language",
    "author_group_id",
    "model_name",
    "generation_prompt_id",
    "editing_level",
    "consent_status",
    "license_or_permission",
    "collection_date",
    "split",
    "exclude_from_training",
    "notes",
)

EMAIL_PATTERN = re.compile(r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b", re.I)
PHONE_PATTERN = re.compile(r"(?<!\w)(?:\+?\d[\d ()-]{7,}\d)(?!\w)")


@dataclass
class DatasetValidationReport:
    """Errors block model training; warnings require human review."""

    row_count: int
    eligible_row_count: int = 0
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    label_counts: dict[str, int] = field(default_factory=dict)
    split_counts: dict[str, int] = field(default_factory=dict)

    @property
    def is_valid(self) -> bool:
        return not self.errors


def text_fingerprint(text: str) -> str:
    """Return a stable exact-text fingerprint after whitespace normalisation."""
    normalised = re.sub(r"\s+", " ", str(text)).strip().lower()
    return hashlib.sha256(normalised.encode("utf-8")).hexdigest()


def empty_dataset_template() -> pd.DataFrame:
    """Return an empty dataframe with the canonical input schema."""
    return pd.DataFrame(columns=REQUIRED_COLUMNS)


def _normalise_boolean(value: object) -> bool | None:
    if isinstance(value, bool):
        return value
    value = str(value).strip().lower()
    if value in {"true", "1", "yes", "y"}:
        return True
    if value in {"false", "0", "no", "n"}:
        return False
    return None


def validate_dataset(dataframe: pd.DataFrame, minimum_words: int = 50) -> DatasetValidationReport:
    """Validate provenance, labels, privacy signals and split leakage."""
    report = DatasetValidationReport(row_count=len(dataframe))
    missing_columns = [column for column in REQUIRED_COLUMNS if column not in dataframe.columns]
    if missing_columns:
        report.errors.append("Missing required columns: " + ", ".join(missing_columns))
        return report

    data = dataframe.copy().fillna("")
    data["label"] = data["label"].astype(str).str.strip().str.upper()
    data["split"] = data["split"].astype(str).str.strip().str.lower()
    data["source_type"] = data["source_type"].astype(str).str.strip().str.lower()
    data["consent_status"] = data["consent_status"].astype(str).str.strip().str.lower()
    data["editing_level"] = data["editing_level"].astype(str).str.strip().str.lower()

    always_required = (
        "record_id",
        "text",
        "label",
        "source_type",
        "source_reference",
        "subject",
        "education_level",
        "language",
        "author_group_id",
        "consent_status",
        "license_or_permission",
        "collection_date",
        "split",
    )
    missing_values = {
        column: int(data[column].astype(str).str.strip().eq("").sum())
        for column in always_required
        if data[column].astype(str).str.strip().eq("").any()
    }
    if missing_values:
        details = ", ".join(f"{column} ({count})" for column, count in missing_values.items())
        report.errors.append("Missing required values: " + details)

    duplicate_ids = data.loc[data["record_id"].astype(str).duplicated(keep=False), "record_id"]
    if not duplicate_ids.empty:
        report.errors.append(f"Duplicate record IDs found: {duplicate_ids.nunique()}")

    invalid_labels = sorted(set(data["label"]) - LABELS)
    if invalid_labels:
        report.errors.append("Invalid labels: " + ", ".join(invalid_labels))

    invalid_splits = sorted(set(data["split"]) - SPLITS)
    if invalid_splits:
        report.errors.append("Invalid dataset splits: " + ", ".join(invalid_splits))

    invalid_sources = sorted(set(data["source_type"]) - SOURCE_TYPES)
    if invalid_sources:
        report.errors.append("Invalid source types: " + ", ".join(invalid_sources))

    invalid_consent = sorted(set(data["consent_status"]) - CONSENT_STATUSES)
    if invalid_consent:
        report.errors.append("Invalid consent statuses: " + ", ".join(invalid_consent))

    parsed_dates = pd.to_datetime(data["collection_date"], format="%Y-%m-%d", errors="coerce")
    invalid_dates = parsed_dates.isna() & data["collection_date"].astype(str).str.strip().ne("")
    if invalid_dates.any():
        report.errors.append(
            f"{int(invalid_dates.sum())} rows have invalid collection dates; use YYYY-MM-DD."
        )

    invalid_editing = sorted(set(data["editing_level"]) - EDITING_LEVELS)
    if invalid_editing:
        report.errors.append("Invalid editing levels: " + ", ".join(invalid_editing))

    permission_missing = data["license_or_permission"].astype(str).str.strip().eq("")
    if permission_missing.any():
        report.errors.append(
            f"{int(permission_missing.sum())} rows lack consent or licence evidence."
        )

    ai_model_missing = data["label"].eq("AI") & data["model_name"].astype(str).str.strip().eq("")
    if ai_model_missing.any():
        report.errors.append(f"{int(ai_model_missing.sum())} AI rows lack a model name.")

    assisted_editing_missing = data["label"].eq("AI_ASSISTED") & data["editing_level"].isin({"", "none"})
    if assisted_editing_missing.any():
        report.errors.append(
            f"{int(assisted_editing_missing.sum())} AI_ASSISTED rows lack an editing level."
        )

    blank_text = data["text"].astype(str).str.strip().eq("")
    if blank_text.any():
        report.errors.append(f"{int(blank_text.sum())} rows contain no text.")

    fingerprints = data["text"].map(text_fingerprint)
    duplicate_text = fingerprints.duplicated(keep=False) & ~blank_text
    if duplicate_text.any():
        report.errors.append(
            f"{int(duplicate_text.sum())} rows belong to exact duplicate-text groups."
        )

    word_counts = data["text"].astype(str).str.findall(r"\b\w+\b").str.len()
    short_rows = (word_counts < minimum_words) & ~blank_text
    if short_rows.any():
        report.warnings.append(
            f"{int(short_rows.sum())} rows contain fewer than {minimum_words} words."
        )

    possible_pii = data["text"].astype(str).map(
        lambda text: bool(EMAIL_PATTERN.search(text) or PHONE_PATTERN.search(text))
    )
    if possible_pii.any():
        report.warnings.append(
            f"{int(possible_pii.sum())} rows may contain an email address or phone number."
        )

    assigned = data[data["split"].isin({"train", "validation", "test"})]
    author_split_counts = assigned.groupby("author_group_id")["split"].nunique()
    leaking_authors = author_split_counts[author_split_counts > 1]
    if not leaking_authors.empty:
        report.errors.append(
            f"{len(leaking_authors)} author groups occur across multiple splits, causing leakage."
        )

    excluded = data["exclude_from_training"].map(_normalise_boolean)
    invalid_booleans = excluded.isna()
    if invalid_booleans.any():
        report.errors.append(
            f"{int(invalid_booleans.sum())} rows have invalid exclude_from_training values."
        )

    report.label_counts = {
        str(label): int(count) for label, count in data["label"].value_counts().items()
    }
    report.split_counts = {
        str(split): int(count) for split, count in data["split"].value_counts().items()
    }
    report.eligible_row_count = int((excluded.eq(False) & ~blank_text).sum())

    missing_labels = sorted(LABELS - set(report.label_counts))
    if missing_labels:
        report.warnings.append("Dataset has no records for labels: " + ", ".join(missing_labels))
    if report.label_counts and min(report.label_counts.values()) * 2 < max(report.label_counts.values()):
        report.warnings.append("Class balance exceeds a 2-to-1 ratio and should be reviewed.")
    if "unassigned" in report.split_counts:
        report.warnings.append(
            f"{report.split_counts['unassigned']} rows have not been assigned to a data split."
        )
    return report


def prepare_training_data(dataframe: pd.DataFrame) -> pd.DataFrame:
    """Create reproducible derived fields after successful validation."""
    report = validate_dataset(dataframe)
    if not report.is_valid:
        raise ValueError("Dataset must pass validation before preparation: " + "; ".join(report.errors))

    prepared = dataframe.copy().fillna("")
    prepared["label"] = prepared["label"].astype(str).str.strip().str.upper()
    prepared["split"] = prepared["split"].astype(str).str.strip().str.lower()
    prepared["text"] = prepared["text"].astype(str).map(
        lambda value: re.sub(r"\s+", " ", value).strip()
    )
    prepared["text_sha256"] = prepared["text"].map(text_fingerprint)
    prepared["word_count"] = prepared["text"].str.findall(r"\b\w+\b").str.len()
    prepared["character_count"] = prepared["text"].str.len()
    excluded = prepared["exclude_from_training"].map(_normalise_boolean)
    return prepared.loc[~excluded].reset_index(drop=True)
