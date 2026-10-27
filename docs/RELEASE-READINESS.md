# Windows 公开下载准备 / Windows release readiness

> **更新 / Update — 0.1.0-preview.1:** 下方保留的是首次只读检查记录，不能用来判断当前安装版状态。本次已采用有对应源码的最小 FFmpeg 构建、排除未使用的 PyAV 视频库、补齐随包材料并生成独立安装器。最终结果及限制见[本版说明](RELEASE-0.1.0-preview.1.md)。
>
> The initial read-only review below is historical. The installer now uses a traceable minimal FFmpeg build, excludes unused PyAV video libraries, includes redistribution materials and is built independently. See the [release notes](RELEASE-0.1.0-preview.1.md) for current results and limitations. Signing, a website, automatic updates and UI changes remain deferred.

核对日期 / Reviewed: **2026-10-27**。源码基线 / Source baseline: `b7c4079`。

## 中文

**Releases 可以承载安装包，但当前候选暂不公开上传。** 本轮只检查现有构建并补文档，不改功能、不重建或安装、不动 SureLive 正式测试包。仓库 Releases 本次查询为空。

### 发布前要补什么

| 项目 | 当前证据与缺口 | 最小下一步 |
| --- | --- | --- |
| 外部 FFmpeg EXE | 实际为 Gyan 7.1 full 静态构建，启用 GPL 和大量外部库；已有 FFmpeg 主源码不等于全部对应源码 | 找到该二进制完整对应源码/构建材料；找不到时，仅替换为可追溯的音频解码构建，比较常见音轨提取结果，保留影院和通信 |
| PyAV 自带 FFmpeg | 新包仍携带 x264/x265 DLL；运行时显示 LGPLv3，上游固定构建补丁将二者移出 GPL 列表，不能仅据该字符串认定整个组合可分发 | 核实该精确构建的授权；或重建/选择不带不需要的视频编码器的兼容版本，再测 ASR。不可只删 DLL，可能导致导入失败 |
| 最终随包说明及对应材料 | 新构建的自动收集仅为部分材料；例如 CTranslate2、tokenizers 目录只有 METADATA，没有单独许可证正文，旧完整材料也未自动装入新包 | 将已收集材料按新包实际文件筛选并纳入构建；核对 Python/Tcl/Tk、推理库及传递依赖、NVIDIA/Intel/Microsoft 条款，需要时提供对应源码/修改重建材料。不是要求把全部依赖改成 MIT |
| 安装与实际用户路径 | 独立构建只生成了程序目录，未生成/验证新安装器；旧 EXE 不等于新仓库构建。当前配置的 NSIS 路径也尚不存在 | 配置 NSIS，为固定源码生成一次新候选；在独立 Windows 环境测试无 Python/无模型首次安装、准备模型、Chrome/Edge 连接、GPU/CPU、取消、升级、卸载及模型保留 |
| 配套影院和发布资产 | 固定扩展 ID/预览 host；正式插件不会因助手安装自动增加入口。新安装器版本、体积、哈希尚无结果 | 明确兼容的影院版本/ID及可获取方式；以固定提交/tag 生成安装器、SHA256SUMS、双语说明和对应材料。配套插件不可用时只能称“预览测试”，不能承诺普通用户直接可用 |

这些是本项目根据实际文件提出的发布验收事项，不是声称 GitHub 会逐项审核或要求 EV 签名。FFmpeg 是否采用 GPL 构建本身不是禁止分发的理由；问题是适用义务及对应材料尚未完整确认。[FFmpeg 官方说明](https://www.ffmpeg.org/legal.html)要求注意准确对应源码和构建方式；具体组合仍应按实际条款处理。

### 已解决和可以后做的事项

- **CTranslate2 来源差异已在新构建解决。** 官方 4.8.2 wheel、冻结目录和构建回执中的 `ctranslate2.dll` SHA-256 均为 `34ff1eeefef2330f8abe777ae12b2238718e04503ad6e3bc9b6c9cb5be9fd274`。此结论仅针对新独立构建，不追认旧安装器。
- 上轮 17 项测试及 45 秒 Small 英文 GPU/CPU 识别通过。本轮重新核对现有目录的 **1,388 个文件全部匹配构建回执**；没有重跑产品验收。
- 签名可以后续做，不是 GitHub 上传 EXE 的前置技术门槛；但未签名会影响 Windows 信任体验，部分策略会阻止运行。签名也不保证首次下载无提示。[Microsoft 官方说明](https://learn.microsoft.com/en-us/windows/apps/package-and-deploy/smartscreen-reputation)。
- 官网、自动更新、精简安装器、把模型打进安装包、额外品牌/UI 改造均可后做；保留 Native Messaging + 本机 HTTP，无需为 Releases 重写通信。
- 中英文安装/模型/语言/托盘说明已准备：[中文](INSTALL.md) / [English](INSTALL.en.md)。安装器 UI 本身仍为中文，本轮只补文档。

### 体积和最小发布方案

现有未压缩程序目录共 **2,147,173,504 字节**（约 2.00 GiB），**不含模型**。这是目录总和，不是新安装 EXE 大小；压缩安装器尚未构建，不能据此判断最终资产已满足大小限制。GitHub 官方要求单个 Release 资产小于 2 GiB；对应源码材料可按组件分包，不必把模型塞入安装器。[GitHub Releases 文档](https://docs.github.com/en/repositories/releasing-projects-on-github/about-releases)。

最少改动的顺序：先解决两套 FFmpeg 相关材料/组合并补包内说明，再用现有脚本生成一次候选，完成隔离安装验证，最后发布标记清楚的 Windows x64 Pre-release。第一版保留模型首次下载/导入，不改影院、连接协议或正式测试包。不把“补了 README”当作二进制问题已解决。

### 证据范围

- 新构建：本地 `artifacts/standalone-001/build-receipt.json` 及对应 payload；这些体积较大的产物不提交 Git。
- 本轮只读检查：文件哈希、签名状态（桌面入口为 NotSigned）、实际 FFmpeg 配置、PyAV DLL、固定模型清单、安装脚本与注册身份。
- [PyAV 固定版本构建补丁](https://github.com/PyAV-Org/pyav-ffmpeg/blob/8.1.2-1/patches/ffmpeg.patch)与本地下载归档相符；“组合待确认”是基于文件的判断，不是宣称已作法律裁定。
- 没有新安装/卸载测试，没有新 Release、tag、二进制上传或数字签名；准确率和全语言兼容性未新增结论。

## English

**GitHub Releases can host the installer, but the current candidate is not ready for public binary distribution.** This review inspects existing outputs and adds documentation only. It does not change functionality, rebuild/install the app, or modify the SureLive production test package. The repository had no releases when checked.

### Required before publishing this candidate

| Item | Current finding | Smallest next step |
| --- | --- | --- |
| External FFmpeg executable | Gyan 7.1 full static build with GPL and many external libraries; the main FFmpeg source archive alone does not cover the complete build | Obtain exact corresponding sources/build materials, or replace only this component with a traceable audio-decoding build and compare common audio-track extraction |
| FFmpeg bundled with PyAV | The new payload still includes x264/x265 DLLs. Its LGPLv3 runtime string conflicts with an unresolved licensing question exposed by the pinned upstream classification patch | Establish authorization for that exact combination, or build/select a compatible distribution without the unnecessary video encoders and retest ASR. Do not simply delete required DLLs |
| Final third-party materials | Automatic collection is incomplete; CTranslate2 and tokenizers currently have METADATA only, without standalone license texts. Earlier collected materials are not automatically included | Match existing materials to the new payload, include required notices/terms and applicable corresponding-source or replacement/rebuild materials, and review transitive and native runtimes |
| Installer and user workflow | New independent output is a program directory, not a tested installer. Old EXEs do not represent this source build; the configured NSIS executable is absent | Configure NSIS, build one pinned candidate, and test clean Windows installation without Python/models, model preparation, both browsers, GPU/CPU, cancellation, upgrade, uninstall, and retained models |
| Compatible cinema and assets | Preview host and fixed extension ID; the helper cannot add a missing ASR entry to the production extension. New installer version/size/hash are not yet established | Identify an obtainable compatible cinema build/ID. Produce the installer, checksums, bilingual notes, and corresponding materials from a fixed commit/tag; label it as a preview while access is limited |

These are project release acceptance items derived from actual files, not claims that GitHub reviews each item or requires an EV certificate. A GPL FFmpeg build is not inherently undistributable; applicable obligations and complete materials remain unresolved. See [FFmpeg's official guidance](https://www.ffmpeg.org/legal.html) and the [pinned PyAV build patch](https://github.com/PyAV-Org/pyav-ffmpeg/blob/8.1.2-1/patches/ffmpeg.patch). The combination assessment is not a legal determination.

### Resolved or deferrable

- **The CTranslate2 binary-origin discrepancy is resolved for the new independent payload:** the official 4.8.2 wheel, payload DLL, and build receipt have the identical SHA-256 shown in the Chinese section. This does not validate old installers.
- The previous run passed 17 unit tests and Small GPU/CPU recognition on a 45-second English clip. This review rechecked **all 1,388 payload files** against their receipt. It did not rerun product acceptance tests.
- Signing can follow later and is not a GitHub EXE-upload prerequisite. Unsigned apps may be blocked by Windows or organizational policy; signing does not guarantee a warning-free first download. See [Microsoft's guidance](https://learn.microsoft.com/en-us/windows/apps/package-and-deploy/smartscreen-reputation).
- A website, auto-updates, smaller installer, bundled models, and UI/branding changes can wait. Preserve Native Messaging plus loopback HTTP.
- Bilingual user guides are ready: [中文](INSTALL.md) / [English](INSTALL.en.md). The installer UI itself remains Chinese.

### Size and minimal release plan

The uncompressed program directory totals **2,147,173,504 bytes** (about 2.00 GiB), excluding models. That is not the size of a new installer; none has been built in this independent project. GitHub requires each release asset to be **under 2 GiB**. Source companion materials can be separate assets; models can remain first-use downloads/imports. See [GitHub's release documentation](https://docs.github.com/en/repositories/releasing-projects-on-github/about-releases).

First resolve the two FFmpeg-related issues and complete bundled materials. Then build one candidate with the existing script, validate installation in an isolated Windows environment, and publish a clearly labeled Windows x64 pre-release. Keep the cinema, protocol, and production test package unchanged.

Evidence comes from the existing local build receipt/payload, file hashes, unsigned desktop entry, runtime configurations, model catalog, installer script, and fixed upstream patch. No new release, tag, binary upload, signing, install/uninstall test, accuracy claim, or all-language compatibility claim was produced by this review.
