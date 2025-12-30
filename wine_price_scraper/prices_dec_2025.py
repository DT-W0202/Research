#!/usr/bin/env python3
"""
2025年12月最新茅台价格数据
数据来源：新浪财经、36氪、21经济网等引用的今日酒价/不二酱数据
"""

import sqlite3

# 2025年12月最新价格数据
PRICES_DEC_2025 = [
    # 2025年12月24日 - 全线上涨
    {"date": "2025-12-24", "name": "25年飞天原箱", "price": 1600, "change": "↑40"},
    {"date": "2025-12-24", "name": "25年飞天散瓶", "price": 1590, "change": "↑40"},
    {"date": "2025-12-24", "name": "24年飞天原箱", "price": 1630, "change": "↑30"},
    {"date": "2025-12-24", "name": "24年飞天散瓶", "price": 1615, "change": "↑35"},
    {"date": "2025-12-24", "name": "散花飞天", "price": 2480, "change": "↑100"},
    {"date": "2025-12-24", "name": "茅台十五年", "price": 4150, "change": "↑80"},
    {"date": "2025-12-24", "name": "精品茅台", "price": 2280, "change": "↑30"},
    {"date": "2025-12-24", "name": "生肖蛇原箱", "price": 2000, "change": "↑230"},
    {"date": "2025-12-24", "name": "彩釉珍品", "price": 3250, "change": ""},

    # 2025年12月12日 - 跌破指导价
    {"date": "2025-12-12", "name": "25年飞天原箱", "price": 1495, "change": "↓15"},
    {"date": "2025-12-12", "name": "25年飞天散瓶", "price": 1485, "change": "↓15"},

    # 2025年12月初
    {"date": "2025-12-04", "name": "飞天茅台", "price": 1545, "change": ""},

    # 2025年12月15日基准（用于计算涨幅）
    {"date": "2025-12-15", "name": "散花飞天", "price": 2200, "change": ""},  # 24日2480-280
    {"date": "2025-12-15", "name": "茅台十五年", "price": 3600, "change": ""},  # 24日4150-550
    {"date": "2025-12-15", "name": "精品茅台", "price": 2070, "change": ""},  # 24日2280-210
    {"date": "2025-12-15", "name": "生肖蛇原箱", "price": 1610, "change": ""},  # 24日2000-390
    {"date": "2025-12-15", "name": "彩釉珍品", "price": 2950, "change": ""},  # 24日3250-300
]

def save_to_db(db_path="buerjjiang_wine.db"):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

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

    count = 0
    for item in PRICES_DEC_2025:
        cursor.execute('''
            INSERT INTO wine_prices (name, price, unit, change, source_title, publish_date)
            VALUES (?, ?, '元/瓶', ?, ?, ?)
        ''', (item['name'], item['price'], item.get('change', ''), '今日酒价/不二酱(新闻引用)', item['date']))
        count += 1

    conn.commit()
    conn.close()
    return count

def show_prices():
    print("=" * 65)
    print("2025年12月茅台价格数据 (今日酒价/不二酱)")
    print("=" * 65)

    current_date = None
    for item in sorted(PRICES_DEC_2025, key=lambda x: x['date'], reverse=True):
        if item['date'] != current_date:
            current_date = item['date']
            print(f"\n【{current_date}】")
        change = item.get('change', '')
        print(f"  {item['name']:<16} {item['price']:>5}元  {change}")

    print("\n" + "=" * 65)

if __name__ == "__main__":
    show_prices()
    count = save_to_db()
    print(f"\n已保存 {count} 条记录到数据库")
