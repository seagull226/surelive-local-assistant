// Integration reference for an extension service worker; register in your existing worker.
// Each cinema tab owns its connection. Closing one tab must not stop another.
const helperConnections = new Map();
function disconnectHelper(key) {
  const connection = helperConnections.get(key);
  helperConnections.delete(key);
  connection?.stopHandshake?.();
  connection?.port.disconnect();
}
chrome.tabs.onRemoved.addListener(tabId => disconnectHelper(tabId));
chrome.runtime.onMessage.addListener((request, sender, reply) => {
  if (!['cinema-helper-connect', 'cinema-helper-disconnect'].includes(request?.type)) return;
  const expected = chrome.runtime.getURL('surelive-local.html');
  if (sender.id !== chrome.runtime.id || sender.url?.split(/[?#]/)[0] !== expected || sender.tab?.id === undefined) {
    reply({error:'仅本地影院可连接助手'}); return;
  }
  const key = sender.tab.id;
  const documentId = sender.documentId || sender.url;
  if (request.type === 'cinema-helper-disconnect') {
    if (helperConnections.get(key)?.documentId === documentId) disconnectHelper(key);
    reply({disconnected:true}); return;
  }
  let connection = helperConnections.get(key);
  if (connection && connection.documentId !== documentId) { disconnectHelper(key); connection = undefined; }
  if (!connection) {
    const port = chrome.runtime.connectNative('com.surelive.asr.preview');
    connection = {port, documentId}; helperConnections.set(key, connection);
    connection.handshake = new Promise((resolve, reject) => {
      let settled = false;
      const fail = message => { if (!settled) { settled = true; reject(Error(message)); } };
      const timer = setTimeout(() => { fail('助手启动超时，请重试'); disconnectHelper(key); }, 35000);
      connection.stopHandshake = () => { clearTimeout(timer); fail('连接已取消'); };
      port.onMessage.addListener(message => {
        if (settled) return;
        if (!/^http:\/\/127\.0\.0\.1:\d+$/.test(message?.endpoint) || typeof message.token !== 'string' || message.version !== 1) {
          clearTimeout(timer); fail('助手版本不兼容'); disconnectHelper(key); return;
        }
        settled = true; clearTimeout(timer); resolve(message);
      });
      port.onDisconnect.addListener(() => {
        const error = chrome.runtime.lastError;
        clearTimeout(timer);
        if (helperConnections.get(key) === connection) helperConnections.delete(key);
        fail(error ? '请先安装 SureLive 本机助手，再点击连接助手' : '助手已断开，请重试');
      });
    });
  }
  connection.handshake.then(reply, error => reply({error:error.message})); return true;
});
