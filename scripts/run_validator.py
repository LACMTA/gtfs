"""
Runs the GTFS validator JAR against a GTFS feed.
Usage: python scripts/run_validator.py [--service {bus,rail}] [--timeframe {current,future,weekly-update}]
By default, validates all timeframes and services for which a .zip file exists on disk.
Reads config from pyproject.toml. Downloads the JAR automatically if missing.
"""

import argparse
import json
import tomllib
import subprocess
import shutil
import sys
from pathlib import Path

TIMEFRAMES = ["current", "future", "weekly-update"]
SERVICES = ["bus", "rail"]

parser = argparse.ArgumentParser()
parser.add_argument("--service", choices=SERVICES, default=None, help="Which GTFS feed to validate (default: all that exist on disk)")
parser.add_argument("--timeframe", choices=TIMEFRAMES, default=None, help="Which timeframe to validate (default: all that exist on disk)")
args = parser.parse_args()

PROJECT_ROOT = Path(__file__).parent.parent
PYPROJECT = PROJECT_ROOT / "pyproject.toml"
JAR = PROJECT_ROOT / "gtfs-validator.jar"

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

# Collect all (timeframe, service) pairs to validate
timeframes = [args.timeframe] if args.timeframe else TIMEFRAMES
services = [args.service] if args.service else SERVICES

targets = [
    (timeframe, service)
    for timeframe in timeframes
    for service in services
    if (PROJECT_ROOT / "gtfs" / timeframe / f"gtfs_{service}.zip").exists()
]

if not targets:
    print("No matching .zip files found to validate.", file=sys.stderr)
    sys.exit(1)

overall_failed = False

for timeframe, service in targets:
    INPUT = PROJECT_ROOT / "gtfs" / timeframe / f"gtfs_{service}.zip"
    OUTPUT = PROJECT_ROOT / "validation-output" / timeframe / service

    OUTPUT.mkdir(parents=True, exist_ok=True)

    cmd = [
        "java", "-jar", str(JAR),
        "--input", str(INPUT),
        "--output_base", str(OUTPUT),
        "--country_code", country_code,
    ]

    print(f"Running: {' '.join(cmd)}\n")
    result = subprocess.run(cmd)

    if result.returncode != 0:
        overall_failed = True
        continue

    # Parse report.json and fail loudly if any ERROR-severity notices exist
    report_path = OUTPUT / "report.json"
    notices = json.loads(report_path.read_text()).get("notices", [])
    errors = [n for n in notices if n.get("severity") == "ERROR"]

    if errors:
        error_list = "\n".join(f"  • {e['code']} ({e['totalNotices']} occurrence(s))" for e in errors)
        print(
            f"\n{'=' * 60}\n"
            f"GTFS VALIDATION FAILED — {len(errors)} error type(s) found in {timeframe} {service} feed:\n"
            f"{error_list}\n"
            f"\nSee full report: {OUTPUT / 'report.html'}\n"
            f"{'=' * 60}",
            file=sys.stderr,
        )
        overall_failed = True
    else:
        print(f"Validation passed for {timeframe} {service} feed.")

if overall_failed:
    sys.exit(1)
