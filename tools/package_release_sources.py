"""Create a source/notice companion without runtime DLLs, model weights or local state."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import zipfile

ROOT = Path(__file__).resolve().parents[1]


def package(output, receipt):
    if output.exists() or not output.resolve().is_relative_to(ROOT / 'artifacts'):
        raise ValueError('Use a new ZIP within artifacts/')
    dependencies = json.loads(receipt.read_text())['dependencies']
    names = {re.sub(r'[-_.]+', '-', d['name']).lower() for d in dependencies}
    names.discard('av')
    pinned = json.loads((ROOT / 'resources/source-archives.json').read_text())['files']
    origins = {x['sha256']: x['url'] for x in pinned}
    sources = ROOT / 'third-party/source-archives'
    files = []
    for p in sources.rglob('*'):
        if not p.is_file():
            continue
        rel = p.relative_to(sources)
        if rel.parts[0] == 'pyav-ffmpeg' or p.name.startswith('pyav-ffmpeg-'):
            continue
        if rel.parts[0] == 'python':
            name = re.sub(r'[-_.]+', '-', re.split(r'-\d', p.name)[0]).lower()
            if name not in names:
                continue
        files.append((p, 'sources/' + rel.as_posix()))
    for p in (ROOT / 'third-party/release-notices').rglob('*'):
        if p.is_file():
            files.append((p, 'notices/' + p.relative_to(ROOT / 'third-party/release-notices').as_posix()))
    for p in (ROOT / 'third-party/ffmpeg-minimal').glob('build-*.txt'):
        files.append((p, 'ffmpeg-build/' + p.name))
    files += [(ROOT / 'tools/build_ffmpeg.sh', 'ffmpeg-build/build_ffmpeg.sh'),
              (ROOT / 'requirements-windows.lock', 'rebuild/requirements-windows.lock'),
              (ROOT / 'tools/build_windows.py', 'rebuild/build_windows.py'),
              (ROOT / 'docs/BUILD.md', 'rebuild/BUILD.md')]
    inventory = []
    with zipfile.ZipFile(output, 'w', compression=zipfile.ZIP_DEFLATED, compresslevel=1) as archive:
        for p, name in sorted(files, key=lambda item: item[1]):
            digest = hashlib.sha256(p.read_bytes()).hexdigest()
            if name.startswith('sources/') and digest not in origins:
                raise ValueError('Source archive missing pinned provenance: ' + name)
            archive.write(p, name)
            inventory.append({'path': name, 'sha256': digest, 'bytes': p.stat().st_size,
                              'source': origins.get(digest, 'Included build recipe or upstream notice')})
        archive.writestr('SOURCES.json', json.dumps(inventory, indent=2))
        archive.writestr('README.txt', 'SureLive Local Assistant source and notices companion.\n'
                         'No models, media, runtime DLLs or credentials.\n'
                         'Extract notices/ as third-party/release-notices. See rebuild/BUILD.md.\n'
                         'FFmpeg source is sources/upstream/ffmpeg-7.1-b08d7969c5.tar.gz.\n'
                         'Build with ffmpeg-build/build_ffmpeg.sh in MSYS2 UCRT64.\n'
                         'Other source archives retain their upstream licenses.\n')
    print(json.dumps({'file': output.name, 'files': len(inventory), 'bytes': output.stat().st_size}))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--receipt', type=Path, required=True)
    args = parser.parse_args()
    package(args.output, args.receipt)
