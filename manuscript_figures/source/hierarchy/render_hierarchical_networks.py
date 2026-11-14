"""Publication redraw of saved partitions. No community detection is run."""
from pathlib import Path
import sys, json, csv, hashlib, colorsys, math

OUT = Path(__file__).resolve().parent
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patheffects as pe
from matplotlib.collections import LineCollection
from matplotlib.patches import Ellipse, Polygon
from matplotlib.colors import to_rgb, to_hex
from matplotlib.path import Path as MplPath
from scipy.spatial import ConvexHull
from scipy.optimize import linear_sum_assignment
from adjustText import adjust_text
from PIL import Image

SOURCE = OUT / 'inputs'
ARCHIVE = SOURCE / 'historical'
ATLAS = SOURCE / 'x4.js'
data = json.loads(ATLAS.read_text(encoding='utf-8').removeprefix('window.phraseAtlasData=').rstrip(';\n '))
r = data['representations']['tokens']
mask = r['masks']['m10']
visible = mask['nodes']
names = r['nodes']
assert len(visible) == 64 and len(mask['edges']) == 239
assert r['full_nodes'] == 968 and r['full_edges'] == 20771
raw_sources = {}
for treatment, graph_prefix in [('s', '0556cd02a5763dd2'), ('h', '5f468569c6c8918e')]:
    for algorithm in ['lo', 'le']:
        run_key = f'{treatment}_m10_{algorithm}_1000'
        raw_path = SOURCE / f'runs/{graph_prefix}_{algorithm}_1000.json'
        raw = json.loads(raw_path.read_text(encoding='utf-8'))
        run = r['runs'][run_key]
        assert raw['graph_sha256'] == run['graph_sha256']
        for index, level in enumerate(['L0', 'L1', 'L2']):
            if index < len(raw['levels']):
                assert all(raw['levels'][index][names[i]] == run['levels'][level][i] for i in visible)
            else:
                assert run['levels'].get(level) is None
        for index, level in [(3, 'L3'), (4, 'L4')]:
            if index < len(raw['levels']):
                run['levels'][level] = [raw['levels'][index].get(word, -1) for word in names]
                run['counts'][level] = len(set(raw['levels'][index].values()))
            else:
                run['levels'][level] = None
                run['counts'][level] = None
        if run['levels']['L4'] is not None:
            assert all(run['levels']['L4'][i] == run['levels']['FINAL'][i] for i in visible)
        run['higher_data'] = {'source_file': str(raw_path), 'raw_levels': raw['levels']}
        raw_sources[run_key] = {'file': str(raw_path), 'sha256': hashlib.sha256(raw_path.read_bytes()).hexdigest(),
                                'community_counts': [len(set(level.values())) for level in raw['levels']]}
rows = [row for row in csv.DictReader((ARCHIVE / 'tables/visually_supported_memberships.csv').open(encoding='utf-8-sig'))
        if row['period'] == '2023-2024' and row['kind'] == 'cross_sectional']
historical_l0, historical_l1 = {}, {}
for row in rows:
    historical_l0.setdefault(row['l0_key'], {'words': set(), 'colour': row['color_l0'], 'shape': row['shape_l1']})['words'].add(row['word'])
    historical_l1.setdefault(row['l1_id'], {'words': set(), 'shape': row['shape_l1']})['words'].add(row['word'])

# Reuse the exact positions from the preceding verified redraw.
previous = SOURCE / 'positions'
position_rows = list(csv.DictReader((previous / 'node_memberships.csv').open(encoding='utf-8-sig')))
by_word = {row['token']: np.array([float(row['x']), float(row['y'])]) for row in position_rows}
P = {i: by_word[names[i]] for i in visible}
pos = np.array([P[i] for i in visible])
areas = {i: 24 + 1.18 * r['frequencies'][i] for i in visible}
from membership_contours import MembershipContours
contour_engine = MembershipContours(P, areas)
from higher_hierarchy import HigherHierarchy
higher_engine = HigherHierarchy(contour_engine, names, visible)

plt.rcParams.update({'font.family': 'DejaVu Sans', 'font.size': 9,
                     'svg.fonttype': 'none', 'pdf.fonttype': 42,
                     'text.color': '#151515', 'axes.titlecolor': '#151515', 'hatch.linewidth': .35})
markers_extra = ['p', 'h', 'v', '<', '>', 'P', 'X', '8', 'H',
                 (4, 0, 22.5), (5, 0, 36), (7, 0, 0),
                 (3, 0, 90), (3, 0, 270), (5, 1, 18),
                 (6, 1, 0), (7, 1, 0), (8, 1, 0), (4, 1, 0), (4, 1, 45)]

def grouped(run, level):
    vals = run['levels'].get(level)
    if vals is None:
        return {}
    return {g: [i for i in visible if vals[i] == g]
            for g in sorted({vals[i] for i in visible})}

def colour_map(run):
    groups = grouped(run, 'L0')
    refs = list(historical_l0.values())
    assignments = {}
    buckets = {}
    for g, ns in groups.items():
        words = {names[i] for i in ns}
        best = max(range(len(refs)), key=lambda j: (len(words & refs[j]['words']),
                   len(words & refs[j]['words']) / max(1, len(words | refs[j]['words'])), -j))
        base = refs[best]['colour']
        buckets.setdefault(base, []).append((g, len(words & refs[best]['words']), len(ns)))
    # Preserve the original hue for the closest/largest matching fine group;
    # split descendants receive deterministic lightness variants, not false
    # identical memberships. The CSV gives the exact mapping for all groups.
    used = set()
    for base, gs in buckets.items():
        gs.sort(key=lambda x: (-x[1], -x[2], x[0]))
        h, l, s = colorsys.rgb_to_hls(*to_rgb(base))
        for rank, (g, _, _) in enumerate(gs):
            offsets = [0, 0.16, -0.12, 0.27, -0.23, 0.08, -0.06, 0.21, -0.18,
                       0.32, -0.28, 0.12, -0.09, 0.24, -0.21]
            delta = offsets[rank % len(offsets)]
            colour = to_hex(colorsys.hls_to_rgb(h, np.clip(l + delta, .20, .82), s))
            while colour in used:
                h = (h + .012) % 1
                colour = to_hex(colorsys.hls_to_rgb(h, np.clip(l + delta, .20, .82), s))
            assignments[g] = colour
            used.add(colour)
    return assignments

def marker_map(run):
    groups = grouped(run, 'L1')
    gids, refs = list(groups), list(historical_l1.values())
    score = np.array([[len({names[i] for i in groups[g]} & ref['words']) for ref in refs] for g in gids])
    a, b = linear_sum_assignment(-score)
    result = {gids[i]: refs[j]['shape'] for i, j in zip(a, b)}
    extra = iter(markers_extra)
    for g in sorted(groups, key=lambda g: (-len(groups[g]), g)):
        if g not in result:
            result[g] = next(extra)
    assert len(result) == len(groups)
    return result

def hierarchy_info(run):
    l2 = grouped(run, 'L2')
    ranked = sorted(l2, key=lambda g: (-len(l2[g]), g))
    selected = [g for g in ranked if len(l2[g]) >= 5][:5]
    return l2, selected


manifest = {'source_atlas': str(ATLAS), 'atlas_sha256': hashlib.sha256(ATLAS.read_bytes()).hexdigest(),
            'historical_image_url': 'https://github.com/EddyNerd/person-reid-keyword-cooccurrence-review/blob/4ae62e66db177659063ffc3ea14d77c263efe958/figures/cross_sectional_graphs/2023-2024.png',
            'visible_nodes': 64, 'visible_edges': 239, 'seed': 1000, 'multiplier': 1,
            'community_detection_recomputed': False,
            'layout': {'type': 'shared force-directed layout of the 64-node reference display graph',
                       'recomputed_for_readability': False, 'coordinates_reused_from': str(previous / 'node_memberships.csv'), 'seed': 1000, 'edge_attraction': 'cooccurrence_weight ** 0.35',
                       'same_positions_in_all_four_panels': True,
                       'readability_transform': 'partition-independent radial expansion and 0.155-unit minimum-separation relaxation',
                       'does_not_replace_campaign_union_layout': True},
            'L2_display_rule': 'At least 5 displayed nodes and at most 5 parents, ranked by displayed count then saved parent ID. Every selected parent receives a common spatial membership enclosure, constructed from member disks and obstacle-routed connectors. Nonmembers are excluded; disconnected pieces are explicitly recorded if routing cannot connect all members. All 64 nodes and 239 edges remain.',
            'colour_rule': 'Original archive hues matched to current L0 groups by member overlap; deterministic lightness variants distinguish splits. Colours are display correspondences, not evidence of identical membership.',
            'L3_encoding': 'Distinct soft halo colours for all visible L3 parents, containing their exact L2 child enclosures.',
            'L4_encoding': 'Distinct sparse hatches for all visible L4 parents, containing their exact L3 child enclosures.',
            'raw_hierarchy_sources': raw_sources,
            'runs': {}}

all_memberships = []
labels_audit = {}

def draw_key(ax, run, markers, l2, selected):
    ax.set_xlim(0, 1); ax.set_ylim(0, 1); ax.axis('off')
    if not l2:
        ax.text(.5, 1.13, 'No L2 partition returned · FINAL = L1', ha='center', fontsize=9.4,
                color='#43484c', weight='bold', va='top')
        groups = grouped(run, 'L1')
        for j, child in enumerate(groups):
            cx = (j + .5) / len(groups)
            ax.text(cx, .95, f'L1-{child}', ha='center', va='center', fontsize=8.5, weight='bold')
            ax.scatter([cx], [.50], s=130, marker=markers[child], facecolor='#9aa1a6',
                       edgecolor='#202326', linewidth=.6, transform=ax.transAxes, zorder=3)
            ax.text(cx, .02, f'{len(groups[child])}/64 tokens', ha='center', fontsize=8.4)
        ax.text(.5, -.09, 'All five L1 groups are shown; no L2 parent is inferred.',
                ha='center', fontsize=8.1, color='#62676c')
        return
    ax.text(.5, 1.13, 'L2 parents of the largest displayed groups', ha='center', fontsize=9.4, weight='bold', va='top')
    bounds = ax.get_position()
    fw, fh = ax.figure.get_size_inches()
    aspect = bounds.width * fw / (bounds.height * fh)
    n = len(selected)
    for j, parent in enumerate(selected):
        cx = (j + .5) / n
        members = l2[parent]
        children = sorted({run['levels']['L1'][i] for i in members})
        # Parent circles are literal hierarchy keys, not geographic claims.
        ax.add_patch(Ellipse((cx, .50), width=.66 / aspect, height=.66,
                             facecolor='white', edgecolor=contour_engine.colour(j), linestyle=contour_engine.style(j), lw=.9, transform=ax.transAxes))
        offsets = {1: [(0, 0)], 2: [(-.038, 0), (.038, 0)],
                   3: [(-.043, .022), (.043, .022), (0, -.035)],
                   4: [(-.035, .033), (.035, .033), (-.035, -.033), (.035, -.033)],
                   5: [(-.044, .038), (.044, .038), (0, 0), (-.044, -.038), (.044, -.038)]}
        off = offsets.get(len(children), [(math.cos(2*math.pi*k/len(children))*.055, math.sin(2*math.pi*k/len(children))*.055) for k in range(len(children))])
        for child, (dx, dy) in zip(children, off):
            ax.scatter([cx + dx], [.50 + dy * aspect], s=46, marker=markers[child], facecolor='#9aa1a6',
                       edgecolor='#202326', linewidth=.5, transform=ax.transAxes, zorder=3)
        ax.text(cx, .95, f'L2-{parent}', ha='center', va='center', fontsize=8.5, weight='bold', color=contour_engine.colour(j))
        ax.text(cx, .02, f'{len(members)}/64 tokens', ha='center', fontsize=8.4)
    covered = sum(len(l2[g]) for g in selected)
    ax.text(.5, -.09, f'{len(selected)} parent groups shown; {covered}/64 displayed tokens. Smaller groups remain in the network.',
            ha='center', fontsize=8.1, color='#62676c')

def render(algorithm, short, only=None):
    if only:
        fig = plt.figure(figsize=(7.2, 10.0), facecolor='white')
        axes = [fig.add_axes([.045, .235, .91, .575])]
        key_axes = [fig.add_axes([.06, .075, .88, .125])]
        treatments = [only]
    else:
        fig = plt.figure(figsize=(17.4, 11.6), facecolor='white')
        axes = [fig.add_axes([.025, .225, .465, .595]), fig.add_axes([.510, .225, .465, .595])]
        key_axes = [fig.add_axes([.04, .075, .435, .125]), fig.add_axes([.525, .075, .435, .125])]
        treatments = ['s', 'h']
    fig.text(.5, .974, '2023–2024 author-keyword network', ha='center', va='top', fontsize=16 if only else 18, weight='bold')
    fig.text(.5, .939, f'{algorithm}  ·  seed 1000  ·  reference multiplier 1', ha='center', fontsize=11, color='#555b60')
    fig.text(.5, .906, 'L0 fill  ·  L1 shape  ·  L2 contour  ·  L3 halo  ·  L4 hatch', ha='center', fontsize=8.4, color='#555b60')
    for k, treatment in enumerate(treatments):
        key = f'{treatment}_m10_{short}_1000'
        run = r['runs'][key]
        ax = axes[k]
        cm, mm = colour_map(run), marker_map(run)
        l2, selected = hierarchy_info(run)
        upper_record = higher_engine.draw(ax, run)
        enclosure_records = []
        contour_labels = []
        for rank, parent in enumerate(selected):
            info, label = contour_engine.draw(ax, l2[parent], parent, rank)
            enclosure_records.append(info)
            contour_labels.append(label)
        edges = sorted(mask['edges'], key=lambda x: x[2])
        weights = np.array([w for _, _, w in edges])
        ratio = (weights - weights.min()) / max(1, weights.max() - weights.min())
        rgba = np.tile(np.array([.36, .38, .40, 1.]), (len(edges), 1))
        rgba[:, 3] = .10 + .48 * ratio ** .65
        ax.add_collection(LineCollection([[P[u], P[v]] for u, v, w in edges], colors=rgba,
                                         linewidths=.26 + 1.55 * ratio ** .70, zorder=1))
        for group, ns in grouped(run, 'L1').items():
            ax.scatter([P[i][0] for i in ns], [P[i][1] for i in ns], s=[areas[i] for i in ns],
                       c=[cm[run['levels']['L0'][i]] for i in ns], marker=mm[group],
                       edgecolors='#252525', linewidths=.58, alpha=.98, zorder=3)
        texts = []
        for i in visible:
            x, y = P[i]
            t = ax.text(x + .014, y + .016, names[i], fontsize=9.2, fontstyle='italic',
                        ha='left', va='bottom', zorder=6,
                        path_effects=[pe.withStroke(linewidth=2.8, foreground='white', alpha=.94)])
            texts.append(t)
        ax.set_xlim(pos[:, 0].min() - .16, pos[:, 0].max() + .23)
        ax.set_ylim(pos[:, 1].min() - .12, pos[:, 1].max() + .12)
        ax.set_aspect('equal'); ax.axis('off')
        np.random.seed(1000)
        node_texts = list(texts)
        texts.extend(contour_labels)
        adjust_text(texts, x=[P[i][0] for i in visible], y=[P[i][1] for i in visible],
                    target_x=[P[i][0] for i in visible] + [label.get_position()[0] for label in contour_labels],
                    target_y=[P[i][1] for i in visible] + [label.get_position()[1] for label in contour_labels],
                    ax=ax, expand=(1.10, 1.22), force_text=(.18, .25), force_static=(.15, .20),
                    force_pull=(.015, .02), max_move=(8, 8), iter_lim=700,
                    prevent_crossings=True, min_arrow_len=10,
                    arrowprops={'arrowstyle': '-', 'color': '#747b81', 'lw': .40, 'alpha': .60})
        treatment_title = 'A  Filter-and-suppress' if treatment == 's' else 'B  Filter-and-hide'
        graph_text = 'Detection: 64 nodes · 239 edges' if treatment == 's' else 'Detection: 968 nodes · 20,771 edges'
        counts = run['counts']; final_idx = run['FINAL_index']
        hline = f"{counts['L0']} L0 · {counts['L1']} L1 · FINAL = L{final_idx} ({counts['FINAL']} groups)"
        if counts.get('L4') is not None:
            hline = f"{counts['L0']} L0 · {counts['L1']} L1 · {counts['L2']} L2 · {counts['L3']} L3 · {counts['L4']} L4 (FINAL)"
        ax.set_title(treatment_title + '\n' + graph_text + '\n' + hline,
                     fontsize=11.5, weight='bold', pad=15, linespacing=1.5)
        draw_key(key_axes[k], run, mm, l2, selected)
        manifest['runs'][key] = {'counts': counts, 'FINAL_index': final_idx, 'graph_sha256': run['graph_sha256'],
                                'displayed_L0_count': len(cm), 'displayed_L1_count': len(mm),
                                'L0_colour': cm, 'L1_marker': {g: str(v) for g, v in mm.items()},
                                'selected_L2': [{'id': g, 'visible_count': len(l2[g]),
                                                 'tokens': [names[i] for i in l2[g]],
                                                 'L1_children': sorted({run['levels']['L1'][i] for i in l2[g]})} for g in selected],
                                'L2_membership_contours': enclosure_records,
                                'higher_hierarchy': upper_record}
        for i in visible:
            if only:
                continue
            all_memberships.append({'algorithm': algorithm, 'treatment': treatment_title[3:], 'token': names[i],
                                    'document_frequency': r['frequencies'][i], 'L0': run['levels']['L0'][i],
                                    'L1': run['levels']['L1'][i], 'L2': None if not l2 else run['levels']['L2'][i],
                                    'L3': None if run['levels']['L3'] is None else run['levels']['L3'][i],
                                    'L4': None if run['levels']['L4'] is None else run['levels']['L4'][i],
                                    'FINAL': run['levels']['FINAL'][i], 'L0_colour': cm[run['levels']['L0'][i]],
                                    'x': P[i][0], 'y': P[i][1]})
        labels_audit[key] = {names[i]: list(node_texts[n].get_position()) for n, i in enumerate(visible)}
    if only:
        higher_engine.legend(fig, run, .06, .88)
    else:
        higher_engine.legend(fig, r['runs'][f's_m10_{short}_1000'], .04, .435)
        higher_engine.legend(fig, r['runs'][f'h_m10_{short}_1000'], .525, .435)
    stem = f'{algorithm}_2023_2024_L0_L4' + (('_suppress' if only == 's' else '_hide') if only else '')
    for ext in ['png', 'svg', 'pdf']:
        fig.savefig(OUT / f'{stem}.{ext}', dpi=350, facecolor='white')
    # Smaller preview only; the publication PNG and editable SVG retain full size.
    with Image.open(OUT / f'{stem}.png') as im:
        im.thumbnail((2500, 1800))
        im.save(OUT / f'{stem}_preview.png')
    plt.close(fig)

render('Louvain', 'lo')
render('Leiden', 'le')
for alg, short in [('Louvain', 'lo'), ('Leiden', 'le')]:
    for treatment in ['s', 'h']:
        render(alg, short, only=treatment)
(OUT / 'figure_provenance.json').write_text(json.dumps(manifest, indent=2), encoding='utf-8')
(OUT / 'label_positions.json').write_text(json.dumps(labels_audit, indent=2), encoding='utf-8')
with (OUT / 'node_memberships.csv').open('w', encoding='utf-8-sig', newline='') as f:
    writer = csv.DictWriter(f, fieldnames=list(all_memberships[0]))
    writer.writeheader(); writer.writerows(all_memberships)
print(json.dumps({'output': str(OUT), 'figures': ['Louvain_2023_2024_L0_L4', 'Leiden_2023_2024_L0_L4'],
                  'node_rows': len(all_memberships), 'community_detection_recomputed': False}))
