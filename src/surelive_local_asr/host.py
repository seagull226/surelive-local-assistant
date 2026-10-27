"""User-installed native host. Only the registered preview extension can pair."""
import argparse, json, os, re, secrets, shutil, struct, subprocess, sys, tempfile, threading, time
from pathlib import Path
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlsplit, parse_qs
from models import Models
from session_state import Session, atomic_json
from gpu_runtime import GpuRuntime

BASE = Path(sys.executable).parent if getattr(sys, 'frozen', False) else Path(__file__).parent
EXTENSION = 'pigcndembijihpdlkdpmopjddomgjogc'
ORIGIN = 'chrome-extension://' + EXTENSION
if '--write-manifest' in sys.argv:
    (BASE / 'native-host.json').write_text(json.dumps({
        'name': 'com.surelive.asr.preview', 'description': 'SureLive ASR preview',
        'path': str(BASE / 'SureLive-NativeHost.exe'), 'type': 'stdio', 'allowed_origins': [ORIGIN + '/'],
    }, ensure_ascii=True), encoding='utf-8')
    raise SystemExit(0)
DATA = Path(os.environ.get('LOCALAPPDATA', str(Path.home()))) / 'SureLiveASRPreview'
DATA.mkdir(parents=True, exist_ok=True)
settings_file = DATA / 'settings.json'
try: settings = json.loads(settings_file.read_text(encoding='utf-8'))
except (OSError, ValueError): settings = {}
catalog = json.loads((BASE / 'models.json').read_text(encoding='utf-8'))
models = Models(catalog, settings.get('modelDirectory', str(DATA / 'models')))
worker = BASE / 'runtime' / 'SureLive-Inference.exe'
gpu = GpuRuntime(json.loads((BASE / 'gpu-runtime.json').read_text(encoding='utf-8')),
                 DATA / 'gpu-runtime', [str(worker)], BASE / 'runtime/gpu')
ffmpeg = BASE / 'ffmpeg.exe'
secret = secrets.token_urlsafe(32)
lock = threading.RLock()
jobs = {}
hardware = {'preferred': 'cpu', 'cudaDevices': 0}
DISK_RESERVE = 64 * 1024 ** 2

def require_space(folder, needed=0):
    if shutil.disk_usage(folder).free < needed + DISK_RESERVE:
        raise RuntimeError('临时磁盘空间不足，请释放空间后重试 / Insufficient temporary disk space')

def refresh_model_directory():
    if any(not j.get('finished') for j in jobs.values()): return
    try:
        current = json.loads(settings_file.read_text(encoding='utf-8'))
        settings.update(current)
        directory = current.get('modelDirectory')
        if isinstance(directory, str) and Path(directory).is_dir(): models.root = Path(directory)
    except (OSError, ValueError): pass

def probe():
    global hardware
    try:
        hardware = gpu.discover()
    except Exception as error:
        hardware = gpu.status = {'preferred':'cpu','cudaDevices':0,'state':'failed','source':'none','directories':[],'error':str(error)}

def stop(job):
    job['cancel'].set()
    process = job.get('process')
    if process and process.poll() is None: process.terminate()

def execute(job, command, stage):
    if job['cancel'].is_set(): raise RuntimeError('已取消')
    job['stage'] = stage
    job.pop('percent', None)
    process = subprocess.Popen(command, stdin=subprocess.DEVNULL, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                               env={**os.environ, 'PYINSTALLER_RESET_ENVIRONMENT': '1'},
                               text=True, encoding='utf-8', errors='replace', creationflags=subprocess.CREATE_NO_WINDOW)
    job['process'] = process
    monitored = threading.Event()
    def monitor_space():
        while not monitored.wait(.25):
            try: require_space(job['folder'])
            except (OSError, RuntimeError) as error:
                job['resourceError'] = str(error)
                if process.poll() is None: process.terminate()
                return
    watcher = threading.Thread(target=monitor_space, daemon=True); watcher.start()
    tail = []
    try:
        for line in process.stdout:
            tail.append(line.strip()); tail = tail[-8:]
            if line.strip() in ('loading', 'recognizing', 'cpu-fallback'): job['stage'] = line.strip()
            if line.startswith('SURELIVE_PROGRESS '):
                progress = json.loads(line[len('SURELIVE_PROGRESS '):])
                job.update({k:progress[k] for k in ('stage','percent','chunk','chunks','processedSec','totalSec') if k in progress})
        code = process.wait()
    finally:
        monitored.set();watcher.join(timeout=1)
        if process.poll() is None: process.terminate(); process.wait()
    if job['cancel'].is_set(): raise RuntimeError('已取消')
    if job.get('resourceError'): raise RuntimeError(job['resourceError'])
    if code: raise RuntimeError(('\n'.join(tail))[-1400:] or '识别进程异常，请重试')

def run(job):
    global hardware
    try:
        if job.get('gpuOnly'):
            job['stage'] = 'preparing'
            hardware = gpu.ensure(job['cancel'], lambda d: job.update(download=d,percent=int(d.get('received',0)*100/max(1,d.get('total',1)))), retry=True)
            if job['cancel'].is_set(): raise RuntimeError('已取消 / Cancelled')
            if hardware['state']=='failed': raise RuntimeError(hardware['error'])
            job.update(result={'ready':hardware['preferred']=='cuda'},stage='complete');return
        job['stage'] = 'preparing'
        folder = models.prepare(job['model'], job['cancel'], lambda n: job.update(percent=n), job.get('import_dir'),
                                job.get('source', 'auto'), lambda detail: job.update(download=detail))
        if job.get('prepareOnly'): job['result'] = {'ready': True}
        else:
            if job['device'] != 'cpu':
                hardware = gpu.ensure(job['cancel'], lambda d: job.update(stage='preparing',download=d,
                                     percent=int(d.get('received',0)*100/max(1,d.get('total',1)))))
                job['gpuDirectories'] = hardware.get('directories',[])
                if hardware['preferred'] != 'cuda':
                    job['device'] = 'cpu'
                    if hardware.get('error'): job['warning'] = 'NVIDIA 加速准备失败，本次使用 CPU / GPU preparation failed; using CPU'
                job.pop('download',None)
            temporary = job['folder']; pcm = temporary / 'audio.f32'; output = temporary / 'result.json'
            execute(job, [str(ffmpeg), '-v', 'error', '-nostdin', '-i', str(temporary / 'input.media'),
                          '-map', '0:a:0', '-vn', '-ac', '1', '-ar', '16000', '-f', 'f32le', str(pcm)], 'extracting')
            (temporary / 'input.media').unlink()  # Release the streamed upload before recognizing the audio.
            spec = {key: job[key] for key in ('model', 'language', 'device')}
            spec.update(modelPath=str(folder), pcm=str(pcm), output=str(output), gpuDirectories=job.get('gpuDirectories',[]),
                        gpuPreparationFailed=bool(job.get('warning')))
            (temporary / 'request.json').write_text(json.dumps(spec), encoding='utf-8')
            execute(job, [str(worker), str(temporary / 'request.json')], 'loading')
            job['result'] = json.loads(output.read_text(encoding='utf-8'))
        job['stage'] = 'complete'
    except Exception as error:
        job.update(stage='cancelled' if job['cancel'].is_set() else 'error', error=str(error))
    finally:
        if job.get('folder'): shutil.rmtree(job['folder'], ignore_errors=True)
        job['finished'] = True

def begin(model, language='auto', device='auto', prepare_only=False, import_dir=None, key=None):
    import uuid
    with lock:
        refresh_model_directory()
        if model not in catalog: raise ValueError('请选择支持的模型')
        if language != 'auto' and language not in catalog[model]['languages']: raise ValueError('该模型不支持所选语言')
        if device not in ('auto', 'cpu'): raise ValueError('无效运行模式')
        if any(not j.get('finished') for j in jobs.values()): raise ValueError('上一任务仍在处理中，请等待或取消')
        if key in jobs: raise ValueError('任务已存在')
        jobs.clear(); key = key or str(uuid.uuid4())
        job = {'model': model, 'language': language, 'device': device, 'stage': 'preparing' if prepare_only else 'uploading',
               'cancel': threading.Event(), 'prepareOnly': prepare_only, 'import_dir': import_dir,
               'source': settings.get('downloadSource', 'auto')}
        if settings.get('accelerationMode') == 'cpu': job['device'] = 'cpu'
        jobs[key] = job
        return key, job

class Handler(BaseHTTPRequestHandler):
    def log_message(self, *_): pass
    def allowed(self):
        return (self.headers.get('Host') == f'127.0.0.1:{server.server_port}' and
                self.headers.get('Origin') in (None, ORIGIN) and secrets.compare_digest(self.headers.get('Authorization', ''), 'Bearer ' + secret))
    def reply(self, status, data):
        body = json.dumps(data, ensure_ascii=False).encode('utf-8')
        self.send_response(status)
        if self.headers.get('Origin') == ORIGIN: self.send_header('Access-Control-Allow-Origin', ORIGIN)
        self.send_header('Vary', 'Origin'); self.send_header('Content-Type', 'application/json')
        self.send_header('Content-Length', str(len(body))); self.end_headers()
        try: self.wfile.write(body)
        except (BrokenPipeError, ConnectionResetError, ConnectionAbortedError): pass
    def do_OPTIONS(self):
        if self.headers.get('Origin') != ORIGIN or self.headers.get('Host') != f'127.0.0.1:{server.server_port}':
            self.reply(403, {}); return
        self.send_response(204); self.send_header('Access-Control-Allow-Origin', ORIGIN)
        self.send_header('Access-Control-Allow-Headers', 'Authorization,Content-Type')
        self.send_header('Access-Control-Allow-Methods', 'GET,PUT,DELETE,POST'); self.end_headers()
    def do_GET(self):
        if not self.allowed(): self.reply(403, {'error': '助手连接已失效，请重新连接'}); return
        if self.path == '/health':
            with lock: refresh_model_directory()
            self.reply(200, {'version': 1, 'capabilities': {'longMedia':True, 'chunkSeconds':300}, 'hardware': gpu.status, 'models': {
                k: {'ready': models.ready(k), 'bytes': sum(f['size'] for f in v['files']), 'languages': v['languages']}
                for k, v in catalog.items()}}); return
        key = self.path.removeprefix('/jobs/')
        with lock:
            job = jobs.get(key)
            self.reply(200, {k: job[k] for k in ('stage', 'percent', 'chunk', 'chunks', 'processedSec', 'totalSec', 'download', 'error', 'warning', 'result', 'finished') if k in job}) if job else self.reply(404, {})
    def do_POST(self):
        if not self.allowed(): self.reply(403, {}); return
        try:
            length = int(self.headers.get('Content-Length', '0'))
            if self.path != '/prepare' or not 0 < length <= 1024: raise ValueError('无效请求')
            spec = json.loads(self.rfile.read(length))
            if not re.fullmatch(r'[a-f0-9-]{36}', spec.get('id', '')): raise ValueError('无效任务')
            key, job = begin(spec['model'], prepare_only=True, key=spec['id'])
            threading.Thread(target=run, args=(job,), daemon=True).start()
            self.reply(202, {'id': key})
        except (ValueError, KeyError) as error: self.reply(400, {'error': str(error)})
    def do_DELETE(self):
        if not self.allowed(): self.reply(403, {}); return
        with lock:
            job = jobs.get(self.path.removeprefix('/jobs/'))
            if job: stop(job)
        self.reply(200, {'cancelled': True})
    def do_PUT(self):
        if not self.allowed(): self.reply(403, {}); return
        job = None
        try:
            parsed = urlsplit(self.path); key = parsed.path.removeprefix('/jobs/')
            if not re.fullmatch(r'[a-f0-9-]{36}', key): raise ValueError('无效任务')
            size = int(self.headers.get('Content-Length', '0'))
            if size <= 0: raise ValueError('无有效文件 / Empty media file')
            query = parse_qs(parsed.query)
            _, job = begin(query.get('model', ['small'])[0], query.get('language', ['auto'])[0], query.get('device', ['auto'])[0], key=key)
            job['folder'] = Path(tempfile.mkdtemp(prefix='surelive-asr-preview-'))
            require_space(job['folder'], size)
            self.connection.settimeout(120)
            with (job['folder'] / 'input.media').open('wb') as out:
                remaining = size
                while remaining:
                    if job['cancel'].is_set(): raise ValueError('已取消')
                    require_space(job['folder'])
                    chunk = self.rfile.read(min(1024 * 1024, remaining))
                    if not chunk: raise ValueError('文件发送中断')
                    out.write(chunk); remaining -= len(chunk)
            threading.Thread(target=run, args=(job,), daemon=True).start(); self.reply(202, {'id': key})
        except (ValueError, OSError, RuntimeError) as error:
            if job:
                job.update(stage='error', error=str(error), finished=True)
                if job.get('folder'): shutil.rmtree(job['folder'], ignore_errors=True)
            self.reply(400, {'error': str(error)})

server = ThreadingHTTPServer(('127.0.0.1', 0), Handler)
server.daemon_threads = True

def shutdown():
    gpu.shutdown.set()
    for job in list(jobs.values()): stop(job)
    server.shutdown(); server.server_close()
    for job in list(jobs.values()):
        process = job.get('process')
        if process:
            try: process.wait(timeout=5)
            except subprocess.TimeoutExpired: process.kill(); process.wait()
        if job.get('folder'): shutil.rmtree(job['folder'], ignore_errors=True)

def gui():
    from desktop import run_gui
    run_gui(sys.modules[__name__])

def status_snapshot():
    with lock:
        job = next(iter(jobs.values()), {})
        return {'kind': 'native' if native else 'manager', 'hardware': gpu.status,
                'job': {k: job[k] for k in ('model', 'stage', 'percent', 'chunk', 'chunks', 'download', 'error', 'finished') if k in job}}

if __name__ == '__main__':
    native = len(sys.argv) > 1 and sys.argv[1].startswith('chrome-extension://')
    if native and sys.argv[1].rstrip('/') != ORIGIN: raise SystemExit(1)
    if not native and '--gui' not in sys.argv: raise SystemExit(1)
    threading.Thread(target=probe, daemon=True).start()
    threading.Thread(target=server.serve_forever, daemon=True).start()
    session = Session(DATA, status_snapshot)
    if native:
        import msvcrt
        msvcrt.setmode(sys.stdin.fileno(), os.O_BINARY); msvcrt.setmode(sys.stdout.fileno(), os.O_BINARY)
        body = json.dumps({'endpoint': f'http://127.0.0.1:{server.server_port}', 'token': secret, 'version': 1}).encode()
        sys.stdout.buffer.write(struct.pack('<I', len(body)) + body); sys.stdout.buffer.flush()
        def read_pipe():
            def read_exact(size):
                data = b''
                while len(data) < size:
                    chunk = os.read(sys.stdin.fileno(), size-len(data))
                    if not chunk: break
                    data += chunk
                return data
            try:
                while True:
                    length = read_exact(4)
                    if len(length) != 4: break
                    size = struct.unpack('<I', length)[0]
                    if size > 4096 or len(read_exact(size)) != size: break
            finally: session.exit_requested.set()
        threading.Thread(target=read_pipe, daemon=True).start()
        try: session.exit_requested.wait()
        finally: shutdown(); session.close()
    else:
        try: gui()
        finally: shutdown(); session.close()
