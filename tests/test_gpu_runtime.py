import hashlib, io, json, os, tempfile, threading, unittest, zipfile
from pathlib import Path
from unittest.mock import patch
from gpu_runtime import GpuRuntime, system_candidates


class GpuRuntimeTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.root=Path(self.tmp.name);self.cancel=threading.Event()
        data=b'checked DLL bytes';buf=io.BytesIO()
        with zipfile.ZipFile(buf,'w') as z:z.writestr('upstream/bin/test.dll',data);z.writestr('../escaped.dll',b'never extract')
        self.archive=buf.getvalue()
        self.component={'id':'test','name':'runtime.zip','size':len(self.archive),'sha256':hashlib.sha256(self.archive).hexdigest(),
                        'url':'https://example.invalid/runtime.zip','members':[{'member':'upstream/bin/test.dll','name':'test.dll',
                         'size':len(data),'sha256':hashlib.sha256(data).hexdigest()}]}
        self.catalog={'revision':'test-v1','components':[self.component]}
        self.manager=GpuRuntime(self.catalog,self.root/'cache',['unused-worker'],self.root/'bundled',device_count=lambda:1)
        self.no_system=patch('gpu_runtime.system_candidates',return_value=[]);self.no_system.start()
        self.good={'preferred':'cuda','cudaDevices':1,'cudaTypes':['float16']}
    def tearDown(self):self.no_system.stop();self.tmp.cleanup()
    def download(self,*args,**kwargs):
        r=io.BytesIO(self.archive);r.status=200;r.headers={};return r
    def test_no_gpu_never_downloads(self):
        self.manager.device_count=lambda:0
        with patch('urllib.request.urlopen',side_effect=AssertionError('no download')):
            self.assertEqual(self.manager.ensure(self.cancel)['state'],'cpu')
    def test_compatible_system_is_reused_without_download(self):
        with patch('gpu_runtime.system_candidates',return_value=[['C:/known/runtime']]),patch.object(self.manager,'_check',return_value=self.good),patch('urllib.request.urlopen',side_effect=AssertionError('no download')):
            result=self.manager.ensure(self.cancel)
            self.assertEqual(result['source'],'system');self.assertFalse((self.manager.root/'active.json').exists())
    def test_verified_activation_restart_reuse_and_no_archive_traversal(self):
        with patch('urllib.request.urlopen',side_effect=self.download),patch.object(self.manager,'_check',return_value=self.good):
            result=self.manager.ensure(self.cancel)
        self.assertEqual(result['source'],'downloaded');self.assertFalse((self.manager.root/'escaped.dll').exists())
        self.assertFalse((self.manager.root/'downloads/test/runtime.zip').exists())
        other=GpuRuntime(self.catalog,self.manager.root,['unused'],self.root/'missing',device_count=lambda:1)
        with patch.object(other,'_check',return_value=self.good),patch('urllib.request.urlopen',side_effect=AssertionError('no redownload')):
            self.assertEqual(other.ensure(self.cancel)['source'],'downloaded')
    def test_download_failure_allows_cpu_and_explicit_retry(self):
        with patch('urllib.request.urlopen',side_effect=OSError('offline')):
            self.assertEqual(self.manager.ensure(self.cancel)['state'],'failed')
        with patch('urllib.request.urlopen',side_effect=self.download),patch.object(self.manager,'_check',return_value=self.good):
            self.assertEqual(self.manager.ensure(self.cancel,retry=True)['preferred'],'cuda')
    def test_corrupt_download_is_not_activated(self):
        self.component['sha256']='0'*64
        with patch('urllib.request.urlopen',side_effect=self.download):
            self.assertEqual(self.manager.ensure(self.cancel)['preferred'],'cpu')
        self.assertFalse((self.manager.root/'active.json').exists())
    def test_extracted_dll_checksum_failure_is_not_activated(self):
        self.component['members'][0]['sha256']='0'*64
        with patch('urllib.request.urlopen',side_effect=self.download):
            self.assertEqual(self.manager.ensure(self.cancel)['state'],'failed')
        self.assertFalse((self.manager.root/'active.json').exists())
    def test_failed_operation_check_is_not_activated(self):
        with patch('urllib.request.urlopen',side_effect=self.download),patch.object(self.manager,'_check',return_value=None):
            self.assertEqual(self.manager.ensure(self.cancel)['state'],'failed')
        self.assertFalse((self.manager.root/'active.json').exists())
    def test_cancel_during_download_retains_partial_and_resumes(self):
        manager=self.manager;event=self.cancel;content=self.archive
        class Interrupted(io.BytesIO):
            status=200;headers={}
            def read(self,size=-1):
                if self.tell():event.set()
                return super().read(5)
        with patch('urllib.request.urlopen',return_value=Interrupted(content)),self.assertRaises(RuntimeError):manager.ensure(event)
        part=manager.root/'downloads/test/runtime.zip.part';self.assertTrue(part.exists());offset=part.stat().st_size
        self.assertFalse((manager.root/'active.json').exists());event.clear()
        def resume(request,**kwargs):
            self.assertEqual(request.headers['Range'],f'bytes={offset}-')
            r=io.BytesIO(content[offset:]);r.status=206;r.headers={'Content-Range':f'bytes {offset}-{len(content)-1}/{len(content)}'};return r
        with patch('urllib.request.urlopen',side_effect=resume),patch.object(manager,'_check',return_value=self.good):
            self.assertEqual(manager.ensure(event)['preferred'],'cuda')
    def test_cpu_request_does_not_download_missing_components(self):
        with patch('urllib.request.urlopen',side_effect=AssertionError('no download')):
            self.assertEqual(self.manager.ensure(self.cancel,download=False)['preferred'],'cpu')
    def test_waiting_for_another_preparation_can_be_cancelled(self):
        import msvcrt
        self.manager.status.update(state='needed',cudaDevices=1)
        with (self.manager.root/'prepare.lock').open('a+b') as guard:
            guard.write(b'0');guard.flush();guard.seek(0);msvcrt.locking(guard.fileno(),msvcrt.LK_NBLCK,1)
            try:
                with self.assertRaises(RuntimeError):
                    self.manager.ensure(self.cancel,lambda _:self.cancel.set())
            finally:guard.seek(0);msvcrt.locking(guard.fileno(),msvcrt.LK_UNLCK,1)
        self.assertEqual(self.manager.status['state'],'needed')
    def test_changed_managed_dll_requires_repair(self):
        with patch('urllib.request.urlopen',side_effect=self.download),patch.object(self.manager,'_check',return_value=self.good):self.manager.ensure(self.cancel)
        p=Path(self.manager.status['directories'][0])/'test.dll';p.write_bytes(b'tampered')
        self.assertIsNone(self.manager._managed())
    def test_discovery_ignores_relative_search_paths(self):
        self.no_system.stop()
        with patch('gpu_runtime.os.environ',{}):self.assertEqual(system_candidates({'PATH':'.;relative','ProgramFiles':str(self.root/'empty')}),[])
        self.no_system.start()
