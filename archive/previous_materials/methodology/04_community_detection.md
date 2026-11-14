# Community Detection

Community detection was used to identify thematic groups in the pruned keyword co-occurrence networks.

## Definition

Community detection is the task of identifying groups of nodes that are more densely connected to one another than to the rest of the network. These groups reveal the mesoscopic structure of the graph and help identify research themes.

In a keyword co-occurrence network, a community can be interpreted as a cluster of terms that tend to appear together in the literature.

## Modularity

The study uses modularity-based community detection. Modularity measures how much the density of edges inside a group exceeds what would be expected at random under a null model.

The null model commonly used for this purpose is the configuration model, which preserves each node's degree while randomly rewiring edges.

A high modularity value indicates that the detected communities contain many internal connections and relatively fewer connections to other communities.

## Method Used

Sci2 provides several modularity-based community detection options, including Blondel, Louvain with a resolution parameter, Louvain multilevel refinement, SLM, and other network measures.

The Blondel method was selected because the pruned co-occurrence networks are relatively small and because the method is straightforward, widely used, and available in Sci2.

The Blondel method is also known as the original Louvain method. It is a greedy modularity optimization algorithm based on Newman-Girvan modularity.

## Resolution Limit

Newman-Girvan modularity has a known resolution limit. This means that small but meaningful communities may sometimes be merged into larger ones. Higher-resolution methods can identify smaller communities, while lower-resolution approaches tend to produce fewer and larger communities.

Despite this limitation, the Blondel method was appropriate for this study because:

- the networks were already pruned;
- the graph sizes were manageable;
- the method does not require manually specifying a resolution parameter in the standard workflow;
- alternatives such as Leiden were not part of standard Sci2 distributions.

## Community Levels

The Blondel method may produce a hierarchical or multilevel partition. In this study, the runs produced two community levels:

- Level 0 (L0): fine-grained communities.
- Level 1 (L1): broader communities that contain one or more L0 communities.

Additional levels are theoretically possible depending on the network structure, but the analysis reported here focuses on L0 and L1.

## Interpretation

L0 communities are interpreted as fine-grained topics. L1 communities are interpreted as broader thematic groupings. In the visualizations, node color represents L0 membership, while node shape represents L1 membership.

Community names are assigned as umbrella terms that summarize the keywords contained in each group.
