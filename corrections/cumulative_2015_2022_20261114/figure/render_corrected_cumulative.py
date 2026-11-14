"""Render the corrected 2015–2022 reference figure from portable CSV inputs.

Run with Python 3 and matplotlib, numpy, adjustText installed:
    python render_corrected_cumulative.py
The fixed native GUESS GEM coordinates and saved Louvain memberships are inputs,
not estimated by this plotting script. Existing label coordinates are reused.
"""
from pathlib import Path
import csv
import json
import os
import sys

HERE = Path(__file__).resolve().parent
# Optional dependency directory in the working machine; not needed elsewhere.
cache_dir = HERE / '.matplotlib-cache'
for parent in HERE.parents:
    candidate = parent / '.figuredeps_20261113'
    if candidate.is_dir():
        sys.path.insert(0, str(candidate))
        cache_dir = parent / '.matplotlib_corrected_graph'
        break
cache_dir.mkdir(parents=True, exist_ok=True)
os.environ.setdefault('MPLCONFIGDIR', str(cache_dir))
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.colors import to_rgb
from matplotlib.lines import Line2D
import numpy as np


def read_csv(name):
    with (HERE / name).open(encoding='utf-8-sig', newline='') as handle:
        return list(csv.DictReader(handle))


def main():
    nodes = read_csv('nodes.csv')
    edges = read_csv('edges.csv')
    by = {node['token']: node for node in nodes}
    pos = {node['token']: (float(node['x']), float(node['y'])) for node in nodes}
    assert len(nodes) == 91 and len(edges) == 434
    assert all(int(edge['weight']) > 16 for edge in edges)
    assert len({node['L0'] for node in nodes}) == 14
    assert len({node['L1'] for node in nodes}) == 7
    plt.rcParams.update({'font.family': 'DejaVu Sans', 'svg.fonttype': 'none',
                         'pdf.fonttype': 42, 'axes.unicode_minus': False})
    fig = plt.figure(figsize=(15, 15), facecolor='white')
    ax = fig.add_axes([.025, .025, .95, .95])
    xy = np.array(list(pos.values()))
    center = (xy.max(axis=0) + xy.min(axis=0)) / 2
    half = float(np.ptp(xy, axis=0).max()) / 2 * 1.08
    ax.set_xlim(center[0]-half, center[0]+half)
    ax.set_ylim(center[1]-half, center[1]+half)
    ax.set_aspect('equal')
    ax.axis('off')
    low = min(int(edge['weight']) for edge in edges)
    high = max(int(edge['weight']) for edge in edges)
    for edge in edges:
        fraction = (int(edge['weight']) - low) / (high-low)
        p, q = pos[edge['source']], pos[edge['target']]
        ax.plot([p[0], q[0]], [p[1], q[1]], color='black',
                linewidth=1+4*fraction, alpha=.01+.39*fraction, zorder=1)
    for marker in dict.fromkeys(node['marker'] for node in nodes):
        group = [node for node in nodes if node['marker'] == marker]
        ax.scatter([float(node['x']) for node in group],
                   [float(node['y']) for node in group],
                   s=[3*int(node['document_frequency']) for node in group],
                   c=[node['color'] for node in group], marker=marker,
                   edgecolors='black', linewidths=.5, alpha=.95, zorder=2)
    frozen = HERE / 'labels.csv'
    label_xy = ({row['token']: (float(row['label_x']), float(row['label_y']))
                 for row in read_csv('labels.csv')}
                if frozen.exists() and '--reflow-labels' not in sys.argv else {})
    texts = []
    for node in nodes:
        token = node['token']
        x, y = label_xy.get(token, pos[token])
        color = tuple(value*.35 for value in to_rgb(node['color']))
        texts.append(ax.text(x, y, node['display_label'], fontsize=14,
                             ha='center', va='center', color=color, zorder=4,
                             bbox=dict(facecolor='white', edgecolor='none',
                                       alpha=.35, pad=.12)))
    if not label_xy:
        from adjustText import adjust_text
        np.random.seed(20261114)
        adjust_text(texts, x=xy[:, 0], y=xy[:, 1], ax=ax,
                    expand=(1.17, 1.32), force_text=(.16, .28),
                    force_static=(.12, .2), force_pull=(.008, .008),
                    ensure_inside_axes=True, iter_lim=700)
        with frozen.open('w', encoding='utf-8', newline='') as handle:
            writer = csv.writer(handle)
            writer.writerow(['token', 'label_x', 'label_y'])
            for node, text in zip(nodes, texts):
                writer.writerow([node['token'], *text.get_position()])
    leaders = 0
    for node, text in zip(nodes, texts):
        x, y = pos[node['token']]
        tx, ty = text.get_position()
        if np.hypot(tx-x, ty-y) / (2*half) > .012:
            ax.plot([x, tx], [y, ty], color='#7c8790', linewidth=.3,
                    alpha=.7, zorder=3)
            leaders += 1
    fig.canvas.draw()
    renderer = fig.canvas.get_renderer()
    boxes = [text.get_window_extent(renderer).expanded(1.01, 1.02)
             for text in texts]
    overlaps = [[nodes[i]['token'], nodes[j]['token']]
                for i in range(len(boxes)) for j in range(i+1, len(boxes))
                if boxes[i].overlaps(boxes[j])]
    bounds = ax.get_window_extent(renderer)
    clipped = [nodes[i]['token'] for i, box in enumerate(boxes)
               if not (bounds.contains(box.x0, box.y0)
                       and bounds.contains(box.x1, box.y1))]
    for extension in ['png', 'svg', 'pdf']:
        kwargs = {'metadata': {'Creator': 'Corrected cumulative 2015–2022 renderer'}}
        if extension == 'png':
            kwargs = {'dpi': 240, 'metadata': {'Description':
                'Corrected full 2015–2022 cumulative author-keyword network; '
                '1499 records; Louvain seed1000; filter-and-suppress; cutoff>16'}}
        fig.savefig(HERE / ('2015–2022.'+extension), facecolor='white', **kwargs)
    fig.savefig(HERE/'preview.png', dpi=80, facecolor='white')
    plt.close(fig)
    qa = {'visible_nodes': len(nodes), 'visible_edges': len(edges),
          'all_91_labels_present': len(texts) == 91,
          'overlapping_label_pairs': overlaps, 'clipped_labels': clipped,
          'leader_lines': leaders, 'font_points': 14,
          'canvas_inches': [15, 15], 'PNG_pixels': [3600, 3600],
          'edge_weight_sum': sum(int(row['weight']) for row in edges),
          'L0_groups': 14, 'L1_groups': 7, 'FINAL': 'L1',
          'native_GEM_node_positions_reused': True,
          'label_positions_frozen': True}
    (HERE/'render_checks.json').write_text(json.dumps(qa, indent=2), encoding='utf-8')
    # A separate key preserves the sparse appearance of the historical figure.
    fig, ax = plt.subplots(figsize=(11, 8))
    ax.axis('off')
    group_rows = []
    for fine in sorted({int(node['L0']) for node in nodes}):
        members = [node for node in nodes if int(node['L0']) == fine]
        row = members[0]
        group_rows.append((row, ', '.join(node['token'] for node in members)))
    for j, (row, words) in enumerate(group_rows):
        y = .94-j*.063
        ax.scatter([.025], [y], s=145, marker=row['marker'], color=row['color'],
                   edgecolors='black', linewidths=.5)
        ax.text(.065, y, f"L0 {row['L0']} / L1 {row['L1']}: {words}",
                fontsize=8.3, va='center', wrap=True)
    ax.set_xlim(0, 1.02); ax.set_ylim(0, 1)
    for ext in ['png', 'svg', 'pdf']:
        fig.savefig(HERE/f'community_key.{ext}', dpi=170, facecolor='white',
                    bbox_inches='tight')
    plt.close(fig)
    print(json.dumps(qa, indent=2))


if __name__ == '__main__':
    main()
