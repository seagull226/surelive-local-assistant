import hashlib, json, tempfile, threading, unittest
from pathlib import Path
from unittest.mock import patch
from models import Models

class ModelTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(); self.root = Path(self.tmp.name)
        self.data = b'model data for verification'
        self.catalog = {'small': {'revision': 'pinned', 'files': [{'name':'model.bin', 'size':len(self.data),
            'sha256':hashlib.sha256(self.data).hexdigest(), 'url':'https://example.invalid/model.bin'}]}}
        self.manager = Models(self.catalog, self.root / 'models'); self.cancel = threading.Event()
        self.source = self.root / 'source'; self.source.mkdir(); (self.source / 'model.bin').write_bytes(self.data)
    def tearDown(self): self.tmp.cleanup()
    def test_import_verified_and_detects_changed_file(self):
        folder = self.manager.prepare('small', self.cancel, lambda _:None, self.source)
        self.assertTrue(self.manager.ready('small'))
        (folder / 'model.bin').write_bytes(b'corrupt')
        self.assertFalse(self.manager.ready('small'))
    def test_invalid_import_is_not_marked_ready(self):
        (self.source / 'model.bin').write_bytes(b'wrong')
        with self.assertRaisesRegex(RuntimeError,'校验'): self.manager.prepare('small', self.cancel, lambda _:None, self.source)
        self.assertFalse(self.manager.ready('small'))
    def test_cancel_preserves_existing_valid_model(self):
        self.manager.prepare('small', self.cancel, lambda _:None, self.source)
        self.cancel.set(); self.manager.prepare('small', self.cancel, lambda _:None, self.source)
        self.assertTrue(self.manager.ready('small'))
    def test_complete_partial_is_verified_without_network(self):
        folder=self.manager.root/'small';folder.mkdir();(folder/'model.bin.part').write_bytes(self.data)
        with patch('urllib.request.urlopen',side_effect=AssertionError('must not download again')):
            self.manager.prepare('small',self.cancel,lambda _:None)
        self.assertTrue(self.manager.ready('small'))
    def test_interrupted_download_can_resume_with_correct_range(self):
        folder=self.manager.root/'small';folder.mkdir();(folder/'model.bin.part').write_bytes(self.data[:5])
        import io
        response=io.BytesIO(self.data[5:]);response.status=206;response.headers={'Content-Range':f'bytes 5-{len(self.data)-1}/{len(self.data)}'}
        with patch('urllib.request.urlopen',return_value=response) as download:
            self.manager.prepare('small',self.cancel,lambda _:None)
        self.assertEqual(download.call_args.args[0].headers['Range'],'bytes=5-')
        self.assertTrue(self.manager.ready('small'))
    def test_wrong_range_is_rejected(self):
        folder=self.manager.root/'small';folder.mkdir();(folder/'model.bin.part').write_bytes(self.data[:5])
        import io
        def wrong(*args, **kwargs):
            response=io.BytesIO(self.data);response.status=206;response.headers={'Content-Range':'bytes 0-1/2'}
            return response
        with patch('urllib.request.urlopen',side_effect=wrong),self.assertRaisesRegex(RuntimeError,'分段'):
            self.manager.prepare('small',self.cancel,lambda _:None)
        self.assertFalse(self.manager.ready('small'))

    def test_auto_falls_back_to_mirror_with_same_hash(self):
        import io, urllib.error
        self.catalog['small']['files'][0]['url']='https://huggingface.co/test/resolve/pinned/model.bin'
        urls=[]; events=[]
        def download(request, **kwargs):
            urls.append(request.full_url)
            if 'huggingface.co' in request.full_url: raise urllib.error.URLError('offline')
            response=io.BytesIO(self.data);response.status=200;response.headers={};return response
        with patch('urllib.request.urlopen',side_effect=download):
            self.manager.prepare('small',self.cancel,lambda _:None,telemetry=events.append)
        self.assertEqual(len(urls),3);self.assertIn('hf-mirror.com',urls[-1]);self.assertTrue(self.manager.ready('small'))
        self.assertTrue(any(e['phase']=='verifying' and e['source']=='mirror' for e in events))

    def test_wrong_mirror_hash_is_never_ready(self):
        import io
        self.catalog['small']['files'][0]['url']='https://huggingface.co/test/model.bin'
        def download(*args,**kwargs):
            response=io.BytesIO(b'x'*len(self.data));response.status=200;response.headers={};return response
        with patch('urllib.request.urlopen',side_effect=download) as request,self.assertRaisesRegex(RuntimeError,'校验'):
            self.manager.prepare('small',self.cancel,lambda _:None,source='mirror')
        self.assertEqual(request.call_count,2);self.assertFalse(self.manager.ready('small'))

    def test_incomplete_import_does_not_download(self):
        (self.source/'model.bin').unlink()
        with patch('urllib.request.urlopen') as request,self.assertRaisesRegex(RuntimeError,'不完整'):
            self.manager.prepare('small',self.cancel,lambda _:None,self.source)
        request.assert_not_called()

    def test_interrupted_transfer_resumes_on_retry(self):
        import io
        class Interrupted(io.BytesIO):
            def read(self,*args):
                if self.tell(): raise OSError('connection lost')
                return super().read(5)
        calls=[]
        def download(request,**kwargs):
            calls.append(request)
            if len(calls)==1:
                response=Interrupted(self.data);response.status=200;response.headers={}
            else:
                response=io.BytesIO(self.data[5:]);response.status=206;response.headers={'Content-Range':f'bytes 5-{len(self.data)-1}/{len(self.data)}'}
            return response
        with patch('urllib.request.urlopen',side_effect=download):self.manager.prepare('small',self.cancel,lambda _:None)
        self.assertEqual(calls[1].headers['Range'],'bytes=5-');self.assertTrue(self.manager.ready('small'))

if __name__=='__main__':unittest.main()
