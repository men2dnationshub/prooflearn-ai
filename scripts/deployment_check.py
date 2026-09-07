"""Print deployment readiness and exit non-zero when demo deployment is blocked."""

from pathlib import Path
import sys

root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(root))

from modules.deployment import deployment_json, run_deployment_checks


if __name__ == "__main__":
    report = run_deployment_checks(root)
    print(deployment_json(report))
    raise SystemExit(0 if report.demo_deployable else 1)
