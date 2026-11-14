# Cross-sectional and Cumulative Analysis

The study uses two complementary strategies to analyze the evolution of person Re-ID research topics from 2015 to 2024: cross-sectional analysis and cumulative analysis.

## Cross-sectional Analysis

Cross-sectional analysis provides separate keyword co-occurrence graphs for each two-year period:

- 2015-2016
- 2017-2018
- 2019-2020
- 2021-2022
- 2023-2024

Each graph highlights the most significant keywords for its respective period. In this study, a keyword is considered important in a period if it appears in the corresponding pruned graph.

This does not necessarily mean that the keyword first appeared in that period. It means that the keyword became structurally significant enough to survive the pruning process in that time slice.

## Purpose of Cross-sectional Analysis

Cross-sectional analysis helps identify emerging or reconfigured topics in each period. It is especially useful for tracing shifts in research emphasis, such as the movement from handcrafted features and metric learning toward deep learning, domain adaptation, transformers, and open-world Re-ID challenges.

From 2017-2018 onward, interpretation emphasizes new or strengthened topics rather than repeating stable vocabulary across periods.

## Cumulative Analysis

Cumulative analysis provides graphs for the following periods:

- 2015-2016
- 2015-2018
- 2015-2020
- 2015-2022
- 2015-2024

In cumulative graphs, each window includes the literature from 2015 up to the endpoint year. For example, the 2015-2020 graph includes the literature from 2015 through 2020.

## Node Position Consistency

The input for the corrected 2015–2022 cumulative network contains all 1,499 study records published from 2015 through 2022, including 1,439 with usable author keywords. It replaces the earlier 1,245-record input labelled 2015–2022, which covered only 2019–2022. The [correction record](../corrections/cumulative_2015_2022_20261114/README.md) documents the restored 254 records and the corrected graph.

The original GUESS workflow allowed node coordinates to be exported and imported. Saved historical figures retain their recorded coordinates; we do not assume that every historical graph or successive cumulative window has identical node positions.

For the corrected 2015–2022 window, a common native GUESS GEM layout was calculated from the union of the seven display masks, containing 202 nodes and 1,463 links. The layout seed is 1000. The exported coordinates are fixed when the masks within this window are compared. Changing a threshold therefore changes which nodes and links are displayed without moving the remaining nodes. This consistency applies within the corrected window; it does not imply fixed coordinates across different publication periods.

Community correspondence is calculated from actual memberships, not from matching colours, shapes or nearby positions in a figure.

## Interpretation of Cumulative Graphs

If a word appears in a cumulative graph ending in year `Y`, it indicates that the word appears in the literature within the 2015-`Y` window and became significant by that endpoint year.

Cumulative analysis is useful for identifying terms with seniority in the person Re-ID discussion and for supporting the broader evolution narrative.

## Complementarity of the Two Analyses

The two strategies answer different questions:

- Cross-sectional graphs show what is structurally prominent in a specific two-year period.
- Cumulative graphs show how topics accumulate and consolidate over time.

Together, they support the paper's objective of tracing the evolution of person Re-ID from closed-world benchmarking toward open-world, deployment-oriented applications.
