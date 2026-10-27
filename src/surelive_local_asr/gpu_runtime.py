"""Discover compatible local runtimes or prepare pinned NVIDIA components on demand."""
import json, os, shutil, subprocess, threading, time, uuid, zipfile
from pathlib import Path
from models import Models, digest
from session_state import atomic_json


def system_candidates(environ=None):
    env = os.environ if environ is None else environ
    folders = []
    def add(value):
        p = Path(value)
        if p.is_absolute() and p.is_dir() and p not in folders: folders.append(p)
    for value in env.get('PATH', '').split(os.pathsep):
        if value: add(value)
    for key, value in env.items():
        if key.startswith('CUDA_PATH') or key == 'CUDNN_PATH':
            add(str(Path(value)/'bin'))
            for p in (Path(value)/'bin').glob('12*'): add(str(p))
    for root in [Path(env.get('ProgramFiles', 'C:/Program Files'))/'NVIDIA GPU Computing Toolkit/CUDA',
                 Path(env.get('ProgramFiles', 'C:/Program Files'))/'NVIDIA/CUDNN']:
        for pattern in ['v*/bin','v*/bin/12*']:
            for p in sorted(root.glob(pattern), reverse=True): add(str(p))
    cuda = [p for p in folders if (p/'cublas64_12.dll').is_file()]
    dnn = [p for p in folders if (p/'cudnn64_9.dll').is_file()]
    rt = [p for p in folders if (p/'cudart64_12.dll').is_file()]
    # Do not mix several copies of one library family or recursively search other applications.
    candidates = []
    for c in cuda[:3]:
        for d in dnn[:3]:
            r = c if c in rt else (rt[0] if rt else None)
            if r:
                group = list(dict.fromkeys(map(str,[c,d,r])))
                if group not in candidates: candidates.append(group)
    return candidates[:6]


class GpuRuntime:
    def __init__(self, catalog, root, worker_command, bundled, device_count=None):
        self.catalog, self.root = catalog, Path(root)
        self.command, self.bundled = worker_command, Path(bundled)
        self.root.mkdir(parents=True, exist_ok=True)
        if device_count is None:
            from gpu_probe import driver_devices
            device_count = driver_devices
        self.device_count = device_count
        self.lock = threading.RLock()
        self.shutdown = threading.Event()
        self.status = {'preferred':'cpu','cudaDevices':0,'state':'checking','source':'none','directories':[]}

    def _check(self, paths, cancel):
        if cancel.is_set() or self.shutdown.is_set(): raise RuntimeError('已取消 / Cancelled')
        process = subprocess.Popen([*self.command, '--gpu-check', json.dumps(paths)], stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, encoding='utf-8', errors='replace',
            env={**os.environ,'PYINSTALLER_RESET_ENVIRONMENT':'1'}, creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0))
        deadline = time.monotonic()+25
        try:
            while True:
                if cancel.is_set() or self.shutdown.is_set(): raise RuntimeError('已取消 / Cancelled')
                try: out, _ = process.communicate(timeout=.2); break
                except subprocess.TimeoutExpired:
                    if time.monotonic()>deadline: return None
            if process.returncode: return None
            value = json.loads(out)
            return value if value.get('preferred')=='cuda' else None
        except (OSError, ValueError): return None
        finally:
            if process.poll() is None: process.kill(); process.communicate()

    def _managed(self):
        try:
            active = json.loads((self.root/'active.json').read_text())
            name = active['folder']
            if active['revision'] != self.catalog['revision'] or not name.startswith('runtime-') or Path(name).name != name: return None
            folder = self.root/name
            if not folder.resolve().is_relative_to(self.root.resolve()): return None
            for component in self.catalog['components']:
                for member in component['members']:
                    p = folder/member['name']
                    if p.stat().st_size != member['size'] or digest(p) != member['sha256']: return None
            return folder
        except (OSError, ValueError, KeyError): return None

    def discover(self, cancel=None):
        cancel = cancel or self.shutdown
        with self.lock:
            count = self.device_count()
            self.status = {'preferred':'cpu','cudaDevices':count,'state':'checking','source':'none','directories':[]}
            if not count:
                self.status['state']='cpu'; return self.status
            candidates = []
            if self.bundled.is_dir(): candidates.append(('bundled',[str(self.bundled)]))
            managed = self._managed()
            if managed: candidates.append(('downloaded',[str(managed)]))
            candidates += [('system',x) for x in system_candidates()]
            for source, paths in candidates:
                result = self._check(paths,cancel)
                if result:
                    self.status = {**result,'state':'ready','source':source,'directories':paths}; return self.status
            self.status['state']='needed'; return self.status

    def ensure(self, cancel, telemetry=lambda _:None, download=True, retry=False):
        # Different native sessions share a cache, but never publish partially extracted libraries.
        while not self.lock.acquire(timeout=.2):
            if cancel.is_set(): raise RuntimeError('已取消 / Cancelled')
        try:
            if cancel.is_set(): raise RuntimeError('已取消 / Cancelled')
            if self.status['state']=='checking' or retry: self.discover(cancel)
            if not download or self.status['state'] in ('ready','cpu'): return dict(self.status)
            if self.status['state']=='failed' and not self._managed(): return dict(self.status)
            import msvcrt
            with (self.root/'prepare.lock').open('a+b') as guard:
                guard.seek(0); guard.write(b'0'); guard.flush()
                while True:
                    guard.seek(0)
                    try: msvcrt.locking(guard.fileno(),msvcrt.LK_NBLCK,1); break
                    except OSError:
                        if cancel.wait(.2): raise RuntimeError('已取消 / Cancelled')
                        telemetry({'phase':'gpu-waiting','source':'nvidia','received':0,'total':self.download_bytes})
                try:
                    current = self._managed()
                    if current:
                        result=self._check([str(current)],cancel)
                        if result:
                            self.status={**result,'state':'ready','source':'downloaded','directories':[str(current)]};return dict(self.status)
                    if self.status['state']=='failed': return dict(self.status)
                    folder = self._prepare(cancel,telemetry)
                    result = self._check([str(folder)],cancel)
                    if not result: raise RuntimeError('加速组件与此显卡或驱动不兼容 / GPU runtime is incompatible with this GPU or driver')
                    atomic_json(self.root/'active.json',{'revision':self.catalog['revision'],'folder':folder.name})
                    self.status={**result,'state':'ready','source':'downloaded','directories':[str(folder)]}
                    # Keep the verified runtime, free only known archive files after successful activation.
                    for item in self.catalog['components']:
                        (self.root/'downloads'/item['id']/item['name']).unlink(missing_ok=True)
                    return dict(self.status)
                finally:
                    guard.seek(0);msvcrt.locking(guard.fileno(),msvcrt.LK_UNLCK,1)
        except Exception as error:
            self.status={**self.status,'preferred':'cpu','state':'needed' if cancel.is_set() else 'failed',
                         'source':'none','directories':[],'error':str(error)}
            if cancel.is_set(): raise
            return dict(self.status)
        finally: self.lock.release()

    @property
    def download_bytes(self): return sum(c['size'] for c in self.catalog['components'])

    def _prepare(self, cancel, telemetry):
        unpacked = sum(m['size'] for c in self.catalog['components'] for m in c['members'])
        if shutil.disk_usage(self.root).free < self.download_bytes+unpacked+128*1024**2:
            raise RuntimeError('加速组件需要约 3 GB 临时空间，可使用 CPU / GPU preparation needs about 3 GB free; CPU remains available')
        self.status={**self.status,'state':'preparing'}
        catalog={c['id']:{'revision':self.catalog['revision'],'files':[c]} for c in self.catalog['components']}
        downloader=Models(catalog,self.root/'downloads')
        done=0; paths=[]
        for c in self.catalog['components']:
            def report(detail):
                telemetry({**detail,'phase':'gpu-'+detail['phase'],'source':'nvidia',
                           'received':done+detail.get('received',0),'total':self.download_bytes})
            location=downloader.prepare(c['id'],cancel,lambda _:None,source='official',telemetry=report)
            paths.append((c,location/c['name']));done+=c['size']
        folder=self.root/('pending-'+uuid.uuid4().hex); folder.mkdir()
        assert folder.resolve().is_relative_to(self.root.resolve())
        try:
            for c, archive in paths:
                with zipfile.ZipFile(archive) as z:
                    for item in c['members']:
                        if Path(item['name']).name!=item['name']: raise ValueError('Invalid runtime filename')
                        if z.getinfo(item['member']).file_size!=item['size']: raise RuntimeError('Invalid component size')
                        target=folder/item['name']
                        telemetry({'phase':'gpu-extracting','source':'nvidia','file':item['name'],
                                   'received':self.download_bytes,'total':self.download_bytes})
                        with z.open(item['member']) as inp,target.open('wb') as out:
                            while block:=inp.read(4*1024**2):
                                if cancel.is_set(): raise RuntimeError('已取消 / Cancelled')
                                out.write(block)
                        if digest(target)!=item['sha256']: raise RuntimeError('加速组件校验失败 / GPU component checksum mismatch')
            final=self.root/('runtime-'+uuid.uuid4().hex);os.replace(folder,final)
            return final
        finally:
            if folder.exists(): shutil.rmtree(folder)
