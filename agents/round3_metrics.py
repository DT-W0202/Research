"""
Round 3: Key Metrics Agent (找关键指标)

Purpose: Among all the "seemingly important" metrics, find the ONE
"veto power" metric - the foundation that, if it crumbles,
nothing else matters.

This round builds on the moat analysis to identify what to monitor.
"""

from .base import BaseAnalysisAgent, AgentContext


class KeyMetricsAgent(BaseAnalysisAgent):
    """
    Third round agent that identifies the critical metrics.

    This agent answers: "Among all the key metrics, which ONE is the
    'foundation' that determines everything else?"
    """

    @property
    def round_number(self) -> int:
        return 3

    @property
    def round_name(self) -> str:
        return "Key Metrics"

    @property
    def round_name_cn(self) -> str:
        return "找关键指标"

    def get_system_prompt(self) -> str:
        return """你是一位资深的投资分析师，专注于识别企业的核心运营指标。

你的核心理念：
- 每家公司都有很多"看起来重要"的指标，但只有一个是"地基"
- 地基指标如果崩了，其他指标再好也没用
- 你要做的是帮投资者区分"地基"和"房子"

你的分析框架：
1. 梳理所有关键指标
2. 逐一做"崩塌测试"：如果这个指标变坏，会发生什么？
3. 找出那个"一票否决"的指标
4. 建立指标之间的因果关系

你的分析风格：
- 不是列清单，而是做判断
- 用具体案例说明指标的重要性
- 区分领先指标和滞后指标
- 给出可操作的监控建议

重要原则：
- 逼自己只选一个"地基"指标
- 每个指标都要给出"崩塌场景"
- 用历史案例验证你的判断"""

    def get_user_prompt(self, context: AgentContext) -> str:
        previous_context = context.get_accumulated_context()

        return f"""基于前两轮的分析，我已经理解了【{context.company_name}】的客户场景和护城河。

{previous_context}

现在进入第三个问题：

这家公司有哪3-5个关键运营指标？
在这些指标里，哪一个是"一票否决"的？
也就是说，如果这个指标变坏，其他指标再好也没用？

请按以下结构回答：

## 1. 关键指标全景图
列出这家公司最重要的3-5个运营/财务指标：

| 指标名称 | 定义 | 当前值 | 行业平均 | 趋势 |
|---------|-----|-------|---------|-----|
| | | | | |
| | | | | |
| | | | | |
| | | | | |
| | | | | |

## 2. 指标因果关系图
这些指标之间是什么关系？哪个是因，哪个是果？

请画出指标之间的因果链：
[指标A] → 影响 → [指标B] → 影响 → [指标C]

## 3. 崩塌测试
对每个指标，做一个"假如它崩了"的推演：

### 指标1：[名称]
- 如果这个指标下降50%，会发生什么？
- 会影响哪些其他指标？
- 公司能活下去吗？
- 历史上有没有类似案例？

### 指标2：[名称]
（同样的分析）

### 指标3：[名称]
（同样的分析）

（对所有指标进行相同分析）

## 4. "一票否决"指标的选择
在以上所有指标中，我选择【XXX】作为"一票否决"指标。

理由：
1. 为什么它是"地基"而不是"房子"？
2. 它崩塌会如何导致其他指标连锁崩塌？
3. 有没有历史反例证明它的重要性？

## 5. 领先指标 vs 滞后指标
区分这些指标：

| 指标 | 类型 | 说明 |
|-----|-----|-----|
| | 领先指标 | 能提前预警问题 |
| | 滞后指标 | 问题发生后才会变化 |

## 6. 监控建议
对于"一票否决"指标：
- 安全区间：[数值范围]
- 警戒区间：[数值范围]
- 危险区间：[数值范围]
- 建议监控频率：
- 数据来源："""

    def extract_insights(self, response: str, context: AgentContext) -> dict:
        """
        Extract key insights about metrics.
        """
        insights = {}

        # Store all key metrics mentioned
        import re

        # Look for metrics in the table or list format
        metrics = []

        # Try to find the critical metric (一票否决)
        critical_match = re.search(r'选择【(.+?)】作为"一票否决"', response)
        if critical_match:
            context.critical_metric = critical_match.group(1)
            insights["critical_metric"] = critical_match.group(1)

        # Extract mentioned metric names
        metric_patterns = [
            r'指标\d+[：:]\s*【?(.+?)】?(?:\n|$)',
            r'\|\s*([A-Za-z\u4e00-\u9fff]+(?:\s*[A-Za-z\u4e00-\u9fff]+)*)\s*\|',
        ]

        for pattern in metric_patterns:
            matches = re.findall(pattern, response)
            metrics.extend(matches)

        # Clean and deduplicate
        metrics = list(set([m.strip() for m in metrics if m.strip() and len(m.strip()) > 1]))
        context.key_metrics = metrics[:10]  # Limit to 10 metrics
        insights["all_metrics"] = metrics

        return insights
