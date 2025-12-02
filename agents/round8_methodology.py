"""
Round 8: Methodology Agent (方法论提炼)

Purpose: Extract reusable methodology from this analysis process.
Turn this specific analysis into a generalizable framework
for analyzing other companies.

This is an optional but valuable round for building analytical capabilities.
"""

from .base import BaseAnalysisAgent, AgentContext


class MethodologyAgent(BaseAnalysisAgent):
    """
    Eighth round agent that extracts reusable methodology.

    This agent distills the thinking tools and frameworks used in
    this analysis into templates that can be applied to other companies.
    """

    @property
    def round_number(self) -> int:
        return 8

    @property
    def round_name(self) -> str:
        return "Methodology Extraction"

    @property
    def round_name_cn(self) -> str:
        return "方法论提炼"

    def get_system_prompt(self) -> str:
        return """你是一位专注于提炼方法论的分析师。

你的核心能力：
- 从具体分析中提炼出可复用的思考框架
- 将隐性知识转化为显性知识
- 创建可操作的分析模板

你的提炼原则：
1. 每个工具都要有具体的使用场景
2. 每个框架都要有清晰的步骤
3. 提供可直接使用的提问模板

你的分析风格：
- 从具体到抽象，再回到具体
- 用这次分析的例子来说明方法论
- 确保方法论可迁移到其他公司

重要原则：
- 不是总结本次分析，而是提炼方法
- 每个工具都要能独立使用
- 要给出"什么时候用"的明确指引"""

    def get_user_prompt(self, context: AgentContext) -> str:
        previous_context = context.get_accumulated_context()

        return f"""我们刚刚完成了对【{context.company_name}】的7轮深度分析。

{previous_context}

最后一个问题：

回顾我们整个对话过程，请总结：
这次分析用了哪些思考方法？
这些方法能推广到分析其他公司吗？

请按以下结构回答：

## 1. 核心思考工具提炼

### 工具1：[名称]（例如："客户场景还原法"）

**定义：**
一句话解释这是什么方法

**核心问题：**
用这个工具时要问的关键问题

**使用步骤：**
1. 第一步：
2. 第二步：
3. 第三步：

**在这次分析中的应用：**
（举例说明我们是怎么用这个工具分析{context.company_name}的）

**适用场景：**
什么类型的公司/问题适合用这个工具？

**注意事项：**
使用这个工具时要避免什么陷阱？

---

### 工具2：[名称]（例如："反向护城河测试"）

（同样的结构）

---

### 工具3：[名称]（例如："一票否决指标法"）

（同样的结构）

---

### 工具4：[名称]（例如："类比压缩法"）

（同样的结构）

---

### 工具5：[名称]（例如："死亡场景推演"）

（同样的结构）

---

## 2. 分析流程模板

下次分析任何公司时，可以按照以下顺序提问：

### 阶段1：理解业务（第1-2轮）

**核心目标：** 建立对公司的直觉理解

**关键问题清单：**
1.
2.
3.
4.
5.

**完成标志：** 能用大白话向外行解释这家公司做什么

---

### 阶段2：识别关键（第3-4轮）

**核心目标：** 找到最关键的指标和理解框架

**关键问题清单：**
1.
2.
3.
4.
5.

**完成标志：** 能用一个类比解释公司的核心逻辑

---

### 阶段3：压力测试（第5-6轮）

**核心目标：** 理解风险和极限情况

**关键问题清单：**
1.
2.
3.
4.
5.

**完成标志：** 知道最坏情况下会发生什么，以及底线在哪里

---

### 阶段4：形成判断（第7轮）

**核心目标：** 得出可执行的结论

**关键问题清单：**
1.
2.
3.
4.
5.

**完成标志：** 有明确的买/卖/持有建议和具体的监控指标

---

## 3. 通用提问模板

以下是可以直接复制使用的提问模板：

### 模板1：快速理解一家公司
```
我要快速理解[公司名]。请回答：
1. 这家公司解决什么问题？（用大白话，不要术语）
2. 谁在付钱？为什么愿意付？
3. 一句话类比：这家公司就像是____领域的____。
```

### 模板2：识别护城河
```
关于[公司名]的护城河：
1. 如果这家公司明天消失，客户会怎么办？
2. 换到最强竞品需要多少时间和成本？
3. 护城河的"半衰期"是多久？
```

### 模板3：找关键指标
```
[公司名]最重要的3个指标是什么？
在这3个里，哪个是"地基"——如果它崩了，其他都会崩？
这个指标的警戒线是多少？
```

### 模板4：压力测试
```
设计3个具体场景，让[公司名]股价跌30%以上。
每个场景要有：
- 具体触发事件（像新闻标题一样）
- 时间线推演（1个月/6个月/12个月/24个月）
- 现在能观察到的前兆信号
```

### 模板5：极限测试
```
如果[公司名]收入暴跌50%：
1. 能撑多久？
2. 会变成什么样的公司？
3. 最坏情况下值多少钱？
```

### 模板6：快速判断
```
关于[公司名]：
1. 一句话概括？
2. 最大优势？（一句话）
3. 最大风险？（一句话）
4. 当前估值下该买/持有/卖？
5. 监控什么指标？警戒线是多少？
```

---

## 4. 工具选择指南

| 分析目的 | 推荐工具 | 关键问题 |
|---------|---------|---------|
| 快速了解公司 | 客户场景还原法 | 谁在付钱？为什么？ |
| 评估竞争力 | 反向护城河测试 | 客户为什么离不开？ |
| 找关键指标 | 一票否决指标法 | 什么崩了其他都会崩？ |
| 建立直觉 | 类比压缩法 | 像什么日常事物？ |
| 评估风险 | 死亡场景推演 | 什么事件让股价跌30%？ |
| 评估极限 | 极限承压测试 | 最坏情况会怎样？ |
| 做出判断 | 强迫选择法 | 买/卖/持有？ |

---

## 5. 方法论的局限性

这套方法论在以下情况可能需要调整：

1. 早期创业公司：
   - 调整方向：
   - 替代方法：

2. 周期性行业：
   - 调整方向：
   - 替代方法：

3. 政策敏感型公司：
   - 调整方向：
   - 替代方法：

4. 复杂控股公司：
   - 调整方向：
   - 替代方法：

---

## 6. 持续改进

这次分析中发现的、可以纳入未来分析框架的新洞察：

1. 新发现1：
2. 新发现2：
3. 新发现3：

下次分析时要特别注意的：

1. 注意点1：
2. 注意点2：
3. 注意点3："""

    def extract_insights(self, response: str, context: AgentContext) -> dict:
        """
        Extract methodology insights.
        """
        insights = {}

        # Try to extract tool names
        import re
        tool_matches = re.findall(r'###\s*工具\d+[：:]\s*(.+?)(?:\n|$)', response)
        if tool_matches:
            context.methodology_tools = tool_matches
            insights["tools"] = tool_matches

        return insights
