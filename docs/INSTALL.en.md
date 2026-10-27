# Installation and connection

[中文](INSTALL.md) | [English](INSTALL.en.md)

**Windows x64 installer: `0.1.0-preview.1`.** Download the `.exe` from [Releases](https://github.com/seagull226/surelive-local-assistant/releases/tag/v0.1.0-preview.1) and check that release's compatibility and validation notes. The matching preview cinema is required; this update cannot add an entry to an arbitrary older extension. GitHub's automatically generated “Source code” ZIP is source code, not an installer.

## Before you start

- Windows x64. Results from the current development PC do not establish support across all Windows versions. No macOS, Linux, or Windows ARM installer is provided.
- The matching preview cinema is required. Installing this helper does not enable ASR in a production extension that does not expose it. Playback, subtitle display, and translation remain in the cinema; the helper is not a standalone video player.
- A dedicated GPU is optional. NVIDIA CUDA is the current GPU path; AMD/Intel graphics use CPU processing. A candidate with the complete GPU runtime does not require a separate CUDA toolkit, but still needs a compatible graphics driver.
- Model weights are not bundled. Allow additional space for models and temporary decoded audio. Long videos consume more resources; the absence of a 90-minute cap does not mean unlimited capacity.

## Install and prepare your first model

1. Download `SureLive-Local-Assistant-0.1.0-preview.1-win-x64.exe` from this repository's Releases. Compare its hash with `SHA256SUMS.txt` from the same release. Historical private-preview EXEs are not this version.
2. Install for the current Windows user. The current script does not request administrator privileges; it registers the Chrome/Edge native host for that user. The installer currently uses Chinese; the assistant window supports Chinese and English.
3. Open the local subtitle helper. Select Small or Large-v3, then **Download / resume**, or choose **Use existing model…** to import a complete matching model folder.
4. Open a local video in the matching cinema, choose **Whisper · local helper**, and click **Connect helper** or **Generate subtitles**. No pairing code is required.
5. Select the video's actual spoken language, or automatic detection. The learning-language setting does not force the video's source language. Translation uses the extension's **My native language** setting. Review generated subtitles for mistakes.

To check your download:

```powershell
Get-FileHash -Algorithm SHA256 -LiteralPath .\SureLive-Local-Assistant-0.1.0-preview.1-win-x64.exe
```

Current builds are unsigned. Windows may report an unknown publisher or block execution; organizational policies can prevent continuation. A hash check does not replace a digital signature. Do not disable security protections to install the app. Signing does not guarantee the absence of warnings; see [Microsoft's guidance](https://learn.microsoft.com/en-us/windows/apps/package-and-deploy/smartscreen-reputation).

## Models, downloads, and languages

| Model | Total pinned file size, excluding caches/temp files | Languages | Selection guide |
| --- | --- | --- | --- |
| Multilingual Small | About 486 MB (464 MiB) | 99 | Smaller download; a starting point for CPU or quick trials |
| Large-v3 | About 3.09 GB (2.88 GiB) | 100 | Higher resource use; compare results when a GPU is available |

Both support Chinese, English, Japanese, Korean, French, German, Spanish, and more. Small is not the English-only `small.en`. Language counts do not imply equal accuracy. Exact language codes and required files are in the [model catalog](../resources/models.json).

Choose the Hugging Face official source, the third-party HF-Mirror service, or automatic mode (official first, mirror after failure). All sources are verified against pinned SHA-256 hashes. Availability depends on your network; the mirror is not an official host and receives neither account credentials nor your media from this helper. Interrupted downloads can resume. You can also obtain the matching complete folder on another computer and import it locally.

Import requires `model.bin` plus the selected model's configuration, tokenizer, and vocabulary files. A `.pt` file, ONNX model, or lone `model.bin` is insufficient. Import verifies and copies files into the configured directory. Changing **Model storage** does not move existing models automatically.

## Connection and identity

| Setting | Current value |
| --- | --- |
| Native Host | `com.surelive.asr.preview` |
| Extension IDs | `pigcndembijihpdlkdpmopjddomgjogc` (fixed key / local), `daefoeomgbpapjnpajciiikmhcadbdop` (Microsoft Edge Add-ons), plus optional `extraExtensionIds` in `settings.json` |
| Protocol | `1` |
| User data | `%LOCALAPPDATA%/SureLiveASRPreview` |

Other extension IDs cannot connect. A future store integration must coordinate the extension ID, native manifest, and HTTP Origin checks. Repository renaming does not change this identity.

The cinema starts the helper after an explicit connect/prepare/generate action. Opening the cinema or switching engines alone does not start it. Native Messaging supplies a per-session credential for local HTTP; no pairing code or permanently public port is required. Browser-based SenseVoice is separate and primarily supports Chinese, English, Cantonese, Japanese, and Korean; its model import/cache belongs to the extension.

## Privacy, tray, and uninstallation

Audio recognition and generated subtitles stay on the PC. Preparing models contacts the selected download source; translation may use the extension's configured online services. The entire extension is not necessarily offline.

Keep the cinema connected during recognition. Closing the management window hides it in the system tray. Open it again or quit from the tray; quitting with active tasks prompts and stops the related work. There is no Windows startup registration.

Uninstall through Windows installed apps. Models and additional user files are preserved; remove them separately only after checking the actual model directory. This version retains the preview installation identity, so avoid overwriting an installation during recognition. See the release notes for the exact installation/uninstallation test scope.

## Troubleshooting

| Symptom | Check |
| --- | --- |
| No Whisper entry or connection failure | Matching preview cinema, extension ID, same Windows user, installation path, and system policy |
| GPU unavailable | Driver and runtime compatibility; CPU remains available |
| Download failure | Selected source, network, resume, or import a complete matching folder |
| Long-video failure | Temporary disk space, audio track, and system resources |

Do not disable firewalls, antivirus, or enterprise policy to make a test pass.
