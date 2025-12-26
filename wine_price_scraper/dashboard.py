#!/usr/bin/env python3
"""
酒价数据 Dashboard

运行: streamlit run dashboard.py
"""

import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime, timedelta

# 页面配置
st.set_page_config(
    page_title="酒价监控 Dashboard",
    page_icon="🍷",
    layout="wide"
)

# 数据库路径
DB_PATH = "wine_prices_daily.db"

# 酒类分类
CATEGORIES = ['全部', '茅台', '五粮液', '国窖', '郎酒', '汾酒', '洋河', '剑南春', '习酒', '古井贡', '其他']

# 时间周期选项
TIME_PERIODS = {
    '最近7天': 7,
    '最近14天': 14,
    '最近30天': 30,
    '最近60天': 60,
    '最近90天': 90,
    '全部': 365
}


@st.cache_data(ttl=60)
def load_data(table: str, days: int, category: str) -> pd.DataFrame:
    """加载数据"""
    conn = sqlite3.connect(DB_PATH)

    start_date = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')

    if category == '全部':
        query = f"""
            SELECT date as 日期, name as 酒名, price as 价格, change as 涨跌, category as 分类, spec as 规格
            FROM {table}
            WHERE date >= ?
            ORDER BY date DESC, category, name
        """
        df = pd.read_sql_query(query, conn, params=(start_date,))
    else:
        query = f"""
            SELECT date as 日期, name as 酒名, price as 价格, change as 涨跌, category as 分类, spec as 规格
            FROM {table}
            WHERE date >= ? AND category = ?
            ORDER BY date DESC, name
        """
        df = pd.read_sql_query(query, conn, params=(start_date, category))

    conn.close()
    return df


@st.cache_data(ttl=60)
def get_price_trend(table: str, name_pattern: str, days: int) -> pd.DataFrame:
    """获取价格趋势"""
    conn = sqlite3.connect(DB_PATH)
    start_date = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')

    query = f"""
        SELECT date, name, price, change
        FROM {table}
        WHERE date >= ? AND name LIKE ?
        ORDER BY date
    """
    df = pd.read_sql_query(query, conn, params=(start_date, f'%{name_pattern}%'))
    conn.close()
    return df


@st.cache_data(ttl=60)
def get_stats(table: str) -> dict:
    """获取统计信息"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute(f'SELECT COUNT(*) FROM {table}')
    total = cursor.fetchone()[0]

    cursor.execute(f'SELECT COUNT(DISTINCT date) FROM {table}')
    days = cursor.fetchone()[0]

    cursor.execute(f'SELECT MIN(date), MAX(date) FROM {table}')
    date_range = cursor.fetchone()

    cursor.execute(f'SELECT COUNT(DISTINCT name) FROM {table}')
    products = cursor.fetchone()[0]

    conn.close()

    return {
        'total': total,
        'days': days,
        'products': products,
        'start': date_range[0] or '-',
        'end': date_range[1] or '-'
    }


def main():
    # 标题
    st.title("🍷 酒价监控 Dashboard")
    st.markdown("数据来源：**今日酒价** & **不二酱**")

    # 侧边栏 - 筛选条件
    st.sidebar.header("📊 筛选条件")

    # 时间周期选择
    period = st.sidebar.selectbox(
        "⏰ 时间周期",
        options=list(TIME_PERIODS.keys()),
        index=2  # 默认30天
    )
    days = TIME_PERIODS[period]

    # 酒类选择
    category = st.sidebar.selectbox(
        "🏷️ 酒类分类",
        options=CATEGORIES,
        index=0
    )

    # 搜索框
    search = st.sidebar.text_input("🔍 搜索酒名", "")

    st.sidebar.markdown("---")

    # 统计信息
    st.sidebar.subheader("📈 数据统计")

    col1, col2 = st.sidebar.columns(2)

    stats1 = get_stats('jinrijiujia')
    stats2 = get_stats('buerjiang')

    with col1:
        st.metric("今日酒价", f"{stats1['total']}条")
    with col2:
        st.metric("不二酱", f"{stats2['total']}条")

    # 主内容区 - 两列布局
    col_left, col_right = st.columns(2)

    # ========== 今日酒价 ==========
    with col_left:
        st.header("📰 今日酒价")

        df1 = load_data('jinrijiujia', days, category)

        # 搜索过滤
        if search:
            df1 = df1[df1['酒名'].str.contains(search, case=False, na=False)]

        if df1.empty:
            st.info("暂无数据")
        else:
            # 显示统计卡片
            st.markdown(f"**共 {len(df1)} 条记录** | 覆盖 {df1['日期'].nunique()} 天")

            # 数据表格
            st.dataframe(
                df1,
                use_container_width=True,
                height=400,
                column_config={
                    "价格": st.column_config.NumberColumn(format="%.0f 元"),
                    "涨跌": st.column_config.TextColumn(),
                }
            )

            # 下载按钮
            csv1 = df1.to_csv(index=False).encode('utf-8-sig')
            st.download_button(
                "📥 下载 CSV",
                csv1,
                f"jinrijiujia_{datetime.now().strftime('%Y%m%d')}.csv",
                "text/csv"
            )

    # ========== 不二酱 ==========
    with col_right:
        st.header("🍶 不二酱")

        df2 = load_data('buerjiang', days, category)

        # 搜索过滤
        if search:
            df2 = df2[df2['酒名'].str.contains(search, case=False, na=False)]

        if df2.empty:
            st.info("暂无数据")
        else:
            # 显示统计卡片
            st.markdown(f"**共 {len(df2)} 条记录** | 覆盖 {df2['日期'].nunique()} 天")

            # 数据表格
            st.dataframe(
                df2,
                use_container_width=True,
                height=400,
                column_config={
                    "价格": st.column_config.NumberColumn(format="%.0f 元"),
                    "涨跌": st.column_config.TextColumn(),
                }
            )

            # 下载按钮
            csv2 = df2.to_csv(index=False).encode('utf-8-sig')
            st.download_button(
                "📥 下载 CSV",
                csv2,
                f"buerjiang_{datetime.now().strftime('%Y%m%d')}.csv",
                "text/csv"
            )

    # ========== 价格趋势图 ==========
    st.markdown("---")
    st.header("📈 价格趋势")

    # 选择要查看趋势的酒
    trend_product = st.selectbox(
        "选择产品查看趋势",
        ['飞天', '精品茅台', '生肖蛇', '散花飞天', '茅台十五年', '五粮液', '国窖1573'],
        index=0
    )

    col_chart1, col_chart2 = st.columns(2)

    with col_chart1:
        st.subheader("今日酒价")
        trend1 = get_price_trend('jinrijiujia', trend_product, days)
        if not trend1.empty:
            # 按日期分组取平均价格
            chart_data1 = trend1.groupby('date')['price'].mean().reset_index()
            chart_data1.columns = ['日期', '价格']
            st.line_chart(chart_data1.set_index('日期'))
        else:
            st.info("暂无趋势数据")

    with col_chart2:
        st.subheader("不二酱")
        trend2 = get_price_trend('buerjiang', trend_product, days)
        if not trend2.empty:
            chart_data2 = trend2.groupby('date')['price'].mean().reset_index()
            chart_data2.columns = ['日期', '价格']
            st.line_chart(chart_data2.set_index('日期'))
        else:
            st.info("暂无趋势数据")

    # 页脚
    st.markdown("---")
    st.markdown(
        f"*数据更新时间: {datetime.now().strftime('%Y-%m-%d %H:%M')} | "
        f"今日酒价: {stats1['start']} ~ {stats1['end']} | "
        f"不二酱: {stats2['start']} ~ {stats2['end']}*"
    )


if __name__ == "__main__":
    main()
