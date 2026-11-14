"""Controlled DE phrase preservation versus the frozen token campaign."""
import os
os.environ['PYTHONHASHSEED']='0'
os.environ['OPENBLAS_NUM_THREADS']='1'
os.environ['OMP_NUM_THREADS']='1'
from pathlib import Path
from collections import Counter,defaultdict
from concurrent.futures import ProcessPoolExecutor,as_completed
from datetime import datetime,timezone
from decimal import Decimal
from itertools import combinations
import argparse,csv,hashlib,json,math,re,shutil,time,unicodedata
import networkx as nx
import numpy as np
from scipy.sparse import csr_matrix
from audit_recovered_historical_data import wos
from sci2_normalizer import normalize_batch
from sci2_pruning import NativeGrid
from community_hierarchy import partitions,nested

ROOT=Path(__file__).resolve().parents[1]
ACTIVE=ROOT/'resultats/Historical_2021_2022_Comparison_Report/test again one ok'
BASE=ACTIVE/'campagne_complete_mots_cles_auteurs_20261110'
CORRECT=ACTIVE/'correction_cumul_2015_2022_DE_20261110'
OUT=ACTIVE/'comparaison_expressions_tokens_20261110'
REPS=['tokens','phrases','phrases_normalized']
ALGS=['louvain','leiden'];SEEDS=list(range(1000,1030));MULT=[.4,.6,.8,1.,1.2,1.4,1.6]
LEVELS=['L0','L1','L2','FINAL'];EXCLUDED='WOS:000450332600002'

def read(p):return json.loads(Path(p).read_text(encoding='utf-8'))
def save(p,d):
    p=Path(p);p.parent.mkdir(parents=True,exist_ok=True);tmp=p.with_suffix(p.suffix+'.pending')
    tmp.write_text(json.dumps(d,ensure_ascii=False,separators=(',',':')),encoding='utf-8');os.replace(tmp,p)
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def digest(d):return hashlib.sha256(json.dumps(d,sort_keys=True,separators=(',',':'),ensure_ascii=False).encode()).hexdigest()
def code(m):return 'm'+str(round(m*10)).zfill(2)
def status(state,**kw):save(OUT/'study_status.json',dict(state=state,updated_utc=datetime.now(timezone.utc).isoformat(),fields=['DE'],corpus=2333,representations=REPS,seeds=SEEDS,multipliers=MULT,report_pending=True,**kw))
def csvout(name,rows):
    if not rows:return
    p=OUT/'tables'/f'{name}.csv';p.parent.mkdir(exist_ok=True)
    with p.open('w',encoding='utf-8-sig',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(dict.fromkeys(k for r in rows for k in r)));w.writeheader()
        w.writerows({k:json.dumps(v,ensure_ascii=False) if isinstance(v,(list,dict)) else v for k,v in r.items()} for r in rows)
def graph(d):
    g=nx.Graph();g.add_nodes_from(d['nodes']);g.add_weighted_edges_from(d['edges']);return g
def serialize(g,df):
    d=dict(nodes=sorted(g),edges=[[min(u,v),max(u,v),float(x['weight'])] for u,v,x in sorted(g.edges(data=True),key=lambda e:(min(e[0],e[1]),max(e[0],e[1])))],frequencies={w:df[w] for w in sorted(g)})
    d['graph_sha256']=digest(dict(nodes=d['nodes'],edges=d['edges']));return d
def at(r,k):return r['levels'][-1] if k=='FINAL' else r['levels'][int(k[1:])] if int(k[1:])<len(r['levels']) else None
def groups(p):
    d=defaultdict(list)
    if p is not None:
        for w,j in p.items():d[j].append(w)
    return {j:sorted(ws) for j,ws in d.items()}
def desc(v):
    a=np.asarray([x for x in v if x is not None],float)
    if not len(a):return dict(valid=0,median=None,q25=None,q75=None,iqr=None,minimum=None,maximum=None)
    q1,med,q3=np.quantile(a,[.25,.5,.75]);return dict(valid=len(a),median=float(med),q25=float(q1),q75=float(q3),iqr=float(q3-q1),minimum=float(a.min()),maximum=float(a.max()))
def ari(y,z,ids=None):
    if ids is None:ids=np.flatnonzero((y>=0)&(z>=0))
    if len(ids)<2:return None
    a=y[ids];b=z[ids];_,a=np.unique(a,return_inverse=True);_,b=np.unique(b,return_inverse=True)
    cells=np.bincount(a*(int(b.max())+1)+b);ca=np.bincount(a);cb=np.bincount(b)
    s=int(np.sum(cells*(cells-1)));aa=int(np.sum(ca*(ca-1)));bb=int(np.sum(cb*(cb-1)));n=len(ids)*(len(ids)-1)
    expected=aa*bb/n;den=(aa+bb)/2-expected
    return float((s-expected)/den) if den else 1.
def clean(s):return re.sub(r'\s+',' ',unicodedata.normalize('NFKC',s).lower()).strip()
def casebase(n):return CORRECT if n=='cumulative_2015-2022' else BASE
def fullpath(rep,n):return OUT/f'{rep}/inputs/full/{n}.json'
def maskpath(rep,n,m):return OUT/f'{rep}/graphs/{n}_{code(m)}.json'
def termpath(rep,n):return OUT/f'{rep}/inputs/terms/{n}.json'
def runpath(h,a,s):return OUT/f'runs/{h[:16]}_{a[:2]}_{s}.json'

def prepare():
    for p in ['inputs','runs','metrics','tables','reports','figures','layouts','atlas_data','sources','native_cache']:(OUT/p).mkdir(parents=True,exist_ok=True)
    if (OUT/'preparation_verification.json').exists():
        assert read(OUT/'preparation_verification.json')['passed'];return
    assert nx.__version__=='3.2.1'
    cases=read(BASE/'source_cases.json');correct=read(CORRECT/'source_cases.json')[0]
    cases=[correct if d['name']==correct['name'] else d for d in cases]
    save(OUT/'source_cases.json',cases)
    records={};protected={};caseids={};baseline_terms={}
    def protect(p):protected[str(Path(p).relative_to(ROOT))]=sha(p)
    for c in cases:
        n=c['name'];source=casebase(n);src=source/f'inputs/source_exports/{n}.txt';protect(src)
        rr=[d for d in wos(src) if d['UT']!=EXCLUDED];caseids[n]=[d['UT'] for d in rr]
        tt=read(source/f'inputs/terms/{n}.json');baseline_terms[n]=tt
        assert set(caseids[n])=={d['UT'] for d in tt} and len(rr)==len(tt)==c['documents']
        for d in rr:
            if d['UT'] in records:assert records[d['UT']]==d
            else:records[d['UT']]=d
        save(OUT/f'inputs/records/{n}.json',rr)
    assert len(records)==2333
    cross=[d for c in cases if c['kind']=='cross_sectional' for d in caseids[c['name']]]
    assert len(cross)==len(set(cross))==2333
    assert len(caseids['cumulative_2015-2022'])==1499
    for c in cases:
        lo,hi=map(int,c['period'].split('-'))
        assert all(lo<=int(records[u]['PY'])<=hi for u in caseids[c['name']])
    stop=BASE/'inputs/recovered_stopwords.txt';protect(stop);shutil.copy2(stop,OUT/'inputs/recovered_stopwords.txt')
    stops=[s.strip() for s in stop.read_text(encoding='utf-8').splitlines() if s.strip()]
    cfg=read(ROOT/'resultats/campagne_20261106/etape03_titres_keywords_2417_seed1000/inputs/text_processing.json')
    patterns=[re.compile(p,re.I) for p in cfg['excluded_phrases_regex']]
    def token_text(s):
        # The recovered historical DE map uses the native stopword analyzer
        # directly. The regex removals in the older TI/AB experiments are not
        # part of this frozen DE-only baseline.
        return clean(s)
    # Native normalization is run once per distinct original keyword expression.
    original=sorted({clean(s) for d in records.values() for s in d.get('DE','').split(';') if clean(s)})
    items=[dict(id=str(i),text=token_text(s)) for i,s in enumerate(original)]
    normalized,provenance=normalize_batch(items,stops,cfg['sci2_plugins'],cfg['java'])
    lookup={s:dict(source=s,tokens=[x[1] for x in r['pairs']],token_sources=[x[0] for x in r['pairs']]) for s,r in zip(original,normalized)}
    stopset={clean(s) for s in stops}
    for s,v in lookup.items():
        v['phrase_normalized']=' '.join(v['tokens'])
        v['phrase_surface']=s if s not in stopset else ''
    save(OUT/'inputs/expression_dictionary.json',lookup);save(OUT/'inputs/native_normalization_provenance.json',provenance)
    docs=[];mismatches=[]
    for d in sorted(records.values(),key=lambda d:(int(d['PY']),d['UT'])):
        phrases=sorted({clean(s) for s in d.get('DE','').split(';') if clean(s)})
        terms=sorted({w for s in phrases for w in lookup[s]['tokens']})
        docs.append(dict(UT=d['UT'],year=int(d['PY']),DE=d.get('DE',''),TI=d.get('TI',''),SO=d.get('SO',''),expressions=phrases,tokens=terms,phrases=sorted({lookup[s]['phrase_surface'] for s in phrases if lookup[s]['phrase_surface']}),phrases_normalized=sorted({lookup[s]['phrase_normalized'] for s in phrases if lookup[s]['phrase_normalized']})))
    byut={d['UT']:d for d in docs}
    for n,tt in baseline_terms.items():
        for d in tt:
            if byut[d['UT']]['tokens']!=d['terms']:mismatches.append(dict(case=n,UT=d['UT'],expected=d['terms'],actual=byut[d['UT']]['tokens']))
    save(OUT/'inputs/native_token_reconstruction_mismatches.json',mismatches)
    if mismatches:raise AssertionError(('Native per-expression reconstruction differs from baseline',len(mismatches),mismatches[:2]))
    save(OUT/'inputs/all_records_with_representations.json',docs)
    missing=[dict(UT=d['UT'],year=d['year'],title=d['TI'],journal=d['SO']) for d in docs if not d['DE'].strip()]
    save(OUT/'inputs/records_without_author_keywords.json',missing);assert len(missing)==72
    allgraphs={};index=[];stats=[];coverage=[];reused=0
    for rep in REPS:
        for f in ['inputs/full','inputs/terms','graphs','native']:(OUT/rep/f).mkdir(parents=True,exist_ok=True)
        for c in cases:
            n=c['name'];source=casebase(n);rr=[byut[u] for u in caseids[n]]
            termrows=[dict(UT=d['UT'],year=d['year'],DE=d['DE'],expressions=d['expressions'],terms=d[rep]) for d in rr];save(termpath(rep,n),termrows)
            coverage.append(dict(representation=rep,case=n,records=len(rr),missing_DE=sum(not d['DE'].strip() for d in rr),no_surviving_units=sum(not d[rep] for d in rr),with_at_least_two_units=sum(len(d[rep])>=2 for d in rr)))
            if rep=='tokens':
                src=source/f'inputs/full/{n}.json';protect(src);shutil.copy2(src,fullpath(rep,n));f=read(src)
                for m in MULT:
                    src=source/f'graphs/{n}_{code(m)}.json';protect(src);shutil.copy2(src,maskpath(rep,n,m))
            else:
                df=Counter();ee=Counter()
                for d in rr:df.update(d[rep]);ee.update(combinations(d[rep],2))
                g=nx.Graph();g.add_nodes_from((w,dict(references=df[w])) for w in sorted(df));g.add_weighted_edges_from((u,v,w) for (u,v),w in sorted(ee.items()))
                f=serialize(g,df);save(fullpath(rep,n),f)
                grid=NativeGrid(g,[(1/3,1/3,0)],dict(retain_isolates=True,community_weight_mode='weighted',node_rank='attribute:references',rounding='half_up',strict_greater=True,java=cfg['java'],sci2_plugins=cfg['sci2_plugins'],pruning_cache=str(ROOT/'tmp/phrase_token_native')))
                pre,pr=grid.get(0);tau=pr['mean_pre_dichotomize_weight']*math.log10(pr['n_second']) if pr['n_second'] else 0.
                policy=c['filter']['threshold_policy'];cutoff=tau if policy=='unrounded' else math.floor(tau+.5)
                comparator=c['filter']['comparator']
                save(OUT/f'{rep}/native/{n}.json',dict(statistics=pr,formula_tau=tau,reference_cutoff=cutoff,comparator=comparator,manifest=read(grid.folder/'manifest.json'),output=read(grid.folder/'c0000.json'),labels=grid.labels,source='Same top-thirds native operators and rounding; threshold recalculated on this representation, not chosen using communities'))
                for m in MULT:
                    cut=float(Decimal(str(cutoff))*Decimal(str(m)));h=nx.Graph();h.add_nodes_from(sorted(pre));h.add_weighted_edges_from((u,v,x['weight']) for u,v,x in pre.edges(data=True) if (x['weight']>=cut if comparator=='>=' else x['weight']>cut))
                    isolates=sorted(nx.isolates(h));components=sorted(nx.connected_components(h),key=lambda s:(-len(s),sorted(s)));keep=next((s for s in components if len(s)>1),set());mask=h.subgraph(keep).copy();d=serialize(mask,df)
                    d.update(case=n,representation=rep,multiplier=m,cutoff=cut,reference_cutoff=cutoff,formula_tau=tau,comparator=comparator,selected_nodes=sorted(pre),isolated_before_component=isolates,discarded_nonisolated_nodes=sorted(set(h)-set(isolates)-keep),component_sizes_before=sorted(map(len,components),reverse=True));save(maskpath(rep,n,m),d)
            for t in ['suppress','hide']:
                for m in (MULT if t=='suppress' else [1.]):
                    p=maskpath(rep,n,m) if t=='suppress' else fullpath(rep,n);gdata=read(p);h=gdata['graph_sha256'];allgraphs[h]=str(p.relative_to(OUT))
                    for a in ALGS:
                        for seed in SEEDS:
                            target=runpath(h,a,seed)
                            if rep=='tokens' and not target.exists():
                                src=source/f'runs/{h[:16]}_{a[:2]}_{seed}.json';r=read(src);assert r['graph_sha256']==h and r['seed']==seed;protect(src)
                                save(target,{**r,'reused_from':str(src.relative_to(ROOT)),'source_sha256':sha(src),'computed_current_campaign':False});reused+=1
                            index.append(dict(representation=rep,case=n,treatment=t,multiplier=m if t=='suppress' else None,algorithm=a,seed=seed,graph_sha256=h,file=str(target.relative_to(OUT))))
            g=graph(f)
            for m in MULT:
                d=read(maskpath(rep,n,m));h=graph(d);components=list(nx.connected_components(h));isolates=d.get('isolated_before_component',[])
                stats.append(dict(representation=rep,case=n,multiplier=m,records=len(rr),full_nodes=len(g),full_edges=g.number_of_edges(),full_isolates=nx.number_of_isolates(g),full_components=nx.number_connected_components(g),retained_nodes=len(h),retained_edges=h.number_of_edges(),retained_components=len(components),isolates_removed=len(isolates),discarded_nonisolated_nodes=len(d.get('discarded_nonisolated_nodes',[])),full_weight=g.size(weight='weight'),retained_weight=h.size(weight='weight'),fraction_weight_retained=h.size(weight='weight')/g.size(weight='weight') if g.number_of_edges() else None,cutoff=d.get('cutoff',d.get('scaled_cutoff')),comparator=d.get('comparator',c['filter']['comparator'])))
            print('PREPARED',rep,n,'full',len(g),g.number_of_edges(),'reference',len(read(maskpath(rep,n,1.))['nodes']),flush=True)
    for p in [ROOT/'scripts/community_hierarchy.py',ROOT/'sci2_robustness/vendor/networkx_leiden/leiden.py',ROOT/'scripts/sci2_normalizer.py',ROOT/'scripts/lucene_normalize.js',ROOT/'scripts/sci2_pruning.py',ROOT/'scripts/sci2_pruning_grid.js']:protect(p)
    reused=sum(not read(p).get('computed_current_campaign',True) for p in (OUT/'runs').glob('*.json'))
    save(OUT/'unique_graphs.json',allgraphs);save(OUT/'run_manifest.json',index);save(OUT/'graph_statistics.json',stats);save(OUT/'corpus_coverage.json',coverage);save(OUT/'protected_sources.json',protected)
    protocol=dict(created_utc=datetime.now(timezone.utc).isoformat(),user_request='Complete phrase preserving analysis versus frozen token condition',corpus=2333,raw_export_count_not_used_as_analytical_denominator=2418,fields=['DE'],titles_used=False,abstracts_used=False,Keywords_Plus_used=False,thesaurus_used=False,excluded_UT=EXCLUDED,representations=dict(tokens='Unchanged native Sci2 word stem sets, independently reconstructed exactly from source keyword entries; native stopwords only, no regex query removals imported from earlier TI/AB conditions',phrases='Complete semicolon-delimited author keyword entries; NFKC, lower case and collapsed whitespace; internal punctuation, hyphens and words preserved; discard only full-entry matches to recovered stopwords including explicitly listed query expressions; no stemming',phrases_normalized='Decomposition control: identical native Sci2 word normalization and stopwords applied within each source keyword, ordered stem sequence retained as one atomic node; every per-document union of component tokens equals frozen baseline exactly'),confounding='Tokens versus literal phrases changes decomposition and normalization. Tokens versus normalized phrases is the controlled boundary comparison. Literal versus normalized phrases assesses normalization within atomic expressions.',seeds=SEEDS,algorithms=ALGS,multipliers=MULT,reference_seed=1000,resolution=1,python_hash_seed=0,networkx=nx.__version__,weights='Binary document incidence; one cooccurrence per unordered pair per record',pruning='Original native top-thirds extraction and half-up rounding. Same per-window comparator. Recalculate each representation reference cutoff from rounded mean edge weight times log10 second-stage nodes, then scale without re-rounding.',cross_sectional_2021_2022_note='Frozen token mask uses approved effective >=15. New phrase conditions recompute their own rounded cutoff and retain >= as comparator; not claimed to reproduce an unrecorded historical UI step.',suppress='Delete filtered elements; log isolates and smaller components; detect on largest nonisolated retained component',hide='Detect on full network with all components and isolates; apply same representation-specific suppression mask to display only',levels='L0 first distinct, L1 second, L2 third if returned; FINAL actual last distinct and index reported. No imputed missing levels.',primary_cross_representation_metric='Document-projected ARI on identical UTs. Each distinct original keyword has unit mass: token mode distributes that mass equally among its distinct surviving stems, atomic modes assign it to the keyword node. Filtered units contribute zero mass. A unique maximum selects document community; zero coverage and tied maxima are unassigned. Common eligible UTs across all paired seeds are fixed before computing the primary 30-score distribution; pairwise intersections are sensitivity results.',secondary_cross_representation_metric='ARI on original keyword-expression units only where token constituents all participate and unanimously share one community. Fragmentation and coverage are reported; no ARI on unlike raw node universes.',logical_detector_conditions=14400,logical_display_conditions=25200,token_detector_outputs_reused=reused,visuals='Weighted Kamada Kawai cross sections, native GUESS GEM cumulative. Frozen union-mask geometry within each representation; different vocabularies do not imply a shared node canvas. Seed1000 illustrated in Word, every seed and multiplier in offline atlas.',current_cumulative_2015_2022_records=1499,case_record_counts={c['name']:len(caseids[c['name']]) for c in cases})
    protocol['pruning']='Original native top-thirds extraction and half-up rounding of extraction counts. Recompute tau = mean edge weight times log10(second-stage node count). Preserve the recovered per-window cutoff policy: unrounded tau for cross-sectional 2023–2024; nearest integer otherwise. Preserve each comparison operator. The ambiguous 2021–2022 approved token >=15 is retained for tokens; atomic graphs use a predeclared rounded recomputation with >=.'
    protocol['reference_cutoff_policy_by_case']={c['name']:c['filter']['threshold_policy'] for c in cases}
    save(OUT/'protocol.json',protocol);csvout('graph_statistics',stats);csvout('corpus_coverage',coverage)
    save(OUT/'preparation_verification.json',dict(passed=True,unique_records=2333,missing_DE=72,all_ten_case_UT_sets_equal_to_token_baseline=True,corrected_cumulative_2015_2022_records=1499,per_expression_native_token_union_equals_baseline=True,distinct_source_expressions=len(original),unique_graphs=len(allgraphs),baseline_outputs_reused=reused))
    status('prepared',unique_graphs=len(allgraphs),cached_outputs=len(list((OUT/'runs').glob('*.json'))),phase='preparation_complete')

def detect_worker(job):
    h,path,a=job;d=read(OUT/path);g=graph(d);made=0
    for s in SEEDS:
        dest=runpath(h,a,s)
        if dest.exists():continue
        start=time.monotonic();pp=partitions(g,a if a=='louvain' else 'leiden_hierarchy',s)
        qq=[nx.community.modularity(g,list(groups(p).values()),weight='weight') if g.number_of_edges() else 0. for p in pp]
        save(dest,dict(algorithm=a,seed=s,python_hash_seed=0,graph_sha256=h,levels=pp,modularity_by_level=qq,distinct_levels=len(pp),elapsed_seconds=time.monotonic()-start,computed_current_campaign=True));made+=1
    return h,a,made

def compute(workers=6):
    gg=read(OUT/'unique_graphs.json');jobs=[(h,p,a) for h,p in gg.items() for a in ALGS if any(not runpath(h,a,s).exists() for s in SEEDS)]
    jobs.sort(key=lambda x:-len(read(OUT/x[1])['edges']));total=len(gg)*60
    def required_done():return sum(runpath(h,a,s).exists() for h in gg for a in ALGS for s in SEEDS)
    status('running',phase='community_detection',unique_output_total=total,cached_outputs=required_done(),workers=workers)
    with ProcessPoolExecutor(max_workers=workers) as pool:
        for f in as_completed([pool.submit(detect_worker,j) for j in jobs]):
            h,a,made=f.result();done=required_done();status('running',phase='community_detection',unique_output_total=total,cached_outputs=done,workers=workers);print('DETECTION',done,'/',total,a,h[:10],flush=True)
    assert required_done()==total
    status('detection_complete',unique_outputs=total)

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('action',choices=['prepare','compute']);ap.add_argument('--workers',type=int,default=6);a=ap.parse_args()
    if a.action=='prepare':prepare()
    else:compute(a.workers)
