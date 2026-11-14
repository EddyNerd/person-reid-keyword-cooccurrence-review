# Supplementary material

The [supplementary methods and tables](Supplementary_methods_and_tables.pdf) provide a continuous reading version of the supporting material. The CSV files below provide the corresponding numerical data and memberships.

## Table S1

[Selected-publication coverage check](tables/Table_S1.csv). This small selected sample documents inclusion or omission of specific publication versions. It is distinct from the systematically assembled OpenAlex reference set and does not estimate retrieval recall.

## Table S2

[Records without usable normalized author keywords](tables/Table_S2.csv). These records remain in the analytical corpus but contribute no keyword nodes or co-occurrence links.

## Table S3

- [S3a: normalized tokens and original word forms](tables/Table_S3a.csv).
- [S3b: complete keyword expressions, normalized representations and supporting records](tables/Table_S3b.csv).

These mappings support interpretation of ambiguous stems. Shared lexical forms do not by themselves establish a common architecture, implementation or scientific topic.

## Table S4

- [S4a: Figure 2 membership key](tables/Table_S4a.csv).
- [S4b: Figure 5 membership key](tables/Table_S4b.csv).

The identifiers are local to the reported partitions. Aligned colours or shapes do not establish identical memberships across conditions.

## Table S5

[Counts and denominators for the four Figure 3 series](tables/Table_S5.csv). Frequencies are measured before pruning, with each publication counted at most once per token.

## Table S6

[Retraction flags in the frozen corpus](tables/Table_S6.csv). Retention records the scope of the analytical input and does not validate the underlying studies.

## Table S7

- [Hierarchy counts for the 40 reference conditions](tables/Table_S7.csv).
- [Complete parent-child memberships](tables/Table_S7_parent_child_memberships.csv).

These reference conditions use seed 1000 and multiplier 1, including the corrected cumulative 2015-2022 input. All-seed partitions are provided separately in [`results/partitions/`](../results/partitions/). L1 availability and the actual FINAL level are reported explicitly.

## Table S8

[Reconciliation of retrieved and analytical records](tables/Table_S8.csv).

## Table S9

[Network sizes at successive pruning stages](tables/Table_S9.csv).

## Table S10

[Effective cutoffs, removed nodes and retained edge weight](tables/Table_S10.csv).

## Table S11

[Full-network and retained-network statistics](tables/Table_S11.csv).

## Table S12

[Selected terminology derived from the historical Sci2 graphs](tables/Table_S12.csv). The categories are interpretative and non-exclusive. A dash identifies an unreported entry, not zero publications or absence of research.

## Table S13

[Counts and prevalence of selected normalized tokens](tables/Table_S13.csv).

## Table S14

[Representative studies, their assumptions and evaluation scope](tables/Table_S14.csv). Suggested comparisons are distinguished from evaluations already reported by the cited studies.

## Table S15

[Publication-version matches between the bibliography and analytical records](tables/Table_S15.csv). Contextual references do not automatically belong to the bibliometric corpus.

## Further numerical evidence

- [Complete normalized prevalence](../results/prevalence/).
- [Native token-network sensitivity results](../results/native/).
- [Keyword-representation comparisons](../results/keyword_representations/).
- [Temporal community correspondence](../results/temporal/).
- [OpenAlex retrieval, eligibility decisions and matching](../data/openalex/).
- [Reproduction instructions](../reproducibility/README.md).

## Retrieval provenance

The preserved export dates, index metadata and cohort reconciliation are documented in [Section S1 of the supplementary methods](Supplementary_methods_and_tables.pdf#page=1).

## Pruning details

The complete selection procedure is described in Section S2. The effective-cutoff exceptions and archival reconstruction details are in [Section S6](Supplementary_methods_and_tables.pdf#page=17). The corresponding counts are in Tables S9-S11.

## Interpretation of thematic names

The names assigned to communities are interpretative summaries supported by the lexical mappings and the stated sensitivity controls. An independent inter-rater assessment of those names is not reported.
