"""Validate a frozen helper directly, without installing or registering it.

Optional recognition uses a local model source and audio; no model downloads.
All test state and copied model files remain under the specified new directory.
"""
import argparse
import json
import os
from pathlib import Path
import struct
import subprocess
import sys
import time
import urllib.error
import urllib.request
import uuid

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src/surelive_local_asr'))
from models import Models
import threading


def run(args):
    payload, output = args.payload.resolve(), args.output.resolve()
    if not output.is_relative_to(ROOT / 'artifacts') or output.exists():
        raise ValueError('Use a NEW directory under this project artifacts/')
    if bool(args.audio) != bool(args.model_source):
        raise ValueError('Supply both --audio and --model-source, or neither')
    output.mkdir(parents=True)
    data = output / 'user/SureLiveASRPreview'
    data.mkdir(parents=True)
    catalog = json.loads((payload / 'models.json').read_text(encoding='utf-8'))
    model_root = output / 'models'
    if args.model_source:
        Models(catalog, model_root).prepare(args.model, threading.Event(), lambda _: None, args.model_source.resolve())
    (data / 'settings.json').write_text(json.dumps({'modelDirectory': str(model_root)}), encoding='utf-8')
    env = {**os.environ, 'LOCALAPPDATA': str(output / 'user'),
           'PATH': str(Path(os.environ['SystemRoot']) / 'System32') + os.pathsep + os.environ['SystemRoot'],
           'PYINSTALLER_RESET_ENVIRONMENT': '1'}
    for name in ('PYTHONPATH', 'PYTHONHOME', 'CUDA_PATH'):
        env.pop(name, None)
    if args.hide_cuda:
        env['CUDA_VISIBLE_DEVICES'] = '-1'
    origin = 'chrome-extension://pigcndembijihpdlkdpmopjddomgjogc'
    host = payload / 'SureLive-NativeHost.exe'
    rejected = subprocess.run([str(host), 'chrome-extension://' + 'a' * 32 + '/'], env=env,
                              stdin=subprocess.DEVNULL, capture_output=True, timeout=35)
    assert rejected.returncode != 0, 'Foreign native origin was accepted'
    process = subprocess.Popen([str(host), origin + '/'], stdin=subprocess.PIPE,
                               stdout=subprocess.PIPE, stderr=subprocess.PIPE, env=env,
                               creationflags=subprocess.CREATE_NO_WINDOW)
    report = {'foreignNativeOriginDenied': True, 'installed': False, 'registryChanged': False}
    watchdog = threading.Timer(45, process.terminate)
    watchdog.start()
    try:
        header = process.stdout.read(4)
        if len(header) != 4:
            raise RuntimeError('Native bootstrap failed: ' + process.stderr.read().decode(errors='replace')[-1500:])
        size = struct.unpack('<I', header)[0]
        assert 0 < size < 4096
        credential = json.loads(process.stdout.read(size))
        watchdog.cancel()
        assert credential['version'] == 1 and credential['endpoint'].startswith('http://127.0.0.1:')

        def request(route, method='GET', body=None, auth=True, source=origin):
            headers = {'Authorization': 'Bearer ' + credential['token']} if auth else {}
            if source is not None:
                headers['Origin'] = source
            req = urllib.request.Request(credential['endpoint'] + route, data=body, method=method, headers=headers)
            try:
                with urllib.request.urlopen(req, timeout=60) as response:
                    return response.status, json.load(response)
            except urllib.error.HTTPError as error:
                return error.code, json.load(error)

        assert request('/health', auth=False)[0] == 403
        assert request('/health', source='https://example.invalid')[0] == 403
        assert request('/health', source=None)[0] == 200
        status, health = request('/health')
        assert status == 200 and health['capabilities']['chunkSeconds'] == 300
        report.update(missingTokenDenied=True, foreignHttpOriginDenied=True,
                      originOptionalWithToken=True, hardware=health['hardware'],
                      modelLanguages={k: len(v['languages']) for k, v in health['models'].items()})
        if args.audio:
            key = str(uuid.uuid4())
            status, _ = request(f'/jobs/{key}?model={args.model}&language={args.language}&device={args.device}',
                                'PUT', args.audio.read_bytes())
            assert status == 202
            deadline = time.monotonic() + 300
            while time.monotonic() < deadline:
                status, job = request('/jobs/' + key)
                assert status == 200
                if job.get('finished'):
                    break
                time.sleep(.2)
            else:
                raise RuntimeError('Recognition timed out')
            assert job['stage'] == 'complete', job.get('error')
            result = job['result']
            assert result['segments'], 'No subtitles produced'
            report['recognition'] = {k: result[k] for k in ('durationSec', 'language', 'device', 'cpuFallback', 'inferenceMs')}
            report['recognition']['segments'] = len(result['segments'])
            assert request('/jobs/' + key, 'DELETE')[0] == 200
            if args.exercise_cancel:
                cancel_key = str(uuid.uuid4())
                assert request(f'/jobs/{cancel_key}?model={args.model}&language={args.language}&device={args.device}',
                               'PUT', args.audio.read_bytes())[0] == 202
                assert request('/jobs/' + cancel_key, 'DELETE')[0] == 200
                deadline = time.monotonic() + 20
                while time.monotonic() < deadline:
                    _, cancelled = request('/jobs/' + cancel_key)
                    if cancelled.get('finished'):
                        break
                    time.sleep(.1)
                assert cancelled['stage'] == 'cancelled', cancelled.get('stage')
                report['activeCancellation'] = True
    finally:
        watchdog.cancel()
        process.stdin.close()
        try:
            process.wait(timeout=20)
        except subprocess.TimeoutExpired:
            process.terminate()
            process.wait(timeout=10)
            raise RuntimeError('Native host did not exit after disconnect')
    assert process.returncode == 0
    report['disconnectExited'] = True
    (output / 'result.json').write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(report))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--payload', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--audio', type=Path)
    parser.add_argument('--model-source', type=Path)
    parser.add_argument('--model', choices=['small', 'large-v3'], default='small')
    parser.add_argument('--language', default='en')
    parser.add_argument('--device', choices=['auto', 'cpu'], default='auto')
    parser.add_argument('--hide-cuda', action='store_true')
    parser.add_argument('--exercise-cancel', action='store_true')
    run(parser.parse_args())
