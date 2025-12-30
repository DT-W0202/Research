#!/usr/bin/env python3
"""
2025年12月26日 今日酒价 最新数据
数据来源：新浪财经"酒价内参12月26日价格发布"
"""

import sqlite3

# 12月26日最新价格
PRICES_TODAY = [
    # 12月26日 - 今日酒价/酒价内参
    {"date": "2025-12-26", "name": "飞天茅台", "price": 1602, "change": "↑2", "source": "今日酒价"},
    {"date": "2025-12-26", "name": "精品茅台", "price": 2308, "change": "↑28", "source": "今日酒价"},  # 2280+28
    {"date": "2025-12-26", "name": "古井贡古20", "price": None, "change": "↑7", "source": "今日酒价"},
    {"date": "2025-12-26", "name": "青花郎", "price": None, "change": "↑5", "source": "今日酒价"},
    {"date": "2025-12-26", "name": "习酒君品", "price": None, "change": "↑4", "source": "今日酒价"},
    {"date": "2025-12-26", "name": "洋河梦之蓝M6+", "price": None, "change": "↑3", "source": "今日酒价"},
    {"date": "2025-12-26", "name": "国窖1573", "price": None, "change": "↑2", "source": "今日酒价"},
    {"date": "2025-12-26", "name": "青花汾20", "price": None, "change": "↑2", "source": "今日酒价"},
    {"date": "2025-12-26", "name": "水晶剑南春", "price": None, "change": "持平", "source": "今日酒价"},
    {"date": "2025-12-26", "name": "五粮液普五八代", "price": None, "change": "↓4", "source": "今日酒价"},

    # 补充12月22日深圳零售价
    {"date": "2025-12-22", "name": "飞天茅台(零售)", "price": 1700, "change": "", "source": "深圳酒行"},
    {"date": "2025-12-22", "name": "飞天茅台原箱(零售)", "price": 1720, "change": "", "source": "深圳酒行"},

    # 12月17日批发价
    {"date": "2025-12-17", "name": "飞天散瓶", "price": 1550, "change": "", "source": "今日酒价"},
    {"date": "2025-12-17", "name": "飞天原箱", "price": 1570, "change": "", "source": "今日酒价"},

    # 12月13-14日反弹数据
    {"date": "2025-12-14", "name": "25年飞天散瓶", "price": 1570, "change": "↑70", "source": "今日酒价"},
    {"date": "2025-12-14", "name": "25年飞天原箱", "price": 1590, "change": "↑70", "source": "今日酒价"},
    {"date": "2025-12-13", "name": "25年飞天散瓶", "price": 1500, "change": "↑20", "source": "今日酒价"},
    {"date": "2025-12-13", "name": "25年飞天原箱", "price": 1520, "change": "↑25", "source": "今日酒价"},
]

def save_to_db(db_path="buerjjiang_wine.db"):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    count = 0
    for item in PRICES_TODAY:
        if item['price'] is None:
            continue  # 跳过没有具体价格的
        cursor.execute('''
            INSERT INTO wine_prices (name, price, unit, change, source_title, publish_date)
            VALUES (?, ?, '元/瓶', ?, ?, ?)
        ''', (item['name'], item['price'], item.get('change', ''), item.get('source', '今日酒价'), item['date']))
        count += 1

    conn.commit()
    conn.close()
    return count

def show_today():
    print("=" * 60)
    print("【2025年12月26日】今日酒价 最新行情")
    print("=" * 60)
    print()
    print("茅台系列:")
    print("  飞天茅台      1602元  ↑2   (连续上涨)")
    print("  精品茅台      2308元  ↑28  (连续三日大涨,累计↑110)")
    print()
    print("其他名酒涨跌:")
    print("  古井贡古20          ↑7")
    print("  青花郎              ↑5")
    print("  习酒君品            ↑4")
    print("  洋河梦之蓝M6+       ↑3")
    print("  国窖1573            ↑2")
    print("  青花汾20            ↑2")
    print("  水晶剑南春          持平")
    print("  五粮液普五八代      ↓4  (唯一下跌)")
    print()
    print("=" * 60)
    print("数据来源: 新浪财经《酒价内参12月26日价格发布》")
    print("=" * 60)

if __name__ == "__main__":
    show_today()
    count = save_to_db()
    print(f"\n已保存 {count} 条记录到数据库")
