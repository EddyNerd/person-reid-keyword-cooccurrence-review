# Publication figure sources

The seven PNGs in the [parent folder](../) are unchanged publication assets. The exact corresponding vector exports are in [vector/](vector/). This folder contains the saved inputs and rendering code used for those figures, with local input paths made relative. No new community detection or analytical result is introduced.

| Article figure | Source and saved data | Vector |
| --- | --- | --- |
| 1 | [conceptual diagram code](conceptual/draw_figure1_publication.py) | [SVG](vector/Figure_1.svg) |
| 2 | [renderer](figure2/render_figure2.py), [15 saved nodes and 27 weighted edges](figure2/Figure2_provenance.json), [memberships](figure2/Figure2_memberships.csv) | [SVG](vector/Figure_2.svg) |
| 3 | [renderer](figure3/render_figure3.py), [saved series](figure3/Figure3_provenance.json) | [SVG](vector/Figure_3.svg) |
| 4 | [alluvial renderer](alluvial/render_translucent.py), [complete saved communities and flows](alluvial/source_panels.json), first panel | [SVG](vector/Figure_4.svg) |
| 5 | [publication renderer](network_publication/render_publication.py), Louvain; [all visible memberships and coordinates](network_publication/all_64_memberships.csv) | [SVG](vector/Figure_5.svg) |
| 6 | Same publication renderer, Leiden; [hierarchy engines and saved inputs](hierarchy/) | [SVG](vector/Figure_6.svg) |
| 7 | Same alluvial renderer, second panel (formerly numbered Figure 6) | [SVG](vector/Figure_7.svg) |

## Rendering

Install the recorded [figure dependencies](requirements-figures.txt) in an isolated environment, then run any of these commands from the repository root:

```sh
python manuscript_figures/source/conceptual/draw_figure1_publication.py
python manuscript_figures/source/figure2/render_figure2.py
python manuscript_figures/source/figure3/render_figure3.py
python manuscript_figures/source/alluvial/render_translucent.py
python manuscript_figures/source/network_publication/render_publication.py
```

Outputs are written beside the corresponding script; they do not replace the publication PNGs. The alluvial script outputs Figures 4 and 7. The network script outputs `Louvain_publication` (Figure 5) and `Leiden_publication` (Figure 6). Its hierarchy module is an internal dependency, not the publication entry point.

Figure 2 uses the final node centres already digitized from the existing detail image; it does not claim that these are the original Sci2 layout coordinates. Figure 3 uses the frozen counts and percentages; full prevalence results are [available separately](../../results/prevalence/). Figures 4 and 7 follow saved historical community membership, with shared-token counts determining ribbon widths. Figures 5 and 6 use the same 64 displayed nodes and 239 weighted edges and the four saved seed-1000 partitions. Node positions, fine-group colours, intermediate shapes and the L2/L3/L4 enclosure engines are included. Only the one plotted mask and four plotted atlas runs are retained here; the complete campaigns are [available separately](../../results/partitions/).

The frozen publication SVGs are the exact portable visual reference. Regenerating raster pixels, label placement and SVG serialization can vary with font availability, Python, plotting backend and package versions. The network renderer repeats the original seeded `adjustText` call; its final publication label coordinates are also retained in [publication_provenance.json](network_publication/publication_provenance.json). This source bundle was checked for valid Python syntax, matching saved memberships and complete inputs without rendering new images. It does not promise byte-identical cross-platform output or recover the unknown historical Sci2 random seed.

`SOURCE_MANIFEST.json` records the original source hashes and the limited portability edits. Local machine provenance paths have been replaced by neutral relative identifiers. Author-owned code and artwork follow the repository's CC BY 4.0 licence; external plotting packages retain their own licences and are not vendored here.
