# 0.1.0-preview.1 · Windows x64

[下载安装包 / Download installer](https://github.com/seagull226/surelive-local-assistant/releases/tag/v0.1.0-preview.1)

## 中文

下载 `SureLive-Local-Assistant-0.1.0-preview.1-win-x64.exe`（1,207,426,509 字节，约 1.21 GB），按当前用户安装。包含 Python、音轨解码器及 CPU/NVIDIA 推理运行库，不需要另外安装 Python 或 CUDA 工具包；NVIDIA 加速仍需要兼容显卡驱动。

**模型不在安装包内。** 首次打开助手，下载或导入 Small（约 486 MB）或 Large-v3（约 3.09 GB），再从配套影院选择 Whisper。安装包未签名，Windows 或企业策略可能提示或阻止运行。详细步骤：[中文使用说明](INSTALL.md)。

**需要配套隔离影院，扩展 ID 为 `pigcndembijihpdlkdpmopjddomgjogc`。** 从原有隔离试用渠道取得影院；本仓库不分发插件。没有该影院的用户可安装并准备模型，但不能仅用此助手播放视频或生成影院字幕。正式插件尚未开放的入口不会自动出现，因此本版标记为预览版。

### 验证范围

- Windows 10 Pro x64（19045）、NVIDIA RTX 5060 Ti，在独立安装目录及隔离测试配置中验证；不是全新 Windows 虚拟机。
- 18 项单元测试通过；最终程序目录的 1,706 个文件、安装器和源码附件全部核对哈希。
- 中文路径全新安装及 Chrome/Edge 注册、同版本重装、卸载通过；重装保留用户文件，卸载保留用户文件和外部模型缓存。测试结束已恢复原有浏览器注册和快捷方式。
- Small 空目录首次下载及校验通过（本次约 36.7 秒）；Small/Large-v3 的官方与镜像配置文件均核对固定哈希。未重新完整下载 Large-v3。
- 同一段 45 秒英文音频：安装后的 Small GPU 约 3.54 秒、无可见 CUDA 设备时自动选 CPU 约 7.79 秒；最终程序的 Large-v3 GPU 约 13.95 秒。均为推理时间，不含启动、上传、解码或模型准备，不代表准确率或长片整体速度。
- WAV、AAC、MP3、AC3、EAC3、FLAC、Opus 和课程 MP4 解码对照通过；Opus 仅有浮点舍入级差异。
- 取消任务、断开退出、未授权来源和缺少令牌拒绝通过。
- 安装后的 Edge 151 与 Chrome for Testing 连接测试通过（测试扩展使用相同身份和本仓库接入代码，验证握手、健康查询及断开）。普通 Chrome 155 的自动加载测试扩展被拦截，该浏览器的端到端测试未完成；不把它计为通过。

本版未新增全语言准确率、长片压力、推理中途显卡故障或所有 Windows/显卡组合的验收结论。现有七个运行模块、影院 UI 和连接协议不变；SureLive 正式测试包未改动。

### 下载文件

- `.exe`：安装器。
- `SHA256SUMS.txt`：下载文件的 SHA-256 校验清单。
- `VALIDATION.json` / `BUILD-MANIFEST.json`：本次验证及构建文件清单。
- `*-sources.zip`：对应的第三方源码、声明和重建材料，普通用户无需下载；GitHub 自带 Source code ZIP 仅为本项目源码。

## English

Download `SureLive-Local-Assistant-0.1.0-preview.1-win-x64.exe` (1,207,426,509 bytes, approximately 1.21 GB) and install for the current Windows user. Python, the audio decoder and CPU/NVIDIA inference runtimes are included. No separate Python or CUDA toolkit installation is required; NVIDIA acceleration still requires a compatible driver.

**Model weights are not bundled.** Download or import Small (about 486 MB) or Large-v3 (about 3.09 GB), then choose Whisper in the matching cinema. The installer is unsigned and Windows or organizational policy may warn or block it. See the [English setup guide](INSTALL.en.md).

**Requires the matching preview cinema**, extension ID `pigcndembijihpdlkdpmopjddomgjogc`, obtained through the existing isolated-preview channel. This repository does not distribute the extension. Without it you can install the helper and prepare models, but the helper cannot play videos or generate cinema subtitles on its own. Installing it does not enable a missing entry in the production extension. This is therefore a pre-release.

### Validation scope

- Windows 10 Pro x64 (19045), RTX 5060 Ti, isolated installation directory and test configuration; not a fresh Windows VM.
- 18 unit tests passed; all 1,706 payload files, the installer and source companion verified by hashes.
- Fresh installation into a Unicode path, Chrome/Edge native-host registration, same-version reinstall and uninstall passed. User files survived reinstall and uninstall; external model caches were retained. Original registrations and the shortcut were restored after testing.
- Fresh Small model download and verification passed (about 36.7 seconds in this run). Official and mirror configuration files for both models matched pinned hashes. A full Large-v3 download was not repeated.
- Same 45-second English sample: installed Small GPU approximately 3.54 seconds, automatic CPU selection with no visible CUDA device approximately 7.79 seconds; final payload Large-v3 GPU approximately 13.95 seconds. These are inference times excluding startup, upload, decoding and model preparation, not accuracy or long-video throughput claims.
- WAV, AAC, MP3, AC3, EAC3, FLAC, Opus and course MP4 decoder comparisons passed; Opus differed only at floating-point rounding scale.
- Active cancellation, disconnect cleanup, rejection of unauthorized origins and missing tokens passed.
- Installed-host connection passed in Edge 151 and Chrome for Testing, using a fixture with the matching extension identity and this repository's integration code to test handshake, health query and disconnect. Retail Chrome 155 blocked automatic loading of the fixture; its end-to-end test was not completed and is not counted as passed.

No new all-language accuracy, long-video stress, mid-inference GPU-failure or universal Windows/hardware claims are made. The seven application runtime modules, cinema UI and protocol are unchanged. SureLive's production test package is untouched.

Download the `.exe` for installation and `SHA256SUMS.txt` for verification. `VALIDATION.json` and `BUILD-MANIFEST.json` record test results and build files. The separate `*-sources.zip` contains corresponding third-party sources, notices and rebuild materials; ordinary users do not need it. GitHub's automatic Source code archives contain this project's source, not an installer.
