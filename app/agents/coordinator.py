import json
import logging
import re
from typing import Dict, List, Optional

from app.agents.base import AgentResult, BaseAgent
from app.agents.tool_loop import _clean_content
from app.core.bus import MessageBus
from app.core.context import DataContext
from app.llm.client import LLMClient
from app.utils.language import get_prompt

logger = logging.getLogger(__name__)
ALLOWED_AGENTS = {"data_engineer", "analyst", "visualizer", "reporter"}


class CoordinatorAgent(BaseAgent):
    def __init__(self, llm_client: LLMClient, bus: Optional[MessageBus] = None):
        super().__init__(role="coordinator", system_prompt=get_prompt("coordinator"), bus=bus)
        self._llm = llm_client

    def _default_plan(self, user_request: str) -> Dict:
        return {
            "understanding": "通用数据分析",
            "tasks": [
                {"agent": "data_engineer", "task": user_request, "depends_on": []},
                {"agent": "analyst", "task": f"分析：{user_request}", "depends_on": [0]},
                {"agent": "visualizer", "task": f"可视化：{user_request}", "depends_on": [0]},
                {"agent": "reporter", "task": f"报告：{user_request}", "depends_on": [1, 2]},
            ],
        }

    def _validate_plan(self, plan: Dict) -> None:
        tasks = plan.get("tasks")
        if not isinstance(tasks, list) or not tasks:
            raise ValueError("Plan must contain a non-empty tasks list")

        for idx, task in enumerate(tasks):
            if not isinstance(task, dict):
                raise ValueError(f"Task {idx} must be an object")
            if task.get("agent") not in ALLOWED_AGENTS:
                raise ValueError(f"Task {idx} uses unknown agent: {task.get('agent')}")
            if not isinstance(task.get("task"), str) or not task["task"].strip():
                raise ValueError(f"Task {idx} must have a non-empty task description")

            deps = task.get("depends_on", [])
            if not isinstance(deps, list):
                raise ValueError(f"Task {idx} dependencies must be a list")
            for dep in deps:
                if not isinstance(dep, int) or dep < 0 or dep >= len(tasks):
                    raise ValueError(f"Task {idx} has invalid dependency: {dep}")
                if dep == idx:
                    raise ValueError(f"Task {idx} cannot depend on itself")

        self._ensure_acyclic(tasks)

    def _ensure_acyclic(self, tasks: List[Dict]) -> None:
        visiting = set()
        visited = set()

        def visit(idx: int) -> None:
            if idx in visiting:
                raise ValueError("Plan dependencies contain a cycle")
            if idx in visited:
                return
            visiting.add(idx)
            for dep in tasks[idx].get("depends_on", []):
                visit(dep)
            visiting.remove(idx)
            visited.add(idx)

        for idx in range(len(tasks)):
            visit(idx)

    def _parse_json_response(self, content: str, user_request: str) -> Dict:
        content = content.strip()
        json_match = re.search(r"```(?:json)?\s*(\{[\s\S]*?\})\s*```", content)
        if json_match:
            content = json_match.group(1)
        else:
            json_match = re.search(r"\{[\s\S]*\}", content)
            if json_match:
                content = json_match.group()
        try:
            plan = json.loads(content)
            self._validate_plan(plan)
            return plan
        except (json.JSONDecodeError, ValueError) as e:
            logger.warning("Plan parse/validation failed: %s", e)

        logger.warning("Using default plan due to parse failure")
        return self._default_plan(user_request)

    async def plan(self, user_request: str) -> Dict:
        messages = [{"role": "system", "content": get_prompt("coordinator")}, {"role": "user", "content": user_request}]
        response = await self._llm.chat(messages=messages, temperature=0.0, response_format={"type": "json_object"})
        content = _clean_content(response.content or "{}")
        return self._parse_json_response(content, user_request)

    async def run(self, task: str, context: DataContext) -> AgentResult:
        plan = await self.plan(task)
        plan_json = json.dumps(plan, ensure_ascii=False)
        self._remember(task, plan_json)
        return AgentResult(success=True, output=plan_json, agent_id=self.role, data={"plan": plan})
