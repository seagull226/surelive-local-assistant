# 基础小包：安装和使用

本包为 `0.1.1-basic.preview.2`，本轮重建的 Edge 兼容候选，发布状态以[对应 Release](https://github.com/seagull226/surelive-local-assistant/releases/tag/v0.1.1-basic.preview.2)为准。原完整包继续保留，选包比较及浏览器内 SenseVoice 模型包下载见[下载与选包说明](DOWNLOADS.md)。需配合 SureLive `v0.1.7+` 本地影院使用；安装方式、模型下载/导入、托盘及通信方式保持原样；不含 Whisper 模型。

下载 `SureLive-Local-Assistant-0.1.1-basic.preview.2-win-x64.exe`，核对同版 `SHA256SUMS.txt` 后按当前用户安装。打开助手，下载或导入 Small / Large-v3 模型，再在本地影院选择“Whisper · 本机小助手”。无需连接码。本版重新构建原生助手，支持商店 ID daefoeomgbpapjnpajciiikmhcadbdop 及固定测试 ID pigcndembijihpdlkdpmopjddomgjogc。旧版 preview.1 和完整包不支持商店 ID；仅改源码或白名单文件不能升级旧 EXE。

首次打开助手会检测显卡和可复用的环境。没有可用 NVIDIA 显卡时使用 CPU，不下载 GPU 组件。发现兼容的 CUDA 12/cuDNN 9 后，在独立进程完成 cuBLAS 运算和 cuDNN 卷积检查再复用，不修改已有环境。搜索范围为 PATH、CUDA_PATH/CUDNN_PATH 和标准 NVIDIA 安装目录，不扫描其他应用的私有环境。

缺少或不兼容时，在首次自动模式识别前，或点击“准备 / 重试 NVIDIA 加速”时，从 NVIDIA 官方下载约 1.11 GB 组件。需要约 3 GB 临时可用空间，逐个检查固定 SHA-256，解压和运行检查成功才启用。最终组件约 1.68 GB；成功后清理下载归档。进度在助手显示，可取消并续传，失败保留 CPU 识别能力。检测只需要显卡驱动，不安装驱动、不要求安装完整 CUDA 工具包。

勾选“仅用 CPU，不下载加速组件”可跳过下载。切换前先取消正在进行的任务；之后重新生成字幕。下载失败后可点击准备/重试，不会在后台无限重试。已有模型和已准备的组件会在后续使用时复用。

组件缓存为 `%LOCALAPPDATA%/SureLiveASRPreview/gpu-runtime`，与视频、字幕及模型目录分开。只在本用户范围使用，不修改系统 PATH；卸载保留模型和组件缓存。AMD/Intel 显卡当前走 CPU。安装器未签名；Windows 或企业策略可能提示或阻止运行。

测试范围与结果见 [按需 GPU 记录](ON-DEMAND-GPU.md)。
