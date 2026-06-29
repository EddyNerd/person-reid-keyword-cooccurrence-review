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

For cumulative evolution, node positions were maintained across time slices by exporting and importing x-y coordinates in GUESS using the node position import/export workflow.

This makes cumulative graphs more visually comparable over time because recurring keywords can remain in stable positions across successive windows.

## Interpretation of Cumulative Graphs

If a word appears in a cumulative graph ending in year `Y`, it indicates that the word appears in the literature within the 2015-`Y` window and became significant by that endpoint year.

Cumulative analysis is useful for identifying terms with seniority in the person Re-ID discussion and for supporting the broader evolution narrative.

## Complementarity of the Two Analyses

The two strategies answer different questions:

- Cross-sectional graphs show what is structurally prominent in a specific two-year period.
- Cumulative graphs show how topics accumulate and consolidate over time.

Together, they support the paper's objective of tracing the evolution of person Re-ID from closed-world benchmarking toward open-world, deployment-oriented applications.
