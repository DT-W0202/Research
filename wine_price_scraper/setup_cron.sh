#!/bin/bash
# 设置每日自动抓取定时任务

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PYTHON_PATH=$(which python3 || which python)
LOG_FILE="$SCRIPT_DIR/logs/cron.log"

echo "========================================"
echo "酒价自动抓取 - 定时任务配置"
echo "========================================"
echo ""
echo "脚本目录: $SCRIPT_DIR"
echo "Python路径: $PYTHON_PATH"
echo ""

# 创建日志目录
mkdir -p "$SCRIPT_DIR/logs"

# 生成cron命令
CRON_CMD="0 9 * * * cd $SCRIPT_DIR && $PYTHON_PATH daily_scraper.py today >> $LOG_FILE 2>&1"

echo "将添加以下定时任务:"
echo "  $CRON_CMD"
echo ""
echo "说明: 每天早上9:00自动运行抓取"
echo ""

read -p "确认添加? (y/n): " confirm

if [ "$confirm" = "y" ] || [ "$confirm" = "Y" ]; then
    # 添加到crontab
    (crontab -l 2>/dev/null | grep -v "daily_scraper.py"; echo "$CRON_CMD") | crontab -
    echo ""
    echo "✓ 定时任务已添加"
    echo ""
    echo "查看当前定时任务: crontab -l"
    echo "删除定时任务: crontab -e (手动删除对应行)"
else
    echo "已取消"
fi
