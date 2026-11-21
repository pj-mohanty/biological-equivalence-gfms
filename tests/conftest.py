"""Shared fixtures and helpers for artifact validation tests.

These tests validate artifacts that are already present in the repository.
They never download models, never use a GPU, and never write to any existing
file. Any test whose inputs are missing is skipped rather than failed, so the
suite stays green on a clone that excludes the large regenerable files.
"""

from __future__ import annotations

from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]

# The standard nuclear genetic code, written out here so that translation
# checks are independent of any table stored with the data.
STANDARD_GENETIC_CODE = {
    "TTT": "F", "TTC": "F", "TTA": "L", "TTG": "L",
    "CTT": "L", "CTC": "L", "CTA": "L", "CTG": "L",
    "ATT": "I", "ATC": "I", "ATA": "I", "ATG": "M",
    "GTT": "V", "GTC": "V", "GTA": "V", "GTG": "V",
    "TCT": "S", "TCC": "S", "TCA": "S", "TCG": "S",
    "CCT": "P", "CCC": "P", "CCA": "P", "CCG": "P",
    "ACT": "T", "ACC": "T", "ACA": "T", "ACG": "T",
    "GCT": "A", "GCC": "A", "GCA": "A", "GCG": "A",
    "TAT": "Y", "TAC": "Y", "TAA": "*", "TAG": "*",
    "CAT": "H", "CAC": "H", "CAA": "Q", "CAG": "Q",
    "AAT": "N", "AAC": "N", "AAA": "K", "AAG": "K",
    "GAT": "D", "GAC": "D", "GAA": "E", "GAG": "E",
    "TGT": "C", "TGC": "C", "TGA": "*", "TGG": "W",
    "CGT": "R", "CGC": "R", "CGA": "R", "CGG": "R",
    "AGT": "S", "AGC": "S", "AGA": "R", "AGG": "R",
    "GGT": "G", "GGC": "G", "GGA": "G", "GGG": "G",
}


def translate(sequence: str) -> str:
    """Translate a CDS with the standard nuclear genetic code."""
    return "".join(
        STANDARD_GENETIC_CODE[sequence[i : i + 3]] for i in range(0, len(sequence), 3)
    )


def hamming(a: str, b: str) -> int:
    """Number of differing positions between two equal-length strings."""
    assert len(a) == len(b), "hamming() requires equal-length sequences"
    return sum(x != y for x, y in zip(a, b, strict=True))


def artifact(relative_path: str) -> Path:
    """Resolve an artifact path, skipping the test if it is not present."""
    path = REPO_ROOT / relative_path
    if not path.exists():
        pytest.skip(f"artifact not present in this checkout: {relative_path}")
    return path


def read_csv(relative_path: str, **kwargs):
    pd = pytest.importorskip("pandas")
    return pd.read_csv(artifact(relative_path), **kwargs)
