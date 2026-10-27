# SureLive Local Assistant

> Edge 商店版请使用新重建的 `0.1.1-basic.preview.2`，发布状态见[新版本](https://github.com/seagull226/surelive-local-assistant/releases/tag/v0.1.1-basic.preview.2)。旧 `preview.1` 和完整包仅保留原固定测试 ID 兼容性；下方旧下载链接不适用于商店 ID。SenseVoice 模型包不受影响。

> For the Edge store extension, use rebuilt `0.1.1-basic.preview.2`; check its [release status](https://github.com/seagull226/surelive-local-assistant/releases/tag/v0.1.1-basic.preview.2). The old preview.1 and full installers support the original test ID only. The SenseVoice model bundle is unaffected.

[中文](README.md) | [English](README.en.md)

Local speech-to-text resources and Windows companion for SureLive Local Cinema (`v0.1.7+`). Two local subtitle generation modes are supported:

### Option 1: Browser-based SenseVoice (Recommended · No EXE installer required)

- **Model Bundle Download**: **[sensevoice-small-fp32-cinema.zip (827 MB)](https://github.com/seagull226/surelive-local-assistant/releases/download/v0.1.1-basic.preview.1/sensevoice-small-fp32-cinema.zip)**
  - SHA-256: `1190dd40123873afab75c853ffbc5edf09c15454ca0b94bac16c262d0861759f`
  - Contains the verified `model.onnx` (937,617,178 bytes) and `tokens.txt` (315,894 bytes) for Chinese, English, Cantonese, Japanese, and Korean recognition in the browser (requires WebGPU).
  - **How to use**: Download and extract the ZIP archive, open SureLive Local Cinema, choose **"SenseVoice · 浏览器内识别"**, click **"导入模型文件夹" (Import model folder)**, and select the extracted `sensevoice-small-fp32` folder.

### Option 2: Whisper Windows Native Companion (99/100 languages · GPU/CPU)

Whisper transcribes audio on your PC; the cinema connects through the Native Messaging handshake and loopback HTTP interface.

**Windows x64: [Basic installer, 87.9 MB](https://github.com/seagull226/surelive-local-assistant/releases/tag/v0.1.1-basic.preview.2) · [Retained full installer, 1.21 GB](https://github.com/seagull226/surelive-local-assistant/releases/tag/v0.1.0-preview.1).** Start with the basic installer for compatible-library reuse and on-demand NVIDIA components. The full installer includes acceleration libraries up front. Neither includes Whisper models or requires a separate Python installation. See [Choose an installer / 两个包怎么选](docs/DOWNLOADS.md).

Read the [basic setup guide](docs/BASIC-INSTALL.en.md) / [中文使用说明](docs/BASIC-INSTALL.md) first. New preview.2 is compatible with SureLive `v0.1.7+` Local Cinema (extension IDs `pigcndembijihpdlkdpmopjddomgjogc` and Microsoft Edge extension ID `daefoeomgbpapjnpajciiikmhcadbdop`). The installer is unsigned; see the [basic release notes](docs/RELEASE-0.1.1-basic.preview.2.md).

## Features

- Multilingual Whisper Small and Large-v3: 99 and 100 language codes respectively; automatic language detection or an explicit source language.
- NVIDIA CUDA acceleration when available, automatic CPU selection otherwise, and explicit CPU selection. Recognized CUDA/memory failures can trigger a CPU retry.
- Pinned model revisions, SHA-256 verification, resumable downloads, complete-folder import, and configurable model storage. Official downloads and a clearly labeled third-party mirror are supported.
- User-initiated connection without a pairing code or Windows startup registration. Chinese/English management UI, system tray, progress, and exit confirmation.
- Five-minute recognition windows with one second of context on each side. Cancellation and disconnect cleanup; no fixed 90-minute limit.

The desktop window manages models and tasks; the cinema handles playback and subtitles. Browser-based SenseVoice runs inside the extension via WebGPU and does not require this native helper. Language availability is not a promise of equal recognition accuracy.

## Development

Windows x64 and Python 3.12 (validated with 3.12.10):

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install --require-hashes -r requirements-windows.lock
.\.venv\Scripts\python.exe tools\run_tests.py
```

Follow the [build guide (Chinese)](docs/BUILD.md) to prepare FFmpeg and optional GPU libraries. Copy `build.example.json` to the ignored `build.local.json`, then specify verified input files and their SHA-256 values:

```powershell
.\.venv\Scripts\python.exe tools\build_windows.py --config build.local.json --output artifacts\local-preview
```

Building does not require model weights. It writes a new directory within this project without installing the app or changing the registry. See the [protocol reference (Chinese)](docs/PROTOCOL.md), [validation record (Chinese)](docs/STATUS.md), and [bilingual release review](docs/RELEASE-READINESS.md).

## Repository layout

| Path | Contents |
| --- | --- |
| `src/surelive_local_asr/` | Host, Whisper worker, desktop UI, model/session management, subtitle stitching |
| `resources/models.json` | Pinned revisions, languages, sizes, and hashes; no model weights |
| `tools/` | Independent build, unit tests, and native-protocol smoke check |
| `installer/windows.nsi` | Per-user installation/uninstallation |
| `integration/` | Extension integration reference |

Local configuration, runtime binaries, models, media, subtitles, and build outputs are excluded from Git. Application source retains the [MIT license](LICENSE); dependencies retain their own terms. See [third-party information](THIRD-PARTY-NOTICES.txt).
