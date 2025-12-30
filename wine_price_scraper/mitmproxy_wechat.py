
# mitmproxy_wechat.py
# 使用方法: mitmproxy -s mitmproxy_wechat.py
# 然后在手机上设置代理，打开微信公众号历史文章页面

import json
import sqlite3
from mitmproxy import http
from datetime import datetime

# 数据库路径
DB_PATH = "wechat_articles.db"

def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS articles (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT,
            url TEXT UNIQUE,
            publish_time TEXT,
            digest TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    conn.close()

init_db()

def response(flow: http.HTTPFlow) -> None:
    """拦截微信公众号历史文章接口"""

    # 公众号历史文章接口
    if "mp.weixin.qq.com/mp/profile_ext" in flow.request.url:
        if "action=getmsg" in flow.request.url:
            try:
                data = json.loads(flow.response.text)
                if data.get("ret") == 0:
                    general_msg_list = json.loads(data.get("general_msg_list", "{}"))
                    articles = general_msg_list.get("list", [])

                    conn = sqlite3.connect(DB_PATH)
                    cursor = conn.cursor()

                    for item in articles:
                        app_msg_ext_info = item.get("app_msg_ext_info", {})
                        title = app_msg_ext_info.get("title", "")
                        url = app_msg_ext_info.get("content_url", "")
                        digest = app_msg_ext_info.get("digest", "")
                        publish_time = item.get("comm_msg_info", {}).get("datetime", 0)

                        if title and url:
                            try:
                                cursor.execute("""
                                    INSERT OR IGNORE INTO articles (title, url, publish_time, digest)
                                    VALUES (?, ?, ?, ?)
                                """, (title, url, datetime.fromtimestamp(publish_time).strftime("%Y-%m-%d"), digest))
                                print(f"[+] 保存文章: {title}")
                            except Exception as e:
                                print(f"[-] 保存失败: {e}")

                        # 处理多图文
                        multi_items = app_msg_ext_info.get("multi_app_msg_item_list", [])
                        for sub_item in multi_items:
                            sub_title = sub_item.get("title", "")
                            sub_url = sub_item.get("content_url", "")
                            sub_digest = sub_item.get("digest", "")

                            if sub_title and sub_url:
                                try:
                                    cursor.execute("""
                                        INSERT OR IGNORE INTO articles (title, url, publish_time, digest)
                                        VALUES (?, ?, ?, ?)
                                    """, (sub_title, sub_url, datetime.fromtimestamp(publish_time).strftime("%Y-%m-%d"), sub_digest))
                                    print(f"[+] 保存文章: {sub_title}")
                                except Exception as e:
                                    print(f"[-] 保存失败: {e}")

                    conn.commit()
                    conn.close()

            except Exception as e:
                print(f"解析失败: {e}")
