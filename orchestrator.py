"""
Orchestrator for the Company Deep Analyzer system.

The Orchestrator manages the sequential execution of all 8 analysis rounds,
passing context between agents and collecting the final comprehensive report.
"""

from dataclasses import dataclass, field
from typing import Optional, Callable
from datetime import datetime
import anthropic

from agents import (
    AgentContext,
    RoundResult,
    SceneUnderstandingAgent,
    MoatAnalysisAgent,
    KeyMetricsAgent,
    AnalogyAgent,
    RiskScenarioAgent,
    StressTestAgent,
    JudgmentAgent,
    MethodologyAgent,
)


@dataclass
class AnalysisReport:
    """
    Complete analysis report containing results from all rounds.
    """
    company_name: str
    timestamp: str
    rounds: list = field(default_factory=list)
    context: Optional[AgentContext] = None
    total_duration_seconds: float = 0
    success: bool = True
    error_message: Optional[str] = None

    def to_markdown(self) -> str:
        """
        Generate a complete markdown report from all rounds.
        """
        lines = [
            f"# {self.company_name} 深度分析报告",
            f"",
            f"**生成时间：** {self.timestamp}",
            f"**分析耗时：** {self.total_duration_seconds:.1f} 秒",
            f"",
            f"---",
            f"",
        ]

        # Table of contents
        lines.extend([
            "## 目录",
            "",
        ])
        for result in self.rounds:
            if result.success:
                lines.append(f"- [第{result.round_number}轮：{result.round_name_cn}](#{result.round_number}-{result.round_name.lower().replace(' ', '-')})")
        lines.extend(["", "---", ""])

        # Each round's full output
        for result in self.rounds:
            if result.success:
                lines.extend([
                    f"## {result.round_number}. {result.round_name_cn}",
                    f"### Round {result.round_number}: {result.round_name}",
                    f"",
                    result.full_response,
                    f"",
                    f"---",
                    f"",
                ])
            else:
                lines.extend([
                    f"## {result.round_number}. {result.round_name_cn}",
                    f"### Round {result.round_number}: {result.round_name}",
                    f"",
                    f"**错误：** {result.error_message}",
                    f"",
                    f"---",
                    f"",
                ])

        # Summary section
        if self.context:
            lines.extend([
                "## 分析摘要",
                "",
                "### 关键发现",
                "",
            ])

            if self.context.value_proposition:
                lines.append(f"**产品类型：** {self.context.value_proposition}")

            if self.context.critical_metric:
                lines.append(f"**核心指标：** {self.context.critical_metric}")

            if self.context.risk_scenarios:
                lines.append(f"**主要风险：** {', '.join(self.context.risk_scenarios[:3])}")

            if self.context.action_recommendation:
                lines.append(f"**投资建议：** {self.context.action_recommendation}")

            if self.context.methodology_tools:
                lines.append(f"**分析工具：** {', '.join(self.context.methodology_tools[:5])}")

        return "\n".join(lines)


class Orchestrator:
    """
    Main orchestrator that coordinates the multi-agent analysis flow.

    The orchestrator:
    1. Initializes all 8 specialized agents
    2. Executes them sequentially, passing context between rounds
    3. Collects and aggregates results into a comprehensive report
    4. Handles errors gracefully
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = "claude-sonnet-4-20250514",
        max_tokens: int = 8192,
        include_methodology: bool = True,
        on_round_start: Optional[Callable[[int, str], None]] = None,
        on_round_complete: Optional[Callable[[int, str, bool], None]] = None,
    ):
        """
        Initialize the orchestrator.

        Args:
            api_key: Anthropic API key. If not provided, uses ANTHROPIC_API_KEY env var.
            model: The Claude model to use for all agents.
            max_tokens: Maximum tokens for each agent response.
            include_methodology: Whether to include the optional Round 8.
            on_round_start: Callback when a round starts. Args: (round_number, round_name)
            on_round_complete: Callback when a round completes. Args: (round_number, round_name, success)
        """
        self.client = anthropic.Anthropic(api_key=api_key)
        self.model = model
        self.max_tokens = max_tokens
        self.include_methodology = include_methodology
        self.on_round_start = on_round_start
        self.on_round_complete = on_round_complete

        # Initialize all agents
        self.agents = [
            SceneUnderstandingAgent(self.client, model, max_tokens),
            MoatAnalysisAgent(self.client, model, max_tokens),
            KeyMetricsAgent(self.client, model, max_tokens),
            AnalogyAgent(self.client, model, max_tokens),
            RiskScenarioAgent(self.client, model, max_tokens),
            StressTestAgent(self.client, model, max_tokens),
            JudgmentAgent(self.client, model, max_tokens),
        ]

        if include_methodology:
            self.agents.append(MethodologyAgent(self.client, model, max_tokens))

    def analyze(self, company_name: str) -> AnalysisReport:
        """
        Run the complete 7-8 round analysis for a company.

        Args:
            company_name: The name of the company to analyze.

        Returns:
            AnalysisReport containing all results and the final report.
        """
        import time
        start_time = time.time()

        # Initialize context
        context = AgentContext(company_name=company_name)

        # Initialize report
        report = AnalysisReport(
            company_name=company_name,
            timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            context=context,
        )

        # Execute each round sequentially
        for agent in self.agents:
            # Notify round start
            if self.on_round_start:
                self.on_round_start(agent.round_number, agent.round_name_cn)

            # Execute agent
            result = agent.execute(context)
            report.rounds.append(result)

            # Notify round complete
            if self.on_round_complete:
                self.on_round_complete(agent.round_number, agent.round_name_cn, result.success)

            # If a round fails, we can continue with subsequent rounds
            # but note the failure
            if not result.success:
                report.success = False
                if not report.error_message:
                    report.error_message = f"Round {agent.round_number} failed: {result.error_message}"

        # Calculate total duration
        report.total_duration_seconds = time.time() - start_time

        return report

    def get_agent_info(self) -> list:
        """
        Get information about all agents.

        Returns:
            List of dicts with agent information.
        """
        return [
            {
                "round": agent.round_number,
                "name": agent.round_name,
                "name_cn": agent.round_name_cn,
            }
            for agent in self.agents
        ]


def create_orchestrator(
    api_key: Optional[str] = None,
    model: str = "claude-sonnet-4-20250514",
    include_methodology: bool = True,
) -> Orchestrator:
    """
    Factory function to create an orchestrator with default settings.

    Args:
        api_key: Optional API key. Uses env var if not provided.
        model: Claude model to use.
        include_methodology: Whether to include Round 8.

    Returns:
        Configured Orchestrator instance.
    """
    return Orchestrator(
        api_key=api_key,
        model=model,
        include_methodology=include_methodology,
    )
