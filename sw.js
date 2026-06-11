// Service Worker: 接收推送并弹出系统通知
// 放在网站根目录（和 index.html 同级）

self.addEventListener('push', function(event) {
  const data = event.data ? event.data.json() : {};

  const title = data.title || '新消息';
  const options = {
    body: data.body || '',
    icon: '/icon-192.png',
    badge: '/icon-192.png',
    data: { url: data.url || '/' },
    requireInteraction: false,
    silent: false
  };

  event.waitUntil(
    self.registration.showNotification(title, options)
  );
});

// 点击通知时打开或聚焦 PWA
self.addEventListener('notificationclick', function(event) {
  event.notification.close();
  const url = event.notification.data.url || '/';

  event.waitUntil(
    clients.matchAll({ type: 'window', includeUncontrolled: true })
      .then(function(clientList) {
        for (const client of clientList) {
          if (client.url.includes(self.location.origin) && 'focus' in client) {
            return client.focus();
          }
        }
        if (clients.openWindow) return clients.openWindow(url);
      })
  );
});

self.addEventListener('install', () => self.skipWaiting());
self.addEventListener('activate', () => self.clients.claim());
