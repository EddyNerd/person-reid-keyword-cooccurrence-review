"""Use the actual Lucene/Snowball libraries shipped with a local Sci2 installation."""
import hashlib
import json
from pathlib import Path
import subprocess
import tempfile
import zipfile


def normalize_batch(items, stopwords, plugins, java='java'):
    plugins = Path(plugins)
    jars = [plugins / name for name in ['lucene_2.3.2.jar', 'lucene_snowball_1.0.0.jar']]
    for jar in jars:
        if not jar.is_file():
            raise FileNotFoundError(jar)
    # Nashorn is available in the Java 8 runtime used by this Sci2 installation.
    script = Path(__file__).with_name('lucene_normalize.js').resolve()
    with tempfile.TemporaryDirectory(prefix='sci2_normalize_') as folder:
        folder = Path(folder)
        src, dst, stop = [folder / name for name in ['input.jsonl', 'output.jsonl', 'stopwords.json']]
        with src.open('w', encoding='utf-8', newline='\n') as f:
            for item in items:
                f.write(json.dumps(item, ensure_ascii=False) + '\n')
        stop.write_text(json.dumps(stopwords, ensure_ascii=False), encoding='utf-8')
        # Java's own runtime supplies Nashorn; resolve its location through java.home.
        result = subprocess.run([java, '-XshowSettings:properties', '-version'], capture_output=True, text=True, check=True)
        home = next(line.split('=', 1)[1].strip() for line in result.stderr.splitlines() if 'java.home =' in line)
        nashorn = Path(home) / 'lib/ext/nashorn.jar'
        if not nashorn.is_file():
            raise RuntimeError('Java 8 with Nashorn is required for the Sci2 normalization bridge')
        import os
        class_jars = []
        for jar, member in zip(jars, ['lucene-core-2.3.2.jar', 'lucene-snowball-2.3.2.jar']):
            extracted = folder / member
            with zipfile.ZipFile(jar) as archive:
                extracted.write_bytes(archive.read(member))
            class_jars.append(extracted)
        cp = os.pathsep.join(str(j.resolve()) for j in class_jars + [nashorn])
        result = subprocess.run([java, '-Dfile.encoding=UTF-8', f'-Dwos.input={src}',
                                f'-Dwos.output={dst}', f'-Dwos.stopwords={stop}',
                                '-cp', cp, 'jdk.nashorn.tools.Shell', str(script)],
                                capture_output=True, encoding='utf-8', errors='replace')
        if result.returncode:
            raise RuntimeError(result.stderr or result.stdout)
        output = [json.loads(line) for line in dst.read_text(encoding='utf-8').splitlines()]
        if [r['id'] for r in output] != [r['id'] for r in items]:
            raise RuntimeError('Normalizer output does not match input identifiers')
    provenance = {'engine': 'Sci2 Lucene SnowballAnalyzer English, Java 8',
                  'java_home': home, 'jars': {j.name: hashlib.sha256(j.read_bytes()).hexdigest() for j in jars},
                  'bridge_sha256': hashlib.sha256(script.read_bytes()).hexdigest()}
    return output, provenance
