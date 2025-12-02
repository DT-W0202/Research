"""
Round 4: Analogy Agent (用类比建立直觉)

Purpose: Use analogies to compress complex business logic into
intuitive mental models. A good analogy can convey what
paragraphs of explanation cannot.

This round builds on the critical metric from Round 3 to create
intuitive understanding.
"""

from .base import BaseAnalysisAgent, AgentContext


class AnalogyAgent(BaseAnalysisAgent):
    """
    Fourth round agent that builds intuition through analogies.

    This agent answers: "Can you use a daily-life analogy to help me
    understand why this metric is so critical?"
    """

    @property
    def round_number(self) -> int:
        return 4

    @property
    def round_name(self) -> str:
        return "Analogy Building"

    @property
    def round_name_cn(self) -> str:
        return "用类比建立直觉"

    def get_system_prompt(self) -> str:
        return """你是一位善于用类比解释复杂概念的商业分析师。

你的核心能力：
- 将复杂的商业逻辑压缩成一个生动的画面
- 用日常生活中的场景来解释抽象的商业概念
- 找到那个"恍然大悟"的类比

你的类比原则：
1. 类比要足够日常——最好是每天都能看到的东西
2. 类比要抓住本质——不只是表面相似，而是结构性相似
3. 类比要有预测力——通过类比能推断出新的结论

经典的商业类比案例：
- "鱼钩与倒刺"：订阅制SaaS就像有倒刺的鱼钩，进去容易出来难
- "引力与推进器"：平台的网络效应就像引力，规模越大引力越强
- "收费站"：垄断性基础设施就像高速公路收费站，绑架刚需
- "滚雪球"：规模经济就像滚雪球，坡道越长雪球越大

你的分析风格：
- 不是解释，而是让人"看到"
- 用一个画面胜过千言万语
- 类比之后，用具体案例验证

重要原则：
- 如果第一个类比不够好，换一个更好的
- 每个类比都要能推导出具体的投资结论
- 一定要配上历史反例"""

    def get_user_prompt(self, context: AgentContext) -> str:
        previous_context = context.get_accumulated_context()

        critical_metric = context.critical_metric or "核心指标"

        return f"""基于前三轮的分析，我已经了解【{context.company_name}】的关键指标是【{critical_metric}】。

{previous_context}

但我还没有完全理解为什么这个指标这么重要。

请用一个生活中的类比来帮我理解：
1. 为什么这个指标这么重要？
2. 它跟其他指标的关系是什么？

请按以下结构回答：

## 1. 核心类比
给我一个具体的、日常的类比来解释这个指标的重要性。

类比：[用一句话描述你的类比]

### 类比的展开
- 在这个类比中，公司像什么？
- 客户像什么？
- 竞争对手像什么？
- 关键指标对应类比中的什么？

### 类比的推论
如果这个类比成立，我们可以推导出什么结论？
1. 结论1：
2. 结论2：
3. 结论3：

## 2. 备用类比
如果上面的类比还不够直观，这里是另一个角度的类比：

类比：[第二个类比]

展开说明：

## 3. 指标关系的类比解释
用类比解释这个关键指标和其他指标的关系：

- [关键指标] 就像 [类比中的什么]
- [其他指标1] 就像 [类比中的什么]
- [其他指标2] 就像 [类比中的什么]

它们之间的关系是：

## 4. 历史反例
有没有类似的公司因为这个"类比逻辑"出问题而失败？

### 反例1：[公司名]
- 发生了什么？
- 用我们的类比来解释，就是：
- 结果如何？
- 我们能学到什么？

### 反例2：[公司名]
（同样的分析）

## 5. 类比的局限性
这个类比有什么局限？在什么情况下这个类比会失效？

## 6. 一句话总结
如果要用一句话向一个完全不懂这个行业的人解释这家公司，你会说：

"【{context.company_name}】就像是________________________________。"

这句话应该让人立刻理解这家公司的核心逻辑。"""

    def extract_insights(self, response: str, context: AgentContext) -> dict:
        """
        Extract key insights from the analogy analysis.
        """
        insights = {}

        # Store the analogy
        context.analogy = response

        # Try to extract the main analogy
        import re

        # Look for the one-sentence summary
        summary_match = re.search(r'就像是[_\s]*(.+?)[。\.]', response)
        if summary_match:
            insights["one_liner"] = summary_match.group(1)

        # Look for historical failure examples
        failure_match = re.search(r'反例\d+[：:]\s*【?(.+?)】?(?:\n|$)', response)
        if failure_match:
            context.historical_failure = failure_match.group(1)
            insights["failure_example"] = failure_match.group(1)

        return insights
