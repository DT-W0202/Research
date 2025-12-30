#!/usr/bin/env python3
"""
微信公众号"不二酱"酒价抓取工具

抓取微信公众号文章有以下几种方法：
1. 通过抓包获取公众号历史文章接口 (推荐)
2. 通过搜狗微信搜索
3. 手动获取文章链接后批量抓取

本脚本提供多种方式帮助你抓取酒价数据。
"""

import re
import json
import time
import sqlite3
import requests
from datetime import datetime
from pathlib import Path
from dataclasses import dataclass, asdict
from typing import Optional, List, Dict
from urllib.parse import urlencode, quote
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

@dataclass
class WinePrice:
    """酒价数据结构"""
    name: str               # 酒名
    price: float           # 价格
    unit: str              # 单位 (元/瓶, 元/箱)
    source: str            # 来源 (文章标题)
    publish_date: str      # 发布日期
    scrape_time: str       # 抓取时间
    change: Optional[float] = None  # 涨跌幅

@dataclass
class Article:
    """公众号文章数据结构"""
    title: str
    url: str
    publish_time: str
    content: Optional[str] = None


class WinePriceDatabase:
    """SQLite数据库存储酒价数据"""

    def __init__(self, db_path: str = "wine_prices.db"):
        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        """初始化数据库表"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # 创建酒价表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS wine_prices (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                price REAL NOT NULL,
                unit TEXT,
                source TEXT,
                publish_date TEXT,
                scrape_time TEXT,
                change REAL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # 创建文章表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS articles (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                url TEXT UNIQUE,
                publish_time TEXT,
                content TEXT,
                scraped INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        conn.commit()
        conn.close()

    def save_price(self, price: WinePrice):
        """保存酒价数据"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO wine_prices (name, price, unit, source, publish_date, scrape_time, change)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (price.name, price.price, price.unit, price.source,
              price.publish_date, price.scrape_time, price.change))
        conn.commit()
        conn.close()

    def save_article(self, article: Article):
        """保存文章数据"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        try:
            cursor.execute('''
                INSERT OR IGNORE INTO articles (title, url, publish_time, content)
                VALUES (?, ?, ?, ?)
            ''', (article.title, article.url, article.publish_time, article.content))
            conn.commit()
        except sqlite3.IntegrityError:
            pass
        finally:
            conn.close()

    def get_latest_prices(self, limit: int = 100) -> List[Dict]:
        """获取最新酒价"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            SELECT name, price, unit, source, publish_date, scrape_time, change
            FROM wine_prices
            ORDER BY created_at DESC
            LIMIT ?
        ''', (limit,))
        rows = cursor.fetchall()
        conn.close()

        return [
            {
                'name': r[0], 'price': r[1], 'unit': r[2],
                'source': r[3], 'publish_date': r[4],
                'scrape_time': r[5], 'change': r[6]
            }
            for r in rows
        ]


class WeChatArticleScraper:
    """
    微信公众号文章抓取器

    使用方法1: 抓包获取cookie和token后自动抓取
    使用方法2: 手动提供文章链接列表
    """

    def __init__(self):
        self.db = WinePriceDatabase()
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        })

        # 常见酒名关键词
        self.wine_keywords = [
            '茅台', '飞天', '五粮液', '国窖', '汾酒', '洋河',
            '剑南春', '郎酒', '习酒', '青花郎', '珍酒', '金沙',
            '钓鱼台', '摘要', '生肖', '原箱', '散瓶', '散飞',
        ]

        # 价格匹配正则表达式
        self.price_patterns = [
            # 匹配: 茅台飞天 2320元/瓶
            r'([\u4e00-\u9fa5]+(?:酒|茅台|飞天|五粮液)?[\u4e00-\u9fa5]*)\s*[：:]*\s*(\d+(?:\.\d+)?)\s*元[/／]?(瓶|箱)?',
            # 匹配: 飞天散瓶 2320
            r'(飞天|茅台|[\u4e00-\u9fa5]*酒[\u4e00-\u9fa5]*)\s*[：:]*\s*(\d{3,5})\s*(元)?',
            # 匹配: 2024年飞天茅台散瓶行情价位2430元
            r'(\d{4}年?[\u4e00-\u9fa5]+)\s*(?:行情)?(?:价位?|批发价|参考价)[为是：:]*\s*(\d+(?:\.\d+)?)\s*元',
            # 匹配表格格式: |飞天(散)|2320|
            r'\|\s*([\u4e00-\u9fa5（）\(\)]+)\s*\|\s*(\d+(?:\.\d+)?)\s*\|',
        ]

    def scrape_article_content(self, url: str) -> Optional[str]:
        """抓取文章内容"""
        try:
            # 微信文章需要特殊处理
            resp = self.session.get(url, timeout=30)
            resp.encoding = 'utf-8'

            if resp.status_code == 200:
                # 提取正文内容
                content = resp.text

                # 移除HTML标签，保留文本
                import re
                # 提取js_content区域的内容
                match = re.search(r'id="js_content"[^>]*>(.*?)</div>', content, re.DOTALL)
                if match:
                    text = match.group(1)
                    # 清理HTML标签
                    text = re.sub(r'<[^>]+>', ' ', text)
                    text = re.sub(r'\s+', ' ', text)
                    return text.strip()

                return content
            else:
                logger.warning(f"请求失败: {resp.status_code}")
                return None

        except Exception as e:
            logger.error(f"抓取文章失败: {e}")
            return None

    def extract_prices(self, text: str, source: str = "", publish_date: str = "") -> List[WinePrice]:
        """从文本中提取酒价信息"""
        prices = []
        scrape_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        for pattern in self.price_patterns:
            matches = re.findall(pattern, text)
            for match in matches:
                if len(match) >= 2:
                    name = match[0].strip()
                    try:
                        price = float(match[1])
                    except ValueError:
                        continue

                    unit = match[2] if len(match) > 2 and match[2] else '元/瓶'
                    if not unit.startswith('元'):
                        unit = f'元/{unit}'

                    # 过滤明显不是酒价的数据
                    if price < 100 or price > 50000:
                        continue

                    # 检查是否包含酒类关键词
                    is_wine = any(kw in name for kw in self.wine_keywords)
                    if not is_wine and '酒' not in name:
                        continue

                    wine_price = WinePrice(
                        name=name,
                        price=price,
                        unit=unit,
                        source=source,
                        publish_date=publish_date,
                        scrape_time=scrape_time
                    )
                    prices.append(wine_price)

        return prices

    def process_article_urls(self, urls: List[str]):
        """处理文章URL列表"""
        for url in urls:
            logger.info(f"正在处理: {url}")

            content = self.scrape_article_content(url)
            if content:
                prices = self.extract_prices(content, source=url)
                for price in prices:
                    self.db.save_price(price)
                    logger.info(f"提取价格: {price.name} - {price.price}{price.unit}")

            time.sleep(2)  # 避免请求过快


class SogouWeChatScraper:
    """
    搜狗微信搜索抓取器

    通过搜狗微信搜索获取公众号文章
    注意: 搜狗可能会有反爬虫限制
    """

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
        })
        self.base_url = 'https://weixin.sogou.com'

    def search_articles(self, query: str, page: int = 1) -> List[Dict]:
        """搜索公众号文章"""
        params = {
            'type': 2,  # 文章搜索
            'query': query,
            'page': page,
        }

        url = f"{self.base_url}/weixin?{urlencode(params)}"

        try:
            resp = self.session.get(url, timeout=30)
            resp.encoding = 'utf-8'

            if resp.status_code == 200:
                # 解析搜索结果
                articles = self._parse_search_results(resp.text)
                return articles
            else:
                logger.warning(f"搜索请求失败: {resp.status_code}")
                return []

        except Exception as e:
            logger.error(f"搜索失败: {e}")
            return []

    def _parse_search_results(self, html: str) -> List[Dict]:
        """解析搜索结果页面"""
        articles = []

        # 使用正则提取文章信息
        # 标题
        title_pattern = r'<a[^>]*href="([^"]*)"[^>]*>([^<]+)</a>'
        # 时间
        time_pattern = r'timeConvert\(\'(\d+)\'\)'

        titles = re.findall(r'class="txt-box"[^>]*>.*?<a[^>]*href="([^"]*)"[^>]*uigs="article_title[^"]*"[^>]*>([^<]+)</a>', html, re.DOTALL)
        times = re.findall(time_pattern, html)

        for i, (url, title) in enumerate(titles):
            article = {
                'title': title.strip(),
                'url': url,
                'publish_time': datetime.fromtimestamp(int(times[i])).strftime('%Y-%m-%d') if i < len(times) else ''
            }
            articles.append(article)

        return articles

    def search_buerjang(self, keyword: str = "不二酱 茅台价格") -> List[Dict]:
        """搜索不二酱相关文章"""
        return self.search_articles(keyword)


class MitmproxyHelper:
    """
    mitmproxy抓包辅助类

    用于生成mitmproxy脚本，抓取微信公众号历史文章接口
    """

    @staticmethod
    def generate_script() -> str:
        """生成mitmproxy抓包脚本"""
        script = '''
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
'''
        return script

    @staticmethod
    def save_script(path: str = "mitmproxy_wechat.py"):
        """保存mitmproxy脚本到文件"""
        script = MitmproxyHelper.generate_script()
        with open(path, 'w', encoding='utf-8') as f:
            f.write(script)
        print(f"脚本已保存到: {path}")


def main():
    """主函数 - 演示用法"""
    print("=" * 60)
    print("微信公众号'不二酱'酒价抓取工具")
    print("=" * 60)
    print()

    print("【方法1】抓包方式 (推荐)")
    print("-" * 40)
    print("1. 安装 mitmproxy: pip install mitmproxy")
    print("2. 运行脚本生成抓包工具")
    print("3. 在手机上设置代理，指向电脑IP")
    print("4. 打开微信，进入'不二酱'公众号")
    print("5. 点击'历史文章'，慢慢滚动加载")
    print("6. 文章链接会自动保存到数据库")
    print()

    # 生成mitmproxy脚本
    MitmproxyHelper.save_script()
    print()

    print("【方法2】手动导入文章链接")
    print("-" * 40)
    print("如果你已经有文章链接，可以直接导入处理:")
    print()

    # 示例: 处理文章链接
    scraper = WeChatArticleScraper()

    # 示例文章URL (需要替换为真实的文章链接)
    example_urls = [
        # "https://mp.weixin.qq.com/s/xxxxx",
    ]

    if example_urls:
        scraper.process_article_urls(example_urls)

    print("【方法3】通过搜狗微信搜索")
    print("-" * 40)
    print("注意: 搜狗搜索有反爬虫限制，可能需要验证码")
    print()

    # sogou = SogouWeChatScraper()
    # articles = sogou.search_buerjang()
    # print(f"找到 {len(articles)} 篇文章")

    print()
    print("=" * 60)
    print("提示: 请查看 README.md 获取详细使用说明")
    print("=" * 60)


if __name__ == "__main__":
    main()
