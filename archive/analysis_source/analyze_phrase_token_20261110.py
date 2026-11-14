"""Comparable-document and source-expression tests for the phrase campaign."""
from campaign_phrase_token_20261110 import *
from functools import lru_cache
from scipy.sparse import save_npz,load_npz
import gzip

CONTRASTS=[('tokens','phrases'),('tokens','phrases_normalized'),('phrases_normalized','phrases')]

def protocol():
    p=OUT/'analysis_protocol.json'
    settings=dict(primary_unit='Unique WoS accession UT, identical within each contrast',document_vote='One unit per distinct original normalized keyword entry. Distribute unit mass evenly among distinct native stems for token graph; assign unit to the whole-keyword node in atomic graphs. Multiple original forms mapping to one normalized node retain their source-keyword votes in this document projection only. Graph edge weights remain binary per record.',unassigned_codes={'-1':'no represented keyword mass','-2':'tied maximum community mass','-3':'partition level unavailable'},primary_scope='Fixed intersection of assigned UTs across all available paired seeds within case, treatment, multiplier, algorithm and level. Report planned and valid seeds; fewer than 30 is conditional level availability. A pairwise-intersection ARI is secondary.',degenerate='Standard ARI is retained for partitions with a single document group, but degeneracy is counted and cannot establish thematic stability.',within_representation='Report both node partition seed ARIs on all detector nodes and projected document seed ARIs on fixed eligible documents, 435 unordered pairs when all 30 levels exist.',secondary_unit='Original source keyword expression. Atomic graphs assign node community. Token graph assigns only when all distinct constituents survive and share exactly one community; a split is -2 and an uncovered constituent -1. Report coverage and fragmentation.',reference_community_matching='At m=1 seed1000, maximum-overlap one-to-one assignment on common projected documents; document intersections, Jaccard, retention, purity and labels from actual community nodes are exported.',matching_label_rule='Exact only for identical projected document sets; high_overlap when matched Jaccard >=0.8, operational descriptive threshold, not a significance test.',strict_cores='Source expressions with nonnegative assignment in every required partition; equal signatures define maximal invariant coassignment cores. Full-hide cores use 180 outputs across three representations, two algorithms, 30 seeds. Full-campaign cores use 1440 logical detector outputs including seven suppression thresholds and full hide. Missing hierarchy levels prevent universal certification.',hide_multipliers='One full partition per seed reused for all seven display masks. Cross-representation hide ARI is calculated once, not replicated as seven independent results.',inference='Descriptive medians, quartiles, IQR and ranges. Seed-pair scores are dependent and not treated as independent samples. No automatic scientific topic label or thesaurus mapping is introduced.')
    if p.exists():assert read(p)==settings
    else:save(p,settings)

def casecode(n):return ('x' if n.startswith('cross') else 'u')+str(['2015-2016','2017-2018','2019-2020','2021-2022','2023-2024'].index(n.split('_')[-1]) if n.startswith('cross') else ['2015-2016','2015-2018','2015-2020','2015-2022','2015-2024'].index(n.split('_')[-1]))

def projection(W,p,fullnodes):
    size=W.shape[0]
    if p is None:return np.full(size,-3,np.int32),np.zeros(size,np.float32),np.zeros(size,np.float32)
    if not p:return np.full(size,-1,np.int32),np.zeros(size,np.float32),np.zeros(size,np.float32)
    ix={w:i for i,w in enumerate(fullnodes)};cc=max(p.values())+1
    C=csr_matrix((np.ones(len(p)),([ix[w] for w in p],list(p.values()))),shape=(len(fullnodes),cc))
    A=(W@C).tocsr();mass=np.asarray(A.sum(axis=1)).ravel();maximum=A.max(axis=1).toarray().ravel();best=np.asarray(A.argmax(axis=1)).ravel().astype(np.int32)
    rowids=np.repeat(np.arange(size),np.diff(A.indptr));ties=np.bincount(rowids,weights=np.isclose(A.data,np.repeat(maximum,np.diff(A.indptr)),rtol=0,atol=1e-10).astype(int),minlength=size)
    best[mass<=1e-12]=-1;best[(mass>1e-12)&(ties!=1)]=-2
    share=np.divide(maximum,mass,out=np.zeros(size),where=mass>1e-12)
    return best,mass.astype(np.float32),share.astype(np.float32)

def source_projection(expressions,lookup,rep,p):
    if p is None:return np.full(len(expressions),-3,np.int32)
    y=np.full(len(expressions),-1,np.int32)
    for i,e in enumerate(expressions):
        if rep=='tokens':
            words=set(lookup[e]['tokens'])
            if words and words<=p.keys():
                vals={p[w] for w in words};y[i]=next(iter(vals)) if len(vals)==1 else -2
        else:
            node=lookup[e]['phrase_surface' if rep=='phrases' else 'phrase_normalized']
            if node and node in p:y[i]=p[node]
    return y

def window(n):
    protocol();(OUT/'proj').mkdir(exist_ok=True);(OUT/'metrics').mkdir(exist_ok=True)
    lookup=read(OUT/'inputs/expression_dictionary.json');docs=read(OUT/f'inputs/records/{n}.json');uts=[d['UT'] for d in docs]
    source_terms=read(termpath('tokens',n));assert uts==[d['UT'] for d in source_terms]
    expressions=sorted({e for d in source_terms for e in d['expressions']});expression_df=Counter(e for d in source_terms for e in d['expressions']);E=len(expressions);D=len(docs)
    save(OUT/f'metrics/{casecode(n)}_units.json',dict(UTs=uts,source_expressions=expressions,expression_df=dict(expression_df)))
    index=[r for r in read(OUT/'run_manifest.json') if r['case']==n];runindex={(r['representation'],r['treatment'],r['multiplier'] if r['multiplier'] is not None else 1.,r['algorithm'],r['seed']):r['file'] for r in index}
    @lru_cache(maxsize=2000)
    def loadrun(rep,t,m,a,s):return read(OUT/runindex[rep,t,m,a,s])
    projections={};source_labels={};quality=[];availability=[];node_seed_summaries=[];inventory=[];extra=[];fragmentation=[];details=[]
    rawpath=OUT/f'metrics/{casecode(n)}_scores.jsonl.gz'
    raw=gzip.open(rawpath,'wt',encoding='utf-8')
    def writerows(rows):
        for r in rows:raw.write(json.dumps(r,ensure_ascii=False,separators=(',',':'))+'\n')
    def score_series(meta,Y,Z,source=False):
        # Every available paired seed shares one fixed common unit set.
        valid=[i for i in range(30) if not np.all(Y[i]==-3) and not np.all(Z[i]==-3)]
        fixed=np.flatnonzero(np.logical_and.reduce([(Y[i]>=0)&(Z[i]>=0) for i in valid])) if valid else np.array([],int)
        rr=[];pairv=[];vals=[];deg=0
        for i in valid:
            common=np.flatnonzero((Y[i]>=0)&(Z[i]>=0));v=ari(Y[i],Z[i],fixed);pv=ari(Y[i],Z[i],common)
            g1=len(np.unique(Y[i,fixed])) if len(fixed) else 0;g2=len(np.unique(Z[i,fixed])) if len(fixed) else 0;degen=g1<2 or g2<2;deg+=degen
            rr.append({**meta,'seed1':SEEDS[i],'seed2':SEEDS[i],'common_units':len(fixed),'pairwise_common_units':len(common),'ARI':v,'pairwise_intersection_ARI':pv,'groups1':g1,'groups2':g2,'degenerate':degen})
            vals.append(v);pairv.append(pv)
        writerows(rr)
        return {**meta,'planned_seed_pairs':30,'available_seed_pairs':len(valid),'universal_level':len(valid)==30,'fixed_common_units':len(fixed),'eligible_fraction':len(fixed)/(E if source else D),'degenerate_pairs':deg,**desc(vals),'pairwise_intersection_summary':desc(pairv)},fixed
    def seed_summary(meta,Y):
        valid=[i for i in range(30) if not np.all(Y[i]==-3)]
        fixed=np.flatnonzero(np.logical_and.reduce([Y[i]>=0 for i in valid])) if valid else np.array([],int)
        rows=[]
        for i,j in combinations(valid,2):rows.append({**meta,'seed1':SEEDS[i],'seed2':SEEDS[j],'common_units':len(fixed),'ARI':ari(Y[i],Y[j],fixed)})
        writerows(rows)
        return {**meta,'planned_runs':30,'available_runs':len(valid),'fixed_common_units':len(fixed),**desc([r['ARI'] for r in rows])}

    for rep in REPS:
        full=read(fullpath(rep,n));nodes=full['nodes'];nodeix={w:i for i,w in enumerate(nodes)};row=[];col=[];val=[]
        for i,d in enumerate(source_terms):
            mass=Counter()
            for e in d['expressions']:
                if rep=='tokens':
                    words=set(lookup[e]['tokens'])
                    for w in words:mass[w]+=1/len(words)
                else:
                    w=lookup[e]['phrase_surface' if rep=='phrases' else 'phrase_normalized']
                    if w:mass[w]+=1
            for w,v in mass.items():row.append(i);col.append(nodeix[w]);val.append(v)
        W=csr_matrix((val,(row,col)),shape=(D,len(nodes)))
        for t in ['suppress','hide']:
            for m in (MULT if t=='suppress' else [1.]):
                data=read(maskpath(rep,n,m)) if t=='suppress' else full;dn=data['nodes']
                for a in ALGS:
                    Y=np.full((30,len(LEVELS),D),-3,np.int32);X=np.full((30,len(LEVELS),E),-3,np.int32);M=np.zeros((30,len(LEVELS),D),np.float32);S=M.copy();N=np.full((30,len(LEVELS),len(dn)),-3,np.int32)
                    for i,s in enumerate(SEEDS):
                        r=loadrun(rep,t,m,a,s)
                        quality.append(dict(case=n,representation=rep,treatment=t,multiplier=m if t=='suppress' else None,algorithm=a,seed=s,distinct_levels=len(r['levels']),groups_by_level=[len(set(p.values())) for p in r['levels']],FINAL_index=len(r['levels'])-1,Q_FINAL=r['modularity_by_level'][-1],nodes=len(dn),edges=len(data['edges'])))
                        if s==1000:
                            for k in LEVELS:
                                p=at(r,k)
                                for j,ws in groups(p).items():inventory.append(dict(case=n,representation=rep,treatment=t,multiplier=m if t=='suppress' else None,algorithm=a,seed=s,level=k,community=j,size=len(ws),members=ws,top_members=sorted(ws,key=lambda w:(-full['frequencies'][w],w))[:12],is_FINAL=(k=='FINAL' or (k!='FINAL' and int(k[1:])==len(r['levels'])-1))))
                            if a=='leiden':
                                for ki,p in enumerate(r['levels'][2:],2):
                                    prev=groups(r['levels'][ki-1]);gg=groups(p)
                                    for j,ws in gg.items():extra.append(dict(case=n,representation=rep,treatment=t,multiplier=m if t=='suppress' else None,seed=s,level='L'+str(ki),is_FINAL=ki==len(r['levels'])-1,parent=j,members=ws,children=[dict(id=q,members=ww) for q,ww in prev.items() if ww and p[ww[0]]==j]))
                        for ki,k in enumerate(LEVELS):
                            p=at(r,k);Y[i,ki],M[i,ki],S[i,ki]=projection(W,p,nodes);X[i,ki]=source_projection(expressions,lookup,rep,p)
                            if p is not None:N[i,ki]=[p[w] for w in dn]
                    key=(rep,t,m,a);projections[key]=Y;source_labels[key]=X
                    dest=OUT/f'proj/{casecode(n)}_{REPS.index(rep)}_{t[0]}{code(m)}_{a[:2]}.npz'
                    np.savez_compressed(dest,document_labels=Y,source_expression_labels=X,document_mass=M,dominant_share=S)
                    for ki,k in enumerate(LEVELS):
                        meta=dict(case=n,representation=rep,treatment=t,multiplier=m if t=='suppress' else None,algorithm=a,level=k)
                        node_seed_summaries.append(seed_summary({**meta,'comparison':'within_representation_between_seeds','unit':'network_node'},N[:,ki]))
                        node_seed_summaries.append(seed_summary({**meta,'comparison':'within_representation_between_seeds','unit':'projected_document'},Y[:,ki]))
                        av=[i for i in range(30) if not np.all(Y[i,ki]==-3)]
                        availability.append({**meta,'records':D,'available_runs':len(av),'assigned_documents':desc([int(np.sum(Y[i,ki]>=0)) for i in av]),'tied_documents':desc([int(np.sum(Y[i,ki]==-2)) for i in av]),'unrepresented_documents':desc([int(np.sum(Y[i,ki]==-1)) for i in av]),'assigned_dominant_share':desc([float(np.median(S[i,ki][Y[i,ki]>=0])) for i in av if np.any(Y[i,ki]>=0)])})
                        for i in av:
                            x=X[i,ki];fully=(x>=0)|(x==-2);weights=np.array([expression_df[e] for e in expressions]);den=int(fully.sum());fr=int((x==-2).sum())
                            fragmentation.append({**meta,'seed':SEEDS[i],'source_expressions':E,'fully_covered_expressions':den,'unanimously_assigned_expressions':int((x>=0).sum()),'split_expressions':fr,'split_fraction_of_fully_covered':fr/den if den else None,'weighted_split_fraction':float(weights[x==-2].sum()/weights[fully].sum()) if weights[fully].sum() else None,'note':'Atomic phrases have zero internal splits by construction; zero is not an empirical quality advantage.' if rep!='tokens' else ''})
                    print('PROJECTED',n,rep,t,m,a,flush=True)

    comparisons=[];matching=[]
    def get(d,rep,t,m,a,k):return d[rep,t,m,a][:,LEVELS.index(k)]
    for rep1,rep2 in CONTRASTS:
        for t in ['suppress','hide']:
            for m in (MULT if t=='suppress' else [1.]):
                for a in ALGS:
                    for k in LEVELS:
                        meta=dict(case=n,comparison='between_representations',representation1=rep1,representation2=rep2,treatment=t,multiplier=m if t=='suppress' else None,algorithm=a,level=k)
                        for unit,data in [('projected_document',projections),('source_expression',source_labels)]:
                            Y=get(data,rep1,t,m,a,k);Z=get(data,rep2,t,m,a,k)
                            summary,fixed=score_series({**meta,'unit':unit},Y,Z,unit=='source_expression');comparisons.append(summary)
                            if unit=='projected_document' and m==1 and len(fixed)>=2:
                                y,z=Y[0],Z[0]
                                if np.all(y[fixed]>=0) and np.all(z[fixed]>=0):
                                    from scipy.optimize import linear_sum_assignment
                                    g1=sorted(set(y[fixed]));g2=sorted(set(z[fixed]));ii={g:i for i,g in enumerate(g1)};jj={g:j for j,g in enumerate(g2)};mat=np.zeros((len(g1),len(g2)),int)
                                    for q in fixed:mat[ii[y[q]],jj[z[q]]]+=1
                                    aa,bb=linear_sum_assignment(-mat);pairs={g1[i]:g2[j] for i,j in zip(aa,bb) if mat[i,j]>0}
                                    rp1=at(loadrun(rep1,t,m,a,1000),k);rp2=at(loadrun(rep2,t,m,a,1000),k);gg1=groups(rp1);gg2=groups(rp2)
                                    df1=read(fullpath(rep1,n))['frequencies'];df2=read(fullpath(rep2,n))['frequencies']
                                    for j in g1:
                                        lhs={q for q in fixed if y[q]==j};target=pairs.get(j);rhs={q for q in fixed if z[q]==target} if target is not None else set();inter=lhs&rhs;union=lhs|rhs;jac=len(inter)/len(union) if union else 0.
                                        matching.append({**meta,'seed':1000,'community1':int(j),'community2':int(target) if target is not None else None,'documents1':len(lhs),'documents2':len(rhs),'intersection':len(inter),'Jaccard':jac,'retention':len(inter)/len(lhs),'purity':len(inter)/len(rhs) if rhs else None,'status':'exact_projected_documents' if lhs==rhs else 'high_overlap' if jac>=.8 else 'reconfigured','top_members1':sorted(gg1[j],key=lambda w:(-df1[w],w))[:12],'top_members2':sorted(gg2[target],key=lambda w:(-df2[w],w))[:12] if target is not None else [],'intersection_UTs':[uts[q] for q in sorted(inter)]})
    # Algorithm, treatment and threshold contrasts use comparable document IDs.
    for rep in REPS:
        for t in ['suppress','hide']:
            for m in (MULT if t=='suppress' else [1.]):
                for k in LEVELS:
                    comparisons.append(score_series(dict(case=n,comparison='between_algorithms',representation1=rep,representation2=rep,treatment=t,multiplier=m if t=='suppress' else None,algorithm='both',level=k,unit='projected_document'),get(projections,rep,t,m,'louvain',k),get(projections,rep,t,m,'leiden',k))[0])
        for a in ALGS:
            for m in MULT:
                for k in LEVELS:
                    common=dict(case=n,representation1=rep,representation2=rep,multiplier=m,algorithm=a,level=k,unit='projected_document')
                    comparisons.append(score_series({**common,'comparison':'suppress_vs_hide','treatment':'both'},get(projections,rep,'suppress',m,a,k),get(projections,rep,'hide',1.,a,k))[0])
                    comparisons.append(score_series({**common,'comparison':'threshold_vs_1','treatment':'suppress'},get(projections,rep,'suppress',m,a,k),get(projections,rep,'suppress',1.,a,k))[0])
    # Fixed exact source expressions, chosen by input frequency only.
    focus=sorted([e for e in expressions if lookup[e]['phrase_surface'] and lookup[e]['tokens']],key=lambda e:(-expression_df[e],e))[:24]
    wanted=['metric learning','appearance model','video surveillance','deep learning','convolutional neural network','convolutional neural networks','feature fusion','domain adaptation','unsupervised learning','generative adversarial network','attention mechanism','vision transformer','occlusion','multi-scale','clothes-changing person re-identification','visible-infrared person re-identification']
    focus=sorted(set(focus+[e for e in wanted if e in expression_df]),key=lambda e:(-expression_df[e],e));fx={e:expressions.index(e) for e in focus};focal=[]
    for rep in REPS:
        for t in ['suppress','hide']:
            for a in ALGS:
                X=source_labels[rep,t,1.,a]
                for ki,k in enumerate(LEVELS):
                    for e,f in combinations(focus,2):
                        y,z=X[:,ki,fx[e]],X[:,ki,fx[f]];ok=(y>=0)&(z>=0);co=ok&(y==z)
                        focal.append(dict(case=n,representation=rep,treatment=t,multiplier=1.,algorithm=a,level=k,expression1=e,expression2=f,documents1=expression_df[e],documents2=expression_df[f],available_seeds=int(ok.sum()),coassigned_seeds=int(co.sum()),coassignment_fraction=float(co.sum()/ok.sum()) if ok.sum() else None))
    cores=[];core_coverage=[]
    for k in LEVELS:
        ki=LEVELS.index(k)
        for scope in ['full_hide','full_campaign']:
            arrays=[v[:,ki,:] for (rep,t,m,a),v in source_labels.items() if scope=='full_campaign' or t=='hide'];A=np.concatenate(arrays,axis=0);available=~np.all(A==-3,axis=1);universal=bool(available.all());eligible=np.all(A>=0,axis=0) if universal else np.zeros(E,bool);sig=defaultdict(list)
            for i in np.flatnonzero(eligible):sig[tuple(A[:,i])].append(expressions[i])
            bb=[es for es in sig.values() if len(es)>1]
            core_coverage.append(dict(case=n,scope=scope,level=k,planned_partitions=A.shape[0],available_levels=int(available.sum()),universal_level=universal,eligible_expressions=int(eligible.sum()),persistent_blocks=len(bb),expressions_in_blocks=sum(map(len,bb))))
            cores.extend(dict(case=n,scope=scope,level=k,expressions=es,size=len(es),required_partitions=A.shape[0]) for es in bb)
    raw.close()
    result=dict(case=n,records=D,source_expressions=E,comparisons=comparisons,seed_summaries=node_seed_summaries,document_availability=availability,run_quality=quality,fragmentation=fragmentation,community_matching=matching,seed1000_inventory=inventory,leiden_additional_levels=extra,focal_pairs=focal,persistent_expression_cores=cores,persistent_core_coverage=core_coverage,focus_expressions=focus)
    save(OUT/f'metrics/{casecode(n)}_summary.json',result)
    print('METRICS_COMPLETE',n,'comparisons',len(comparisons),'communities',len(inventory),'strict cores',len(cores),flush=True)
    return n

def main(workers=3):
    protocol();names=[c['name'] for c in read(OUT/'source_cases.json')]
    status('metrics_running',phase='cross_representation_comparison')
    pending=[n for n in names if not (OUT/f'metrics/{casecode(n)}_summary.json').exists()]
    with ProcessPoolExecutor(max_workers=workers) as pool:
        for f in as_completed([pool.submit(window,n) for n in pending]):f.result()
    keys=['comparisons','seed_summaries','document_availability','run_quality','fragmentation','community_matching','seed1000_inventory','leiden_additional_levels','focal_pairs','persistent_expression_cores','persistent_core_coverage']
    for key in keys:
        rows=[r for n in names for r in read(OUT/f'metrics/{casecode(n)}_summary.json')[key]];save(OUT/(key+'.json'),rows);csvout(key,rows)
    status('metrics_complete',phase='figures_and_report_pending')

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--workers',type=int,default=3);ap.add_argument('--freeze-only',action='store_true');ap.add_argument('--case');args=ap.parse_args()
    if args.freeze_only:protocol()
    elif args.case:window(args.case)
    else:main(args.workers)
