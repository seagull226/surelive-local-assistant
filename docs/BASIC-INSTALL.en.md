# Basic installer: isolated preview

Version `0.1.1-basic.preview.1` is under isolated validation and does not replace the published full installer. It requires the matching preview cinema. Model management, the tray and the connection protocol are unchanged. Whisper models are not bundled.

The helper checks the GPU and reusable libraries. Without an available NVIDIA GPU, it uses CPU and downloads no GPU components. Compatible CUDA 12/cuDNN 9 libraries are reused after a separate process successfully runs cuBLAS operations and a cuDNN convolution. Discovery uses PATH, CUDA_PATH/CUDNN_PATH and standard NVIDIA installation directories; it does not scan private environments belonging to other applications or modify system libraries.

When components are missing or incompatible, the first automatic recognition job, or **Prepare / retry NVIDIA acceleration**, downloads about 1.11 GB from NVIDIA. Allow about 3 GB of temporary free disk space. Pinned archive and extracted-file SHA-256 checks and a runtime check must pass before activation. The final components occupy about 1.68 GB; downloaded archives are removed after success. Progress, cancellation and resume are supported. On failure, CPU recognition remains available. The helper does not install drivers or require the full CUDA toolkit.

Select **Use CPU only; do not download acceleration components** to skip downloads. Cancel active work before changing this option, then start recognition again. Failed preparation can be retried explicitly; it does not retry endlessly in the background. Prepared components and models are reused on later runs.

Components are cached under `%LOCALAPPDATA%/SureLiveASRPreview/gpu-runtime`, separately from media and model folders. No system PATH changes are made. Uninstallation retains model and GPU caches. AMD/Intel graphics currently use CPU recognition. The installer is unsigned; Windows or organizational policy may warn or block it.

The published full installer, production extension test package and store release are unchanged. See the [validation record](ON-DEMAND-GPU.md).
