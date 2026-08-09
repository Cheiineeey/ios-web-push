# iOS Web Push：从零到 iPhone 系统通知

用 VAPID + Service Worker + pywebpush，四个文件，让 iPhone 收到真正的系统级推送通知。不需要 App Store，不需要 APNs 证书，不需要第三方推送服务。

## 为什么做这个

iOS 16.4 开始支持 Web Push Notification。一个 PWA（添加到主屏幕的网页应用）可以像原生 App 一样给 iPhone 发推送——锁屏横幅、通知中心、声音震动，全都有。

但 iOS 的实现比 Android 和桌面浏览器多了几道门槛：必须 HTTPS，必须通过"添加到主屏幕"安装，必须在 PWA 模式下才能订阅，权限请求必须由用户手势触发。这些坑中文资料几乎没有讲清楚。

## 架构

```
iPhone (PWA)                VPS (Python)
    │                           │
    │  1. navigator.serviceWorker.register()
    │  2. pushManager.subscribe()
    │  ──── subscription JSON ───▶
    │                    3. 存入 SQLite
    │                           │
    │                    4. pywebpush(sub, payload)
    │  ◀── Push via FCM/APNs ───│
    │  5. sw.js: push event → showNotification()
    ▼                           ▼
```

## 快速开始

### 1. 生成 VAPID 密钥

```bash
pip install pywebpush
vapid --gen
vapid --applicationServerKey
# 输出一串 Base64 字符串，复制下来
```

### 2. 部署文件

把以下文件放到你的 HTTPS 网站根目录：

| 文件 | 作用 |
|------|------|
| `sw.js` | Service Worker，接收 push 事件并弹出通知 |
| `manifest.json` | PWA 清单，iOS 必须 |
| `subscribe.js` | 前端订阅逻辑，注册 SW + 请求权限 |
| `server.py` | 后端 API：存订阅 + 发推送 |

### 3. 修改配置

- `subscribe.js` 里替换 `VAPID_PUBLIC_KEY` 为你的公钥
- `server.py` 里替换 `VAPID_PRIVATE_KEY_PATH` 和 `VAPID_EMAIL`

### 4. 在 iPhone 上测试

1. 用 Safari 打开你的网站
2. 点分享按钮 → **添加到主屏幕**
3. 从主屏幕图标打开 PWA
4. 点击页面上的"开启通知"按钮
5. 运行 `python3 server.py` 发送测试推送

## iOS 的三道门槛

### 门槛一：必须 HTTPS
HTTP 下 `PushManager` 直接不存在。用 Let's Encrypt 免费证书。

### 门槛二：必须"添加到主屏幕"
只有以 PWA 模式运行时（从主屏幕图标打开，没有 Safari 地址栏），`PushManager` 才可用。在 Safari 里直接打开？`PushManager` 是 `undefined`。

### 门槛三：权限请求必须由用户手势触发
`Notification.requestPermission()` 必须在 click/tap 回调里调用。页面加载时直接请求会被 iOS 静默拒绝，没有弹窗。

## 调试指南

**推送发了但没收到？**

1. 确认是从主屏幕图标打开的（不是 Safari）
2. 设置 → 通知 → 找到你的 PWA → 确认通知权限开着
3. 检查 subscription 是否正确存入了数据库
4. 服务端 `webpush()` 有没有抛异常（401 = VAPID 密钥错误，410 = 订阅已过期）
5. 确认 `sw.js` 在根目录且能正常访问

**410 Gone**：订阅过期了。需要用户重新打开 PWA 自动重新订阅。

**桌面 Chrome 能收到但 iPhone 收不到**：99% 是因为没从主屏幕打开，或者权限请求没在用户手势里触发。

## 进阶玩法

- **定时推送**：用 cron 定时调用 `send_push()` 发送早安/晚安消息
- **iOS Shortcuts 触发**：创建捷径，用"获取 URL 内容"动作 POST 到推送接口，从 iPhone 甚至 Apple Watch 一键触发
- **LLM 生成内容**：推送前调用 AI API 生成消息内容，每次收到的都不一样

## 依赖

- Python 3.7+
- `pywebpush`（`pip install pywebpush`）
- HTTPS 域名
- iOS 16.4+ / 任意现代浏览器

## License

[MIT](LICENSE)

---

*韩屿 · 2026.6*
