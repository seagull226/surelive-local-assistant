# Basic installer: setup and usage

Version `0.1.1-basic.preview.1` is available as a [public preview](https://github.com/seagull226/surelive-local-assistant/releases/tag/v0.1.1-basic.preview.1). The original full installer remains available; see [Downloads & Choose an installer](DOWNLOADS.md) (which also includes the browser-based SenseVoice model bundle). Compatible with SureLive `v0.1.7+` Local Cinema. Model management, the tray and the connection protocol are unchanged. Whisper models are not bundled.

Download `SureLive-Local-Assistant-0.1.1-basic.preview.1-win-x64.exe`, verify it against the release's `SHA256SUMS.txt`, and install for the current user. Open the helper, download or import Small / Large-v3, then select **Whisper · local helper** in Local Cinema. No pairing code is needed. The installer is the exact validated file; its embedded isolated-preview notes are a test-stage snapshot. This guide and the release attachments provide current instructions.

The helper checks the GPU and reusable libraries. Without an available NVIDIA GPU, it uses CPU and downloads no GPU components. Compatible CUDA 12/cuDNN 9 libraries are reused after a separate process successfully runs cuBLAS operations and a cuDNN convolution. Discovery uses PATH, CUDA_PATH/CUDNN_PATH and standard NVIDIA installation directories; it does not scan private environments belonging to other applications or modify system libraries.

When components are missing or incompatible, the first automatic recognition job, or **Prepare / retry NVIDIA acceleration**, downloads about 1.11 GB from NVIDIA. Allow about 3 GB of temporary free disk space. Pinned archive and extracted-file SHA-256 checks and a runtime check must pass before activation. The final components occupy about 1.68 GB; downloaded archives are removed after success. Progress, cancellation and resume are supported. On failure, CPU recognition remains available. The helper does not install drivers or require the full CUDA toolkit.

Select **Use CPU only; do not download acceleration components** to skip downloads. Cancel active work before changing this option, then start recognition again. Failed preparation can be retried explicitly; it does not retry endlessly in the background. Prepared components and models are reused on later runs.

Components are cached under `%LOCALAPPDATA%/SureLiveASRPreview/gpu-runtime`, separately from media and model folders. No system PATH changes are made. Uninstallation retains model and GPU caches. AMD/Intel graphics currently use CPU recognition. The installer is unsigned; Windows or organizational policy may warn or block it.

See the [validation record](ON-DEMAND-GPU.md).
