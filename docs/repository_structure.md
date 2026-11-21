# Repository Structure

```text
biological-equivalence-gfms/
├── synonymous_composition.ipynb   FROZEN experiment record (161 cells, outputs retained)
│
├── configs/
│   └── experiment.yaml            consolidated record of the experimental configuration
│
├── data/
│   ├── raw/                       Ensembl CDS FASTA (not version controlled)
│   └── processed/                 frozen cohorts, variants and matched controls
│
├── embeddings/                    pooled representations (.pt) + row-aligned metadata (.csv)
├── results/                       distances, bootstrap summaries, retrieval, probe outputs
├── figures/                       publication figures (.png + .pdf)
├── metadata/                      provenance, pre-specified design, per-edit audit, manifests
├── logs/
│   └── decision_log.txt           21 numbered design decisions (D001–D021)
│
├── docs/
│   ├── methodology.md             experimental design and metric definitions
│   ├── dataset.md                 data provenance, filtering, file-by-file description
│   ├── results.md                 every reported number, cited to its result file
│   ├── reproducibility.md         what can and cannot be reproduced, and with what
│   ├── repository_structure.md    this file
│   ├── artifact_manifest.md       generated inventory with SHA-256 digests
│   └── artifact_manifest.csv      machine-readable manifest
│
├── scripts/
│   ├── verify_artifacts.py        read-only integrity and provenance check
│   └── make_manifest.py           regenerate the artifact manifest
│
├── tests/                         CPU-only validation suite (no model downloads)
├── .github/workflows/validate.yml CI: tests, manifest check, notebook digest guard
│
├── README.md
├── CITATION.cff
├── LICENSE                        MIT (code)
├── LICENSE-DATA.md                CC BY 4.0 (data and derived artifacts)
├── requirements-experiment.txt    environment that produced the artifacts (a record)
├── requirements-validation.txt    CPU environment for the validation suite
├── pyproject.toml                 ruff/pytest config, scoped to tests/ and scripts/
├── .gitignore
└── .gitattributes
```

---

## The frozen notebook

`synonymous_composition.ipynb` is the primary record of how every artifact
here was produced. It is treated as **immutable**:

| Property | Value |
| --- | --- |
| SHA-256 | `660a5f37c539a01aba356e5f8f3b109276f2b0716f8eb7e203105e78d41f6334` |
| Cells | 161 |
| Outputs | retained (not stripped) |

`tests/test_notebook_untouched.py` fails if the digest changes, and
`pyproject.toml` excludes `*.ipynb` from every formatter and linter configured
in this repository. No tool here rewrites the notebook. If you need to change
it, do so deliberately and update the digest in the three places named in that
test's docstring.

### Notebook sections

| Cells | Stage |
| --- | --- |
| 0–21 | Environment, reproducibility controls, Ensembl download, CDS filtering |
| 22–59 | Transformation smoke tests (diagnostic only, D012/D013) |
| 30–46 | Omni-DNA-20M loading, representation definition, determinism checks |
| 60–84 | Pre-specified 300-source pilot: cohort freeze, embeddings, distances, bootstrap, Figure 1 |
| 85–97 | Structural extension (100 sources × 10 paths): path consistency, class geometry, retrieval, Figure 2 |
| 98–104 | Omni-DNA-116M scale replication |
| 105–119 | NucEL-93M cross-family replication, 91-source cohort freeze, Figure 3 |
| 120–126 | Downstream protein-semantic Ridge probe |
| 127–153 | JEPA-DNA-NTv3-100M: checkpoint pinning, loading, embedding, analyses |
| 154–159 | Four-model consolidation and publication figures |

---

## Which files hold the headline numbers

| Claim | File |
| --- | --- |
| Four-model equivalence retrieval and geometry | `results/final_four_model_structural_comparison_91.csv` |
| Four-model downstream probe comparison | `results/final_four_model_downstream_probe_comparison_91.csv` |
| Pre-specified pilot drift and difference-in-differences | `results/bootstrap_summary.csv`, `results/bootstrap_difference_in_differences.csv` |
| Omni-DNA scale replication | `results/omnidna_scale_comparison.csv` |
| Frozen headline summary | `metadata/final_core_experiment_summary.json` |

---

## Artifact traceability

The chain from input to claim, for the four-model comparison:

```text
metadata/source_metadata.json                     (Ensembl release + SHA-256)
  └─> data/processed/validated_cds_candidates*.csv       (not tracked; regenerable)
        └─> data/processed/original_sequences.csv              300 pilot sources
              └─> data/processed/structural_extension_sources.csv    100 sources
                    └─> data/processed/cross_family_sources_91.csv    91 sources
                          └─> data/processed/cross_family_embedding_inputs_91.csv   5,551 rows
                                ├─> embeddings/omnidna20m_structural_embeddings.pt
                                ├─> embeddings/omnidna116m_structural_embeddings.pt
                                ├─> embeddings/nucel_cross_family_embeddings_91.pt
                                └─> embeddings/jepa_dna_ntv3_100m_cross_family_embeddings_91.pt
                                      └─> results/final_four_model_structural_comparison_91.csv
                                            └─> figures/figure4_*.png|pdf
```

Each embedding tensor is paired with a metadata CSV in the same row order;
that alignment is the load-bearing assumption of every downstream analysis and
is tested explicitly in `tests/test_artifact_alignment.py`.

Per-file sizes and SHA-256 digests for all 111 artifacts are in
[`artifact_manifest.md`](artifact_manifest.md).

---

## Version control policy

Tracked: all frozen cohorts, embeddings, results, figures, metadata, logs,
documentation and code.

Not tracked (see `.gitignore`, with reasons):

| File | Size | Why |
| --- | ---: | --- |
| `data/processed/validated_cds_candidates_with_token_lengths.csv` | 345 MB | Exceeds GitHub's 100 MB limit; regenerable (cell 48) |
| `data/processed/validated_cds_candidates.csv` | 344 MB | Exceeds GitHub's 100 MB limit; regenerable (cell 21) |
| `data/raw/*.fa.gz` | 37 MB | Re-downloadable from Ensembl; SHA-256 recorded |

This keeps the repository at roughly 98 MB without Git LFS while preserving
every artifact a reader needs to check the paper's numbers.
`.gitattributes` disables end-of-line normalisation for `.csv`, `.json`,
`.txt` and `.ipynb` files so that checkout and commit cannot alter a byte of
any recorded artifact.
