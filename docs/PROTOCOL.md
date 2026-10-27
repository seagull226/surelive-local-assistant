# 通信接口

保留 Native Messaging 握手 + 本机 HTTP，不改为纯 HTTP，不增加云端识别。

1. 扩展 service worker 调用 `chrome.runtime.connectNative('com.surelive.asr.preview')`。
2. 浏览器启动 Host，Host 核对调用来源，在随机 `127.0.0.1` 端口监听。
3. 管道返回 `{endpoint, token, version: 1}`。Native 消息为四字节小端长度前缀加 UTF-8 JSON。
4. 扩展携带本次令牌，通过 HTTP 上传媒体、查询进度和取消。
5. 管道断开后，该会话释放服务和推理子进程。

令牌每次随机生成，不持久保存。HTTP 校验 Host、Bearer 与 Origin；浏览器 GET 可省略 Origin，但仍须令牌。预检只允许配套扩展。

| 接口 | 行为 |
| --- | --- |
| `GET /health` | 版本、长片能力、设备、模型就绪状态/大小/语言 |
| `POST /prepare` | JSON `{model, id}`，准备固定模型 |
| `PUT /jobs/<uuid>?model=small&language=auto&device=auto` | 请求体为媒体文件，提供 Content-Length；device 支持 auto/cpu |
| `GET /jobs/<uuid>` | 阶段、进度、错误、结果、finished |
| `DELETE /jobs/<uuid>` | 取消 |

结果包含 segments、durationSec、language、requestedLanguage、device、cpuFallback、inferenceMs。字幕时间单位为秒，耗时为毫秒。每个 Host 同时一个任务；各影院标签拥有独立连接。

媒体留在本机，任务结束/取消/退出清理临时文件。模型准备会访问下载源；不要把本地识别说成整个插件所有功能离线。

`integration/native-background.example.js` 仅是 service worker 接入参考，不是完整扩展；应保留影院页面来源检查。扩展需 Native Messaging 权限及实际本机 HTTP 访问配置，本仓库不修改插件 manifest。
