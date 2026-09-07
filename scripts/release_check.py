from pathlib import Path
import sys

root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(root))

from modules.release_readiness import readiness_json, run_readiness_checks

if __name__ == "__main__":
    print(readiness_json(run_readiness_checks(root)))
