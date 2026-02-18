"""
Manual update script for the bus GTFS feed.

Allows a new GTFS zip to be applied to gtfs-unzipped/current/gtfs_bus/ with
updated feed date range values.

Steps:
  1. Prompt for a path to a zip of new GTFS files.
  2. Unzip those files into temp/working-gtfs/current/gtfs_bus/.
  3. Copy feed_info.txt from gtfs-unzipped/current/gtfs_bus/ into the working
     directory, then prompt for feed_start_date and feed_end_date and write
     those values into the working copy of feed_info.txt.
  4. On success, overwrite gtfs-unzipped/current/gtfs_bus/ with the working
     directory.
"""

import shutil
import zipfile
from pathlib import Path

import pandas as pd

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

PROJECT_ROOT = Path(__file__).parent.parent
UNZIPPED_DIR = PROJECT_ROOT / "gtfs-unzipped"
TEMP_DIR = PROJECT_ROOT / "temp"

CURRENT_BUS_DIR = UNZIPPED_DIR / "current" / "gtfs_bus"
WORKING_BUS_DIR = TEMP_DIR / "working-gtfs" / "current" / "gtfs_bus"

# ---------------------------------------------------------------------------
# Step 1: Prompt for the path to the new GTFS zip
# ---------------------------------------------------------------------------

zip_path_input = input("Path to new GTFS zip file: ").strip().strip("'\"")
zip_path = Path(zip_path_input).expanduser().resolve()

if not zip_path.exists():
    raise FileNotFoundError(f"Zip file not found: {zip_path}")

if not zipfile.is_zipfile(zip_path):
    raise ValueError(f"File does not appear to be a valid zip: {zip_path}")

# ---------------------------------------------------------------------------
# Step 2: Unzip into the working directory
# ---------------------------------------------------------------------------

print(
    f"\n[1/3] Unzipping {zip_path.name} "
    f"→ {WORKING_BUS_DIR.relative_to(PROJECT_ROOT)} ..."
)

if WORKING_BUS_DIR.exists():
    shutil.rmtree(WORKING_BUS_DIR)

WORKING_BUS_DIR.mkdir(parents=True, exist_ok=True)

with zipfile.ZipFile(zip_path, "r") as zf:
    zf.extractall(WORKING_BUS_DIR)

print("    Done.")

# ---------------------------------------------------------------------------
# Step 3: Copy feed_info.txt from current, update date range, and save
# ---------------------------------------------------------------------------

source_feed_info = CURRENT_BUS_DIR / "feed_info.txt"
working_feed_info = WORKING_BUS_DIR / "feed_info.txt"

if not source_feed_info.exists():
    raise FileNotFoundError(
        f"feed_info.txt not found in source directory: {source_feed_info}\n"
        "Run 'poe unzip' first to populate gtfs-unzipped/current/."
    )

print("\n[2/3] Updating feed_info.txt ...")

shutil.copy2(source_feed_info, working_feed_info)

feed_start_date = input("  feed_start_date (YYYYMMDD): ").strip()
feed_end_date = input("  feed_end_date   (YYYYMMDD): ").strip()

# Basic format validation
for label, value in [("feed_start_date", feed_start_date), ("feed_end_date", feed_end_date)]:
    if not value.isdigit() or len(value) != 8:
        raise ValueError(
            f"Invalid {label} '{value}'. Expected 8-digit date in YYYYMMDD format."
        )

df = pd.read_csv(working_feed_info, dtype=str)

if "feed_start_date" not in df.columns or "feed_end_date" not in df.columns:
    raise ValueError(
        "feed_info.txt is missing expected columns "
        "'feed_start_date' and/or 'feed_end_date'."
    )

df["feed_start_date"] = feed_start_date
df["feed_end_date"] = feed_end_date
df.to_csv(working_feed_info, index=False)

print(
    f"    feed_start_date = {feed_start_date}, feed_end_date = {feed_end_date} "
    f"written to {working_feed_info.relative_to(PROJECT_ROOT)}"
)

# ---------------------------------------------------------------------------
# Step 4: Overwrite gtfs-unzipped/current/gtfs_bus/ with the working copy
# ---------------------------------------------------------------------------

print(
    f"\n[3/3] Copying {WORKING_BUS_DIR.relative_to(PROJECT_ROOT)} "
    f"→ {CURRENT_BUS_DIR.relative_to(PROJECT_ROOT)} ..."
)

if CURRENT_BUS_DIR.exists():
    shutil.rmtree(CURRENT_BUS_DIR)

shutil.copytree(WORKING_BUS_DIR, CURRENT_BUS_DIR)
print("    Done.")

print("\nManual bus update complete.")
