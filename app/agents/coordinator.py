import json
import re
import traceback
import logging
from typing import Dict
from app.agents.base import BaseAgent, AgentResult
from app.core.context import DataContext
from app.llm.client import LLMClient

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """你是数据分析团队的协调者。你的职责是：
1. 理解用户需求
2. 拆解为子任务
3. 分配给合适的 Agent

可用 Agent：data_engineer(数据加载清洗), analyst(统计分析), visualizer(图表生成), reporter(报告撰写)

输出 JSON：
{"understanding": "理解", "tasks": [{"agent": "xxx", "task": "描述", "depends_on": []}]}"""


class CoordinatorAgent(BaseAgent):
    def __init__(self, llm_client: LLMClient):
        super().__init__(role="coordinator", system_prompt=SYSTEM_PROMPT)
        self._llm = llm_client

    def _parse_json_response(self, content: str, user_request: str) -> Dict:
        try:
            json_match = re.search(r'\{[\s\S]*\}', content)
            if json_match:
                return json.loads(json_match.group())
        except json.JSONDecodeError as e:
            logger.warning(f"JSON parse failed: {e}")
        
        logger.warning("Using default plan due to parse failure")
        return {
            "understanding": "通用数据分析",
            "tasks": [
                {"agent": "data_engineer", "task": user_request, "depends_on": []},
                {"agent": "analyst", "task": f"分析：{user_request}", "depends_on": [0]},
                {"agent": "visualizer", "task": f"可视化：{user_request}", "depends_on": [0]},
                {"agent": "reporter", "task": f"报告：{user_request}", "depends_on": [1, 2]}
            ]
        }

    async def plan(self, user_request: str) -> Dict:
        messages = [{"role": "system", "content": SYSTEM_PROMPT}, {"role": "user", "content": user_request}]
        response = await self._llm.chat(messages=messages, temperature=0.0)
        content = response.content or "{}"
        plan = self._parse_json_response(content, user_request)
        return plan

    async def run(self, task: str, context: DataContext) -> AgentResult:
        try:
            plan = await self.plan(task)
            summary = f"理解：{plan.get('understanding', '')}\n计划 {len(plan.get('tasks', []))} 个子任务"
            self._remember(task, summary)
            return AgentResult(success=True, output=summary, agent_id=self.role, data={"plan": plan})
        except Exception as e:
            return AgentResult(success=False, output="", agent_id=self.role, error=f"{e}\n{traceback.format_exc()}")
