#!/usr/bin/env python3
"""Verify the integrity and provenance of the artifacts in this repository.

Read-only. Nothing is downloaded, no model is loaded, no GPU is used, and no
file is written. Intended for anyone who has obtained a copy of this
repository and wants to confirm that the artifacts are the ones the paper was
written from.

Checks performed:

  1. The frozen notebook matches its recorded SHA-256.
  2. The Ensembl source FASTA matches the SHA-256 in metadata/source_metadata.json
     (skipped if the FASTA is absent; it is excluded from version control).
  3. Every artifact listed in docs/artifact_manifest.csv is present and has the
     recorded digest (skipped if the manifest has not been generated).
  4. Expected artifact tables and embedding tensors are present.

Usage:
    python scripts/verify_artifacts.py
    python scripts/verify_artifacts.py --quick   # skip digest recomputation
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]

NOTEBOOK = "synonymous_composition.ipynb"
NOTEBOOK_SHA256 = "660a5f37c539a01aba356e5f8f3b109276f2b0716f8eb7e203105e78d41f6334"

EXPECTED_ARTIFACTS = [
    "data/processed/original_sequences.csv",
    "data/processed/synonymous_variants.csv",
    "data/processed/nonsynonymous_controls.csv",
    "data/processed/structural_extension_sources.csv",
    "data/processed/structural_synonymous_variants.csv",
    "data/processed/structural_nonsynonymous_controls.csv",
    "data/processed/cross_family_sources_91.csv",
    "data/processed/cross_family_synonymous_variants_91.csv",
    "data/processed/cross_family_nonsynonymous_controls_91.csv",
    "data/processed/cross_family_embedding_inputs_91.csv",
    "embeddings/omnidna20m_pilot_embeddings.pt",
    "embeddings/omnidna20m_structural_embeddings.pt",
    "embeddings/omnidna116m_structural_embeddings.pt",
    "embeddings/nucel_cross_family_embeddings_91.pt",
    "embeddings/jepa_dna_ntv3_100m_cross_family_embeddings_91.pt",
    "results/distance_results.csv",
    "results/bootstrap_summary.csv",
    "results/final_four_model_structural_comparison_91.csv",
    "results/final_four_model_downstream_probe_comparison_91.csv",
    "metadata/experiment_metadata.json",
    "metadata/pilot_design.json",
    "metadata/source_metadata.json",
    "logs/decision_log.txt",
]

PASS = "PASS"
FAIL = "FAIL"
SKIP = "SKIP"


class Report:
    def __init__(self) -> None:
        self.failures = 0
        self.skips = 0

    def record(self, status: str, message: str) -> None:
        if status == FAIL:
            self.failures += 1
        elif status == SKIP:
            self.skips += 1
        print(f"[{status}] {message}")


def sha256_of(path: Path) -> str:
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def check_notebook(report: Report) -> None:
    path = REPO_ROOT / NOTEBOOK
    if not path.exists():
        report.record(FAIL, f"{NOTEBOOK} is missing")
        return
    digest = sha256_of(path)
    if digest == NOTEBOOK_SHA256:
        report.record(PASS, f"{NOTEBOOK} matches its recorded SHA-256")
    else:
        report.record(FAIL, f"{NOTEBOOK} digest is {digest}, expected {NOTEBOOK_SHA256}")


def check_source_fasta(report: Report) -> None:
    metadata_path = REPO_ROOT / "metadata" / "source_metadata.json"
    if not metadata_path.exists():
        report.record(SKIP, "metadata/source_metadata.json not found")
        return
    with open(metadata_path, encoding="utf-8") as handle:
        metadata = json.load(handle)
    fasta = REPO_ROOT / "data" / "raw" / metadata["file_name"]
    if not fasta.exists():
        report.record(
            SKIP,
            f"data/raw/{metadata['file_name']} not present "
            "(excluded from version control; download from Ensembl to verify)",
        )
        return
    digest = sha256_of(fasta)
    if digest == metadata["sha256"]:
        report.record(PASS, f"{metadata['file_name']} matches the recorded Ensembl SHA-256")
    else:
        report.record(
            FAIL,
            f"{metadata['file_name']} digest is {digest}, expected {metadata['sha256']}",
        )


def check_expected_artifacts(report: Report) -> None:
    missing = [name for name in EXPECTED_ARTIFACTS if not (REPO_ROOT / name).exists()]
    if missing:
        for name in missing:
            report.record(FAIL, f"expected artifact missing: {name}")
    else:
        report.record(PASS, f"all {len(EXPECTED_ARTIFACTS)} expected core artifacts are present")


def check_manifest(report: Report, quick: bool) -> None:
    manifest_path = REPO_ROOT / "docs" / "artifact_manifest.csv"
    if not manifest_path.exists():
        report.record(SKIP, "docs/artifact_manifest.csv not generated yet")
        return
    if quick:
        report.record(SKIP, "manifest digest verification skipped (--quick)")
        return

    checked = 0
    absent = 0
    with open(manifest_path, encoding="utf-8", newline="") as handle:
        for row in csv.DictReader(handle):
            path = REPO_ROOT / row["path"]
            if not path.exists():
                if row["version_controlled"] == "false":
                    absent += 1
                    continue
                report.record(FAIL, f"manifested artifact missing: {row['path']}")
                continue
            if sha256_of(path) != row["sha256"]:
                report.record(FAIL, f"digest mismatch: {row['path']}")
                continue
            checked += 1
    report.record(PASS, f"{checked} manifested artifacts match their recorded digests")
    if absent:
        report.record(
            SKIP,
            f"{absent} manifested artifacts are not in this copy "
            "(excluded from version control by design)",
        )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--quick",
        action="store_true",
        help="skip recomputing digests for the full manifest",
    )
    args = parser.parse_args()

    print(f"Verifying repository at {REPO_ROOT}\n")
    report = Report()
    check_notebook(report)
    check_source_fasta(report)
    check_expected_artifacts(report)
    check_manifest(report, quick=args.quick)

    print()
    if report.failures:
        print(f"{report.failures} check(s) FAILED, {report.skips} skipped.")
        return 1
    print(f"All checks passed ({report.skips} skipped).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
