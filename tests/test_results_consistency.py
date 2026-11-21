"""Internal consistency of the recorded statistical results.

These tests do not re-run any bootstrap. They check that the frozen result
tables are self-consistent and mutually consistent, which is what a reader
auditing the paper's numbers needs to be able to rely on.
"""

from __future__ import annotations

import glob
import os

import pytest

from conftest import REPO_ROOT, read_csv

POINT_ESTIMATE_COLUMNS = (
    "mean",
    "estimate",
    "mean_difference",
    "mean_difference_in_differences",
    "mean_syn_minus_non",
)

# (file suffix, expected sources) for the three models with retrieval tables.
RETRIEVAL_SETS = [("", 100), ("_116m", 100), ("_nucel", 91)]

PAIRWISE_TRIALS_PER_SOURCE = 90  # 10 query paths x 9 candidate paths

RESULT_TABLES_WITH_CIS = sorted(
    os.path.relpath(path, REPO_ROOT).replace(os.sep, "/")
    for path in glob.glob(str(REPO_ROOT / "results" / "*.csv"))
)


def _point_estimate_column(columns):
    for name in POINT_ESTIMATE_COLUMNS:
        if name in columns:
            return name
    return None


@pytest.mark.parametrize("relative_path", RESULT_TABLES_WITH_CIS)
def test_confidence_intervals_are_ordered_and_bracket_their_estimate(relative_path):
    table = read_csv(relative_path)
    if not {"ci95_low", "ci95_high"} <= set(table.columns):
        pytest.skip(f"{relative_path} reports no confidence intervals")
    assert (table["ci95_low"] <= table["ci95_high"]).all(), "ci95_low exceeds ci95_high"
    estimate = _point_estimate_column(table.columns)
    if estimate is None:
        pytest.skip(f"{relative_path} reports no point estimate column")
    assert (table["ci95_low"] <= table[estimate]).all()
    assert (table[estimate] <= table["ci95_high"]).all()


def test_pilot_distance_table_is_complete_and_in_range():
    distances = read_csv("results/distance_results.csv")
    assert len(distances) == 1800
    assert distances["cosine_distance"].notna().all()
    assert (distances["cosine_distance"] >= 0).all()
    assert (distances["cosine_distance"] <= 2).all()
    assert set(distances["condition"].unique()) == {"synonymous", "nonsynonymous"}
    assert (distances.groupby(["condition", "depth"]).size() == 300).all()


def test_bootstrap_summary_uses_the_full_pilot_cohort():
    summary = read_csv("results/bootstrap_summary.csv")
    assert len(summary) == 6
    assert (summary["n_sources"] == 300).all()
    assert sorted(summary["depth"].unique()) == [1, 2, 3]


def test_retrieval_accuracies_are_probabilities_against_a_chance_reference():
    for relative_path in [
        "results/equivalence_retrieval_bootstrap_summary.csv",
        "results/equivalence_retrieval_bootstrap_summary_116m.csv",
        "results/equivalence_retrieval_bootstrap_summary_nucel.csv",
    ]:
        table = read_csv(relative_path)
        accuracy = table[table["metric"] == "equivalence_retrieval_accuracy"]
        assert len(accuracy) == 1
        assert 0.0 <= float(accuracy["mean"].iloc[0]) <= 1.0
        assert float(accuracy["reference"].iloc[0]) == 0.5


def test_cross_family_and_four_model_tables_report_identical_shared_values():
    """The four-model table must not have restated the three-model results."""
    numpy = pytest.importorskip("numpy")
    three_model = read_csv("results/cross_family_comparison_91_sources.csv")
    four_model = read_csv("results/final_four_model_structural_comparison_91.csv")
    merged = three_model.merge(four_model, on=["model", "metric"], suffixes=("_a", "_b"))
    assert len(merged) == 15, "expected 3 models x 5 metrics shared between tables"
    for column in ["mean", "ci95_low", "ci95_high"]:
        assert numpy.allclose(
            merged[f"{column}_a"], merged[f"{column}_b"], rtol=1e-9, atol=0.0
        ), f"{column} disagrees between the three-model and four-model tables"


def test_four_model_tables_cover_all_four_models_on_the_91_source_cohort():
    expected = {"Omni-DNA-20M", "Omni-DNA-116M", "NucEL-93M", "JEPA-DNA-NTv3-100M"}
    structural = read_csv("results/final_four_model_structural_comparison_91.csv")
    probe = read_csv("results/final_four_model_downstream_probe_comparison_91.csv")
    assert set(structural["model"].unique()) == expected
    assert set(probe["model"].unique()) == expected
    assert (structural["n_sources"] == 91).all()
    assert (probe["n_sources"] == 91).all()


@pytest.mark.parametrize("suffix,n_sources", RETRIEVAL_SETS)
def test_retrieval_chain_is_internally_consistent(suffix, n_sources):
    """Pairwise trials -> per-source summary -> bootstrap mean must agree.

    This walks the full retrieval evidence chain rather than trusting the
    summary tables: the reported accuracy is re-derived from the individual
    forced-choice trials.
    """
    numpy = pytest.importorskip("numpy")
    pairwise = read_csv(f"results/equivalence_retrieval_pairwise{suffix}.csv")
    per_source = read_csv(f"results/equivalence_retrieval_source_summary{suffix}.csv")
    bootstrap = read_csv(f"results/equivalence_retrieval_bootstrap_summary{suffix}.csv")

    assert pairwise["sequence_id"].nunique() == n_sources
    assert len(pairwise) == n_sources * PAIRWISE_TRIALS_PER_SOURCE
    assert len(per_source) == n_sources

    # Each source must contribute exactly 90 forced-choice trials.
    assert (pairwise.groupby("sequence_id").size() == PAIRWISE_TRIALS_PER_SOURCE).all()

    recorded = bootstrap[bootstrap["metric"] == "equivalence_retrieval_accuracy"]
    recorded_accuracy = float(recorded["mean"].iloc[0])

    from_trials = pairwise.groupby("sequence_id")["retrieval_correct"].mean().mean()
    from_summary = per_source["retrieval_accuracy"].mean()

    assert numpy.isclose(from_trials, recorded_accuracy, rtol=0, atol=1e-12)
    assert numpy.isclose(from_summary, recorded_accuracy, rtol=0, atol=1e-12)


def test_reported_probe_changes_come_from_the_stable_refit():
    """Provenance lock: cell 124's stable probe, not cell 123's first pass.

    The two prediction tables are easy to confuse. This recomputes the reported
    prediction-change table from each one and asserts that only the stable
    refit reproduces it, so a future reanalysis cannot silently pick up the
    superseded probe. See docs/reproducibility.md.
    """
    numpy = pytest.importorskip("numpy")
    pandas = pytest.importorskip("pandas")
    changes = read_csv("results/protein_semantic_probe_prediction_changes.csv")
    stable = read_csv("results/protein_semantic_probe_predictions_stable.csv")
    superseded = read_csv("results/protein_semantic_probe_predictions.csv")

    prediction_columns = [column for column in stable.columns if column.startswith("pred_")]
    assert len(prediction_columns) == 20, "expected 20 amino-acid prediction columns"

    def recompute_l1(predictions):
        originals = predictions[predictions["condition"] == "original"].set_index(
            ["model", "sequence_id"]
        )[prediction_columns]
        variants = predictions[predictions["condition"] != "original"]
        baseline = originals.reindex(
            pandas.MultiIndex.from_arrays([variants["model"], variants["sequence_id"]])
        ).to_numpy()
        l1 = numpy.abs(variants[prediction_columns].to_numpy() - baseline).sum(axis=1)
        return variants.assign(recomputed_l1=l1)[
            ["model", "sequence_id", "condition", "path_id", "recomputed_l1"]
        ]

    keys = ["model", "sequence_id", "condition", "path_id"]

    merged_stable = changes.merge(recompute_l1(stable), on=keys, how="left")
    assert merged_stable["recomputed_l1"].notna().all(), "stable probe is missing rows"
    assert numpy.allclose(
        merged_stable["prediction_change_l1"],
        merged_stable["recomputed_l1"],
        rtol=1e-6,
        atol=1e-12,
    ), "reported prediction changes do not reproduce from the stable refit"

    merged_superseded = changes.merge(recompute_l1(superseded), on=keys, how="left")
    assert not numpy.allclose(
        merged_superseded["prediction_change_l1"],
        merged_superseded["recomputed_l1"],
        rtol=1e-6,
        atol=1e-12,
    ), "the superseded cell-123 probe now also reproduces the reported changes"


def test_headline_retrieval_accuracies_match_the_frozen_summary_json():
    """metadata/final_core_experiment_summary.json must match results/."""
    import json

    numpy = pytest.importorskip("numpy")
    with open(REPO_ROOT / "metadata" / "final_core_experiment_summary.json") as handle:
        summary = json.load(handle)
    recorded = summary["cross_family_retrieval_accuracy"]
    table = read_csv("results/final_four_model_structural_comparison_91.csv")
    accuracy = table[table["metric"] == "equivalence_retrieval_accuracy"]
    for model, value in recorded.items():
        row = accuracy[accuracy["model"] == model]
        assert len(row) == 1, f"no retrieval row for {model}"
        assert numpy.isclose(float(row["mean"].iloc[0]), value, rtol=0, atol=1e-7)
