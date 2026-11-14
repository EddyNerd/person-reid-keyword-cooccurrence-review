"""Recalculate T/N/P publication and source-expression agreement.

Uses the published record incidence and saved partitions, with no detector rerun.
The voting units, tie tolerance and fixed-common-seed eligibility rule follow
the recorded analysis implementation. Python standard library only.
"""
from pathlib import Path
from collections import Counter
from itertools import combinations
import argparse,csv,gzip,json,math,statistics

from saved_partitions import find_saved

from paths import ROOT
SEEDS=list(range(1000,1030))
REP_NAME={'T':'tokens','N':'phrases_normalized','P':'phrases'}

def read_gz(path):
    with gzip.open(path,'rt',encoding='utf-8') as f:return json.load(f)

def partition(record,level):
    if level=='FINAL':return record['levels'][-1]
    index=int(level[1:])
    return record['levels'][index] if index<len(record['levels']) else None

def document_labels(records,lookup,rep,p):
    if p is None:return [-3]*len(records)
    if not p:return [-1]*len(records)
    labels=[]
    for record in records:
        mass=Counter()
        for expr in record['expressions']:
            item=lookup[expr]
            if rep=='T':
                words=set(item['tokens'])
                for w in words:mass[w]+=1/len(words)
            else:
                word=item['phrase_normalized' if rep=='N' else 'phrase_surface']
                if word:mass[word]+=1
        votes=Counter()
        # This is the full-graph column order used by the sparse implementation.
        for word in sorted(mass):
            if word in p:votes[p[word]]+=mass[word]
        total=sum(votes.values())
        if total<=1e-12:
            labels.append(-1)
        else:
            maximum=max(votes.values())
            winners=[group for group,value in votes.items() if abs(value-maximum)<=1e-10]
            labels.append(winners[0] if len(winners)==1 else -2)
    return labels

def source_labels(expressions,lookup,rep,p):
    if p is None:return [-3]*len(expressions)
    result=[]
    for expr in expressions:
        item=lookup[expr]
        if rep=='T':
            words=set(item['tokens'])
            if not words or not words<=p.keys():result.append(-1)
            else:
                values={p[w] for w in words}
                result.append(next(iter(values)) if len(values)==1 else -2)
        else:
            node=item['phrase_normalized' if rep=='N' else 'phrase_surface']
            result.append(p.get(node,-1) if node else -1)
    return result

def choose2(n):return n*(n-1)//2

def ari(a,b):
    if len(a)<2:return None
    cells=Counter(zip(a,b));aa=Counter(a);bb=Counter(b)
    nij=sum(choose2(n) for n in cells.values())
    ai=sum(choose2(n) for n in aa.values());bj=sum(choose2(n) for n in bb.values())
    total=choose2(len(a))
    numerator=2*(total*nij-ai*bj)
    denominator=total*(ai+bj)-2*ai*bj
    return numerator/denominator if denominator else 1.0

def quantile(values,p):
    pos=(len(values)-1)*p;lo=math.floor(pos);hi=math.ceil(pos)
    return values[lo]+(values[hi]-values[lo])*(pos-lo)

def summary(y,z):
    valid=[i for i in range(30) if not all(v==-3 for v in y[i]) and not all(v==-3 for v in z[i])]
    if valid:
        fixed=[j for j in range(len(y[0])) if all(y[i][j]>=0 and z[i][j]>=0 for i in valid)]
    else:fixed=[]
    scores=[];degenerate=0
    for i in valid:
        a=[y[i][j] for j in fixed];b=[z[i][j] for j in fixed]
        value=ari(a,b)
        if value is not None:scores.append(value)
        degenerate+=len(set(a))<2 or len(set(b))<2
    values=sorted(scores)
    return {'planned_seed_pairs':30,'available_seed_pairs':len(valid),'fixed_common_units':len(fixed),'eligible_fraction':len(fixed)/len(y[0]) if y and y[0] else 0.,'degenerate_pairs':degenerate,'valid':len(values),'median':statistics.median(values) if values else None,'q25':quantile(values,.25) if values else None,'q75':quantile(values,.75) if values else None,'minimum':min(values) if values else None,'maximum':max(values) if values else None}

def calculate(case,treatment,multiplier,algorithm,level,records,lookup,index,label_writer=None):
    first,last=map(int,case.rsplit('_',1)[1].split('-'))
    selected=[r for r in records if first<=r['year']<=last]
    expressions=sorted({e for r in selected for e in r['expressions']})
    doc={};expr={}
    for rep in ['T','N','P']:
        graph=next(r for r in index if r['representation']==rep and r['case']==case and r['treatment']==treatment and (treatment=='hide' or abs(float(r['multiplier'])-multiplier)<1e-9))
        doc[rep]=[];expr[rep]=[]
        for seed in SEEDS:
            run=find_saved(graph['graph_sha256'],algorithm,seed,'native' if rep=='T' else 'TNP')
            p=partition(run,level)
            doc[rep].append(document_labels(selected,lookup,rep,p))
            expr[rep].append(source_labels(expressions,lookup,rep,p))
            if label_writer is not None:
                for unit,ids,values in [('projected_document',[r['UT'] for r in selected],doc[rep][-1]),('source_expression',expressions,expr[rep][-1])]:
                    for unit_id,label in zip(ids,values):
                        label_writer.writerow({'case':case,'representation':rep,'treatment':treatment,'multiplier':multiplier if treatment=='suppress' else '', 'algorithm':algorithm,'seed':seed,'level':level,'unit':unit,'unit_id':unit_id,'label':label})
    result=[]
    for a,b in [('T','P'),('T','N'),('N','P')]:
        for unit,labels in [('projected_document',doc),('source_expression',expr)]:
            result.append({'case':case,'comparison':'between_representations','representation1':REP_NAME[a],'representation2':REP_NAME[b],'treatment':treatment,'multiplier':multiplier if treatment=='suppress' else '', 'algorithm':algorithm,'level':level,'unit':unit,**summary(labels[a],labels[b])})
    return result

def verify_against_saved(rows):
    path=ROOT/'results'/'keyword_representations'/'comparisons.csv.gz'
    with gzip.open(path,'rt',encoding='utf-8-sig',newline='') as f:saved=list(csv.DictReader(f))
    count=0
    for row in rows:
        candidates=[r for r in saved if all(r[k]==str(row[k]) for k in ['case','comparison','representation1','representation2','treatment','algorithm','level','unit']) and (row['treatment']=='hide' or abs(float(r['multiplier'])-float(row['multiplier']))<1e-9)]
        assert len(candidates)==1,(row['case'],row['level'],row['unit'],len(candidates))
        old=candidates[0]
        for key in ['available_seed_pairs','fixed_common_units','degenerate_pairs','valid']:
            assert int(old[key])==row[key],(key,old[key],row[key],row)
        for key in ['median','q25','q75','minimum','maximum']:
            if old[key] in ('','None','nan'):
                assert row[key] is None,(key,old[key],row[key])
            else:assert row[key] is not None and abs(float(old[key])-row[key])<1e-10,(key,old[key],row[key],row)
        count+=1
    return count

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--case',default='cross_sectional_2023-2024')
    p.add_argument('--treatment',choices=['suppress','hide'],default='hide')
    p.add_argument('--multiplier',type=float,default=1.)
    p.add_argument('--algorithm',choices=['louvain','leiden','both'],default='both')
    p.add_argument('--level',default='L1')
    p.add_argument('--all',action='store_true',help='All windows, both algorithms, seven suppressed masks plus full detection, and L0/L1/L2/FINAL')
    p.add_argument('--export-labels',type=Path,help='Optional gzip CSV of every source-record and expression label')
    p.add_argument('--output',type=Path,default=ROOT/'.verification'/'document_ari_recalculated.csv')
    args=p.parse_args()
    with gzip.open(ROOT/'data'/'record_incidence.jsonl.gz','rt',encoding='utf-8') as f:records=[json.loads(line) for line in f]
    lookup=read_gz(ROOT/'data'/'expression_dictionary.json.gz')
    with (ROOT/'data'/'graph_index.csv').open(encoding='utf-8',newline='') as f:index=list(csv.DictReader(f))
    rows=[]
    if args.all:
        tasks=[(case,t,m,a,l) for case in sorted({r['case'] for r in index}) for t,m in [('hide',1.)]+[('suppress',m) for m in [.4,.6,.8,1.,1.2,1.4,1.6]] for a in ['louvain','leiden'] for l in ['L0','L1','L2','FINAL']]
    else:
        tasks=[(args.case,args.treatment,args.multiplier,a,args.level) for a in (['louvain','leiden'] if args.algorithm=='both' else [args.algorithm])]
    label_file=None;label_writer=None
    if args.export_labels:
        args.export_labels.parent.mkdir(parents=True,exist_ok=True)
        label_file=gzip.open(args.export_labels,'wt',encoding='utf-8',newline='')
        label_writer=csv.DictWriter(label_file,fieldnames=['case','representation','treatment','multiplier','algorithm','seed','level','unit','unit_id','label'])
        label_writer.writeheader()
    try:
        for task in tasks:
            rows.extend(calculate(*task,records,lookup,index,label_writer))
    finally:
        if label_file is not None:label_file.close()
    checked=verify_against_saved(rows)
    args.output.parent.mkdir(parents=True,exist_ok=True)
    with args.output.open('w',encoding='utf-8',newline='') as f:
        writer=csv.DictWriter(f,fieldnames=list(rows[0]));writer.writeheader();writer.writerows(rows)
    print(json.dumps({'saved_rows_matched':checked,'output':str(args.output)},indent=2))

if __name__=='__main__':main()
