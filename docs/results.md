# Results

Every number on this page is copied from a result table in
[`results/`](../results) and is cited with its source file. Intervals are
95% percentile bootstrap intervals over **source sequences**, 10,000
resamples. Nothing here was recomputed while writing this documentation.

**Sign conventions.** For each metric, "favours equivalence" means the model
treats protein-preserving edits as more interchangeable than edit-matched
protein-altering ones:

| Metric | Favours equivalence when |
| --- | --- |
| `equivalence_retrieval_accuracy` | **> 0.5** |
| `syn_minus_non_endpoint_dispersion` | **< 0** (synonymous class is tighter) |
| `original_margin_non_minus_syn` | **> 0** |
| `pairwise_margin_non_minus_syn` | **> 0** |
| downstream probe margin (`non − syn`) | **> 0** |

---

## 1. Headline: equivalence retrieval on the matched 91-source cohort

The most interpretable number in the study. Each source contributes 90
forced-choice trials (10 query paths × 9 candidate paths); the model is
correct when the synonymous endpoint is closer than the nonsynonymous one.
Chance is 0.5.

| Model | Retrieval accuracy | 95% CI | Reads as |
| --- | ---: | --- | --- |
| Omni-DNA-20M | 0.4957 | [0.4766, 0.5153] | indistinguishable from chance |
| Omni-DNA-116M | 0.5004 | [0.4758, 0.5258] | indistinguishable from chance |
| **NucEL-93M** | **0.5965** | **[0.5723, 0.6210]** | **above chance** |
| JEPA-DNA-NTv3-100M | 0.5243 | [0.5004, 0.5496] | lower bound at chance; inconclusive |

Source: [`results/final_four_model_structural_comparison_91.csv`](../results/final_four_model_structural_comparison_91.csv).
All four models were run on byte-identical inputs
(`data/processed/cross_family_embedding_inputs_91.csv`), so these numbers are
directly comparable.

**Interpretation.** Biological-equivalence geometry is *model-dependent, not
scale-dependent*. A 6× parameter increase within the Omni-DNA family moves
retrieval from 0.4957 to 0.5004 — both at chance — while a different
pretraining family at comparable scale reaches 0.5965. JEPA-DNA's interval
reaches down to 0.5003, so it cannot be separated from chance at this cohort
size; it should not be described as a positive result.

---

## 2. Full four-model structural comparison (n = 91)

From [`results/final_four_model_structural_comparison_91.csv`](../results/final_four_model_structural_comparison_91.csv).

| Model | Endpoint dispersion `syn − non` | Original margin `non − syn` | Pairwise margin `non − syn` |
| --- | --- | --- | --- |
| Omni-DNA-20M | +2.10e-04 [−1.08e-04, +5.10e-04] | −2.27e-04 [−3.81e-04, −7.66e-05] | −2.10e-04 [−5.14e-04, +1.12e-04] |
| Omni-DNA-116M | +1.67e-05 [+7.33e-07, +3.29e-05] | −2.12e-05 [−2.99e-05, −1.31e-05] | −1.67e-05 [−3.31e-05, −4.34e-07] |
| NucEL-93M | **−2.36e-05 [−3.89e-05, −1.08e-05]** | **+1.22e-05 [+3.23e-06, +2.37e-05]** | **+2.36e-05 [+1.08e-05, +3.89e-05]** |
| JEPA-DNA-NTv3-100M | +7.78e-04 [−2.04e-03, +3.65e-03] | +1.13e-03 [−1.28e-03, +4.27e-03] | −7.78e-04 [−3.80e-03, +2.03e-03] |

NucEL-93M is the only model whose intervals exclude zero in the
equivalence-supporting direction on all three geometry metrics. Both Omni-DNA
models land on the *opposite* side: their intervals exclude zero in the
direction of synonymous variants being **more** dispersed and **farther**
from the original than matched nonsynonymous ones. JEPA-DNA's intervals
straddle zero throughout.

> **Magnitudes are tiny.** These effects are on the order of 1e-5 to 1e-3
> cosine distance. Absolute distances also differ by roughly an order of
> magnitude across models, which is why cross-model comparison relies on the
> retrieval accuracy and on signed, within-source paired contrasts rather
> than on raw distances.

---

## 3. Downstream protein-semantic probe (n = 91)

A Ridge probe predicting 20-dimensional amino-acid composition is fitted on
original sequences only; the metric is how much more a nonsynonymous edit
perturbs the prediction than a matched synonymous edit (`non − syn`, L1).

> **Which probe these numbers come from.** The reported values derive from the
> **stable refit** (notebook cell 124 for Omni-DNA and NucEL, cell 152 for
> JEPA-DNA), which searches α ∈ {1e-2 … 1e7} in float64. The earlier probe in
> cell 123 is superseded: all 15 of its folds selected α = 100.0, the maximum
> of its narrower grid. `results/protein_semantic_probe_predictions.csv`
> (cell 123) therefore underlies **no** reported number;
> `..._predictions_stable.csv` does. This was confirmed by recomputing the
> prediction-change table from each file — see
> [reproducibility.md](reproducibility.md) — and is now asserted by
> `tests/test_results_consistency.py`.

| Model | Margin | 95% CI | Sources positive |
| --- | ---: | --- | ---: |
| Omni-DNA-20M | 2.76e-05 | [−5.60e-04, +6.30e-04] | 51.6% |
| Omni-DNA-116M | 1.02e-05 | [−6.05e-04, +6.38e-04] | 54.9% |
| **NucEL-93M** | **3.81e-03** | **[+2.90e-03, +4.86e-03]** | **92.3%** |
| JEPA-DNA-NTv3-100M | 1.68e-03 | [−2.16e-03, +5.59e-03] | 56.0% |

Source: [`results/final_four_model_downstream_probe_comparison_91.csv`](../results/final_four_model_downstream_probe_comparison_91.csv).

The `fraction_positive` column matters here: NucEL's effect holds for 92% of
individual sources, so it is not carried by a few outliers, whereas the other
models sit near the 50% coin-flip line.

A companion diagnostic,
`nonsynonymous_target_change_alignment` in
[`results/protein_semantic_probe_bootstrap_summary.csv`](../results/protein_semantic_probe_bootstrap_summary.csv),
measures how well the probe's predicted change tracks the actual change in
amino-acid composition: Omni-DNA-20M 0.187 [0.172, 0.203], Omni-DNA-116M
0.197 [0.182, 0.211], NucEL-93M 0.319 [0.297, 0.341]. All are well below 1,
so even NucEL recovers only part of the protein-level consequence.

---

## 4. Pre-specified pilot: composition drift (n = 300, Omni-DNA-20M)

From [`results/bootstrap_summary.csv`](../results/bootstrap_summary.csv).
Mean cosine distance from the original sequence:

| Depth | Synonymous | Nonsynonymous |
| ---: | --- | --- |
| 1 | 0.000862 [0.000711, 0.001022] | 0.000680 [0.000568, 0.000807] |
| 2 | 0.001702 [0.001429, 0.001996] | 0.001458 [0.001220, 0.001723] |
| 3 | 0.002372 [0.002027, 0.002742] | 0.002131 [0.001828, 0.002459] |

Representation drift grows monotonically with composition depth under **both**
conditions, and the paired depth contrasts in
[`results/bootstrap_depth_contrasts.csv`](../results/bootstrap_depth_contrasts.csv)
exclude zero for every step (e.g. synonymous depth 3 − depth 1 =
0.001510 [0.001276, 0.001770], positive for 99% of sources). The model is
clearly sensitive to the edits.

### The pre-specified test: difference-in-differences

Does the synonymous–nonsynonymous gap *grow* with depth? From
[`results/bootstrap_difference_in_differences.csv`](../results/bootstrap_difference_in_differences.csv):

| Contrast | Estimate | 95% CI |
| --- | ---: | --- |
| depth 2 − depth 1 | +6.17e-05 | [−1.03e-04, +2.19e-04] |
| depth 3 − depth 2 | −2.62e-06 | [−1.40e-04, +1.38e-04] |
| depth 3 − depth 1 | +5.91e-05 | [−1.46e-04, +2.73e-04] |

**Null.** Every interval contains zero. This is the pre-registered primary
outcome, and decision D021 records it as such: the data do not support faster
synonymous-specific drift across depth. The two conditions drift in near
parallel.

### Edit-distance confound check

[`results/edit_distance_correlations.csv`](../results/edit_distance_correlations.csv)
reports Spearman correlations between cosine distance and realised nucleotide
edit distance: pooled across depths, ρ = 0.380 (synonymous) and ρ = 0.401
(nonsynonymous), both p < 1e-31. Within a fixed depth the correlations fall to
0.02–0.14. Because the conditions are exactly edit-matched per source and
contrasts are paired within source, this shared dependence on edit magnitude
is differenced out of the condition comparisons.

---

## 5. Scale replication within Omni-DNA (n = 100)

From [`results/omnidna_scale_comparison.csv`](../results/omnidna_scale_comparison.csv).

| Metric | Omni-DNA-20M | Omni-DNA-116M |
| --- | --- | --- |
| Retrieval accuracy | 0.4973 [0.4791, 0.5159] | 0.5062 [0.4824, 0.5304] |
| Endpoint dispersion `syn − non` | +1.74e-04 [−1.13e-04, +4.56e-04] | +1.42e-05 [−8.44e-07, +2.94e-05] |
| Original margin `non − syn` | −2.03e-04 [−3.47e-04, −6.44e-05] | −1.87e-05 [−2.71e-05, −1.10e-05] |

Scaling compresses absolute distances by roughly an order of magnitude but
does not change the **sign** or the **chance-level retrieval**. The frozen
summary in
[`metadata/omnidna_scale_replication_summary.json`](../metadata/omnidna_scale_replication_summary.json)
states this conclusion as recorded at freeze time.

---

## 6. Figures

| Figure | File | Content |
| --- | --- | --- |
| 1 | [`figures/figure1_depth_vs_distance.png`](../figures/figure1_depth_vs_distance.png) | Pilot: mean cosine distance vs composition depth by condition, with bootstrap CIs and a zero baseline (cell 83) |
| 2 | [`figures/figure2_structural_geometry_20m.png`](../figures/figure2_structural_geometry_20m.png) | Omni-DNA-20M structural geometry summary (cell 96) |
| 3 | [`figures/figure3_cross_model_equivalence.png`](../figures/figure3_cross_model_equivalence.png) | Three-model matched comparison on the 91-source cohort (cell 118) |
| 4 | [`figures/figure4_four_model_clean_publication.png`](../figures/figure4_four_model_clean_publication.png) | Four-model summary, cleaned three-panel design (cell 159) |

Each figure has a vector `.pdf` beside the `.png`. Figure 1 is deliberately
drawn against a zero y-axis baseline so the small absolute magnitudes are not
visually exaggerated.

### The four figure-4 variants

All four are alternative renderings of the **same** frozen tables
(`final_four_model_structural_comparison_91.csv` and
`final_four_model_downstream_probe_comparison_91.csv`), so none of them
disagrees numerically with any other. Their generation order is established by
notebook execution counts:

| Order | Cell | ec | File | Notebook label |
| ---: | ---: | ---: | --- | --- |
| 1 | 154 | 105 | `figure4_final_four_model_comparison` | first consolidation (later overwritten) |
| 2 | 156 | 107 | `figure4_final_four_model_comparison` | the version now on disk |
| 3 | 157 | 108 | `figure4_four_model_publication` | "clean four-model summary for paper / WiML submission" |
| 4 | 158 | 109 | `figure4_four_model_forest_publication` | "V2 — polished forest-plot summary" |
| 5 | 159 | **110** | `figure4_four_model_clean_publication` | "V3 — cleaner version of the original 3-panel design" |

Cell 159 carries the highest execution count in the notebook, so
`figure4_four_model_clean_publication` is the **last generated** variant, and
it is the one shown in the README. File modification times carry no ordering
information (all artifacts share a single sync timestamp).

> **Last generated is not the same as submitted.** Which variant appears in
> the paper or on the poster is not recorded in any artifact. **TODO
> (author): confirm.** All variants are retained.

---

## 7. What this study does and does not show

**Supported by these artifacts:**

- All four models' representations move measurably under single-codon edits,
  and that movement accumulates with composition depth.
- For Omni-DNA at both scales, synonymous and nonsynonymous edits of matched
  nucleotide magnitude produce near-parallel drift; equivalence retrieval sits
  at chance; the pre-specified difference-in-differences test is null.
- Increasing Omni-DNA scale 6× does not change that conclusion.
- NucEL-93M, evaluated on the identical matched cohort, shows above-chance
  equivalence retrieval and equivalence-favouring geometry on all three
  structural metrics and on the downstream probe.
- JEPA-DNA-NTv3-100M is inconclusive on this cohort: four of five structural
  intervals straddle zero and retrieval's lower bound sits at chance.

**Not supported, and not claimed:**

- No claim that any model does or does not "understand" the genetic code.
  These are geometric probes of frozen representations, not interventions.
- No claim about *why* NucEL differs: pretraining data, objective, tokenisation
  and architecture all differ simultaneously, and this design cannot attribute
  the difference to any one of them.
- No claim of generalisation beyond human CDSs that fit a 250-token Omni-DNA
  context, at composition depths 1–3, with n ≤ 300 sources.
- No causal or functional claim about the biological consequences of
  synonymous variation.
- The non-pilot analyses are **extensions**, not pre-registered tests, and
  carry correspondingly weaker evidential status.
