"""L3 halo and L4 hatch encodings from saved, strictly nested partitions."""
import numpy as np
from scipy import ndimage
from matplotlib.colors import to_rgb
from matplotlib.patches import Ellipse, Rectangle


class HigherHierarchy:
    halo_palette = ['#6fa8dc', '#e6af57', '#ad8ac6', '#63b6a4', '#de8faa',
                    '#a1ae58', '#b59070', '#c76e60', '#8b93a3']
    hatch_palette = ['//', '\\\\', '..', 'xx', '||', '--', '++', 'oo']

    def __init__(self, engine, names, visible):
        self.engine = engine
        self.names = names
        self.visible = visible
        self.cache = {}

    def groups(self, run, level):
        values = run['levels'].get(level)
        if values is None:
            return {}
        return {g: [i for i in self.visible if values[i] == g]
                for g in sorted({values[i] for i in self.visible})}

    def checks(self, field, members):
        region = field >= 0
        outsiders = [i for i in self.visible if i not in set(members)]
        labels, count = ndimage.label(region, structure=np.ones((3, 3)))
        components = {int(labels[self.engine.cell(i)]) for i in members}
        result = {'visible_members': len(members),
                  'member_centres_inside': sum(bool(region[self.engine.cell(i)]) for i in members),
                  'nonmember_centres_inside': sum(bool(region[self.engine.cell(i)]) for i in outsiders),
                  'nonmember_glyph_core_pixels_inside': int((region & self.engine.disks(outsiders, .004)).sum()),
                  'region_components': int(count), 'all_members_connected': len(components) == 1 and 0 not in components}
        assert result['member_centres_inside'] == len(members)
        assert result['nonmember_centres_inside'] == 0
        assert result['nonmember_glyph_core_pixels_inside'] == 0
        assert result['all_members_connected']
        return result

    def prepare(self, run):
        cache_key = run['higher_data']['source_file']
        if cache_key in self.cache:
            return self.cache[cache_key]
        groups = {level: self.groups(run, level) for level in ['L2', 'L3', 'L4']}
        if not groups['L3']:
            result = {'present': False, 'L3': [], 'L4': [], 'fields': {}}
            self.cache[cache_key] = result
            return result
        fields, records = {'L2': {}, 'L3': {}, 'L4': {}}, {'L3': [], 'L4': []}
        for group, members in groups['L2'].items():
            fields['L2'][group] = self.engine.build(members)[0]
        raw = run['higher_data']['raw_levels']
        for level, child_level, raw_index in [('L3', 'L2', 3), ('L4', 'L3', 4)]:
            for group, members in groups[level].items():
                base = self.engine.build(members)[0].copy()
                children = sorted({run['levels'][child_level][i] for i in members})
                for child in children:
                    child_members = groups[child_level][child]
                    assert all(run['levels'][level][i] == group for i in child_members)
                    base = np.maximum(base, fields[child_level][child])
                outsiders = [i for i in self.visible if i not in set(members)]
                exclusion = self.engine.disks(outsiders, .004)
                base[exclusion] = np.minimum(base[exclusion], -.0001)
                check = self.checks(base, members)
                # Exact raster containment: every child enclosure is inside its parent.
                child_contained = all(np.all((fields[child_level][child] < 0) | (base >= 0)) for child in children)
                assert child_contained
                fields[level][group] = base
                all_tokens = [word for word, code in raw[raw_index].items() if code == group]
                full_children = sorted({raw[raw_index-1][word] for word in all_tokens})
                row = {'id': int(group), 'full_members': len(all_tokens),
                       'displayed_tokens': [self.names[i] for i in members],
                       'displayed_children': [int(c) for c in children],
                       'all_children': [int(c) for c in full_children],
                       'child_enclosures_contained': child_contained, **check}
                if level == 'L3':
                    row['halo_colour'] = self.halo_palette[group % len(self.halo_palette)]
                else:
                    row['hatch'] = self.hatch_palette[group % len(self.hatch_palette)]
                records[level].append(row)
        result = {'present': True, **records, 'fields': fields}
        self.cache[cache_key] = result
        return result

    def draw(self, ax, run):
        data = self.prepare(run)
        if not data['present']:
            return {'present': False, 'L3': [], 'L4': []}
        engine = self.engine
        extent = [engine.x[0], engine.x[-1], engine.y[0], engine.y[-1]]
        for row in data['L3']:
            group = row['id']
            field = data['fields']['L3'][group]
            members = self.groups(run, 'L3')[group]
            parents = {run['levels']['L4'][i] for i in members}
            assert len(parents) == 1
            parent = next(iter(parents))
            # The glow is soft within its L4 parent and cannot colour nonmember glyphs.
            alpha = ndimage.gaussian_filter(np.clip(field / .035, 0, 1), sigma=1.0) * .20
            alpha[field < 0] = 0
            alpha[data['fields']['L4'][parent] < 0] = 0
            outsiders = [i for i in self.visible if i not in set(members)]
            alpha[engine.disks(outsiders, .004)] = 0
            rgba = np.zeros(field.shape + (4,))
            rgba[:, :, :3] = to_rgb(row['halo_colour'])
            rgba[:, :, 3] = alpha
            ax.imshow(rgba, origin='lower', extent=extent, interpolation='bilinear', zorder=-2)
        for row in data['L4']:
            field = data['fields']['L4'][row['id']]
            hatch = ax.contourf(engine.x, engine.y, field,
                                levels=[0, field.max() + .001], colors='none',
                                hatches=[row['hatch']], zorder=-1)
            hatch.set_facecolor('none')
            hatch.set_edgecolor((.32, .32, .32, .24))
            hatch.set_linewidth(0)
        return {'present': True, 'L3': data['L3'], 'L4': data['L4']}

    def legend(self, fig, run, left, width):
        data = self.prepare(run)
        if not data['present']:
            fig.text(left + width/2, .041, 'L3 and L4 were not returned for this detection run.',
                     ha='center', va='center', fontsize=8.1, color='#555b60')
            fig.text(left + width/2, .017, 'Node area: document frequency · edge width: co-occurrence frequency.',
                     ha='center', va='center', fontsize=7.6, color='#62676c')
            return
        fw, fh = fig.get_size_inches()
        for level, yy, label in [('L3', .041, 'L3 halos (7/9 visible)'), ('L4', .017, 'L4 hatches (6/8 visible)')]:
            entries = data[level]
            fig.text(left, yy, label, ha='left', va='center', fontsize=7.2, weight='bold', color='#444a4f')
            start = left + width * .275
            span = width * .725
            for index, row in enumerate(entries):
                xx = start + span * index / len(entries)
                if level == 'L3':
                    patch = Ellipse((xx, yy), width=.095/fw, height=.095/fh,
                                    transform=fig.transFigure, facecolor=row['halo_colour'],
                                    edgecolor='none', alpha=.65)
                else:
                    patch = Rectangle((xx-.07/fw, yy-.055/fh), .14/fw, .11/fh,
                                      transform=fig.transFigure, facecolor='white',
                                      edgecolor='#777777', linewidth=.35, hatch=row['hatch'])
                fig.add_artist(patch)
                fig.text(xx + .105/fw, yy, f"{row['id']} ({row['visible_members']})",
                         ha='left', va='center', fontsize=7.2, color='#444a4f')
