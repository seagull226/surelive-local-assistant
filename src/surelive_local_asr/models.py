"""Pinned, hash-checked model data. Partial downloads survive cancellation."""
import hashlib, json, os, shutil, time, urllib.request
from pathlib import Path

def digest(file):
    h = hashlib.sha256()
    with Path(file).open('rb') as source:
        for block in iter(lambda: source.read(4 * 1024 * 1024), b''): h.update(block)
    return h.hexdigest()

class Models:
    def __init__(self, catalog, root):
        self.catalog, self.root = catalog, Path(root)
        self.root.mkdir(parents=True, exist_ok=True)

    def ready(self, model):
        folder = self.root / model
        try:
            receipt = json.loads((folder / 'verified.json').read_text())
            return receipt['revision'] == self.catalog[model]['revision'] and all(
                (folder / f['name']).stat().st_size == f['size'] and
                (folder / f['name']).stat().st_mtime_ns == receipt['mtimes'][f['name']]
                for f in self.catalog[model]['files'])
        except (OSError, KeyError, ValueError): return False

    def prepare(self, model, cancel, progress, import_dir=None, source='auto', telemetry=None):
        import msvcrt
        with (self.root / (model + '.lock')).open('a+b') as guard:
            guard.seek(0); guard.write(b'0'); guard.flush(); guard.seek(0)
            try: msvcrt.locking(guard.fileno(), msvcrt.LK_NBLCK, 1)
            except OSError: raise RuntimeError('另一个助手正在准备此模型，请稍后重试')
            try: return self._prepare(model, cancel, progress, import_dir, source, telemetry or (lambda _: None))
            finally:
                guard.seek(0); msvcrt.locking(guard.fileno(), msvcrt.LK_UNLCK, 1)

    def _prepare(self, model, cancel, progress, import_dir=None, source='auto', telemetry=lambda _: None):
        if source not in ('auto', 'official', 'mirror'): raise ValueError('无效下载源 / Invalid source')
        record = self.catalog[model]
        folder = self.root / model
        folder.mkdir(parents=True, exist_ok=True)
        if self.ready(model): return folder
        if import_dir and any(not (Path(import_dir) / f['name']).is_file() for f in record['files']):
            raise RuntimeError('模型文件不完整，请选择对应 CTranslate2 模型文件夹 / Incomplete model folder')
        needed = sum(f['size'] for f in record['files'] if not (folder / f['name']).exists())
        if shutil.disk_usage(folder).free < needed + 128 * 1024 ** 2:
            raise RuntimeError('模型目录空间不足，请在助手中选择其他位置')
        total, done = sum(f['size'] for f in record['files']), 0
        source_order = ['official', 'mirror'] if source == 'auto' else [source]
        for item in record['files']:
            if cancel.is_set(): raise RuntimeError('已取消模型准备；可继续下载')
            target = folder / item['name']
            if target.exists() and target.stat().st_size == item['size'] and digest(target) == item['sha256']:
                done += item['size']; continue
            partial = target.with_suffix(target.suffix + '.part')
            source = Path(import_dir) / item['name'] if import_dir else None
            if source and source.is_file():
                began = time.monotonic()
                with source.open('rb') as inp, partial.open('wb') as out:
                    while block := inp.read(4 * 1024 ** 2):
                        if cancel.is_set(): raise RuntimeError('已取消模型准备')
                        out.write(block)
                        progress(int((done + out.tell()) * 100 / total))
                        telemetry({'phase':'importing', 'source':'local', 'file':item['name'], 'received':done + out.tell(),
                                   'total':total, 'speed':out.tell() / max(.01, time.monotonic()-began)})
            else:
                offset = partial.stat().st_size if partial.exists() else 0
                if offset == item['size']:
                    if digest(partial) == item['sha256']:
                        os.replace(partial, target); done += item['size']; continue
                    partial.unlink(); offset = 0
                if offset > item['size']: partial.unlink(); offset = 0
                errors, downloaded = [], False
                for site in list(source_order):
                    url = item['url']
                    if site == 'mirror':
                        if not url.startswith('https://huggingface.co/'): continue
                        url = url.replace('https://huggingface.co/', 'https://hf-mirror.com/', 1)
                    for attempt in range(2):
                        if cancel.is_set(): raise RuntimeError('已取消模型准备；可继续下载 / Cancelled; resume available')
                        offset = partial.stat().st_size if partial.exists() else 0
                        telemetry({'phase':'connecting', 'source':site, 'file':item['name'], 'received':done+offset,
                                   'total':total, 'speed':0, 'attempt':attempt+1})
                        request = urllib.request.Request(url, headers={'Range': f'bytes={offset}-'} if offset else {})
                        try:
                            began, transferred = time.monotonic(), 0
                            with urllib.request.urlopen(request, timeout=15) as response:
                                if response.status == 206:
                                    if not response.headers.get('Content-Range', '').startswith(f'bytes {offset}-'):
                                        raise RuntimeError('下载分段不匹配 / Invalid response range')
                                elif response.status == 200: offset = 0
                                else: raise RuntimeError('下载暂不可用 / Download unavailable')
                                with partial.open('ab' if offset else 'wb') as out:
                                    while block := response.read(1024 * 1024):
                                        if cancel.is_set(): raise RuntimeError('已取消 / Cancelled')
                                        if out.tell() + len(block) > item['size']: raise RuntimeError('下载大小超出预期 / Invalid download size')
                                        out.write(block); transferred += len(block)
                                        progress(int((done + out.tell()) * 100 / total))
                                        telemetry({'phase':'downloading', 'source':site, 'file':item['name'], 'received':done+out.tell(),
                                                   'total':total, 'speed':transferred/max(.01,time.monotonic()-began)})
                            telemetry({'phase':'verifying', 'source':site, 'file':item['name'], 'received':done+item['size'], 'total':total, 'speed':0})
                            if partial.stat().st_size != item['size']: raise RuntimeError('文件未下载完整 / Incomplete download')
                            if digest(partial) != item['sha256']:
                                partial.unlink(); raise RuntimeError('模型校验失败 / Model checksum mismatch')
                            downloaded = True
                            if len(source_order) > 1: source_order = [site] + [s for s in source_order if s != site]
                            break
                        except (OSError, RuntimeError) as error:
                            errors.append(site + ': ' + str(error))
                            if cancel.is_set(): raise RuntimeError('已取消模型准备；可继续下载 / Cancelled; resume available')
                            if attempt == 0: cancel.wait(.4)
                    if downloaded: break
                if not downloaded: raise RuntimeError('下载失败，可重试、切换下载源或导入已有模型 / Download failed; retry, change source or import.\n' + '\n'.join(errors)[-500:])
            if partial.stat().st_size != item['size'] or digest(partial) != item['sha256']:
                partial.unlink(missing_ok=True)
                raise RuntimeError('模型校验失败，请重试下载或选择正确的模型文件夹')
            os.replace(partial, target)
            done += item['size']
        receipt = {'revision': record['revision'], 'mtimes': {f['name']: (folder / f['name']).stat().st_mtime_ns for f in record['files']}}
        (folder / 'verified.json').write_text(json.dumps(receipt), encoding='utf-8')
        progress(100)
        return folder
