# SureLive Local Assistant 0.1.1-basic.preview.1

## 中文

Windows x64 基础小包公开预览。上传的是隔离验证通过的原安装器，没有重新构建；原完整包继续保留。

| 怎么选 | 基础小包：本 Release | 完整包：上一版 |
| --- | --- | --- |
| 下载大小 | **87.9 MB** | **1.21 GB** |
| 建议用途 | CPU、AMD/Intel 显卡、已有兼容 NVIDIA 环境，或先少下载 | NVIDIA 用户希望一次备齐加速库，或网络不稳定 |
| NVIDIA 组件 | 优先复用兼容环境，缺少时从 NVIDIA 官方按需下载约 1.11 GB | 安装器已包含 |
| Whisper 模型 | 不包含，另行下载或导入 | 不包含，另行下载或导入 |

[原完整包下载](https://github.com/seagull226/surelive-local-assistant/releases/tag/v0.1.0-preview.1) · [详细选包说明](https://github.com/seagull226/surelive-local-assistant/blob/v0.1.1-basic.preview.1/docs/DOWNLOADS.md) · [中文安装说明](https://github.com/seagull226/surelive-local-assistant/blob/v0.1.1-basic.preview.1/docs/BASIC-INSTALL.md)

有 NVIDIA 显卡/驱动不等于已有兼容的 CUDA/cuDNN 库。助手会实际验证再复用；准备失败可用 CPU，也可选择“仅用 CPU，不下载加速组件”。AMD/Intel 显卡目前使用 CPU。首次补齐组件需要约 3 GB 临时空间，成功后保留约 1.68 GB 组件缓存。若需补齐全部 GPU 组件，基础包总下载量约 1.2 GB，另加模型；已有完整包正常工作的用户无需换装。二选一安装，连接身份相同。

安装后打开助手，下载或导入模型，再在配套影院选择“Whisper · 本机助手”。Small 约 486 MB，Large-v3 约 3.09 GB。无需另外安装 Python。模型和加速组件准备好后可离线识别。

**预览范围：** 两种安装器均未签名，需要已有配套隔离影院（扩展 ID `pigcndembijihpdlkdpmopjddomgjogc`）。本仓库不分发插件，助手不是独立播放器，安装不会为旧正式插件增加 ASR 入口。正式插件测试包未修改。

**验证：** 31 项单元测试；最终安装器的真实 NVIDIA 官方组件下载、GPU 识别、重启后缓存复用、已有兼容环境复用、手动 CPU、模拟无显卡、下载失败回退、Small/Large-v3、安装/卸载/模型保留通过。Edge 和 Chrome for Testing 连接通过。测试机为 Windows 10 x64 / RTX 5060 Ti；未验证全新虚拟机或实体无 NVIDIA 机器。零售 Chrome 自动加载测试受阻；真实窗口控件已测，截图验收未完成。这不是新的准确率或长片性能基准。完整限制见附件 `VALIDATION.json` 和仓库验证记录。

**文件核对与源码：** 使用 `SHA256SUMS.txt` 核对附件。`VALIDATION.json` 中 `published: false` 是原测试阶段快照，发布信息见本 Release。安装器内“隔离试用”文字也保留原测试快照。助手当前源码及构建脚本见本 tag；未变更的第三方对应源码和材料复用[上一版 sources.zip](https://github.com/seagull226/surelive-local-assistant/releases/download/v0.1.0-preview.1/SureLive-Local-Assistant-0.1.0-preview.1-sources.zip)，校验值见 `SOURCE-MATERIALS.txt`。安装器仍包含适用的通知及条款。

## English

Windows x64 basic installer preview. This is the exact installer validated in isolation, without rebuilding. The previous full installer remains available.

| Choose | Basic: this release | Full: previous release |
| --- | --- | --- |
| Installer download | **87.9 MB** | **1.21 GB** |
| Best for | CPU, AMD/Intel GPUs, compatible existing NVIDIA libraries, or a smaller initial download | NVIDIA users who want acceleration libraries bundled, or have unreliable connectivity |
| NVIDIA libraries | Reuse a compatible environment; otherwise download about 1.11 GB from NVIDIA on demand | Included in the installer |
| Whisper models | Not included; download or import separately | Not included; download or import separately |

[Retained full installer](https://github.com/seagull226/surelive-local-assistant/releases/tag/v0.1.0-preview.1) · [Detailed comparison](https://github.com/seagull226/surelive-local-assistant/blob/v0.1.1-basic.preview.1/docs/DOWNLOADS.md) · [English installation guide](https://github.com/seagull226/surelive-local-assistant/blob/v0.1.1-basic.preview.1/docs/BASIC-INSTALL.en.md)

An NVIDIA GPU/driver alone does not provide compatible CUDA/cuDNN libraries. The helper validates libraries before reuse; preparation failure leaves CPU recognition available. Select CPU-only to skip acceleration downloads. AMD/Intel GPUs currently use CPU. Preparation needs about 3 GB of temporary free space and retains about 1.68 GB of runtime files. If all GPU components are needed, total downloads are about 1.2 GB plus the model. Keep a working full installation if desired; choose one installer, as both use the same helper identity.

Open the installed helper, download/import a model, then select Whisper in the matching cinema. Small is about 486 MB and Large-v3 about 3.09 GB. Python installation is not required. Recognition works offline after models and required components are prepared.

**Preview scope:** Both installers are unsigned and require the existing matching preview cinema (extension ID `pigcndembijihpdlkdpmopjddomgjogc`). This repository does not distribute the extension. The helper is not a standalone player and cannot add ASR to an older production extension. The production extension test package is unchanged.

**Validation:** 31 unit tests passed. The final installer passed real NVIDIA downloads and GPU inference, restart/cache reuse, existing-library reuse, explicit CPU, simulated unavailable GPU, failed-download CPU fallback, Small/Large-v3, installation/uninstallation and model retention. Edge and Chrome for Testing connections passed. Tested on Windows 10 x64 / RTX 5060 Ti, not a clean VM or physical non-NVIDIA machine. Retail Chrome blocked automated fixture loading; real window controls were tested but screenshot acceptance is incomplete. These are smoke checks, not new accuracy or long-video throughput benchmarks. See `VALIDATION.json` and the repository validation record for limitations.

**Checksums and source:** Verify attachments with `SHA256SUMS.txt`. `published: false` in `VALIDATION.json` records the original validation stage, not the current release state; embedded isolated-preview notes are also preserved snapshots. Current helper source and build scripts are in this tag. Unchanged third-party corresponding sources and materials are shared with the retained [previous sources.zip](https://github.com/seagull226/surelive-local-assistant/releases/download/v0.1.0-preview.1/SureLive-Local-Assistant-0.1.0-preview.1-sources.zip); see `SOURCE-MATERIALS.txt` for its checksum. Applicable notices and terms remain in the installer.
