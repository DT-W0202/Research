"""
Round 7: Judgment Agent (形成判断)

Purpose: After 6 rounds of deep analysis, force a clear conclusion.
A one-sentence summary tests whether you truly understand the company.

This is the synthesis round - crystallizing all insights into actionable judgment.
"""

from .base import BaseAnalysisAgent, AgentContext


class JudgmentAgent(BaseAnalysisAgent):
    """
    Seventh round agent that forms final judgment.

    This agent synthesizes all previous analysis into clear,
    actionable conclusions with specific numbers and thresholds.
    """

    @property
    def round_number(self) -> int:
        return 7

    @property
    def round_name(self) -> str:
        return "Judgment Formation"

    @property
    def round_name_cn(self) -> str:
        return "形成判断"

    def get_system_prompt(self) -> str:
        return """你是一位需要做出明确投资决策的分析师。

你的核心理念：
- 经过深入分析后，必须给出明确判断
- 一句话概括测试你是否真正理解了这家公司
- 模糊的结论等于没有结论

你的分析要求：
1. 每个答案都要简洁（不超过3句话）
2. 给出可执行的数字（具体的警戒线和阈值）
3. 不要模棱两可（禁用"可能"、"也许"、"或许"）

你的判断框架：
- 一句话概括公司本质
- 最大优势（一句话）
- 最大风险（一句话）
- 关键监控指标和警戒线
- 明确的买/卖/持有建议

重要原则：
- 给出明确的是或否
- 所有建议都要有具体数字
- 警戒线要分4档：安全/警戒/危险/清仓"""

    def get_user_prompt(self, context: AgentContext) -> str:
        previous_context = context.get_accumulated_context()

        return f"""经过6轮深入分析，我们已经从多个角度分析了【{context.company_name}】。

{previous_context}

现在请帮我做最终总结：

## 1. 一句话概括
如果用一句话概括这家公司，你会怎么说？

**【{context.company_name}】是一家_______________________________________的公司。**

（这句话应该让一个完全不了解这家公司的人立刻理解它的核心价值和风险）

## 2. 核心判断

### 最大优势
（用一句话，不超过30字）


### 最大风险
（用一句话，不超过30字）


### 核心逻辑
（用3句话解释：为什么投资这家公司可能是好主意/坏主意）
1.
2.
3.

## 3. 监控指标

### 主要监控指标
我应该盯住哪1-2个核心指标？

| 指标 | 为什么重要 | 当前值 | 数据来源 | 监控频率 |
|-----|----------|-------|---------|---------|
| | | | | |
| | | | | |

### 警戒线设置

#### 指标1：[名称]
| 状态 | 数值范围 | 应对措施 |
|-----|---------|---------|
| 安全 | | 持有/加仓 |
| 警戒 | | 密切关注，不加仓 |
| 危险 | | 减仓50% |
| 清仓 | | 全部卖出 |

#### 指标2：[名称]
| 状态 | 数值范围 | 应对措施 |
|-----|---------|---------|
| 安全 | | |
| 警戒 | | |
| 危险 | | |
| 清仓 | | |

## 4. 估值判断

### 当前估值
- 当前股价：
- 当前市值：
- 主要估值指标：
  - P/S：
  - P/E：
  - EV/EBITDA：
  - 其他相关指标：

### 估值区间
| 估值状态 | 价格区间 | 当前相对位置 |
|---------|---------|-------------|
| 严重低估 | | |
| 合理低估 | | |
| 合理估值 | | |
| 合理高估 | | |
| 严重高估 | | |

### 估值结论
当前估值处于：【    】区间

## 5. 投资建议

### 明确建议
在当前价格下，我的建议是：

**【 买入 / 持有 / 卖出 】**

### 建议理由
（3句话解释为什么）
1.
2.
3.

### 仓位建议
| 投资者类型 | 建议仓位 | 理由 |
|-----------|---------|-----|
| 保守型 | | |
| 平衡型 | | |
| 进取型 | | |

### 买入/卖出价格
- 理想买入价：
- 可接受买入价：
- 止损价：
- 目标卖出价：

## 6. 关键假设
这个投资建议基于以下关键假设。如果这些假设被证伪，结论需要重新评估：

1. 假设1：
2. 假设2：
3. 假设3：

## 7. 下一步行动
如果决定投资，接下来应该：
1.
2.
3.

如果决定不投资，应该在什么条件下重新考虑：
1.
2.
3."""

    def extract_insights(self, response: str, context: AgentContext) -> dict:
        """
        Extract the final judgment insights.
        """
        insights = {}

        context.final_judgment = response

        import re

        # Try to extract the one-liner
        one_liner_match = re.search(r'是一家(.+?)的公司', response)
        if one_liner_match:
            insights["one_liner"] = one_liner_match.group(1)

        # Try to extract the recommendation
        if "买入" in response and ("建议是" in response or "建议：" in response):
            context.action_recommendation = "买入"
            insights["recommendation"] = "buy"
        elif "卖出" in response and ("建议是" in response or "建议：" in response):
            context.action_recommendation = "卖出"
            insights["recommendation"] = "sell"
        elif "持有" in response and ("建议是" in response or "建议：" in response):
            context.action_recommendation = "持有"
            insights["recommendation"] = "hold"

        return insights
