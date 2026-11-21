# Dataset

Provenance, filtering, and file-by-file description of the sequence data.

---

## 1. Source

| Field | Value |
| --- | --- |
| Database | Ensembl |
| Organism | *Homo sapiens* |
| Assembly | GRCh38 |
| File | `Homo_sapiens.GRCh38.cds.all.fa.gz` |
| Size | 35.23 MB |
| SHA-256 | `f8c6731e185957e29816a8a38ce21dc61ef6c3fc4963fbb9c0cdd8ebd20f1342` |

Recorded in [`metadata/source_metadata.json`](../metadata/source_metadata.json)
and verifiable with `python scripts/verify_artifacts.py`.

> **Caution on the download URL.** The recorded URL points at Ensembl's
> `current_fasta` path, which always serves the newest release. Once Ensembl
> advances a release it will no longer return this exact file. Always check
> the SHA-256 after downloading; if it differs, you have a different Ensembl
> release and downstream cohorts will not match. See
> [reproducibility.md](reproducibility.md).

The compressed FASTA is **excluded from version control** (37 MB, freely
re-downloadable, checksum recorded).

---

## 2. Filtering

Applied in notebook cells 15–21; the governing decisions are in
[`logs/decision_log.txt`](../logs/decision_log.txt).

1. **Conventional nuclear protein-coding CDSs only**, using the standard
   genetic code (D001). Non-standard-code sequences are excluded.
2. **Exact duplicate CDS sequences removed** before sampling (D002).
3. **Tokenizer-based eligibility** (D003, D007): a sequence qualifies only if
   its *actual* Omni-DNA token length fits the 250-token context, with the
   original capped at 245 tokens to leave headroom. Truncation is never
   permitted (D008).
4. **One CDS per gene** for the pilot cohort (D014).
5. **Minimum CDS length 300 nt** for the pilot cohort (D015).

Properties re-verified in this repository rather than assumed: all source
sequences are pure ACGT, length divisible by 3, and begin with ATG
(`tests/test_dataset_integrity.py::test_source_sequences_are_well_formed_cds`),
and every stored `protein_translation` matches an independent translation
under the standard genetic code.

---

## 3. Cohorts

Strictly nested — 91 ⊂ 100 ⊂ 300 — so cross-model comparisons use identical
inputs.

| Cohort | Sources | Paths/source | Depths | Variant rows per condition |
| --- | ---: | ---: | --- | ---: |
| Pilot | 300 | 1 | 1, 2, 3 | 900 |
| Structural extension | 100 | 10 | 3 (all intermediate depths retained) | 3,000 |
| Cross-family | 91 | 10 | 3 | 2,730 |

The cross-family embedding input table contains **5,551 rows** = 91 originals
+ 2,730 synonymous + 2,730 nonsynonymous, and is the single frozen table that
NucEL and JEPA-DNA both consumed in identical row order (verified by
`tests/test_artifact_alignment.py`).

---

## 4. Files

### `data/raw/`

| File | Status |
| --- | --- |
| `Homo_sapiens.GRCh38.cds.all.fa.gz` | Not version controlled; re-download and verify SHA-256 |

### `data/processed/` — primary cohorts

| File | Rows | Description |
| --- | ---: | --- |
| `original_sequences.csv` | 300 | Frozen pilot cohort with gene/transcript identifiers, genomic coordinates, protein translation, editable-codon count, token length |
| `synonymous_variants.csv` | 900 | Pilot synonymous variants, depths 1–3 |
| `nonsynonymous_controls.csv` | 900 | Edit-matched pilot controls |
| `structural_extension_sources.csv` | 100 | Structural cohort sources |
| `structural_synonymous_variants.csv` | 3,000 | 10 paths × 3 depths × 100 sources |
| `structural_nonsynonymous_controls.csv` | 3,000 | Path-matched controls |
| `cross_family_sources_91.csv` | 91 | Cross-family cohort sources |
| `cross_family_synonymous_variants_91.csv` | 2,730 | Cross-family synonymous variants |
| `cross_family_nonsynonymous_controls_91.csv` | 2,730 | Cross-family controls |
| `cross_family_embedding_inputs_91.csv` | 5,551 | The exact table fed to every cross-family model |
| `protein_semantic_probe_targets_91.csv` | 1,911 | 20-dim amino-acid composition targets for the probe |

### `data/processed/` — diagnostics and intermediates

| File | Rows | Description |
| --- | ---: | --- |
| `smoke_source_sequences.csv` | 5 | Pipeline smoke test only |
| `smoke_synonymous_variants.csv` | — | Smoke test only |
| `smoke_nonsynonymous_controls.csv` | — | Smoke test only |
| `validated_cds_candidates.csv` | — | Full filtered CDS pool (344 MB, **not version controlled**) |
| `validated_cds_candidates_with_token_lengths.csv` | — | Same, with Omni-DNA token lengths (345 MB, **not version controlled**) |

> **Smoke-test artifacts are diagnostic only.** Decisions D012 and D013 record
> that the 5-sequence smoke set used context headroom purely to validate the
> pipeline, and that its distances must not be read as results. They are kept
> for transparency, not for analysis.

The two `validated_cds_candidates*` files are deterministic derivations of the
Ensembl FASTA (cells 21 and 48) and exceed GitHub's 100 MB per-file limit;
they are excluded from version control and regenerable.

### `metadata/`

| File | Description |
| --- | --- |
| `source_metadata.json` | Ensembl download provenance and checksum |
| `pilot_design.json` | Pre-specified pilot design, frozen before analysis |
| `experiment_metadata.json` | Model, representation, seed, library versions, GPU |
| `transformation_metadata.csv` | 1,800 rows: per-edit audit (codon index, nt position, old/new codon, old/new amino acid, step edit distance) |
| `structural_transformation_metadata.csv` | Same audit for the structural cohort |
| `decision_log.txt` → in `logs/` | 21 numbered design decisions |
| `*_manifest.csv`, `*_summary.json` | Freeze-time artifact manifests and headline summaries |
| `jepa_dna_official_repo_commit.txt`, `ntv3_base_code_revision.txt` | JEPA-DNA / NTv3 provenance |
| `protein_semantic_probe_hyperparameters_stable.csv` | Selected Ridge α per fold and model for the **reported** probe (cell 124) |
| `protein_semantic_probe_hyperparameters.csv` | Same for the **superseded** first-pass probe (cell 123) |

> **One probe is superseded.** Two prediction tables exist in `results/`:
> `protein_semantic_probe_predictions_stable.csv` (cell 124) is the basis of
> every reported downstream number, and
> `protein_semantic_probe_predictions.csv` (cell 123) is **not** — all 15 of
> its folds selected α at the maximum of its grid, so it was refit. Both are
> retained for transparency. Use the `_stable` file for any reanalysis; see
> [methodology.md](methodology.md) §5.5 and [results.md](results.md) §3.

The per-edit audit is strong enough to re-derive the transformations: for
every synonymous row the recorded `original_aa` equals `new_aa`, and for every
nonsynonymous row it does not — checked in
`tests/test_artifact_alignment.py::test_transformation_audit_log_covers_every_pilot_edit`.

---

## 5. Column conventions

Shared across variant tables:

| Column | Meaning |
| --- | --- |
| `sequence_id` | Ensembl transcript ID (e.g. `ENST00000335360.12`) |
| `path_id` | Independent composition path, 0–9 (multi-path tables only) |
| `depth` | Number of composed edits; `0` denotes the untransformed original |
| `condition` | `original`, `synonymous`, or `nonsynonymous` |
| `edited_codons` | Count of codon sites changed |
| `nucleotide_edit_distance` | Hamming distance from the original sequence |
| `fraction_sequence_changed` | `nucleotide_edit_distance / sequence_length` |
| `translation_equal` | Whether the translated protein is unchanged |
| `omnidna_token_length` | Token count under the Omni-DNA tokenizer |

---

## 6. Licensing

Sequence-derived artifacts are redistributed under CC BY 4.0
([LICENSE-DATA.md](../LICENSE-DATA.md)). Ensembl releases its data without
restriction; please credit Ensembl alongside this work when reusing them.
