# Person Re-Identification Keyword Co-occurrence Review

This repository contains supplementary materials for the paper:

**Person Re-Identification: A Longitudinal Keyword Co-Occurrence Graph-Based Review of Its Evolution Toward Open-World Applications**

The repository provides the figures, tables, and methodological notes used to support the longitudinal analysis of person Re-ID research from 2015 to 2024.

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

- `table_01_number_of_papers.xlsx`  
  Number of person Re-ID papers indexed in the Web of Science Core Collection by year.

- `table_02_thematic_evolution_2015_2024.xlsx`  
  Summary of the top thematic evolution of person Re-ID research from 2015 to 2024.

- `table_03_l1_l0_communities_2015_2024.xlsx`  
  L1 and L0 communities for the cumulative 2015–2024 period.

- `table_04_l1_l0_communities_2015_2016.xlsx`  
  L1 and L0 communities for the period 2015–2016.

- `table_05_l1_l0_communities_2017_2018.xlsx`  
  L1 and L0 communities for the period 2017–2018.

- `table_06_l1_l0_communities_2019_2020.xlsx`  
  L1 and L0 communities for the period 2019–2020.

- `table_07_l1_l0_communities_2021_2022.xlsx`  
  L1 and L0 communities for the period 2021–2022.

- `table_08_l1_l0_communities_2023_2024.xlsx`  
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

The cross-sectional graphs use the Kamada–Kawai layout. In this layout, keywords that are structurally close in the network tend to be placed near each other, while keywords connected through longer graph-theoretical paths are placed farther apart. Because the layout projects a high-dimensional network onto a two-dimensional plane, local distortions may occur. For the cumulative graphs, the utilization of the Kamada-Kawai layout resulted in a cluttered graph. For this reason, we preferred the GEM (Graph Embedder) layout. Fruchterman-Reingold layout aims to create a balanced layout where nodes are evenly distributed across the graph and the attraction/repulsion forces are proportional to the number of connected edges. Conversely, GEM modifies Fruchterman-Reingold using a simulated annealing process, which results in a graph where the distances between nodes are maximized, and edge crossings are minimized. This makes the graph more legible (see the annexes).

References

] A. Frick, A. Ludwig, and H. Mehldau, "A fast adaptive layout algorithm for undirected graphs," in Graph Drawing, DIMACS Workshop Proc., Princeton, NJ, USA, Oct. 10–12, 1994, pp. 388–403.

T. M. Fruchterman and E. M. Reingold, "Graph drawing by force-directed placement," Softw. Pract. Exp., vol. 21, no. 11, pp. 1129–1164, Nov. 1991.

S. Kirkpatrick, C. D. Gelatt, Jr., et M. P. Vecchi, “Optimization by simulated annealing,” Science, vol. 220, no. 4598, pp. 671–680, 13 May 1983. doi: 10.1126/science.220.4598.671.

## Citation

If you use these materials, please cite the associated paper:

**Person Re-Identification: A Longitudinal Keyword Co-Occurrence Graph-Based Review of Its Evolution Toward Open-World Applications**
