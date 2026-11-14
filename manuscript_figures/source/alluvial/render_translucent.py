"""Minimal alluvial figures; explanations are external captions and notes."""
from pathlib import Path
import hashlib
import json
import os
import re
import sys
import zipfile

HERE=Path(__file__).resolve().parent
os.environ['MPLCONFIGDIR']=str(HERE/'mpl_cache')
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
from matplotlib.path import Path as MPath
from matplotlib.patches import Rectangle,PathPatch

SOURCE=HERE/'source_panels.json'
PALETTE={0:'#0072b2',1:'#ce6800',2:'#9c408d',3:'#008568'}
INK='#203247'
plt.rcParams.update({'font.family':'DejaVu Sans','font.size':14,'text.color':INK,
                     'svg.fonttype':'none','savefig.facecolor':'white'})


def tint(c):
    return tuple(x+(1-x)*.40 for x in mcolors.to_rgb(c))


def positions(values,minimum=.18):
    order=sorted(range(len(values)),key=lambda i:-values[i])
    yy=[values[i] for i in order]
    mean=sum(yy)/len(yy)
    for j in range(1,len(yy)):
        yy[j]=min(yy[j],yy[j-1]-minimum)
    shift=mean-sum(yy)/len(yy)
    return {i:y+shift for i,y in zip(order,yy)}


def validate(p):
    membership={side:{w:g['id'] for g in p[side] for w in g['words_full']} for side in ('left','right')}
    shared=set(membership['left'])&set(membership['right'])
    tokens=[]
    for f in p['flows']:
        assert len(f['words'])==f['count']
        assert all(membership['left'][w]==f['source'] and membership['right'][w]==f['target'] for w in f['words'])
        tokens.extend(f['words'])
    assert len(tokens)==len(set(tokens))==p['coverage']['common_visible']
    assert set(tokens)==shared
    for side,key in [('left','source'),('right','target')]:
        for g in p[side]:
            assert sum(f['count'] for f in p['flows'] if f[key]==g['id'])==len(g['words_common'])


def render(p,number):
    validate(p)
    source_order=[0,3,1,2]
    left=sorted(p['left'],key=lambda g:source_order.index(g['id']))
    right=sorted(p['right'],key=lambda g:g['id'])
    li={g['id']:i for i,g in enumerate(left)}
    ri={g['id']:i for i,g in enumerate(right)}
    n=p['coverage']['common_visible']
    top,bottom,gap=6.15,.35,.30
    unit=(top-bottom-gap*(max(len(left),len(right))-1))/n
    ranges={}
    for side,groups in [('left',left),('right',right)]:
        height=n*unit+gap*(len(groups)-1)
        cursor=top-((top-bottom)-height)/2
        ranges[side]={}
        for g in groups:
            lo=cursor-len(g['words_common'])*unit
            ranges[side][g['id']]=(lo,cursor)
            cursor=lo-gap
    lx,rx,bw=1.20,9.40,.14
    start,end=lx+bw,rx
    lc={k:v[1] for k,v in ranges['left'].items()}
    rc={k:v[1] for k,v in ranges['right'].items()}
    flows=sorted(p['flows'],key=lambda f:(li[f['source']],ri[f['target']]))
    geom=[]
    for f in flows:
        h=f['count']*unit
        lt,rt=lc[f['source']],rc[f['target']]
        lb,rb=lt-h,rt-h
        lc[f['source']],rc[f['target']]=lb,rb
        geom.append({'flow':f,'left':(lb,lt),'right':(rb,rt)})
    for side,cursor in [('left',lc),('right',rc)]:
        assert all(abs(cursor[k]-lo)<1e-10 for k,(lo,hi) in ranges[side].items())
    fig=plt.figure(figsize=(10.8,7.2),facecolor='white')
    ax=fig.add_axes([0,0,1,1]);ax.set(xlim=(0,10.8),ylim=(0,7.2));ax.axis('off')
    texts=[]

    def text(x,y,s,**kw):
        a=ax.text(x,y,s,**kw);texts.append(a);return a

    sp=p['source_period'].replace('-','\N{EN DASH}')
    tp=p['target_period'].replace('-','\N{EN DASH}')
    text(lx,6.77,sp,fontsize=19,fontweight='bold',ha='center',va='center')
    text(rx+bw,6.77,tp,fontsize=19,fontweight='bold',ha='center',va='center')
    for obj in sorted(geom,key=lambda o:-o['flow']['count']):
        lb,lt=obj['left'];rb,rt=obj['right'];c=PALETTE[obj['flow']['source']]
        verts=[(start,lt),(start+2.6,lt),(end-2.6,rt),(end,rt),
               (end,rb),(end-2.6,rb),(start+2.6,lb),(start,lb),(start,lt)]
        codes=[MPath.MOVETO,MPath.CURVE4,MPath.CURVE4,MPath.CURVE4,MPath.LINETO,
               MPath.CURVE4,MPath.CURVE4,MPath.CURVE4,MPath.CLOSEPOLY]
        patch=PathPatch(MPath(verts,codes),facecolor=mcolors.to_rgba(c,0.42),edgecolor=(1,1,1,0.45),linewidth=.45,zorder=1)
        patch.set_gid(f'ribbon_C{obj["flow"]["source"]}_C{obj["flow"]["target"]}')
        ax.add_patch(patch)
        for x,side in [(lx,'left'),(rx,'right')]:
            lo,hi=obj[side]
            ax.add_patch(Rectangle((x,lo),bw,hi-lo,facecolor=c,edgecolor='white',linewidth=.55,zorder=3))
    labels=[]
    for side,key,x in [('left','source',start+.30),('right','target',end-.30)]:
        for g in p['left' if side=='left' else 'right']:
            objects=[obj for obj in geom if obj['flow'][key]==g['id']]
            centers=[sum(obj[side])/2 for obj in objects]
            adjusted=positions(centers)
            for j,obj in enumerate(objects):
                y=adjusted[j]
                if abs(y-centers[j])>.008:
                    px=start+.05 if side=='left' else end-.05
                    ax.plot([px,x],[centers[j],y],color=PALETTE[obj['flow']['source']],linewidth=.7,zorder=4)
                text(x,y,str(obj['flow']['count']),fontsize=12.5,fontweight='bold',ha='center',va='center',
                     bbox={'boxstyle':'round,pad=.12','facecolor':'white','edgecolor':'none','alpha':.96},zorder=5)
                labels.append({'side':side,'source':obj['flow']['source'],'target':obj['flow']['target'],'count':obj['flow']['count']})
    for side,groups in [('left',left),('right',right)]:
        for g in groups:
            cy=sum(ranges[side][g['id']])/2
            x,align=(lx-.24,'right') if side=='left' else (rx+bw+.24,'left')
            text(x,cy,f'C{g["id"]}',fontsize=16,fontweight='bold',ha=align,va='center',
                 color=PALETTE[g['id']] if side=='left' else INK)
    fig.canvas.draw();ren=fig.canvas.get_renderer()
    out=[]
    visible=[]
    for t in texts:
        s=t.get_text();visible.append(s)
        assert re.fullmatch(r'(?:\d{4}\N{EN DASH}\d{4}|C\d+|\d+)',s),f'Unexpected explanatory text: {s}'
        bb=t.get_window_extent(ren)
        if bb.x0<0 or bb.y0<0 or bb.x1>fig.bbox.width or bb.y1>fig.bbox.height:out.append(s)
    assert not out,out
    stem=f'Figure{number}_translucide'
    for ext in ('png','svg'):fig.savefig(HERE/f'{stem}.{ext}',dpi=350)
    fig.savefig(HERE/f'{stem}_preview.png',dpi=140)
    plt.close(fig)
    title=f'Figure {number}. Shared-token correspondence between archived Louvain L1 communities in {sp} and {tp}.'
    note=(f'Note. The diagram includes {n} normalized keyword tokens visible in both historical filter-and-suppress graphs. '
          'Ribbon widths and bar heights represent shared-token counts. Colours identify source communities within the figure '
          'and continue into the destination bars. The same overlap count is repeated at both ends of each ribbon. Community '
          'identifiers are local to each period, and communities are positioned to reduce crossings. Counts refer to tokens, '
          'not publications. The historical random seed was not recorded. Tokens outside the shared set are omitted; their '
          'absence from the diagram does not establish absence from the corpus.')
    if number==4:
        example=('The 14 shared members of 2019–2020 C3 are distributed across three 2021–2022 communities: '
                 'C0 contains base, data, surveil and video (4); C1 contains id, learn, metric, recognit, supervis and vision (6); '
                 'and C2 contains adapt, domain, label and unsupervis (4).')
    else:
        example=('The 18 shared members of 2021–2022 C1 are distributed across four 2023–2024 communities: '
                 'C1 contains retriev (1); C2 contains attent, mechan, multi, scale and vision (5); '
                 'C3 contains contrast, deep, id, learn, loss, metric, recognit and supervis (8); '
                 'and C4 contains convolut, graph, network and neural (4).')
    saved={side:{f'C{g["id"]}':{'shared':len(g['words_common']),'total_archived_pruned':len(g['words_full'])} for g in p[side]} for side in ('left','right')}
    return {'id':p['id'],'stem':stem,'shared_tokens':n,'source_order':source_order,
            'target_order':[g['id'] for g in right],'all_nonzero_flows':len(flows),
            'flows':flows,'endpoint_labels':labels,'visible_text':visible,'out_of_bounds_text':out,
            'shared_and_saved_sizes':saved,'title':title,'note':note,'optional_example':example}


def main():
    raw=SOURCE.read_bytes();data=json.loads(raw)
    panels=sorted([p for p in data['panels'] if p['level']=='L1' and p['source_period'] in ('2019-2020','2021-2022')],key=lambda p:p['source_period'])
    assert len(panels)==2
    reports=[render(p,4 if i==0 else 7) for i,p in enumerate(panels)]
    proof={'source':str(SOURCE),'source_sha256':hashlib.sha256(raw).hexdigest(),
           'new_detection_runs':0,'originals_modified':False,'all_memberships_and_counts_verified':True,
           'ribbon_fill_alpha':0.42,'variant_change':'Translucent fill and finer edges; geometry and labels unchanged',
           'image_text_restricted_to':'Periods, community IDs and ribbon counts',
           'reports':reports,'visual_QA':'pending'}
    (HERE/'verification.json').write_text(json.dumps(proof,ensure_ascii=False,indent=2),encoding='utf-8')
    captions='\n\n'.join(r['title']+'\n'+r['note']+'\n\nOptional explanatory paragraph:\n'+r['optional_example'] for r in reports)
    (HERE/'Captions_and_notes.txt').write_text(captions+'\n',encoding='utf-8')
    (HERE/'source_panels.json').write_text(json.dumps({'metadata':data['metadata'],'panels':panels},ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps({'output':str(HERE),'figures':[r['stem'] for r in reports],
                      'shared_tokens':[r['shared_tokens'] for r in reports],'data_checks':'passed','visual_QA':'pending'},indent=2))


if __name__=='__main__':main()
