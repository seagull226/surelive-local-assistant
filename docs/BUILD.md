# 独立构建

无需检出 SureLive 插件。当前目标为 Windows x64、Python 3.12，锁文件只针对该组合。

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

```powershell
Get-FileHash -Algorithm SHA256 -LiteralPath .\third-party\ffmpeg\ffmpeg.exe
```

构建前核对文件存在和 SHA-256；不要仅更新错误文件的哈希来代替来源核查。`notices` 按组件复制，收集文本不代表完整源码交付或许可组合已完成。

## 构建

```powershell
.\.venv\Scripts\python.exe tools\build_windows.py --config build.local.json --output artifacts\preview-001
```

输出必须为本仓库 `artifacts` 下的新目录，避免覆盖试用副本。`payload` 内包含 `SureLive-NativeHost.exe`、桌面入口 `SureLive-ASR-Helper.exe`、`runtime/SureLive-Inference.exe`、FFmpeg、运行库和模型清单。`build-receipt.json` 记录源码和产物哈希。

模型清单直接来自 `resources/models.json`；构建不读取开发者模型缓存，不包含权重。需要安装器时，在配置 NSIS 后使用新目录并加 `--installer`：

```powershell
.\.venv\Scripts\python.exe tools\build_windows.py --config build.local.json --output artifacts\installer-001 --installer
```

该步骤不自动安装、签名或上传。安装器保留隔离连接身份和界面；生成 EXE 不等于可以公开分发，见 [当前状态](STATUS.md)。

## 修改与验证

需要修改 pystray 时，可编辑独立环境 `Lib/site-packages/pystray` 中的 Python 源码，再使用新的输出目录构建 Native Host。助手不通过自身签名检查拒绝兼容库替换；Windows 安全策略仍适用。

`tools/run_tests.py` 无需下载模型，覆盖模型准备、窗口/时间轴和构建输入保护。冻结程序可通过 `tools/smoke_native.py` 验证；它将状态写到本仓库临时目录，不写浏览器注册表。实际识别另需合法音频与匹配模型。

```powershell
.\.venv\Scripts\python.exe tools\smoke_native.py --payload artifacts\preview-001\payload --output artifacts\smoke-001
```

加入 `--audio <音频文件> --model-source <匹配的完整模型目录>` 可验证识别；默认 Small/英语，其他配置用 `--model` 和 `--language`。`--hide-cuda` 模拟无可用 CUDA 设备，`--device cpu` 则明确选择 CPU。每次使用新的输出目录；模型导入副本、临时配置和结果均留在被 Git 忽略的 `artifacts/` 中。
