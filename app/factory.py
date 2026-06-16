from app.config import get_settings
from app.llm.client import LLMClient
from app.core.orchestrator import Orchestrator
from app.agents.coordinator import CoordinatorAgent
from app.agents.data_engineer import DataEngineerAgent
from app.agents.analyst import AnalystAgent
from app.agents.visualizer import VisualizerAgent
from app.agents.reporter import ReporterAgent
from app.agents.reviewer import ReviewerAgent


def create_system():
    settings = get_settings()
    llm = LLMClient(settings=settings)
    orchestrator = Orchestrator()
    bus = orchestrator.bus
    coordinator = CoordinatorAgent(llm_client=llm, bus=bus)
    orchestrator.register_agent(DataEngineerAgent(llm_client=llm, bus=bus))
    orchestrator.register_agent(AnalystAgent(llm_client=llm, sandbox_timeout=settings.sandbox_timeout_sec, bus=bus))
    orchestrator.register_agent(VisualizerAgent(llm_client=llm, chart_output_dir=settings.chart_output_dir, bus=bus))
    orchestrator.register_agent(ReporterAgent(llm_client=llm, bus=bus))
    orchestrator.register_agent(ReviewerAgent(llm_client=llm, bus=bus))
    return coordinator, orchestrator
