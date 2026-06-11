#!/bin/bash
# 一键生成 VAPID 密钥对

echo "📦 安装 pywebpush..."
pip install pywebpush --quiet

echo ""
echo "🔑 生成 VAPID 密钥对..."
vapid --gen

echo ""
echo "📋 你的 Application Server Key（前端用）："
vapid --applicationServerKey

echo ""
echo "✅ 生成完成！"
echo "   private_key.pem → 服务端用，不要泄露"
echo "   public_key.pem  → 备份用"
echo "   上面输出的 Base64 字符串 → 粘贴到 subscribe.js 的 VAPID_PUBLIC_KEY"
