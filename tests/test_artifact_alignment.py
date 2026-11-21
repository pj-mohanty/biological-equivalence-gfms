"""Alignment between frozen inputs, embedding tensors and their metadata.

Row-order alignment between an embedding matrix and its metadata table is the
load-bearing assumption of every downstream analysis in this study, so it is
checked explicitly here.
"""

from __future__ import annotations

import pytest

from conftest import artifact, hamming, read_csv, translate

# (embedding tensor, metadata table, expected rows, expected dimension)
EMBEDDING_SETS = [
    (
        "embeddings/omnidna20m_pilot_embeddings.pt",
        "embeddings/omnidna20m_pilot_embedding_metadata.csv",
        2100,
        256,
    ),
    (
        "embeddings/omnidna20m_structural_embeddings.pt",
        "embeddings/omnidna20m_structural_embedding_metadata.csv",
        6100,
        256,
    ),
    (
        "embeddings/omnidna116m_structural_embeddings.pt",
        "embeddings/omnidna116m_structural_embedding_metadata.csv",
        6100,
        768,
    ),
    (
        "embeddings/nucel_cross_family_embeddings_91.pt",
        "embeddings/nucel_cross_family_embedding_metadata_91.csv",
        5551,
        512,
    ),
    (
        "embeddings/jepa_dna_ntv3_100m_cross_family_embeddings_91.pt",
        "embeddings/jepa_dna_ntv3_100m_cross_family_embedding_metadata_91.csv",
        5551,
        768,
    ),
]

STRUCTURAL_TABLES = [
    ("data/processed/structural_synonymous_variants.csv", 3000),
    ("data/processed/structural_nonsynonymous_controls.csv", 3000),
    ("data/processed/cross_family_synonymous_variants_91.csv", 2730),
    ("data/processed/cross_family_nonsynonymous_controls_91.csv", 2730),
]


@pytest.mark.parametrize("tensor_path,metadata_path,rows,_dim", EMBEDDING_SETS)
def test_embedding_metadata_row_count_and_index(tensor_path, metadata_path, rows, _dim):
    metadata = read_csv(metadata_path)
    assert len(metadata) == rows
    # embedding_index must be a dense 0..n-1 range in file order.
    assert list(metadata["embedding_index"]) == list(range(rows))


@pytest.mark.requires_torch
@pytest.mark.parametrize("tensor_path,metadata_path,rows,dim", EMBEDDING_SETS)
def test_embedding_tensor_matches_metadata(tensor_path, metadata_path, rows, dim):
    torch = pytest.importorskip("torch", reason="torch not installed; .pt checks skipped")
    tensor = torch.load(artifact(tensor_path), map_location="cpu", weights_only=True)
    assert tuple(tensor.shape) == (rows, dim)
    assert torch.isfinite(tensor).all(), "embedding tensor contains NaN or Inf"
    assert len(read_csv(metadata_path)) == tensor.shape[0]


@pytest.mark.parametrize("path,rows", STRUCTURAL_TABLES)
def test_multi_path_variant_tables_are_complete(path, rows):
    """Each source contributes 10 paths x 3 depths in the structural design."""
    variants = read_csv(path)
    assert len(variants) == rows
    per_source = variants.groupby("sequence_id").size()
    assert (per_source == 30).all()
    assert sorted(variants["path_id"].unique()) == list(range(10))
    assert sorted(variants["depth"].unique()) == [1, 2, 3]


@pytest.mark.parametrize("path,_rows", STRUCTURAL_TABLES)
def test_multi_path_transformations_respect_their_condition(path, _rows):
    variants = read_csv(path)
    original = variants["original_sequence"].map(translate)
    mutated = variants["variant_sequence"].map(translate)
    if "synonymous" in path and "nonsynonymous" not in path:
        assert (original == mutated).all()
    else:
        assert (original != mutated).all()
    recomputed = [
        hamming(a, b)
        for a, b in zip(
            variants["original_sequence"], variants["variant_sequence"], strict=True
        )
    ]
    assert list(variants["nucleotide_edit_distance"]) == recomputed


def test_cross_family_embedding_input_table_composition():
    """5551 = 91 originals + 2 conditions x 91 sources x 10 paths x 3 depths."""
    inputs = read_csv("data/processed/cross_family_embedding_inputs_91.csv")
    assert len(inputs) == 5551
    counts = inputs["condition"].value_counts().to_dict()
    assert counts == {"synonymous": 2730, "nonsynonymous": 2730, "original": 91}
    originals = inputs[inputs["condition"] == "original"]
    assert len(originals) == 91
    assert (originals["depth"] == 0).all()


def test_cross_family_embedding_metadata_agrees_across_models():
    """NucEL and JEPA embedded the identical frozen input table, in order."""
    nucel = read_csv("embeddings/nucel_cross_family_embedding_metadata_91.csv")
    jepa = read_csv("embeddings/jepa_dna_ntv3_100m_cross_family_embedding_metadata_91.csv")
    keys = ["sequence_id", "path_id", "condition", "depth"]
    assert nucel[keys].equals(jepa[keys])


def test_transformation_audit_log_covers_every_pilot_edit():
    """metadata/transformation_metadata.csv records one row per applied edit."""
    audit = read_csv("metadata/transformation_metadata.csv")
    # 300 sources x (1 + 2 + 3) edits per condition x 2 conditions = 3600 edits,
    # recorded as 1800 synonymous/nonsynonymous paired rows per the frozen file.
    assert len(audit) == 1800
    assert set(audit["condition"].unique()) <= {"synonymous", "nonsynonymous"}
    synonymous = audit[audit["condition"] == "synonymous"]
    assert (synonymous["original_aa"] == synonymous["new_aa"]).all()
    nonsynonymous = audit[audit["condition"] == "nonsynonymous"]
    assert (nonsynonymous["original_aa"] != nonsynonymous["new_aa"]).all()
