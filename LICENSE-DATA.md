# Data and Artifact License

The research data and derived artifacts in this repository — specifically the
contents of `data/`, `embeddings/`, `results/`, `figures/`, `metadata/` and
`logs/` — are licensed under the
**Creative Commons Attribution 4.0 International License (CC BY 4.0)**.

The canonical legal text is published at
<https://creativecommons.org/licenses/by/4.0/legalcode>; a plain-language
summary is at <https://creativecommons.org/licenses/by/4.0/>. The full legal
text is not reproduced here in order to avoid any transcription divergence
from the canonical version.

## In brief

You are free to share and adapt these artifacts for any purpose, including
commercially, provided you give appropriate credit, link to the license, and
indicate whether changes were made.

## How to attribute

Please cite the accompanying paper (see [`CITATION.cff`](CITATION.cff)) and
link back to this repository.

## Upstream material

* **Ensembl human CDS data.** Sequences under `data/` derive from the Ensembl
  *Homo sapiens* GRCh38 CDS release recorded in
  [`metadata/source_metadata.json`](metadata/source_metadata.json). Ensembl
  releases its data without restriction; please also credit Ensembl when
  reusing sequence-derived artifacts. See [`docs/dataset.md`](docs/dataset.md).
* **Pretrained model checkpoints.** No model weights are redistributed in this
  repository. The embeddings under `embeddings/` are derived representations
  computed with the checkpoints listed in [`docs/methodology.md`](docs/methodology.md);
  each checkpoint remains subject to its own upstream license and, for
  `nvidia/NV-JEPA-DNA-NTv3`, its access conditions.
