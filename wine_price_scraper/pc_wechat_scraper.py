#!/usr/bin/env python3
"""
微信PC端抓包方案 - 获取"不二酱"公众号文章

这是最简单可行的方案：
1. 使用 Fiddler/Charles 抓取微信PC端的HTTPS请求
2. 导出文章链接
3. 用本脚本批量抓取文章内容并提取酒价

详细步骤见下方说明。
"""

import re
import json
import time
import sqlite3
import requests
from datetime import datetime
from bs4 import BeautifulSoup
from dataclasses import dataclass
from typing import List, Optional, Dict
import logging
import csv

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@dataclass
class WinePrice:
    """酒价数据"""
    name: str
    price: float
    unit: str
    change: Optional[str]  # 涨跌
    source_title: str
    source_url: str
    publish_date: str


class BuerjiangScraper:
    """不二酱公众号酒价抓取器"""

    def __init__(self, db_path: str = "buerjjiang_wine.db"):
        self.db_path = db_path
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 MicroMessenger/7.0.20.1781(0x6700143B) NetType/WIFI MiniProgramEnv/Windows WindowsWechat/WMPF WindowsWechat(0x63090a13)',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
        })
        self._init_db()

        # 酒名关键词
        self.wine_keywords = [
            '茅台', '飞天', '五粮液', '国窖1573', '青花郎', '红花郎',
            '习酒', '珍酒', '金沙', '钓鱼台', '汉酱', '赖茅',
            '王子', '迎宾', '生肖', '精品', '原箱', '散瓶', '散飞',
            '牛年', '虎年', '兔年', '龙年', '蛇年', '马年',
            '羊年', '猴年', '鸡年', '狗年', '猪年', '鼠年',
        ]

    def _init_db(self):
        """初始化数据库"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS articles (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                url TEXT UNIQUE,
                publish_date TEXT,
                content TEXT,
                processed INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS wine_prices (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                price REAL NOT NULL,
                unit TEXT DEFAULT '元/瓶',
                change TEXT,
                source_title TEXT,
                source_url TEXT,
                publish_date TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        conn.commit()
        conn.close()

    def import_urls_from_file(self, filepath: str) -> int:
        """从文件导入文章URL（每行一个URL）"""
        count = 0
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        with open(filepath, 'r', encoding='utf-8') as f:
            for line in f:
                url = line.strip()
                if url and 'mp.weixin.qq.com' in url:
                    try:
                        cursor.execute('''
                            INSERT OR IGNORE INTO articles (title, url)
                            VALUES (?, ?)
                        ''', ('待抓取', url))
                        if cursor.rowcount > 0:
                            count += 1
                    except:
                        pass

        conn.commit()
        conn.close()
        logger.info(f"导入了 {count} 个新URL")
        return count

    def import_urls_from_json(self, filepath: str) -> int:
        """从JSON文件导入（Fiddler/Charles导出格式）"""
        count = 0
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)

        # 支持多种JSON格式
        urls = []
        if isinstance(data, list):
            for item in data:
                if isinstance(item, str):
                    urls.append(item)
                elif isinstance(item, dict):
                    urls.append(item.get('url') or item.get('content_url', ''))
        elif isinstance(data, dict):
            # 微信接口格式
            if 'general_msg_list' in str(data):
                msg_list = data.get('general_msg_list', {})
                if isinstance(msg_list, str):
                    msg_list = json.loads(msg_list)
                for item in msg_list.get('list', []):
                    app_msg = item.get('app_msg_ext_info', {})
                    if app_msg.get('content_url'):
                        urls.append(app_msg['content_url'])
                    for sub in app_msg.get('multi_app_msg_item_list', []):
                        if sub.get('content_url'):
                            urls.append(sub['content_url'])

        for url in urls:
            url = url.replace('\\', '').strip()
            if url and 'mp.weixin.qq.com' in url:
                try:
                    cursor.execute('''
                        INSERT OR IGNORE INTO articles (title, url)
                        VALUES (?, ?)
                    ''', ('待抓取', url))
                    if cursor.rowcount > 0:
                        count += 1
                except:
                    pass

        conn.commit()
        conn.close()
        logger.info(f"从JSON导入了 {count} 个新URL")
        return count

    def scrape_article(self, url: str) -> Optional[Dict]:
        """抓取单篇文章"""
        try:
            resp = self.session.get(url, timeout=30)
            resp.encoding = 'utf-8'

            if resp.status_code != 200:
                logger.warning(f"请求失败 {resp.status_code}: {url[:50]}")
                return None

            soup = BeautifulSoup(resp.text, 'html.parser')

            # 提取标题
            title_elem = soup.find('h1', class_='rich_media_title') or soup.find('h1')
            title = title_elem.get_text(strip=True) if title_elem else '未知标题'

            # 提取发布时间
            time_elem = soup.find('em', id='publish_time') or soup.find(class_='publish_time')
            publish_date = time_elem.get_text(strip=True) if time_elem else ''

            # 提取正文
            content_elem = soup.find('div', id='js_content') or soup.find(class_='rich_media_content')
            content = content_elem.get_text(separator='\n', strip=True) if content_elem else ''

            return {
                'title': title,
                'url': url,
                'publish_date': publish_date,
                'content': content
            }

        except Exception as e:
            logger.error(f"抓取失败: {e}")
            return None

    def extract_prices_from_content(self, content: str, title: str, url: str, publish_date: str) -> List[WinePrice]:
        """从文章内容提取酒价"""
        prices = []

        # 匹配模式
        patterns = [
            # 表格格式: 飞天(散) 2320 ↓80
            r'([\u4e00-\u9fa5]+(?:[（(][^）)]+[）)])?)\s+(\d{3,5})\s*([↑↓]?\d*)?',
            # 标准格式: 茅台飞天 2320元/瓶
            r'([\u4e00-\u9fa5]+)\s*[：:]\s*(\d{3,5})\s*元?/?瓶?',
            # 行情价位格式
            r'([\u4e00-\u9fa5]+(?:散瓶|原箱|散飞)?)\s*(?:行情|批发|参考)?价[位为是：:]*\s*(\d{3,5})',
        ]

        seen = set()  # 去重

        for pattern in patterns:
            matches = re.findall(pattern, content)
            for match in matches:
                name = match[0].strip()
                try:
                    price = float(match[1])
                except (ValueError, IndexError):
                    continue

                # 涨跌幅
                change = match[2] if len(match) > 2 else ''

                # 过滤
                if price < 200 or price > 30000:
                    continue

                # 检查是否是酒类
                is_wine = any(kw in name for kw in self.wine_keywords)
                if not is_wine:
                    continue

                # 去重
                key = f"{name}_{price}"
                if key in seen:
                    continue
                seen.add(key)

                prices.append(WinePrice(
                    name=name,
                    price=price,
                    unit='元/瓶',
                    change=change or None,
                    source_title=title,
                    source_url=url,
                    publish_date=publish_date
                ))

        return prices

    def process_all_articles(self, delay: float = 2.0):
        """处理所有未处理的文章"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('SELECT url FROM articles WHERE processed = 0')
        urls = [row[0] for row in cursor.fetchall()]
        conn.close()

        logger.info(f"待处理文章: {len(urls)} 篇")

        for i, url in enumerate(urls):
            logger.info(f"[{i+1}/{len(urls)}] 正在处理...")

            article = self.scrape_article(url)
            if article:
                # 提取价格
                prices = self.extract_prices_from_content(
                    article['content'],
                    article['title'],
                    article['url'],
                    article['publish_date']
                )

                # 保存
                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()

                # 更新文章
                cursor.execute('''
                    UPDATE articles SET title=?, publish_date=?, content=?, processed=1
                    WHERE url=?
                ''', (article['title'], article['publish_date'], article['content'], url))

                # 保存价格
                for p in prices:
                    cursor.execute('''
                        INSERT INTO wine_prices (name, price, unit, change, source_title, source_url, publish_date)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                    ''', (p.name, p.price, p.unit, p.change, p.source_title, p.source_url, p.publish_date))
                    logger.info(f"  提取: {p.name} {p.price}元 {p.change or ''}")

                conn.commit()
                conn.close()

            time.sleep(delay)

    def export_to_csv(self, filepath: str = "wine_prices.csv"):
        """导出价格数据到CSV"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            SELECT name, price, unit, change, publish_date, source_title
            FROM wine_prices
            ORDER BY publish_date DESC, name
        ''')
        rows = cursor.fetchall()
        conn.close()

        with open(filepath, 'w', newline='', encoding='utf-8-sig') as f:
            writer = csv.writer(f)
            writer.writerow(['酒名', '价格', '单位', '涨跌', '日期', '来源'])
            writer.writerows(rows)

        logger.info(f"已导出 {len(rows)} 条记录到 {filepath}")

    def get_latest_prices(self, limit: int = 50) -> List[Dict]:
        """获取最新价格"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            SELECT name, price, unit, change, publish_date, source_title
            FROM wine_prices
            ORDER BY created_at DESC
            LIMIT ?
        ''', (limit,))
        rows = cursor.fetchall()
        conn.close()

        return [
            {'name': r[0], 'price': r[1], 'unit': r[2],
             'change': r[3], 'date': r[4], 'source': r[5]}
            for r in rows
        ]

    def print_stats(self):
        """打印统计信息"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('SELECT COUNT(*) FROM articles')
        article_count = cursor.fetchone()[0]

        cursor.execute('SELECT COUNT(*) FROM articles WHERE processed = 1')
        processed_count = cursor.fetchone()[0]

        cursor.execute('SELECT COUNT(*) FROM wine_prices')
        price_count = cursor.fetchone()[0]

        conn.close()

        print(f"\n{'='*40}")
        print(f"文章总数: {article_count}")
        print(f"已处理:   {processed_count}")
        print(f"酒价记录: {price_count}")
        print(f"{'='*40}\n")


def print_instructions():
    """打印使用说明"""
    print("""
╔══════════════════════════════════════════════════════════════════╗
║          不二酱公众号酒价抓取工具 - 使用指南                      ║
╠══════════════════════════════════════════════════════════════════╣
║                                                                   ║
║  【推荐方案】使用 Fiddler 抓取微信PC端                            ║
║                                                                   ║
║  步骤1: 下载安装 Fiddler Classic (免费)                           ║
║         https://www.telerik.com/download/fiddler                 ║
║                                                                   ║
║  步骤2: 配置 Fiddler 解密HTTPS                                    ║
║         Tools → Options → HTTPS                                  ║
║         勾选 "Decrypt HTTPS traffic"                             ║
║         点击 "Actions" → "Trust Root Certificate"                ║
║                                                                   ║
║  步骤3: 打开微信PC端，进入"不二酱"公众号                           ║
║         点击公众号头像 → 查看历史消息                              ║
║         慢慢向下滚动加载更多文章                                   ║
║                                                                   ║
║  步骤4: 在 Fiddler 中筛选请求                                     ║
║         右侧面板搜索: mp.weixin.qq.com/mp/profile_ext             ║
║         找到包含 action=getmsg 的请求                             ║
║         右键 → Copy → Just URL 或 Save Response Body             ║
║                                                                   ║
║  步骤5: 将URL保存到 urls.txt，然后运行:                            ║
║         python pc_wechat_scraper.py                              ║
║                                                                   ║
╚══════════════════════════════════════════════════════════════════╝
""")


def main():
    import sys

    print_instructions()

    scraper = BuerjiangScraper()

    # 命令行参数处理
    if len(sys.argv) > 1:
        cmd = sys.argv[1]

        if cmd == 'import' and len(sys.argv) > 2:
            filepath = sys.argv[2]
            if filepath.endswith('.json'):
                scraper.import_urls_from_json(filepath)
            else:
                scraper.import_urls_from_file(filepath)

        elif cmd == 'scrape':
            scraper.process_all_articles()

        elif cmd == 'export':
            scraper.export_to_csv()

        elif cmd == 'stats':
            scraper.print_stats()

        elif cmd == 'show':
            prices = scraper.get_latest_prices(30)
            print("\n最新酒价:")
            print("-" * 60)
            for p in prices:
                change_str = f" {p['change']}" if p['change'] else ""
                print(f"{p['date']} | {p['name']}: {p['price']}{p['unit']}{change_str}")

    else:
        print("""
使用方法:
  python pc_wechat_scraper.py import urls.txt   # 导入URL文件
  python pc_wechat_scraper.py import data.json  # 导入JSON文件
  python pc_wechat_scraper.py scrape            # 抓取所有文章
  python pc_wechat_scraper.py export            # 导出CSV
  python pc_wechat_scraper.py stats             # 查看统计
  python pc_wechat_scraper.py show              # 显示最新价格
""")

    scraper.print_stats()


if __name__ == "__main__":
    main()
