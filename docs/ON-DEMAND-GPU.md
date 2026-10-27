# 基础安装包与按需 NVIDIA 组件（隔离验证）

范围：2026-10-27 用户授权；负责人为本聊天。目录 `E:/GitHub/surelive-local-assistant`，分支 `codex/on-demand-gpu`，基线 `8bbfadefbde43f0689ffb7fa5b7a31cac7589c8e`。保留已发布的完整包，另生成基础安装器，不覆盖 Release、不改 SureLive 正式测试包。

验收：基础包不带大型 GPU 库；无可用 NVIDIA 时不下载且 CPU 可识别；本机兼容运行库通过子进程实际运算后复用；缺失/不兼容时按需下载固定 NVIDIA 归档，校验后启用；下载可取消、续传和重试，失败可走 CPU；再次使用无需重复下载。保留现有影院通信和模型管理；硬件区域仅增加必要状态、准备/重试入口及 CPU 选项。

组件来源：NVIDIA 官方再分发归档，不下载或安装显卡驱动，不修改全局 PATH/CUDA 安装。下载写入助手自己的用户缓存，系统已有库只读。模型下载方式保持不变。新安装器先保存在本项目 artifacts 下验证，不公开上传。

## 最终隔离候选与结果

代码提交 `a49f2d8`，构建目录 `artifacts/basic-004`，版本 `0.1.1-basic.preview.1`。安装器 **87,930,828 字节（约 87.9 MB）**，比已发布完整包缩小约 **92.7%**；程序目录约 **340.6 MB**。没有随包携带大型 NVIDIA 加速库，保留推理依赖自身的小型 cuDNN 接口库。模型仍需另行准备。

本地交付目录：`artifacts/basic-delivery-0.1.1`。其中包含安装器、中英文指南、`VALIDATION.json` 和 `SHA256SUMS.txt`。安装器 SHA-256：`f6ab32cba2f3f5fe7e2e653afd0e94ae3c117bccb543ed9877d348f770ae3d15`。

| 场景 | 最终候选结果 | 本地证据目录 |
| --- | --- | --- |
| NVIDIA、无兼容库、空缓存 | 从 NVIDIA 官方实际下载 1,105,298,786 字节，校验、解压、运行检查通过，Small 使用 CUDA 生成字幕，缓存激活 | `basic-final-fresh-download` |
| 关闭后重连 | 读取已验证缓存，CUDA 识别通过，没有新的组件下载阶段 | `basic-final-cache-reuse` |
| 已有兼容环境 | 在隔离 PATH 中提供真实 CUDA/cuDNN 库，实际 GPU 运算检查和 Small 识别通过，没有下载、没有复制成托管缓存 | `basic-final-install/gpu` |
| 无可见 CUDA 设备 | 使用 `CUDA_VISIBLE_DEVICES=-1` 模拟，CPU 识别通过，无组件下载 | `basic-final-install/cpu` |
| 有 NVIDIA、手动选 CPU | CPU 识别通过，无组件下载、无已激活 GPU 缓存 | `basic-final-explicit-cpu` |
| 损坏的本机库并且下载不可用 | 隔离测试副本注入坏 DLL 和不可达下载地址，拒绝启用坏库，回退 CPU 完成识别并提示可重试 | `basic-final-offline` |
| Large-v3 | 最终程序复用兼容环境，CUDA 识别通过，无组件下载 | `basic-final-large` |
| 安装与连接 | 中文路径安装、Chrome/Edge 注册、同版本重装、卸载、保留用户文件/模型通过；原注册与快捷方式恢复。Edge 和 Chrome for Testing 握手、健康查询、断开通过 | `basic-final-install` |

同一 45 秒英文小样用于实际识别验证；这里只证明运行分支和生成字幕成功，不新增准确率或长片速度结论。各次推理耗时保存在回执中，存在并发测试，不作受控性能比较。

31 项单元测试通过，包括下载取消/续传、损坏归档与 DLL 不激活、保留大小/时间戳的缓存篡改修复、下载失败后重试、等待跨进程准备锁时取消。真实 Tk 控件通过 CPU 设置持久化、准备按钮调用、复用/无显卡状态、中英文切换及控件宽度检查，证据 `basic-ui-controls/result.json`。

## 边界与早期失败记录

- 环境为 Windows 10 Pro x64（19045）、RTX 5060 Ti；不是全新 Windows VM，没有另外一台 AMD/Intel 显卡机器的验收。未修改插件、影院或模型/字幕拼接算法。
- 普通 Chrome 155 拦截自动加载测试扩展，其端到端检查未计为通过。窗口截图工具两次返回 `window capture timed out: timed out waiting on channel`；真实控件测试通过，但视觉截图验收仍未完成。
- 早期 `basic-001` 完整下载后首次 GPU 检查失败并回退 CPU；一次后续解压重试出现 CRC 错误，复核三个归档和已解压 DLL 的 SHA-256 均与固定值一致，原始失败的确切原因未证实。后续补充检查失败诊断、首次加载等待时间、一次新进程重试，以及缓存归档的全字节复检。最终 `basic-004` 重新从空缓存走完整网络下载并激活 GPU、重启复用及识别全部通过，不能将早期失败回执当作最终结果。
- 保留原有完整安装包及公开 Release；本轮没有上传新版本、改正式测试包或更改全局 CUDA/PATH。已有安装目录和系统环境只读复用，测试安装只在独立目录进行，临时注册均已恢复。

## English summary

The isolated basic installer is **87.9 MB**, about **92.7% smaller** than the retained full installer. It uses compatible local libraries after real cuBLAS/cuDNN checks; otherwise it downloads pinned NVIDIA components on demand. No GPU or explicit CPU mode skips downloads. A real empty-cache download, GPU transcription, restart/cache reuse, existing-library reuse, CPU operation, failure fallback, Large-v3, and isolated installation/reinstallation/uninstallation passed on the final candidate. Original browser registrations were restored.

The package remains local and unsigned. The full release and production extension are unchanged. Retail Chrome fixture loading and visual screenshot verification remain incomplete; a fresh Windows VM and separate non-NVIDIA machine were not tested. Early-candidate failures are retained above and are separate from final-candidate results. See `VALIDATION.json` and the bilingual setup guides in the local delivery folder.
