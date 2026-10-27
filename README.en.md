# SureLive Local Assistant

[中文](README.md) | [English](README.en.md)

A Windows companion for SureLive's local cinema. Whisper transcribes audio on your PC; the cinema connects through the existing Native Messaging handshake and loopback HTTP interface.

**Windows x64 preview installer: [Download 0.1.0-preview.1](https://github.com/seagull226/surelive-local-assistant/releases/tag/v0.1.0-preview.1).** Download the `.exe`; no separate Python installation is required. The existing interface, model management, and connection protocol are preserved. Model weights are downloaded or imported separately.

Read the [setup guide](docs/INSTALL.en.md) / [中文使用说明](docs/INSTALL.md) first. This helper currently requires the matching preview cinema. Installing it does not add Whisper to an existing production extension. The installer is unsigned; see the [release notes and validation scope](docs/RELEASE-0.1.0-preview.1.md).

## Features

- Multilingual Whisper Small and Large-v3: 99 and 100 language codes respectively; automatic language detection or an explicit source language.
- NVIDIA CUDA acceleration when available, automatic CPU selection otherwise, and explicit CPU selection. Recognized CUDA/memory failures can trigger a CPU retry.
- Pinned model revisions, SHA-256 verification, resumable downloads, complete-folder import, and configurable model storage. Official downloads and a clearly labeled third-party mirror are supported.
- User-initiated connection without a pairing code or Windows startup registration. Chinese/English management UI, system tray, progress, and exit confirmation.
- Five-minute recognition windows with one second of context on each side. Cancellation and disconnect cleanup; no fixed 90-minute limit.

The desktop window manages models and tasks; the cinema handles playback and subtitles. Browser-based SenseVoice belongs to the extension and does not run in this native helper. Language availability is not a promise of equal recognition accuracy.

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
| `installer/windows.nsi` | Per-user installation/uninstallation using the preview identity |
| `integration/` | Extension integration reference |

Local configuration, runtime binaries, models, media, subtitles, and build outputs are excluded from Git. Application source retains the [MIT license](LICENSE); dependencies retain their own terms. See [third-party information](THIRD-PARTY-NOTICES.txt).
