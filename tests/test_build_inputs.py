import hashlib
from pathlib import Path
import tempfile
import unittest
from build_windows import native_inputs, build, ROOT


class BuildInputTests(unittest.TestCase):
    def test_tampered_input_rejected(self):
        with tempfile.TemporaryDirectory() as folder:
            binary = Path(folder) / 'ffmpeg.exe'
            binary.write_bytes(b'changed')
            with self.assertRaisesRegex(ValueError, 'SHA-256 mismatch'):
                native_inputs({'ffmpeg': {'path': str(binary), 'sha256': hashlib.sha256(b'original').hexdigest()}})

    def test_verified_cpu_input_needs_no_gpu_directory(self):
        with tempfile.TemporaryDirectory() as folder:
            binary = Path(folder) / 'ffmpeg.exe'
            binary.write_bytes(b'fixture')
            config = {'ffmpeg': {'path': str(binary), 'sha256': hashlib.sha256(b'fixture').hexdigest()}, 'gpu': []}
            self.assertEqual(len(native_inputs(config)), 1)

    @unittest.skipUnless(__import__('sys').platform == 'win32', 'Windows output restriction')
    def test_output_cannot_target_another_project(self):
        with self.assertRaisesRegex(ValueError, 'NEW directory'):
            build(ROOT / 'nonexistent-config.json', ROOT.parent / 'unrelated-output')
