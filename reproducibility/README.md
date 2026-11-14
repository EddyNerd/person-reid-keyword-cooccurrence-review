# Reproducing the saved analysis

## 1 Check the frozen material without running a detector

```text
python src/verify_materials.py --check-partitions
```

This command uses only the Python standard library. It checks the release checksums, the 2,333-record incidence file, the 2,260 usable-keyword records, all full T/N/P graphs, the corrected cumulative 2015-2022 scope, the OpenAlex reference counts and the saved hierarchy structure. Generated checks are written to `.verification/`.

The frozen graph inputs preserve the node and edge sets used for detection. The initial native extraction, including its handling of rank ties, is represented by these saved inputs and the recorded mask specifications. The original WoS search interface history and Sci2 random seed are unavailable and cannot be regenerated from these files.

## 2 Recalculate publication and expression agreement from saved partitions

```text
python src/reproduce_document_ari.py
```

The default reproduces the 2023-2024 full-network comparison at L1, for Louvain and Leiden and all three representation pairs. It recalculates labels for source publications and source keyword expressions, uses one fixed intersection of clearly assigned objects across the available paired seeds, and checks the counts and descriptive ARI values against the saved table.

Other conditions can be selected explicitly:

```text
python src/reproduce_document_ari.py --case cumulative_2015-2020 --level FINAL
python src/reproduce_document_ari.py --case cross_sectional_2015-2016 --treatment suppress --multiplier 1 --level L1
python src/reproduce_document_ari.py --all
```

The complete option covers all windows, both algorithms, the seven suppressed masks and full-network detection, at L0, L1, L2 and FINAL. It can take substantially longer. It uses saved partitions rather than launching new detector runs.

For an explicit publication/expression membership export:

```text
python src/reproduce_document_ari.py --export-labels .verification/projected_labels.csv.gz
```

Each distinct source expression receives one unit of voting mass. In T, that unit is divided among its distinct normalized stems before graph filtering; missing stems lose their share. In N/P, the corresponding atomic expression receives the unit when present. A record is labelled only when one community has a unique maximum. The original tolerance of 1e-10 is retained for tied vote totals.

Projected-label codes are `-1` for no represented keyword mass, `-2` for a tie or split source expression, and `-3` for an unavailable partition level. These are not community identifiers. Degenerate comparisons are counted separately.

The original projected-array cache is derivable from these inputs and is not duplicated in full. One representative NPZ example and checksums of all original NPZ/NPY arrays are retained in [`results/document_projection/`](../results/document_projection/). Files `x0`-`x4` refer to successive two-year cross-sections; `u0`-`u4` refer to successive cumulative windows. Within the original cache filenames, representations 0/1/2 correspond to T/N/P.

## 3 Replay community detection

Exact membership replay uses the recorded interpreter, **CPython 3.9.12**, together with **NetworkX 3.2.1** and `PYTHONHASHSEED=0`. The numerical random seed alone does not guarantee identical partitions across Python versions. The standard-library checks and saved-partition ARI recalculation above can be run with a newer Python interpreter.

Using Python 3.9.12, create an isolated environment and install the recorded dependency versions:

```text
python -m venv .venv
```

Activate that environment using the command appropriate to the operating system, then install the recorded dependencies:

```text
python -m pip install -r requirements-replay.txt
```

Launch a fresh process with `PYTHONHASHSEED=0`. For example, in PowerShell:

```text
$env:PYTHONHASHSEED='0'
python src/replay_detection.py --representation T --case cross_sectional_2023-2024 --algorithm louvain --seed 1000
python src/replay_detection.py --representation P --case cross_sectional_2023-2024 --algorithm leiden --treatment hide --seed 1000
```

On a POSIX shell:

```text
PYTHONHASHSEED=0 python src/replay_detection.py --representation T --case cross_sectional_2023-2024 --algorithm louvain --seed 1000
```

For all distinct frozen graph/algorithm/seed inputs:

```text
python src/replay_detection.py --all
```

The complete detector replay is computationally heavier than checks based on saved outputs. Every replayed partition is compared with its saved membership assignments. Identical graph inputs are processed once per algorithm and seed, even when they are shared by several windows or display masks.

The release checks reproduced four existing detector outputs under that recorded interpreter and package version, covering T/N/P, both algorithms, the corrected cumulative window and full-network detection. They also reproduced the document/source-expression ARI summaries for three contrasting conditions. These are packaging and reproducibility checks of existing results, not a new detection campaign. Details are in [`validation.json`](validation.json).

## Figure rendering

The [figure-source guide](../manuscript_figures/source/README.md) provides the exact vector files, rendering scripts and frozen drawing data for the seven article figures. Rebuilding a drawing from its saved coordinates and memberships is separate from rerunning community detection. The supplied PNGs remain the article originals.

## Software and algorithm provenance

The recorded analysis used NetworkX 3.2.1 for Louvain. Leiden uses the pinned NetworkX 3.7 implementation at commit `49ca2290b80c1389eb4d8d8e49dcba73f8fec016`, loaded through the original adapter. The adapter removes backend-dispatch decorators and the unused CPM import; its modularity algorithm bodies remain unchanged. The public adapter changes only the lookup of the vendor directory to a repository-relative path. The upstream source, its licence and checksums are in [`src/vendor/networkx_leiden/`](../src/vendor/networkx_leiden/).

The recorded package versions and scientific protocols are in this directory. The original analysis source snapshots in [`archive/analysis_source/`](../archive/analysis_source/) preserve implementation provenance; they contain historical directory assumptions and are not the portable entry points.

## Saved membership format

The partition archives are divided into gzip JSONL shards by the first hexadecimal character of `graph_sha256`. Each record identifies the graph, algorithm and seed and stores `membership_arrays`: one community identifier per sorted graph node at each actual returned hierarchy level. No memberships are omitted. [`src/saved_partitions.py`](../src/saved_partitions.py) resolves the graph node order and reconstructs the original dictionaries.

The 240 frozen graph input files are stored losslessly in [`data/frozen_graph_inputs.zip`](../data/frozen_graph_inputs.zip). The index in [`data/graph_index.csv`](../data/graph_index.csv) gives each archive member's logical path, graph hash and analytical setting. The portable scripts read those members directly; manual extraction is unnecessary.

L0, L1 and FINAL are selected from the actual returned hierarchy. Missing L1 levels remain missing. Counts of shared seeds, masks or reused cache entries are not independent sample sizes.

## Source scope

The publication identifiers and derived keyword incidence are included to support the reported analysis. Raw WoS export files, account information and search-interface records are not distributed. OpenAlex metadata and the exact saved search requests are provided separately; generated OpenAlex keywords do not replace author keywords in the networks.

## Checksum maintenance

For a newly assembled local release, create the integrity manifest once before verification:

```text
python src/write_manifest.py
python src/verify_materials.py --check-partitions
```

Users of a published release should verify the supplied manifest rather than replacing it.
