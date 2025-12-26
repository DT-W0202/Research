#!/usr/bin/env python3
"""
迁移现有数据到统一的日价数据库
"""

import sqlite3
from daily_scraper import WinePriceDB, WinePrice, DailyScraper
from datetime import datetime

def migrate_from_old_db():
    """从旧数据库迁移数据"""
    old_db = "buerjjiang_wine.db"
    new_db = WinePriceDB("wine_prices_daily.db")
    scraper = DailyScraper(new_db)

    try:
        conn = sqlite3.connect(old_db)
        cursor = conn.cursor()
        cursor.execute('''
            SELECT name, price, change, publish_date, source_title
            FROM wine_prices
        ''')
        rows = cursor.fetchall()
        conn.close()

        prices_data = []
        for row in rows:
            name, price, change, date, source = row
            if not date or not price:
                continue
            prices_data.append({
                'name': name,
                'price': price,
                'change': change or '',
                'date': date,
                'source': '今日酒价' if '今日酒价' in (source or '') else '不二酱'
            })

        count = scraper.add_manual_prices(prices_data)
        print(f"从旧数据库迁移了 {count} 条记录")
        return count

    except Exception as e:
        print(f"迁移失败: {e}")
        return 0


def add_sample_data():
    """添加示例数据（用于测试）"""
    db = WinePriceDB("wine_prices_daily.db")
    scraper = DailyScraper(db)

    # 2025年12月数据
    sample_prices = [
        # 12月26日
        {'date': '2025-12-26', 'name': '飞天茅台', 'price': 1602, 'change': '↑2', 'source': '今日酒价'},
        {'date': '2025-12-26', 'name': '精品茅台', 'price': 2308, 'change': '↑28', 'source': '今日酒价'},
        {'date': '2025-12-26', 'name': '古井贡古20', 'price': 520, 'change': '↑7', 'source': '今日酒价'},
        {'date': '2025-12-26', 'name': '青花郎', 'price': 680, 'change': '↑5', 'source': '今日酒价'},
        {'date': '2025-12-26', 'name': '国窖1573', 'price': 830, 'change': '↑2', 'source': '今日酒价'},
        {'date': '2025-12-26', 'name': '五粮液普五八代', 'price': 920, 'change': '↓4', 'source': '今日酒价'},

        # 12月24日
        {'date': '2025-12-24', 'name': '25年飞天原箱', 'price': 1600, 'change': '↑40', 'source': '今日酒价'},
        {'date': '2025-12-24', 'name': '25年飞天散瓶', 'price': 1590, 'change': '↑40', 'source': '今日酒价'},
        {'date': '2025-12-24', 'name': '24年飞天原箱', 'price': 1630, 'change': '↑30', 'source': '今日酒价'},
        {'date': '2025-12-24', 'name': '24年飞天散瓶', 'price': 1615, 'change': '↑35', 'source': '今日酒价'},
        {'date': '2025-12-24', 'name': '散花飞天', 'price': 2480, 'change': '↑100', 'source': '今日酒价'},
        {'date': '2025-12-24', 'name': '茅台十五年', 'price': 4150, 'change': '↑80', 'source': '今日酒价'},
        {'date': '2025-12-24', 'name': '精品茅台', 'price': 2280, 'change': '↑30', 'source': '今日酒价'},
        {'date': '2025-12-24', 'name': '生肖蛇原箱', 'price': 2000, 'change': '↑230', 'source': '不二酱'},
        {'date': '2025-12-24', 'name': '彩釉珍品', 'price': 3250, 'change': '', 'source': '不二酱'},

        # 12月15日
        {'date': '2025-12-15', 'name': '散花飞天', 'price': 2200, 'change': '', 'source': '今日酒价'},
        {'date': '2025-12-15', 'name': '茅台十五年', 'price': 3600, 'change': '', 'source': '今日酒价'},
        {'date': '2025-12-15', 'name': '25年飞天散瓶', 'price': 1560, 'change': '', 'source': '今日酒价'},

        # 12月12日 - 跌破指导价
        {'date': '2025-12-12', 'name': '25年飞天原箱', 'price': 1495, 'change': '↓15', 'source': '今日酒价'},
        {'date': '2025-12-12', 'name': '25年飞天散瓶', 'price': 1485, 'change': '↓15', 'source': '今日酒价'},
    ]

    count = scraper.add_manual_prices(sample_prices)
    print(f"添加了 {count} 条示例数据")
    return count


if __name__ == "__main__":
    print("=" * 50)
    print("数据迁移工具")
    print("=" * 50)

    # 先迁移旧数据
    print("\n1. 迁移旧数据库...")
    migrate_from_old_db()

    # 添加示例数据
    print("\n2. 添加最新数据...")
    add_sample_data()

    # 显示统计
    db = WinePriceDB("wine_prices_daily.db")
    stats = db.get_stats()
    print(f"\n{'='*50}")
    print("迁移完成!")
    print(f"{'='*50}")
    print(f"总记录数: {stats['total_records']}")
    print(f"覆盖天数: {stats['total_days']}")
    print(f"时间范围: {stats['date_range']}")
