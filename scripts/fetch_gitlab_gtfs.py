"""
Downloads the current GTFS zip files from GitLab permalinks.

Saves each file to gtfs/current/gtfs_{service}.zip, overwriting any
existing file.

Usage: python scripts/fetch_gitlab_gtfs.py [--service {bus,rail}]
By default, downloads both bus and rail.
"""

import argparse
import urllib.request
from pathlib import Path

# ---------------------------------------------------------------------------
# Configuration – fill in the GitLab permalink for each service
# ---------------------------------------------------------------------------

GITLAB_URLS = {
    "bus": "https://gitlab.com/LACMTA/gtfs_bus/-/raw/master/gtfs_bus.zip?ref_type=heads&inline=false",
    "rail": "https://gitlab.com/LACMTA/gtfs_rail/-/raw/master/gtfs_rail.zip?ref_type=heads&inline=false",
}

SERVICES = ["bus", "rail"]

# ---------------------------------------------------------------------------
# Argument parsing
# ---------------------------------------------------------------------------

parser = argparse.ArgumentParser(
    description="Download current GTFS zips from GitLab permalinks."
)
parser.add_argument(
    "--service",
    choices=SERVICES,
    default=None,
    help="Which service to download (default: both bus and rail)",
)
args = parser.parse_args()

services = [args.service] if args.service else SERVICES

# ---------------------------------------------------------------------------
# Download
# ---------------------------------------------------------------------------

PROJECT_ROOT = Path(__file__).parent.parent
CURRENT_DIR = PROJECT_ROOT / "gtfs" / "current"
CURRENT_DIR.mkdir(parents=True, exist_ok=True)

for service in services:
    url = GITLAB_URLS[service]
    if not url:
        print(f"[{service}] No URL configured – skipping.")
        continue

    dest = CURRENT_DIR / f"gtfs_{service}.zip"
    print(f"[{service}] Downloading {url} ...")
    urllib.request.urlretrieve(url, dest)
    print(f"[{service}] Saved to {dest.relative_to(PROJECT_ROOT)}")

print("Done.")
