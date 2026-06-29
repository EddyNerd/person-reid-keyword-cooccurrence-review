# Graph Interpretation

This document explains how to read the keyword co-occurrence graphs used in the person Re-ID longitudinal review.

## Nodes and Edges

Each node represents a keyword. Each edge represents a co-occurrence between two keywords.

An edge means that the two connected keywords appear together in the bibliometric corpus. A thicker edge indicates a stronger co-occurrence relationship.

## Node Size

Node size represents keyword frequency. Larger nodes correspond to keywords that appear in more references.

## Edge Thickness and Opacity

Edge thickness represents co-occurrence strength. Stronger co-occurrence relationships are shown with thicker edges.

Edge opacity follows the same logic: thicker edges are more opaque, while weaker edges are lighter. This helps visually distinguish strong keyword associations from weaker ones.

## Node Colors: Level 0 Communities

Node color indicates Level 0 community membership. Level 0 communities correspond to fine-grained thematic groups.

Nodes with the same color belong to the same Level 0 community.

## Node Shapes: Level 1 Communities

Node shape indicates Level 1 community membership. Level 1 communities correspond to broader thematic groups.

Nodes with the same shape belong to the same Level 1 community. A Level 1 community may contain one or more Level 0 communities.

## Reading Communities

A community should be interpreted by combining:

- the keywords contained in the group;
- the color of the nodes;
- the shape of the nodes;
- the strength of the edges connecting them;
- the position of the nodes in the layout.

For example, a group containing terms such as `deep`, `neural`, `convolut`, and `network` can be interpreted as a deep neural network topic. A group containing `metric`, `learn`, `kernel`, and `represent` can be interpreted as a metric-learning and representation-learning topic.

## Kamada-Kawai Layout

The graphs use the Kamada-Kawai layout. This layout places structurally close nodes near each other by trying to preserve graph-theoretical distances in a two-dimensional space.

Keywords connected by shorter graph-theoretical paths tend to appear closer together. Keywords connected through longer paths tend to appear farther apart.

However, the layout is a two-dimensional projection of a more complex network structure. Some local distortions can occur, so visual proximity should not be interpreted alone.

## Interpretation Rule

The graph should be read using both topology and visual encoding:

- strong edges indicate strong keyword co-occurrence;
- colors identify fine-grained communities;
- shapes identify broader communities;
- node size indicates keyword frequency;
- node position indicates structural proximity under the Kamada-Kawai layout.

The most reliable interpretation comes from reading these elements together rather than relying on a single visual cue.
