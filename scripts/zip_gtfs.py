"""
Zips GTFS feeds from gtfs-unzipped/{timeframe}/{feed}/ back into gtfs/{timeframe}/{feed}.zip.
Usage: python scripts/zip_gtfs.py [--timeframe {current,future,weekly-update}] [--service {bus,rail}]
By default, zips all timeframes and services that exist on disk.
"""

import argparse
import zipfile
from pathlib import Path

TIMEFRAMES = ["current", "future", "weekly-update"]
SERVICES = ["bus", "rail"]

parser = argparse.ArgumentParser()
parser.add_argument(
    "--timeframe",
    choices=TIMEFRAMES,
    default=None,
    help="Which timeframe to zip (default: all that exist on disk)",
)
parser.add_argument(
    "--service",
    choices=SERVICES,
    default=None,
    help="Which service to zip (default: all services)",
)
args = parser.parse_args()

PROJECT_ROOT = Path(__file__).parent.parent
GTFS_DIR = PROJECT_ROOT / "gtfs"
UNZIPPED_DIR = PROJECT_ROOT / "gtfs-unzipped"

timeframes = [args.timeframe] if args.timeframe else TIMEFRAMES

for timeframe in timeframes:
    src_dir = UNZIPPED_DIR / timeframe
    if not src_dir.exists():
        continue

    feed_dirs = sorted(p for p in src_dir.iterdir() if p.is_dir())

    if args.service:
        feed_dirs = [p for p in feed_dirs if args.service in p.name]

    for feed_dir in feed_dirs:
        dest = GTFS_DIR / timeframe / f"{feed_dir.name}.zip"
        dest.parent.mkdir(parents=True, exist_ok=True)

        print(f"Zipping {feed_dir.relative_to(PROJECT_ROOT)}/ → {dest.relative_to(PROJECT_ROOT)}")
        # Skip macOS filesystem artifacts
        skip = {".DS_Store"}
        skip_dirs = {"__MACOSX"}

        # Use a fixed timestamp so identical content produces identical zips
        FIXED_DATE = (2020, 1, 1, 0, 0, 0)

        with zipfile.ZipFile(dest, "w", zipfile.ZIP_DEFLATED) as zf:
            for file_path in sorted(feed_dir.rglob("*")):
                if not file_path.is_file():
                    continue
                if file_path.name in skip:
                    continue
                if any(part in skip_dirs for part in file_path.relative_to(feed_dir).parts):
                    continue
                info = zipfile.ZipInfo(
                    filename=str(file_path.relative_to(feed_dir)),
                    date_time=FIXED_DATE,
                )
                info.compress_type = zipfile.ZIP_DEFLATED
                zf.writestr(info, file_path.read_bytes())

print("Done.")
