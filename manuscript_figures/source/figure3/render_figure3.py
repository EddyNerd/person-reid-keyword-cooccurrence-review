"""Figure 3 redraw from saved publication series; no prevalence recomputation."""
from pathlib import Path
import json, os
OUT=Path(__file__).resolve().parent
os.environ.setdefault('MPLCONFIGDIR',str(OUT/'mpl_cache'))
DATA=json.loads((OUT/'Figure3_provenance.json').read_text(encoding='utf-8'))
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
plt.rcParams.update({'font.family':'DejaVu Sans','font.size':10,'axes.spines.top':False,'axes.spines.right':False,'axes.titleweight':'bold','savefig.facecolor':'white','svg.fonttype':'none'})
x=np.arange(5); labels=[c['period'].replace('-','–') for c in CROSS]
colors={'metric':'#B35C00','learn':'#2166AC','convolut':'#168270','attent':'#884EA0'}
fig,axs=plt.subplots(1,2,figsize=(10.6,4),layout='constrained')
report={}
for t,col in colors.items():
    counts=DATA['series'][t]['counts']
    rates=DATA['series'][t]['prevalence_percent']
    axs[0].plot(x,counts,'o-',label=t,color=col,linewidth=2)
    axs[1].plot(x,rates,'o-',label=t,color=col,linewidth=2)
    report[t]={'counts':counts,'prevalence_percent':rates}
for ax,title,ylabel in zip(axs,['Raw document counts','Share of usable keyword records'],['Documents','Records containing the token (%)']):
    ax.set(title=title,ylabel=ylabel,xticks=x,xticklabels=labels,ylim=(0,None))
    ax.tick_params(axis='x',labelrotation=30)
    ax.grid(axis='y',color='#dddddd',linewidth=.6)
    ax.legend(frameon=False,prop={'size':9,'style':'italic'})
for ext in ['png','pdf','svg']:
    fig.savefig(OUT/f'Figure3_publication.{ext}',dpi=400)
fig.savefig(OUT/'Figure3_publication_preview.png',dpi=120)
plt.close(fig)
