"""Decode the lossless saved community-membership arrays."""
from pathlib import Path
from functools import lru_cache
import csv,gzip,json

from paths import ROOT,load_graph

@lru_cache(maxsize=1)
def graph_files():
    with (ROOT/'data'/'graph_index.csv').open(encoding='utf-8',newline='') as f:
        return {r['graph_sha256']:r['file'] for r in csv.DictReader(f)}

@lru_cache(maxsize=256)
def graph_nodes(graph_hash):
    return sorted(load_graph(graph_files()[graph_hash])['nodes'])

def decode_levels(record):
    if 'levels' in record:return record['levels']
    nodes=graph_nodes(record['graph_sha256'])
    arrays=record['membership_arrays']
    assert all(len(a)==len(nodes) for a in arrays)
    return [dict(zip(nodes,a)) for a in arrays]

@lru_cache(maxsize=64)
def records_for_graph(graph_hash,collection):
    path=ROOT/'results'/'partitions'/collection/f'shard-{graph_hash[0]}.jsonl.gz'
    result={}
    with gzip.open(path,'rt',encoding='utf-8') as f:
        for line in f:
            r=json.loads(line)
            if r['graph_sha256']==graph_hash:result[(r['algorithm'],r['seed'])]=r
    return result

def find_saved(graph_hash,algorithm,seed,collection='native'):
    r=records_for_graph(graph_hash,collection).get((algorithm,seed))
    if r is not None:return {**r,'levels':decode_levels(r)}
    raise KeyError((graph_hash,algorithm,seed))
