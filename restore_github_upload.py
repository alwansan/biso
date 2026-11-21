#!/usr/bin/env python3
"""Recreate and verify the original files from a normal Git checkout."""
import hashlib, json, pathlib, sys
base = pathlib.Path(__file__).resolve().parent
out = pathlib.Path(sys.argv[1] if len(sys.argv)>1 else base.parent/(base.name+'-restored')).resolve()
if out == base or base in out.parents or out.exists():
    raise SystemExit('Choose a NEW output directory outside the checkout.')
m = json.loads((base/'GITHUB_UPLOAD_MANIFEST.json').read_text())
def safe(s):
    p = pathlib.PurePosixPath(s)
    if not p.parts or p.is_absolute() or '..' in p.parts or '.' in p.parts:
        raise ValueError('Unsafe manifest path: '+s)
    return p
out.mkdir(parents=True)
for x in m['files']:
    dest = out/safe(x['path']); dest.parent.mkdir(parents=True, exist_ok=True)
    h = hashlib.sha256(); n = 0
    try:
        with dest.open('xb') as w:
            for p in x['parts']:
                source = (base/safe(p)).resolve()
                if base not in source.parents: raise ValueError('Unsafe source: '+p)
                with source.open('rb') as f:
                    for block in iter(lambda:f.read(1024*1024), b''):
                        w.write(block); h.update(block); n += len(block)
        if n != x['bytes'] or h.hexdigest() != x['sha256']:
            raise ValueError('SHA-256 or size mismatch: '+x['path'])
    except Exception:
        dest.unlink(missing_ok=True); raise
    print('OK', x['path'], flush=True)
for p in m.get('empty_dirs', []): (out/safe(p)).mkdir(parents=True, exist_ok=True)
print('SUCCESS: restored and SHA-256 verified',len(m['files']),'files in',out)
