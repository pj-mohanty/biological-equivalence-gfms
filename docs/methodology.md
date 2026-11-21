# Methodology

Every statement on this page is traceable to an artifact in this repository or
to a cell of [`synonymous_composition.ipynb`](../synonymous_composition.ipynb).
Cell numbers are 0-indexed positions in the notebook as frozen.

---

## 1. The question

A genomic foundation model is usually probed for *robustness*: does a small
input perturbation leave the representation roughly unchanged? That framing
treats all small edits alike. Coding DNA offers a sharper test, because the
genetic code makes some edits **biologically meaningful** and others **not**.

A **synonymous** substitution changes the nucleotide sequence but leaves the
translated protein identical. A **nonsynonymous** substitution of the same size
changes the protein. If a model has internalised the structure of the genetic
code, these two classes of edit should not be treated as interchangeable: the
model should place protein-preserving variants closer together than
protein-altering ones of equal nucleotide magnitude.

This study therefore asks: **do genomic foundation models represent
synonymous coding-DNA variants as equivalent to their source sequence,
relative to edit-matched nonsynonymous controls?**

The key design property is that the two conditions are matched on everything
except biological meaning — same source sequence, same codon positions, same
number of nucleotide substitutions — so a difference in representation cannot
be attributed to edit magnitude.

---

## 2. Sequence cohorts

Human coding sequences come from the Ensembl GRCh38 CDS release recorded in
[`metadata/source_metadata.json`](../metadata/source_metadata.json), whose
SHA-256 is verifiable against the downloaded file. Full provenance and
filtering rules are in [dataset.md](dataset.md).

Three **strictly nested** cohorts are used (verified by
`tests/test_dataset_integrity.py::test_cohorts_are_strictly_nested`):

| Cohort | n | Design | Used for |
| --- | ---: | --- | --- |
| Pilot | 300 | 1 path per source, depths 1–3 | Composition drift (pre-specified pilot) |
| Structural | 100 | 10 paths per source, depth 3 | Path consistency, class geometry, retrieval |
| Cross-family | 91 | 10 paths per source, depth 3 | Matched four-model comparison |

The 91-source cohort is the subset of the structural cohort whose sequences
satisfy the context limits of *every* evaluated model family, so all four
models are compared on byte-identical inputs (cell 109).

---

## 3. Transformations

### Synonymous variants

A synonymous edit replaces one codon with a different codon encoding the same
amino acid. Each edit is applied at a codon site not previously edited on that
path, so a depth-*d* variant carries exactly *d* edited codons (decision D005).

Every synonymous variant is validated by retranslating the **full** CDS and
requiring an exact protein match (decision D004). This repository re-verifies
that claim independently, translating from a genetic-code table defined inside
the test rather than trusting the stored `translation_equal` column
(`tests/test_dataset_integrity.py::test_synonymous_variants_preserve_the_protein_exactly`).

### Matched nonsynonymous controls

For each synonymous edit, a control edit is generated at the **same codon
position** with the **same per-step nucleotide Hamming distance**, but
changing the encoded amino acid (decision D006). Decision D019 records that all
900 pilot controls are exactly edit-matched; this is re-verified here by
recomputing Hamming distances from the sequences themselves
(`test_controls_are_exactly_edit_matched_to_their_synonymous_counterparts`).

### Composition depth

Edits compose along a path: depth 1 → 2 → 3 accumulates substitutions on the
same source. Depth is the study's dose axis — if a model tracks protein
identity, synonymous and nonsynonymous drift should *diverge* as depth grows.

### Multiple paths

For the structural and cross-family cohorts, 10 independent depth-3 paths are
generated per source. All 10 synonymous endpoints encode the **same protein**,
so they form an *equivalence class*: a model that represents biological
equivalence should keep that class tight.

---

## 4. Representations

| Model | Checkpoint | Revision | Dim | Pooling |
| --- | --- | --- | ---: | --- |
| Omni-DNA-20M | `zehui127/Omni-DNA-20M` | `3b64e6a5…` | 256 | masked mean over final hidden states |
| Omni-DNA-116M | `zehui127/Omni-DNA-116M` | `8a602a83…` | 768 | masked mean over final hidden states |
| NucEL-93M | `FreakingPotato/NucEL` | `0c802982…` | 512 | masked mean over final hidden states |
| JEPA-DNA-NTv3-100M | `nvidia/NV-JEPA-DNA-NTv3` (gated) | `be526df5…` | 768 | official `infer_sequence_to_sequence_representative` |

Full revisions are in [`configs/experiment.yaml`](../configs/experiment.yaml).

JEPA-DNA is assembled from three pinned sources, which is why three different
revisions appear in the artifacts:

| Component | Repository | Revision |
| --- | --- | --- |
| JEPA checkpoint | `nvidia/NV-JEPA-DNA-NTv3` (gated) | `be526df5…` |
| NTv3 backbone **weights** | `InstaDeepAI/NTv3_100M_pre` (gated) | `5c685dca…` |
| NTv3 modelling **code** | `InstaDeepAI/ntv3_base_model` | `0ecff363…` |
| Reference implementation | `github.com/NVIDIA-Digital-Bio/JEPA-DNA` | `99e44334…` |

The backbone-weights revision is the one recorded in the `ntv3_base_revision`
column of the JEPA embedding metadata (cell 138 resolved it, cell 149 wrote
it); the modelling-code revision is the one in
[`metadata/ntv3_base_code_revision.txt`](../metadata/ntv3_base_code_revision.txt)
(cell 140). They refer to different repositories and are not alternative
values for the same identifier.

For Omni-DNA and NucEL the representation is fixed as the mean of the final
hidden states over attention-valid, **non-special** tokens — padding and
tokenizer special tokens are excluded from the pool (decision D010, cell 40).
For JEPA-DNA the official NVIDIA sequence-representative API is used rather
than a hand-rolled pooling, and the embedding metadata records it as
`final_hidden_state_masked_mean` (cell 149).

**Truncation is never permitted** (decision D008). Sequence eligibility is
determined by the model's *actual tokenizer* length against its context limit
(D003, D007), not by a nucleotide-length heuristic. Distances are cosine
distances on these pooled vectors.

---

## 5. Metrics

Let *d*(·,·) denote cosine distance between pooled embeddings.

**5.1 Composition drift** (pilot, cells 73–79). Mean *d*(original, variant) per
condition and depth, plus paired depth contrasts and a **difference-in-
differences**: does the synonymous–nonsynonymous gap *grow* with depth? This
is the pre-specified test of synonymous-specific acceleration.

**5.2 Multiple-path endpoint dispersion** (cell 90). Within a source, the mean
pairwise distance among the 10 depth-3 endpoints, computed separately for each
condition, then differenced as `syn − non`. A model encoding equivalence
should give a **negative** value: the protein-preserving class is tighter.

**5.3 Equivalence-class geometry** (cell 91). Two margins, both expressed as
`non − syn` so that **positive** favours equivalence:
`original_margin` compares distances from the original to class members, and
`pairwise_margin` compares within-class member-to-member distances.

**5.4 Equivalence retrieval** (cell 93). For each source and each of the 10
synonymous depth-3 endpoints used as a query, and for each of the 9 *other*
paths, the query is compared against that path's synonymous endpoint and its
nonsynonymous endpoint. The trial is scored **correct** when the synonymous
candidate is closer. That is 90 forced-choice trials per source. **Chance is
0.5** — the reference value recorded in every retrieval result table. This is
the most interpretable single number in the study.

**5.5 Downstream protein-semantic probe** (cells 121–126, 151–153). A Ridge
regression probe maps embeddings to the 20-dimensional amino-acid composition
of the translated CDS. Probes are fitted on **original sequences only**, with
5-fold outer cross-validation split at the **source** level and an inner
4-fold search over the regularisation strength. Transformed variants are used
only at prediction time, to measure how much each condition perturbs the
probe's output (`non − syn`, positive favours equivalence). A companion
metric, `nonsynonymous_target_change_alignment`, measures how well the
predicted change aligns with the actual change in amino-acid composition.

The reported probe is the **stable refit** of cells 124 (Omni-DNA, NucEL) and
152 (JEPA-DNA): `Pipeline(StandardScaler, Ridge(solver="svd"))` on float64
embeddings, searching α ∈ {1e-2, 1e-1, 1, 10, 100, 1e3, 1e4, 1e5, 1e6, 1e7}.

> **Why the first-pass probe was superseded.** Cell 123 searched
> α ∈ {1e-4 … 1e2}, and **all 15 folds selected α = 100.0 — the maximum of
> that grid**, so the search was saturated at its boundary and the chosen
> regularisation was not identified by the data. Cell 124 refit with the wider
> grid above; selected α then falls in the interior (100.0 and 1000.0, see
> [`metadata/protein_semantic_probe_hyperparameters_stable.csv`](../metadata/protein_semantic_probe_hyperparameters_stable.csv)).
> The superseded predictions remain in the repository for transparency but
> underlie no reported number; see [results.md](results.md) §3 and
> [dataset.md](dataset.md).

---

## 6. Statistical treatment

The statistical unit is the **source CDS**, never the individual variant: all
10 paths and 3 depths derived from one CDS are correlated, so pooling them as
independent observations would understate uncertainty. Every reported interval
is a **percentile bootstrap over source sequences with 10,000 resamples**
(decisions recorded in `metadata/pilot_design.json`), and comparisons between
conditions are **paired within source**.

Reported alongside each interval is `fraction_positive` (or
`fraction_above_reference`) — the share of sources whose individual estimate
falls on the equivalence-supporting side. It is a useful consistency check:
a mean driven by a handful of sources shows up here.

No p-value-based inference is used for the primary claims; intervals and the
chance reference carry the conclusions. The one exception is the
edit-distance confound diagnostic (cell 75), which reports Spearman
correlations with p-values in
[`results/edit_distance_correlations.csv`](../results/edit_distance_correlations.csv).

---

## 7. Pre-specification and deviations

The pilot was labelled `PRE-SPECIFIED PILOT` and its design frozen in
[`metadata/pilot_design.json`](../metadata/pilot_design.json) before the full
distance analysis: N=300, seed 42, depths 1–3, cosine distance, 10,000
source-level bootstrap resamples (decision D016).

[`logs/decision_log.txt`](../logs/decision_log.txt) records 21 numbered
decisions, including ones that constrain interpretation rather than flatter
it — D012/D013 mark the smoke-test distances as diagnostic only, and D021
records the difference-in-differences null as a finding.

Analyses beyond the pilot (multiple paths, class geometry, retrieval, the
downstream probe, and the three replication models) are **extensions**, not
pre-registered tests, and are reported as such in [results.md](results.md).
