"""
Round 2: Moat Analysis Agent (找护城河本质)

Purpose: Identify the true competitive moat by thinking in reverse -
not "what do I have" but "why can't customers leave me".

This round builds on the customer scenario from Round 1 to understand
what makes this company irreplaceable.
"""

from .base import BaseAnalysisAgent, AgentContext


class MoatAnalysisAgent(BaseAnalysisAgent):
    """
    Second round agent that identifies the true competitive moat.

    This agent answers: "If this product didn't exist, what would customers do?
    And why can't they just switch to alternatives?"
    """

    @property
    def round_number(self) -> int:
        return 2

    @property
    def round_name(self) -> str:
        return "Moat Analysis"

    @property
    def round_name_cn(self) -> str:
        return "找护城河本质"

    def get_system_prompt(self) -> str:
        return """你是一位专注于竞争战略的商业分析师，擅长识别企业的真正护城河。

你的核心理念：
护城河不是"我有什么"，而是"为什么客户换不掉我"。
真正的护城河是从客户的角度来看的，而不是从公司的角度。

你的分析框架：
1. 替代方案分析：如果这个产品消失了，客户会怎么办？
2. 转换成本分析：客户换掉它需要付出什么代价？
3. 不可替代性分析：在哪个维度上，这个产品是无法被替代的？

你的分析风格：
- 反向思考：先想客户能怎么离开，再想为什么离不开
- 具体量化：转换成本要用具体的时间、金钱、人力来衡量
- 区分真假护城河：
  - 真护城河：网络效应、规模经济、品牌心智、专利/牌照
  - 假护城河：技术领先（可追赶）、先发优势（可超越）、资金优势（可融资）

重要原则：
- 不要列举公司的优势清单
- 要从客户决策的角度分析
- 每个论点都要有具体的反例或对比"""

    def get_user_prompt(self, context: AgentContext) -> str:
        previous_context = context.get_accumulated_context()

        return f"""基于上一轮的分析，我已经理解了【{context.company_name}】的客户场景。

{previous_context}

现在进入第二个问题：

如果没有这家公司的产品，客户会怎么办？他们有哪些替代方案？
为什么客户不能继续用旧方法或者换成竞品？

请按以下结构回答：

## 1. 替代方案全景图
列出客户可以选择的所有替代方案：
- 替代方案A：[名称]
- 替代方案B：[名称]
- 替代方案C：[名称]
- 替代方案D：不用任何产品，自己解决

## 2. 每个替代方案的深度分析
对每个替代方案，分析：
### 替代方案A：[名称]
- 产品/服务描述
- 能解决原问题的程度（百分比估算）
- 核心不足是什么？
- 什么类型的客户会选择它？
- 市场份额和趋势

（对B、C、D同样分析）

## 3. 转换成本分析
如果现有客户要换到最强的竞品，需要付出什么代价？

| 成本类型 | 具体内容 | 量化估算 |
|---------|---------|---------|
| 时间成本 | | |
| 金钱成本 | | |
| 学习成本 | | |
| 数据迁移成本 | | |
| 关系成本 | | |
| 风险成本 | | |

## 4. 不可替代性分析
这家公司的产品在哪个维度上是"不可替代"的？

请从以下维度逐一分析：
- 网络效应：用户越多，产品越好用吗？
- 规模经济：规模越大，成本越低吗？
- 品牌心智：在客户心中占据了什么独特位置？
- 技术壁垒：有什么技术是别人短期内无法复制的？
- 数据壁垒：积累了什么数据是别人没有的？
- 生态系统：构建了什么生态是别人无法复制的？

## 5. 护城河强度评估
用1-10分评估护城河强度，并说明理由：
- 评分：X/10
- 理由：
- 护城河的"半衰期"：这个护城河能维持多久？

## 6. 最大威胁
如果有一家公司要打破这个护城河，它最可能从哪个角度进攻？
- 可能的进攻者是谁？
- 进攻策略会是什么？
- 成功概率有多大？"""

    def extract_insights(self, response: str, context: AgentContext) -> dict:
        """
        Extract key insights about competitive moat.
        """
        insights = {}

        context.moat_description = response

        # Try to extract moat strength score
        import re
        score_match = re.search(r'评分[：:]\s*(\d+)/10', response)
        if score_match:
            insights["moat_score"] = int(score_match.group(1))

        # Look for key moat types mentioned
        moat_types = []
        if "网络效应" in response:
            moat_types.append("network_effects")
        if "规模经济" in response:
            moat_types.append("economies_of_scale")
        if "品牌心智" in response:
            moat_types.append("brand")
        if "技术壁垒" in response:
            moat_types.append("technology")
        if "数据壁垒" in response:
            moat_types.append("data")
        if "生态系统" in response:
            moat_types.append("ecosystem")

        insights["moat_types"] = moat_types

        # Extract the irreplaceable dimension
        if "不可替代" in response:
            # Find the paragraph discussing irreplaceability
            irreplaceable_section = response.split("不可替代")[1][:500] if "不可替代" in response else ""
            context.irreplaceable_dimension = irreplaceable_section[:200] if irreplaceable_section else None

        return insights
