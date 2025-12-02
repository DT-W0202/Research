"""
Round 6: Stress Test Agent (极限压力测试)

Purpose: Test the extreme case - if all the nightmare scenarios happen
together, will the company go bankrupt or just see stock price drop?

This is about distinguishing between "stock price risk" and
"permanent capital loss risk".
"""

from .base import BaseAnalysisAgent, AgentContext


class StressTestAgent(BaseAnalysisAgent):
    """
    Sixth round agent that performs extreme stress testing.

    This agent answers: "If all nightmare scenarios happen at once,
    will the company go bankrupt? What's the floor?"
    """

    @property
    def round_number(self) -> int:
        return 6

    @property
    def round_name(self) -> str:
        return "Stress Testing"

    @property
    def round_name_cn(self) -> str:
        return "极限压力测试"

    def get_system_prompt(self) -> str:
        return """你是一位专注于极限场景分析的投资分析师。

你的核心理念：
- 区分"股价风险"和"本金永久损失风险"
- 知道下限在哪里，才能决定仓位
- 最坏情况下能活着，就值得投资

你的分析框架：
1. 财务结构分析：毛利率、现金流、债务
2. 极限承压测试：收入暴跌50%能撑多久
3. 底线估值：最坏情况下值多少钱
4. 历史对照：有没有类似公司经历过类似困境

你的分析风格：
- 像信用分析师一样严苛
- 关注现金流而不是利润
- 计算"存活时间"而不是"增长空间"
- 找历史上的极端案例作参照

重要原则：
- 不要乐观假设
- 要用最坏情况下的数据
- 给出具体的"底线估值"数字"""

    def get_user_prompt(self, context: AgentContext) -> str:
        previous_context = context.get_accumulated_context()

        scenarios = context.risk_scenarios if context.risk_scenarios else ["场景1", "场景2", "场景3"]
        scenarios_text = "、".join(scenarios[:3])

        return f"""基于前五轮的分析，我已经识别了【{context.company_name}】的三个风险场景：
{scenarios_text}

{previous_context}

现在我要做极限测试：

如果这3个噩梦场景同时发生，这家公司会破产吗？
还是只是股价大跌，但业务还能活着？

请按以下结构回答：

## 1. 财务结构分析

### 收入结构
| 收入来源 | 占比 | 稳定性 | 在极端情况下会下降多少 |
|---------|-----|-------|---------------------|
| | | | |
| | | | |
| | | | |

### 成本结构
| 成本项目 | 金额/占比 | 固定/可变 | 能削减多少 |
|---------|---------|----------|----------|
| | | | |
| | | | |
| | | | |

### 现金状况
- 现金及等价物：
- 短期投资：
- 可用信贷额度：
- 总可用现金：

### 债务状况
- 短期债务：
- 长期债务：
- 债务到期时间表：
- 债务契约条款（如有）：

## 2. 极限承压测试

### 假设条件
假设三个风险场景同时发生：
- 收入下降：XX%
- 毛利率下降：XX个百分点
- 客户流失：XX%
- 融资渠道关闭

### 季度现金流推演

| 时间 | 收入 | 成本 | 现金流 | 累计现金 | 能否存活 |
|-----|-----|-----|-------|---------|---------|
| Q1 | | | | | |
| Q2 | | | | | |
| Q3 | | | | | |
| Q4 | | | | | |
| Year 2 | | | | | |

### 存活能力评估
- 不做任何调整，能撑多久：
- 如果大幅裁员（砍掉XX%人力成本），能撑多久：
- 如果卖掉非核心资产，能额外获得多少现金：
- 最长存活时间：

## 3. 最坏情况下的公司形态

如果极限压力下存活下来，这家公司会变成什么样？

### 业务规模
- 收入会缩减到：
- 员工会减少到：
- 客户会减少到：

### 市场地位
- 从[当前地位]变成[最坏情况地位]
- 会失去哪些市场：
- 会保留哪些核心业务：

### 竞争格局
- 竞争对手会如何趁机进攻：
- 公司能守住的底线是什么：

## 4. 底线估值

在最坏情况下，这家公司值多少钱？

### 清算价值
如果公司被清算：
- 有形资产价值：
- 无形资产价值：
- 负债：
- 清算价值：
- 对应每股价格：

### 压力估值
如果公司以最坏状态继续运营：
- 收入：
- 利润率：
- 给予X倍P/E（考虑到风险）：
- 压力估值：
- 对应每股价格：

### 当前估值对比
- 当前市值：
- 当前股价：
- 底线估值对应股价：
- 当前价格相对底线的安全边际：XX%

## 5. 历史对照

有没有类似的公司经历过类似的极端困境？

### 对照案例1：[公司名]
- 遭遇了什么：
- 最坏时跌了多少：
- 后来怎样了：
- 对我们的启示：

### 对照案例2：[公司名]
（同样的分析）

## 6. 极限测试结论

### 破产风险评估
- 破产概率：XX%
- 理由：

### 最坏情况总结
- 股价最多可能跌到：
- 需要多久能恢复（如果能恢复）：
- 永久性损失的风险：

### 仓位建议
基于极限测试的结果：
- 如果你是风险厌恶型投资者：
- 如果你是风险中性型投资者：
- 如果你是风险偏好型投资者："""

    def extract_insights(self, response: str, context: AgentContext) -> dict:
        """
        Extract key insights from the stress test.
        """
        insights = {}

        context.financial_resilience = response

        import re

        # Try to extract bankruptcy probability
        bankruptcy_match = re.search(r'破产概率[：:]\s*(\d+)%', response)
        if bankruptcy_match:
            insights["bankruptcy_probability"] = int(bankruptcy_match.group(1))

        # Try to extract survival time
        survival_match = re.search(r'能撑(\d+)个?(?:月|季度|年)', response)
        if survival_match:
            insights["survival_time"] = survival_match.group(1)

        # Try to extract floor valuation
        floor_match = re.search(r'底线估值[^：:]*[：:]\s*([^\n]+)', response)
        if floor_match:
            context.worst_case_valuation = floor_match.group(1)
            insights["floor_valuation"] = floor_match.group(1)

        return insights
