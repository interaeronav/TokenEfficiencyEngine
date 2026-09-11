"""Read-only checksum verification of one delivered HF2 recipient directory."""
import hashlib
import json
import sys
import zipfile
from pathlib import Path


def digest(data):
    return hashlib.sha256(data).hexdigest()


def identity(path):
    data = path.read_bytes()
    return len(data), digest(data)


def payload(archive, prefix):
    rows = []
    with zipfile.ZipFile(archive) as z:
        names = z.namelist()
        assert len(set(names)) == len(names), 'duplicate archive members'
        for name in sorted(names):
            assert not name.startswith('/') and '..' not in Path(name).parts
            if name.endswith('/') or not name.startswith(prefix):
                continue
            if '__pycache__' in Path(name).parts or name.endswith(('.pyc', '.pyo', '/.DS_Store')):
                continue
            data = z.read(name)
            rows.append({'path': 'tee/' + name[len(prefix):], 'bytes': len(data), 'sha256': digest(data)})
    normalized = {'algorithm': 'tee-payload-v1', 'files': rows}
    return digest(json.dumps(normalized, sort_keys=True, ensure_ascii=True, separators=(',', ':')).encode())


def main():
    folder = Path(sys.argv[1]).resolve() if len(sys.argv) == 2 else Path(__file__).resolve().parent
    content = (folder / 'release-manifest.json').read_bytes()
    expected = (folder / 'release-manifest.sha256').read_text().split()[0]
    assert digest(content) == expected, 'manifest checksum'
    release = json.loads(content)
    for row in release['common_files']:
        path = Path(row['path'])
        assert not path.is_absolute() and '..' not in path.parts
        assert identity(folder / path) == (row['bytes'], row['sha256']), str(path)
    normalized = json.loads((folder / 'source-manifest.json').read_text())
    assert digest(json.dumps(normalized, sort_keys=True, ensure_ascii=True, separators=(',', ':')).encode()) == release['source']['sha256']
    checked = []
    for shape, prefix in [('claude', 'src/tee/'), ('codex', 'server/src/tee/')]:
        spec = release['targets'][shape]['artifact']
        archive = folder / Path(spec['path']).name
        if not archive.exists():
            continue
        assert identity(archive) == (spec['bytes'], spec['sha256'])
        assert payload(archive, prefix) == release['source']['sha256']
        rollback = release['rollback']['artifacts'][shape]
        previous = folder / 'rollback' / Path(rollback['path']).name
        assert identity(previous) == (rollback['bytes'], rollback['sha256'])
        assert payload(previous, prefix) == release['rollback']['payload']
        checked.append(shape)
    assert len(checked) == 1, 'expect exactly the appropriate recipient artifact'
    print(json.dumps({'verified': True, 'recipient': checked[0], 'manifest_sha256': expected,
                      'payload': release['source']['sha256'], 'runtime_acceptance': False}, indent=2))


if __name__ == '__main__':
    main()
