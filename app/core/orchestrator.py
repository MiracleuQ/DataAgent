import asyncio
import uuid
from typing import Dict
from app.agents.base import BaseAgent, AgentResult
from app.core.context import DataContext
from app.core.bus import MessageBus, Message
from app.history import HistoryManager


class Orchestrator:
    def __init__(self):
        self._agents: Dict[str, BaseAgent] = {}
        self._bus = MessageBus()
        self._history = HistoryManager()

    def register_agent(self, agent: BaseAgent) -> None:
        self._agents[agent.role] = agent

    async def execute_plan(self, plan: Dict, context: DataContext) -> Dict[str, AgentResult]:
        tasks = plan.get("tasks", [])
        results: Dict[str, AgentResult] = {}
        completed: set = set()
        max_iterations = len(tasks) * 2
        iteration = 0

        while len(completed) < len(tasks) and iteration < max_iterations:
            iteration += 1
            ready = []
            for idx, task_def in enumerate(tasks):
                if idx in completed:
                    continue
                deps = task_def.get("depends_on", [])
                if all(d in completed for d in deps):
                    ready.append((idx, task_def))

            if not ready:
                break

            for idx, task_def in ready:
                agent_name = task_def["agent"]
                task_desc = task_def["task"]
                agent = self._agents.get(agent_name)
                if not agent:
                    results[f"{agent_name}_{idx}"] = AgentResult(success=False, output="", agent_id=agent_name, error=f"Agent '{agent_name}' not registered")
                    completed.add(idx)
                    continue

                dep_context = ""
                for dep_idx in task_def.get("depends_on", []):
                    dep_key = f"{tasks[dep_idx]['agent']}_{dep_idx}"
                    if dep_key in results and results[dep_key].success:
                        dep_context += f"\n前置任务结果：{results[dep_key].output[:500]}"

                full_task = f"{task_desc}{dep_context}"
                result = await agent.run(full_task, context)
                results[f"{agent_name}_{idx}"] = result
                completed.add(idx)
                await self._bus.send(Message(sender=agent_name, receiver="coordinator", content=f"任务完成：{task_desc[:100]}", msg_type="result"))

        return results

    async def run(self, user_request: str, context: DataContext, coordinator: "BaseAgent") -> Dict:
        from app.agents.coordinator import CoordinatorAgent
        assert isinstance(coordinator, CoordinatorAgent)
        session_id = str(uuid.uuid4())
        self._history.create_session(session_id, user_request)
        try:
            plan_result = await coordinator.plan(user_request)
            results = await self.execute_plan(plan_result, context)
            final_report = context.get_result("final_report") or ""
            agent_outputs = {k: v.output[:200] for k, v in results.items() if v.success}
            for key, result in results.items():
                self._history.log_agent(
                    session_id,
                    result.agent_id,
                    key,
                    result.output[:500],
                    result.success,
                )
            self._history.update_session(
                session_id,
                str(plan_result),
                final_report[:500] if final_report else "",
                "success",
            )
            return {"plan": plan_result, "agent_results": agent_outputs, "report": final_report, "charts": context.charts, "dataframes": context.list_dataframes()}
        except Exception as e:
            self._history.update_session(session_id, "", str(e), "failed")
            raise
