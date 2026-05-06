"""Validate the EvalsLangchain live UI project."""

from __future__ import annotations

import argparse
import compileall
import json
from pathlib import Path
import subprocess
import sys

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from src.ui.engine.config import DEFAULT_DATASET
from src.ui.engine.validation import ValidationReport, validate_project
from src.ui.store.paths import RUNS_PATH


def run_compile_check(report: ValidationReport) -> None:
    ok = compileall.compile_dir(REPO_ROOT / "src", quiet=1)
    if ok:
        report.add("info", "compile", "Compiled src/ successfully.", REPO_ROOT / "src")
    else:
        report.add("error", "compile", "Python compilation failed in src/.", REPO_ROOT / "src")


def run_tests(report: ValidationReport) -> None:
    result = subprocess.run(
        [sys.executable, "-m", "unittest", "discover", "-s", "tests"],
        cwd=REPO_ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    if result.returncode == 0:
        report.add("info", "tests", "Unit tests passed.", REPO_ROOT / "tests")
    else:
        details = (result.stdout + "\n" + result.stderr).strip()
        report.add("error", "tests", details or "Unit tests failed.", REPO_ROOT / "tests")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Validate imports, data, run storage, compilation, and tests.")
    parser.add_argument("--dataset", default=DEFAULT_DATASET, help="Dataset path to validate.")
    parser.add_argument("--runs", default=str(RUNS_PATH), help="Run store JSON path to validate.")
    parser.add_argument("--skip-tests", action="store_true", help="Skip unittest discovery.")
    parser.add_argument("--json", action="store_true", help="Print machine-readable JSON output.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    report = validate_project(dataset_path=args.dataset, runs_path=Path(args.runs))
    run_compile_check(report)
    if not args.skip_tests:
        run_tests(report)

    if args.json:
        print(json.dumps({"ok": report.ok, "issues": report.as_rows()}, indent=2, ensure_ascii=False))
    else:
        status = "OK" if report.ok else "FAILED"
        print(f"Project validation: {status}")
        for issue in report.issues:
            path = f" ({issue.path})" if issue.path else ""
            print(f"[{issue.level.upper()}] {issue.check}: {issue.message}{path}")

    return 0 if report.ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
