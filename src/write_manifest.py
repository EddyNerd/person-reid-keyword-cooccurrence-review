"""Create a checksum manifest for the files in this scientific release."""
from pathlib import Path
import hashlib
import json

from paths import ROOT
EXCLUDE={'.git','.verification','__pycache__'}
TARGET=ROOT/'reproducibility'/'SHA256SUMS.json'

def main():
    entries=[]
    for p in sorted(ROOT.rglob('*')):
        if not p.is_file() or p==TARGET or any(x in EXCLUDE for x in p.relative_to(ROOT).parts):continue
        entries.append({'path':p.relative_to(ROOT).as_posix(),'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()})
    TARGET.parent.mkdir(parents=True,exist_ok=True)
    TARGET.write_text(json.dumps(entries,ensure_ascii=False,indent=2),encoding='utf-8')
    print('Manifest:',len(entries),'files')

if __name__=='__main__':main()
