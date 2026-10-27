# 下载模型与安装包 / Downloads & Choose an Installer

> Edge 商店版请使用新重建的 `0.1.1-basic.preview.2`，发布状态见[新版本](https://github.com/seagull226/surelive-local-assistant/releases/tag/v0.1.1-basic.preview.2)。旧 `preview.1` 和完整包仅保留原固定测试 ID 兼容性；下方旧下载链接不适用于商店 ID。SenseVoice 模型包不受影响。

> For the Edge store extension, use rebuilt `0.1.1-basic.preview.2`; check its [release status](https://github.com/seagull226/surelive-local-assistant/releases/tag/v0.1.1-basic.preview.2). The old preview.1 and full installers support the original test ID only. The SenseVoice model bundle is unaffected.

## 一、SenseVoice 浏览器内识别模型包（免装 EXE 助手）

如果你在 SureLive 本地影院中选择 **“SenseVoice · 浏览器内识别”**（支持中文、英语、粤语、日语、韩语，需浏览器支持 WebGPU），无需安装下方的 Windows 助手程序，直接下载并解压此模型文件夹包即可：

- **直接下载**：**[sensevoice-small-fp32-cinema.zip (827 MB)](https://github.com/seagull226/surelive-local-assistant/releases/download/v0.1.1-basic.preview.1/sensevoice-small-fp32-cinema.zip)**
- **ZIP SHA-256**：`1190dd40123873afab75c853ffbc5edf09c15454ca0b94bac16c262d0861759f`
- **包含文件**：
  - `model.onnx`（`937,617,178` 字节，SHA-256 `977016bd9c79f9eb343430b5cc305e07ab64d5212dff41b0dcfa1694bee9a8cb`）
  - `tokens.txt`（`315,894` 字节，SHA-256 `f449eb28dc567533d7fa59be34e2abca8784f771850c78a47fb731a31429a1dc`）
- **导入步骤**：下载后**先解压 ZIP**，在本地影院左下角点击 **“导入模型文件夹”**，选中解压出来的 `sensevoice-small-fp32` 文件夹即可保存至浏览器本地并离线识别。

---

## 二、Whisper Windows 本机字幕助手（支持 99/100 种语言）

### 中文

两种安装包都需要 Windows x64 和配套 SureLive 本地影院（`v0.1.7+`），二选一即可，不需要都安装。它们使用同一个助手连接身份；当前不是两个独立并行安装的产品。

| 选择 | 基础小包（推荐先选） | 原完整包（保留） |
| --- | --- | --- |
| 版本 | `0.1.1-basic.preview.2` | `0.1.0-preview.1` |
| 安装器大小 | **87.9 MB** | **1.21 GB** |
| 适合谁 | CPU 用户、AMD/Intel 显卡用户、已有兼容 NVIDIA 环境，或希望先少下载的用户 | NVIDIA 用户希望一次备齐加速库，或需要准备多台电脑/网络不稳定的环境 |
| NVIDIA 加速库 | 检测后复用兼容环境；缺少时从 NVIDIA 官方按需下载约 **1.11 GB**，以后复用缓存 | 加速库已经包含在安装器内 |
| 无可用 NVIDIA 显卡 | 使用 CPU，不下载 GPU 组件 | 使用 CPU，但仍需下载整个安装器 |
| Whisper 模型 | **不包含**，首次下载或导入 | **不包含**，首次下载或导入 |
| 下载 | [基础包 Release](https://github.com/seagull226/surelive-local-assistant/releases/tag/v0.1.1-basic.preview.2) | [完整包 Release](https://github.com/seagull226/surelive-local-assistant/releases/tag/v0.1.0-preview.1) |

有 NVIDIA 显卡或驱动，不等于已经装好兼容的 CUDA/cuDNN 推理库。基础包会实际检查这些库；缺少时下载组件，下载失败仍可使用 CPU。选择“仅用 CPU，不下载加速组件”可以跳过加速组件准备。AMD/Intel 显卡目前不用于此助手的 GPU 加速。

**已有完整包运行正常，可以继续使用，无需为了下载体积换装。** 基础包主要减少首次安装器下载量；如果新机器需要补齐全部 NVIDIA 组件，总下载量仍约 1.2 GB，另加模型。覆盖安装也不会保证清除原来已有的加速库。完整包只包含运行环境，只有另外准备好模型后才能离线识别，它不是“包含模型的全离线包”。

Small 模型约 486 MB，Large-v3 约 3.09 GB；两种安装包都不需要用户另外安装 Python。NVIDIA 加速需要兼容显卡驱动，助手不会安装驱动。两种包均未签名，Windows 或企业策略可能提示或阻止运行。

新版 preview.2 配合 SureLive `v0.1.7+` 本地影院使用（支持固定扩展 ID `pigcndembijihpdlkdpmopjddomgjogc` 及 Edge 商店版扩展 ID `daefoeomgbpapjnpajciiikmhcadbdop`）。本仓库不分发浏览器扩展本体，也不是独立视频播放器。首次安装和模型准备见[基础包中文说明](BASIC-INSTALL.md)或[完整包中文说明](INSTALL.md)。下载后核对相应 Release 的 `SHA256SUMS.txt`。

### English

If you use **SenseVoice (in-browser WebGPU recognition)** in SureLive Local Cinema, you do not need the Windows EXE installer—simply download and extract **[sensevoice-small-fp32-cinema.zip (827 MB)](https://github.com/seagull226/surelive-local-assistant/releases/download/v0.1.1-basic.preview.1/sensevoice-small-fp32-cinema.zip)** (SHA-256: `1190dd40123873afab75c853ffbc5edf09c15454ca0b94bac16c262d0861759f`) and import the extracted `sensevoice-small-fp32` folder in Local Cinema.

For **Whisper (Windows native companion)**, both installers require Windows x64 and SureLive Local Cinema (`v0.1.7+`). **Choose one; you do not need both.** They use the same helper identity and are not separate side-by-side products.

| Choice | Basic installer (recommended starting point) | Retained full installer |
| --- | --- | --- |
| Version | `0.1.1-basic.preview.2` | `0.1.0-preview.1` |
| Installer size | **87.9 MB** | **1.21 GB** |
| Best for | CPU users, AMD/Intel graphics users, compatible NVIDIA environments, or a smaller initial download | NVIDIA users who want acceleration libraries included up front, multiple-PC deployment, or unreliable network access |
| NVIDIA libraries | Checks and reuses compatible local libraries; otherwise downloads about **1.11 GB** from NVIDIA and caches them | Included in the installer |
| No usable NVIDIA GPU | Uses CPU without downloading GPU components | Uses CPU, but the whole installer must still be downloaded |
| Whisper models | **Not included**; download or import separately | **Not included**; download or import separately |
| Download | [Basic release](https://github.com/seagull226/surelive-local-assistant/releases/tag/v0.1.1-basic.preview.2) | [Full release](https://github.com/seagull226/surelive-local-assistant/releases/tag/v0.1.0-preview.1) |

Having an NVIDIA GPU and driver does not imply that compatible CUDA/cuDNN inference libraries are installed. The basic installer checks them, prepares missing components when needed, and retains CPU operation on failure. Select **Use CPU only; do not download acceleration components** to skip preparation. AMD/Intel graphics are currently handled through CPU recognition.

**If the full installer already works for you, you can keep using it.** The basic installer reduces the initial download; a new NVIDIA setup that needs all components still downloads about 1.2 GB in total, plus a model. Installing over an existing copy does not guarantee removal of old acceleration libraries. The full installer is not an all-in-one offline model package: offline recognition also requires a model prepared separately.

Small is about 486 MB and Large-v3 about 3.09 GB. Neither installer requires a separate Python installation. NVIDIA acceleration requires a compatible driver; the helper does not install drivers. Both installers are unsigned, so Windows or organizational policy may warn or block them.

New preview.2 is compatible with SureLive `v0.1.7+` Local Cinema (extension IDs `pigcndembijihpdlkdpmopjddomgjogc` and Microsoft Edge extension ID `daefoeomgbpapjnpajciiikmhcadbdop`). This repository does not distribute the browser extension or play videos independently. See the [basic setup guide](BASIC-INSTALL.en.md) or [full setup guide](INSTALL.en.md). Verify downloads against `SHA256SUMS.txt` in the corresponding release.
