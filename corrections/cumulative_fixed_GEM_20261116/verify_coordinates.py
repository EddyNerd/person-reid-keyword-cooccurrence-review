"""Verify exact coordinate inheritance and unchanged scientific node attributes."""
from pathlib import Path
import csv,hashlib,json,sys
HERE=Path(__file__).resolve().parent

def read(p):
 with p.open(encoding='utf-8-sig',newline='') as h:return list(csv.DictReader(h))

def main():
 ref={}
 for r in read(HERE/'archived_GEM_positions.csv'):ref.setdefault(r['period'],{})[r['token']]=(float(r['x']),float(r['y']))
 rows={p:read(HERE/p/'nodes.csv') for p in ('2015-2022','2015-2024')}
 pos={p:{r['token']:(float(r['x']),float(r['y'])) for r in rr} for p,rr in rows.items()}
 assert (len(rows['2015-2022']),len(rows['2015-2024']))==(91,116)
 for p in rows:
  old={r['token']:r for r in read(HERE/f'baseline_memberships_{p}.csv')}
  fields=('token','document_frequency','L0','L1','FINAL')
  assert all(tuple(r[k] for k in fields)==tuple(old[r['token']][k] for k in fields) for r in rows[p])
 shared20=ref['2015-2020'].keys()&pos['2015-2022'].keys()
 shared24=pos['2015-2022'].keys()&pos['2015-2024'].keys()
 assert len(shared20)==58 and all(pos['2015-2022'][n]==ref['2015-2020'][n] for n in shared20)
 assert len(shared24)==89 and all(pos['2015-2022'][n]==pos['2015-2024'][n] for n in shared24)
 changes=sorted(n for n in pos['2015-2024'] if pos['2015-2024'][n]!=ref['2015-2024'][n])
 assert changes==['face','intellig','rank','similar','spatial']
 edges={p:read(HERE/p/'edges.csv') for p in rows}
 assert len(edges['2015-2022'])==434 and sum(int(r['weight']) for r in edges['2015-2022'])==15907
 assert len(edges['2015-2024'])==615
 inherited={n:xy for n,xy in pos['2015-2022'].items() if n not in ('modul','structur')}
 assert len(inherited)==89
 if '--replay-additions' in sys.argv:
  from anchored_gem import place_new_nodes
  out,meta=place_new_nodes(inherited,[(r['source'],r['target'],int(r['weight'])) for r in edges['2015-2022']],seed=1000,characteristic_length=32.0)
  assert all(tuple(out[n])==xy for n,xy in pos['2015-2022'].items())
 manifest=HERE/'SHA256SUMS.json'
 if manifest.exists():
  for r in json.loads(manifest.read_text(encoding='utf-8')):assert hashlib.sha256((HERE/r['path']).read_bytes()).hexdigest()==r['sha256'],r['path']
 print(json.dumps({'passed':True,'unchanged_2022_predecessor_positions':58,'unchanged_2022_2024_shared_positions':89,'only_2024_changes':changes,'new_node_replay':'--replay-additions' in sys.argv},indent=2))

if __name__=='__main__':main()
