"""Install, exercise, upgrade and uninstall a candidate, restoring existing HKCU entries.

Uses a NEW project artifacts directory. Existing installed files are never overwritten.
The preview's known registry keys/shortcut are backed up and restored in finally.
"""
import argparse
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import winreg

ROOT = Path(__file__).resolve().parents[1]
HOST = 'com.surelive.asr.preview'
KEYS = [f'Software\\{browser}\\NativeMessagingHosts\\{HOST}' for browser in
        ('Google\\Chrome', 'Microsoft\\Edge')]
KEYS += ['Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\SureLive-ASR-Preview']
VIEWS = (winreg.KEY_WOW64_32KEY, winreg.KEY_WOW64_64KEY)


def snapshot(key, view):
    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, key, 0, winreg.KEY_READ | view) as handle:
            count, values, _ = winreg.QueryInfoKey(handle)
            return {'values': [winreg.EnumValue(handle, i) for i in range(values)],
                    'children': {winreg.EnumKey(handle, i): snapshot(key + '\\' + winreg.EnumKey(handle, i), view)
                                 for i in range(count)}}
    except FileNotFoundError:
        return None


def restore(key, view, saved):
    assert any(key == root or key.startswith(root + '\\') for root in KEYS)
    current = snapshot(key, view)
    if current:
        for child in current['children']:
            restore(key + '\\' + child, view, None)
        winreg.DeleteKeyEx(winreg.HKEY_CURRENT_USER, key, view)
    if saved is not None:
        with winreg.CreateKeyEx(winreg.HKEY_CURRENT_USER, key, 0, winreg.KEY_WRITE | view) as handle:
            for name, value, kind in saved['values']:
                winreg.SetValueEx(handle, name, 0, kind, value)
        for child, content in saved['children'].items():
            restore(key + '\\' + child, view, content)


def run(args):
    output = args.output.resolve()
    if output.exists() or not output.is_relative_to(ROOT / 'artifacts'):
        raise ValueError('Use a NEW directory inside project artifacts')
    output.mkdir(parents=True)
    install = output / 'installed-中文路径'
    saved = [(key, view, snapshot(key, view)) for key in KEYS for view in VIEWS]
    shortcut = Path(os.environ['APPDATA']) / 'Microsoft/Windows/Start Menu/Programs/SureLive ASR Preview/本机字幕助手.lnk'
    shortcut_before = shortcut.read_bytes() if shortcut.exists() else None
    (output / 'registry-before.json').write_text(json.dumps(saved, default=str, indent=2), encoding='utf-8')
    report = {'isolatedInstallDirectory': True, 'freshWindowsVm': False}
    def installer():
        subprocess.run([str(args.installer.resolve()), '/S', '/D=' + str(install)],
                       check=True, timeout=240, creationflags=subprocess.CREATE_NO_WINDOW)
        manifest = json.loads((install / 'native-host.json').read_text())
        assert Path(manifest['path']).resolve() == install / 'SureLive-NativeHost.exe'
        for key in KEYS[:2]:
            for view in VIEWS:
                value = next(value for name, value, _ in snapshot(key, view)['values'] if name == '')
                assert Path(value) == install / 'native-host.json'
    try:
        installer()
        report['installAndRegistration'] = True
        sentinel = install / 'user-keep.txt'
        sentinel.write_text('User file must survive upgrade and uninstall')
        for label, extra in [('gpu', []), ('cpu', ['--hide-cuda'])]:
            if label=='gpu' and args.runtime_path: extra += ['--runtime-path',str(args.runtime_path.resolve())]
            command = [sys.executable, str(ROOT / 'tools/smoke_native.py'), '--payload', str(install),
                       '--output', str(output / label), '--audio', str(args.audio.resolve()),
                       '--model-source', str(args.model_source.resolve()), '--exercise-cancel', *extra]
            subprocess.run(command, check=True, timeout=360)
            report[label] = json.loads((output / label / 'result.json').read_text())
        if args.browser_test:
            subprocess.run(['node', str(args.browser_test.resolve()), str(output / 'browser')], check=True, timeout=120)
            report['browsers'] = json.loads((output / 'browser/result.json').read_text())
        installer()
        assert sentinel.is_file()
        report['sameVersionReinstallPreservesUserFile'] = True
        subprocess.run([str(install / 'Uninstall.exe'), '/S', '_?=' + str(install)],
                       check=True, timeout=120, creationflags=subprocess.CREATE_NO_WINDOW)
        assert not (install / 'SureLive-NativeHost.exe').exists()
        assert sentinel.is_file()
        assert (output / 'gpu/models/small/model.bin').is_file()
        for key in KEYS[:2]:
            for view in VIEWS:
                assert snapshot(key, view) is None
        report['uninstallAndModelRetention'] = True
    finally:
        for key, view, value in saved:
            restore(key, view, value)
        if shortcut_before is not None:
            shortcut.parent.mkdir(parents=True, exist_ok=True)
            shortcut.write_bytes(shortcut_before)
        elif shortcut.exists():
            shortcut.unlink()
        for key, view, value in saved:
            assert snapshot(key, view) == value, 'Registry restoration failed'
        report['originalRegistrationsRestored'] = True
        (output / 'result.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
    print(json.dumps({'installerValidation': 'passed', 'report': str(output / 'result.json')}))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    for field in ('installer', 'output', 'audio', 'model-source'):
        parser.add_argument('--' + field, required=True, type=Path)
    parser.add_argument('--browser-test', type=Path)
    parser.add_argument('--runtime-path', type=Path)
    run(parser.parse_args())
