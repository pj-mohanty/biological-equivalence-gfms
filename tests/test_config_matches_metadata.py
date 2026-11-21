"""configs/experiment.yaml must not drift from the frozen metadata it restates.

The config file is a convenience view over metadata/*.json. These tests make
that relationship enforceable rather than aspirational.
"""

from __future__ import annotations

import json

import pytest

from conftest import REPO_ROOT, read_csv

yaml = pytest.importorskip("yaml")


def _load_json(name):
    with open(REPO_ROOT / "metadata" / name, encoding="utf-8") as handle:
        return json.load(handle)


@pytest.fixture(scope="module")
def config():
    with open(REPO_ROOT / "configs" / "experiment.yaml", encoding="utf-8") as handle:
        return yaml.safe_load(handle)


@pytest.fixture(scope="module")
def experiment_metadata():
    return _load_json("experiment_metadata.json")


@pytest.fixture(scope="module")
def pilot_design():
    return _load_json("pilot_design.json")


@pytest.fixture(scope="module")
def source_metadata():
    return _load_json("source_metadata.json")


def test_reproducibility_block_matches_pilot_design(config, pilot_design):
    assert config["reproducibility"]["seed"] == pilot_design["seed"]
    assert config["reproducibility"]["bootstrap_resamples"] == pilot_design["bootstrap_resamples"]
    assert config["reproducibility"]["bootstrap_unit"] == pilot_design["bootstrap_unit"]
    assert config["study"]["analysis_label"] == pilot_design["analysis_label"]


def test_pilot_cohort_block_matches_pilot_design(config, pilot_design):
    pilot = config["cohorts"]["pilot_300"]
    assert pilot["n_sources"] == pilot_design["n_source_sequences"]
    assert pilot["composition_depths"] == pilot_design["composition_depths"]
    assert pilot["one_cds_per_gene"] == pilot_design["one_cds_per_gene"]
    assert pilot["minimum_cds_nt_length"] == pilot_design["minimum_cds_nt_length"]
    assert (
        pilot["maximum_original_omnidna_token_length"]
        == pilot_design["maximum_original_omnidna_token_length"]
    )


def test_data_source_block_matches_source_metadata(config, source_metadata):
    data_source = config["data_source"]
    assert data_source["database"] == source_metadata["source"]
    assert data_source["organism"] == source_metadata["organism"]
    assert data_source["assembly"] == source_metadata["assembly"]
    assert data_source["file_name"] == source_metadata["file_name"]
    assert data_source["download_url"] == source_metadata["download_url"]
    assert data_source["sha256"] == source_metadata["sha256"]


def test_primary_model_block_matches_experiment_metadata(config, experiment_metadata):
    primary = next(model for model in config["models"] if model["name"] == "Omni-DNA-20M")
    assert primary["hf_id"] == experiment_metadata["model_id"]
    assert primary["revision"] == experiment_metadata["model_commit_hash"]
    assert primary["model_class"] == experiment_metadata["model_class"]
    assert primary["embedding_dimension"] == experiment_metadata["embedding_dimension"]
    assert primary["context_tokens"] == experiment_metadata["model_context_tokens"]
    assert config["representation"]["primary_distance"] == experiment_metadata["primary_distance"]


def test_environment_block_matches_experiment_metadata(config, experiment_metadata):
    environment = config["environment_as_recorded"]
    assert environment["python"] == experiment_metadata["python_version"]
    assert environment["platform"] == experiment_metadata["platform"]
    assert environment["torch"] == experiment_metadata["torch_version"]
    assert environment["transformers"] == experiment_metadata["transformers_version"]
    assert environment["tokenizers"] == experiment_metadata["tokenizers_version"]
    assert environment["numpy"] == experiment_metadata["numpy_version"]
    assert environment["pandas"] == experiment_metadata["pandas_version"]
    assert environment["gpu"] == experiment_metadata["gpu_name"]


def test_model_checkpoints_match_the_frozen_core_experiment_summary(config):
    summary = _load_json("final_core_experiment_summary.json")
    by_name = {model["name"]: model for model in config["models"]}
    for name, recorded in summary["models"].items():
        assert by_name[name]["hf_id"] == recorded["model_id"]
        if "revision" in recorded:
            assert by_name[name]["revision"] == recorded["revision"]


def test_jepa_provenance_matches_the_recorded_commit_file(config):
    recorded = {}
    path = REPO_ROOT / "metadata" / "jepa_dna_official_repo_commit.txt"
    with open(path, encoding="utf-8") as handle:
        for line in handle:
            if "=" in line:
                key, value = line.strip().split("=", 1)
                recorded[key] = value
    jepa = next(model for model in config["models"] if model["name"] == "JEPA-DNA-NTv3-100M")
    assert jepa["hf_id"] == recorded["hf_model"]
    assert jepa["revision"] == recorded["hf_revision"]
    assert jepa["implementation_commit"] == recorded["commit"]
    assert jepa["implementation_repo"] == recorded["repository"]


def test_ntv3_code_revision_matches_the_recorded_snapshot_file(config):
    """The NTv3 *code* repository, as recorded by notebook cell 140."""
    recorded = {}
    path = REPO_ROOT / "metadata" / "ntv3_base_code_revision.txt"
    with open(path, encoding="utf-8") as handle:
        for line in handle:
            if "=" in line:
                key, value = line.strip().split("=", 1)
                recorded[key] = value
    jepa = next(model for model in config["models"] if model["name"] == "JEPA-DNA-NTv3-100M")
    assert jepa["ntv3_code_repo"] == recorded["repo"]
    assert jepa["ntv3_code_revision"] == recorded["revision"]
    # The code revision must not be confused with the backbone-weights revision.
    assert jepa["ntv3_code_revision"] != jepa["ntv3_base_weights_revision"]


def test_ntv3_base_weights_revision_matches_the_jepa_embedding_metadata(config):
    """The NTv3 *weights* repository, as written into the embedding metadata."""
    metadata = read_csv(
        "embeddings/jepa_dna_ntv3_100m_cross_family_embedding_metadata_91.csv",
        usecols=["ntv3_base_revision"],
    )
    recorded = set(metadata["ntv3_base_revision"].unique())
    assert len(recorded) == 1, "embedding metadata records more than one NTv3 base revision"
    jepa = next(model for model in config["models"] if model["name"] == "JEPA-DNA-NTv3-100M")
    assert jepa["ntv3_base_weights_revision"] == recorded.pop()


def test_reported_probe_grid_is_the_stable_refit(config):
    """The documented alpha grid must be the one behind the reported numbers.

    The superseded first-pass grid saturated at its maximum; recording it as
    the reported configuration would misdescribe the results.
    """
    probe = config["downstream_probe"]
    assert max(probe["alpha_grid"]) > 100.0, "reported grid must extend past the superseded maximum"
    superseded = probe["superseded_probe"]
    assert max(superseded["alpha_grid"]) == 100.0

    selected = read_csv("metadata/protein_semantic_probe_hyperparameters_stable.csv")
    assert set(selected["best_alpha"]) <= set(probe["alpha_grid"])
    # Interior selection: the refit is no longer pinned to its grid boundary.
    assert selected["best_alpha"].max() < max(probe["alpha_grid"])

    saturated = read_csv("metadata/protein_semantic_probe_hyperparameters.csv")
    assert (saturated["best_alpha"] == max(superseded["alpha_grid"])).all(), (
        "the superseded probe is documented as boundary-saturated; it no longer is"
    )


def test_declared_cohort_sizes_match_the_actual_source_tables(config):
    for cohort_key in ["pilot_300", "structural_100", "cross_family_91"]:
        cohort = config["cohorts"][cohort_key]
        table = read_csv(cohort["source_table"])
        assert len(table) == cohort["n_sources"], f"{cohort_key} size mismatch"


def test_declared_embedding_dimensions_match_the_saved_tensors(config):
    torch = pytest.importorskip("torch", reason="torch not installed; .pt checks skipped")
    tensors = {
        "Omni-DNA-20M": "embeddings/omnidna20m_structural_embeddings.pt",
        "Omni-DNA-116M": "embeddings/omnidna116m_structural_embeddings.pt",
        "NucEL-93M": "embeddings/nucel_cross_family_embeddings_91.pt",
        "JEPA-DNA-NTv3-100M": "embeddings/jepa_dna_ntv3_100m_cross_family_embeddings_91.pt",
    }
    by_name = {model["name"]: model for model in config["models"]}
    for name, relative_path in tensors.items():
        path = REPO_ROOT / relative_path
        if not path.exists():
            pytest.skip(f"artifact not present in this checkout: {relative_path}")
        tensor = torch.load(path, map_location="cpu", weights_only=True)
        assert tensor.shape[1] == by_name[name]["embedding_dimension"], name
