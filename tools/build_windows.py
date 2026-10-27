"""Build a local Windows preview from this repository and explicit native inputs."""
import argparse
import ast
import hashlib
import importlib.util
import importlib.metadata as metadata
import json
from pathlib import Path
import re
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / 'src/surelive_local_asr'
VERSION = '0.1.1-basic.preview.1'


def stage_pcm_dependency(output):
    """Keep upstream PCM inference unchanged; do not eagerly load unused PyAV."""
    origin = Path(importlib.util.find_spec('faster_whisper').origin).parent
    target = output / 'patched-dependencies/faster_whisper'
    shutil.copytree(origin, target, ignore=shutil.ignore_patterns('__pycache__', '*.pyc'))
    audio = target / 'audio.py'
    original = audio.read_text(encoding='utf-8')
    if original.count('\nimport av\n') != 1 or original.count('    resampler = av.audio.resampler.AudioResampler(') != 1:
        raise ValueError('Unexpected faster-whisper audio source; review the PCM packaging patch')
    patched = original.replace('\nimport av\n', '\n# SureLive: PyAV is optional for the PCM-only packaged worker.\n')
    patched = patched.replace('    resampler = av.audio.resampler.AudioResampler(',
                              '    global av\n    import av\n\n    resampler = av.audio.resampler.AudioResampler(')
    audio.write_text(patched, encoding='utf-8')
    return target.parent


def sha256(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def resolve_input(value):
    path = Path(value)
    return path.resolve() if path.is_absolute() else (ROOT / path).resolve()


def native_inputs(config):
    rows = []
    for item in [config['ffmpeg'], *config.get('gpu', [])]:
        source = resolve_input(item['path'])
        if not source.is_file():
            raise ValueError(f'Missing native input: {source.name}')
        if not re.fullmatch('[a-f0-9]{64}', item.get('sha256', '')) or sha256(source) != item['sha256']:
            raise ValueError(f'Native input SHA-256 mismatch: {source.name}')
        if source != resolve_input(config['ffmpeg']['path']) and source.suffix.lower() != '.dll':
            raise ValueError('GPU inputs must be DLL files')
        rows.append((source, item['sha256']))
    return rows


def toc_entries(value):
    if isinstance(value, (list, tuple)):
        if len(value) == 3 and all(isinstance(v, str) for v in value):
            if Path(value[1]).is_file():
                yield value
        else:
            for child in value:
                yield from toc_entries(child)


def collect_local_notices(work, destination):
    used = {str(Path(row[1]).resolve()).casefold()
            for toc in work.rglob('Analysis-00.toc')
            for row in toc_entries(ast.literal_eval(toc.read_text(encoding='utf-8')))}
    found = []
    for distribution in metadata.distributions():
        if not any(str(distribution.locate_file(f).resolve()).casefold() in used for f in distribution.files or []):
            continue
        name, version = distribution.metadata['Name'], distribution.version
        folder = destination / f'{name}-{version}'
        folder.mkdir(parents=True, exist_ok=True)
        (folder / 'METADATA.txt').write_text(distribution.read_text('METADATA') or '', encoding='utf-8')
        count = 0
        for item in distribution.files or []:
            source = distribution.locate_file(item)
            if (not source.is_file() or source.suffix in ('.py', '.pyc') or
                    not re.search('license|licence|copying|copyright|notice|authors', source.name, re.I)):
                continue
            relative = Path(*[p for p in Path(item).parts if p not in ('.', '..')])
            target = folder / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, target)
            count += 1
        found.append({'name': name, 'version': version, 'noticeFiles': count})
    return sorted(found, key=lambda item: item['name'].lower())


def freeze(output, script, name, options=()):
    subprocess.run([sys.executable, '-m', 'PyInstaller', '--onedir', '--noupx',
                    '--name', name, '--distpath', str(output / 'dist'),
                    '--workpath', str(output / 'work' / name), '--specpath', str(output),
                    '--exclude-module', 'torch', '--exclude-module', 'tensorflow',
                    '--exclude-module', 'transformers', '--exclude-module', 'matplotlib',
                    '--exclude-module', 'pandas', *options, str(SOURCE / script)], cwd=ROOT, check=True)


def build(config_path, output, installer=False):
    if sys.platform != 'win32' or sys.version_info[:2] != (3, 12):
        raise ValueError('Use Windows x64 and Python 3.12 with requirements-windows.lock')
    output = output.resolve()
    if not output.is_relative_to(ROOT / 'artifacts') or output.exists():
        raise ValueError('Output must be a NEW directory under this project artifacts/')
    config = json.loads(config_path.read_text(encoding='utf-8'))
    inputs = native_inputs(config)
    formats = subprocess.check_output([str(inputs[0][0]), '-hide_banner', '-muxers'],
                                      stderr=subprocess.STDOUT, text=True, timeout=20)
    if not re.search(r'\bf32le\b', formats):
        raise ValueError('FFmpeg must support the f32le output required by the helper')
    supplement = resolve_input(config['supplementalNotices'])
    if not supplement.is_dir():
        raise ValueError('Provide the release source/materials bundle notices directory')
    nsis = resolve_input(config['makensis']) if installer else None
    if installer and not nsis.is_file():
        raise ValueError('Configure an existing makensis.exe before building the installer')
    # Validate before any build writes; never install or register a native host.
    output.mkdir(parents=True)
    patched = stage_pcm_dependency(output)
    freeze(output, 'worker.py', 'SureLive-Inference', [
        '--paths', str(patched), '--exclude-module', 'av',
        '--collect-binaries', 'ctranslate2', '--collect-binaries', 'tokenizers',
        '--collect-binaries', 'onnxruntime', '--collect-data', 'faster_whisper',
        '--exclude-module', 'torchvision', '--exclude-module', 'torchaudio', '--exclude-module', 'pyarrow',
        '--exclude-module', 'polars', '--exclude-module', 'onnxruntime.transformers', '--exclude-module', 'onnxruntime.tools'])
    freeze(output, 'host.py', 'SureLive-NativeHost', ['--hidden-import', 'pystray._win32'])
    freeze(output, 'launcher.py', 'SureLive-ASR-Helper', ['--windowed'])
    payload = output / 'payload'
    shutil.copytree(output / 'dist/SureLive-NativeHost', payload)
    shutil.copytree(output / 'dist/SureLive-ASR-Helper', payload, dirs_exist_ok=True)
    shutil.copytree(output / 'dist/SureLive-Inference', payload / 'runtime')
    shutil.copy2(inputs[0][0], payload / 'ffmpeg.exe')
    if len(inputs) > 1:
        (payload / 'runtime/gpu').mkdir()
        for source, _ in inputs[1:]:
            shutil.copy2(source, payload / 'runtime/gpu' / source.name)
    shutil.copy2(ROOT / 'resources/models.json', payload / 'models.json')
    shutil.copy2(ROOT / 'resources/gpu-runtime.json', payload / 'gpu-runtime.json')
    shutil.copy2(ROOT / 'LICENSE', payload / 'LICENSE.txt')
    shutil.copy2(ROOT / 'THIRD-PARTY-NOTICES.txt', payload / 'THIRD-PARTY-NOTICES.txt')
    dependencies = collect_local_notices(output / 'work', payload / 'licenses')
    shutil.copytree(supplement, payload / 'licenses/supplement', dirs_exist_ok=True)
    shutil.copytree(patched / 'faster_whisper', payload / 'sources/faster_whisper')
    shutil.copy2(ROOT / 'tools/build_windows.py', payload / 'sources/build_windows.py')
    guide = 'INSTALL' if len(inputs)>1 else 'BASIC-INSTALL'
    shutil.copy2(ROOT / f'docs/{guide}.md', payload / 'README.zh-CN.md')
    shutil.copy2(ROOT / f'docs/{guide}.en.md', payload / 'README.en.md')
    shutil.copy2(ROOT / 'resources/DISTRIBUTION.txt', payload / 'DISTRIBUTION.txt')
    for index, item in enumerate([config['ffmpeg'], *config.get('gpu', [])]):
        for notice in item.get('notices', []):
            source = resolve_input(notice)
            target = payload / 'licenses/native-inputs' / str(index) / source.name
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, target)
    files = [{'path': p.relative_to(payload).as_posix(), 'size': p.stat().st_size, 'sha256': sha256(p)}
             for p in sorted(payload.rglob('*')) if p.is_file()]
    uninstall = ['Delete "$INSTDIR\\' + f['path'].replace('/', '\\') + '"' for f in files]
    uninstall += ['RMDir "$INSTDIR\\' + str(p.relative_to(payload)) + '"'
                  for p in sorted((p for p in payload.rglob('*') if p.is_dir()), key=lambda p: len(p.parts), reverse=True)]
    (output / 'uninstall-files.nsh').write_text('\n'.join(uninstall), encoding='utf-8-sig')
    if any('av.libs/' in f['path'] or '/av/' in f['path'] for f in files):
        raise ValueError('Unexpected PyAV runtime in PCM-only payload')
    receipt = {'project': 'surelive-local-assistant', 'version': VERSION, 'publicDistributionReady': False,
               'packageVariant': 'full' if len(inputs)>1 else 'basic', 'gpuPreparation': 'on-demand',
               'protocolVersion': 1, 'nativeHost': 'com.surelive.asr.preview',
               'modelsBundled': False, 'gpuDlls': len(inputs) - 1, 'dependencies': dependencies,
               'files': files, 'installed': False, 'signed': False,
               'sourceFiles': {p.name: sha256(p) for p in sorted(SOURCE.glob('*.py'))}}
    if installer:
        subprocess.run([str(nsis), '/INPUTCHARSET', 'UTF8', '/DROOT=' + str(output), '/DAPP_VERSION=' + VERSION,
                        str(ROOT / 'installer/windows.nsi')], check=True)
        setup = output / 'SureLive-ASR-Setup-Preview.exe'
        receipt['installer'] = {'name': setup.name, 'sha256': sha256(setup), 'size': setup.stat().st_size}
    (output / 'build-receipt.json').write_text(json.dumps(receipt, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({'payload': str(payload), 'files': len(files), 'installerBuilt': installer}))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--config', type=Path, default=ROOT / 'build.local.json')
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--installer', action='store_true', help='Build a private installer; do not install it')
    args = parser.parse_args()
    build(args.config.resolve(), args.output, args.installer)
