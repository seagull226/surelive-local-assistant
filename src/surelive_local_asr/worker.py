"""Frozen inference subprocess; no dependency on the user's Python or PATH."""
import json, os, sys, time
from pathlib import Path

BASE = Path(sys.executable).parent if getattr(sys, 'frozen', False) else Path(__file__).parent
handles = []
if (BASE / 'gpu').is_dir():
    handles.append(os.add_dll_directory(str(BASE / 'gpu')))
    os.environ['PATH'] = str(BASE / 'gpu') + os.pathsep + os.environ.get('PATH', '')
os.environ['HF_HUB_OFFLINE'] = '1'
import ctranslate2
from chunking import RATE, CHUNK_SECONDS, windows, owned_words, append_chunk

def hardware():
    try:
        count = ctranslate2.get_cuda_device_count()
        types = sorted(ctranslate2.get_supported_compute_types('cuda')) if count else []
        return {'cudaDevices': count, 'cudaTypes': types, 'preferred': 'cuda' if 'float16' in types else 'cpu'}
    except Exception:
        return {'cudaDevices': 0, 'cudaTypes': [], 'preferred': 'cpu'}

if __name__ == '__main__':
    if sys.argv[1] == '--probe':
        print(json.dumps(hardware()), flush=True)
    else:
        import numpy as np
        from faster_whisper import WhisperModel, BatchedInferencePipeline
        spec = json.loads(Path(sys.argv[1]).read_text(encoding='utf-8'))
        sample_count = Path(spec['pcm']).stat().st_size // 4
        if not sample_count: raise RuntimeError('没有有效音轨 / No audio samples')
        duration = sample_count / RATE
        started = time.perf_counter()
        device = 'cpu' if spec.get('device') == 'cpu' else hardware()['preferred']
        fallback = False
        def recognize(device):
            print('loading', flush=True)
            model = WhisperModel(spec['modelPath'], device=device, compute_type='float16' if device == 'cuda' else 'int8',
                                 cpu_threads=min(8, os.cpu_count() or 4), local_files_only=True)
            pipeline = BatchedInferencePipeline(model=model)
            rows, detected = [], None if spec['language'] == 'auto' else spec['language']
            total = (sample_count + CHUNK_SECONDS * RATE - 1) // (CHUNK_SECONDS * RATE)
            with Path(spec['pcm']).open('rb') as source:
                for index, (begin, end, read_begin, read_end) in enumerate(windows(sample_count)):
                    print('SURELIVE_PROGRESS '+json.dumps({'stage':'recognizing', 'percent':int(begin/sample_count*100),
                          'chunk':index+1, 'chunks':total, 'processedSec':begin/RATE, 'totalSec':duration}), flush=True)
                    source.seek(read_begin * 4)
                    pcm = np.frombuffer(source.read((read_end-read_begin)*4), dtype='<f4')
                    if np.any(pcm):
                        segments, info = pipeline.transcribe(
                            pcm, language=detected,
                            batch_size=(4 if spec['model'] == 'large-v3' else 8) if device == 'cuda' else 1,
                            beam_size=5, temperature=0, word_timestamps=True, vad_filter=True, condition_on_previous_text=False)
                        words = [w for segment in segments for w in segment.words or []]
                        if words and detected is None: detected = info.language
                        append_chunk(rows, owned_words(words, read_begin/RATE, begin/RATE, end/RATE, duration))
                    del pcm
            return rows, detected or spec['language']
        try:
            rows, detected = recognize(device)
        except RuntimeError as error:
            if device != 'cuda' or not any(word in str(error).lower() for word in ('cuda', 'cudnn', 'cublas', 'out of memory', 'gpu')): raise
            # DLL/driver/VRAM failures must not make CPU-only users configure CUDA.
            import gc
            gc.collect()
            device, fallback = 'cpu', True
            print('cpu-fallback', flush=True)
            rows, detected = recognize(device)
        result = {'durationSec': duration, 'segments': rows, 'language': detected,
                  'requestedLanguage': spec['language'], 'engine': 'whisper-' + spec['model'],
                  'device': device, 'cpuFallback': fallback, 'chunkSeconds':CHUNK_SECONDS,
                  'inferenceMs': (time.perf_counter() - started) * 1000}
        Path(spec['output']).write_text(json.dumps(result, ensure_ascii=False), encoding='utf-8')
