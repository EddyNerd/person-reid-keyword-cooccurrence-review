# Corrected cumulative keyword network for 2015–2022

The current [2015–2022 cumulative figure](../../figures/cumulative_graphs/2015%E2%80%932022.png) uses the complete 2015–2022 study corpus. The earlier input was labelled 2015–2022 but contained only 2019–2022 records. Restoring 254 records from 2015–2018 gives 1,499 records, including 1,439 with usable normalized author keywords. Only author keywords (WoS field DE) contribute terms to the network. Periods use final publication years.

## Corpus coverage

| Publication period | Analytical records | Records with usable author keywords |
| --- | ---: | ---: |
| 2015–2016 | 73 | 66 |
| 2017–2018 | 181 | 175 |
| 2019–2020 | 505 | 486 |
| 2021–2022 | 740 | 712 |
| **Total, 2015–2022** | **1,499** | **1,439** |

The former 1,245-record input and the corrected 1,499-record input are different cohorts and cannot be used interchangeably. The corrected input is the reference for the current cumulative figure, community detection, sensitivity analyses and temporal comparisons.

## Network construction and reference pruning

Each node is a distinct normalized author-keyword token. Each link joins two tokens found in the same record. A record contributes at most once to a token's document frequency and to each token-pair count.

| Stage or quantity | Corrected 2015–2022 value |
| --- | ---: |
| Complete network | 1,365 nodes; 33,630 links |
| Total complete-network co-occurrence weight | 72,170 |
| Selected nodes after the first stage | 500 |
| Links between the selected nodes | 21,810 |
| Selected links after the second stage | 7,300 |
| Mean weight of the 7,300 selected links | 6.054109589041096 |
| Calculated adaptive threshold, mean weight × log10(500) | 16.33986018378498 |
| Reference cutoff | Weight > 16, equivalent to integer weights of 17 or more |
| Final reference graph | 91 nodes; 434 links |
| Total reference-graph co-occurrence weight | 15,907 (22.04% of complete-network weight) |

The first two stages select approximately one third of the nodes by document frequency and then approximately one third of the links between those nodes by co-occurrence weight. Target counts are rounded to the nearest hundred using half-up rounding and capped at the available count. The final threshold is applied to the selected links. Isolates and nodes outside the largest retained connected component are then removed for filter-and-suppress community detection. The reference graph is connected and has no isolates.

## Community assignments and hierarchy

The replacement figure uses the saved **Louvain, filter-and-suppress, seed 1000, multiplier 1** partition. It has 14 L0 communities and 7 L1 communities; FINAL is L1. The node colours represent these actual L0 assignments and shapes represent actual L1 assignments.

The reference hierarchies for the corrected cumulative window are:

| Detection condition | Algorithm | L0 groups | L1 groups | L2 groups | L3 groups | FINAL |
| --- | --- | ---: | ---: | ---: | ---: | --- |
| Retained 91-node, 434-link graph (filter-and-suppress) | Louvain | 14 | 7 | — | — | L1 |
| Retained 91-node, 434-link graph (filter-and-suppress) | Leiden | 19 | 7 | 6 | — | L2 |
| Complete 1,365-node, 33,630-link graph (filter-and-hide) | Louvain | 59 | 7 | — | — | L1 |
| Complete 1,365-node, 33,630-link graph (filter-and-hide) | Leiden | 247 | 52 | 14 | 7 | L3 |

A dash means that the run returned no such level. An additional hierarchy level combines communities already present at a lower level; it is not evidence of a newly emerging research theme. In the suppressed Leiden run, the seven L1 groups are combined into six L2 groups. In the full-network Leiden run, 52 L1 groups are combined into 14 L2 groups and then seven L3 groups. The [complete Leiden memberships and parent–child relationships](figure/leiden_hierarchy_reference.json) preserve the actual groups at every returned level. Community identifiers are local to each run.

## Layout and visual design

The figure retains the historical cumulative design: pastel L0 colours, L1 node shapes, document-frequency node sizes, co-occurrence-based link widths and normalized token labels. The corrected graph has more communities than the earlier graph, so additional distinct colours and shapes are used as needed. Display styles may be aligned through membership overlap, but the numeric community assignments are never changed to make the figures look alike.

The native GUESS GEM layout uses seed 1000. It was calculated on the union of the seven corrected display masks, containing 202 nodes and 1,463 links. The saved union coordinates are fixed when those masks are compared. The reference figure displays the retained 91 nodes and 434 links at these coordinates, with an enlarged viewport for readability. Labels are positioned separately without moving nodes. These positions apply to this corrected window and do not imply identical coordinates across historical publication periods.

## Reproducibility files

- [Corrected PNG figure](../../figures/cumulative_graphs/2015%E2%80%932022.png), [SVG](../../figures/cumulative_graphs/2015%E2%80%932022.svg) and [PDF](../../figures/cumulative_graphs/2015%E2%80%932022.pdf).
- [Portable rendering instructions](figure/README.md).
- [Node frequencies, memberships, GEM coordinates and styles](figure/nodes.csv).
- [Weighted links](figure/edges.csv) and [saved label positions](figure/labels.csv).
- [Rendering script](figure/render_corrected_cumulative.py), [provenance](figure/provenance.json), [display-style alignment](figure/display_alignment.json) and [render checks](figure/render_checks.json).
- [Community key](figure/community_key.svg) and [Leiden hierarchy memberships](figure/leiden_hierarchy_reference.json).
- [Analysis audit](audit/analysis_audit.md) and [machine-readable validation](audit/validation.json).

The portable renderer reads the published CSV files and saved positions. It redraws the corrected saved partition; it does not rerun community detection.

## Effect on the analyses and historical checks

The current cumulative statistics, sensitivity results and temporal comparisons use the corrected 1,499-record cohort. The [analysis audit](audit/analysis_audit.md) checks their input provenance and separates them from results obtained with the earlier incomplete input. The other nine temporal windows are unchanged by this cumulative-cohort correction. Across the two algorithms and ten windows, 18 algorithm–window scopes were unaffected and the two cumulative 2015–2022 scopes were updated. These scopes must not be confused with the count of historical L0/L1 partitions below.

The historical figure remains available at [commit 4ae62e66db177659063ffc3ea14d77c263efe958](https://github.com/EddyNerd/person-reid-keyword-cooccurrence-review/blob/4ae62e66db177659063ffc3ea14d77c263efe958/figures/cumulative_graphs/2015%E2%80%932022.png). Earlier replay reproduced all 18 available historical L0/L1 partitions with ARI = 1. That total included the L0 and L1 partitions of the incomplete cumulative input. Excluding that condition leaves nine unaffected historical graph conditions and 16 available historical partitions, all reproduced with ARI = 1. These checks verify agreement with the old saved memberships; they do not validate the community assignments of the corrected 2015–2022 graph. The corrected cohort, graph, saved partitions and current figure are checked separately in the published audit.
