"""
Round 5: Risk Scenario Agent (设计死亡场景)

Purpose: Design specific scenarios that could cause the stock price
to drop 30%+. Concrete scenarios are 100x more useful than
abstract "risk lists".

This round builds on all previous insights to stress-test the company.
"""

from .base import BaseAnalysisAgent, AgentContext


class RiskScenarioAgent(BaseAnalysisAgent):
    """
    Fifth round agent that designs specific risk scenarios.

    This agent answers: "What specific events could cause this company's
    stock to drop 30%+? Give me the timeline and warning signs."
    """

    @property
    def round_number(self) -> int:
        return 5

    @property
    def round_name(self) -> str:
        return "Risk Scenario Design"

    @property
    def round_name_cn(self) -> str:
        return "设计死亡场景"

    def get_system_prompt(self) -> str:
        return """你是一位专注于风险分析的投资分析师，擅长设计压力测试场景。

你的核心理念：
- 具体场景比"风险清单"有用100倍
- 好的风险分析要有：触发事件、时间线推演、前兆信号
- 不是列出"可能的风险"，而是设计"如果发生这件事，会怎样"

你的分析框架：
1. 设计具体的触发事件（像写新闻标题一样具体）
2. 推演时间线：发生后1个月→6个月→12个月→24个月
3. 评估概率和影响
4. 识别前兆信号（现在就能观察到的）

你的分析风格：
- 像写惊悚小说一样描述场景
- 每个场景都要有具体的日期和事件
- 从公司最脆弱的地方下手
- 同时考虑内部风险和外部风险

重要原则：
- 不要写"竞争加剧"这种抽象风险
- 要写"2025年Q3，XXX公司发布了YYY产品"这种具体事件
- 每个场景都要可验证、可监控"""

    def get_user_prompt(self, context: AgentContext) -> str:
        previous_context = context.get_accumulated_context()

        return f"""基于前四轮的分析，我已经深入理解了【{context.company_name}】。

{previous_context}

现在我要做压力测试：

请设计3个具体场景，每个场景下这家公司的股价会跌30%以上。

请按以下结构回答：

---

## 场景1：[给这个场景起一个新闻标题式的名字]

### 触发事件
- 具体事件：[像写新闻标题一样，写一个具体的事件]
- 可能发生时间：[给出一个具体的时间范围]
- 为什么这个事件可能发生：

### 时间线推演
#### 触发时刻
- 发生了什么
- 市场的即时反应

#### 1个月后
- 公司的应对措施
- 客户的反应
- 竞争对手的动作
- 财务影响

#### 6个月后
- 问题是否扩大
- 公司能否止血
- 市场情绪变化

#### 12个月后
- 长期影响评估
- 公司的状态

#### 24个月后
- 最终结局

### 影响评估
| 维度 | 影响 |
|-----|-----|
| 收入影响 | |
| 利润影响 | |
| 估值影响 | |
| 股价预计下跌 | |

### 前兆信号
现在就能观察到的、预示这个风险可能发生的信号：
1. 信号1：[在哪里能看到] [什么情况说明危险]
2. 信号2：
3. 信号3：

### 概率评估
- 未来2年内发生的概率：XX%
- 理由：

---

## 场景2：[新闻标题式名字]

（同样的结构）

---

## 场景3：[新闻标题式名字]

（同样的结构）

---

## 风险场景汇总

| 场景 | 概率 | 股价影响 | 最重要的前兆信号 |
|-----|-----|---------|----------------|
| 场景1 | | | |
| 场景2 | | | |
| 场景3 | | | |

## 综合风险评估
1. 最可能发生的是哪个场景？为什么？
2. 破坏力最大的是哪个场景？为什么？
3. 有没有多个场景可能同时发生的情况？

## 风险监控清单
我应该定期监控哪些信息源来跟踪这些风险？

| 风险 | 监控指标 | 数据来源 | 监控频率 |
|-----|---------|---------|---------|
| | | | |
| | | | |
| | | | |"""

    def extract_insights(self, response: str, context: AgentContext) -> dict:
        """
        Extract key insights from the risk scenarios.
        """
        insights = {}

        # Store risk scenarios
        import re

        # Try to extract scenario names/headlines
        scenario_matches = re.findall(r'##\s*场景\d+[：:]\s*(.+?)(?:\n|$)', response)
        if scenario_matches:
            context.risk_scenarios = scenario_matches
            insights["scenarios"] = scenario_matches

        # Try to extract probabilities
        prob_matches = re.findall(r'概率[：:]\s*(\d+)%', response)
        if prob_matches:
            insights["probabilities"] = [int(p) for p in prob_matches]

        # Try to extract stock impact
        impact_matches = re.findall(r'股价(?:预计)?下跌[：:]\s*(\d+)%', response)
        if impact_matches:
            insights["stock_impacts"] = [int(i) for i in impact_matches]

        return insights
