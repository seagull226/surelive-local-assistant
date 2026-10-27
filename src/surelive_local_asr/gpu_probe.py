"""Run only in a disposable worker: validate actual CUDA/cuBLAS/cuDNN operations."""
import ctypes as C
import os
from pathlib import Path

_handles = []


def function(lib, name, args, result=C.c_int):
    fn = getattr(lib, name); fn.argtypes = args; fn.restype = result
    return fn


def check(code):
    if code: raise RuntimeError('GPU operation returned ' + str(code))


def driver_devices():
    if os.environ.get('CUDA_VISIBLE_DEVICES') in ('', '-1'): return 0
    try:
        driver = C.WinDLL(str(Path(os.environ['SystemRoot']) / 'System32/nvcuda.dll'))
        check(function(driver, 'cuInit', [C.c_uint])(0))
        count = C.c_int(); check(function(driver, 'cuDeviceGetCount', [C.POINTER(C.c_int)])(C.byref(count)))
        return count.value
    except (OSError, RuntimeError, KeyError): return 0


def load_runtime(paths):
    folders = [Path(p).resolve() for p in paths]
    for folder in folders: _handles.append(os.add_dll_directory(str(folder)))
    os.environ['PATH'] = os.pathsep.join(map(str, folders)) + os.pathsep + os.environ.get('PATH', '')
    def load(name):
        path = next((p / name for p in folders if (p / name).is_file()), None)
        if path is None: raise RuntimeError('Missing ' + name)
        dll = C.WinDLL(str(path)); _handles.append(dll); return dll
    runtime = load('cudart64_12.dll')
    load('cublasLt64_12.dll'); blas = load('cublas64_12.dll'); dnn = load('cudnn64_9.dll')
    return runtime, blas, dnn


def validate(paths):
    count = driver_devices()
    if not count: return {'preferred':'cpu', 'cudaDevices':0, 'cudaTypes':[]}
    runtime, blas, dnn = load_runtime(paths)
    version = C.c_int(); check(function(runtime, 'cudaRuntimeGetVersion', [C.POINTER(C.c_int)])(C.byref(version)))
    dnn_version = function(dnn, 'cudnnGetVersion', [], C.c_size_t)()
    if not 12000 <= version.value < 13000 or not 90000 <= dnn_version < 100000:
        raise RuntimeError('CUDA 12 / cuDNN 9 required')
    P = C.c_void_p; I = C.c_int; F = C.c_float; ref = C.byref
    allocations = []; descriptors = []; b = P(); h = P()
    malloc = function(runtime, 'cudaMalloc', [C.POINTER(P), C.c_size_t])
    copy = function(runtime, 'cudaMemcpy', [P, P, C.c_size_t, I])
    free = function(runtime, 'cudaFree', [P])
    def allocate(values):
        host = (F * len(values))(*values); device = P()
        check(malloc(ref(device), C.sizeof(host))); allocations.append(device)
        check(copy(device, host, C.sizeof(host), 1)); return device
    def descriptor(create, destroy):
        value = P(); check(function(dnn, create, [C.POINTER(P)])(ref(value)))
        descriptors.append((function(dnn, destroy, [P]), value)); return value
    try:
        check(function(blas, 'cublasCreate_v2', [C.POINTER(P)])(ref(b)))
        a, x, y = allocate([2]), allocate([3]), allocate([0])
        alpha, beta = F(1), F(0)
        gemm = function(blas, 'cublasSgemm_v2', [P,I,I,I,I,I,C.POINTER(F),P,I,P,I,C.POINTER(F),P,I])
        check(gemm(b,0,0,1,1,1,ref(alpha),a,1,x,1,ref(beta),y,1))
        answer = F(); check(copy(ref(answer), y, 4, 2))
        if abs(answer.value - 6) > 1e-5: raise RuntimeError('cuBLAS result mismatch')
        check(function(dnn, 'cudnnCreate', [C.POINTER(P)])(ref(h)))
        tensor = descriptor('cudnnCreateTensorDescriptor', 'cudnnDestroyTensorDescriptor')
        filt = descriptor('cudnnCreateFilterDescriptor', 'cudnnDestroyFilterDescriptor')
        conv = descriptor('cudnnCreateConvolutionDescriptor', 'cudnnDestroyConvolutionDescriptor')
        check(function(dnn, 'cudnnSetTensor4dDescriptor', [P,I,I,I,I,I,I])(tensor,0,0,1,1,2,2))
        check(function(dnn, 'cudnnSetFilter4dDescriptor', [P,I,I,I,I,I,I])(filt,0,0,1,1,1,1))
        check(function(dnn, 'cudnnSetConvolution2dDescriptor', [P,I,I,I,I,I,I,I,I])(conv,0,0,1,1,1,1,1,0))
        inp, kernel, out = allocate([1,2,3,4]), allocate([2]), allocate([0]*4)
        size = C.c_size_t()
        check(function(dnn, 'cudnnGetConvolutionForwardWorkspaceSize', [P,P,P,P,P,I,C.POINTER(C.c_size_t)])(h,tensor,filt,conv,tensor,0,ref(size)))
        workspace = P()
        if size.value: check(malloc(ref(workspace),size.value)); allocations.append(workspace)
        forward = function(dnn, 'cudnnConvolutionForward', [P,P,P,P,P,P,P,I,P,C.c_size_t,P,P,P])
        check(forward(h,ref(alpha),tensor,inp,filt,kernel,conv,0,workspace,size.value,ref(beta),tensor,out))
        answer = (F*4)(); check(copy(answer,out,16,2))
        if any(abs(a-b)>1e-5 for a,b in zip(answer,[2,4,6,8])): raise RuntimeError('cuDNN result mismatch')
        # Import only after choosing one coherent runtime; do not mix in the wheel's cuDNN shim.
        import ctranslate2
        types = sorted(ctranslate2.get_supported_compute_types('cuda'))
        if 'float16' not in types: raise RuntimeError('GPU does not support the selected float16 engine')
        return {'preferred':'cuda','cudaDevices':count,'cudaTypes':types,'cudaRuntime':version.value,
                'cudnnRuntime':dnn_version,'runtimeCheck':'cuBLAS GEMM + cuDNN convolution'}
    finally:
        for destroy, value in reversed(descriptors): destroy(value)
        if h: function(dnn, 'cudnnDestroy', [P])(h)
        if b: function(blas, 'cublasDestroy_v2', [P])(b)
        for value in allocations: free(value)
