import asyncio
import time
import uuid
from typing import Dict, List, Optional, Tuple

from app.agents.base import AgentResult, BaseAgent
from app.agents.tool_loop import _clean_content
from app.config import get_settings
from app.core.bus import Message, MessageBus
from app.core.context import DataContext
from app.history import HistoryManager


class Orchestrator:
    def __init__(self, history_db_path: Optional[str] = None):
        settings = get_settings()
        self._agents: Dict[str, BaseAgent] = {}
        self._bus = MessageBus()
        self._history = HistoryManager(db_path=history_db_path or settings.history_db_path)
        self._execution_events: List[Dict] = []

    @property
    def bus(self) -> MessageBus:
        return self._bus

    @property
    def execution_events(self) -> List[Dict]:
        return list(self._execution_events)

    def register_agent(self, agent: BaseAgent) -> None:
        self._agents[agent.role] = agent

    async def execute_plan(
        self,
        plan: Dict,
        context: DataContext,
        execution_events: Optional[List[Dict]] = None,
    ) -> Dict[str, AgentResult]:
        tasks = plan.get("tasks", [])
        results: Dict[str, AgentResult] = {}
        events = execution_events if execution_events is not None else []
        if execution_events is None:
            self._execution_events = events
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
                invalid_deps = [d for d in deps if not isinstance(d, int) or d < 0 or d >= len(tasks)]
                if invalid_deps:
                    agent_name = task_def.get("agent", "unknown")
                    result = AgentResult(
                        success=False,
                        output="",
                        agent_id=agent_name,
                        error=f"Invalid dependencies: {invalid_deps}",
                    )
                    results[f"{agent_name}_{idx}"] = result
                    self._record_event(events, idx, agent_name, "failed", result.error, duration_ms=0)
                    completed.add(idx)
                    continue

                if all(d in completed for d in deps):
                    failed_deps = []
                    for dep_idx in deps:
                        dep_key = f"{tasks[dep_idx]['agent']}_{dep_idx}"
                        if dep_key not in results or not results[dep_key].success:
                            failed_deps.append(dep_idx)
                    if failed_deps:
                        agent_name = task_def.get("agent", "unknown")
                        result = AgentResult(
                            success=False,
                            output="",
                            agent_id=agent_name,
                            error=f"Skipped because dependency task(s) failed: {failed_deps}",
                        )
                        results[f"{agent_name}_{idx}"] = result
                        self._record_event(events, idx, agent_name, "skipped", result.error, duration_ms=0)
                        completed.add(idx)
                        continue

                    ready.append((idx, task_def))

            if not ready:
                break

            batch_results = await asyncio.gather(
                *[
                    self._execute_task(idx, task_def, tasks, results, context, events)
                    for idx, task_def in ready
                ]
            )
            for idx, agent_name, result in batch_results:
                results[f"{agent_name}_{idx}"] = result
                completed.add(idx)

        for idx, task_def in enumerate(tasks):
            if idx not in completed:
                agent_name = task_def.get("agent", "unknown")
                result = AgentResult(
                    success=False,
                    output="",
                    agent_id=agent_name,
                    error="Skipped because dependencies could not be resolved",
                )
                results[f"{agent_name}_{idx}"] = result
                self._record_event(events, idx, agent_name, "skipped", result.error, duration_ms=0)

        return results

    async def _execute_task(
        self,
        idx: int,
        task_def: Dict,
        tasks: List[Dict],
        existing_results: Dict[str, AgentResult],
        context: DataContext,
        execution_events: List[Dict],
    ) -> Tuple[int, str, AgentResult]:
        agent_name = task_def["agent"]
        task_desc = task_def["task"]
        agent = self._agents.get(agent_name)
        if not agent:
            result = AgentResult(
                success=False,
                output="",
                agent_id=agent_name,
                error=f"Agent '{agent_name}' not registered",
            )
            self._record_event(execution_events, idx, agent_name, "failed", result.error, duration_ms=0)
            return idx, agent_name, result

        dep_context = ""
        for dep_idx in task_def.get("depends_on", []):
            dep_key = f"{tasks[dep_idx]['agent']}_{dep_idx}"
            if dep_key in existing_results and existing_results[dep_key].success:
                dep_agent = tasks[dep_idx]['agent']
                context.add_result(f"dep_{dep_agent}_{dep_idx}", existing_results[dep_key].output)
                dep_context += f"\nDependency '{dep_agent}' completed successfully."

        full_task = f"{task_desc}{dep_context}"
        self._record_event(execution_events, idx, agent_name, "running", "", duration_ms=0)
        result = await agent.run_with_timeout(full_task, context)
        status = "success" if result.success else "failed"
        self._record_event(
            execution_events,
            idx,
            agent_name,
            status,
            result.error or "",
            duration_ms=result.duration_ms,
        )
        await self._bus.send(
            Message(
                sender=agent_name,
                receiver="coordinator",
                content=f"Task completed: {task_desc[:100]}",
                msg_type="result" if result.success else "error",
            )
        )
        return idx, agent_name, result

    def _record_event(
        self,
        execution_events: List[Dict],
        task_index: int,
        agent: str,
        status: str,
        message: str,
        duration_ms: float,
    ) -> None:
        execution_events.append(
            {
                "task_index": task_index,
                "agent": agent,
                "status": status,
                "message": message,
                "duration_ms": duration_ms,
                "timestamp": time.time(),
            }
        )

    def _execution_summary(
        self,
        results: Dict[str, AgentResult],
        duration_ms: float,
        execution_events: List[Dict],
    ) -> Dict:
        succeeded = sum(1 for result in results.values() if result.success)
        failed = sum(1 for result in results.values() if not result.success)
        return {
            "total_tasks": len(results),
            "succeeded": succeeded,
            "failed": failed,
            "duration_ms": round(duration_ms, 2),
            "events": list(execution_events),
        }

    async def run(self, user_request: str, context: DataContext, coordinator: "BaseAgent") -> Dict:
        from app.agents.coordinator import CoordinatorAgent

        if not isinstance(coordinator, CoordinatorAgent):
            raise TypeError(f"Expected CoordinatorAgent, got {type(coordinator).__name__}")
        session_id = str(uuid.uuid4())
        self._history.create_session(session_id, user_request)
        run_started = time.perf_counter()
        execution_events: List[Dict] = []
        try:
            plan_result = await coordinator.plan(user_request)
            results = await self.execute_plan(plan_result, context, execution_events=execution_events)
            final_report = context.get_result("final_report") or ""
            reviewer = self._agents.get("reviewer")
            if final_report and reviewer:
                review_result = await reviewer.run("Review the final report against the available data and artifacts.", context)
                results["reviewer_auto"] = review_result
            agent_outputs = {k: _clean_content(v.output)[:200] for k, v in results.items() if v.success}
            failures = {k: v.error for k, v in results.items() if not v.success}

            for key, result in results.items():
                self._history.log_agent(
                    session_id,
                    result.agent_id,
                    key,
                    result.output[:500],
                    result.success,
                )

            status = "success" if not failures else "failed"
            stored_result = final_report[:500] if final_report else "; ".join(
                f"{key}: {error}" for key, error in failures.items() if error
            )[:500]
            self._history.update_session(
                session_id,
                str(plan_result),
                stored_result,
                status,
            )
            return {
                "plan": plan_result,
                "agent_results": agent_outputs,
                "errors": failures,
                "status": status,
                "report": final_report,
                "review": context.get_result("review_report") or "",
                "artifacts": [artifact.to_dict() for artifact in context.artifacts],
                "execution": self._execution_summary(
                    results,
                    (time.perf_counter() - run_started) * 1000,
                    execution_events,
                ),
                "charts": context.charts,
                "dataframes": context.list_dataframes(),
            }
        except Exception as e:
            self._history.update_session(session_id, "", str(e), "failed")
            raise
