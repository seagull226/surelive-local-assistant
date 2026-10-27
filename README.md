# SureLive Local Assistant

SureLive 的 Windows 本地字幕助手。Whisper 在用户电脑上识别音频，通过现有 Native Messaging 握手与本机 HTTP 接口连接影院。

**当前仓库提供源码、构建配置和测试，不提供正式安装包。** 从 SureLive 的隔离助手提取，保留界面、模型管理和通信方式。源码公开不表示安装包已通过商店审核或完成公开分发验证。

## 功能

- Whisper Small 多语言版和 Large-v3，模型词表提供 99 / 100 种语言；支持自动检测或指定原语言。
- NVIDIA CUDA 检测和加速；无可用 GPU 时使用 CPU，可手动选择 CPU；CUDA/显存类错误可回退 CPU。
- 固定版本与 SHA-256 校验的模型下载、续传、文件夹导入及存储位置设置；支持官方源和明确标注的第三方镜像。
- 按用户操作连接，无需连接码，不设置开机自启。中英管理界面、托盘、任务进度和退出确认。
- 按 5 分钟窗口识别，窗口两侧各 1 秒上下文；取消/断开清理，不设固定 90 分钟上限。

桌面窗口管理模型和任务，播放与字幕展示由影院负责。浏览器内 SenseVoice 继续属于插件，不在此原生助手中运行。

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
