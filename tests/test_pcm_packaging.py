"""The helper supplies PCM arrays, so importing inference must not require PyAV."""
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from build_windows import stage_pcm_dependency


class PcmPackagingTests(unittest.TestCase):
    def test_inference_import_works_with_pyav_blocked(self):
        with tempfile.TemporaryDirectory() as folder:
            patched = stage_pcm_dependency(Path(folder))
            script = '''
import sys, importlib.abc
class NoAv(importlib.abc.MetaPathFinder):
    def find_spec(self, fullname, path=None, target=None):
        if fullname == 'av' or fullname.startswith('av.'):
            raise ImportError('PyAV deliberately unavailable')
sys.meta_path.insert(0, NoAv())
sys.path.insert(0, sys.argv[1])
from faster_whisper import WhisperModel, BatchedInferencePipeline
from faster_whisper.audio import pad_or_trim
import numpy as np
assert pad_or_trim(np.ones((2, 2)), 3).shape == (2, 3)
assert 'av' not in sys.modules
'''
            subprocess.run([sys.executable, '-c', script, str(patched)], check=True, timeout=45)
