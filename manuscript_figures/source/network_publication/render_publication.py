"""Publication-size views of four frozen 2023–2024 community partitions.

All 64 nodes, 239 edges and hierarchy fields are unchanged. Only selected
labels and a more compact canvas/key layout differ from the archived redraw.
"""
from pathlib import Path
import csv, hashlib, json, os, sys, math

OUT=Path(__file__).resolve().parent
ORIGINAL=OUT.parent/'hierarchy'
sys.path.insert(0,str(ORIGINAL))
os.environ['MPLCONFIGDIR']=str(OUT/'mpl_cache')

# Reuse the saved memberships, coordinate/palette rules and exact enclosure
# engines. Stop before the original script's rendering/output calls.
source_path=ORIGINAL/'render_hierarchical_networks.py'
code=source_path.read_text(encoding='utf-8')
prefix=code.split("render('Louvain', 'lo')\n",1)[0]
assert prefix!=code
ns={'__file__':str(source_path),'__name__':'publication_source'}
exec(compile(prefix,str(source_path),'exec'),ns)

import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patheffects as pe
from matplotlib.collections import LineCollection
from matplotlib.patches import Ellipse,Rectangle
from adjustText import adjust_text
from PIL import Image

r,visible,names,P,pos,areas=(ns[k] for k in ('r','visible','names','P','pos','areas'))
grouped,colour_map,marker_map,hierarchy_info=(ns[k] for k in ('grouped','colour_map','marker_map','hierarchy_info'))
contour_engine,higher_engine=ns['contour_engine'],ns['higher_engine']

SELECTED=['convolut','neural','network','graph','vision','transform','occlud','cloth','chang',
          'adversari','generat','cross','modal','infrar','visibl','text','retriev',
          'domain','adapt','learn','metric','pseudo','label','featur']
assert len(SELECTED)==24 and set(SELECTED)<=set(names[i] for i in visible)
selected=[i for i in visible if names[i] in SELECTED]
TOKEN_FONT=8.3
plt.rcParams.update({'font.family':'DejaVu Sans','svg.fonttype':'none','font.size':8.0,
                     'hatch.linewidth':.30,'text.color':'#151515'})


def bounds(ax):
    ax.set_xlim(pos[:,0].min()-.16,pos[:,0].max()+.23)
    ax.set_ylim(pos[:,1].min()-.12,pos[:,1].max()+.12)
    ax.set_aspect('equal');ax.axis('off')


def key(ax,run,markers,l2,parents):
    ax.set(xlim=(0,1),ylim=(0,1));ax.axis('off')
    groups=grouped(run,'L1') if not l2 else {g:l2[g] for g in parents}
    width_in=ax.get_position().width*ax.figure.get_figwidth()
    height_in=ax.get_position().height*ax.figure.get_figheight()
    aspect=width_in/height_in
    for j,(g,members) in enumerate(groups.items()):
        cx=(j+.5)/len(groups)
        if l2:
            rank=parents.index(g)
            ax.add_patch(Ellipse((cx,.48),width=.47/aspect,height=.47,facecolor='white',
                         edgecolor=contour_engine.colour(rank),linestyle=contour_engine.style(rank),
                         linewidth=.65,transform=ax.transAxes))
            children=sorted({run['levels']['L1'][i] for i in members})
            if len(children)==1:offset=[(0,0)]
            else:offset=[(math.cos(2*math.pi*k/len(children))*.029,
                          math.sin(2*math.pi*k/len(children))*.029*aspect) for k in range(len(children))]
            for child,(dx,dy) in zip(children,offset):
                ax.scatter([cx+dx],[.48+dy],s=13,marker=markers[child],facecolor='#a3a8ad',
                           edgecolor='#303030',linewidth=.35,transform=ax.transAxes,zorder=3)
            label=f'L2-{g}'
        else:
            ax.scatter([cx],[.48],s=30,marker=markers[g],facecolor='#a3a8ad',
                       edgecolor='#303030',linewidth=.35,transform=ax.transAxes,zorder=3)
            label=f'L1-{g}'
        ax.text(cx,.93,label,fontsize=7.2,ha='center',va='center',weight='bold')
        ax.text(cx,.04,str(len(members)),fontsize=7.1,ha='center',va='center')


def higher_key(fig,run):
    data=higher_engine.prepare(run)
    if not data['present']:return
    left,width=.520,.455
    for level,yy in [('L3',.041),('L4',.015)]:
        rows=data[level]
        fig.text(left,yy,level,fontsize=7.2,weight='bold',va='center')
        start=left+.036
        span=width-.049
        for j,row in enumerate(rows):
            xx=start+span*j/len(rows)
            if level=='L3':
                patch=Ellipse((xx,yy),width=.075/fig.get_figwidth(),height=.075/fig.get_figheight(),
                              transform=fig.transFigure,facecolor=row['halo_colour'],edgecolor='none',alpha=.7)
            else:
                patch=Rectangle((xx-.045/fig.get_figwidth(),yy-.037/fig.get_figheight()),
                                .09/fig.get_figwidth(),.074/fig.get_figheight(),transform=fig.transFigure,
                                facecolor='white',edgecolor='#777',linewidth=.3,hatch=row['hatch'])
            fig.add_artist(patch)
            fig.text(xx+.067/fig.get_figwidth(),yy,str(row['id']),fontsize=7.1,ha='left',va='center')


def render(algorithm,short):
    fig=plt.figure(figsize=(9.8,6.15),facecolor='white')
    axes=[fig.add_axes([.020,.205,.470,.725]),fig.add_axes([.510,.205,.470,.725])]
    keys=[fig.add_axes([.030,.078,.450,.091]),fig.add_axes([.520,.078,.450,.091])]
    for ax in axes:bounds(ax)
    fig.canvas.draw()
    # Match the old marker sizes relative to the saved coordinate geometry.
    oldfig=plt.figure(figsize=(17.4,11.6))
    oldax=oldfig.add_axes([.025,.225,.465,.595]);bounds(oldax);oldfig.canvas.draw()
    point_scale=axes[0].get_window_extent().height/fig.dpi/(oldax.get_window_extent().height/oldfig.dpi)
    plt.close(oldfig)
    memberships=[];runmeta={};labelmeta={}
    for k,treatment in enumerate(['s','h']):
        runkey=f'{treatment}_m10_{short}_1000'
        run=r['runs'][runkey];ax=axes[k]
        colours,markers=colour_map(run),marker_map(run)
        l2,parents=hierarchy_info(run)
        upper=higher_engine.draw(ax,run)
        contour_records=[];contour_labels=[]
        for rank,parent in enumerate(parents):
            rec,t=contour_engine.draw(ax,l2[parent],parent,rank)
            t.set_fontsize(7.0)
            contour_records.append(rec);contour_labels.append(t)
        edges=sorted(ns['mask']['edges'],key=lambda e:e[2])
        weights=np.array([e[2] for e in edges])
        ratio=(weights-weights.min())/max(1,weights.max()-weights.min())
        rgba=np.tile(np.array([.36,.38,.40,1.]),(len(edges),1))
        rgba[:,3]=.10+.48*ratio**.65
        ax.add_collection(LineCollection([[P[u],P[v]] for u,v,w in edges],colors=rgba,
                          linewidths=(.26+1.55*ratio**.70)*point_scale,zorder=1))
        for group,nodes in grouped(run,'L1').items():
            ax.scatter([P[i][0] for i in nodes],[P[i][1] for i in nodes],
                       s=[areas[i]*point_scale**2 for i in nodes],
                       c=[colours[run['levels']['L0'][i]] for i in nodes],marker=markers[group],
                       edgecolors='#252525',linewidths=.58*point_scale,alpha=.98,zorder=3)
        labels=[]
        for i in selected:
            x,y=P[i]
            labels.append(ax.text(x+.014,y+.016,names[i],fontsize=TOKEN_FONT,fontstyle='italic',
                          ha='left',va='bottom',zorder=6,
                          path_effects=[pe.withStroke(linewidth=1.6,foreground='white',alpha=.96)]))
        np.random.seed(1000)
        alltext=labels+contour_labels
        adjust_text(alltext,x=[P[i][0] for i in visible],y=[P[i][1] for i in visible],
                    target_x=[P[i][0] for i in selected]+[t.get_position()[0] for t in contour_labels],
                    target_y=[P[i][1] for i in selected]+[t.get_position()[1] for t in contour_labels],
                    ax=ax,expand=(1.14,1.24),force_text=(.20,.30),force_static=(.18,.23),
                    force_pull=(.009,.012),max_move=(7,7),iter_lim=1000,prevent_crossings=True,
                    min_arrow_len=4,arrowprops={'arrowstyle':'-','color':'#657079','lw':.35,'alpha':.65})
        ax.set_title('A  Filter-and-suppress' if treatment=='s' else 'B  Filter-and-hide',
                     fontsize=9.3,weight='bold',pad=8)
        key(keys[k],run,markers,l2,parents)
        if treatment=='h':higher_key(fig,run)
        labelmeta[runkey]={names[i]:list(t.get_position()) for i,t in zip(selected,labels)}
        for i in visible:
            memberships.append({'algorithm':algorithm,'treatment':'suppress' if treatment=='s' else 'hide',
                                'token':names[i],'label_visible':i in selected,'document_frequency':r['frequencies'][i],
                                **{level:None if run['levels'].get(level) is None else run['levels'][level][i]
                                   for level in ['L0','L1','L2','L3','L4','FINAL']},
                                'L0_colour':colours[run['levels']['L0'][i]],
                                'L1_shape':str(markers[run['levels']['L1'][i]]),'x':P[i][0],'y':P[i][1]})
        runmeta[runkey]={'counts':run['counts'],'FINAL_index':run['FINAL_index'],'graph_sha256':run['graph_sha256'],
                         'selected_L2':[{'id':g,'visible_count':len(l2[g])} for g in parents],
                         'L2_membership_contours':contour_records,'higher_hierarchy':upper}
    fig.canvas.draw();renderer=fig.canvas.get_renderer()
    outside=[]
    for ax in fig.axes:
        for t in ax.texts:
            bb=t.get_window_extent(renderer)
            if bb.x0<-1 or bb.y0<-1 or bb.x1>fig.bbox.width+1 or bb.y1>fig.bbox.height+1:outside.append(t.get_text())
    assert not outside,outside
    stem=f'{algorithm}_publication'
    for ext in ('png','svg'):fig.savefig(OUT/f'{stem}.{ext}',dpi=400,facecolor='white')
    fig.savefig(OUT/f'{stem}_preview.png',dpi=160,facecolor='white')
    plt.close(fig)
    return {'algorithm':algorithm,'stem':stem,'canvas_inches':[9.8,6.15],
            'token_font_pt_at_9_8in_width':TOKEN_FONT,'uniform_marker_edge_scale':point_scale,
            'displayed_node_count':64,'displayed_edge_count':239,'label_count_per_panel':len(selected),
            'labels':SELECTED,'runs':runmeta,'label_positions':labelmeta,'out_of_figure_text':outside},memberships


def main():
    reports=[];memberships=[]
    for alg,short in [('Louvain','lo'),('Leiden','le')]:
        meta,rows=render(alg,short);reports.append(meta);memberships.extend(rows)
    old=list(csv.DictReader((ORIGINAL/'node_memberships.csv').open(encoding='utf-8-sig')))
    oldmap={(x['algorithm'],x['treatment'],x['token']):x for x in old}
    for row in memberships:
        treatment='Filter-and-suppress' if row['treatment']=='suppress' else 'Filter-and-hide'
        prior=oldmap[(row['algorithm'],treatment,row['token'])]
        for k in ['x','y']:
            assert float(prior[k])==float(row[k])
        assert prior['L0_colour']==row['L0_colour']
        for k in ['L0','L1','L2','L3','L4','FINAL']:
            assert (None if prior[k]=='' else int(prior[k]))==row[k]
    with (OUT/'all_64_memberships.csv').open('w',encoding='utf-8-sig',newline='') as f:
        writer=csv.DictWriter(f,fieldnames=list(memberships[0]));writer.writeheader();writer.writerows(memberships)
    manifest={'source_renderer':str(source_path),'source_renderer_sha256':hashlib.sha256(source_path.read_bytes()).hexdigest(),
              'source_provenance':ns['manifest'],'source_memberships':str(ORIGINAL/'node_memberships.csv'),
              'changes':'Publication canvas and selected larger labels; no graph, partition, palette or coordinate changes',
              'unchanged_coordinates_colours_memberships_verified':True,'community_detection_recomputed':False,
              'reported_level_counts_include_hidden_nodes':True,'reports':reports,'visual_QA':'pending'}
    (OUT/'publication_provenance.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps({'output':str(OUT),'reports':[{'algorithm':r['algorithm'],'labels_per_panel':r['label_count_per_panel'],
                       'token_font_pt':r['token_font_pt_at_9_8in_width']} for r in reports],
                      'all_memberships_verified':True,'new_detector_runs':0},indent=2))


if __name__=='__main__':main()
