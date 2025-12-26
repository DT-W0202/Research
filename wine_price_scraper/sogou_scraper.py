#!/usr/bin/env python3
"""
通过搜狗微信搜索抓取"不二酱"公众号文章
"""

import re
import time
import json
import sqlite3
import requests
from datetime import datetime, timedelta
from bs4 import BeautifulSoup
from urllib.parse import urlencode, unquote
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')
logger = logging.getLogger(__name__)


class SogouWeChatScraper:
    """搜狗微信搜索抓取器"""

    def __init__(self, db_path: str = "buerjjiang_wine.db"):
        self.db_path = db_path
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
            'Referer': 'https://weixin.sogou.com/',
        })
        self._init_db()

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

    def search_articles(self, query: str = "不二酱 茅台", pages: int = 3) -> list:
        """搜索文章"""
        articles = []

        for page in range(1, pages + 1):
            logger.info(f"搜索第 {page} 页...")

            params = {
                'type': 2,  # 文章搜索
                'query': query,
                'page': page,
                'ie': 'utf8',
            }

            url = f"https://weixin.sogou.com/weixin?{urlencode(params)}"

            try:
                resp = self.session.get(url, timeout=30)
                resp.encoding = 'utf-8'

                if resp.status_code == 200:
                    soup = BeautifulSoup(resp.text, 'html.parser')

                    # 查找文章列表
                    items = soup.find_all('div', class_='txt-box')

                    for item in items:
                        try:
                            # 标题和链接
                            title_elem = item.find('a')
                            if not title_elem:
                                continue

                            title = title_elem.get_text(strip=True)
                            href = title_elem.get('href', '')

                            # 时间
                            time_elem = item.find('span', class_='s2')
                            pub_time = ''
                            if time_elem:
                                time_script = time_elem.find('script')
                                if time_script:
                                    match = re.search(r"timeConvert\('(\d+)'\)", str(time_script))
                                    if match:
                                        ts = int(match.group(1))
                                        pub_time = datetime.fromtimestamp(ts).strftime('%Y-%m-%d')

                            # 摘要
                            digest_elem = item.find('p', class_='txt-info')
                            digest = digest_elem.get_text(strip=True) if digest_elem else ''

                            articles.append({
                                'title': title,
                                'url': href,
                                'publish_date': pub_time,
                                'digest': digest
                            })

                        except Exception as e:
                            continue

                    logger.info(f"  找到 {len(items)} 条结果")

                else:
                    logger.warning(f"请求失败: {resp.status_code}")

            except Exception as e:
                logger.error(f"搜索出错: {e}")

            time.sleep(2)  # 避免请求过快

        return articles

    def get_real_url(self, sogou_url: str) -> str:
        """获取真实的微信文章URL"""
        try:
            resp = self.session.get(sogou_url, timeout=30, allow_redirects=False)

            # 搜狗会返回302重定向到真实URL
            if resp.status_code == 302:
                return resp.headers.get('Location', sogou_url)

            # 或者从页面中提取
            if 'url' in resp.text:
                match = re.search(r"url\s*['\"]:\s*['\"]([^'\"]+)['\"]", resp.text)
                if match:
                    return unquote(match.group(1))

        except Exception as e:
            logger.error(f"获取真实URL失败: {e}")

        return sogou_url

    def scrape_article_content(self, url: str) -> dict:
        """抓取文章内容"""
        try:
            resp = self.session.get(url, timeout=30)
            resp.encoding = 'utf-8'

            if resp.status_code != 200:
                return None

            soup = BeautifulSoup(resp.text, 'html.parser')

            # 标题
            title_elem = soup.find('h1', class_='rich_media_title') or soup.find('h1')
            title = title_elem.get_text(strip=True) if title_elem else ''

            # 发布时间
            time_elem = soup.find('em', id='publish_time')
            pub_time = time_elem.get_text(strip=True) if time_elem else ''

            # 正文
            content_elem = soup.find('div', id='js_content')
            content = content_elem.get_text(separator='\n', strip=True) if content_elem else ''

            return {
                'title': title,
                'url': url,
                'publish_date': pub_time,
                'content': content
            }

        except Exception as e:
            logger.error(f"抓取文章失败: {e}")
            return None

    def extract_prices(self, content: str, title: str, url: str, pub_date: str) -> list:
        """提取酒价"""
        prices = []

        wine_keywords = [
            '茅台', '飞天', '五粮液', '国窖', '青花郎', '习酒',
            '珍酒', '金沙', '钓鱼台', '王子', '迎宾', '生肖',
            '原箱', '散瓶', '散飞', '龙年', '兔年', '虎年', '牛年',
        ]

        patterns = [
            r'([\u4e00-\u9fa5]+(?:[（(][^）)]+[）)])?)\s+(\d{3,5})\s*([↑↓][0-9]*)?',
            r'([\u4e00-\u9fa5]+)\s*[：:]\s*(\d{3,5})\s*元',
        ]

        seen = set()

        for pattern in patterns:
            for match in re.findall(pattern, content):
                name = match[0].strip()
                try:
                    price = float(match[1])
                except:
                    continue

                change = match[2] if len(match) > 2 else ''

                if price < 200 or price > 30000:
                    continue

                if not any(kw in name for kw in wine_keywords):
                    continue

                key = f"{name}_{price}"
                if key in seen:
                    continue
                seen.add(key)

                prices.append({
                    'name': name,
                    'price': price,
                    'change': change,
                    'source_title': title,
                    'source_url': url,
                    'publish_date': pub_date
                })

        return prices

    def save_to_db(self, articles: list, prices: list):
        """保存到数据库"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        for a in articles:
            try:
                cursor.execute('''
                    INSERT OR IGNORE INTO articles (title, url, publish_date, content, processed)
                    VALUES (?, ?, ?, ?, 1)
                ''', (a.get('title', ''), a.get('url', ''), a.get('publish_date', ''), a.get('content', '')))
            except:
                pass

        for p in prices:
            try:
                cursor.execute('''
                    INSERT INTO wine_prices (name, price, unit, change, source_title, source_url, publish_date)
                    VALUES (?, ?, '元/瓶', ?, ?, ?, ?)
                ''', (p['name'], p['price'], p.get('change', ''), p['source_title'], p['source_url'], p['publish_date']))
            except:
                pass

        conn.commit()
        conn.close()

    def run(self, query: str = "不二酱", pages: int = 5):
        """运行抓取"""
        logger.info(f"开始搜索: {query}")

        # 搜索文章
        search_results = self.search_articles(query, pages)
        logger.info(f"搜索到 {len(search_results)} 篇文章")

        all_articles = []
        all_prices = []

        for i, item in enumerate(search_results):
            logger.info(f"[{i+1}/{len(search_results)}] {item['title'][:40]}...")

            # 获取真实URL
            real_url = self.get_real_url(item['url'])

            # 抓取内容
            article = self.scrape_article_content(real_url)

            if article and article.get('content'):
                all_articles.append(article)

                # 提取价格
                prices = self.extract_prices(
                    article['content'],
                    article['title'],
                    article['url'],
                    article['publish_date']
                )

                if prices:
                    all_prices.extend(prices)
                    for p in prices:
                        logger.info(f"  -> {p['name']}: {p['price']}元 {p.get('change', '')}")

            time.sleep(2)

        # 保存
        self.save_to_db(all_articles, all_prices)

        logger.info(f"\n完成! 抓取 {len(all_articles)} 篇文章, 提取 {len(all_prices)} 条价格")

        return all_articles, all_prices


def main():
    scraper = SogouWeChatScraper()

    print("=" * 60)
    print("通过搜狗微信搜索抓取'不二酱'酒价")
    print("=" * 60)

    # 多个搜索词
    queries = [
        "不二酱 茅台行情",
        "不二酱 酒价",
        "不二酱 飞天",
    ]

    all_prices = []

    for query in queries:
        print(f"\n搜索: {query}")
        print("-" * 40)
        _, prices = scraper.run(query, pages=3)
        all_prices.extend(prices)
        time.sleep(3)

    # 显示结果
    print("\n" + "=" * 60)
    print("抓取结果汇总")
    print("=" * 60)

    # 去重并按日期排序
    unique_prices = {}
    for p in all_prices:
        key = f"{p['publish_date']}_{p['name']}_{p['price']}"
        if key not in unique_prices:
            unique_prices[key] = p

    sorted_prices = sorted(unique_prices.values(), key=lambda x: x.get('publish_date', ''), reverse=True)

    current_date = None
    for p in sorted_prices[:50]:
        if p['publish_date'] != current_date:
            current_date = p['publish_date']
            print(f"\n【{current_date or '未知日期'}】")

        change = f" {p['change']}" if p.get('change') else ""
        print(f"  {p['name']}: {p['price']}元{change}")


if __name__ == "__main__":
    main()
