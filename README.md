# Person Re-Identification Keyword Co-occurrence Review

Supplementary materials for **Person Re-Identification: A Longitudinal Keyword Co-Occurrence Graph-Based Review of Its Evolution Toward Open-World Applications**, by Edouard Bengono Essola and Makoto Tsukai.

The materials support the analysis of author-keyword co-occurrence in the 2015-2024 person Re-ID literature. They provide the data behind the article's figures and tables, detailed numerical results, saved community memberships and reproducibility scripts.

## Start here

- **Read the supporting methods and tables:** [Supplementary material](supplementary/README.md).
- **Inspect a result:** [Scientific evidence index](reproducibility/evidence_index.csv).
- **Check a figure:** [Article figures and captions](manuscript_figures/) and [rendering sources](manuscript_figures/source/).
- **Verify the frozen data and results:** [Reproduction guide](reproducibility/README.md).
- **Inspect the corpus-coverage audit:** [OpenAlex reference data](data/openalex/).

## Repository contents

| Directory | Contents |
|---|---|
| `manuscript_figures/` | The seven article figures, captions, exact vector files and rendering sources |
| `article_tables/` | Machine-readable versions of the tables retained in the article |
| `supplementary/` | Detailed methods, additional tables and an index of Supplementary Tables S1-S15 |
| `data/` | Derived record incidence, expression mappings, frozen graph inputs and the OpenAlex coverage audit |
| `results/` | Saved partitions, numerical comparisons, prevalence, temporal correspondence and projection provenance |
| `src/` | Portable verification, detector-replay and document-projection scripts |
| `reproducibility/` | Protocols, software provenance, scientific evidence index and file checksums |
| `archive/` | Preserved source implementations and historical material, identified separately from current outputs |

## Analytical corpus and current scope

The analytical corpus contains **2,333 records**, including **2,260 with usable normalized author keywords**. Vocabulary is derived exclusively from author keywords. Titles, abstracts and Keywords Plus do not contribute network nodes or edges. The public incidence file contains derived representations and record identifiers, rather than raw WoS exports.

There are five nonoverlapping two-year cross-sections and five cumulative windows. The current cumulative 2015-2022 input contains **1,499 records**, including **1,439 with usable keywords**. It restores the 254 records from 2015-2018 that were absent from the older input carrying that label. Current graph inputs, numerical tables and reference memberships use this corrected scope. Historical source material is kept separately for provenance.

The independent OpenAlex audit uses a screened reference set of **4,665 publications**: 2,450 journal articles/reviews and 2,215 conference papers. Of these, 1,869 match the analytical WoS corpus. The resulting proportion describes relative recall against that defined reference set, not recall for all relevant Re-ID research. The retrieval list, eligibility decisions, matches and search-page manifest are provided in [`data/openalex/`](data/openalex/).

## Representations and community levels

- **T**: the historical normalized token representation.
- **N**: the same normalized stems retained together as an atomic keyword expression.
- **P**: complete source keyword expressions, with case and whitespace harmonized.

**L0** is the first distinct partition returned by an implementation; **L1** is the next, when available. **FINAL** is the actual last returned partition and may therefore be L0, L1 or a later level. An unavailable L1 is not replaced by FINAL. Additional hierarchy levels aggregate existing communities; their presence does not by itself identify additional research themes.

Under **filter-and-suppress**, detection uses the retained graph. Under **filter-and-hide**, detection uses the full graph and filtering changes only what is displayed. Several display masks can therefore refer to the same saved detection output. Saved-output counts are not independent bibliographic sample sizes.

## Quick verification

From the repository root, using Python:

```text
python src/verify_materials.py --check-partitions
python src/reproduce_document_ari.py
```

The first command checks file integrity, reconstructs all 30 full T/N/P graphs from the published incidence data, checks the corrected cumulative counts and verifies the saved hierarchies. The second recalculates the 2023-2024 full-network L1 publication and source-expression agreement for both algorithms and compares it with the saved numerical results. Neither command reruns community detection.

The [reproduction guide](reproducibility/README.md) explains the complete detector replay, other settings, optional label exports and the recorded environment.

## Provenance and limits

The saved analyses use Louvain and Leiden, seeds 1000-1029, and final-cutoff multipliers 0.4, 0.6, 0.8, 1, 1.2, 1.4 and 1.6. The initial node/edge selection rules remain fixed. The original Sci2 random seed and complete historical WoS search history were not recovered. Replaying frozen graph inputs is therefore distinct from reconstructing that unavailable search history.

File checksums are recorded in [`reproducibility/SHA256SUMS.json`](reproducibility/SHA256SUMS.json). The accompanying article and its associated repository version should be used together. Third-party code retains its original licence in [`src/vendor/`](src/vendor/).

## Citation

Please cite the associated article when using these materials. Repository citation metadata are available in [`CITATION.cff`](CITATION.cff).
