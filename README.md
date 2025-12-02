# Company Deep Analyzer

公司深度分析系统 - 基于多Agent对话的系统性公司分析框架

## 概述

这是一个使用多轮 Subagent 对话实现的公司深度分析框架。传统做法是一次性要求"全面分析"，结果得到几万字的教科书式内容——全面但无用。正确做法是设计一个 7-8 轮的对话流程，每一轮都在上一轮的基础上深挖，像剥洋葱一样逐层逼近核心。

## 架构

```
主控制器 (Orchestrator)
    │
    ├── Round 1: SceneUnderstandingAgent  (建立场景理解)
    │   └── 从抽象的"价值主张"落到具体场景
    │
    ├── Round 2: MoatAnalysisAgent        (找护城河本质)
    │   └── 反向思考：为什么客户换不掉我？
    │
    ├── Round 3: KeyMetricsAgent          (找关键指标)
    │   └── 找到那个"一票否决"的地基指标
    │
    ├── Round 4: AnalogyAgent             (用类比建立直觉)
    │   └── 用日常类比压缩复杂逻辑
    │
    ├── Round 5: RiskScenarioAgent        (设计死亡场景)
    │   └── 具体场景比风险清单有用100倍
    │
    ├── Round 6: StressTestAgent          (极限压力测试)
    │   └── 区分"股价风险"和"本金永久损失风险"
    │
    ├── Round 7: JudgmentAgent            (形成判断)
    │   └── 强迫做出明确判断，不要模棱两可
    │
    └── Round 8: MethodologyAgent (可选)  (方法论提炼)
        └── 提炼可复用的分析框架
```

## 安装

```bash
# 安装依赖
pip install anthropic rich

# 或者使用 pip install -e .
pip install -e .
```

## 使用方法

### 命令行使用

```bash
# 设置 API Key
export ANTHROPIC_API_KEY='your-api-key'

# 基本使用
python main.py "Apple"

# 指定输出文件
python main.py "Tesla" -o tesla_report.md

# 使用 Opus 模型
python main.py "Microsoft" --model claude-opus-4-20250514

# 跳过方法论提炼（第8轮）
python main.py "Google" --no-methodology

# 在控制台打印完整报告
python main.py "Amazon" --print-report
```

### 编程接口

```python
from orchestrator import Orchestrator

# 创建协调器
orchestrator = Orchestrator(
    model="claude-sonnet-4-20250514",
    include_methodology=True,
)

# 运行分析
report = orchestrator.analyze("Apple")

# 获取 Markdown 报告
markdown = report.to_markdown()
print(markdown)

# 或者保存到文件
with open("apple_analysis.md", "w") as f:
    f.write(markdown)
```

### 添加进度回调

```python
def on_start(round_num, round_name):
    print(f"开始第{round_num}轮：{round_name}")

def on_complete(round_num, round_name, success):
    status = "成功" if success else "失败"
    print(f"第{round_num}轮{status}：{round_name}")

orchestrator = Orchestrator(
    on_round_start=on_start,
    on_round_complete=on_complete,
)
```

## 项目结构

```
.
├── main.py                # 命令行入口
├── orchestrator.py        # 主控制器
├── pyproject.toml         # 项目配置
├── README.md              # 说明文档
└── agents/
    ├── __init__.py        # 模块导出
    ├── base.py            # 基础Agent类和上下文
    ├── round1_scene.py    # 第1轮：建立场景理解
    ├── round2_moat.py     # 第2轮：找护城河本质
    ├── round3_metrics.py  # 第3轮：找关键指标
    ├── round4_analogy.py  # 第4轮：用类比建立直觉
    ├── round5_risk.py     # 第5轮：设计死亡场景
    ├── round6_stress.py   # 第6轮：极限压力测试
    ├── round7_judgment.py # 第7轮：形成判断
    └── round8_methodology.py # 第8轮：方法论提炼
```

## 每轮分析的核心问题

| 轮次 | 核心问题 | 完成标志 |
|-----|---------|---------|
| 1 | 客户每天遇到什么问题愿意付钱？ | 能用大白话解释产品价值 |
| 2 | 为什么客户换不掉？ | 理解真正的护城河 |
| 3 | 哪个指标崩了其他都会崩？ | 找到一票否决指标 |
| 4 | 能用什么日常类比解释？ | 建立直觉理解 |
| 5 | 什么事件会让股价跌30%？ | 识别具体风险场景 |
| 6 | 最坏情况下会破产吗？ | 知道底线在哪里 |
| 7 | 买/卖/持有？ | 明确的投资建议 |
| 8 | 学到了什么方法论？ | 可复用的分析框架 |

## 设计理念

### 为什么这个框架有效

1. **渐进式深入**：每一步都在上一步基础上深挖，而不是并行罗列
2. **每一步都在过滤信息**：从无限可能聚焦到核心问题
3. **强迫做判断**：不是列清单，而是逼迫选择
4. **用类比建立直觉**：不是让你"理解"，而是让你"看到"

### 关键技巧

- **逼迫选择**："在这5个里，哪个是一票否决的？"
- **具体化**："给我一个生活中的类比"
- **因果推演**："如果这个崩了，会发生什么？"
- **反例验证**："历史上有没有类似公司因此失败？"

## 环境要求

- Python >= 3.10
- anthropic >= 0.40.0
- rich >= 13.0.0

## License

MIT
