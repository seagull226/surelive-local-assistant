# Edge store compatibility / Edge 商店兼容修复

This release rebuilds the native host for Edge extension ID `daefoeomgbpapjnpajciiikmhcadbdop` while retaining test ID `pigcndembijihpdlkdpmopjddomgjogc`. The earlier preview.1 executable does not contain the updated allowlist even though its tag's source was subsequently changed. Install this new version; editing an old manifest alone is insufficient. Old releases remain available for historical testing.

本版重新构建原生助手，同时支持 Edge 商店 ID 与原固定测试 ID。旧 preview.1 下载到的 EXE 没有包含更新后的白名单；仅修改旧 manifest 或源码不等于升级安装器。需要商店兼容性时安装本版，旧发布文件保留。

- Installer: `SureLive-Local-Assistant-0.1.1-basic.preview.2-win-x64.exe`
- Size: 87,932,453 bytes (87.93 MB / 83.86 MiB).
- SHA-256: `e91bb2de7194be7a883b611de32a30240eae85b4c679b0b6c6b04b2e10dde3d7`.
- Build source: `f8306f366fb57fb3dee5ce58adb01dcd82509f61`; subsequent download-guide changes do not change the executable.
- Native host remains `com.surelive.asr.preview`. Native messaging bootstraps an authenticated random-port loopback HTTP connection. No online ASR is restored.

Validation on 2026-10-27: 31 Python tests pass. Final binary probes accept both intended IDs and reject foreign native origins, foreign HTTP origins and missing tokens. The actual installer registers both Chrome and Edge registry views. An isolated Edge profile using the supplied store public key connects, prepares a local Small model, transcribes real English audio and displays subtitles, opens a second cinema connection and disconnects. Prior registry entries and shortcut were restored after testing. The store ZIP itself retains no public key.

验证范围：31 项自动测试、最终二进制双 ID 与拒绝路径、安装器注册、真实 Edge 商店身份下 Small 识别与字幕显示、双影院连接和断开。未重测全部模型、完整 GPU 下载或全新 Windows 系统。安装器仍未签名；模型不随安装器分发。

Use the release's `SHA256SUMS.txt`, `BUILD-MANIFEST.json` and `SOURCE-MATERIALS.txt`. SenseVoice's model archive remains at its existing URL and does not require this Windows helper. This helper release does not publish the browser extension.
