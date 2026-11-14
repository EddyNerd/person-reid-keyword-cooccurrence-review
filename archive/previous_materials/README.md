# Person Re-Identification Keyword Co-occurrence Review

This repository contains supplementary materials for the paper:

**Person Re-Identification: A Longitudinal Keyword Co-Occurrence Graph-Based Review of Its Evolution Toward Open-World Applications**

The repository provides the figures, tables, and methodological notes used to support the longitudinal analysis of person Re-ID research from 2015 to 2024.

## Corrected cumulative graph for 2015–2022

The cumulative 2015–2022 figure has been rebuilt from the complete study-period corpus. The earlier input labelled 2015–2022 contained only 2019–2022 records. Restoring the 254 records from 2015–2018 gives **1,499 records**, including **1,439 with usable author keywords**.

The [corrected figure](figures/cumulative_graphs/2015%E2%80%932022.png) displays **91 nodes and 434 weighted links**. It uses the saved Louvain partition under filter-and-suppress (seed 1000; threshold multiplier 1): 14 L0 communities and 7 L1 communities, with FINAL at L1. The historical visual design is retained, while the memberships come from the corrected analysis. Its native GUESS GEM layout uses seed 1000 and saved coordinates from the union of the seven display masks (202 nodes and 1,463 links).

The [correction record](corrections/cumulative_2015_2022_20261114/README.md) provides the cohort counts, graph statistics, portable rendering files, Leiden hierarchy memberships and analysis audit. The earlier figure remains available in the versioned Git history and is not the current cumulative 2015–2022 reference.

## Contents

### Figures

The `figures/` directory contains keyword co-occurrence graphs used in the study.

- `figures/cross_sectional_graphs/`  
  Cross-sectional keyword co-occurrence graphs for each two-year period:
  2015–2016, 2017–2018, 2019–2020, 2021–2022, and 2023–2024.

- `figures/cumulative_graphs/`  
  Cumulative keyword co-occurrence graphs for the periods:
  2015–2016, 2015–2018, 2015–2020, 2015–2022, and 2015–2024.

- `figures/graph_interpretation/`  
  Example figures explaining node colors, node shapes, Level 0 communities, Level 1 communities, and edge thickness.

### Tables

The `tables/` directory contains the tables used to summarize the thematic evolution and community structure of the field.

- `table_01_l1_l0_communities_2015_2024.xlsx`  
  L1 and L0 communities for the cumulative 2015–2024 period.

- `table_02_l1_l0_communities_2015_2016.xlsx`  
  L1 and L0 communities for the period 2015–2016.

- `table_03_l1_l0_communities_2017_2018.xlsx`  
  L1 and L0 communities for the period 2017–2018.

- `table_04_l1_l0_communities_2019_2020.xlsx`  
  L1 and L0 communities for the period 2019–2020.

- `table_05_l1_l0_communities_2021_2022.xlsx`  
  L1 and L0 communities for the period 2021–2022.

- `table_06_l1_l0_communities_2023_2024.xlsx`  
  L1 and L0 communities for the period 2023–2024.

### Methodology

The `methodology/` directory documents the workflow used to generate and interpret the keyword co-occurrence graphs.

- `01_data_collection_and_preprocessing.md`  
  Description of the bibliometric corpus, keyword extraction, stopword processing, and text normalization.

- `02_cooccurrence_network_construction.md`  
  Explanation of how keyword co-occurrence networks were constructed, including the definition of nodes, edges, weights, and node degree.

- `03_graph_pruning.md`  
  Description of the pruning strategy used to improve graph readability and maintain consistency across study periods.

- `04_community_detection.md`  
  Explanation of the modularity-based community detection procedure, including the use of the Blondel/Louvain method and the interpretation of Level 0 and Level 1 communities.

- `05_graph_visualization.md`  
  Description of the visual encoding used in the graphs. Node size represents keyword frequency, node color represents Level 0 community membership, node shape represents Level 1 community membership, and edge thickness represents co-occurrence strength.

- `06_cross_sectional_and_cumulative_analysis.md`  
  Description of the two analytical strategies used in the study: cross-sectional analysis and cumulative analysis.

## Graph interpretation

In the keyword co-occurrence graphs, each node represents a keyword and each edge represents a co-occurrence between two keywords. Thicker edges indicate stronger co-occurrence. Node colors indicate Level 0 communities, corresponding to fine-grained thematic groups. Node shapes indicate Level 1 communities, corresponding to broader thematic groups.

The historical cross-sectional figures use Kamada–Kawai, and the cumulative figures use GEM (Graph Embedder) in GUESS. The corrected cumulative 2015–2022 figure reuses the saved native GUESS GEM coordinates from the corrected campaign. These layout coordinates arrange nodes for display; the community-detection algorithm determines community membership separately. The corrected coordinates remain fixed within comparisons of that window's pruning masks. Spatial proximity alone does not establish a shared community or thematic persistence.

References

] A. Frick, A. Ludwig, and H. Mehldau, "A fast adaptive layout algorithm for undirected graphs," in Graph Drawing, DIMACS Workshop Proc., Princeton, NJ, USA, Oct. 10–12, 1994, pp. 388–403.

T. M. Fruchterman and E. M. Reingold, "Graph drawing by force-directed placement," Softw. Pract. Exp., vol. 21, no. 11, pp. 1129–1164, Nov. 1991.

S. Kirkpatrick, C. D. Gelatt, Jr., et M. P. Vecchi, “Optimization by simulated annealing,” Science, vol. 220, no. 4598, pp. 671–680, 13 May 1983. doi: 10.1126/science.220.4598.671.

## Citation

If you use these materials, please cite the associated paper:

**Person Re-Identification: A Longitudinal Keyword Co-Occurrence Graph-Based Review of Its Evolution Toward Open-World Applications**
