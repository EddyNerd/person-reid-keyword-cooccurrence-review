"""Membership enclosures for fixed positions; no graph or partition changes."""
import heapq
import math
import numpy as np
from scipy import ndimage
from scipy.spatial.distance import cdist
from scipy.sparse.csgraph import minimum_spanning_tree


class MembershipContours:
    colours = ['#546b83', '#967047', '#60816e', '#8d6d8b', '#737373']
    styles = ['solid', (0, (7, 3)), (0, (2, 2)), (0, (7, 2, 1, 2)), (0, (9, 2, 2, 2))]

    def __init__(self, positions, areas):
        self.P = positions
        self.ids = list(positions)
        self.xy = np.array([positions[i] for i in self.ids])
        self.radii = {i: .025 + .0027 * math.sqrt(areas[i]) for i in self.ids}
        self.step = .007
        self.x = np.arange(self.xy[:, 0].min() - .18, self.xy[:, 0].max() + .18, self.step)
        self.y = np.arange(self.xy[:, 1].min() - .18, self.xy[:, 1].max() + .18, self.step)
        self.X, self.Y = np.meshgrid(self.x, self.y)
        self.cache = {}

    def colour(self, rank):
        return self.colours[rank % len(self.colours)]

    def style(self, rank):
        return self.styles[rank % len(self.styles)]

    def cell(self, i):
        x, y = self.P[i]
        return (int(round((y - self.y[0]) / self.step)), int(round((x - self.x[0]) / self.step)))

    def disks(self, ids, padding=0):
        mask = np.zeros(self.X.shape, dtype=bool)
        for i in ids:
            x, y = self.P[i]
            radius = self.radii[i] + padding
            mask |= (self.X - x) ** 2 + (self.Y - y) ** 2 <= radius ** 2
        return mask

    @staticmethod
    def route(start, goal, blocked):
        if blocked[start] or blocked[goal]:
            return None
        height, width = blocked.shape
        diagonal = math.sqrt(2)
        neighbours = [(-1, 0, 1.), (1, 0, 1.), (0, -1, 1.), (0, 1, 1.),
                      (-1, -1, diagonal), (-1, 1, diagonal), (1, -1, diagonal), (1, 1, diagonal)]
        def h(v):
            a, b = abs(v[0] - goal[0]), abs(v[1] - goal[1])
            return max(a, b) + (diagonal - 1) * min(a, b)
        queue = [(h(start), 0., start)]
        scores, parent = {start: 0.}, {}
        while queue:
            _, cost, u = heapq.heappop(queue)
            if u == goal:
                path = [u]
                while u in parent:
                    u = parent[u]
                    path.append(u)
                return path
            if cost > scores.get(u, float('inf')):
                continue
            uy, ux = u
            for dy, dx, step_cost in neighbours:
                vy, vx = uy + dy, ux + dx
                if not (0 <= vy < height and 0 <= vx < width) or blocked[vy, vx]:
                    continue
                if dy and dx and (blocked[uy + dy, ux] or blocked[uy, ux + dx]):
                    continue
                v = (vy, vx)
                candidate = cost + step_cost
                if candidate + 1e-10 < scores.get(v, float('inf')):
                    scores[v] = candidate
                    parent[v] = u
                    heapq.heappush(queue, (candidate + h(v), candidate, v))
        return None

    def build(self, members):
        key = tuple(sorted(members))
        if key in self.cache:
            return self.cache[key]
        member_set = set(members)
        outsiders = [i for i in self.ids if i not in member_set]
        excluded = self.disks(outsiders, padding=.004)
        exclusion_clearance = np.full(self.X.shape, np.inf)
        for i in outsiders:
            x, y = self.P[i]
            clearance = np.sqrt((self.X - x) ** 2 + (self.Y - y) ** 2) - self.radii[i] - .004
            exclusion_clearance = np.minimum(exclusion_clearance, clearance)
        member_disks = self.disks(members, padding=.014)
        xy = np.array([self.P[i] for i in members])
        mst = minimum_spanning_tree(cdist(xy, xy)).tocoo()
        pairs = [(members[a], members[b]) for a, b in zip(mst.row, mst.col)]
        final = None
        for width in [.022, .014, .009]:
            blocked = self.disks(outsiders, padding=width + .011)
            skeleton = np.zeros(self.X.shape, dtype=bool)
            failed = []
            for a, b in pairs:
                path = self.route(self.cell(a), self.cell(b), blocked)
                if path is None:
                    failed.append([a, b])
                    continue
                for py, px in path:
                    skeleton[py, px] = True
            if skeleton.any():
                corridors = ndimage.distance_transform_edt(~skeleton, sampling=self.step) <= width
            else:
                corridors = skeleton
            region = member_disks | corridors
            signed_distance = (ndimage.distance_transform_edt(region) - ndimage.distance_transform_edt(~region)) * self.step
            field = ndimage.gaussian_filter(signed_distance, sigma=1.25)
            field = np.minimum(field, exclusion_clearance - 1e-5)
            region = field >= 0
            components, component_count = ndimage.label(region, structure=np.ones((3, 3)))
            member_components = sorted({int(components[self.cell(i)]) for i in members})
            final = (field, {'member_centres_inside': sum(bool(region[self.cell(i)]) for i in members),
                              'nonmember_centres_inside': sum(bool(region[self.cell(i)]) for i in outsiders),
                              'nonmember_glyph_core_pixels_inside': int((region & excluded).sum()),
                              'member_components': member_components, 'region_components': int(component_count),
                              'corridor_half_width': width, 'unrouted_mst_connections': failed})
            if not failed and len(member_components) == 1 and member_components[0] != 0:
                break
        field, checks = final
        assert checks['member_centres_inside'] == len(members), checks
        assert checks['nonmember_centres_inside'] == 0, checks
        assert checks['nonmember_glyph_core_pixels_inside'] == 0, checks
        checks['all_members_connected'] = len(checks['member_components']) == 1 and checks['member_components'][0] != 0
        self.cache[key] = field, checks
        return self.cache[key]

    def draw(self, ax, members, parent_id, rank):
        field, checks = self.build(members)
        colour, style = self.colour(rank), self.style(rank)
        ax.contourf(self.x, self.y, field, levels=[0, field.max() + .001],
                    colors=[colour], alpha=.035, zorder=.15)
        outline = ax.contour(self.x, self.y, field, levels=[0],
                             colors=[colour], linewidths=.78, linestyles=[style], alpha=.75, zorder=.3)
        boundary = np.vstack([segment for segment in outline.allsegs[0] if len(segment)])
        # Choose an exposed perimeter point, far from the node centres.
        distances = cdist(boundary, self.xy).min(axis=1)
        radius = np.linalg.norm(boundary, axis=1)
        score = distances + .028 * radius
        anchor = boundary[int(np.argmax(score))]
        direction = anchor - np.mean([self.P[i] for i in members], axis=0)
        direction /= max(np.linalg.norm(direction), 1e-8)
        text_xy = anchor + direction * .045
        label = ax.text(*text_xy, f'L2-{parent_id} · {len(members)}', fontsize=8.3,
                        color=colour, weight='bold', ha='center', va='center', zorder=8,
                        bbox={'facecolor': 'white', 'edgecolor': colour, 'linewidth': .5,
                              'boxstyle': 'round,pad=0.25', 'alpha': .96})
        info = {'parent_id': int(parent_id), 'visible_members': len(members),
                'colour': colour, 'line_style': str(style), **checks}
        return info, label
