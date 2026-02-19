"""
Manual pathways update script for the rail GTFS feed.

Merges pathways data from an external GTFS zip into the current rail feed.

Steps:
  1. Copy gtfs-unzipped/current/gtfs_rail/ into a working directory at
     temp/working-gtfs/current/gtfs_rail/.
  2. Prompt for a path to a GTFS zip containing pathways data.
  3. Unzip that file into temp/pathways-import/.
  4. Copy pathways.txt, levels.txt, and stops.txt from temp/pathways-import/
     into the working directory, overwriting any existing files.
  5. On success, overwrite gtfs-unzipped/current/gtfs_rail/ with the working
     directory.
"""

import shutil
import zipfile
from pathlib import Path

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

PROJECT_ROOT = Path(__file__).parent.parent
UNZIPPED_DIR = PROJECT_ROOT / "gtfs-unzipped"
TEMP_DIR = PROJECT_ROOT / "temp"

CURRENT_RAIL_DIR = UNZIPPED_DIR / "current" / "gtfs_rail"
WORKING_RAIL_DIR = TEMP_DIR / "working-gtfs" / "current" / "gtfs_rail"
PATHWAYS_IMPORT_DIR = TEMP_DIR / "pathways-import"

PATHWAYS_FILES = ["pathways.txt", "levels.txt", "stops.txt"]

# ---------------------------------------------------------------------------
# Step 1: Copy current rail files into the working directory
# ---------------------------------------------------------------------------

print(
    f"[1/4] Copying {CURRENT_RAIL_DIR.relative_to(PROJECT_ROOT)} "
    f"→ {WORKING_RAIL_DIR.relative_to(PROJECT_ROOT)} ..."
)

if not CURRENT_RAIL_DIR.exists():
    raise FileNotFoundError(
        f"Source directory does not exist: {CURRENT_RAIL_DIR}\n"
        "Run 'poe unzip' first to populate gtfs-unzipped/current/."
    )

if WORKING_RAIL_DIR.exists():
    shutil.rmtree(WORKING_RAIL_DIR)

shutil.copytree(CURRENT_RAIL_DIR, WORKING_RAIL_DIR)
print("    Done.")

# ---------------------------------------------------------------------------
# Step 2: Prompt for the path to the pathways GTFS zip
# ---------------------------------------------------------------------------

zip_path_input = input("\nPath to pathways GTFS zip file: ").strip().strip("'\"")
zip_path = Path(zip_path_input).expanduser().resolve()

if not zip_path.exists():
    raise FileNotFoundError(f"Zip file not found: {zip_path}")

if not zipfile.is_zipfile(zip_path):
    raise ValueError(f"File does not appear to be a valid zip: {zip_path}")

# ---------------------------------------------------------------------------
# Step 3: Unzip into temp/pathways-import/
# ---------------------------------------------------------------------------

print(
    f"\n[2/4] Unzipping {zip_path.name} "
    f"→ {PATHWAYS_IMPORT_DIR.relative_to(PROJECT_ROOT)} ..."
)

if PATHWAYS_IMPORT_DIR.exists():
    shutil.rmtree(PATHWAYS_IMPORT_DIR)

PATHWAYS_IMPORT_DIR.mkdir(parents=True, exist_ok=True)

with zipfile.ZipFile(zip_path, "r") as zf:
    zf.extractall(PATHWAYS_IMPORT_DIR)

print("    Done.")

# ---------------------------------------------------------------------------
# Step 4: Copy pathways files into the working directory
# ---------------------------------------------------------------------------

print(f"\n[3/4] Copying pathways files into {WORKING_RAIL_DIR.relative_to(PROJECT_ROOT)} ...")

for filename in PATHWAYS_FILES:
    src = PATHWAYS_IMPORT_DIR / filename
    dest = WORKING_RAIL_DIR / filename
    if not src.exists():
        raise FileNotFoundError(
            f"Expected file not found in pathways zip: {filename}"
        )
    overwriting = dest.exists()
    shutil.copy2(src, dest)
    print(f"    {filename} → copied{'  (overwrote existing)' if overwriting else ''}")

print("    Done.")

# ---------------------------------------------------------------------------
# Step 5: Overwrite gtfs-unzipped/current/gtfs_rail/ with the working copy
# ---------------------------------------------------------------------------

print(
    f"\n[4/4] Copying {WORKING_RAIL_DIR.relative_to(PROJECT_ROOT)} "
    f"→ {CURRENT_RAIL_DIR.relative_to(PROJECT_ROOT)} ..."
)

if CURRENT_RAIL_DIR.exists():
    shutil.rmtree(CURRENT_RAIL_DIR)

shutil.copytree(WORKING_RAIL_DIR, CURRENT_RAIL_DIR)
print("    Done.")

print("\nRail pathways update complete.")
