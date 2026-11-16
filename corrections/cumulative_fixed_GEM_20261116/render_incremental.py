"""Draw cumulative networks from frozen successive GEM coordinates only."""
from pathlib import Path
import csv,json,os,sys

HERE=Path('\\\\?\\'+str(Path(__file__).resolve()).removeprefix('\\\\?\\')).parent
DATA=HERE/'public' if (HERE/'public').is_dir() else HERE
for p in HERE.parents:
 dep=p/'.figuredeps_20261113'
 if dep.is_dir():
  sys.path.insert(0,str(dep));os.environ.setdefault('MPLCONFIGDIR',str(p/'.matplotlib_cumulative_20261116'));break
os.environ.setdefault('MPLCONFIGDIR',str(HERE/'.matplotlib-cache'))
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.colors import to_rgb
import numpy as np
from adjustText import adjust_text

def read(p):
 with p.open(encoding='utf-8-sig',newline='') as h:return list(csv.DictReader(h))

def render(period):
 folder=DATA/period;nodes=read(folder/'nodes.csv');edges=read(folder/'edges.csv')
 by={r['token']:r for r in nodes};pos={r['token']:(float(r['x']),float(r['y'])) for r in nodes}
 bounds=json.loads((DATA/'viewport.json').read_text())['bounds']
 plt.rcParams.update({'font.family':'DejaVu Sans','svg.fonttype':'none','pdf.fonttype':42,'axes.unicode_minus':False})
 fig=plt.figure(figsize=(15,15),facecolor='white');ax=fig.add_axes([.01,.01,.98,.98])
 ax.set_xlim(bounds[:2]);ax.set_ylim(bounds[2:]);ax.axis('off')
 lo=min(int(e['weight']) for e in edges);hi=max(int(e['weight']) for e in edges)
 for e in edges:
  frac=(int(e['weight'])-lo)/(hi-lo);a,b=pos[e['source']],pos[e['target']]
  ax.plot([a[0],b[0]],[a[1],b[1]],color='black',linewidth=1+4*frac,alpha=.01+.39*frac,zorder=1)
 for marker in dict.fromkeys(n['marker'] for n in nodes):
  g=[n for n in nodes if n['marker']==marker]
  ax.scatter([float(n['x']) for n in g],[float(n['y']) for n in g],s=[float(n['area_points2']) for n in g],c=[n['color'] for n in g],marker=marker,edgecolors='black',linewidths=.5,alpha=.95,zorder=2)
 label_file=folder/'labels.csv'
 frozen={r['token']:(float(r['label_x']),float(r['label_y'])) for r in read(label_file)} if label_file.exists() else {}
 texts=[]
 for n in nodes:
  x,y=frozen.get(n['token'],pos[n['token']]);color=tuple(c*.35 for c in to_rgb(n['color']))
  texts.append(ax.text(x,y,n['display_label'],fontsize=12,ha='center',va='center',color=color,zorder=4,bbox=dict(facecolor='white',edgecolor='none',alpha=.35,pad=.12)))
 xy=np.array(list(pos.values()))
 if not frozen:
  np.random.seed(20261116)
  adjust_text(texts,x=xy[:,0],y=xy[:,1],ax=ax,expand=(1.12,1.25),force_text=(.15,.23),force_static=(.1,.16),force_pull=(.006,.006),ensure_inside_axes=True,iter_lim=900)
  with label_file.open('w',encoding='utf-8',newline='') as h:
   w=csv.writer(h);w.writerow(['token','label_x','label_y'])
   for n,t in zip(nodes,texts):w.writerow([n['token'],*t.get_position()])
 # A small text-only inset prevents anti-aliased glyphs touching the axes edge.
 fig.canvas.draw();screen=fig.canvas.get_renderer();screen_bounds=ax.get_window_extent(screen)
 for t in texts:
  box=t.get_window_extent(screen);dx=max(0,screen_bounds.x0+2-box.x0)-max(0,box.x1-(screen_bounds.x1-2));dy=max(0,screen_bounds.y0+2-box.y0)-max(0,box.y1-(screen_bounds.y1-2))
  if dx or dy:
   px,py=ax.transData.transform(t.get_position());t.set_position(ax.transData.inverted().transform((px+dx,py+dy)))
 with label_file.open('w',encoding='utf-8',newline='') as h:
  w=csv.writer(h);w.writerow(['token','label_x','label_y'])
  for n,t in zip(nodes,texts):w.writerow([n['token'],*t.get_position()])
 leaders=0
 for n,t in zip(nodes,texts):
  x,y=pos[n['token']];tx,ty=t.get_position()
  if np.hypot((tx-x)/(bounds[1]-bounds[0]),(ty-y)/(bounds[3]-bounds[2]))>.02:
   ax.plot([x,tx],[y,ty],color='#7c8790',linewidth=.25,alpha=.65,zorder=3);leaders+=1
 fig.canvas.draw();r=fig.canvas.get_renderer();boxes=[t.get_window_extent(r).expanded(1.005,1.005) for t in texts];area=ax.get_window_extent(r)
 overlaps=[[nodes[i]['token'],nodes[j]['token']] for i in range(len(boxes)) for j in range(i+1,len(boxes)) if boxes[i].overlaps(boxes[j])]
 clipped=[nodes[i]['token'] for i,b in enumerate(boxes) if not(area.contains(b.x0,b.y0) and area.contains(b.x1,b.y1))]
 name=period.replace('-',chr(0x2013))
 for ext in ('png','svg','pdf'):
  fig.savefig(folder/(name+'.'+ext),dpi=240,facecolor='white')
 fig.savefig(folder/'preview.png',dpi=63.6,facecolor='white');plt.close(fig)
 qa={'nodes':len(nodes),'edges':len(edges),'labels':len(texts),'overlapping_label_pairs':overlaps,'clipped_labels':clipped,'leader_lines':leaders,'node_coordinates_never_adjusted_by_renderer':True,'label_font_pt':12,'PNG_pixels':[3600,3600],'preview_pixels':[954,954],'common_viewport':bounds,'versions':{'matplotlib':matplotlib.__version__,'numpy':np.__version__}}
 (folder/'render_checks.json').write_text(json.dumps(qa,indent=2),encoding='utf-8')
 print(period,json.dumps(qa))

if __name__=='__main__':
 for period in ('2015-2022','2015-2024'):render(period)
