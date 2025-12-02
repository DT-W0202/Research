"""
Base Agent class for the Company Deep Analyzer system.

Each round of analysis is implemented as a specialized subagent that inherits
from BaseAnalysisAgent. The agents are designed to be executed sequentially,
with each round building upon the insights from previous rounds.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Optional
import anthropic


@dataclass
class AgentContext:
    """
    Context object that carries information between agent rounds.

    This context accumulates insights and findings from each round,
    allowing subsequent agents to build upon previous analysis.
    """
    company_name: str
    round_results: dict = field(default_factory=dict)

    # Key insights extracted from each round
    customer_scenario: Optional[str] = None  # From Round 1
    core_pain_point: Optional[str] = None    # From Round 1
    value_proposition: Optional[str] = None  # From Round 1

    moat_description: Optional[str] = None   # From Round 2
    irreplaceable_dimension: Optional[str] = None  # From Round 2

    key_metrics: list = field(default_factory=list)  # From Round 3
    critical_metric: Optional[str] = None    # From Round 3 (一票否决指标)

    analogy: Optional[str] = None            # From Round 4
    historical_failure: Optional[str] = None # From Round 4

    risk_scenarios: list = field(default_factory=list)  # From Round 5

    financial_resilience: Optional[str] = None  # From Round 6
    worst_case_valuation: Optional[str] = None  # From Round 6

    final_judgment: Optional[str] = None     # From Round 7
    action_recommendation: Optional[str] = None  # From Round 7

    methodology_tools: list = field(default_factory=list)  # From Round 8

    def get_accumulated_context(self) -> str:
        """
        Generate a summary of all accumulated insights for use by subsequent agents.
        """
        parts = [f"公司：{self.company_name}\n"]

        if self.customer_scenario:
            parts.append(f"【客户场景】\n{self.customer_scenario}\n")

        if self.core_pain_point:
            parts.append(f"【核心痛点】\n{self.core_pain_point}\n")

        if self.value_proposition:
            parts.append(f"【价值主张】\n{self.value_proposition}\n")

        if self.moat_description:
            parts.append(f"【护城河描述】\n{self.moat_description}\n")

        if self.irreplaceable_dimension:
            parts.append(f"【不可替代维度】\n{self.irreplaceable_dimension}\n")

        if self.key_metrics:
            parts.append(f"【关键指标】\n" + "\n".join(f"- {m}" for m in self.key_metrics) + "\n")

        if self.critical_metric:
            parts.append(f"【一票否决指标】\n{self.critical_metric}\n")

        if self.analogy:
            parts.append(f"【核心类比】\n{self.analogy}\n")

        if self.historical_failure:
            parts.append(f"【历史反例】\n{self.historical_failure}\n")

        if self.risk_scenarios:
            parts.append(f"【风险场景】\n" + "\n".join(f"- {r}" for r in self.risk_scenarios) + "\n")

        if self.financial_resilience:
            parts.append(f"【财务韧性】\n{self.financial_resilience}\n")

        if self.worst_case_valuation:
            parts.append(f"【最坏估值】\n{self.worst_case_valuation}\n")

        return "\n".join(parts)


@dataclass
class RoundResult:
    """
    Result from a single round of analysis.
    """
    round_number: int
    round_name: str
    round_name_cn: str
    full_response: str
    key_insights: dict = field(default_factory=dict)
    success: bool = True
    error_message: Optional[str] = None


class BaseAnalysisAgent(ABC):
    """
    Abstract base class for all analysis agents.

    Each agent implements a specific round of the company analysis framework.
    Agents are designed to:
    1. Receive context from previous rounds
    2. Execute their specific analysis task
    3. Extract key insights for subsequent rounds
    4. Return a complete, unabridged response
    """

    def __init__(
        self,
        client: anthropic.Anthropic,
        model: str = "claude-sonnet-4-20250514",
        max_tokens: int = 8192,
    ):
        self.client = client
        self.model = model
        self.max_tokens = max_tokens

    @property
    @abstractmethod
    def round_number(self) -> int:
        """Return the round number (1-8)."""
        pass

    @property
    @abstractmethod
    def round_name(self) -> str:
        """Return the English name of this round."""
        pass

    @property
    @abstractmethod
    def round_name_cn(self) -> str:
        """Return the Chinese name of this round."""
        pass

    @abstractmethod
    def get_system_prompt(self) -> str:
        """
        Return the system prompt for this agent.

        The system prompt defines the agent's role, expertise, and behavior.
        """
        pass

    @abstractmethod
    def get_user_prompt(self, context: AgentContext) -> str:
        """
        Generate the user prompt based on the current context.

        This prompt incorporates insights from previous rounds and
        specifies exactly what analysis this round should perform.
        """
        pass

    @abstractmethod
    def extract_insights(self, response: str, context: AgentContext) -> dict:
        """
        Extract key insights from the response to update the context.

        These insights will be used by subsequent agents to build
        upon this round's analysis.
        """
        pass

    def execute(self, context: AgentContext) -> RoundResult:
        """
        Execute this agent's analysis round.

        This method:
        1. Constructs the prompts
        2. Calls the Claude API
        3. Extracts insights
        4. Returns the complete result
        """
        try:
            system_prompt = self.get_system_prompt()
            user_prompt = self.get_user_prompt(context)

            message = self.client.messages.create(
                model=self.model,
                max_tokens=self.max_tokens,
                system=system_prompt,
                messages=[
                    {"role": "user", "content": user_prompt}
                ]
            )

            # Extract text content from response
            response_text = ""
            for block in message.content:
                if block.type == "text":
                    response_text += block.text

            # Extract key insights and update context
            insights = self.extract_insights(response_text, context)

            # Store result in context
            context.round_results[self.round_number] = response_text

            return RoundResult(
                round_number=self.round_number,
                round_name=self.round_name,
                round_name_cn=self.round_name_cn,
                full_response=response_text,
                key_insights=insights,
                success=True
            )

        except Exception as e:
            return RoundResult(
                round_number=self.round_number,
                round_name=self.round_name,
                round_name_cn=self.round_name_cn,
                full_response="",
                success=False,
                error_message=str(e)
            )
