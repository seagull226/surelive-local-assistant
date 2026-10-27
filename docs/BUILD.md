# 独立构建

无需检出 SureLive 插件。当前目标为 Windows x64、Python 3.12，锁文件只针对该组合。`0.1.0-preview.1` 保持助手源码和连接方式，打包时对 faster-whisper 的 PyAV 导入作延迟加载补丁；助手先通过独立 FFmpeg 解码音轨，再给识别模型传入 NumPy PCM，因此不分发未使用的 PyAV 视频库。

## 准备环境

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install --require-hashes -r requirements-windows.lock
.\.venv\Scripts\python.exe tools\run_tests.py
```

30 个直接和传递构建/运行依赖固定版本及 wheel SHA-256。不要从其他程序复制 `ctranslate2.dll` 覆盖 wheel。离线可先 `pip download --require-hashes -r requirements-windows.lock -d third-party/wheels`，安装时加 `--no-index --find-links third-party/wheels`。

## 配置原生输入

复制 `build.example.json` 为 Git 忽略的 `build.local.json`。路径可以相对仓库，也可以是本机绝对路径。

- `ffmpeg`：兼容的 FFmpeg EXE、SHA-256 和说明文件路径。助手读取第一条音轨并转换为 16 kHz 单声道 Float32 PCM。
- `gpu`：DLL 数组，每项使用 `path`、`sha256` 和可选 `notices`，格式同 `ffmpeg`。空数组生成 CPU 路径。完整 GPU 构建需要与 CTranslate2 兼容的 CUDA/cuDNN。本次隔离验证使用 cudart 12.1.105、cuBLAS 12.1.3.1、cuDNN 9.1.0.70 的官方归档文件。
- `makensis`：仅 `--installer` 需要，指向 NSIS `makensis.exe`。
- `supplementalNotices`：Release 对应源码材料包中的 `notices/`，解压为 `third-party/release-notices`；补充 wheel 没有包含的许可和本机组件条款。不能用旧自动收集目录代替完整随包材料。

发布候选的 FFmpeg 使用对应材料包中的 `ffmpeg-7.1-b08d7969c5.tar.gz`，不使用 Gyan full 或 PyAV 的二进制。解压后，在 MSYS2 UCRT64 安装 `mingw-w64-ucrt-x86_64-gcc make diffutils nasm`，执行 `bash tools/build_ffmpeg.sh <源目录> <新构建目录>`。保留内置解码器和本地文件输入，仅输出助手使用的 Float32 PCM；禁用外部自动探测、GPL/nonfree、网络和视频编码。对应源码、配置及工具版本随源码材料包提供。重新计算生成 EXE 的 SHA-256 填入本机配置。

```powershell
Get-FileHash -Algorithm SHA256 -LiteralPath .\third-party\ffmpeg\ffmpeg.exe
```

构建前核对文件存在和 SHA-256；不要仅更新错误文件的哈希来代替来源核查。`notices` 按组件复制，收集文本不代表完整源码交付或许可组合已完成。

## 构建

基础小包分支：把本机配置的 `gpu` 设为 `[]`，其余 FFmpeg、随包材料和 NSIS 配置沿用。构建仍保留 CPU 所需运行库和固定 `resources/gpu-runtime.json`，不带大型 CUDA/cuDNN 加速库。首次使用按需从 NVIDIA 官方归档准备，详见 [基础包说明](BASIC-INSTALL.md)。完整包配置及已发布资产保留，不覆盖旧输出目录。本轮构建版本为 `0.1.1-basic.preview.1`，验证后的同一安装器用于[公开预览](RELEASE-0.1.1-basic.preview.1.md)。构建回执中的未发布状态保留为构建阶段快照。

```powershell
.\.venv\Scripts\python.exe tools\build_windows.py --config build.local.json --output artifacts\preview-001
```

输出必须为本仓库 `artifacts` 下的新目录，避免覆盖试用副本。`payload` 内包含 `SureLive-NativeHost.exe`、桌面入口 `SureLive-ASR-Helper.exe`、`runtime/SureLive-Inference.exe`、FFmpeg、运行库和模型清单。`build-receipt.json` 记录源码和产物哈希。

模型清单直接来自 `resources/models.json`；构建不读取开发者模型缓存，不包含权重。需要安装器时，在配置 NSIS 后使用新目录并加 `--installer`：

```powershell
.\.venv\Scripts\python.exe tools\build_windows.py --config build.local.json --output artifacts\installer-001 --installer
```

该步骤不自动安装、签名或上传。安装器保留隔离连接身份和界面；生成 EXE 不等于可以公开分发，见 [当前状态](STATUS.md)。

构建会在输出目录复制 faster-whisper 1.2.1，并只将 `audio.py` 顶层 PyAV 导入延迟至 `decode_audio()`。推理模块始终传入 NumPy PCM，转写算法不变；PyInstaller 显式排除 `av`。已修改源码及构建脚本随包保留，原虚拟环境不被修改。开发锁文件保留上游声明的 PyAV 依赖，但它不进入安装包。不要直接从原 wheel 随意删 DLL。

## 修改与验证

需要修改 pystray 时，可编辑独立环境 `Lib/site-packages/pystray` 中的 Python 源码，再使用新的输出目录构建 Native Host。助手不通过自身签名检查拒绝兼容库替换；Windows 安全策略仍适用。

`tools/run_tests.py` 无需下载模型，覆盖模型准备、窗口/时间轴和构建输入保护。冻结程序可通过 `tools/smoke_native.py` 验证；它将状态写到本仓库临时目录，不写浏览器注册表。实际识别另需合法音频与匹配模型。

```powershell
.\.venv\Scripts\python.exe tools\smoke_native.py --payload artifacts\preview-001\payload --output artifacts\smoke-001
```

加入 `--audio <音频文件> --model-source <匹配的完整模型目录>` 可验证识别；默认 Small/英语，其他配置用 `--model` 和 `--language`。`--hide-cuda` 模拟无可用 CUDA 设备，`--device cpu` 则明确选择 CPU。每次使用新的输出目录；模型导入副本、临时配置和结果均留在被 Git 忽略的 `artifacts/` 中。
