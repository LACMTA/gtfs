"""
Weekly update script for the bus GTFS feed.

Steps:
  1. Copy gtfs-unzipped/current/gtfs_bus/ into a working directory at
     temp/working-gtfs/weekly-update/gtfs_bus/.
  2. Fetch calendar_dates.txt from an FTP server and save it to temp/.
  3. Merge the fetched calendar_dates.txt with the one already in the working
     directory, deduplicate, and write the result back.
  4. On success, overwrite gtfs-unzipped/weekly-update/gtfs_bus/ with the
     finished working directory.

Required environment variables (set in a .env file at the project root):
  FTP_HOST                 - FTP server hostname or IP
  FTP_USER                 - FTP username
  FTP_PASSWORD             - FTP password
"""

import ftplib
import os
import shutil
from pathlib import Path

import pandas as pd
from dotenv import load_dotenv

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

load_dotenv()

PROJECT_ROOT = Path(__file__).parent.parent
UNZIPPED_DIR = PROJECT_ROOT / "gtfs-unzipped"
TEMP_DIR = PROJECT_ROOT / "temp"

CURRENT_BUS_DIR = UNZIPPED_DIR / "current" / "gtfs_bus"
WEEKLY_BUS_DIR = UNZIPPED_DIR / "weekly-update" / "gtfs_bus"
WORKING_BUS_DIR = TEMP_DIR / "working-gtfs" / "weekly-update" / "gtfs_bus"

FTP_HOST = os.environ["FTP_HOST"]
FTP_USER = os.environ["FTP_USER"]
FTP_PASSWORD = os.environ["FTP_PASSWORD"]
FTP_REMOTE_PATH = "/nextbus/prod/calendar_dates.txt"

# ---------------------------------------------------------------------------
# Step 1: Copy current bus files into the working directory
# ---------------------------------------------------------------------------

print(
    f"[1/4] Copying {CURRENT_BUS_DIR.relative_to(PROJECT_ROOT)} "
    f"→ {WORKING_BUS_DIR.relative_to(PROJECT_ROOT)} ..."
)

if not CURRENT_BUS_DIR.exists():
    raise FileNotFoundError(
        f"Source directory does not exist: {CURRENT_BUS_DIR}\n"
        "Run 'poe unzip' first to populate gtfs-unzipped/current/."
    )

if WORKING_BUS_DIR.exists():
    shutil.rmtree(WORKING_BUS_DIR)

shutil.copytree(CURRENT_BUS_DIR, WORKING_BUS_DIR)
print("    Done.")

# ---------------------------------------------------------------------------
# Step 2: Fetch calendar_dates.txt from the FTP server
# ---------------------------------------------------------------------------

TEMP_DIR.mkdir(parents=True, exist_ok=True)
temp_calendar_path = TEMP_DIR / "calendar_dates.txt"

print(f"[2/4] Fetching calendar_dates.txt from ftp://{FTP_HOST}/{FTP_REMOTE_PATH} ...")

with ftplib.FTP(FTP_HOST) as ftp:
    ftp.login(FTP_USER, FTP_PASSWORD)
    with open(temp_calendar_path, "wb") as f:
        ftp.retrbinary(f"RETR {FTP_REMOTE_PATH}", f.write)

print(f"    Saved to {temp_calendar_path.relative_to(PROJECT_ROOT)}")

# ---------------------------------------------------------------------------
# Step 3: Merge calendar_dates.txt, deduplicate, and save to working directory
# ---------------------------------------------------------------------------

working_calendar_path = WORKING_BUS_DIR / "calendar_dates.txt"

print("[3/4] Merging calendar_dates.txt files and removing duplicates ...")

df_working = pd.read_csv(working_calendar_path, dtype=str)
df_new = pd.read_csv(temp_calendar_path, dtype=str)

df_merged = (
    pd.concat([df_working, df_new])
    .drop_duplicates()
    .reset_index(drop=True)
)

df_merged.to_csv(working_calendar_path, index=False)

print(
    f"    Merged result ({len(df_merged)} rows) saved to "
    f"{working_calendar_path.relative_to(PROJECT_ROOT)}"
)

# ---------------------------------------------------------------------------
# Step 4: Overwrite gtfs-unzipped/weekly-update/gtfs_bus/ with working copy
# ---------------------------------------------------------------------------

print(
    f"[4/4] Copying {WORKING_BUS_DIR.relative_to(PROJECT_ROOT)} "
    f"→ {WEEKLY_BUS_DIR.relative_to(PROJECT_ROOT)} ..."
)

if WEEKLY_BUS_DIR.exists():
    shutil.rmtree(WEEKLY_BUS_DIR)

shutil.copytree(WORKING_BUS_DIR, WEEKLY_BUS_DIR)
print("    Done.")

print("\nWeekly update complete.")
