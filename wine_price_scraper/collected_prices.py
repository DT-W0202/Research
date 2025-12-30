#!/usr/bin/env python3
"""
从公开来源收集到的"不二酱"茅台价格数据
数据来源：财经新闻网站引用的不二酱数据
"""

import sqlite3
from datetime import datetime

# 从搜索结果中提取的不二酱价格数据
COLLECTED_PRICES = [
    # 2024年12月数据
    {"date": "2024-12-05", "name": "飞天原箱", "price": 2290, "unit": "元/瓶", "change": "↑55"},
    {"date": "2024-12-05", "name": "飞天散瓶", "price": 2210, "unit": "元/瓶", "change": "↑20"},
    {"date": "2024-12-01", "name": "飞天原箱", "price": 2235, "unit": "元/瓶", "change": ""},
    {"date": "2024-12-01", "name": "飞天散瓶", "price": 2190, "unit": "元/瓶", "change": ""},

    # 2024年11月数据
    {"date": "2024-11-04", "name": "2025年飞天散瓶", "price": 1640, "unit": "元/瓶", "change": ""},
    {"date": "2024-11-03", "name": "飞天原箱", "price": 2280, "unit": "元/瓶", "change": "↑50"},
    {"date": "2024-11-02", "name": "飞天原箱", "price": 2230, "unit": "元/瓶", "change": "↑80"},
    {"date": "2024-11-02", "name": "飞天散瓶", "price": 2210, "unit": "元/瓶", "change": "↑70"},
    {"date": "2024-11-01", "name": "飞天散瓶", "price": 2270, "unit": "元/瓶", "change": "↑140"},
    {"date": "2024-11-01", "name": "飞天原箱", "price": 2300, "unit": "元/瓶", "change": "↑130"},

    # 2024年6月数据
    {"date": "2024-06-11", "name": "飞天散瓶", "price": 2430, "unit": "元/瓶", "change": ""},
    {"date": "2024-06-11", "name": "飞天散瓶", "price": 2320, "unit": "元/瓶", "change": "↓80"},

    # 历史参考数据
    {"date": "2024-01-01", "name": "飞天茅台", "price": 2700, "unit": "元/瓶", "change": "年初参考价"},
]

def save_to_db(db_path: str = "buerjjiang_wine.db"):
    """保存到数据库"""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # 确保表存在
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
    for item in COLLECTED_PRICES:
        try:
            cursor.execute('''
                INSERT INTO wine_prices (name, price, unit, change, source_title, publish_date)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (
                item['name'],
                item['price'],
                item['unit'],
                item.get('change', ''),
                '不二酱数据(新闻引用)',
                item['date']
            ))
            count += 1
        except Exception as e:
            print(f"跳过: {e}")

    conn.commit()
    conn.close()
    return count

def show_prices():
    """显示收集的价格数据"""
    print("=" * 70)
    print("从公开来源收集的'不二酱'茅台价格数据")
    print("=" * 70)
    print(f"\n{'日期':<12} {'酒名':<20} {'价格':>8} {'涨跌':>8}")
    print("-" * 70)

    current_month = None
    for item in sorted(COLLECTED_PRICES, key=lambda x: x['date'], reverse=True):
        month = item['date'][:7]
        if month != current_month:
            current_month = month
            print(f"\n【{month}】")

        change = item.get('change', '')
        print(f"  {item['date']}  {item['name']:<18} {item['price']:>6}元  {change}")

    print("\n" + "=" * 70)
    print(f"共收集 {len(COLLECTED_PRICES)} 条价格记录")
    print("数据来源: 财联社、证券时报、澎湃新闻等财经媒体引用的不二酱数据")
    print("=" * 70)

if __name__ == "__main__":
    show_prices()

    print("\n保存到数据库...")
    count = save_to_db()
    print(f"已保存 {count} 条记录到 buerjjiang_wine.db")
