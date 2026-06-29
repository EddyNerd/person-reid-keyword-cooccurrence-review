# Graph Pruning

The initial keyword co-occurrence networks generated in Sci2 were dense and difficult to interpret. When first displayed in GUESS, all nodes were connected, which reduced readability and made the thematic structure harder to identify.

Graph pruning was therefore used to simplify the networks while maintaining a consistent procedure across study periods.

## Objective

The pruning strategy aims to:

- improve graph readability;
- reduce visual clutter;
- retain the most structurally important nodes and strongest edges;
- keep pruning consistent across cross-sectional and cumulative periods.

## Pruning Procedure

For each network `N`, the pruning process was performed as follows.

1. Use the Network Analysis Toolkit (NAT) to obtain the number of nodes `n` and the number of edges `e` in the original network `N`.

2. Divide the number of nodes by three and round to the nearest multiple of 100:

   ```text
   n_prime = round_to_nearest_100(n / 3)
   ```

3. Extract the top `n_prime` nodes from the original network. This produces a first reduced network `N_prime`.

4. Use NAT to obtain the number of edges `e_prime` in `N_prime`.

5. Divide `e_prime` by three and round to the nearest multiple of 100:

   ```text
   e_double_prime = round_to_nearest_100(e_prime / 3)
   ```

6. Extract the top `e_double_prime` edges from `N_prime`. This produces a second reduced network `N_double_prime`.

7. Use NAT to obtain the number of nodes `n_double_prime` in `N_double_prime` and compute the average edge weight.

8. Compute an adaptive threshold `w`:

   ```text
   w = average_edge_weight * log10(n_double_prime)
   ```

9. Use the Dichotomize tool to keep only edges whose weights are greater than `w`.

## Rationale for the Adaptive Threshold

The base-10 logarithm is used as a heuristic adaptive threshold. As the network grows, the cutoff increases sub-linearly. This means that larger graphs must retain proportionally stronger edges to remain readable, while smaller graphs are not over-pruned.

This approach provides a practical compromise between readability and thematic coverage.

## Interpretation After Pruning

A keyword is considered important for a given time period if it appears in the corresponding pruned graph. This does not necessarily mean that the keyword first appeared in that period; rather, it means that the keyword became structurally significant enough to survive the pruning process for that period.
