"""Verify the frozen scientific material without rerunning community detection.

Uses only the Python standard library. No network connection is required.
"""
from pathlib import Path
from collections import Counter
from itertools import combinations
import argparse
import csv
import gzip
import hashlib
import json
import sys
from saved_partitions import decode_levels

from paths import ROOT,load_graph as load_frozen_graph


def csv_rows(path):
    with path.open(encoding='utf-8-sig',newline='') as f:
        return list(csv.DictReader(f))


def load_graph(path):
    return load_frozen_graph(path.relative_to(ROOT))


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--skip-hashes',action='store_true')
    parser.add_argument('--check-partitions',action='store_true',help='Also inspect every saved partition hierarchy')
    parser.add_argument('--output',type=Path,default=ROOT/'.verification'/'quick_verification.json')
    args=parser.parse_args()
    checks=[]
    if not args.skip_hashes:
        manifest=ROOT/'reproducibility'/'SHA256SUMS.json'
        if not manifest.exists():
            raise SystemExit('Run python src/write_manifest.py before hash verification.')
        entries=json.loads(manifest.read_text(encoding='utf-8'))
        for entry in entries:
            path=ROOT/entry['path']
            assert path.is_file(),str(path)
            assert hashlib.sha256(path.read_bytes()).hexdigest()==entry['sha256'],entry['path']
        checks.append({'check':'file_hashes','files':len(entries),'passed':True})

    with gzip.open(ROOT/'data'/'record_incidence.jsonl.gz','rt',encoding='utf-8') as f:
        records=[json.loads(line) for line in f if line.strip()]
    assert len(records)==2333
    assert len({r['UT'] for r in records})==2333
    assert sum(bool(r['tokens']) for r in records)==2260
    assert Counter(r['year'] for r in records).keys() <= set(range(2015,2025))
    checks.append({'check':'analytical_corpus','records':2333,'usable_keyword_records':2260,'passed':True})

    rep_keys={'T':'tokens','N':'phrases_normalized','P':'phrases'}
    graph_index=csv_rows(ROOT/'data'/'graph_index.csv')
    full_graphs=[r for r in graph_index if r['treatment']=='hide']
    assert len(full_graphs)==30
    for row in full_graphs:
        first,last=map(int,row['case'].rsplit('_',1)[1].split('-'))
        subset=[r for r in records if first<=r['year']<=last]
        assert len(subset)==int(row['documents']),row['case']
        field=rep_keys[row['representation']]
        freq=Counter()
        weights=Counter()
        for record in subset:
            words=sorted(set(record[field]))
            freq.update(words)
            weights.update(combinations(words,2))
        graph=load_graph(ROOT/row['file'])
        saved_edges={tuple(sorted((u,v))):float(w) for u,v,w in graph['edges']}
        assert set(graph['nodes'])==set(freq),('nodes',row['representation'],row['case'])
        assert saved_edges==dict(weights),('edges',row['representation'],row['case'])
        if 'frequencies' in graph:
            assert graph['frequencies']==dict(freq),('frequencies',row['representation'],row['case'])
        checks.append({'check':'full_graph_from_incidence','representation':row['representation'],'case':row['case'],'records':len(subset),'nodes':len(freq),'edges':len(weights),'total_weight':sum(weights.values()),'passed':True})
    corrected=[r for r in records if r['year']<=2022]
    assert len(corrected)==1499 and sum(bool(r['tokens']) for r in corrected)==1439
    checks.append({'check':'corrected_cumulative_2015_2022','records':1499,'usable':1439,'passed':True})

    folder=ROOT/'data'/'openalex'
    decisions=csv_rows(folder/'eligibility_decisions.csv')
    eligible=csv_rows(folder/'eligible_reference_publications.csv')
    matches=csv_rows(folder/'matched_publications.csv')
    assert len(decisions)==5666
    assert sum(r['decision']=='eligible' for r in decisions)==4665
    assert len(eligible)==4665
    assert len({r['pool_id'] for r in matches})==1869
    assert Counter(r['kind'] for r in eligible)=={'journal':2450,'conference':2215}
    checks.append({'check':'OpenAlex_reference','retrieved_records':5666,'eligible_publications':4665,'journal':2450,'conference':2215,'represented':1869,'relative_recall':1869/4665,'passed':True})

    missing=csv_rows(ROOT/'supplementary'/'tables'/'Table_S2.csv')
    assert {r['WoS accession number'] for r in missing}=={r['UT'] for r in records if not r['tokens']}
    checks.append({'check':'unusable_keyword_inventory','records':len(missing),'passed':True})
    if args.check_partitions:
        for kind in ['native','TNP']:
            count=0
            for path in (ROOT/'results'/'partitions'/kind).glob('shard-*.jsonl.gz'):
                with gzip.open(path,'rt',encoding='utf-8') as f:
                    for line in f:
                        r=json.loads(line)
                        levels=decode_levels(r)
                        assert 1000<=r['seed']<=1029
                        assert levels
                        words=set(levels[0])
                        assert all(set(p)==words for p in levels)
                        for child,parent in zip(levels,levels[1:]):
                            mapping={}
                            for word,c in child.items():
                                if c in mapping: assert mapping[c]==parent[word]
                                mapping[c]=parent[word]
                        count+=1
            checks.append({'check':'saved_partition_hierarchies','collection':kind,'unique_outputs':count,'passed':True})
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps({'passed':True,'checks':checks},indent=2),encoding='utf-8')
    print(json.dumps({'passed':True,'checks':len(checks),'report':str(args.output)},indent=2))


if __name__=='__main__':main()
