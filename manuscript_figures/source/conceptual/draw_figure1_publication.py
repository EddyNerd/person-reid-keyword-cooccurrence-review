"""Publication figure: identity coverage in closed- and open-set Re-ID."""
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Ellipse

OUT = Path(__file__).resolve().parent
plt.rcParams.update({
    'font.family': 'serif', 'font.serif': ['Times New Roman', 'DejaVu Serif'],
    'font.size': 10, 'mathtext.fontset': 'stix',
    'svg.fonttype': 'path', 'pdf.fonttype': 42,
})
INK, GALLERY, QUERY, UNKNOWN = '#222831', '#4b6263', '#285d8b', '#985332'
fig, axs = plt.subplots(1, 2, figsize=(7.2, 3.2))
fig.subplots_adjust(left=.025, right=.975, top=.91, bottom=.055, wspace=.13)

def boundary(ax, xy, width, height, query=False):
    ax.add_patch(Ellipse(xy, width, height,
        facecolor='#eaf1f7' if query else '#f0f3f2',
        edgecolor='none', zorder=1))
    ax.add_patch(Ellipse(xy, width, height,
        facecolor='none', edgecolor=QUERY if query else GALLERY,
        linewidth=1.05, linestyle=(0, (4.5, 2.8)) if query else '-', zorder=3))

def point(ax, x, y, label, unknown=False):
    color = UNKNOWN if unknown else INK
    ax.plot(x, y, 'o', ms=4.6, mfc='white' if unknown else color,
            mec=color, mew=1.05, zorder=5)
    ax.text(x+.18, y, label, ha='left', va='center', color=color,
            fontsize=11, zorder=5)

for ax, label, title in zip(axs, ['(a)', '(b)'],
                           ['Closed-set evaluation', 'Open-set evaluation']):
    ax.set(xlim=(0, 5), ylim=(0, 4))
    ax.axis('off')
    ax.text(.12, 3.95, label, va='top', fontsize=11, fontweight='bold', color=INK)
    ax.text(.64, 3.95, title, va='top', fontsize=12, color=INK)

a, b = axs
boundary(a, (2.5, 2.21), 4.5, 2.25)
boundary(a, (2.9, 2.13), 2.65, 1.40, query=True)
a.text(1.12, 3.42, r'Gallery $I_G$', ha='center', color=GALLERY, fontsize=10.5)
a.text(2.90, 2.51, r'Query $I_Q$', ha='center', color=QUERY, fontsize=10.5)
point(a, 2.30, 1.99, 'A')
point(a, 3.32, 1.99, 'B')
point(a, .95, 2.21, 'C')

# Identical gallery/query heights and aligned centres across panels.
boundary(b, (1.84, 2.21), 2.96, 2.25)
boundary(b, (3.14, 2.21), 2.96, 2.25, query=True)
# Restore both boundaries above the fills so the intersection stays explicit.
b.add_patch(Ellipse((1.84, 2.21), 2.96, 2.25, facecolor='none',
                    edgecolor=GALLERY, linewidth=1.05, zorder=4))
b.text(1.12, 3.42, r'Gallery $I_G$', ha='center', color=GALLERY, fontsize=10.5)
b.text(3.92, 3.42, r'Query $I_Q$', ha='center', color=QUERY, fontsize=10.5)
point(b, .96, 2.48, 'B')
point(b, .96, 1.90, 'C')
point(b, 2.36, 2.21, 'A')
point(b, 3.79, 2.21, 'D', unknown=True)
b.text(3.91, 1.76, 'Unknown', ha='center', color=UNKNOWN, fontsize=9)

for ax, equation, text in zip(axs,
    [r'$I_Q \subseteq I_G$', r'$I_Q \setminus I_G \neq \varnothing$'],
    ['All query identities are present in the gallery.',
     'Unknown query identities are absent from the gallery.']):
    ax.text(2.5, .70, equation, ha='center', va='center', fontsize=16, color=INK)
    ax.text(2.5, .20, text, ha='center', va='center', fontsize=8.6, color=INK)

for ext in ['pdf', 'svg', 'png']:
    fig.savefig(OUT / f'Figure1_publication.{ext}', dpi=600, facecolor='white')
fig.savefig(OUT / 'Figure1_publication_preview.png', dpi=200, facecolor='white')
plt.close(fig)
(OUT / 'Figure1_publication_caption.tex').write_text(
    r'Figure 1. Closed-set and open-set person re-identification. '
    r'$Q$ and $G$ denote image sets, with corresponding identity sets $I_Q$ and $I_G$. '
    r'Closed-set evaluation requires $I_Q \subseteq I_G$; open-set evaluation includes '
    r'unknown query identities, so $I_Q \setminus I_G \neq \varnothing$. '
    r'Solid and dashed boundaries denote gallery and query identity sets, respectively. '
    r'Each marker represents an identity; the hollow marker denotes an unknown query identity.'
    '\n', encoding='utf-8')
print('Exported Figure1_publication: PNG (600 dpi), PDF, SVG and LaTeX caption.')
