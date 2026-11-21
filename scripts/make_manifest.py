#!/usr/bin/env python3
"""Regenerate the repository artifact manifest.

Walks the research artifact directories, records each file's size and SHA-256,
and writes two outputs:

    docs/artifact_manifest.md   human-readable table, grouped by directory
    docs/artifact_manifest.csv  machine-readable (path, bytes, sha256)

This script only reads existing artifacts and only writes the two files above.
It never modifies anything under data/, embeddings/, figures/, logs/,
metadata/ or results/.

Usage:
    python scripts/make_manifest.py              # regenerate both outputs
    python scripts/make_manifest.py --check      # fail if outputs are stale
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import io
import sys
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]

ARTIFACT_DIRECTORIES = [
    "data/raw",
    "data/processed",
    "embeddings",
    "figures",
    "logs",
    "metadata",
    "results",
]

TOP_LEVEL_ARTIFACTS = ["synonymous_composition.ipynb"]

MARKDOWN_OUTPUT = REPO_ROOT / "docs" / "artifact_manifest.md"
CSV_OUTPUT = REPO_ROOT / "docs" / "artifact_manifest.csv"

# Files excluded from version control by .gitignore. They are still manifested
# when present locally, but flagged so a reader knows why a clone lacks them.
NOT_VERSION_CONTROLLED = {
    "data/raw/Homo_sapiens.GRCh38.cds.all.fa.gz",
    "data/processed/validated_cds_candidates.csv",
    "data/processed/validated_cds_candidates_with_token_lengths.csv",
}


def sha256_of(path: Path) -> str:
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def human_size(num_bytes: int) -> str:
    size = float(num_bytes)
    for unit in ["B", "KB", "MB", "GB"]:
        if size < 1024 or unit == "GB":
            return f"{size:.1f} {unit}" if unit != "B" else f"{int(size)} B"
        size /= 1024
    return f"{size:.1f} GB"


def collect() -> list[dict]:
    records = []
    paths: list[Path] = []
    for name in TOP_LEVEL_ARTIFACTS:
        candidate = REPO_ROOT / name
        if candidate.exists():
            paths.append(candidate)
    for directory in ARTIFACT_DIRECTORIES:
        base = REPO_ROOT / directory
        if not base.exists():
            continue
        paths.extend(sorted(p for p in base.rglob("*") if p.is_file()))

    for path in paths:
        relative = path.relative_to(REPO_ROOT).as_posix()
        records.append(
            {
                "path": relative,
                "bytes": path.stat().st_size,
                "sha256": sha256_of(path),
                "version_controlled": relative not in NOT_VERSION_CONTROLLED,
            }
        )
    return records


def render_markdown(records: list[dict]) -> str:
    out = io.StringIO()
    generated = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    total = sum(record["bytes"] for record in records)

    out.write("# Artifact Manifest\n\n")
    out.write(
        "Inventory of every research artifact in this repository with its exact size\n"
        "and SHA-256 digest, so that any copy can be checked for bit-level integrity.\n\n"
    )
    out.write(
        "Regenerate with `python scripts/make_manifest.py`; verify an existing copy\n"
        "with `python scripts/verify_artifacts.py`.\n\n"
    )
    out.write(f"- Generated: {generated}\n")
    out.write(f"- Files: {len(records)}\n")
    out.write(f"- Total size: {human_size(total)}\n\n")
    out.write(
        "Rows marked :no_entry: are excluded from version control by `.gitignore`\n"
        "(too large for GitHub, and regenerable). See\n"
        "[reproducibility.md](reproducibility.md).\n"
    )

    groups: dict[str, list[dict]] = {}
    for record in records:
        directory = record["path"].rsplit("/", 1)[0] if "/" in record["path"] else "."
        groups.setdefault(directory, []).append(record)

    for directory in sorted(groups):
        label = "(repository root)" if directory == "." else f"`{directory}/`"
        out.write(f"\n## {label}\n\n")
        out.write("| File | Size | SHA-256 | Tracked |\n")
        out.write("| --- | ---: | --- | :---: |\n")
        for record in groups[directory]:
            name = record["path"].rsplit("/", 1)[-1]
            tracked = "yes" if record["version_controlled"] else ":no_entry:"
            out.write(
                f"| `{name}` | {human_size(record['bytes'])} | "
                f"`{record['sha256'][:16]}…` | {tracked} |\n"
            )

    out.write(
        "\n---\n\nDigests are truncated to 16 hex characters for readability; the full\n"
        "values are in [`artifact_manifest.csv`](artifact_manifest.csv).\n"
    )
    return out.getvalue()


def render_csv(records: list[dict]) -> str:
    out = io.StringIO(newline="")
    writer = csv.writer(out, lineterminator="\n")
    writer.writerow(["path", "bytes", "sha256", "version_controlled"])
    for record in records:
        writer.writerow(
            [
                record["path"],
                record["bytes"],
                record["sha256"],
                str(record["version_controlled"]).lower(),
            ]
        )
    return out.getvalue()


def check(records: list[dict]) -> int:
    """Compare the working copy against the committed manifest.

    A clone legitimately lacks the files excluded by .gitignore, so absence is
    only an error for artifacts the manifest records as version controlled.
    Everything present must match its recorded digest, and nothing may be
    present that the manifest does not know about.
    """
    if not CSV_OUTPUT.exists():
        print(f"missing {CSV_OUTPUT.relative_to(REPO_ROOT)}", file=sys.stderr)
        return 1

    with open(CSV_OUTPUT, encoding="utf-8", newline="") as handle:
        recorded = {row["path"]: row for row in csv.DictReader(handle)}

    problems = []
    present = {record["path"]: record for record in records}

    for path, record in present.items():
        if path not in recorded:
            problems.append(f"not in manifest: {path}")
        elif recorded[path]["sha256"] != record["sha256"]:
            problems.append(f"digest changed: {path}")

    for path, row in recorded.items():
        if path not in present and row["version_controlled"] == "true":
            problems.append(f"manifested artifact missing: {path}")

    if problems:
        for problem in problems:
            print(problem, file=sys.stderr)
        print(
            "\nartifact manifest is out of date; run python scripts/make_manifest.py",
            file=sys.stderr,
        )
        return 1

    untracked_absent = len(recorded) - len(present)
    suffix = f", {untracked_absent} not in this copy by design" if untracked_absent else ""
    print(f"manifest is up to date ({len(present)} artifacts verified{suffix})")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--check",
        action="store_true",
        help="do not write; exit non-zero if the CSV manifest is out of date",
    )
    args = parser.parse_args()

    records = collect()
    if not records:
        print("No artifacts found; nothing to manifest.", file=sys.stderr)
        return 1

    csv_text = render_csv(records)

    if args.check:
        return check(records)

    MARKDOWN_OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    MARKDOWN_OUTPUT.write_text(render_markdown(records), encoding="utf-8")
    CSV_OUTPUT.write_text(csv_text, encoding="utf-8")
    print(f"wrote {MARKDOWN_OUTPUT.relative_to(REPO_ROOT)} ({len(records)} artifacts)")
    print(f"wrote {CSV_OUTPUT.relative_to(REPO_ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
