#!/usr/bin/env python3
"""Reproduce the independent corrected cumulative 2015–2022 audit.

Standard-library-only audit; it never modifies the frozen source release and
does not rerun a community detector. This consolidates the calculations run on
2026-11-14, including the amendment that ignores documentary ``provenance``
when testing reuse of the 18 unaffected hierarchy scopes.

Usage:
    python audit_corrected_campaign.py --base PATH_TO_ACTIVE_OUTPUT_DIRECTORY

The base directory contains ``latest_corrected_campaign.json`` and the dated
analysis folders. The output defaults to this script's directory. No personal
absolute path is embedded. Windows extended-length paths are handled locally.
"""

from __future__ import annotations

import argparse
import csv
import datetime
import hashlib
import io
import json
import math
import os
from collections import Counter, defaultdict
from itertools import combinations
from pathlib import Path


CORRECTED = "correction_cumul_2015_2022_DE_20261110"
BASE_CAMPAIGN = "campagne_complete_mots_cles_auteurs_20261110"
PHRASE_CAMPAIGN = "comparaison_expressions_tokens_20261110"
CASE = "cumulative_2015-2022"


def local_path(path: Path) -> Path:
    """Permit long local Windows paths without changing other platforms."""
    resolved = path.resolve()
    value = str(resolved)
    if os.name == "nt" and not value.startswith("\\\\?\\"):
        return Path("\\\\?\\" + value)
    return resolved


def read(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def edge_map(graph):
    return {tuple(sorted((a, b))): weight for a, b, weight in graph["edges"]}


def incidence_counts(records):
    """One count per distinct token or unordered token pair per publication."""
    frequencies, pair_counts = Counter(), Counter()
    for record in records:
        terms = sorted(set(record["terms"]))
        frequencies.update(terms)
        pair_counts.update(combinations(terms, 2))
    return frequencies, pair_counts


def connected_components(nodes, weighted_edges):
    adjacency = {node: set() for node in nodes}
    for a, b in weighted_edges:
        adjacency[a].add(b)
        adjacency[b].add(a)
    unseen, components = set(nodes), []
    while unseen:
        start = min(unseen)
        stack, members = [start], {start}
        unseen.remove(start)
        while stack:
            for node in adjacency[stack.pop()]:
                if node in unseen:
                    unseen.remove(node)
                    members.add(node)
                    stack.append(node)
        components.append(members)
    return sorted(components, key=lambda members: (-len(members), sorted(members)))


def hierarchy_exports(corrected, run_manifest, reference_nodes):
    rows, examples = [], []
    for item in run_manifest:
        run = read(corrected / item["file"])
        levels = run["levels"]
        row = {
            "treatment": item["treatment"],
            "multiplier": item["multiplier"],
            "algorithm": item["algorithm"],
            "seed": item["seed"],
            "detection_nodes": len(levels[0]),
            "FINAL_level": f"L{len(levels) - 1}",
            "FINAL_groups": len(set(levels[-1].values())),
        }
        for level in range(5):
            row[f"L{level}_groups"] = (
                len(set(levels[level].values())) if level < len(levels) else None
            )
        rows.append(row)
        if item["seed"] != 1000 or not (
            item["treatment"] == "hide" or item["multiplier"] == 1
        ):
            continue
        example = {**row, "levels": []}
        for index, partition in enumerate(levels):
            groups = []
            for group_id in sorted(set(partition.values())):
                members = sorted(n for n in partition if partition[n] == group_id)
                group = {
                    "group": group_id,
                    "full_size": len(members),
                    "members": members,
                    "reference_visible_members": [
                        node for node in members if node in reference_nodes
                    ],
                }
                if index:
                    previous = levels[index - 1]
                    group["children"] = [
                        {
                            "group": child,
                            "full_size": sum(g == child for g in previous.values()),
                            "members": sorted(n for n in previous if previous[n] == child),
                        }
                        for child in sorted({previous[n] for n in members})
                    ]
                groups.append(group)
            example["levels"].append({"level": f"L{index}", "groups": groups})
        examples.append(example)
    return rows, examples


def audit(base: Path):
    corrected = base / CORRECTED
    manifest = read(corrected / "artifact_manifest.json")
    missing, mismatched = [], []
    for relative, metadata in manifest["files"].items():
        path = corrected / relative
        if not path.exists():
            missing.append(relative)
        elif sha256(path) != metadata["sha256"]:
            mismatched.append(relative)

    records = read(corrected / f"inputs/terms/{CASE}.json")
    source_records = read(corrected / "inputs/source_exports/records_2015_2022.json")
    source_by_ut = {record["UT"]: record for record in source_records}
    full = read(corrected / f"inputs/full/{CASE}.json")
    reference = read(corrected / f"graphs/{CASE}_m10.json")
    frequencies, pair_counts = incidence_counts(records)
    cross_sectional_records = []
    for period in ("2015-2016", "2017-2018", "2019-2020", "2021-2022"):
        cross_sectional_records += read(
            base / BASE_CAMPAIGN / f"inputs/terms/cross_sectional_{period}.json"
        )
    by_ut = {record["UT"]: record for record in records}
    checks = {
        "all_records_within_2015_2022": all(2015 <= r["year"] <= 2022 for r in records),
        "cross_sectional_union_exact": by_ut == {
            r["UT"]: r for r in cross_sectional_records
        },
        "full_frequency_matrix_matches_source_records": dict(frequencies) == full["frequencies"],
        "full_edge_matrix_matches_source_records": dict(pair_counts) == edge_map(full),
        "normalized_record_DE_and_final_year_match_raw_export": all(
            r["UT"] in source_by_ut
            and source_by_ut[r["UT"]].get("DE", "") == r["DE"]
            and int(source_by_ut[r["UT"]]["PY"]) == r["year"]
            for r in records
        ),
        "healthcare_exclusion_preserved": "WOS:000450332600002" not in source_by_ut,
    }
    native = read(corrected / f"inputs/native/{CASE}.json")
    labels = native["word_labels"]
    candidate_edges = {
        tuple(sorted((labels[str(a)], labels[str(b)]))): weight
        for a, b, weight in native["output"]["edges"]
    }
    candidate_nodes = {labels[str(n)] for n in native["output"]["node_ids"]}
    mean_weight = sum(candidate_edges.values()) / len(candidate_edges)
    tau = mean_weight * math.log10(len(candidate_nodes))
    mask_checks, masks = [], {}
    for code in ("m04", "m06", "m08", "m10", "m12", "m14", "m16"):
        graph = read(corrected / f"graphs/{CASE}_{code}.json")
        masks[graph["multiplier"]] = graph
        passing = {ab: w for ab, w in candidate_edges.items() if w > graph["scaled_cutoff"]}
        passing_nodes = {n for pair in passing for n in pair}
        components = connected_components(passing_nodes, passing)
        kept_nodes = components[0] if components else set()
        expected = {
            ab: w for ab, w in passing.items() if ab[0] in kept_nodes and ab[1] in kept_nodes
        }
        mask_checks.append({
            "multiplier": graph["multiplier"], "nodes": len(graph["nodes"]),
            "edges": len(graph["edges"]), "cutoff": graph["scaled_cutoff"],
            "exact_candidate_rule_reconstruction": set(graph["nodes"]) == kept_nodes
            and edge_map(graph) == expected,
            "graph_sha256": graph["graph_sha256"],
        })

    run_manifest = read(corrected / "run_manifest.json")
    output_checks, seed1000 = [], []
    for item in run_manifest:
        run = read(corrected / item["file"])
        graph = full if item["treatment"] == "hide" else masks[item["multiplier"]]
        nodes = set(graph["nodes"])
        coverage = all(set(partition) == nodes for partition in run["levels"])
        nested = True
        for child, parent in zip(run["levels"][:-1], run["levels"][1:]):
            parents = defaultdict(set)
            for node, child_id in child.items():
                parents[child_id].add(parent[node])
            nested &= all(len(parent_ids) == 1 for parent_ids in parents.values())
        output_checks.append(
            coverage and nested and run["graph_sha256"] == graph["graph_sha256"]
            and run["algorithm"] == item["algorithm"] and run["seed"] == item["seed"]
        )
        if item["seed"] == 1000 and (
            item["treatment"] == "hide" or item["multiplier"] == 1
        ):
            seed1000.append({
                "treatment": item["treatment"], "algorithm": item["algorithm"],
                "community_counts": [len(set(p.values())) for p in run["levels"]],
                "FINAL_level": len(run["levels"]) - 1,
                "file": item["file"], "file_sha256": sha256(corrected / item["file"]),
            })

    def substantive(hierarchy):
        return {key: value for key, value in hierarchy.items() if key != "provenance"}

    old_hierarchies = read(base / "hierarchies_stables_20261110/hierarchies.json")
    new_hierarchies = read(corrected / "hierarchies.json")
    old_map = {(h["case"], h["algorithm"]): substantive(h) for h in old_hierarchies}
    new_map = {(h["case"], h["algorithm"]): substantive(h) for h in new_hierarchies}
    unchanged = [key for key in old_map if old_map[key] == new_map[key]]
    changed = [key for key in old_map if old_map[key] != new_map[key]]

    tnp = {}
    phrase_root = base / PHRASE_CAMPAIGN
    for representation in ("tokens", "phrases_normalized", "phrases"):
        terms_path = phrase_root / representation / f"inputs/terms/{CASE}.json"
        graph_path = phrase_root / representation / f"inputs/full/{CASE}.json"
        rows, graph = read(terms_path), read(graph_path)
        term_counts, edge_counts = incidence_counts(rows)
        tnp[representation] = {
            "records": len(rows),
            "same_UTs_and_DE_and_years_as_corrected": {
                r["UT"]: (r["year"], r["DE"]) for r in rows
            } == {r["UT"]: (r["year"], r["DE"]) for r in records},
            "matrix_exact": dict(term_counts) == graph["frequencies"]
            and dict(edge_counts) == edge_map(graph),
            "nodes": len(graph["nodes"]), "edges": len(graph["edges"]),
            "graph_sha256": graph["graph_sha256"], "full_file_sha256": sha256(graph_path),
        }
    downstream = {}
    for name in (
        "prevalence_statistiques_comparables_DE_20261111",
        "correspondance_temporelle_DE_20261111",
    ):
        input_manifest = read(base / name / "input_manifest.json")
        entries = [entry for entry in input_manifest if CORRECTED in entry["path"]]
        bad = []
        for entry in entries:
            relative = entry["path"].split(CORRECTED)[1].replace("\\", "/").lstrip("/")
            path = corrected / relative
            if not path.exists() or sha256(path) != entry["sha256"]:
                bad.append(relative)
        downstream[name] = {
            "corrected_inputs_in_manifest": len(entries),
            "corrected_input_hash_mismatches": bad,
        }

    old_new_summary = read(corrected / "old_versus_corrected_summary.json")
    result = {
        "created_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "scope": "Independent audit of frozen corrected 2015–2022 campaign; no detector reruns and no alteration of earlier artifacts",
        "checks": checks,
        "artifact_integrity": {
            "manifest_sha256": sha256(corrected / "artifact_manifest.json"),
            "expected_pointer_sha256": read(base / "latest_corrected_campaign.json")["manifest_sha256"],
            "files_checked": len(manifest["files"]), "missing": missing, "mismatched": mismatched,
        },
        "corpus": {
            "records": len(records), "unique_UTs": len(by_ut),
            "usable_records": sum(bool(r["terms"]) for r in records),
            "years": dict(sorted(Counter(r["year"] for r in records).items())),
            "source_export_records": len(source_records),
            "added_2015_2018": sum(r["year"] <= 2018 for r in records),
            "source_terms_file_sha256": sha256(corrected / f"inputs/terms/{CASE}.json"),
            "source_export_file_sha256": sha256(corrected / "inputs/source_exports/records_2015_2022.json"),
        },
        "full_graph": {
            "nodes": len(full["nodes"]), "edges": len(full["edges"]),
            "total_edge_weight": sum(w for a, b, w in full["edges"]),
            "graph_sha256": full["graph_sha256"],
            "file_sha256": sha256(corrected / f"inputs/full/{CASE}.json"),
        },
        "preselection": {
            "nodes": len(candidate_nodes), "edges": len(candidate_edges),
            "mean_edge_weight": mean_weight, "computed_tau": tau,
            "recorded_tau": reference["formula_tau"],
            "reference_cutoff": reference["effective_reference_cutoff"],
            "comparator": reference["comparator"],
        },
        "mask_checks": mask_checks,
        "detector_outputs": {
            "unique_outputs": len(run_manifest),
            "all_graph_hashes_coverage_and_nesting_match": all(output_checks),
            "failed_outputs": [run_manifest[i] for i, okay in enumerate(output_checks) if not okay],
            "group_sizes": {str(k): v for k, v in Counter(
                (r["treatment"], r["multiplier"], r["algorithm"]) for r in run_manifest
            ).items()},
            "seed1000": seed1000,
        },
        "hierarchy_scope_reuse": {
            "ignored_metadata_field": "provenance",
            "unchanged_count": len(unchanged), "unchanged": unchanged,
            "changed_count": len(changed), "changed": changed,
        },
        "TNP": tnp,
        "reference_graph": {
            "nodes": len(reference["nodes"]), "edges": len(reference["edges"]),
            "total_weight": sum(w for a, b, w in reference["edges"]),
            "weight_fraction": sum(w for a, b, w in reference["edges"])
            / sum(w for a, b, w in full["edges"]),
            "file_sha256": sha256(corrected / f"graphs/{CASE}_m10.json"),
            "graph_sha256": reference["graph_sha256"],
        },
        "current_downstream_provenance": downstream,
        "legacy_outputs_notice": "Pre-correction folders remain archival evidence; their cumulative_2015-2022 entries cover 2019–2022. Current 2015–2022 scientific results require the corrected window override. Latest normalized statistics, corrected hierarchies, T/N/P and temporal correspondence use the corrected cohort.",
        "old_versus_corrected_reference_L1": [
            row for row in old_new_summary if row["multiplier"] == 1 and row["level"] == "L1"
        ],
        "old_versus_corrected_reference_summary_sha256": sha256(corrected / "old_versus_corrected_summary.json"),
    }
    result["all_independent_checks_passed"] = (
        not missing and not mismatched
        and result["artifact_integrity"]["manifest_sha256"]
        == result["artifact_integrity"]["expected_pointer_sha256"]
        and all(checks.values())
        and all(row["exact_candidate_rule_reconstruction"] for row in mask_checks)
        and all(output_checks) and len(unchanged) == 18 and len(changed) == 2
        and all(row["same_UTs_and_DE_and_years_as_corrected"] and row["matrix_exact"] for row in tnp.values())
        and all(not row["corrected_input_hash_mismatches"] for row in downstream.values())
    )
    hierarchy_rows, hierarchy_examples = hierarchy_exports(
        corrected, run_manifest, set(reference["nodes"])
    )
    return result, hierarchy_rows, hierarchy_examples


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base", required=True, type=Path)
    parser.add_argument("--output", type=Path, default=Path(__file__).parent)
    args = parser.parse_args()
    base, output = local_path(args.base), local_path(args.output)
    output.mkdir(parents=True, exist_ok=True)
    result, rows, examples = audit(base)
    (output / "independent_corrected_campaign_audit.json").write_text(
        json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    buffer = io.StringIO(newline="")
    writer = csv.DictWriter(buffer, fieldnames=list(rows[0]))
    writer.writeheader()
    writer.writerows(rows)
    (output / "corrected_hierarchy_counts_all_480_runs.csv").write_text(
        buffer.getvalue(), encoding="utf-8-sig"
    )
    (output / "corrected_seed1000_parent_child_memberships.json").write_text(
        json.dumps(examples, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(json.dumps({
        "all_independent_checks_passed": result["all_independent_checks_passed"],
        "records": result["corpus"]["records"],
        "unique_detector_outputs": result["detector_outputs"]["unique_outputs"],
    }))
    raise SystemExit(0 if result["all_independent_checks_passed"] else 1)


if __name__ == "__main__":
    main()
