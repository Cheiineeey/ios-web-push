"""
Web Push 后端：存储订阅 + 发送推送
依赖：pip install pywebpush

使用方式：
  1. 修改下面的 VAPID_PRIVATE_KEY_PATH 和 VAPID_EMAIL
  2. python3 server.py
  3. 访问 http://localhost:8000 测试
"""

import json
import sqlite3
from http.server import HTTPServer, BaseHTTPRequestHandler
from pywebpush import webpush, WebPushException

# ===== 配置 =====
VAPID_PRIVATE_KEY_PATH = '/path/to/private_key.pem'  # 替换为你的私钥路径
VAPID_EMAIL = 'mailto:you@example.com'               # 替换为你的邮箱
DB_PATH = 'push.db'
PORT = 8000

def get_db():
    db = sqlite3.connect(DB_PATH)
    db.execute("""CREATE TABLE IF NOT EXISTS push_subscriptions
        (id INTEGER PRIMARY KEY, sub TEXT, created_at TEXT)""")
    return db

def save_subscription(sub_json):
    """保存推送订阅（单用户场景，只保留最新一个）"""
    db = get_db()
    db.execute("DELETE FROM push_subscriptions")
    db.execute(
        "INSERT INTO push_subscriptions (sub, created_at) VALUES (?, datetime('now'))",
        (json.dumps(sub_json),)
    )
    db.commit()
    db.close()

def send_push(title, body, url='/'):
    """发送推送通知"""
    db = get_db()
    row = db.execute("SELECT sub FROM push_subscriptions LIMIT 1").fetchone()
    db.close()

    if not row:
        raise Exception("没有订阅。请先在 PWA 中打开通知权限。")

    sub = json.loads(row[0])
    payload = json.dumps({"title": title, "body": body, "url": url})

    try:
        webpush(
            subscription_info=sub,
            data=payload,
            vapid_private_key=VAPID_PRIVATE_KEY_PATH,
            vapid_claims={"sub": VAPID_EMAIL}
        )
        print(f"✅ 推送成功: {title} - {body}")
    except WebPushException as e:
        print(f"❌ 推送失败: {e}")
        # 410 = 订阅过期，清理掉
        if e.response and e.response.status_code == 410:
            db = get_db()
            db.execute("DELETE FROM push_subscriptions")
            db.commit()
            db.close()
            print("🗑️ 已清理过期订阅")
        raise

class Handler(BaseHTTPRequestHandler):
    def do_POST(self):
        length = int(self.headers.get('Content-Length', 0))
        body = json.loads(self.rfile.read(length))

        if self.path == '/api/push-subscribe':
            save_subscription(body)
            self._respond(200, {"ok": True})

        elif self.path == '/api/push-send':
            try:
                send_push(
                    title=body.get('title', '通知'),
                    body=body.get('body', ''),
                    url=body.get('url', '/')
                )
                self._respond(200, {"ok": True})
            except Exception as e:
                self._respond(500, {"error": str(e)})
        else:
            self._respond(404, {"error": "not found"})

    def _respond(self, code, data):
        self.send_response(code)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(json.dumps(data).encode())

    def do_OPTIONS(self):
        self.send_response(204)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()

if __name__ == '__main__':
    print(f"🚀 Push server running on http://localhost:{PORT}")
    print("📮 POST /api/push-subscribe  - 保存订阅")
    print("📮 POST /api/push-send       - 发送推送")
    print()
    print("测试推送:")
    print(f'  curl -X POST http://localhost:{PORT}/api/push-send \\')
    print('    -H "Content-Type: application/json" \\')
    print('    -d \'{"title":"Hello","body":"你的第一条推送！"}\'')
    HTTPServer(('', PORT), Handler).serve_forever()
