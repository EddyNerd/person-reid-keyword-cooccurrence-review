"""Cached native Sci2 pruning, including its original priority queue tie behavior."""
from contextlib import contextmanager
import hashlib
import json
import math
import os
from pathlib import Path
import subprocess
import tempfile
import zipfile

import networkx as nx

MODULES = ['edu.iu.nwb.preprocessing.extractnodesandedges_0.0.1.jar',
           'edu.iu.nwb.analysis.dichotomize_1.0.0.jar', 'edu.iu.nwb.util_1.2.0.jar',
           'com.google.guava_11.0.1.jar', 'org.cishell.framework_1.0.0.jar',
           'org.cishell.utilities_1.0.2.jar', 'org.eclipse.osgi_3.7.0.v20110613.jar',
           'org.prefuse.lib_20071021.0.0.jar']


def sha(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b''):
            h.update(chunk)
    return h.hexdigest()


@contextmanager
def runtime(plugins, java):
    with tempfile.TemporaryDirectory(prefix='sci2_runtime_') as temp:
        paths = []
        for name in MODULES:
            jar = Path(plugins) / name
            paths.append(str(jar.resolve()))
            with zipfile.ZipFile(jar) as archive:
                for member in archive.namelist():
                    if member.endswith('.jar'):
                        dest = Path(temp) / (name + '_' + Path(member).name)
                        dest.write_bytes(archive.read(member))
                        paths.append(str(dest))
        result = subprocess.run([java, '-XshowSettings:properties', '-version'], capture_output=True, text=True, check=True)
        home = next(line.split('=', 1)[1].strip() for line in result.stderr.splitlines() if 'java.home =' in line)
        nashorn = Path(home) / 'lib/ext/nashorn.jar'
        if not nashorn.is_file():
            raise RuntimeError('Sci2 pruning requires the configured Java 8 runtime')
        paths.append(str(nashorn))
        yield os.pathsep.join(paths)


def count(size, ratio, mode):
    value = size * ratio / 100
    rounded = math.floor(value + .5) if mode == 'half_up' else round(value)
    return min(size, max(1, int(rounded * 100))) if size else 0


class NativeGrid:
    def __init__(self, graph, grid, cfg, input_nwb=None, attribute=None):
        if not cfg.get('retain_isolates') or cfg.get('community_weight_mode') != 'weighted':
            raise ValueError('Native Sci2 alignment requires retain_isolates=true and weighted edges')
        root = Path(__file__).resolve().parents[1]
        text_cfg = json.loads((root / 'sci2_robustness/text_processing.json').read_text(encoding='utf-8'))
        plugins = Path(cfg.get('sci2_plugins', text_cfg['sci2_plugins']))
        java = cfg.get('java', text_cfg.get('java', 'java'))
        self.grid = list(grid)
        script = Path(__file__).with_name('sci2_pruning_grid.js')
        self.provenance = {'modules': {n: sha(plugins / n) for n in MODULES}, 'script': sha(script),
                           'backend': 'sci2_native', 'node_rank': cfg['node_rank'],
                           'input_order': 'Original NWB order' if input_nwb else 'Alphabetical node labels and lexicographic endpoint pairs'}
        if not len(graph):
            raise ValueError('Cannot prune an empty input graph')
        with tempfile.TemporaryDirectory(prefix='sci2_grid_') as temp:
            temp = Path(temp)
            if input_nwb:
                src = Path(input_nwb).resolve()
                self.labels = {int(n): n for n in graph}
                attr = attribute or 'references'
            else:
                labels = sorted(graph, key=str)
                self.labels = {i + 1: n for i, n in enumerate(labels)}
                indices = {n: i for i, n in self.labels.items()}
                src = temp / 'input.nwb'
                metric = cfg['node_rank']
                if metric == 'degree':
                    scores = dict(graph.degree())
                elif metric == 'strength':
                    scores = dict(graph.degree(weight='weight'))
                elif metric.startswith('attribute:'):
                    scores = {n: float(graph.nodes[n][metric.split(':', 1)[1]]) for n in graph}
                else:
                    raise ValueError('Unknown node ranking: ' + metric)
                attr = 'score'
                with src.open('w', encoding='utf-8', newline='\n') as f:
                    f.write('*Nodes\nid*int\tlabel*string\tscore*float\n')
                    for i, n in self.labels.items():
                        f.write(f'{i}\t{json.dumps(str(n), ensure_ascii=False)}\t{scores[n]}\n')
                    f.write('*UndirectedEdges\nsource*int\ttarget*int\tweight*float\n')
                    # Graphs loaded from sorted edge CSVs already preserve this deterministic order.
                    for u, v in sorted((min(indices[u], indices[v]), max(indices[u], indices[v])) for u, v in graph.edges()):
                        f.write(f'{u}\t{v}\t{float(graph[self.labels[u]][self.labels[v]]["weight"])}\n')
            options = {'input': str(src), 'attribute': attr, 'node_rank': cfg['node_rank'],
                       'rounding': cfg['rounding'], 'retain_isolates': True, 'weighted': True,
                       'strict_greater': cfg['strict_greater'], 'n_original': len(graph),
                       'e_original': graph.number_of_edges(), 'requests': [
                           {'id': f'c{i:04d}', 'n_top': count(len(graph), nr, cfg['rounding']), 'er': er, 'tm': tm}
                           for i, (nr, er, tm) in enumerate(self.grid)]}
            self.provenance['input_sha256'] = sha(src)
            key = hashlib.sha256(json.dumps({'options': {k: v for k, v in options.items() if k != 'input'},
                                           'provenance': self.provenance}, sort_keys=True).encode()).hexdigest()
            cache = Path(cfg.get('pruning_cache', root / 'sci2_robustness/cache/pruning'))
            self.folder = cache / key
            self.folder.mkdir(parents=True, exist_ok=True)
            completed = self.folder / 'manifest.json'
            if not completed.exists() or not all((self.folder / f'c{i:04d}.json').exists() for i in range(len(self.grid))):
                options['output'] = str(self.folder.resolve())
                opt = temp / 'options.json'
                opt.write_text(json.dumps(options, ensure_ascii=False), encoding='utf-8')
                with runtime(plugins, java) as cp:
                    result = subprocess.run([java, '-Xmx2g', '-Dfile.encoding=UTF-8', f'-Dgrid.options={opt}',
                                             '-cp', cp, 'jdk.nashorn.tools.Shell', str(script.resolve())],
                                            # Inherit stdout so lengthy calculations show progress.
                                            stderr=subprocess.PIPE, encoding='utf-8', errors='replace')
                    if result.returncode:
                        raise RuntimeError(result.stderr)
                completed.write_text(json.dumps({'provenance': self.provenance, 'parameters': options}, indent=2), encoding='utf-8')
            self.summary = json.loads((self.folder / 'summary.json').read_text(encoding='utf-8'))

    def get(self, index):
        item = json.loads((self.folder / f'c{index:04d}.json').read_text(encoding='utf-8'))
        graph = nx.Graph()
        graph.add_nodes_from(self.labels[int(n)] for n in item['node_ids'])
        graph.add_weighted_edges_from((self.labels[int(u)], self.labels[int(v)], w) for u, v, w in item['edges'])
        return graph, item['stats']
