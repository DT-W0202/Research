"""
Round 1: Scene Understanding Agent (建立场景理解)

Purpose: Transform abstract "value propositions" into concrete scenarios,
establishing an intuitive anchor point for understanding the company.

This is the foundation round - it establishes the customer context that
all subsequent analysis will build upon.
"""

from .base import BaseAnalysisAgent, AgentContext


class SceneUnderstandingAgent(BaseAnalysisAgent):
    """
    First round agent that establishes concrete customer scenarios.

    This agent answers: "What specific daily problem does the customer face
    that makes them willing to pay for this product?"
    """

    @property
    def round_number(self) -> int:
        return 1

    @property
    def round_name(self) -> str:
        return "Scene Understanding"

    @property
    def round_name_cn(self) -> str:
        return "建立场景理解"

    def get_system_prompt(self) -> str:
        return """你是一位资深的商业分析师，专注于理解企业的客户价值主张。

你的核心能力是：
1. 将抽象的商业概念转化为具体、可感知的客户场景
2. 用大白话解释复杂的业务模式，避免行业术语
3. 量化价值——用数据说明产品/服务带来的具体改变
4. 区分"锦上添花"和"雪中送炭"的价值

你的分析风格：
- 从客户视角出发，而非公司视角
- 用"一天的生活"来描述场景，让读者能够想象
- 强调对比：使用前 vs 使用后
- 给出具体数据和真实案例

重要原则：
- 不要给出泛泛而谈的描述
- 不要使用"提高效率"、"优化流程"等抽象词汇
- 每个论点都要有具体的场景或数据支撑
- 如果信息不足，明确指出并给出合理推测"""

    def get_user_prompt(self, context: AgentContext) -> str:
        return f"""我要分析【{context.company_name}】这家公司。

先别给我全面分析。请回答一个具体问题：

假设我是这家公司的典型客户，我每天遇到的什么具体问题，让我愿意付钱给它？

请按以下结构回答：

## 1. 典型客户画像
描述这家公司的主要客户是谁（具体到行业、规模、角色）

## 2. 一天的具体场景
用讲故事的方式，描述客户在没有这个产品时的一天：
- 早上会遇到什么问题？
- 这个问题有多痛？会造成什么后果？
- 客户之前是怎么凑合解决的？

## 3. 使用产品后的改变
同样用讲故事的方式，描述使用产品后：
- 同样的场景变成什么样了？
- 具体省了多少时间/钱/人力？
- 有没有以前做不到、现在能做到的事？

## 4. 价值量化
- 给出具体的数据（比如：节省X小时/天，降低X%成本，提升X%效率）
- 如果可能，给出一个真实的客户案例或引用

## 5. 是"止痛药"还是"维生素"？
这个产品解决的是：
- 止痛药：不用就很痛，必须要有
- 维生素：用了更好，不用也行
给出你的判断和理由。

要求：
- 不要用行业术语，假设我完全不懂这个行业
- 每个部分都要有具体的场景描述，不要抽象概括
- 如果某些信息你不确定，明确说明并给出合理推测"""

    def extract_insights(self, response: str, context: AgentContext) -> dict:
        """
        Extract key insights about customer scenario and value proposition.
        """
        insights = {}

        # Store the full response as customer scenario
        context.customer_scenario = response

        # Try to identify key elements (simplified extraction)
        if "止痛药" in response:
            context.value_proposition = "止痛药型产品（刚需）"
            insights["product_type"] = "painkiller"
        elif "维生素" in response:
            context.value_proposition = "维生素型产品（可选）"
            insights["product_type"] = "vitamin"

        # Extract any quantified values mentioned
        import re
        percentages = re.findall(r'(\d+(?:\.\d+)?%)', response)
        if percentages:
            insights["quantified_values"] = percentages

        time_savings = re.findall(r'节省.*?(\d+).*?(?:小时|分钟|天)', response)
        if time_savings:
            insights["time_savings"] = time_savings

        return insights
