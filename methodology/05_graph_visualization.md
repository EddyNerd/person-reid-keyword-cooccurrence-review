# Graph Visualization

The keyword co-occurrence networks were visualized to support thematic interpretation across time.

## Visualization Workflow

The networks were first displayed in GUESS, the visualization module integrated into the Sci2 Tool. Network data were then extracted from GUESS and reproduced with Python in order to control the final visual encodings used in the figures.

## Visual Encodings

The graphs use the following visual encodings:

- Node size represents keyword frequency, defined as the number of references in which the keyword is found.
- Node color represents Level 0 community membership.
- Node shape represents Level 1 community membership.
- Edge thickness represents co-occurrence strength.
- Edge opacity increases with edge thickness to make stronger relationships more visually salient.

These encodings allow the graph to show both fine-grained and broad thematic structures at the same time.

## Community Encoding

Nodes with the same color belong to the same Level 0 community. These are fine-grained thematic groups.

Nodes with the same shape belong to the same Level 1 community. These are broader thematic groups that may contain one or more Level 0 communities.

A Level 1 community can therefore contain several Level 0 communities.

## Keyword Labels

Because Sci2 applies stemming, graph labels often appear as normalized word stems. For example:

- `learn` refers to learning.
- `convolut` refers to convolutional.
- `represent` refers to representation.
- `surveil` refers to surveillance.

Topics should therefore be interpreted by considering groups of terms, communities, and edge strengths rather than isolated labels alone.

## Kamada-Kawai Layout

The graphs use the Kamada-Kawai layout. Kamada-Kawai is a spring-based layout model in which the ideal distance between every pair of nodes is proportional to their graph-theoretical distance, usually measured by shortest-path distance.

In practical terms, keywords that are structurally close in the network tend to be placed near one another, while keywords connected through longer graph-theoretical paths tend to be placed farther apart.

This layout is useful for the pruned co-occurrence networks because it emphasizes global shortest-path structure and helps preserve relative proximity between thematically related keywords.

## Interpretation Caution

The final node positions are obtained through an energy-minimization process. Because the layout projects a high-dimensional network structure onto a two-dimensional plane, local distortions are inevitable.

Therefore, visual proximity should be interpreted together with edge thickness, community membership, and the keyword tables.
