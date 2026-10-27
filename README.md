# SureLive Local Assistant

> Edge 商店版请使用新重建的 `0.1.1-basic.preview.2`，发布状态见[新版本](https://github.com/seagull226/surelive-local-assistant/releases/tag/v0.1.1-basic.preview.2)。旧 `preview.1` 和完整包仅保留原固定测试 ID 兼容性；下方旧下载链接不适用于商店 ID。SenseVoice 模型包不受影响。

> For the Edge store extension, use rebuilt `0.1.1-basic.preview.2`; check its [release status](https://github.com/seagull226/surelive-local-assistant/releases/tag/v0.1.1-basic.preview.2). The old preview.1 and full installers support the original test ID only. The SenseVoice model bundle is unaffected.

[中文](README.md) | [English](README.en.md)

SureLive 本地影院的本地语音识别（ASR）配套资源与 Windows 助手。配合 SureLive `v0.1.7` 及以上版本的本地影院使用，提供两种本地字幕生成方式：

### 方式一：SenseVoice 浏览器内识别（推荐 · 免安装 EXE 助手）

- **模型整合包下载**：**[sensevoice-small-fp32-cinema.zip (827 MB)](https://github.com/seagull226/surelive-local-assistant/releases/download/v0.1.1-basic.preview.1/sensevoice-small-fp32-cinema.zip)**
  - SHA-256：`1190dd40123873afab75c853ffbc5edf09c15454ca0b94bac16c262d0861759f`
  - 包含完整校验的 `model.onnx`（937,617,178 字节）与 `tokens.txt`（315,894 字节），支持中文、英语、粤语、日语、韩语（需浏览器支持 WebGPU）。
  - **使用方法**：下载并解压该 ZIP，打开 SureLive 本地影院，在左下角“本地生成字幕”面板选择 **“SenseVoice · 浏览器内识别”**，点击 **“导入模型文件夹”** 并选择解压后的 `sensevoice-small-fp32` 文件夹即可离线识别，无需安装下方的 Windows 助手。

### 方式二：Whisper Windows 本机助手（支持 99/100 种语言 · GPU/CPU）

Whisper 在用户电脑上识别音频，通过 Native Messaging 握手与本机 HTTP 接口连接 SureLive 本地影院。

**Windows x64：[基础小包 87.9 MB](https://github.com/seagull226/surelive-local-assistant/releases/tag/v0.1.1-basic.preview.2) · [原完整包 1.21 GB](https://github.com/seagull226/surelive-local-assistant/releases/tag/v0.1.0-preview.1)。** 一般先选基础包：复用兼容环境，缺少 NVIDIA 加速库时按需下载；完整包预先包含加速库。两者都不含 Whisper 模型、不需要另装 Python。详细比较见[两个包怎么选 / Choose an installer](docs/DOWNLOADS.md)。

准备安装前请先看[基础包中文说明](docs/BASIC-INSTALL.md) / [English setup guide](docs/BASIC-INSTALL.en.md)。新版 preview.2 支持配套的 SureLive `v0.1.7+` 本地影院（固定扩展 ID `pigcndembijihpdlkdpmopjddomgjogc` 及 Edge 商店扩展 ID `daefoeomgbpapjnpajciiikmhcadbdop`）。安装包尚未签名；基础包验证范围见[本版说明](docs/RELEASE-0.1.1-basic.preview.2.md)。

## 功能

- Whisper Small 多语言版和 Large-v3，模型词表提供 99 / 100 种语言；支持自动检测或指定原语言。
- NVIDIA CUDA 检测和加速；无可用 GPU 时使用 CPU，可手动选择 CPU；CUDA/显存类错误可回退 CPU。
- 固定版本与 SHA-256 校验的模型下载、续传、文件夹导入及存储位置设置；支持官方源和明确标注的第三方镜像。
- 按用户操作连接，无需连接码，不设置开机自启。中英管理界面、托盘、任务进度和退出确认。
- 按 5 分钟窗口识别，窗口两侧各 1 秒上下文；取消/断开清理，不设固定 90 分钟上限。

桌面窗口管理模型和任务，播放与字幕展示由影院负责。浏览器内 SenseVoice 在插件内部通过 WebGPU 运行，不在此原生助手中运行。

## 开发

Windows x64、Python 3.12（本次使用 3.12.10）：

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install --require-hashes -r requirements-windows.lock
.\.venv\Scripts\python.exe tools\run_tests.py
```

按 [构建说明](docs/BUILD.md) 准备 FFmpeg 和可选 GPU 输入，将 `build.example.json` 复制为不提交的 `build.local.json`，填写文件及校验值：

```powershell
.\.venv\Scripts\python.exe tools\build_windows.py --config build.local.json --output artifacts\local-preview
```

构建不需要 Whisper 权重，只生成本项目下的新目录，不安装、不改注册表。参见 [安装与连接](docs/INSTALL.md)、[通信接口](docs/PROTOCOL.md)、[验证与当前状态](docs/STATUS.md)。

## 目录

| 路径 | 内容 |
| --- | --- |
| `src/surelive_local_asr/` | Host、Whisper 工作进程、桌面窗口、模型与会话管理、字幕拼接 |
| `resources/models.json` | 固定模型清单、语言、大小和校验值，不含权重 |
| `tools/` | 独立构建、测试及本机协议验证 |
| `installer/windows.nsi` | 按用户安装/卸载，保留隔离身份 |
| `integration/` | 扩展接入参考 |

本机配置、依赖二进制、模型、音视频、字幕与构建结果不提交。源代码沿用 [MIT 许可证](LICENSE)，依赖组件适用各自条款，见 [第三方说明](THIRD-PARTY-NOTICES.txt)。
