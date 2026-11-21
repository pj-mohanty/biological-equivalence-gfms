"""Guard: the frozen experiment notebook must not change.

synonymous_composition.ipynb is the primary record of how every artifact in
this repository was produced, including its stored outputs. It is treated as
immutable: no formatter, linter or notebook-processing tool in this repository
is permitted to rewrite it.

If this test fails, either the notebook was edited or the expected digest
below is stale. To update it after an intentional, reviewed change, recompute
the SHA-256 of the notebook and record the new value in three places: this
file, configs/experiment.yaml, and docs/repository_structure.md.
"""

from __future__ import annotations

import hashlib
import json

import pytest

from conftest import REPO_ROOT

NOTEBOOK = REPO_ROOT / "synonymous_composition.ipynb"
EXPECTED_SHA256 = "660a5f37c539a01aba356e5f8f3b109276f2b0716f8eb7e203105e78d41f6334"
EXPECTED_CELL_COUNT = 161


def test_notebook_is_present():
    assert NOTEBOOK.exists(), "the frozen experiment notebook is missing"


def test_notebook_digest_is_unchanged():
    digest = hashlib.sha256(NOTEBOOK.read_bytes()).hexdigest()
    assert digest == EXPECTED_SHA256, (
        "synonymous_composition.ipynb has changed. If this was intentional, "
        "update EXPECTED_SHA256 here, configs/experiment.yaml and "
        "docs/repository_structure.md in the same commit."
    )


def test_notebook_structure_is_intact():
    with open(NOTEBOOK, encoding="utf-8") as handle:
        notebook = json.load(handle)
    assert len(notebook["cells"]) == EXPECTED_CELL_COUNT
    # Stored outputs are part of the record; the notebook must not be stripped.
    executed = [
        cell
        for cell in notebook["cells"]
        if cell["cell_type"] == "code" and cell.get("execution_count") is not None
    ]
    assert len(executed) > 100, "code cell outputs appear to have been stripped"


def test_recorded_digest_matches_the_config():
    yaml = pytest.importorskip("yaml")
    with open(REPO_ROOT / "configs" / "experiment.yaml", encoding="utf-8") as handle:
        config = yaml.safe_load(handle)
    assert config["study"]["notebook_sha256"] == EXPECTED_SHA256
