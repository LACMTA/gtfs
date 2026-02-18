"""
Downloads the GTFS validator JAR defined by `validator-jar` in pyproject.toml
and saves it as `gtfs-validator.jar` in the project root.
"""

import tomllib
import urllib.request
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
PYPROJECT = PROJECT_ROOT / "pyproject.toml"
OUTPUT = PROJECT_ROOT / "gtfs-validator.jar"

with open(PYPROJECT, "rb") as f:
    config = tomllib.load(f)

try:
    url = config["tool"]["lacmta-gtfs"]["validator-jar"]
except KeyError:
    print("Error: `validator-jar` not found under [tool.lacmta-gtfs] in pyproject.toml", file=sys.stderr)
    sys.exit(1)


def progress(block_count, block_size, total_size):
    if total_size > 0:
        percent = min(block_count * block_size / total_size * 100, 100)
        bar = "#" * int(percent / 2)
        print(f"\r  [{bar:<50}] {percent:.1f}%", end="", flush=True)


print(f"Downloading: {url}")
urllib.request.urlretrieve(url, OUTPUT, reporthook=progress)
print(f"\nSaved to: {OUTPUT}")
