"""Native Louvain levels and pinned upstream NetworkX Leiden levels.

The installed NetworkX remains unchanged. For Leiden, only backend dispatch
decorators and the unused CPM import are removed from the vendored 3.7 source.
All algorithm bodies remain unchanged; this adapter supports modularity only.
"""
import ast
from functools import lru_cache
import hashlib
import json
from pathlib import Path

import networkx as nx
from paths import ROOT as REPOSITORY_ROOT


def canonical(communities):
    groups=sorted((set(map(str,c)) for c in communities if c),key=lambda c:(min(c),len(c)))
    return {n:i for i,c in enumerate(groups) for n in c}


@lru_cache(maxsize=1)
def leiden_generator():
    folder=REPOSITORY_ROOT/'src/vendor/networkx_leiden'
    provenance=json.loads((folder/'provenance.json').read_text(encoding='utf-8'))
    path=folder/'leiden.py'
    assert hashlib.sha256(path.read_bytes()).hexdigest()==provenance['files']['leiden.py']['sha256']
    tree=ast.parse(path.read_text(encoding='utf-8'))
    decorators_removed=0; imports_removed=0
    for node in tree.body:
        if isinstance(node,(ast.FunctionDef,ast.AsyncFunctionDef)):
            decorators=[]
            for d in node.decorator_list:
                f=d.func if isinstance(d,ast.Call) else d
                if isinstance(f,ast.Attribute) and isinstance(f.value,ast.Name) and f.value.id=='nx' and f.attr=='_dispatchable':
                    decorators_removed+=1
                else:decorators.append(d)
            node.decorator_list=decorators
        elif isinstance(node,ast.ImportFrom) and node.module=='networkx.algorithms.community.quality':
            imports_removed+=sum(a.name=='constant_potts_model' for a in node.names)
            node.names=[a for a in node.names if a.name!='constant_potts_model']
    assert decorators_removed==2 and imports_removed==1
    namespace={'__name__':'pinned_networkx37_leiden','__file__':str(path)}
    exec(compile(ast.fix_missing_locations(tree),str(path),'exec'),namespace)
    return namespace['leiden_partitions']


def nested(first,second):
    parents={}
    for n,c in first.items():
        if c in parents and parents[c]!=second[n]:return False
        parents[c]=second[n]
    return True


def partitions(graph,algorithm,seed,resolution=1.):
    if graph.number_of_edges()==0:
        return [canonical([{n} for n in graph])]
    if algorithm=='louvain':
        raw=nx.community.louvain_partitions(graph,weight='weight',resolution=resolution,seed=seed)
    elif algorithm=='leiden_hierarchy':
        raw=leiden_generator()(graph,weight='weight',metric='modularity',resolution=resolution,seed=seed)
    else:raise ValueError(algorithm)
    result=[]; previous_q=None
    for groups in raw:
        p=canonical(groups)
        assert set(p)==set(graph)
        q=nx.community.modularity(graph,groups,weight='weight',resolution=resolution)
        assert previous_q is None or q>=previous_q-1e-10, ('Non-monotone modularity',algorithm,seed)
        if result:
            assert nested(result[-1],p),('Non-nested algorithm levels',algorithm,seed)
            if p==result[-1]:continue
        result.append(p);previous_q=q
    assert result
    return result
