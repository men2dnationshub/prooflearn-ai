"""Deployment checks for the controlled ProofLearn AI prototype."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path
import json
import re
from typing import Any

from modules.config import APP_VERSION


@dataclass(frozen=True)
class DeploymentCheck:
    name: str
    status: str
    detail: str


@dataclass(frozen=True)
class DeploymentReport:
    application_version: str
    status: str
    demo_deployable: bool
    production_ready: bool
    checks: tuple[DeploymentCheck, ...]
    production_blockers: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


REQUIRED_FILES = (
    "app.py",
    "requirements.txt",
    ".streamlit/config.toml",
    ".github/workflows/ci.yml",
    "docs/deployment_guide.md",
    "docs/operations_runbook.md",
)

PRODUCTION_BLOCKERS = (
    "No representative authorised training corpus is bundled.",
    "No independently validated production model is approved.",
    "Institutional privacy, accessibility and academic-integrity review is pending.",
    "A supervised educator pilot has not yet been completed.",
)


def _check(status: bool, name: str, passed: str, failed: str) -> DeploymentCheck:
    return DeploymentCheck(name, "PASS" if status else "FAIL", passed if status else failed)


def run_deployment_checks(root: str | Path) -> DeploymentReport:
    """Check whether the repository can be published as a controlled demo."""
    root = Path(root)
    checks: list[DeploymentCheck] = []

    for relative in REQUIRED_FILES:
        present = (root / relative).is_file()
        checks.append(_check(present, f"file:{relative}", "Present", "Missing"))

    requirements_path = root / "requirements.txt"
    requirements = requirements_path.read_text(encoding="utf-8") if requirements_path.exists() else ""
    unpinned = [
        line for line in requirements.splitlines()
        if line.strip() and not line.lstrip().startswith(("#", "-"))
        and not re.search(r"===?[^=]", line)
    ]
    checks.append(_check(not unpinned, "dependencies:pinned", "Runtime dependencies are pinned", f"Unpinned: {', '.join(unpinned)}"))

    forbidden = (root / ".env", root / ".streamlit" / "secrets.toml")
    exposed = [str(path.relative_to(root)) for path in forbidden if path.exists()]
    checks.append(_check(not exposed, "secrets:not_packaged", "No local secret files are present", f"Remove: {', '.join(exposed)}"))

    deployable = all(check.status == "PASS" for check in checks)
    return DeploymentReport(
        application_version=APP_VERSION,
        status="DEPLOYABLE_PROTOTYPE" if deployable else "DEPLOYMENT_BLOCKED",
        demo_deployable=deployable,
        production_ready=False,
        checks=tuple(checks),
        production_blockers=PRODUCTION_BLOCKERS,
    )


def deployment_json(report: DeploymentReport) -> str:
    return json.dumps(report.to_dict(), indent=2)
