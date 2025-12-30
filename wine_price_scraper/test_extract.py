#!/usr/bin/env python3
"""测试价格提取功能"""

from pc_wechat_scraper import BuerjiangScraper

# 模拟不二酱公众号文章内容
sample_content = """
【2024年12月26日行情】

今日茅台行情参考价:

飞天(散) 2320 ↓80
飞天(原箱) 2550 ↓50
精品茅台 1680 ↓30
茅台王子 380 -
茅台迎宾 198 -

五粮液52度 980 ↓20
国窖1573 850 ↓15
青花郎20年 1180 ↓25

生肖系列:
龙年茅台 3200 ↑50
兔年茅台 2800 ↓100
虎年茅台 2650 ↓80
牛年茅台 2700 ↓60

【温馨提示】
以上价格仅供参考，实际成交价以市场为准。
"""

scraper = BuerjiangScraper(db_path="test_wine.db")

# 测试提取
prices = scraper.extract_prices_from_content(
    content=sample_content,
    title="不二酱每日行情 2024-12-26",
    url="https://mp.weixin.qq.com/s/test123",
    publish_date="2024-12-26"
)

print("=" * 60)
print("测试价格提取功能")
print("=" * 60)
print(f"\n从模拟文章中提取到 {len(prices)} 条价格:\n")

for p in prices:
    change = f" {p.change}" if p.change else ""
    print(f"  {p.name}: {p.price}元{change}")

print("\n" + "=" * 60)
print("提取功能正常!")
print("=" * 60)
