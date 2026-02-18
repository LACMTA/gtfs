"""
Zips GTFS feeds from gtfs-unzipped/{timeframe}/{feed}/ back into gtfs/{timeframe}/{feed}.zip.
Usage: python scripts/zip_gtfs.py [--timeframe {current,future,weekly-update}]
By default, zips all timeframes that exist on disk.
"""

import argparse
import zipfile
from pathlib import Path

TIMEFRAMES = ["current", "future", "weekly-update"]

parser = argparse.ArgumentParser()
parser.add_argument(
    "--timeframe",
    choices=TIMEFRAMES,
    default=None,
    help="Which timeframe to zip (default: all that exist on disk)",
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

    for feed_dir in sorted(p for p in src_dir.iterdir() if p.is_dir()):
        dest = GTFS_DIR / timeframe / f"{feed_dir.name}.zip"
        dest.parent.mkdir(parents=True, exist_ok=True)

        print(f"Zipping {feed_dir.relative_to(PROJECT_ROOT)}/ → {dest.relative_to(PROJECT_ROOT)}")
        # Skip macOS filesystem artifacts
        skip = {".DS_Store"}
        skip_dirs = {"__MACOSX"}

        with zipfile.ZipFile(dest, "w", zipfile.ZIP_DEFLATED) as zf:
            for file_path in sorted(feed_dir.rglob("*")):
                if not file_path.is_file():
                    continue
                if file_path.name in skip:
                    continue
                if any(part in skip_dirs for part in file_path.relative_to(feed_dir).parts):
                    continue
                zf.write(file_path, file_path.relative_to(feed_dir))

print("Done.")
