"""
Runs the GTFS validator JAR against a GTFS feed.
Usage: python scripts/run_validator.py --feed [bus|rail]
Reads config from pyproject.toml. Downloads the JAR automatically if missing.
"""

import argparse
import json
import tomllib
import subprocess
import shutil
import sys
from pathlib import Path

parser = argparse.ArgumentParser()
parser.add_argument("--feed", choices=["bus", "rail"], required=True, help="Which GTFS feed to validate")
args = parser.parse_args()

PROJECT_ROOT = Path(__file__).parent.parent
PYPROJECT = PROJECT_ROOT / "pyproject.toml"
JAR = PROJECT_ROOT / "gtfs-validator.jar"
INPUT = PROJECT_ROOT / "gtfs" / f"gtfs_{args.feed}.zip"
OUTPUT = PROJECT_ROOT / "validation-output" / args.feed

with open(PYPROJECT, "rb") as f:
    config = tomllib.load(f)["tool"]["lacmta-gtfs"]

country_code = config.get("default-country-code", "us")

if not JAR.exists():
    print("JAR not found — downloading...")
    subprocess.run(
        ["python", str(PROJECT_ROOT / "scripts" / "download_validator.py")],
        check=True,
    )

if shutil.which("java") is None:
    print(
        "Error: Java not found on PATH.\n"
        "Install Java 17+ by following the instructions at:\n"
        "https://github.com/MobilityData/gtfs-validator?tab=readme-ov-file#using-the-command-line",
        file=sys.stderr,
    )
    sys.exit(1)

if not INPUT.exists():
    print(f"Error: Input file not found: {INPUT}", file=sys.stderr)
    sys.exit(1)

OUTPUT.mkdir(exist_ok=True)

cmd = [
    "java", "-jar", str(JAR),
    "--input", str(INPUT),
    "--output_base", str(OUTPUT),
    "--country_code", country_code,
]

print(f"Running: {' '.join(cmd)}\n")
result = subprocess.run(cmd)

if result.returncode != 0:
    sys.exit(result.returncode)

# Parse report.json and fail loudly if any ERROR-severity notices exist
report_path = OUTPUT / "report.json"
notices = json.loads(report_path.read_text()).get("notices", [])
errors = [n for n in notices if n.get("severity") == "ERROR"]

if errors:
    error_list = "\n".join(f"  • {e['code']} ({e['totalNotices']} occurrence(s))" for e in errors)
    print(
        f"\n{'=' * 60}\n"
        f"GTFS VALIDATION FAILED — {len(errors)} error type(s) found in {args.feed} feed:\n"
        f"{error_list}\n"
        f"\nSee full report: {OUTPUT / 'report.html'}\n"
        f"{'=' * 60}",
        file=sys.stderr,
    )
    sys.exit(1)

print(f"Validation passed for {args.feed} feed.")
