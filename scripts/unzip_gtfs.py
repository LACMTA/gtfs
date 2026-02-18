"""
Unzips GTFS feeds into gtfs-unzipped/{timeframe}/{feed}/.
Usage: python scripts/unzip_gtfs.py [--timeframe {current,future,weekly-update}] [--service {bus,rail}]
By default, unzips all timeframes and services that exist on disk.
"""

import argparse
import shutil
import zipfile
from pathlib import Path

TIMEFRAMES = ["current", "future", "weekly-update"]
SERVICES = ["bus", "rail"]

parser = argparse.ArgumentParser()
parser.add_argument(
    "--timeframe",
    choices=TIMEFRAMES,
    default=None,
    help="Which timeframe to unzip (default: all that exist on disk)",
)
parser.add_argument(
    "--service",
    choices=SERVICES,
    default=None,
    help="Which service to unzip (default: all services)",
)
args = parser.parse_args()

PROJECT_ROOT = Path(__file__).parent.parent
GTFS_DIR = PROJECT_ROOT / "gtfs"
UNZIPPED_DIR = PROJECT_ROOT / "gtfs-unzipped"

timeframes = [args.timeframe] if args.timeframe else TIMEFRAMES

for timeframe in timeframes:
    src_dir = GTFS_DIR / timeframe
    if not src_dir.exists():
        continue

    zip_paths = sorted(src_dir.glob("*.zip"))

    if args.service:
        zip_paths = [p for p in zip_paths if args.service in p.stem]

    for zip_path in zip_paths:
        dest = UNZIPPED_DIR / timeframe / zip_path.stem
        if dest.exists():
            shutil.rmtree(dest)
        dest.mkdir(parents=True, exist_ok=True)

        print(f"Unzipping {zip_path.relative_to(PROJECT_ROOT)} → {dest.relative_to(PROJECT_ROOT)}/")
        with zipfile.ZipFile(zip_path, "r") as zf:
            zf.extractall(dest)

print("Done.")
