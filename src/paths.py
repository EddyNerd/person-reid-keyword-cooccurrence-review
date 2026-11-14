"""Repository-relative paths, including long-path support on Windows."""
from pathlib import Path
import os
import gzip,json,zipfile

ROOT=Path(os.environ.get('REID_MATERIALS_ROOT',str(Path(__file__).resolve().parents[1])))
if os.name=='nt' and not str(ROOT).startswith('\\\\?\\'):
    ROOT=Path('\\\\?\\'+str(ROOT))

def load_graph(relative):
    """Read an individual frozen graph or its lossless ZIP archive member."""
    name=Path(relative).as_posix()
    path=ROOT/name
    if path.is_file():data=path.read_bytes()
    else:
        with zipfile.ZipFile(ROOT/'data'/'frozen_graph_inputs.zip') as z:data=z.read(name)
    return json.loads(gzip.decompress(data).decode('utf-8'))
