"""Independent re-derivation of the dataset's core biological guarantees.

Nothing here trusts a recorded column: translations are recomputed from the
standard genetic code and edit distances are recomputed from the sequences.
"""

from __future__ import annotations

import pytest

from conftest import hamming, read_csv, translate

PILOT_SOURCES = "data/processed/original_sequences.csv"
PILOT_SYNONYMOUS = "data/processed/synonymous_variants.csv"
PILOT_NONSYNONYMOUS = "data/processed/nonsynonymous_controls.csv"
STRUCTURAL_SOURCES = "data/processed/structural_extension_sources.csv"
CROSS_FAMILY_SOURCES = "data/processed/cross_family_sources_91.csv"


def test_pilot_cohort_shape_and_uniqueness():
    sources = read_csv(PILOT_SOURCES)
    assert len(sources) == 300
    assert not sources["sequence_id"].duplicated().any()
    # Decision D014: at most one CDS per Ensembl gene.
    assert not sources["gene_id"].duplicated().any()


def test_source_sequences_are_well_formed_cds():
    sources = read_csv(PILOT_SOURCES)
    seqs = sources["original_sequence"]
    assert seqs.str.fullmatch("[ACGT]+").all(), "non-ACGT characters in source CDS"
    assert (seqs.str.len() % 3 == 0).all(), "source CDS length is not a multiple of 3"
    assert seqs.str.startswith("ATG").all(), "source CDS does not start with ATG"
    # Decision D015: pilot requires CDS length >= 300 nt.
    assert (seqs.str.len() >= 300).all()


def test_stored_protein_translation_matches_standard_genetic_code():
    sources = read_csv(PILOT_SOURCES)
    recomputed = sources["original_sequence"].map(translate)
    assert (recomputed == sources["protein_translation"]).all()


@pytest.mark.parametrize(
    "path,expected_rows", [(PILOT_SYNONYMOUS, 900), (PILOT_NONSYNONYMOUS, 900)]
)
def test_variant_tables_have_one_row_per_source_and_depth(path, expected_rows):
    variants = read_csv(path)
    assert len(variants) == expected_rows
    assert sorted(variants["depth"].unique()) == [1, 2, 3]
    assert (variants.groupby(["sequence_id", "depth"]).size() == 1).all()


def test_synonymous_variants_preserve_the_protein_exactly():
    """Decision D004: every synonymous variant is validated by retranslation."""
    variants = read_csv(PILOT_SYNONYMOUS)
    original = variants["original_sequence"].map(translate)
    mutated = variants["variant_sequence"].map(translate)
    assert (original == mutated).all(), "a 'synonymous' variant changes the protein"
    assert variants["translation_equal"].all()


def test_nonsynonymous_controls_change_the_protein():
    variants = read_csv(PILOT_NONSYNONYMOUS)
    original = variants["original_sequence"].map(translate)
    mutated = variants["variant_sequence"].map(translate)
    assert (original != mutated).all(), "a 'nonsynonymous' control preserves the protein"
    assert not variants["translation_equal"].any()


@pytest.mark.parametrize("path", [PILOT_SYNONYMOUS, PILOT_NONSYNONYMOUS])
def test_recorded_edit_distance_matches_recomputed_hamming_distance(path):
    variants = read_csv(path)
    assert (
        variants["variant_sequence"].str.len() == variants["original_sequence"].str.len()
    ).all(), "transformations must be length-preserving"
    recomputed = [
        hamming(a, b)
        for a, b in zip(
            variants["original_sequence"], variants["variant_sequence"], strict=True
        )
    ]
    assert list(variants["nucleotide_edit_distance"]) == recomputed


def test_controls_are_exactly_edit_matched_to_their_synonymous_counterparts():
    """Decision D019: all 900 nonsynonymous observations are exactly edit-matched."""
    synonymous = read_csv(PILOT_SYNONYMOUS)
    nonsynonymous = read_csv(PILOT_NONSYNONYMOUS)
    merged = synonymous.merge(
        nonsynonymous, on=["sequence_id", "depth"], suffixes=("_syn", "_non")
    )
    assert len(merged) == 900
    assert (
        merged["nucleotide_edit_distance_syn"] == merged["nucleotide_edit_distance_non"]
    ).all()
    assert (merged["edited_codons_syn"] == merged["edited_codons_non"]).all()


def test_cohorts_are_strictly_nested():
    """91 cross-family sources subset of 100 structural sources subset of 300 pilot."""
    pilot = set(read_csv(PILOT_SOURCES)["sequence_id"])
    structural = set(read_csv(STRUCTURAL_SOURCES)["sequence_id"])
    cross_family = set(read_csv(CROSS_FAMILY_SOURCES)["sequence_id"])
    assert len(pilot) == 300 and len(structural) == 100 and len(cross_family) == 91
    assert structural <= pilot
    assert cross_family <= structural
