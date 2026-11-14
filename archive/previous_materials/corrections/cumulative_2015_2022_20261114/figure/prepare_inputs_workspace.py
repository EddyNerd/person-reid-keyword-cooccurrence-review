"""Extract portable figure inputs from frozen verified campaign artifacts.

This extraction helper runs in the project workspace. The portable renderer
needs only nodes.csv, edges.csv and labels.csv, not the original WoS exports.
"""
from pathlib import Path
import csv
import hashlib
import json
import sys

HERE = Path(__file__).resolve().parent
ROOT = next(parent for parent in HERE.parents if (parent/'sci2_robustness').is_dir())
WORKSPACE = ROOT.parent.parent
sys.path.insert(0, str(WORKSPACE/'.figuredeps_20261113'))
import numpy as np
from scipy.optimize import linear_sum_assignment
from matplotlib.colors import to_rgb, to_hex
BASE = ROOT/'resultats/Historical_2021_2022_Comparison_Report/test again one ok'
SOURCE = BASE/'correction_cumul_2015_2022_DE_20261110'


def read(path):
    return json.loads(path.read_text(encoding='utf-8'))


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def save(name, value):
    (HERE/name).write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding='utf-8')


def csvwrite(name, rows):
    with (HERE/name).open('w', encoding='utf-8', newline='') as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def main():
    graphfile = SOURCE/'graphs/cumulative_2015-2022_m10.json'
    graph = read(graphfile)
    manifest = read(SOURCE/'run_manifest.json')
    runrow = next(row for row in manifest if row['algorithm'] == 'louvain'
                  and row['treatment'] == 'suppress' and row['seed'] == 1000
                  and row['multiplier'] == 1)
    runfile = SOURCE/runrow['file']
    run = read(runfile)
    assert graph['graph_sha256'] == run['graph_sha256']
    levels = run['levels']
    assert len(levels) == 2
    assert set(levels[0]) == set(graph['nodes']) == set(levels[1])
    oldcasefile = ROOT/'resultats/reproduction_historique_2418_20261104/cases.json'
    old = next(row for row in read(oldcasefile) if row['name'] == 'cumulative_2015-2022')
    oldmember = {node['originallabel'].lower(): old['original_memberships'][node['name']]
                 for node in old['nodes']}
    oldpal = ['#0173B2', '#DE8F05', '#029E73', '#D55E00', '#CC78BC',
              '#CA9161', '#FBAFE4', '#949494', '#ECE133', '#56B4E9']
    # The historical palette cycles after ten colours. The corrected graph has
    # fourteen L0 groups, so add four compatible pastel colours instead of
    # assigning an identical colour to distinct communities.
    pastel = [to_hex(tuple(1-(1-value)*.6 for value in to_rgb(color)))
              for color in oldpal] + ['#7B99C2', '#D7A6AC', '#B5C187', '#AAA4D1']
    assert len(set(pastel)) == 14
    markers = ['o', 's', 'D', '*', '^', 'v', '<', '>']
    styleindex, alignment = [], []
    for level in [0, 1]:
        newgroups = sorted(set(levels[level].values()))
        oldgroups = sorted({value[level] for value in oldmember.values()})
        matrix = np.array([[sum(levels[level].get(word) == new
                               and oldlabels[level] == oldgroup
                               for word, oldlabels in oldmember.items())
                            for oldgroup in oldgroups] for new in newgroups])
        ii, jj = linear_sum_assignment(-matrix)
        matching = {newgroups[int(i)]: int(j) for i, j in zip(ii, jj) if matrix[i, j] > 0}
        nextindex = len(oldgroups)
        for group in newgroups:
            if group not in matching:
                matching[group] = nextindex
                nextindex += 1
        styleindex.append(matching)
        alignment.append({'level': f'L{level}', 'corrected_groups': newgroups,
                          'historical_groups': oldgroups,
                          'overlap_matrix': matrix.tolist(),
                          'display_mapping': matching,
                          'note': 'Display styles only; corrected memberships are never replaced by historical memberships.'})
    layoutfile = SOURCE/'layouts/cumulative_2015-2022.json'
    layout = read(layoutfile)
    assert layout['method']['algorithm'] == 'Installed GUESS com.hp.hpl.guess.layout.GEM'
    nodes = []
    for token in graph['nodes']:
        fine, parent = levels[0][token], levels[1][token]
        x, y = layout['positions'][token]
        nodes.append({'token': token, 'display_label': token.capitalize(),
                      'document_frequency': graph['frequencies'][token],
                      'L0': fine, 'L1': parent, 'FINAL': parent, 'x': x, 'y': y,
                      'color': pastel[styleindex[0][fine]],
                      'marker': markers[styleindex[1][parent]],
                      'area_points2': 3*graph['frequencies'][token]})
    assert len({node['color'] for node in nodes}) == 14
    assert len({node['marker'] for node in nodes}) == 7
    edges = [{'source': u, 'target': v, 'weight': int(weight)}
             for u, v, weight in graph['edges']]
    csvwrite('nodes.csv', nodes)
    csvwrite('edges.csv', edges)
    save('display_alignment.json', alignment)
    hierarchy = []
    for treatment in ['suppress', 'hide']:
        rr = next(row for row in manifest if row['algorithm'] == 'leiden'
                  and row['treatment'] == treatment and row['seed'] == 1000
                  and (row['multiplier'] == 1 or treatment == 'hide'))
        data = read(SOURCE/rr['file'])
        ll = data['levels']
        transitions = []
        for index in range(1, len(ll)):
            children = {}
            for token, group in ll[index-1].items():
                parent = ll[index][token]
                children.setdefault(parent, {}).setdefault(group, []).append(token)
            for group in set(ll[index-1].values()):
                assert len({ll[index][token] for token, previous in ll[index-1].items()
                            if previous == group}) == 1
            transitions.append({'parent_level': f'L{index}', 'parents': [
                {'group': parent, 'children': [
                    {'child_group': child, 'members': sorted(words)}
                    for child, words in sorted(ch.items())]}
                for parent, ch in sorted(children.items())]})
        hierarchy.append({'treatment': treatment, 'algorithm': 'leiden', 'seed': 1000,
                          'levels': [{'level': f'L{i}', 'groups': len(set(part.values()))}
                                     for i, part in enumerate(ll)],
                          'FINAL': f'L{len(ll)-1}', 'FINAL_differs_from_L1': len(ll) > 2,
                          'additional_levels_above_L1': max(0, len(ll)-2),
                          'parent_child_memberships': transitions,
                          'source_file': rr['file'], 'source_sha256': sha(SOURCE/rr['file'])})
    save('leiden_hierarchy_reference.json', hierarchy)
    sourcefiles = [graphfile, runfile, layoutfile,
                   SOURCE/'inputs/full/cumulative_2015-2022.json', oldcasefile,
                   ROOT/'scripts/render_recovered_historical.py']
    provenance = {
        'period': '2015–2022', 'selected_records': 1499,
        'usable_author_keyword_records': 1439, 'source_years': list(range(2015, 2023)),
        'keyword_field': 'DE only', 'titles_abstracts_KeywordsPlus_not_used': True,
        'algorithm': 'Louvain', 'seed': 1000, 'treatment': 'filter-and-suppress',
        'multiplier': 1, 'cutoff': 16, 'operator': '>', 'retained_minimum_integer_weight': 17,
        'nodes': len(nodes), 'edges': len(edges), 'full_nodes': graph['full_nodes'],
        'full_edges': graph['full_edges'],
        'retained_edge_weight': sum(edge['weight'] for edge in edges),
        'full_edge_weight': graph['full_weight'],
        'graph_canonical_sha256': graph['graph_sha256'],
        'groups': {'L0': 14, 'L1': 7, 'FINAL': 'L1'},
        'geometry': {'source': 'Frozen corrected-campaign native GUESS GEM union coordinates',
                     'algorithm': layout['method']['algorithm'],
                     'layout_seed': layout['method']['seed'],
                     'layout_graph_nodes': layout['method']['nodes'],
                     'layout_graph_edges': layout['method']['edges'],
                     'node_coordinates_recomputed': False,
                     'view_only': '91 retained nodes shown with an enlarged viewport; no coordinate optimization or community manipulation',
                     'weighting': layout['method']['weighting'],
                     'guess_jar_sha256': layout['method']['guess_jar_sha256']},
        'design': {'source': 'Archived original plotting code and original GitHub PNG',
                   'original_palette': oldpal, 'cumulative_lightening_factor': .6,
                   'pastel_palette_extended_to_14_distinct_colours': pastel,
                   'node_area': '3 × document frequency in points squared',
                   'colour': 'L0 community; display styles aligned by maximum shared-token overlap',
                   'shape': 'L1 community; display styles aligned by maximum shared-token overlap',
                   'display_alignment_not_membership_identity': True,
                   'label_style': '14pt title-case normalized stems; deterministic repulsion',
                   'edge_width': '1 + 4 × normalized within-graph weight',
                   'edge_alpha': '0.01 + 0.39 × normalized within-graph weight'},
        'historical_input_used_only_for': 'Display code alignment and visual design; never network data or corrected membership',
        'historical_github_path': 'figures/cumulative_graphs/2015–2022.png',
        'sources': [{'path_relative_to_project': path.relative_to(ROOT).as_posix(),
                     'sha256': sha(path)} for path in sourcefiles],
        'Leiden_seed1000_summary': [{key: value for key, value in row.items()
                                    if key != 'parent_child_memberships'} for row in hierarchy]}
    save('provenance.json', provenance)
    print('Prepared', len(nodes), 'nodes,', len(edges), 'edges')
    for row in provenance['Leiden_seed1000_summary']:
        print('Leiden', row['treatment'], row['levels'], 'FINAL =', row['FINAL'])


if __name__ == '__main__':
    main()
