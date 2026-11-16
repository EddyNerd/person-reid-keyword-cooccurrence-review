# Successive cumulative GEM coordinates

This update of 16 November 2026 restores the successive-coordinate convention
in the cumulative 2015-2022 drawing. Nodes retained in consecutive cumulative
windows keep their saved GEM coordinates; additional nodes are added around
them. The archived 2015-2016, 2015-2018 and 2015-2020 drawings are unchanged.

The corrected 2015-2022 graph still represents 1,499 publications, including
1,439 records with usable author keywords. Its 91 nodes, 434 weighted edges,
document frequencies and saved Louvain seed-1000 communities are unchanged.
Only the drawing geometry is updated. No corpus, pruning or community-detection
analysis was rerun.

## Coordinate inheritance

| Transition | Shared displayed terms | Exactly equal node coordinates |
|---|---:|---:|
| 2015-2016 to 2015-2018 | 10 | 10 |
| 2015-2018 to 2015-2020 | 23 | 23 |
| 2015-2020 to corrected 2015-2022 | 58 | 58 |
| Corrected 2015-2022 to aligned 2015-2024 | 89 | 89 |

Of the 91 corrected 2022 nodes, 58 inherit their positions from 2015-2020.
Another 31 use their saved positions from the historical 2015-2024 drawing.
The remaining two terms, `modul` and `structur`, were absent from the inspected
historical drawings. They are placed by the fixed-anchor GEM extension
described below, while all 89 inherited positions remain immobile. They each
have one retained neighbour: `modul` connects to `attent`, and `structur` to
`learn`, with weight 17 in both cases.

Five terms had been omitted from the older, temporally incomplete 2022 graph
and later returned at different positions in 2024: `face`, `intellig`, `rank`,
`similar` and `spatial`. Restoring them in the corrected 2022 graph requires
carrying their earlier 2020 positions forward. The aligned 2024 drawing changes
only these five coordinates; its other 111 positions, 116-node/615-edge graph,
frequencies and saved communities remain unchanged.

The previous drawings remain in the repository history and the historical
archive. The independently recalculated 2022 GEM geometry published on
14 November remains documented in its own correction directory. It is not
silently reclassified as a fixed-coordinate drawing.

## GEM and the two additional nodes

The inherited coordinates come from saved historical GEM drawings. Their
original layout random seed was not recorded. The Louvain seed 1000 identifies
the corrected 2022 partition, not the historical GEM geometry.

The original GUESS GEM implementation initializes and rescales all nodes and
does not honour fixed-node flags. `anchored_gem.py` therefore implements a
constrained extension of the GEM arrangement phase: attraction, repulsion,
gravity, jitter and adaptive local temperature are applied only to the two
additional nodes. All inherited coordinates enter the forces but are never
updated. This is not a claim of executing the unmodified native GEM class.

The extension uses seed 1000, unweighted adjacency, floating-point arithmetic
and no final rescaling. Its characteristic length is 32 archived-coordinate
units: the recorded native GEM length of 128 multiplied by its final rescaling
factor of 0.25. Full coefficients, stop conditions and coordinates are recorded
in `provenance.json`. The two-node placement does not use community labels or
alter the scientific co-occurrence weights.

## Rendering and interpretation

Both revised drawings use the same viewport and coordinate-to-page mapping.
Node area remains three times document frequency. Colours encode L0 and shapes
encode L1, using the saved memberships of the corresponding graph. Matching
positions, colours or shapes do not establish identical community membership
between periods. Label positions may be adjusted separately for readability;
the renderer never moves a node.

The 2022 graph has 14 L0 and 7 L1 communities, with FINAL at L1. The companion
Leiden hierarchy remains in `2015-2022/leiden_hierarchy_reference.json`: its
additional levels aggregate saved communities and are not drawn as new themes
in this Louvain figure.

## Files and reproduction

- `2015-2022/` and `2015-2024/`: publication PNG/SVG/PDF, 954-pixel preview,
  node/edge tables, frozen label coordinates and rendering checks.
- `archived_GEM_positions.csv`: neutral coordinate exports from the historical
  cumulative inputs used to verify inheritance.
- `coordinate_verification.json`: exact-coordinate and graph checks.
- `provenance.json`: sources, graph scope and fixed-anchor placement details.
- `baseline_memberships_*.csv`: scientific node attributes before this update.
- `SHA256SUMS.json`: integrity checks for this bundle.

From this directory:

```text
python verify_coordinates.py
python verify_coordinates.py --replay-additions
python -m pip install -r requirements.txt
python render_incremental.py
```

Verification uses the Python standard library. Rendering uses the recorded
plotting dependencies. Raster pixels and font placement may differ across
platforms; the supplied coordinates and vector files are the fixed references.
