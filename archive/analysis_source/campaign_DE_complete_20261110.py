"""Eight-stage author-keyword campaign with hash-controlled graph/seed caching."""
import os
os.environ['PYTHONHASHSEED']='0'
os.environ['OPENBLAS_NUM_THREADS']='1'
os.environ['OMP_NUM_THREADS']='1'
from pathlib import Path
from collections import Counter,defaultdict
from datetime import datetime,timezone
from concurrent.futures import ProcessPoolExecutor,as_completed
from itertools import combinations
from functools import lru_cache
import argparse,json,shutil,time,hashlib,csv
import networkx as nx
import numpy as np
from community_hierarchy import partitions,nested
from audit_recovered_historical_data import wos
from compare_historical_suppress_hide_seed1000 import read,save,sha,digest,csvfile,groups,qdirect
from campaign_DE_suppress_thresholds1000 import ROOT,ACTIVE,OUT as SUP,SOURCE as BASE,MULT,ALGS,code,makegraph

OUT=ACTIVE/'campagne_complete_mots_cles_auteurs_20261110'
HIST=ACTIVE/'historical_community_reproduction'
SEEDS=list(range(1000,1030));LEVELS=['L0','L1','FINAL']
FOCAL_PAIRS=[('attent','mechan'),('chang','cloth'),('featur','fusion'),('granular','multi'),('multi','scale'),('occlud','transform'),('transform','vision'),('adapt','domain'),('loss','triplet'),('infrar','visibl'),('label','pseudo'),('convolut','neural')]
def atomic(p,d):
    p=Path(p);p.parent.mkdir(parents=True,exist_ok=True);tmp=p.with_suffix('.pending');tmp.write_text(json.dumps(d,ensure_ascii=False,separators=(',',':')),encoding='utf-8');os.replace(tmp,p)
def status(state,**kw):atomic(OUT/'study_status.json',dict(state=state,updated_utc=datetime.now(timezone.utc).isoformat(),fields=['DE'],seeds=SEEDS,multipliers=MULT,**kw))
@lru_cache(maxsize=10)
def full(n):return read(OUT/f'inputs/full/{n}.json')
@lru_cache(maxsize=70)
def mask(n,m):return read(OUT/f'graphs/{n}_{code(m)}.json')
def cache(h,a,s):return OUT/f'runs/{h[:16]}_{a[:2]}_{s}.json'
def run(n,t,m,a,s):return read(cache((full(n) if t=='hide' else mask(n,m))['graph_sha256'],a,s))
def at(r,k):return r['levels'][-1] if k=='FINAL' else r['levels'][int(k[1:])] if int(k[1:])<len(r['levels']) else None
def export(name,rr):
    atomic(OUT/(name+'.json'),rr)
    csvfile(OUT/f'tables/{name}.csv',[{k:json.dumps(v,ensure_ascii=False) if isinstance(v,(list,dict)) else v for k,v in r.items()} for r in rr])
def prepare():
    if (OUT/'protocol.json').exists():assert read(OUT/'protocol.json')['fields']==['DE'];return
    for d in ['inputs/full','inputs/terms','inputs/native','inputs/source_exports','graphs','runs','metrics','tables','historical','layouts','figures','atlas_data','reports','sources']:(OUT/d).mkdir(parents=True,exist_ok=True)
    protected={}
    def cp(src,dst):
        protected[str(src)]=sha(src);dst=OUT/dst;dst.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(src,dst)
    cases=read(SUP/'source_cases.json');save(OUT/'source_cases.json',cases)
    for f in ['cases.json','comparison_scopes.json','graph_statistics.json']:cp(SUP/f,f)
    cp(SUP/'inputs/recovered_stopwords.txt','inputs/recovered_stopwords.txt')
    cp(BASE/'inputs/native_DE_normalization.json','inputs/native_DE_normalization.json')
    for src in [SUP,BASE,HIST]:
        for f in ['artifact_manifest.json','study_status.json','independent_verification.json','partition_verification.json','source_verification.json','binary_verification.json']:
            if (src/f).exists():protected[str(src/f)]=sha(src/f)
    unique_graphs={};missing=[];empty=[];records={};manifest=[];imports=[]
    for c in cases:
        n=c['name']
        for d in ['full','terms','native']:cp(SUP/f'inputs/{d}/{n}.json',f'inputs/{d}/{n}.json')
        cp(BASE/f'inputs/source_exports/{n}.txt',f'inputs/source_exports/{n}.txt')
        for suffix in ['.json','_geometry.json']:cp(SUP/f'layouts/{n}{suffix}',f'layouts/{n}{suffix}')
        cp(HIST/f'inputs/{n}.gdf',f'historical/{n}.gdf');cp(HIST/f'reference_images/{n}.png',f'historical/{n}_original.png')
        for f in [f'{n}_native_preview.png',f'{n}_archived_memberships.png']:
            if (HIST/'figures'/f).exists():cp(HIST/'figures'/f,'historical/'+f)
        f=full(n);unique_graphs[f['graph_sha256']]=dict(nodes=f['nodes'],edges=f['edges'],graph_sha256=f['graph_sha256'])
        for m in MULT:
            cp(SUP/f'graphs/{n}_{code(m)}.json',f'graphs/{n}_{code(m)}.json');g=mask(n,m);unique_graphs[g['graph_sha256']]=dict(nodes=g['nodes'],edges=g['edges'],graph_sha256=g['graph_sha256'])
            for a in ALGS:
                old=SUP/f'runs/{n}_{code(m)}_{a}.json';r=read(old);target=cache(g['graph_sha256'],a,1000)
                if target.exists():assert read(target)['levels']==r['levels']
                else:atomic(target,{**r,'source_output':str(old),'source_sha256':sha(old),'computed_current_campaign':False})
                protected[str(old)]=sha(old);imports.append(dict(case=n,treatment='suppress',multiplier=m,algorithm=a,seed=1000,graph_sha256=g['graph_sha256'],source=str(old)))
        for a in ALGS:
            old=BASE/f'runs/{n}_hide_{a}_1000.json';r=read(old);target=cache(f['graph_sha256'],a,1000)
            if target.exists():assert read(target)['levels']==r['levels']
            else:atomic(target,{**r,'source_output':str(old),'source_sha256':sha(old),'computed_current_campaign':False})
            protected[str(old)]=sha(old);imports.append(dict(case=n,treatment='hide',algorithm=a,seed=1000,graph_sha256=f['graph_sha256'],source=str(old)))
        if c['kind']=='cross_sectional':
            terms={d['UT']:d for d in read(OUT/f'inputs/terms/{n}.json')}
            for d in wos(OUT/f'inputs/source_exports/{n}.txt'):
                if d['UT']=='WOS:000450332600002':continue
                assert d['UT'] not in records;records[d['UT']]=d
                meta=dict(UT=d['UT'],year=d.get('PY',''),title=' '.join(d.get('TI','').split()),journal=' '.join(d.get('SO','').split()),document_type=d.get('DT',''),DOI=d.get('DI',''),period=c['period'])
                if not d.get('DE','').strip():missing.append(meta)
                elif not terms[d['UT']]['terms']:empty.append({**meta,'author_keywords':d['DE']})
    assert len(records)==2333 and len(missing)==72 and len(empty)==1
    missing.sort(key=lambda d:(int(d['year']),d['title'].lower()));save(OUT/'notices_sans_mots_cles_auteurs.json',missing)
    save(OUT/'notices_sans_mots_apres_normalisation.json',empty)
    txt=['NOTICES WITHOUT AUTHOR KEYWORDS IN THE HISTORICAL WOS EXPORTS','',
         'Scope: 2333 selected unique records from the direct recovered historical corpus, excluding the confirmed off-topic healthcare record WOS:000450332600002.',
         'Criterion: missing or whitespace-only Web of Science author-keyword field DE before normalization. Titles are metadata only and never contribute vocabulary in this campaign.',
         '72 records have empty DE. One additional record has nonempty DE but no surviving normalized terms. Therefore 73 records (3.13%) contribute no vocabulary and 2260 contribute at least one term.',
         'The missing-keyword records are not removed from bibliographic denominators and no title, abstract, Keywords Plus or invented keyword is substituted.',
         'Absence is established in the saved WoS export. Publisher keyword availability has not been audited. Missingness may be associated with journals, document type and period; no random-missingness assumption is made.','',
         'TEXT FOR THE MANUSCRIPT',
         'The co-occurrence analysis was restricted to author keywords. Of the 2333 retained historical records, 72 (3.09%) contained no author keywords in the saved Web of Science exports, and one additional record yielded no terms after preprocessing. These 73 records remained in the bibliographic corpus but contributed no vocabulary or co-occurrence links. The resulting networks therefore represent the author-keyword-bearing subset rather than all retrieved publications. This limitation may affect thematic coverage, particularly if keyword availability differs across publication sources, document types or periods. Missing author-keyword fields were not supplemented with titles or abstracts, in order to preserve the historical analytical condition.','',
         'COMPLETE LIST']
    for i,d in enumerate(missing,1):txt.extend([f'{i}. {d["title"]}',f'Year: {d["year"]} | Journal: {d["journal"]}',f'WoS: {d["UT"]} | Type: {d["document_type"]} | DOI: {d["DOI"] or "not supplied"}',''])
    txt.extend(['ADDITIONAL RECORD WITH NO SURVIVING NORMALIZED TERMS',json.dumps(empty[0],ensure_ascii=False,indent=2)])
    (OUT/'notices_sans_mots_cles_auteurs.txt').write_text('\n'.join(txt),encoding='utf-8')
    coverage=[]
    for c in cases:
        rr=read(OUT/f'inputs/terms/{c["name"]}.json');no=sum(not d['DE'].strip() for d in rr);zero=sum(not d['terms'] for d in rr)
        coverage.append(dict(case=c['name'],documents=len(rr),missing_author_keywords=no,no_surviving_terms=zero,with_terms=len(rr)-zero,with_at_least_two_terms=sum(len(d['terms'])>=2 for d in rr),missing_fraction=no/len(rr)))
    export('corpus_coverage',coverage)
    for f in ['partition_verification.json','source_verification.json','render_verification.json','binary_verification.json','cases.json']:cp(HIST/f,'historical/'+f)
    cp(ACTIVE/'louvain_leiden_seed1000_all_windows_20261109/archive_agreement.json','historical/archive_agreement_seed1000.json')
    for c in cases:
        n=c['name']
        for t in ['suppress','hide']:
            for m in (MULT if t=='suppress' else [1.]):
                h=(full(n) if t=='hide' else mask(n,m))['graph_sha256']
                for a in ALGS:
                    for s in SEEDS:manifest.append(dict(case=n,treatment=t,multiplier=m if t=='suppress' else None,algorithm=a,seed=s,graph_sha256=h,file=cache(h,a,s).relative_to(OUT).as_posix()))
    save(OUT/'unique_graphs.json',list(unique_graphs.values()));save(OUT/'run_manifest.json',manifest);save(OUT/'imported_seed1000_outputs.json',imports);save(OUT/'protected_sources.json',dict(files=protected))
    save(OUT/'protocol.json',dict(created_utc=datetime.now(timezone.utc).isoformat(),user_decision='Author keywords only to remain consistent with historical work; explicitly supersedes earlier TI plus DE request',fields=['DE'],titles_used_for_vocabulary=False,abstracts_used=False,keywords_plus_used=False,thesaurus_used=False,corpus=2333,missing_DE=72,empty_normalized_DE=73,unique_records_with_terms=2260,excluded_UT='WOS:000450332600002',stopword_entries=334,stopword_unique_entries=333,normalization='Recovered native Sci2 English Snowball map, exact UT and DE',weights='Raw integer binary document cooccurrence; no encoded rescaling',algorithms=ALGS,seeds=SEEDS,multipliers=MULT,reference_seed=1000,historical_seed=None,python_hash_seed=0,resolution=1,louvain='NetworkX 3.2.1 louvain_partitions threshold 1e-7',leiden='Pinned NetworkX 3.7 modularity leiden_partitions theta 0.01 via unchanged local adapter',threshold='Frozen native top thirds then t(m)=m*t_effective_reference; original per-window comparator; no further rounding',reference_2021_2022='Approved effective >=15 preserves all historical nodes and links; not a uniquely recovered historical UI step',suppress='Exclude mask isolates and retain largest nonisolated component before detection',hide='All full-network nodes, edges and components participate; same suppression mask used for display only',levels='L0 first distinct, L1 second distinct if available, FINAL actual last with index; never substitute FINAL for missing L1',logical_detector_conditions=4800,logical_display_conditions=8400,full_partitions=600,suppress_partitions=4200,cache='Graph hash plus algorithm plus seed; identical inputs reused after equality and hash verification; physical executions counted separately',primary_ARI='Within-threshold seed pairs on identical visible nodes; 435 pairs when all 30 outputs have the level',secondary_ARI='Fixed core across all seven masks; treatment, algorithm and threshold comparisons on explicitly identical words',statistics='Median, quartiles, IQR, min, max and valid comparisons; pairwise scores not independent samples',local_blocks='Strict coassignment across all 480 partition outputs per window on fixed core, plus focal-pair frequencies and availability',figures='Fixed preceding union layouts: weighted KK cross-sectional; native GUESS GEM cumulative. Seed1000 illustrated a priori; offline atlas produces every seed and mask with SVG download.',historical_reproduction='Preserved original GDFs and PNGs plus verified native Sci2 replay outputs. Original available memberships match exactly; new seed1000 NetworkX Louvain is a separate comparator.',cumulative_warning='Archive cumulative 2015-2022 actually contains 2019-2022 records only; preserve and flag, not a valid nested cumulative cohort',stages=list(range(1,9))))
    status('prepared',logical_detector_conditions=4800,logical_display_conditions=8400,unique_graphs=len(unique_graphs),cached_outputs=len(list((OUT/'runs').glob('*.json'))),report_pending=True)
    print('PREPARED',len(unique_graphs),'unique graphs; 4800 logical detector conditions; 8400 displays',flush=True)

def worker(job):
    d,a=job;g=makegraph(d['nodes'],d['edges']);count=0
    for s in SEEDS:
        p=cache(d['graph_sha256'],a,s)
        if p.exists():continue
        start=time.monotonic();pp=partitions(g,'leiden_hierarchy' if a=='leiden' else a,s);q=[qdirect(g,x) for x in pp]
        atomic(p,dict(algorithm=a,seed=s,python_hash_seed=0,graph_sha256=d['graph_sha256'],levels=pp,modularity_by_level=q,distinct_levels=len(pp),elapsed_seconds=time.monotonic()-start,computed_current_campaign=True));count+=1
    return d['graph_sha256'],a,count
def compute(workers=6):
    gg=read(OUT/'unique_graphs.json');jobs=[(d,a) for d in sorted(gg,key=lambda x:len(x['edges']),reverse=True) for a in ALGS if any(not cache(d['graph_sha256'],a,s).exists() for s in SEEDS)];total=len(gg)*2*30
    status('running',phase='community_detection',unique_output_total=total,cached_outputs=len(list((OUT/'runs').glob('*.json'))),workers=workers,report_pending=True)
    with ProcessPoolExecutor(max_workers=workers) as pool:
        for future in as_completed([pool.submit(worker,j) for j in jobs]):
            h,a,k=future.result();done=len(list((OUT/'runs').glob('*.json')));status('running',phase='community_detection',unique_output_total=total,cached_outputs=done,workers=workers,report_pending=True);print('DETECTION',done,'/',total,a,h[:10],flush=True)
    assert len(list((OUT/'runs').glob('*.json')))==total
    status('detection_complete',unique_output_total=total,logical_detector_conditions=4800,logical_display_conditions=8400,report_pending=True)

def ari(p,q,ww):
    if p is None or q is None or len(ww)<2:return None
    a=np.asarray([p[w] for w in ww]);b=np.asarray([q[w] for w in ww]);_,a=np.unique(a,return_inverse=True);_,b=np.unique(b,return_inverse=True);cells=np.bincount(a*(b.max()+1)+b);aa=np.bincount(a);bb=np.bincount(b);S=int((cells*(cells-1)).sum());A=int((aa*(aa-1)).sum());B=int((bb*(bb-1)).sum());N=len(ww)*(len(ww)-1);ex=A*B/N;den=(A+B)/2-ex;return float((S-ex)/den) if den else 1.
def desc(v):
    a=np.array([x for x in v if x is not None]);
    if not len(a):return dict(valid=0,median=None,q25=None,q75=None,iqr=None,minimum=None,maximum=None)
    lo,md,hi=np.quantile(a,[.25,.5,.75]);return dict(valid=len(a),median=float(md),q25=float(lo),q75=float(hi),iqr=float(hi-lo),minimum=float(a.min()),maximum=float(a.max()))

def metrics_window(n):
    cc=[x for x in read(OUT/'cases.json') if x['case']==n];by={x['multiplier']:x for x in cc};core=sorted(set.intersection(*(set(x['nodes']) for x in cc)));ref=set(by[1.]['nodes']);rr={(t,m,a,s):run(n,t,m,a,s) for t in ['suppress','hide'] for m in MULT for a in ALGS for s in SEEDS};summary=[];scores=[];quality=[];extras=[];persistent=[];focal=[];seed1000=[];sets={};stats=[]
    def record(comp,t,m,a,k,scope,ww,items):
        vv=[]
        for s,z,p,q in items:
            v=ari(p,q,ww);vv.append(v);scores.append(dict(case=n,comparison=comp,treatment=t,multiplier=m,algorithm=a,level=k,scope=scope,nodes=len(ww),seed_a=s,seed_b=z,ARI=v))
        summary.append(dict(case=n,comparison=comp,treatment=t,multiplier=m,algorithm=a,level=k,scope=scope,nodes=len(ww),planned=len(items),**desc(vv)))
    sets={(t,m,a,s,k):at(r,k) for (t,m,a,s),r in rr.items() for k in LEVELS}
    for t in ['suppress','hide']:
        for m in MULT:
            for a in ALGS:
                for s in SEEDS:
                    r=rr[t,m,a,s]
                    for k in LEVELS:sets[t,m,a,s,k]=at(r,k)
                    quality.append(dict(case=n,treatment=t,multiplier=m,algorithm=a,seed=s,distinct_levels=len(r['levels']),FINAL_index='L'+str(len(r['levels'])-1),groups_L0=len(groups(at(r,'L0'))),groups_L1=len(groups(at(r,'L1'))) if at(r,'L1') is not None else None,groups_FINAL=len(groups(at(r,'FINAL'))),Q_FINAL=r['modularity_by_level'][-1]))
                    if a=='leiden' and (t=='suppress' or m==1.):
                        for i,p in enumerate(r['levels'][2:],2):
                            for j,ws in groups(p).items():
                                children=[dict(id=v,words=sorted(tt)) for v,tt in groups(r['levels'][i-1]).items() if tt<=ws]
                                extras.append(dict(case=n,treatment=t,multiplier=m if t=='suppress' else None,seed=s,level='L'+str(i),parent=j,words=sorted(ws),children=children,is_FINAL=i==len(r['levels'])-1))
                for k in LEVELS:
                    for scope,ww in [('visible',by[m]['nodes']),('core',core)]:
                        record('between_seeds',t,m,a,k,scope,ww,[(s,z,sets[t,m,a,s,k],sets[t,m,a,z,k]) for s,z in combinations(SEEDS,2)])
                    common=sorted(set(by[m]['nodes'])&ref)
                    for scope,ww in [('common_reference',common),('core',core)]:record('threshold_vs_1',t,m,a,k,scope,ww,[(s,s,sets[t,m,a,s,k],sets[t,1.,a,s,k]) for s in SEEDS])
            for k in LEVELS:
                for scope,ww in [('visible',by[m]['nodes']),('core',core)]:record('between_algorithms',t,m,'both',k,scope,ww,[(s,s,sets[t,m,'louvain',s,k],sets[t,m,'leiden',s,k]) for s in SEEDS])
    for m in MULT:
        for a in ALGS:
            for k in LEVELS:
                for scope,ww in [('visible',by[m]['nodes']),('core',core)]:record('between_treatments','both',m,a,k,scope,ww,[(s,s,sets['suppress',m,a,s,k],sets['hide',m,a,s,k]) for s in SEEDS])
    # Cross-seed algorithm agreement at the reference prevents treating matching numbers as shared randomness.
    for t in ['suppress','hide']:
        for k in LEVELS:record('algorithm_all_seed_pairs',t,1.,'both',k,'core',core,[(s,z,sets[t,1.,'louvain',s,k],sets[t,1.,'leiden',z,k]) for s in SEEDS for z in SEEDS])
    for k in LEVELS[:2]:
        pp=[sets['suppress',m,a,s,k] for m in MULT for a in ALGS for s in SEEDS]+[sets['hide',1.,a,s,k] for a in ALGS for s in SEEDS];available=sum(p is not None for p in pp)
        if available==480:
            sig=defaultdict(list)
            for w in core:sig[tuple(p[w] for p in pp)].append(w)
            persistent.extend(dict(case=n,level=k,words=ws,size=len(ws),outputs=480) for ws in sig.values() if len(ws)>1)
        for t in ['suppress','hide']:
            for m in MULT:
                ww=set(by[m]['nodes'])
                for a in ALGS:
                    for u,v in FOCAL_PAIRS:
                        ps=[sets[t,m,a,s,k] for s in SEEDS];valid=[p for p in ps if p is not None and u in p and v in p];co=sum(p[u]==p[v] for p in valid)
                        focal.append(dict(case=n,treatment=t,multiplier=m,algorithm=a,level=k,word1=u,word2=v,both_visible=u in ww and v in ww,available=len(valid),coassigned=co,fraction=co/len(valid) if valid else None))
    for m in MULT:
        for t in ['suppress','hide']:
            for a in ALGS:
                r=rr[t,m,a,1000];visible=set(by[m]['nodes'])
                for k in LEVELS:
                    p=at(r,k)
                    for j,ws in groups(p).items():seed1000.append(dict(case=n,treatment=t,multiplier=m,algorithm=a,level=k,group=j,full_size=len(ws),visible_words=sorted(ws&visible),hidden_count=len(ws-visible),words=sorted(ws)))
    for name,data in [('summary',summary),('scores',scores),('run_quality',quality),('leiden_extra_levels',extras),('persistent_blocks',persistent),('focal_pairs',focal),('seed1000_communities',seed1000)]:atomic(OUT/f'metrics/{n}_{name}.json',data)
    print('METRICS',n,len(scores),'scores',len(persistent),'strict blocks',flush=True)

def metrics(workers=4):
    names=[c['name'] for c in read(OUT/'source_cases.json')]
    with ProcessPoolExecutor(max_workers=workers) as pool:
        for f in as_completed([pool.submit(metrics_window,n) for n in names]):f.result()
    for name in ['summary','run_quality','leiden_extra_levels','persistent_blocks','focal_pairs','seed1000_communities']:export(name,[r for n in names for r in read(OUT/f'metrics/{n}_{name}.json')])
    count=0
    with (OUT/'tables/all_ARI_scores.csv').open('w',encoding='utf-8-sig',newline='') as f:
        w=None
        for n in names:
            rr=read(OUT/f'metrics/{n}_scores.json')
            if w is None:w=csv.DictWriter(f,fieldnames=list(rr[0]));w.writeheader()
            w.writerows(rr);count+=len(rr)
    status('metrics_complete',ARI_rows=count,logical_detector_conditions=4800,logical_display_conditions=8400,figures_pending=True,report_pending=True)
if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('action',choices=['prepare','compute','metrics']);ap.add_argument('--workers',type=int,default=6);a=ap.parse_args()
    if a.action=='prepare':prepare()
    else:globals()[a.action](a.workers)
