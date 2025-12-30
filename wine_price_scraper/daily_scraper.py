#!/usr/bin/env python3
"""
每日酒价自动抓取工具

数据分表存储：
- jinrijiujia (今日酒价)
- buerjiang (不二酱)
"""

import os
import re
import json
import sqlite3
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Optional
from dataclasses import dataclass
import csv

# 配置日志
LOG_DIR = Path(__file__).parent / "logs"
LOG_DIR.mkdir(exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_DIR / f"scraper_{datetime.now().strftime('%Y%m')}.log", encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


@dataclass
class WinePrice:
    """酒价数据结构"""
    date: str
    name: str
    price: float
    change: str
    change_value: Optional[float]
    category: str
    spec: str
    created_at: str


class WinePriceDB:
    """酒价数据库 - 分表存储"""

    def __init__(self, db_path: str = "wine_prices_daily.db"):
        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        """初始化数据库 - 两个独立的表"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # 今日酒价 表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS jinrijiujia (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date TEXT NOT NULL,
                name TEXT NOT NULL,
                price REAL NOT NULL,
                change TEXT,
                change_value REAL,
                category TEXT,
                spec TEXT,
                created_at TEXT,
                UNIQUE(date, name)
            )
        ''')

        # 不二酱 表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS buerjiang (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date TEXT NOT NULL,
                name TEXT NOT NULL,
                price REAL NOT NULL,
                change TEXT,
                change_value REAL,
                category TEXT,
                spec TEXT,
                created_at TEXT,
                UNIQUE(date, name)
            )
        ''')

        # 创建索引
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_jrjj_date ON jinrijiujia(date)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_bej_date ON buerjiang(date)')

        conn.commit()
        conn.close()
        logger.info(f"数据库初始化完成: {self.db_path}")

    def save_price(self, table: str, price: WinePrice) -> bool:
        """保存价格到指定表"""
        if table not in ('jinrijiujia', 'buerjiang'):
            raise ValueError(f"无效的表名: {table}")

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        try:
            cursor.execute(f'''
                INSERT OR REPLACE INTO {table}
                (date, name, price, change, change_value, category, spec, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                price.date, price.name, price.price, price.change,
                price.change_value, price.category, price.spec, price.created_at
            ))
            conn.commit()
            return True
        except Exception as e:
            logger.error(f"保存失败: {e}")
            return False
        finally:
            conn.close()

    def save_prices(self, table: str, prices: List[WinePrice]) -> int:
        """批量保存价格"""
        count = 0
        for p in prices:
            if self.save_price(table, p):
                count += 1
        return count

    def get_prices(self, table: str, date: str = None, limit: int = 50) -> List[Dict]:
        """获取价格"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        if date:
            cursor.execute(f'''
                SELECT date, name, price, change, category, spec
                FROM {table} WHERE date = ?
                ORDER BY category, name
            ''', (date,))
        else:
            cursor.execute(f'''
                SELECT date, name, price, change, category, spec
                FROM {table}
                ORDER BY date DESC, category, name
                LIMIT ?
            ''', (limit,))

        rows = cursor.fetchall()
        conn.close()
        return [
            {'date': r[0], 'name': r[1], 'price': r[2], 'change': r[3],
             'category': r[4], 'spec': r[5]}
            for r in rows
        ]

    def get_all_latest(self, limit: int = 30) -> Dict[str, List[Dict]]:
        """获取两个表的最新数据"""
        return {
            '今日酒价': self.get_prices('jinrijiujia', limit=limit),
            '不二酱': self.get_prices('buerjiang', limit=limit)
        }

    def get_history(self, table: str, name: str, days: int = 30) -> List[Dict]:
        """获取某酒的历史价格"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        start_date = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')
        cursor.execute(f'''
            SELECT date, price, change FROM {table}
            WHERE name LIKE ? AND date >= ?
            ORDER BY date
        ''', (f'%{name}%', start_date))
        rows = cursor.fetchall()
        conn.close()
        return [{'date': r[0], 'price': r[1], 'change': r[2]} for r in rows]

    def export_csv(self, table: str, filepath: str = None, days: int = 30):
        """导出指定表的CSV"""
        if filepath is None:
            filepath = f"{table}_{datetime.now().strftime('%Y%m%d')}.csv"

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        start_date = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')
        cursor.execute(f'''
            SELECT date, name, price, change, category, spec
            FROM {table} WHERE date >= ?
            ORDER BY date DESC, category, name
        ''', (start_date,))
        rows = cursor.fetchall()
        conn.close()

        with open(filepath, 'w', newline='', encoding='utf-8-sig') as f:
            writer = csv.writer(f)
            writer.writerow(['日期', '酒名', '价格', '涨跌', '分类', '规格'])
            writer.writerows(rows)

        logger.info(f"导出 {len(rows)} 条记录到 {filepath}")
        return filepath

    def export_all_csv(self, days: int = 30):
        """导出两个表的CSV"""
        f1 = self.export_csv('jinrijiujia', days=days)
        f2 = self.export_csv('buerjiang', days=days)
        return f1, f2

    def get_stats(self) -> Dict:
        """获取统计信息"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        stats = {}
        for table in ['jinrijiujia', 'buerjiang']:
            cursor.execute(f'SELECT COUNT(*) FROM {table}')
            total = cursor.fetchone()[0]

            cursor.execute(f'SELECT COUNT(DISTINCT date) FROM {table}')
            days = cursor.fetchone()[0]

            cursor.execute(f'SELECT MIN(date), MAX(date) FROM {table}')
            date_range = cursor.fetchone()

            stats[table] = {
                'total': total,
                'days': days,
                'range': f"{date_range[0]} ~ {date_range[1]}" if date_range[0] else "无数据"
            }

        conn.close()
        return stats


class DailyScraper:
    """每日抓取器"""

    def __init__(self, db: WinePriceDB = None):
        self.db = db or WinePriceDB()
        self.today = datetime.now().strftime('%Y-%m-%d')

        # 酒类分类规则
        self.category_rules = {
            '茅台': ['茅台', '飞天', '生肖', '精品', '王子', '迎宾', '散花', '珍品'],
            '五粮液': ['五粮液', '普五'],
            '国窖': ['国窖', '1573'],
            '汾酒': ['汾酒', '青花汾'],
            '洋河': ['洋河', '梦之蓝', 'M6'],
            '剑南春': ['剑南春', '水晶剑'],
            '郎酒': ['郎酒', '青花郎', '红花郎'],
            '习酒': ['习酒', '君品'],
            '古井贡': ['古井贡', '古20'],
        }

    def _classify(self, name: str) -> str:
        for category, keywords in self.category_rules.items():
            if any(kw in name for kw in keywords):
                return category
        return '其他'

    def _get_spec(self, name: str) -> str:
        if any(kw in name for kw in ['原箱', '整箱']):
            return '原箱'
        return '散瓶'

    def _parse_change(self, change_str: str) -> Optional[float]:
        if not change_str:
            return None
        match = re.search(r'[↑↓+-]?\s*(\d+(?:\.\d+)?)', change_str)
        if match:
            value = float(match.group(1))
            if '↓' in change_str or '-' in change_str:
                value = -value
            return value
        return None

    def _create_price(self, date: str, name: str, price: float, change: str = "") -> WinePrice:
        return WinePrice(
            date=date,
            name=name,
            price=price,
            change=change,
            change_value=self._parse_change(change),
            category=self._classify(name),
            spec=self._get_spec(name),
            created_at=datetime.now().isoformat()
        )

    def add_prices(self, source: str, prices_data: List[Dict]) -> int:
        """
        添加价格数据

        参数:
            source: '今日酒价' 或 '不二酱'
            prices_data: [{'name': '飞天茅台', 'price': 1600, 'change': '↑10', 'date': '2025-12-26'}, ...]
        """
        table = 'jinrijiujia' if source == '今日酒价' else 'buerjiang'

        prices = []
        for item in prices_data:
            p = self._create_price(
                date=item.get('date', self.today),
                name=item['name'],
                price=item['price'],
                change=item.get('change', '')
            )
            prices.append(p)

        count = self.db.save_prices(table, prices)
        logger.info(f"[{source}] 添加 {count} 条记录")
        return count


def show_prices(db: WinePriceDB):
    """显示两个表的最新价格"""
    data = db.get_all_latest(limit=20)

    for source, prices in data.items():
        print(f"\n{'='*50}")
        print(f"【{source}】")
        print('='*50)

        if not prices:
            print("  暂无数据")
            continue

        current_date = None
        for p in prices:
            if p['date'] != current_date:
                current_date = p['date']
                print(f"\n  [{current_date}]")
            change = f" {p['change']}" if p['change'] else ""
            print(f"    {p['name']:<16} {p['price']:>6.0f}元{change}")


def show_stats(db: WinePriceDB):
    """显示统计"""
    stats = db.get_stats()

    print(f"\n{'='*50}")
    print("数据统计")
    print('='*50)

    for table, s in stats.items():
        name = '今日酒价' if table == 'jinrijiujia' else '不二酱'
        print(f"\n【{name}】")
        print(f"  记录数: {s['total']}")
        print(f"  天数:   {s['days']}")
        print(f"  范围:   {s['range']}")


def interactive_add(scraper: DailyScraper):
    """交互式添加"""
    print("\n选择数据来源:")
    print("  1. 今日酒价")
    print("  2. 不二酱")
    choice = input("请选择 (1/2): ").strip()

    source = '今日酒价' if choice == '1' else '不二酱'
    print(f"\n添加到【{source}】")
    print("格式: 酒名 价格 涨跌 (例: 飞天茅台 1600 ↑10)")
    print("输入 'done' 完成, 'cancel' 取消")
    print("-" * 40)

    prices = []
    while True:
        try:
            line = input("> ").strip()
            if line.lower() == 'done':
                break
            if line.lower() == 'cancel':
                print("已取消")
                return

            parts = line.split()
            if len(parts) >= 2:
                name = parts[0]
                price = float(parts[1])
                change = parts[2] if len(parts) > 2 else ""
                prices.append({'name': name, 'price': price, 'change': change})
                print(f"  ✓ {name}: {price}元 {change}")
        except ValueError:
            print("  ✗ 格式错误")
        except KeyboardInterrupt:
            print("\n已取消")
            return

    if prices:
        count = scraper.add_prices(source, prices)
        print(f"\n已保存 {count} 条到【{source}】")


def show_menu():
    print("""
╔════════════════════════════════════════════════════════════════╗
║              每日酒价自动抓取工具 v2.0                           ║
║                   (分表存储版)                                  ║
╠════════════════════════════════════════════════════════════════╣
║                                                                ║
║  数据表:                                                       ║
║    - jinrijiujia  (今日酒价)                                   ║
║    - buerjiang    (不二酱)                                     ║
║                                                                ║
║  命令:                                                         ║
║    python daily_scraper.py show      - 显示两表最新价格         ║
║    python daily_scraper.py stats     - 查看统计信息            ║
║    python daily_scraper.py add       - 手动添加价格            ║
║    python daily_scraper.py export    - 导出CSV (两个文件)       ║
║    python daily_scraper.py history 飞天 - 查看历史             ║
║                                                                ║
╚════════════════════════════════════════════════════════════════╝
""")


def main():
    import sys

    db = WinePriceDB()
    scraper = DailyScraper(db)

    if len(sys.argv) < 2:
        show_menu()
        return

    cmd = sys.argv[1].lower()

    if cmd == 'show':
        show_prices(db)

    elif cmd == 'stats':
        show_stats(db)

    elif cmd == 'add':
        interactive_add(scraper)

    elif cmd == 'export':
        days = int(sys.argv[2]) if len(sys.argv) > 2 else 30
        f1, f2 = db.export_all_csv(days=days)
        print(f"已导出:\n  {f1}\n  {f2}")

    elif cmd == 'history':
        name = sys.argv[2] if len(sys.argv) > 2 else "飞天"
        print(f"\n{name} 历史价格:")

        for table, label in [('jinrijiujia', '今日酒价'), ('buerjiang', '不二酱')]:
            history = db.get_history(table, name, 30)
            if history:
                print(f"\n【{label}】")
                for h in history:
                    change = f" {h['change']}" if h['change'] else ""
                    print(f"  {h['date']}  {h['price']:>6.0f}元{change}")

    else:
        show_menu()


if __name__ == "__main__":
    main()
