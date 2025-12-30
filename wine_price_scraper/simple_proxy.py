#!/usr/bin/env python3
"""
简易HTTPS代理服务器 - 用于抓取微信公众号文章链接

使用方法:
1. 运行此脚本: python simple_proxy.py
2. 在手机WiFi设置中配置HTTP代理，指向电脑IP，端口8888
3. 打开微信，进入公众号历史文章页面
4. 滚动加载文章，链接会自动保存

注意: 此脚本仅抓取HTTP请求，微信大部分是HTTPS
      完整抓包建议使用 Charles/Fiddler 等专业工具
"""

import socket
import threading
import sqlite3
import json
import re
from datetime import datetime
from urllib.parse import urlparse, parse_qs
import ssl

# 配置
PROXY_HOST = '0.0.0.0'
PROXY_PORT = 8888
DB_PATH = 'wechat_articles.db'

def init_db():
    """初始化数据库"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS articles (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT,
            url TEXT UNIQUE,
            publish_time TEXT,
            digest TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()
    print(f"[*] 数据库已初始化: {DB_PATH}")

def save_article(title, url, publish_time="", digest=""):
    """保存文章到数据库"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute('''
            INSERT OR IGNORE INTO articles (title, url, publish_time, digest)
            VALUES (?, ?, ?, ?)
        ''', (title, url, publish_time, digest))
        conn.commit()
        conn.close()
        if cursor.rowcount > 0:
            print(f"[+] 保存文章: {title[:50]}...")
            return True
    except Exception as e:
        print(f"[-] 保存失败: {e}")
    return False

def parse_wechat_response(data):
    """解析微信公众号历史文章接口响应"""
    try:
        # 尝试找到JSON数据
        json_match = re.search(r'\{.*"general_msg_list".*\}', data, re.DOTALL)
        if json_match:
            json_data = json.loads(json_match.group())
            if json_data.get("ret") == 0:
                msg_list = json.loads(json_data.get("general_msg_list", "{}"))
                articles = msg_list.get("list", [])

                for item in articles:
                    app_msg = item.get("app_msg_ext_info", {})
                    title = app_msg.get("title", "")
                    url = app_msg.get("content_url", "").replace("\\", "")
                    digest = app_msg.get("digest", "")
                    pub_time = item.get("comm_msg_info", {}).get("datetime", 0)

                    if title and url:
                        time_str = datetime.fromtimestamp(pub_time).strftime("%Y-%m-%d") if pub_time else ""
                        save_article(title, url, time_str, digest)

                    # 处理多图文
                    for sub in app_msg.get("multi_app_msg_item_list", []):
                        sub_title = sub.get("title", "")
                        sub_url = sub.get("content_url", "").replace("\\", "")
                        if sub_title and sub_url:
                            save_article(sub_title, sub_url, time_str, sub.get("digest", ""))

    except Exception as e:
        pass  # 静默处理非JSON响应

def handle_client(client_socket):
    """处理客户端连接"""
    try:
        request = client_socket.recv(8192).decode('utf-8', errors='ignore')

        # 解析请求
        first_line = request.split('\n')[0]
        method = first_line.split(' ')[0]

        if method == 'CONNECT':
            # HTTPS隧道请求
            host_port = first_line.split(' ')[1]
            host, port = host_port.split(':') if ':' in host_port else (host_port, 443)

            # 建立到目标服务器的连接
            server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            server_socket.connect((host, int(port)))

            # 发送连接成功响应
            client_socket.send(b'HTTP/1.1 200 Connection Established\r\n\r\n')

            # 双向转发数据
            def forward(src, dst):
                try:
                    while True:
                        data = src.recv(8192)
                        if not data:
                            break
                        dst.send(data)
                except:
                    pass

            t1 = threading.Thread(target=forward, args=(client_socket, server_socket))
            t2 = threading.Thread(target=forward, args=(server_socket, client_socket))
            t1.daemon = True
            t2.daemon = True
            t1.start()
            t2.start()
            t1.join()

        else:
            # HTTP请求
            url_match = re.search(r'(GET|POST) (\S+)', first_line)
            if url_match:
                url = url_match.group(2)
                parsed = urlparse(url)
                host = parsed.netloc or re.search(r'Host: (\S+)', request).group(1)

                # 检查是否是微信公众号接口
                if 'mp.weixin.qq.com' in host:
                    print(f"[*] 检测到微信请求: {url[:80]}...")

                # 转发请求到目标服务器
                server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                server_socket.connect((host, 80))
                server_socket.send(request.encode())

                # 接收响应
                response = b''
                while True:
                    data = server_socket.recv(8192)
                    if not data:
                        break
                    response += data
                    client_socket.send(data)

                # 解析微信响应
                if 'mp.weixin.qq.com' in host:
                    parse_wechat_response(response.decode('utf-8', errors='ignore'))

                server_socket.close()

    except Exception as e:
        pass
    finally:
        client_socket.close()

def get_local_ip():
    """获取本机局域网IP"""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except:
        return "127.0.0.1"

def main():
    init_db()

    local_ip = get_local_ip()

    print("=" * 60)
    print("微信公众号文章抓包代理服务器")
    print("=" * 60)
    print(f"\n[*] 代理服务器启动: {local_ip}:{PROXY_PORT}")
    print("\n手机设置步骤:")
    print(f"  1. 确保手机和电脑在同一WiFi网络")
    print(f"  2. 手机WiFi设置 → 配置代理 → 手动")
    print(f"  3. 服务器: {local_ip}")
    print(f"  4. 端口: {PROXY_PORT}")
    print(f"  5. 打开微信 → 进入公众号 → 查看历史消息")
    print(f"  6. 滚动加载更多文章")
    print("\n" + "=" * 60)
    print("注意: 微信使用HTTPS，此简易代理只能透传加密流量")
    print("完整抓包请使用: Charles / Fiddler / mitmproxy")
    print("=" * 60)
    print("\n按 Ctrl+C 停止服务器\n")

    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind((PROXY_HOST, PROXY_PORT))
    server.listen(100)

    try:
        while True:
            client, addr = server.accept()
            thread = threading.Thread(target=handle_client, args=(client,))
            thread.daemon = True
            thread.start()
    except KeyboardInterrupt:
        print("\n[*] 服务器已停止")

        # 显示抓取统计
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM articles")
        count = cursor.fetchone()[0]
        conn.close()
        print(f"[*] 共抓取 {count} 篇文章")

if __name__ == "__main__":
    main()
