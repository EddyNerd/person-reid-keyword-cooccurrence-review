# Corrected cumulative 2015–2022 keyword network

This figure uses all **1,499 analytical records from 2015–2022**, including
**1,439 records with usable author keywords**. It restores the 254 records from
2015–2018 that were absent from the historical file labelled 2015–2022.
Author keywords (`DE`) provide the vocabulary. Titles, abstracts and Keywords
Plus do not contribute terms.

The displayed graph contains **91 nodes and 434 weighted edges**. It uses the
corrected campaign's reference pruning rule, **weight > 16** (integer weights
of at least 17), and the largest retained connected component. The full graph
contains 1,365 nodes and 33,630 edges. The displayed edges retain 15,907 of the
full graph's 72,170 units of co-occurrence weight (22.04%). A link's weight
counts source records containing both normalized tokens.

## Communities and design

The figure uses the saved **Louvain partition, seed 1000**, computed on the
corrected retained graph (*filter-and-suppress*). It contains **14 L0 groups
and 7 L1 groups; FINAL is L1**. Node colours represent L0 and shapes represent
L1. Numeric memberships are preserved in `nodes.csv`. These are corrected
memberships, not copied historical memberships.

The visual grammar follows the historical cumulative figure: a white square
canvas, pastel colours, mixed node shapes, grey translucent weighted edges,
document-frequency node areas and title-case stem labels. The historical
ten-colour palette has been extended to fourteen distinct pastel colours so
that different L0 communities do not receive an identical colour. Display
codes are aligned to the historical figure by shared-token overlap where
possible; a matching colour or shape does not establish equal membership.

Coordinates come from the corrected campaign's frozen **native GUESS GEM**
layout (seed 1000), originally calculated on the union of seven corrected
pruning masks: 202 nodes and 1,463 unweighted adjacency edges. The reference
figure shows the 91 retained nodes at these same coordinates in an enlarged
viewport. Positions have not been optimized to create communities. Only
label locations were adjusted to avoid text overlap; labels use a 14-point font
for readability. Layout seed 1000 is
documented for this corrected layout; the original historical seed was not
recorded.

The companion Leiden reference is documented, without assigning its groups
to this Louvain figure. At seed 1000, corrected Leiden suppression returns
19 L0, 7 L1 and 6 L2 groups, with FINAL = L2. Corrected Leiden full-network
detection returns 247 L0, 52 L1, 14 L2 and 7 L3 groups, with FINAL = L3.
`leiden_hierarchy_reference.json` supplies the actual parent/child memberships.
Additional hierarchy levels combine existing groups and do not independently
establish new research themes.

## Reproduce the image

Install Python with `matplotlib`, `numpy` and `adjustText`, then run:

```text
python render_corrected_cumulative.py
```

The portable renderer reads the adjacent CSV files; the source WoS exports,
Java and Sci2 are not needed to redraw the figure. `adjustText` is used only
if `labels.csv` is absent. The frozen `labels.csv` provides the label positions
used in the delivered image. Versions used for this rendering were matplotlib
3.11.2, numpy 2.5.4 and adjustText 1.4.0.

- `2015–2022.png`: 3,600 × 3,600-pixel figure replacing the repository display.
- `2015–2022.svg` and `2015–2022.pdf`: vector versions of the same figure.
- `nodes.csv`: all 91 tokens, document frequencies, numeric L0/L1/FINAL labels,
  coordinates, colours, markers and node areas.
- `edges.csv`: all 434 displayed edges and integer co-occurrence weights.
- `labels.csv`: frozen positions for all 91 text labels.
- `community_key.*`: a separate visual membership key.
- `provenance.json`: cohort, pruning, partition, geometry and source hashes.
- `display_alignment.json`: membership-overlap matrices used only for styling.
- `render_checks.json`: label-count, overlap, clipping and graph checks.
- `artifact_hashes.json`: SHA-256 hashes of the delivered files.

`prepare_inputs_workspace.py` is the optional workspace extraction helper. It
requires the original project tree and is not needed for portable rendering.
Previous historical images remain archived separately; they should not be
treated as the corrected full 2015–2022 network.
