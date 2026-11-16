"""Place additional nodes with an anchored extension of GEM's arrangement phase.

This is a pure-Python, floating-point constrained extension, NOT an unmodified
Sci2/GUESS GEM execution. The force terms and adaptive local-temperature update
were transcribed from com.hp.hpl.guess.layout.GEM.a_round/displace in the locally
installed guess.jar, using tmp/guess_layout_runtime/GEM_bytecode.txt as evidence.
Native GEM ignores fixed nodes and rescales all coordinates; those behaviours
are deliberately replaced here by immutable anchors and no final rescaling.

Only the requested movable nodes are initialized or displaced. All other input
coordinate values are copied verbatim to the result. Adjacency is unweighted,
as in GUESS GEM; scientific edge weights and community assignments are unused.
The caller may specify GEM's characteristic length in the archived coordinate
system; otherwise the median anchored-edge length is used. Native dimensionless arrangement coefficients are
retained. Native integer rounding is replaced by floating-point arithmetic.

API: result, metadata = place_new_nodes(positions, edges, seed=1000)
Input positions: {node: [x,y]} for the fixed nodes (new nodes may be absent).
Input edges: iterable of (source,target) or (source,target,weight).
No files are read or written and no community analysis is performed.
"""

from math import cos, sin, hypot, isfinite, pi, sqrt
from statistics import median


class _JavaRandom:
    """java.util.Random nextDouble, also used by the native GEM rand()."""

    def __init__(self, seed):
        self.state = (int(seed) ^ 0x5DEECE66D) & ((1 << 48) - 1)

    def _next(self, bits):
        self.state = (self.state * 0x5DEECE66D + 11) & ((1 << 48) - 1)
        return self.state >> (48 - bits)

    def random(self):
        return ((self._next(26) << 27) + self._next(27)) / float(1 << 53)

    def rand(self):
        return int(self.random() * 2147483647)


def place_new_nodes(positions: dict, edges: list, movable=('modul', 'structur'),
                    seed=1000, max_rounds=1000, characteristic_length=None):
    """Return all positions and an audit; only ``movable`` may be changed.

    One round displaces each movable node once in seeded randomized order.
    Early stopping uses GEM's final-temperature criterion, calculated only
    over movable nodes. Otherwise max_rounds provides a deterministic cap.
    Existing positions of movable nodes are ignored: initialization always
    uses their anchored neighbours and a seeded offset for reproducibility.
    """
    movable = tuple(sorted(set(movable)))
    if not movable:
        raise ValueError('At least one movable node is required')
    if not isinstance(max_rounds, int) or max_rounds < 1:
        raise ValueError('max_rounds must be a positive integer')
    edge_pairs = sorted({tuple(sorted((str(e[0]), str(e[1]))))
                         for e in edges if str(e[0]) != str(e[1])})
    anchors = {str(n): p for n, p in positions.items() if str(n) not in movable}
    if not anchors:
        raise ValueError('At least one immutable anchor is required')
    for n, p in anchors.items():
        if len(p) != 2 or not all(isfinite(float(x)) for x in p):
            raise ValueError('Invalid anchor coordinates: ' + n)
    nodes = sorted(set(anchors) | set(movable))
    node_set = set(nodes)
    if any(u not in node_set or v not in node_set for u, v in edge_pairs):
        raise ValueError('An edge endpoint has neither an anchor nor a movable node')
    adjacency = {n: set() for n in nodes}
    for u, v in edge_pairs:
        adjacency[u].add(v)
        adjacency[v].add(u)
    old_lengths = [hypot(float(anchors[u][0]) - float(anchors[v][0]),
                         float(anchors[u][1]) - float(anchors[v][1]))
                   for u, v in edge_pairs if u in anchors and v in anchors]
    old_lengths = [v for v in old_lengths if v > 0]
    if not old_lengths:
        raise ValueError('Cannot derive GEM scale: no positive anchored-edge lengths')
    elen = median(old_lengths) if characteristic_length is None else float(characteristic_length)
    if not isfinite(elen) or elen <= 0:
        raise ValueError('The characteristic length must be finite and positive')
    elensqr = elen * elen
    rng = _JavaRandom(seed)
    xy = {n: [float(anchors[n][0]), float(anchors[n][1])] for n in anchors}
    anchor_center = [sum(p[k] for p in xy.values()) / len(xy) for k in (0, 1)]
    initial = {}
    initialization_neighbors = {}
    for n in movable:
        neighbours = sorted(adjacency[n] & set(anchors))
        initialization_neighbors[n] = neighbours
        center = ([sum(xy[v][k] for v in neighbours) / len(neighbours)
                   for k in (0, 1)] if neighbours else anchor_center)
        angle = 2 * pi * rng.random()
        xy[n] = [center[0] + 0.2 * elen * cos(angle),
                 center[1] + 0.2 * elen * sin(angle)]
        initial[n] = xy[n][:]
    mass = {n: 1.0 + len(adjacency[n]) / 3.0 for n in movable}
    heat = {n: elen for n in movable}
    previous = {n: (0.0, 0.0) for n in movable}
    direction = {n: 0.0 for n in movable}
    # Native a_* defaults: shake .3, gravity .1, oscillation .4,
    # rotation .9, starttemp 1, maxtemp 1.5, finaltemp .02.
    shake, gravity, oscillation, rotation = 0.3, 0.1, 0.4, 0.9
    maxtemp, mintemp, finaltemp = 1.5 * elen, elen / 64.0, 0.02 * elen
    n_total = len(nodes)
    updates = 0
    stop = 'maximum_rounds'
    rounds = 0
    for rounds in range(1, max_rounds + 1):
        # Without-replacement selection, adapted to movable nodes only.
        order = list(movable)
        for remaining in range(len(order), 1, -1):
            i = rng.rand() % remaining
            order[i], order[remaining - 1] = order[remaining - 1], order[i]
        for n in order:
            x, y = xy[n]
            centroid = [sum(xy[v][k] for v in nodes) / n_total for k in (0, 1)]
            ix = (2.0 * rng.random() - 1.0) * shake * elen
            iy = (2.0 * rng.random() - 1.0) * shake * elen
            ix += (centroid[0] - x) * mass[n] * gravity
            iy += (centroid[1] - y) * mass[n] * gravity
            for v in nodes:
                if v == n:
                    continue
                dx, dy = x - xy[v][0], y - xy[v][1]
                r2 = dx * dx + dy * dy
                if r2 > 0:
                    ix += dx * elensqr / r2
                    iy += dy * elensqr / r2
            for v in sorted(adjacency[n]):
                dx, dy = x - xy[v][0], y - xy[v][1]
                attraction = min((dx * dx + dy * dy) / mass[n],
                                 64.0 * elensqr) / elensqr
                ix -= dx * attraction
                iy -= dy * attraction
            norm = hypot(ix, iy)
            updates += 1
            if norm == 0:
                continue
            t = heat[n]
            dx, dy = ix * t / norm, iy * t / norm
            xy[n][0] += dx
            xy[n][1] += dy
            px, py = previous[n]
            denom = t * hypot(px, py)
            if denom > 0:
                new_heat = min(t + t * oscillation * (dx * px + dy * py) / denom,
                               maxtemp)
                direction[n] += rotation * (dx * py - dy * px) / denom
                new_heat -= new_heat * abs(direction[n]) / n_total
                heat[n] = max(new_heat, mintemp)
            previous[n] = (dx, dy)
        if sum(t * t for t in heat.values()) <= len(movable) * finaltemp ** 2:
            stop = 'movable_temperature_below_GEM_arrangement_threshold'
            break
    # Copy anchor VALUES verbatim, not xy's floating-point work copies.
    result = {n: [p[0], p[1]] for n, p in anchors.items()}
    result.update({n: xy[n][:] for n in movable})
    unchanged = all(result[n][0] == p[0] and result[n][1] == p[1]
                    for n, p in anchors.items())
    if not unchanged or not all(isfinite(c) for n in movable for c in result[n]):
        raise ArithmeticError('Anchor preservation or finite-coordinate verification failed')
    metadata = {
        'method': 'Pure-Python fixed-anchor extension of GUESS GEM arrangement',
        'unmodified_native_GEM': False,
        'native_evidence': 'tmp/guess_layout_runtime/GEM_bytecode.txt: a_round/displace',
        'seed': int(seed), 'rng': 'java.util.Random nextDouble reimplementation',
        'fixed_nodes': len(anchors), 'movable_nodes': list(movable),
        'nodes': n_total, 'edges': len(edge_pairs), 'weighted_forces': False,
        'characteristic_length': elen,
        'characteristic_length_rule': ('median positive fixed-to-fixed edge length' if characteristic_length is None else 'Explicit archived-coordinate characteristic length: native ELEN 128 times final rescaling factor 0.25 = 32'),
        'initial_positions': initial,
        'initialization_neighbors': initialization_neighbors,
        'initialization': 'anchored-neighbour barycentre plus seeded 0.2*ELEN offset',
        'arrangement_coefficients': {'starttemp': 1.0, 'maxtemp': 1.5,
                                    'finaltemp': 0.02, 'shake': shake,
                                    'gravity': gravity, 'oscillation': oscillation,
                                    'rotation': rotation},
        'rounds': rounds, 'displacement_attempts': updates,
        'maximum_rounds': max_rounds, 'stop_reason': stop,
        'final_local_temperature': heat,
        'final_movable_temperature': sqrt(sum(t*t for t in heat.values())),
        'all_input_anchor_values_unchanged': unchanged,
        'post_layout_rescaling': False,
        'native_differences': [
            'Only new nodes are initialized or displaced; anchors enter every force calculation.',
            'Characteristic length follows the archived coordinate scale.',
            'Floating-point arithmetic replaces native integer/float rounding.',
            'Stopping and shuffled selection concern movable nodes only.',
            'No insertion/optimization stages or final whole-graph rescaling.',
        ],
        'community_detection_or_partition_changes': False,
    }
    return result, metadata
