# Reproducibility

This page states plainly what can be reproduced from this repository, what
can be reproduced only with external resources, and what cannot currently be
reproduced at all. It is deliberately specific about the limits.

Commands shown under **Tier A** were executed on this repository and their
output verified. Commands under Tiers B–D are **not verified** here, because
running them requires a GPU and model downloads that were out of scope; they
are marked as such and derived from the notebook rather than invented.

---

## Tier A — Fully reproducible, CPU-only, from this repository

No downloads, no GPU, no model weights. Runs in seconds.

```bash
pip install -r requirements-validation.txt
pytest -q                          # validates datasets, alignment, results
python scripts/verify_artifacts.py # checksums every artifact
python scripts/make_manifest.py --check
```

What this actually establishes:

- Synonymous variants preserve the translated protein exactly, re-derived from
  a genetic-code table defined inside the test suite rather than read from the
  data.
- Nonsynonymous controls change the protein and are **exactly edit-matched**
  to their synonymous counterparts, with Hamming distances recomputed from the
  sequences.
- The three cohorts are strictly nested (91 ⊂ 100 ⊂ 300).
- Every embedding tensor's shape matches its metadata table row-for-row, and
  `embedding_index` is a dense range in file order.
- Every reported confidence interval is ordered and brackets its point
  estimate; the three-model and four-model result tables agree exactly on
  their 15 shared values; the headline retrieval accuracies match the frozen
  `metadata/final_core_experiment_summary.json`.
- The **full retrieval chain** re-derives: individual forced-choice trials →
  per-source summary → bootstrap mean agree to 1e-12 for all three models
  with retrieval tables (9,000 / 9,000 / 8,190 trials).
- The reported downstream-probe changes reproduce from the **stable** probe
  predictions and not from the superseded ones, so the two cannot be confused.
- The documented probe grid is the one actually used, and the superseded grid
  is still demonstrably boundary-saturated.
- The NTv3 code and backbone-weights revisions in `configs/experiment.yaml`
  match `metadata/ntv3_base_code_revision.txt` and the JEPA embedding metadata
  respectively, and remain distinct.
- `configs/experiment.yaml` still matches the frozen `metadata/*.json` files
  it restates.
- `synonymous_composition.ipynb` matches its recorded SHA-256.

This is the layer that lets a reviewer trust the numbers in the paper without
access to a GPU.

---

## Tier B — Reproducible from saved artifacts (analysis and figures)

All statistical analyses and figures are deterministic functions of the saved
embeddings (`embeddings/*.pt`) plus the frozen input tables, with a fixed seed
of 42 and 10,000 bootstrap resamples. The embeddings **are** in this
repository, so no model inference is needed to re-derive the results.

**However, this is not currently a one-command operation**, for a specific
reason: the analysis code exists only inside
[`synonymous_composition.ipynb`](../synonymous_composition.ipynb), and every
path in it is absolute to the original Google Drive location:

```python
PROJECT_ROOT = Path("/content/drive/MyDrive/wiml_equivalence")
```

To re-run an analysis cell you would need to point `PROJECT_ROOT` at your
clone of this repository and run only the relevant cells. The notebook is
frozen and must not be edited in place
(`tests/test_notebook_untouched.py` enforces this), so do that work in a copy.

**The notebook does not run top to bottom.** This is a factual property of the
frozen record, not a caveat added for caution:

- Execution counts restart three times (cells 3–4 and 35–36 install packages
  and require a Colab runtime restart).
- The first 5-sequence smoke sample was superseded mid-notebook by a
  context-safe replacement (cells 49–57); both remain in the record.
- Cells 134–138 are an interactive Hugging Face authentication loop.
- Several cells were re-run after upstream state changed, so execution counts
  are not monotonic.

Do not describe this notebook as "run all". It is a faithful log of an
exploratory session that ends in frozen artifacts, which is why the artifacts,
not the notebook, are the reproducible object.

### Proposed extraction (not implemented)

Turning Tier B into one command would mean extracting the analysis from the
notebook into a small package, roughly:

```text
src/bioequiv/
    data.py        # cohort loading and schema validation
    transforms.py  # synonymous / matched-nonsynonymous generation
    embed.py       # model loading, pooling, batched inference  (GPU)
    metrics.py     # dispersion, class geometry, retrieval
    stats.py       # source-level paired bootstrap
    figures.py     # figure generation
```

This was deliberately **not** implemented here. Re-implementing `metrics.py`
and `stats.py` would produce code whose agreement with the published numbers
could be asserted (the embeddings are available), but `embed.py` could not be
validated at all without GPU access and the gated JEPA checkpoint — and
shipping a `src/` package whose core is unexercised would make the repository
look more reproducible than it is. If you extract it later, the acceptance
criterion is clear: the extracted pipeline must reproduce
`results/final_four_model_structural_comparison_91.csv` from
`embeddings/*.pt` to within floating-point tolerance.

---

## Tier C — Requires GPU and model downloads (embedding regeneration)

Regenerating `embeddings/*.pt` requires loading pretrained checkpoints.

| Requirement | Detail |
| --- | --- |
| GPU | NVIDIA Tesla T4 was used (16 GB). Recorded in `metadata/experiment_metadata.json`. |
| Batch size | 32 for Omni-DNA (decision D020); 16 for JEPA-DNA (cell 149); NucEL validated separately (cell 112) |
| Precision | float32 throughout |
| Determinism | seed 42, `cudnn.deterministic = True`, `cudnn.benchmark = False` (cell 6) |

Checkpoints and revisions are pinned in
[`configs/experiment.yaml`](../configs/experiment.yaml). Note that
`transformers` must be **4.48.3**: decision D009 records that 5.13.1 was
incompatible with Omni-DNA's custom model loading.

Wall-clock embedding time was not recorded in the frozen metadata, so no
runtime estimate is given here rather than a guessed one.

### Environment caveat

`requirements-experiment.txt` is a **transcription of what was recorded**, not
a tested installation recipe. Two known issues:

1. **numpy version discrepancy.** Notebook cell 3 force-installs
   `numpy==2.2.6`, but `metadata/experiment_metadata.json` records
   `numpy 2.5.2` at freeze time, after later installs changed the runtime.
   Both values are reported; neither has been silently reconciled.
2. **`ai2-olmo` version unrecorded.** Omni-DNA's custom code imports `olmo`,
   but the installed version is not captured in the frozen metadata.

---

## Tier D — Requires external access beyond a GPU

| Resource | Constraint |
| --- | --- |
| `nvidia/NV-JEPA-DNA-NTv3` | **Gated** on Hugging Face. Requires an account with access granted; the notebook performs an interactive login (cells 135–138). |
| NVIDIA JEPA-DNA implementation | Custom code from `github.com/NVIDIA-Digital-Bio/JEPA-DNA` at commit `99e44334…`, not vendored here |
| `InstaDeepAI/ntv3_base_model` | Custom NTv3 modules loaded from a pinned snapshot |
| Ensembl FASTA | The recorded URL serves Ensembl's *current* release and will not return this exact file after a release rollover. Verify the SHA-256; a mismatch means a different release. |

No model weights are redistributed in this repository.

---

## Regenerating the excluded large files

Three files are excluded from version control (see `.gitignore`):

| File | How to regenerate |
| --- | --- |
| `data/raw/Homo_sapiens.GRCh38.cds.all.fa.gz` | Download from Ensembl; verify SHA-256 against `metadata/source_metadata.json` |
| `data/processed/validated_cds_candidates.csv` | Notebook cell 21, from the FASTA |
| `data/processed/validated_cds_candidates_with_token_lengths.csv` | Notebook cell 48, adds Omni-DNA token lengths |

Nothing downstream in Tier A or Tier B depends on them: the frozen cohorts
were already sampled from them and are committed.

---

## Provenance questions — resolved

These were open in the first pass of this documentation and have since been
settled from evidence in the repository.

1. **The two NTv3 revisions are not in conflict.** They identify different
   repositories:

   | Revision | Repository | Role | Evidence |
   | --- | --- | --- | --- |
   | `5c685dca…` | `InstaDeepAI/NTv3_100M_pre` | gated backbone **weights** | cell 138 output returns this as the revision of `NTv3_100M_pre`; cell 149 writes it to the `ntv3_base_revision` column |
   | `0ecff363…` | `InstaDeepAI/ntv3_base_model` | custom modelling **code** | cell 140 resolves it; cells 142/144 outputs show the matching snapshot path |

   Both are now recorded under explicit names in `configs/experiment.yaml`.

2. **The reported probe is the stable refit (cell 124), not the first-pass
   probe (cell 123).** Established by recomputation rather than by reading the
   code: recomputing `prediction_change_l1` from each candidate prediction
   file against the stored originals reproduces
   `results/protein_semantic_probe_prediction_changes.csv` to a maximum
   absolute difference of **7.1e-16** from
   `protein_semantic_probe_predictions_stable.csv`, versus **8.4e-02** from
   `protein_semantic_probe_predictions.csv`. The chain is therefore
   cell 124 → cell 125 (changes, source stability) → cell 126 (bootstrap) →
   `results/final_four_model_downstream_probe_comparison_91.csv`.

   The first-pass probe was superseded because all 15 of its folds selected
   α = 100.0, the maximum of its grid. See [methodology.md](methodology.md) §5.5.
   `tests/test_results_consistency.py` now asserts this provenance so the two
   files cannot be confused again.

## Open provenance questions

3. **Which figure-4 variant was submitted.** Execution counts establish the
   generation order — cell 154 (ec 105) → 156 (ec 107) → 157 (ec 108) → 158
   (ec 109) → 159 (ec 110) — so `figure4_four_model_clean_publication`
   (cell 159) is the **last generated** variant, and all four render the same
   frozen tables. Which one appears in the paper or on the poster is not
   recorded in any artifact. **TODO (author).** See [results.md](results.md) §6.

4. **`ai2-olmo` version** not captured (see Tier C).

---

## Summary table

| Layer | Reproducible here? | Needs |
| --- | --- | --- |
| Artifact integrity and dataset guarantees | **Yes**, verified | Python + pandas |
| Statistical results from saved embeddings | In principle | Notebook cells with `PROJECT_ROOT` repointed |
| Embedding regeneration (Omni-DNA, NucEL) | No | GPU, pinned checkpoints, `transformers==4.48.3` |
| Embedding regeneration (JEPA-DNA) | No | GPU + gated checkpoint access + NVIDIA custom code |
| Cohort resampling from raw FASTA | No | Ensembl FASTA matching the recorded checksum |
