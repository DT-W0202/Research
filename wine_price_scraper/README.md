# 微信公众号"不二酱"酒价抓取工具

抓取微信公众号"不二酱"发布的酒价数据（茅台、五粮液等白酒行情）。

## 背景

"不二酱"是一个专门追踪酱香型白酒价格行情的公众号，被多家财经媒体作为茅台酒批发价格的参考来源。

## 抓取方案

由于微信公众号的特殊性，内容不允许被搜索引擎直接抓取，主要有以下几种方式获取数据：

### 方法1: 抓包方式 (推荐)

使用 mitmproxy 拦截微信客户端请求，获取公众号历史文章接口数据。

**步骤:**

1. 安装依赖
```bash
pip install -r requirements.txt
```

2. 运行主脚本生成 mitmproxy 抓包脚本
```bash
python wechat_scraper.py
```

3. 启动 mitmproxy
```bash
mitmproxy -s mitmproxy_wechat.py
```

4. 配置手机代理
   - 手机和电脑连接同一WiFi
   - 在手机WiFi设置中配置HTTP代理，指向电脑IP，端口8080
   - 在手机浏览器访问 `http://mitm.it` 安装证书

5. 在微信中操作
   - 打开微信，搜索并关注"不二酱"公众号
   - 点击公众号头像 → 查看历史消息
   - 慢慢向下滚动，加载更多文章
   - mitmproxy 会自动抓取文章链接保存到 SQLite 数据库

6. 处理抓取到的文章
```python
from wechat_scraper import WeChatArticleScraper
import sqlite3

# 从数据库读取文章链接
conn = sqlite3.connect('wechat_articles.db')
cursor = conn.cursor()
cursor.execute('SELECT url FROM articles')
urls = [row[0] for row in cursor.fetchall()]
conn.close()

# 抓取文章内容并提取价格
scraper = WeChatArticleScraper()
scraper.process_article_urls(urls)
```

### 方法2: 手动导入文章链接

如果你已经有文章链接（比如从微信聊天记录中获取），可以直接处理：

```python
from wechat_scraper import WeChatArticleScraper

scraper = WeChatArticleScraper()

# 文章链接列表
urls = [
    "https://mp.weixin.qq.com/s/xxxxx",
    "https://mp.weixin.qq.com/s/yyyyy",
]

scraper.process_article_urls(urls)

# 查看提取的价格
prices = scraper.db.get_latest_prices()
for p in prices:
    print(f"{p['name']}: {p['price']} {p['unit']}")
```

### 方法3: 搜狗微信搜索

通过搜狗微信搜索获取公众号文章（有反爬限制）：

```python
from wechat_scraper import SogouWeChatScraper

sogou = SogouWeChatScraper()
articles = sogou.search_buerjang("不二酱 茅台价格")

for article in articles:
    print(f"{article['title']} - {article['publish_time']}")
```

## 数据存储

抓取的数据保存在 SQLite 数据库中：

- `wine_prices.db` - 酒价数据
- `wechat_articles.db` - 文章链接（mitmproxy抓取）

### 查看数据

```python
from wechat_scraper import WinePriceDatabase

db = WinePriceDatabase()
prices = db.get_latest_prices(limit=50)

for p in prices:
    print(f"{p['publish_date']} | {p['name']}: {p['price']} {p['unit']}")
```

## 自动化定时抓取

可以使用 cron (Linux/Mac) 或 Task Scheduler (Windows) 设置定时任务：

```bash
# 每天早上9点运行
0 9 * * * cd /path/to/wine_price_scraper && python wechat_scraper.py
```

## 注意事项

1. **频率限制**: 微信有反爬虫机制，请求频率不要太高，建议每次请求间隔2-5秒
2. **登录态**: 抓包获取的cookie有时效性，需要定期更新
3. **法律合规**: 请遵守相关法律法规，仅用于个人学习研究
4. **数据准确性**: 自动提取的价格可能有误差，重要数据请人工核实

## 文件结构

```
wine_price_scraper/
├── README.md              # 使用说明
├── requirements.txt       # Python依赖
├── wechat_scraper.py     # 主抓取脚本
├── mitmproxy_wechat.py   # mitmproxy抓包脚本（运行后自动生成）
├── wine_prices.db        # 酒价数据库（运行后生成）
└── wechat_articles.db    # 文章数据库（运行后生成）
```

## 参考资源

- [mitmproxy 官方文档](https://docs.mitmproxy.org/)
- [微信公众号爬虫 GitHub](https://github.com/wnma3mz/wechat_articles_spider)
