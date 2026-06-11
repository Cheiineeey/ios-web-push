// 前端推送订阅逻辑
// 替换下面的公钥为你自己生成的 Application Server Key

const VAPID_PUBLIC_KEY = '你的Base64公钥';

// Web Push API 要求 Base64 转 Uint8Array
function urlBase64ToUint8Array(base64String) {
  const padding = '='.repeat((4 - base64String.length % 4) % 4);
  const base64 = (base64String + padding)
    .replace(/-/g, '+').replace(/_/g, '/');
  const rawData = window.atob(base64);
  return new Uint8Array([...rawData].map(c => c.charCodeAt(0)));
}

// 初始化推送订阅
async function initPush() {
  if (!('serviceWorker' in navigator) || !('PushManager' in window)) {
    console.log('Push not supported');
    return;
  }

  try {
    // 注册 Service Worker
    const reg = await navigator.serviceWorker.register('/sw.js');
    await navigator.serviceWorker.ready;

    // 检查是否已订阅
    let sub = await reg.pushManager.getSubscription();

    if (!sub) {
      // 请求通知权限
      const permission = await Notification.requestPermission();
      if (permission !== 'granted') {
        console.log('Notification permission denied');
        return;
      }

      // 发起推送订阅
      sub = await reg.pushManager.subscribe({
        userVisibleOnly: true,
        applicationServerKey: urlBase64ToUint8Array(VAPID_PUBLIC_KEY)
      });

      // 把 subscription 发给后端存储
      await fetch('/api/push-subscribe', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(sub)
      });

      console.log('Push subscription saved');
    }
  } catch (e) {
    console.warn('Push init failed:', e);
  }
}

// ⚠️ iOS 要求：权限请求必须在用户手势（click/tap）中触发
// 不要在 window.onload 里直接调用 initPush()
// 推荐：给按钮绑定 onclick，用户点了再初始化
//
// 示例：
// document.getElementById('enablePush').onclick = () => initPush();
//
// 如果你确定只在桌面/Android 上用，可以这样自动初始化：
// window.addEventListener('load', () => setTimeout(initPush, 2000));
