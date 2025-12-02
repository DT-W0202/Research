"""
Company Deep Analyzer - Multi-Agent System

This package contains 8 specialized agents for systematic company analysis:
- Round 1: Scene Understanding (建立场景理解)
- Round 2: Moat Analysis (找护城河本质)
- Round 3: Key Metrics (找关键指标)
- Round 4: Analogy Building (用类比建立直觉)
- Round 5: Risk Scenario Design (设计死亡场景)
- Round 6: Stress Testing (极限压力测试)
- Round 7: Judgment Formation (形成判断)
- Round 8: Methodology Extraction (方法论提炼)
"""

from .base import BaseAnalysisAgent, AgentContext, RoundResult
from .round1_scene import SceneUnderstandingAgent
from .round2_moat import MoatAnalysisAgent
from .round3_metrics import KeyMetricsAgent
from .round4_analogy import AnalogyAgent
from .round5_risk import RiskScenarioAgent
from .round6_stress import StressTestAgent
from .round7_judgment import JudgmentAgent
from .round8_methodology import MethodologyAgent

__all__ = [
    "BaseAnalysisAgent",
    "AgentContext",
    "RoundResult",
    "SceneUnderstandingAgent",
    "MoatAnalysisAgent",
    "KeyMetricsAgent",
    "AnalogyAgent",
    "RiskScenarioAgent",
    "StressTestAgent",
    "JudgmentAgent",
    "MethodologyAgent",
]
