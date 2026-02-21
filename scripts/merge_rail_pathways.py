"""
Merges GTFS pathways data from one set of GTFS files into another.

The script sets up two staging directories in temp/ before performing any
merge work:
  - temp/pathways-source/  – the GTFS that contains the pathways data to pull from
  - temp/pathways-target/  – the GTFS that will receive the pathways data

Usage:
  python scripts/merge_rail_pathways.py \\
      --pathways-source {current,prompt} \\
      --gtfs-target {current,gitlab,prompt}

--pathways-source
  current  Use gtfs-unzipped/current/gtfs_rail/ as the source of pathways data.
  prompt   Prompt for a path to a .zip archive of GTFS to use as the source of pathways data.

--gtfs-target
  current  Use gtfs-unzipped/current/gtfs_rail/ as the GTFS to merge pathways data into.
  gitlab   Fetch the rail GTFS zip from the GitLab URL in gtfs-meta.toml and use it as the
           GTFS to merge pathways data into.
  prompt   Prompt for a path to a .zip archive of GTFS to merge pathways data onto.
"""

import argparse
import shutil
import tomllib
import urllib.request
import zipfile
from pathlib import Path

import pandas as pd

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

PROJECT_ROOT = Path(__file__).parent.parent
META_PATH = PROJECT_ROOT / "gtfs-meta.toml"
UNZIPPED_DIR = PROJECT_ROOT / "gtfs-unzipped"
TEMP_DIR = PROJECT_ROOT / "temp"

with open(META_PATH, "rb") as _f:
    META = tomllib.load(_f)

CURRENT_RAIL_DIR = UNZIPPED_DIR / "current" / "gtfs_rail"

PATHWAYS_SOURCE_DIR = TEMP_DIR / "pathways-source"
GTFS_TARGET_DIR = TEMP_DIR / "pathways-target"
GITLAB_RAIL_DIR = TEMP_DIR / "gitlab-gtfs" / "rail"

# ---------------------------------------------------------------------------
# Argument parsing
# ---------------------------------------------------------------------------

parser = argparse.ArgumentParser(description="Merge GTFS pathways data from one feed into another.")
parser.add_argument(
    "--pathways-source",
    choices=["current", "prompt"],
    required=True,
    help=(
        "Where to get the pathways data from. "
        "'current' uses gtfs-unzipped/current/gtfs_rail/; "
        "'prompt' prompts for a GTFS .zip archive."
    ),
)
parser.add_argument(
    "--gtfs-target",
    choices=["current", "gitlab", "prompt"],
    required=True,
    help=(
        "Which GTFS feed to merge the pathways onto. "
        "'current' uses gtfs-unzipped/current/gtfs_rail/; "
        "'gitlab' fetches the latest from GitLab; "
        "'prompt' prompts for a GTFS .zip archive."
    ),
)
args = parser.parse_args()

# ---------------------------------------------------------------------------
# Helper: validate and return a user-supplied zip path
# ---------------------------------------------------------------------------


def prompt_for_zip(prompt_text: str) -> Path:
    """Prompt the user for a path to a .zip file and validate it."""
    raw = input(f"\n{prompt_text}: ").strip().strip("'\"")
    path = Path(raw).expanduser().resolve()
    if not path.exists():
        raise FileNotFoundError(f"File not found: {path}")
    if not zipfile.is_zipfile(path):
        raise ValueError(f"File does not appear to be a valid zip archive: {path}")
    return path


# ---------------------------------------------------------------------------
# Helper: unzip an archive into a destination directory
# ---------------------------------------------------------------------------


def unzip_into(zip_path: Path, dest_dir: Path) -> None:
    """Unzip *zip_path* into *dest_dir*, clearing the destination first."""
    if dest_dir.exists():
        shutil.rmtree(dest_dir)
    dest_dir.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(zip_path, "r") as zf:
        zf.extractall(dest_dir)


# ---------------------------------------------------------------------------
# Step 1: Populate temp/pathways-source/
# ---------------------------------------------------------------------------

print("=== Step 1: Prepare pathways source ===")

if args.pathways_source == "current":
    if not CURRENT_RAIL_DIR.exists():
        raise FileNotFoundError(
            f"Source directory does not exist: {CURRENT_RAIL_DIR}\n"
            "Run 'poe unzip' first to populate gtfs-unzipped/current/."
        )
    print(
        f"Copying {CURRENT_RAIL_DIR.relative_to(PROJECT_ROOT)}"
        f" → {PATHWAYS_SOURCE_DIR.relative_to(PROJECT_ROOT)} ..."
    )
    if PATHWAYS_SOURCE_DIR.exists():
        shutil.rmtree(PATHWAYS_SOURCE_DIR)
    shutil.copytree(CURRENT_RAIL_DIR, PATHWAYS_SOURCE_DIR)
    print("    Done.")

else:  # prompt
    zip_path = prompt_for_zip("Path to pathways GTFS .zip archive")
    print(f"\nUnzipping {zip_path.name} → {PATHWAYS_SOURCE_DIR.relative_to(PROJECT_ROOT)} ...")
    unzip_into(zip_path, PATHWAYS_SOURCE_DIR)
    print("    Done.")

# ---------------------------------------------------------------------------
# Step 2: Populate temp/pathways-target/
# ---------------------------------------------------------------------------

print("\n=== Step 2: Prepare GTFS target ===")

if args.gtfs_target == "current":
    if not CURRENT_RAIL_DIR.exists():
        raise FileNotFoundError(
            f"Source directory does not exist: {CURRENT_RAIL_DIR}\n"
            "Run 'poe unzip' first to populate gtfs-unzipped/current/."
        )
    print(
        f"Copying {CURRENT_RAIL_DIR.relative_to(PROJECT_ROOT)}"
        f" → {GTFS_TARGET_DIR.relative_to(PROJECT_ROOT)} ..."
    )
    if GTFS_TARGET_DIR.exists():
        shutil.rmtree(GTFS_TARGET_DIR)
    shutil.copytree(CURRENT_RAIL_DIR, GTFS_TARGET_DIR)
    print("    Done.")

elif args.gtfs_target == "gitlab":
    rail_url = META["gitlab"]["rail"]

    GITLAB_RAIL_DIR.mkdir(parents=True, exist_ok=True)
    gitlab_zip_path = GITLAB_RAIL_DIR / "gtfs_rail.zip"

    print(f"Downloading rail GTFS from GitLab:\n    {rail_url}")
    print(f"    → {gitlab_zip_path.relative_to(PROJECT_ROOT)} ...")
    urllib.request.urlretrieve(rail_url, gitlab_zip_path)
    print("    Download complete.")

    print(
        f"\nUnzipping {gitlab_zip_path.relative_to(PROJECT_ROOT)}"
        f" → {GTFS_TARGET_DIR.relative_to(PROJECT_ROOT)} ..."
    )
    unzip_into(gitlab_zip_path, GTFS_TARGET_DIR)
    print("    Done.")

else:  # prompt
    zip_path = prompt_for_zip("Path to GTFS .zip archive to merge onto")
    print(f"\nUnzipping {zip_path.name} → {GTFS_TARGET_DIR.relative_to(PROJECT_ROOT)} ...")
    unzip_into(zip_path, GTFS_TARGET_DIR)
    print("    Done.")

# ---------------------------------------------------------------------------
# Summary
# ---------------------------------------------------------------------------

print("\n=== Setup complete ===")
print(f"  Pathways source : {PATHWAYS_SOURCE_DIR.relative_to(PROJECT_ROOT)}")
print(f"  GTFS target     : {GTFS_TARGET_DIR.relative_to(PROJECT_ROOT)}")
print("\nReady to merge pathways data.")

# ---------------------------------------------------------------------------
# Step 3: Identify stops to carry over from the pathways source
# ---------------------------------------------------------------------------

print("\n=== Step 3: Identify stops in the pathways source ===")

INCLUDED_STOPS: list[str] = META["pathways"]["included_stops"]
print(f"Included parent station stop_ids from gtfs-meta.toml: {INCLUDED_STOPS}")

stops_df = pd.read_csv(PATHWAYS_SOURCE_DIR / "stops.txt", dtype=str).fillna("")

# Recursively expand the set of stop_ids rooted at each included parent station.
# At each iteration, add any stop whose parent_station is already in the set.
in_scope: set[str] = set(INCLUDED_STOPS)
while True:
    children = set(stops_df.loc[stops_df["parent_station"].isin(in_scope), "stop_id"])
    new = children - in_scope
    if not new:
        break
    in_scope.update(new)

scoped_stops = stops_df[stops_df["stop_id"].isin(in_scope)].reset_index(drop=True)

print(f"\nFound {len(scoped_stops)} stops in scope:\n")
print(
    scoped_stops[["stop_id", "stop_name", "location_type", "parent_station"]].to_string(index=False)
)

# ---------------------------------------------------------------------------
# Step 4: Identify pathways to carry over from the pathways source
# ---------------------------------------------------------------------------

print("\n=== Step 4: Identify pathways in the pathways source ===")

pathways_path = PATHWAYS_SOURCE_DIR / "pathways.txt"
scoped_pathways = None

if not pathways_path.exists():
    print("    No pathways.txt found in the pathways source – skipping.")
else:
    pathways_df = pd.read_csv(pathways_path, dtype=str).fillna("")

    scoped_pathways = pathways_df[
        pathways_df["from_stop_id"].isin(in_scope) & pathways_df["to_stop_id"].isin(in_scope)
    ].reset_index(drop=True)

    print(f"Found {len(scoped_pathways)} pathways in scope (out of {len(pathways_df)} total):\n")
    print(
        scoped_pathways[
            ["pathway_id", "from_stop_id", "to_stop_id", "pathway_mode", "is_bidirectional"]
        ].to_string(index=False)
    )

# ---------------------------------------------------------------------------
# Step 5: Identify levels to carry over from the pathways source
# ---------------------------------------------------------------------------

print("\n=== Step 5: Identify levels in the pathways source ===")

levels_path = PATHWAYS_SOURCE_DIR / "levels.txt"
scoped_levels = None

if not levels_path.exists():
    print("    No levels.txt found in the pathways source – skipping.")
else:
    levels_df = pd.read_csv(levels_path, dtype=str).fillna("")

    # Collect the level_ids referenced by our in-scope stops
    scoped_level_ids = set(scoped_stops["level_id"].dropna().unique()) - {""}

    scoped_levels = levels_df[levels_df["level_id"].isin(scoped_level_ids)].reset_index(drop=True)

    print(f"Found {len(scoped_levels)} levels in scope (out of {len(levels_df)} total):\n")
    print(scoped_levels.to_string(index=False))

# ---------------------------------------------------------------------------
# Step 6: Write merged data into temp/pathways-target/
# ---------------------------------------------------------------------------

print("\n=== Step 6: Merge pathways data into GTFS target ===")

# --- stops.txt ---

target_stops_path = GTFS_TARGET_DIR / "stops.txt"
target_stops_df = pd.read_csv(target_stops_path, dtype=str).fillna("")

# Add any missing pathway-related columns
for col in ["stop_timezone", "wheelchair_boarding", "level_id"]:
    if col not in target_stops_df.columns:
        target_stops_df[col] = ""

# Move tpis_name to the end of the column list (by label – data follows)
if "tpis_name" in target_stops_df.columns:
    cols = [c for c in target_stops_df.columns if c != "tpis_name"] + ["tpis_name"]
    target_stops_df = target_stops_df[cols]

# Align scoped_stops to the target column set (fill any missing columns with "")
scoped_stops_aligned = scoped_stops.reindex(columns=target_stops_df.columns, fill_value="")

# Index both DataFrames on stop_id and update target rows with scoped data
target_stops_df = target_stops_df.set_index("stop_id")
scoped_stops_aligned = scoped_stops_aligned.set_index("stop_id")
target_stops_df.update(scoped_stops_aligned)

# Append any scoped stops that do not yet exist in the target
new_stops = scoped_stops_aligned[~scoped_stops_aligned.index.isin(target_stops_df.index)]
if not new_stops.empty:
    target_stops_df = pd.concat([target_stops_df, new_stops])

target_stops_df = target_stops_df.reset_index()
target_stops_df.to_csv(target_stops_path, index=False)
print(
    f"stops.txt    – updated {len(scoped_stops_aligned)} rows, "
    f"wrote {len(target_stops_df)} total rows."
)

# --- pathways.txt ---

if scoped_pathways is not None:
    pathways_out_path = GTFS_TARGET_DIR / "pathways.txt"
    scoped_pathways.to_csv(pathways_out_path, index=False)
    print(f"pathways.txt – wrote {len(scoped_pathways)} rows.")
else:
    print(
        """WARNING: No pathways data found in pathways source. Are you sure you provided the right file?"""
    )  # noqa: E501

# --- levels.txt ---

if scoped_levels is not None:
    levels_out_path = GTFS_TARGET_DIR / "levels.txt"
    scoped_levels.to_csv(levels_out_path, index=False)
    print(f"levels.txt   – wrote {len(scoped_levels)} rows.")
else:
    print("levels.txt   – no source data; skipped.")

print("\nMerge complete.")

# ---------------------------------------------------------------------------
# Step 7: Overwrite gtfs-unzipped/current/gtfs_rail/ with the merged target
# ---------------------------------------------------------------------------

print("\n=== Step 7: Move merged GTFS to gtfs-unzipped/current/gtfs_rail/ ===")

if CURRENT_RAIL_DIR.exists():
    shutil.rmtree(CURRENT_RAIL_DIR)

shutil.copytree(GTFS_TARGET_DIR, CURRENT_RAIL_DIR)

print(
    f"Copied {GTFS_TARGET_DIR.relative_to(PROJECT_ROOT)}"
    f" → {CURRENT_RAIL_DIR.relative_to(PROJECT_ROOT)}"
)
print("\nDone.")
