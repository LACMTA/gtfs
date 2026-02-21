# gtfs

GTFS automation scripts for LA Metro.

## Getting started

### 1. Install `uv`

Follow the [uv installation instructions](https://docs.astral.sh/uv/getting-started/installation/). We use uv as a package and Python environment manager to make these operations portable across platforms.

### 2. Install Java

Java is required to run the GTFS validator. Install Java 17+ by following the instructions at:
https://github.com/MobilityData/gtfs-validator?tab=readme-ov-file#using-the-command-line

### 3. Download the validator

```bash
uv run poe download-validator
```

This downloads the GTFS validator JAR (defined in `pyproject.toml`) and saves it as `gtfs-validator.jar` in the project root.

### 4. (Optional) Configure environment variables

Some scripts require FTP credentials. Copy `.env.example` to `.env` and fill in the values:

```bash
cp .env.example .env
```

| Variable       | Description  |
| -------------- | ------------ |
| `FTP_HOST`     | FTP server   |
| `FTP_USER`     | FTP username |
| `FTP_PASSWORD` | FTP password |

---

## Scripts

All scripts are run via `uv run poe <task>`.

### `download-validator`

Downloads the GTFS validator JAR file specified by `validator-jar` in `pyproject.toml` and saves it as `gtfs-validator.jar` in the project root.

```bash
uv run poe download-validator
```

---

### `unzip`

Unzips GTFS feed `.zip` files from `gtfs/{timeframe}/` into `gtfs-unzipped/{timeframe}/{feed}/`. By default, unzips all timeframes (`current`, `future`, `weekly-update`) and services (`bus`, `rail`) that exist on disk. Accepts optional `--timeframe` and `--service` flags to narrow the scope.

```bash
uv run poe unzip
```

---

### `zip`

The inverse of `unzip`. Re-zips GTFS feeds from `gtfs-unzipped/{timeframe}/{feed}/` back into `gtfs/{timeframe}/{feed}.zip`. By default, zips all timeframes and services that exist on disk. Accepts optional `--timeframe` and `--service` flags. Uses a fixed timestamp so that identical file content always produces identical zips.

```bash
uv run poe zip
```

---

### `validate`

Runs the GTFS validator JAR against the GTFS feed `.zip` files. By default, validates all timeframes and services for which a `.zip` file exists on disk. Accepts optional `--timeframe` and `--service` flags. Automatically downloads the validator JAR if it is not already present. Outputs HTML and JSON reports to `validation-output/{timeframe}/{service}/` and exits with a non-zero status if any ERROR-severity notices are found.

```bash
uv run poe validate
```

---

### `fetch-current-gitlab`

Downloads the current bus and rail GTFS `.zip` files from their GitLab permalink URLs and saves them to `gtfs/current/`. By default, downloads both services. Accepts an optional `--service` flag to download only `bus` or `rail`. Note that this **does not merge pathways data from the existing rail GTFS** and isntead will just overwrite with data from GitLab. To instead fetch and merge with current pathways, use `uv run poe merge-gitlab-rail`.

```bash
uv run poe fetch-current-gitlab
```

---

### `bus-weekly-update`

Prepares a weekly-update bus GTFS feed by merging updated calendar data from the FTP server into the current bus feed.

Requires `FTP_HOST`, `FTP_USER`, and `FTP_PASSWORD` to be set in `.env`.

```bash
uv run poe bus-weekly-update
```

---

### `manual-bus-update`

Applies a new bus GTFS zip to `gtfs-unzipped/current/gtfs_bus/` with updated feed date range values. Interactively prompts for:

1. Path to the new GTFS `.zip` file.
2. `feed_start_date` (YYYYMMDD).
3. `feed_end_date` (YYYYMMDD).

Unzips the new GTFS into a temporary working directory, copies over the existing `feed_info.txt`, updates the date range fields, then overwrites `gtfs-unzipped/current/gtfs_bus/` with the result.

```bash
uv run poe manual-bus-update
```

---

### `merge-rail-pathways`

Merges GTFS pathways data (`pathways.txt`, `levels.txt`, and related stops from `stops.txt`) from one GTFS feed into another. The set of stations to include is controlled by `included_stops` in `gtfs-meta.toml`. Requires `--pathways-source` and `--gtfs-target` arguments:

| Argument            | Values    | Description                                                           |
| ------------------- | --------- | --------------------------------------------------------------------- |
| `--pathways-source` | `current` | Use `gtfs-unzipped/current/gtfs_rail/` as the source of pathways data |
|                     | `prompt`  | Prompt for a path to a GTFS `.zip` archive                            |
| `--gtfs-target`     | `current` | Merge pathways into `gtfs-unzipped/current/gtfs_rail/`                |
|                     | `gitlab`  | Fetch the latest rail GTFS from GitLab and merge pathways into it     |
|                     | `prompt`  | Prompt for a path to a GTFS `.zip` archive to merge pathways into     |

```bash
uv run poe merge-rail-pathways -- --pathways-source <source> --gtfs-target <target>
```

---

### `manual-rail-pathways-import`

Use this to import a fresh set of pathways data from a local file into the current rail feed. This is a preset of `merge-rail-pathways` that uses the current rail feed as the target (`--gtfs-target current`) and prompts for the pathways source zip (`--pathways-source prompt`).

```bash
uv run poe manual-rail-pathways-import
```

---

### `merge-gitlab-rail`

Use this to apply the current pathways data onto the latest GitLab rail feed. This is a preset of `merge-rail-pathways` that fetches the latest rail GTFS from GitLab as the target (`--gtfs-target gitlab`) and uses the current rail feed as the pathways source (`--pathways-source current`).

```bash
uv run poe merge-gitlab-rail
```

---

### `revert-gtfs`

Reverts the `gtfs/` and `validation-output/` directories to their last committed state via `git checkout`, then re-unzips the feeds. Useful for discarding local changes and resetting to a clean state.

```bash
uv run poe revert-gtfs
```
