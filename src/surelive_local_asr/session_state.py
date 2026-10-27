"""Local status/control files contain no media, transcripts or connection credentials."""
import json, os, re, threading, time, uuid
from pathlib import Path

def atomic_json(path, value):
    path = Path(path)
    temporary = path.with_suffix('.' + str(os.getpid()) + '.tmp')
    temporary.write_text(json.dumps(value, ensure_ascii=False), encoding='utf-8')
    os.replace(temporary, path)

class Session:
    def __init__(self, data, snapshot):
        self.root = Path(data) / 'sessions'; self.root.mkdir(parents=True, exist_ok=True)
        self.id = uuid.uuid4().hex; self.snapshot = snapshot
        self.exit_requested = threading.Event(); self.closed = threading.Event()
        self.path = self.root / (self.id + '.json'); self.command = self.root / (self.id + '.stop')
        self.thread = threading.Thread(target=self.loop, daemon=True); self.thread.start()

    def loop(self):
        while not self.closed.is_set():
            if self.command.exists(): self.exit_requested.set()
            try: atomic_json(self.path, {'id':self.id, 'pid':os.getpid(), 'at':time.time(), **self.snapshot()})
            except (OSError, RuntimeError): pass
            self.closed.wait(.5)

    def close(self):
        self.closed.set(); self.thread.join(timeout=2)
        self.path.unlink(missing_ok=True); self.command.unlink(missing_ok=True)

def sessions(data):
    result = []
    for file in (Path(data) / 'sessions').glob('*.json'):
        try:
            value = json.loads(file.read_text(encoding='utf-8'))
            if time.time() - value['at'] < 4 and value['id'] + '.json' == file.name:
                result.append(value)
        except (OSError, ValueError, KeyError, TypeError): pass
    return result

def request_exit(data, session_id):
    if not re.fullmatch(r'[0-9a-f]{32}', session_id): raise ValueError('Invalid session')
    (Path(data) / 'sessions' / (session_id + '.stop')).touch()
