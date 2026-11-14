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

## Layouts and saved coordinates

The historical cross-sectional graphs use Kamada–Kawai, while the historical cumulative graphs use GEM (Graph Embedder) in GUESS. The two layouts arrange nodes for display; the community-detection algorithm determines their community assignments separately.

Kamada–Kawai is a spring-based layout in which the ideal distance between two nodes depends on their shortest-path distance in the graph. Structurally close nodes therefore tend to appear near one another, although a two-dimensional drawing cannot preserve every network distance.

The corrected cumulative 2015–2022 figure uses the native GUESS GEM implementation with layout seed 1000. One layout was calculated from the union of all seven display masks (202 nodes and 1,463 links), and its exported coordinates are retained for the reference figure and comparisons between masks. The reference figure displays 91 of these nodes and 434 links. Label positions are adjusted for readability without moving the nodes. The [portable figure files](../corrections/cumulative_2015_2022_20261114/figure/README.md) contain the node coordinates, label positions and rendering code.

Node sizes use keyword document frequencies. Colours encode the corrected L0 memberships, shapes encode the corrected L1 memberships, and link widths use co-occurrence counts. Matching historical display styles does not mean that the corrected and historical communities contain identical terms.

## Interpretation Caution

The final node positions are obtained through an energy-minimization process. Because the layout projects a high-dimensional network structure onto a two-dimensional plane, local distortions are inevitable.

Therefore, visual proximity should be interpreted together with edge thickness, community membership, and the keyword tables.

