"""Replay community detection on the frozen graph inputs.

One graph is selected by representation, window, treatment and multiplier.
The saved output is found by graph hash, algorithm and seed, because identical
graphs may have been reused across windows and display masks.
"""
from pathlib import Path
import argparse
import csv
import gzip
import json
import os
import warnings

import networkx as nx
from community_hierarchy import partitions
from saved_partitions import find_saved

from paths import ROOT,load_graph as load_frozen_graph


def load_json(path):
    return load_frozen_graph(path.relative_to(ROOT))


def replay(row,algorithm,seed,output):
    data=load_json(ROOT/row['file'])
    graph=nx.Graph()
    graph.add_nodes_from(sorted(data['nodes']))
    graph.add_weighted_edges_from(sorted(data['edges']))
    detected=partitions(graph,'leiden_hierarchy' if algorithm=='leiden' else 'louvain',seed,resolution=1.)
    collection='native' if row['representation']=='T' else 'TNP'
    saved=find_saved(row['graph_sha256'],algorithm,seed,collection)
    equal=detected==saved['levels']
    result={'case':row['case'],'representation':row['representation'],'treatment':row['treatment'],'multiplier':row['multiplier'],'graph_sha256':row['graph_sha256'],'algorithm':algorithm,'seed':seed,'levels':detected,'matches_saved_partitions':equal,'networkx':nx.__version__}
    output.parent.mkdir(parents=True,exist_ok=True)
    output.write_text(json.dumps(result,ensure_ascii=False,separators=(',',':')),encoding='utf-8')
    if not equal: raise AssertionError('Partition mismatch: inspect the recorded environment and pinned package versions.')
    return len(detected)


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--case',default='cross_sectional_2023-2024')
    p.add_argument('--representation',choices=['T','N','P'],default='T')
    p.add_argument('--treatment',choices=['suppress','hide'],default='suppress')
    p.add_argument('--multiplier',type=float,default=1.)
    p.add_argument('--algorithm',choices=['louvain','leiden'],default='louvain')
    p.add_argument('--seed',type=int,default=1000)
    p.add_argument('--all',action='store_true',help='Replay all distinct graph/algorithm/seed inputs; this is substantially slower')
    p.add_argument('--output',type=Path,default=ROOT/'.verification'/'replayed_partitions')
    a=p.parse_args()
    if os.environ.get('PYTHONHASHSEED')!='0':warnings.warn('For a fresh process use PYTHONHASHSEED=0; graph ordering is also fixed explicitly.')
    if nx.__version__!='3.2.1':warnings.warn('The archived environment used NetworkX 3.2.1. Install requirements-replay.txt for the pinned replay.')
    with (ROOT/'data'/'graph_index.csv').open(encoding='utf-8',newline='') as f:rows=list(csv.DictReader(f))
    if a.all:
        seen=set();count=0
        for row in rows:
            for alg in ['louvain','leiden']:
                for seed in range(1000,1030):
                    key=(row['graph_sha256'],alg,seed)
                    if key in seen:continue
                    seen.add(key)
                    replay(row,alg,seed,a.output/f'{key[0][:16]}_{alg}_{seed}.json')
                    count+=1
        print('Replayed and matched',count,'distinct inputs')
    else:
        row=next(r for r in rows if r['case']==a.case and r['representation']==a.representation and r['treatment']==a.treatment and (a.treatment=='hide' or abs(float(r['multiplier'])-a.multiplier)<1e-9))
        levels=replay(row,a.algorithm,a.seed,a.output/f'{row["graph_sha256"][:16]}_{a.algorithm}_{a.seed}.json')
        print('Matched saved output;',levels,'distinct hierarchy levels')


if __name__=='__main__':main()
