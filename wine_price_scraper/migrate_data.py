#!/usr/bin/env python3
"""
迁移数据到分表结构
"""

import sqlite3
from daily_scraper import WinePriceDB, DailyScraper

def migrate():
    """迁移旧数据到新的分表结构"""
    old_db = "buerjjiang_wine.db"

    db = WinePriceDB("wine_prices_daily.db")
    scraper = DailyScraper(db)

    try:
        conn = sqlite3.connect(old_db)
        cursor = conn.cursor()
        cursor.execute('''
            SELECT name, price, change, publish_date, source_title
            FROM wine_prices
        ''')
        rows = cursor.fetchall()
        conn.close()

        jrjj_data = []  # 今日酒价
        bej_data = []   # 不二酱

        for row in rows:
            name, price, change, date, source = row
            if not date or not price:
                continue

            item = {
                'name': name,
                'price': price,
                'change': change or '',
                'date': date
            }

            # 根据来源分类
            if '今日酒价' in (source or ''):
                jrjj_data.append(item)
            else:
                bej_data.append(item)

        # 保存到各自的表
        count1 = scraper.add_prices('今日酒价', jrjj_data)
        count2 = scraper.add_prices('不二酱', bej_data)

        print(f"迁移完成:")
        print(f"  今日酒价: {count1} 条")
        print(f"  不二酱:   {count2} 条")

        return count1 + count2

    except Exception as e:
        print(f"迁移失败: {e}")
        return 0


def add_sample_data():
    """添加示例数据"""
    db = WinePriceDB("wine_prices_daily.db")
    scraper = DailyScraper(db)

    # 今日酒价数据
    jrjj_prices = [
        {'date': '2025-12-26', 'name': '飞天茅台', 'price': 1602, 'change': '↑2'},
        {'date': '2025-12-26', 'name': '精品茅台', 'price': 2308, 'change': '↑28'},
        {'date': '2025-12-26', 'name': '国窖1573', 'price': 830, 'change': '↑2'},
        {'date': '2025-12-26', 'name': '五粮液普五八代', 'price': 920, 'change': '↓4'},
        {'date': '2025-12-26', 'name': '青花郎', 'price': 680, 'change': '↑5'},
        {'date': '2025-12-24', 'name': '25年飞天原箱', 'price': 1600, 'change': '↑40'},
        {'date': '2025-12-24', 'name': '25年飞天散瓶', 'price': 1590, 'change': '↑40'},
        {'date': '2025-12-24', 'name': '散花飞天', 'price': 2480, 'change': '↑100'},
        {'date': '2025-12-24', 'name': '茅台十五年', 'price': 4150, 'change': '↑80'},
        {'date': '2025-12-12', 'name': '25年飞天散瓶', 'price': 1485, 'change': '↓15'},
    ]

    # 不二酱数据
    bej_prices = [
        {'date': '2025-12-24', 'name': '生肖蛇原箱', 'price': 2000, 'change': '↑230'},
        {'date': '2025-12-24', 'name': '彩釉珍品', 'price': 3250, 'change': ''},
        {'date': '2025-12-15', 'name': '生肖蛇原箱', 'price': 1610, 'change': ''},
        {'date': '2025-12-15', 'name': '散花飞天', 'price': 2200, 'change': ''},
        {'date': '2024-12-05', 'name': '飞天原箱', 'price': 2290, 'change': '↑55'},
        {'date': '2024-12-05', 'name': '飞天散瓶', 'price': 2210, 'change': '↑20'},
        {'date': '2024-11-03', 'name': '飞天原箱', 'price': 2280, 'change': '↑50'},
    ]

    count1 = scraper.add_prices('今日酒价', jrjj_prices)
    count2 = scraper.add_prices('不二酱', bej_prices)

    print(f"\n添加示例数据:")
    print(f"  今日酒价: {count1} 条")
    print(f"  不二酱:   {count2} 条")


if __name__ == "__main__":
    print("=" * 50)
    print("数据迁移 (分表版)")
    print("=" * 50)

    # 删除旧的统一表数据库，重新创建
    import os
    if os.path.exists("wine_prices_daily.db"):
        os.remove("wine_prices_daily.db")
        print("\n已清除旧数据库")

    print("\n1. 迁移旧数据...")
    migrate()

    print("\n2. 添加示例数据...")
    add_sample_data()

    # 显示统计
    db = WinePriceDB("wine_prices_daily.db")
    stats = db.get_stats()

    print(f"\n{'='*50}")
    print("迁移完成!")
    print('='*50)
    for table, s in stats.items():
        name = '今日酒价' if table == 'jinrijiujia' else '不二酱'
        print(f"\n【{name}】")
        print(f"  记录数: {s['total']}")
        print(f"  范围:   {s['range']}")
