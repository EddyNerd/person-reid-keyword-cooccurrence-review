# Corrected cumulative 2015–2022 network: analysis audit

The original input labelled 2015–2022 contained 1,245 records from 2019–2022. The corrected input restores 254 records from 2015–2018. It contains **1,499 unique records**, including **1,439 with usable normalized author keywords**. Only author keywords contribute vocabulary.

## Independent checks

All **654 files** in the frozen corrected release matched their recorded SHA-256 hashes. The audit recomputed every node frequency and co-occurrence weight from the record-level token sets. The corrected record set equals the union of the four cross-sectional cohorts from 2015–2016 through 2021–2022. Author-keyword fields and final publication years match the source export; the documented healthcare exclusion remains applied.

| Graph or stage | Nodes | Links | Total edge weight |
|---|---:|---:|---:|
| Complete corrected network | 1,365 | 33,630 | 72,170 |
| Preselected candidates | 500 | 7,300 | — |
| Reference-pruned network | 91 | 434 | 15,907 |

The adaptive value is 16.33986018378498. The reference rule is **weight > 16**, so retained integer weights start at 17. The reference graph retains 22.04101427185811% of the complete network's co-occurrence weight. All seven masks were independently reconstructed from the frozen candidate lists. Graph hashes, partition coverage and hierarchy nesting were checked for all **480 unique detector outputs**: seven suppression thresholds and one full-network detection condition, each with two algorithms and 30 seeds.

## Scope of the correction

Only the cumulative 2015–2022 Louvain and Leiden hierarchy scopes changed. The other **18 algorithm-by-window scopes** (nine windows × two algorithms) are substantively identical to their earlier versions; the documentary provenance field was excluded from that equality check. These 18 scopes are **not** the 18 historical L0/L1 partitions used in separate archival replay checks. Their reuse does not validate the incomplete historical cumulative cohort as a full 2015–2022 input.

Current T, N and P analyses all use the same 1,499 corrected records. Their three full-network matrices were independently recomputed and agree exactly with the stored matrices. The token-network hash is identical to the corrected native-token graph hash. The normalized-prevalence input manifest contains ten corrected-release entries and the temporal-correspondence manifest contains 490; all these hashes match the corrected release.

## The correction changes community assignments

The following ARI values measure agreement **between the old incomplete and corrected partitions**, using common nodes and 30 matched numerical seeds. They are not before/after differences in a stability score.

| Detection condition | Algorithm | Common nodes | Median L1 ARI, old versus corrected |
|---|---|---:|---:|
| Reference suppression | Louvain | 75 | 0.5398511714118273 |
| Reference suppression | Leiden | 75 | 0.5079502396291293 |
| Complete-network detection (hide) | Louvain | 1,218 | 0.24636180382594675 |
| Complete-network detection (hide) | Leiden | 1,218 | 0.3225934887699415 |

The old and corrected partitions are therefore not interchangeable. Current scientific claims for the full 2015–2022 interval must use the corrected partitions.

## Hierarchy at seed 1000

| Treatment | Algorithm | Group counts | FINAL |
|---|---|---|---|
| Reference suppression | Louvain | L0: 14; L1: 7 | L1 |
| Reference suppression | Leiden | L0: 19; L1: 7; L2: 6 | L2 |
| Complete-network detection (hide) | Louvain | L0: 59; L1: 7 | L1 |
| Complete-network detection (hide) | Leiden | L0: 247; L1: 52; L2: 14; L3: 7 | L3 |

Leiden adds aggregation levels: L2 under reference suppression, and L2/L3 under full-network detection. They merge existing groups; they do not establish new research themes. Actual parent–child IDs, full membership lists and the 91 reference-visible members are provided in [corrected_seed1000_parent_child_memberships.json](corrected_seed1000_parent_child_memberships.json). Counts for all 480 runs are in [corrected_hierarchy_counts_all_480_runs.csv](corrected_hierarchy_counts_all_480_runs.csv).

## Reproduction and limits

[validation.json](validation.json) records full numerical values, source graph hashes, check results and public-file hashes. The standard-library-only [audit_corrected_campaign.py](audit_corrected_campaign.py) consolidates the independent audit calculations; supply `--base` pointing to the local active-output directory. It reads the frozen release and does not execute Louvain or Leiden again. Reproducing the complete audit requires the original local inputs; raw WoS record text and personal absolute paths are not included in this public subset. Computational agreement does not establish bibliographic coverage or thematic validity.
