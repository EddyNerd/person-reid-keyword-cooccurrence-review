"""Figure 2 redraw from frozen publication node/edge tables; no raster extraction or detection."""
from pathlib import Path
import json, os
OUT=Path(__file__).resolve().parent
os.environ.setdefault('MPLCONFIGDIR',str(OUT/'mpl_cache'))
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.collections import LineCollection
report=json.loads((OUT/'Figure2_provenance.json').read_text(encoding='utf-8'))
nodes=report['node_table']
by_token={n['token']:n['id'] for n in nodes}
edges=[{'node1':by_token[e['source']],'node2':by_token[e['target']],'weight':e['cooccurrence_documents']} for e in report['edge_table']]
by_node={n['id']:n for n in nodes}
marker=report['L1_marker']
assert len(nodes)==15 and len(edges)==27
plt.rcParams.update({'font.family':'DejaVu Sans','font.size':9.6,'svg.fonttype':'none'})
fig=plt.figure(figsize=(6.0,3.65),facecolor='white')
ax=fig.add_axes([.02,.02,.96,.96])
ax.set_xlim(0,765);ax.set_ylim(425,5);ax.set_aspect('equal');ax.axis('off')
segments=[];widths=[];colours=[]
edge_rows=[]
for e in sorted(edges,key=lambda e:float(e['weight'])):
    a,b=by_node[e['node1']],by_node[e['node2']]
    weight=float(e['weight']);assert weight.is_integer()
    segments.append([(a['x'],a['y']),(b['x'],b['y'])])
    widths.append(.065*weight)
    colours.append((.40,.42,.44,.18+.50*weight/39))
    edge_rows.append({'source':a['token'],'target':b['token'],'cooccurrence_documents':int(weight)})
ax.add_collection(LineCollection(segments,linewidths=widths,colors=colours,zorder=1))
for n in nodes:
    ax.scatter([n['x']],[n['y']],s=3.4*n['document_frequency'],marker=marker[n['L1']],
               facecolor=n['colour'],edgecolor=n['colour'],linewidth=.4,zorder=3)
text_artists=[]
for n in nodes:
    token=n['token'];dx,dy,ha=14,1,'left'
    if token=='metric':dx,ha=-20,'right'
    if token=='neural':dx,ha=-14,'right'
    if token=='multi':dx,ha=-17,'right'
    if token=='network':dx,dy,ha=0,26,'center'
    if token=='surveil':dx,dy=14,0
    if token=='learn':dx,dy=28,5
    t=ax.text(n['x']+dx,n['y']+dy,token,fontsize=9.6,fontstyle='italic',
              ha=ha,va='center',color='#171717',zorder=5)
    text_artists.append(t)
fig.canvas.draw();renderer=fig.canvas.get_renderer()
outside=[];overlaps=[]
for i,t in enumerate(text_artists):
    bb=t.get_window_extent(renderer)
    if bb.x0<0 or bb.y0<0 or bb.x1>fig.bbox.width or bb.y1>fig.bbox.height:outside.append(t.get_text())
    for other in text_artists[i+1:]:
        if bb.overlaps(other.get_window_extent(renderer)):overlaps.append((t.get_text(),other.get_text()))
assert not outside,outside
assert not overlaps,overlaps
for ext in ('png','svg'):fig.savefig(OUT/f'Figure2_publication.{ext}',dpi=400,facecolor='white')
fig.savefig(OUT/'Figure2_publication_preview.png',dpi=180,facecolor='white')
plt.close(fig)
