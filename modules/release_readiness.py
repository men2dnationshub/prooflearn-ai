"""Automated release evidence for the ProofLearn AI prototype."""

from __future__ import annotations
from dataclasses import asdict, dataclass
from pathlib import Path
import importlib
import json
import sys
from typing import Any
from modules.config import APP_VERSION

REQUIRED_MODULES = (
    "document_reader", "feature_extractor", "dataset_manager", "authorship_model",
    "risk_engine", "passage_analyzer", "question_generator", "writing_assistant",
    "deployment",
)
REQUIRED_PAGES = (
    "1_Assignment_Review.py", "2_Proof_of_Learning.py", "3_Writing_Assistant.py",
    "4_Dataset_Lab.py", "5_Reports.py",
)

@dataclass(frozen=True)
class ReadinessCheck:
    name: str
    status: str
    detail: str

@dataclass(frozen=True)
class ReadinessReport:
    application_version: str
    python_version: str
    status: str
    production_ready: bool
    checks: tuple[ReadinessCheck, ...]
    blockers: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]: return asdict(self)

def run_readiness_checks(root: str | Path) -> ReadinessReport:
    root = Path(root); checks = []
    for name in REQUIRED_MODULES:
        try: importlib.import_module(f"modules.{name}")
        except Exception as exc: checks.append(ReadinessCheck(f"module:{name}", "FAIL", str(exc)))
        else: checks.append(ReadinessCheck(f"module:{name}", "PASS", "Import succeeded"))
    for name in REQUIRED_PAGES:
        exists = (root / "pages" / name).is_file()
        checks.append(ReadinessCheck(f"page:{name}", "PASS" if exists else "FAIL", "Present" if exists else "Missing"))
    secret_present = (root / ".env").exists()
    checks.append(ReadinessCheck("secrets", "FAIL" if secret_present else "PASS", "No local .env packaged" if not secret_present else "Local .env must not be packaged"))
    checks.append(ReadinessCheck("automated_tests", "MANUAL", "Run: python -m pytest -q"))
    blockers = (
        "No representative authorised training corpus is bundled.",
        "No independently validated production model is approved.",
        "Institutional privacy, accessibility and academic-integrity review is pending.",
        "A real educator pilot has not yet been completed.",
    )
    failed = any(check.status == "FAIL" for check in checks)
    return ReadinessReport(
        application_version=APP_VERSION,
        python_version=sys.version.split()[0],
        status="CHECKS_FAILED" if failed else "PROTOTYPE_VALIDATED",
        production_ready=False,
        checks=tuple(checks),
        blockers=blockers,
    )

def readiness_json(report: ReadinessReport) -> str:
    return json.dumps(report.to_dict(), indent=2)
