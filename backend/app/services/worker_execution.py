import json
import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from typing import Any

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.integrations.ai.base import WorkerModelResponse
from app.integrations.ai.factory import get_ai_provider
from app.models import (
    Worker,
    WorkerInstance,
    WorkerInstanceStatus,
    WorkerMemoryScope,
    WorkerRun,
    WorkerRunStatus,
    WorkerRunTriggerType,
    WorkerStatus,
    WorkerTemplate,
)
from app.services.ai_utils import normalize_whitespace, parse_json_object
from app.services.audit import log_audit_event
from app.services.worker_memory import build_worker_memory_bundle, store_worker_run_context, upsert_worker_memory
from app.services.worker_tools import (
    ensure_system_worker_tools,
    invoke_tool_calls,
    resolve_template_allowed_tool_slugs,
)


@dataclass
class WorkerExecutionContext:
    db: Session
    instance: WorkerInstance
    template: WorkerTemplate
    worker: Worker
    run: WorkerRun
    runtime_input: dict[str, Any]
    memory_context: dict[str, Any]
    allowed_actions: list[str]
    allowed_tools: list[str]
    model_name: str
    capabilities: dict[str, Any]
    started_at: datetime
    prompt: str = ""
    notes: list[str] = field(default_factory=list)


class WorkerExecutionEngine:
    def __init__(self, ai_provider_factory=get_ai_provider) -> None:
        self.ai_provider_factory = ai_provider_factory

    @staticmethod
    def _estimate_tokens(text: str) -> int:
        return max(len(text or "") // 4, 1)

    @staticmethod
    def _coerce_utc(value: datetime) -> datetime:
        if value.tzinfo is None:
            return value.replace(tzinfo=UTC)
        return value.astimezone(UTC)

    @staticmethod
    def _sanitize_string_list(value: Any) -> list[str]:
        if not isinstance(value, list):
            return []
        items: list[str] = []
        for item in value:
            text = normalize_whitespace(str(item))
            if text:
                items.append(text)
        return items

    def _resolve_worker_for_instance(self, db: Session, instance: WorkerInstance, template: WorkerTemplate) -> Worker:
        if instance.legacy_worker_id:
            existing = db.get(Worker, instance.legacy_worker_id)
            if existing and existing.workspace_id == instance.workspace_id:
                return existing

        runtime_config = instance.runtime_config_json if isinstance(instance.runtime_config_json, dict) else {}
        worker = Worker(
            workspace_id=instance.workspace_id,
            name=instance.name or template.name or template.display_name,
            worker_type=template.worker_type,
            worker_category=template.worker_category,
            mission=template.description or template.instructions or "Execute worker template mission",
            goal=template.description or template.instructions or "Execute worker template mission",
            plan_version=template.plan_version,
            allowed_actions=self._sanitize_string_list(template.allowed_actions or template.actions_json or []),
            template_id=template.id,
            origin_type="template_install",
            is_custom_worker=template.worker_type == "custom_worker" or template.workspace_id is not None,
            is_internal=False,
            status=WorkerStatus.IDLE.value,
            tone="professional",
            send_limit_per_day=40,
            run_interval_minutes=60,
            config_json=runtime_config or template.config_json or template.default_config_json or {},
        )
        db.add(worker)
        db.flush()
        instance.legacy_worker_id = worker.id
        return worker

    def build_execution_context(
        self,
        db: Session,
        *,
        instance: WorkerInstance,
        runtime_input: dict[str, Any] | None = None,
        triggered_by: WorkerRunTriggerType | str = WorkerRunTriggerType.MANUAL,
        trigger_source: str | None = None,
        run: WorkerRun | None = None,
    ) -> WorkerExecutionContext:
        template = db.get(WorkerTemplate, instance.template_id)
        if not template:
            raise HTTPException(status_code=404, detail="Worker template not found for instance")
        worker = self._resolve_worker_for_instance(db, instance, template)
        payload = runtime_input if isinstance(runtime_input, dict) else {}
        trigger_value = triggered_by.value if isinstance(triggered_by, WorkerRunTriggerType) else str(triggered_by)

        if run is None:
            run = WorkerRun(
                workspace_id=instance.workspace_id,
                worker_id=worker.id,
                instance_id=instance.id,
                template_id=template.id,
                run_type="template_execution",
                triggered_by=trigger_value,
                trigger_source=trigger_source,
                status=WorkerRunStatus.QUEUED.value,
                input_json=payload,
            )
            db.add(run)
            db.flush()
        else:
            run.workspace_id = run.workspace_id or instance.workspace_id
            run.worker_id = run.worker_id or worker.id
            run.instance_id = run.instance_id or instance.id
            run.template_id = run.template_id or template.id
            run.triggered_by = run.triggered_by or trigger_value
            run.trigger_source = run.trigger_source or trigger_source
            if run.input_json is None:
                run.input_json = payload

        allowed_actions = self._sanitize_string_list(template.allowed_actions or template.actions_json or [])
        ensure_system_worker_tools(db)
        allowed_tools = resolve_template_allowed_tool_slugs(db, template)
        capabilities = template.capabilities_json if isinstance(template.capabilities_json, dict) else {}
        memory_context = (
            build_worker_memory_bundle(
                db,
                workspace_id=instance.workspace_id,
                scope=instance.memory_scope,
                instance_id=instance.id,
                template_id=template.id,
            )
            if template.memory_enabled
            else {}
        )
        model_name = normalize_whitespace(template.model_name or "") or "mock-ai-v1"
        return WorkerExecutionContext(
            db=db,
            instance=instance,
            template=template,
            worker=worker,
            run=run,
            runtime_input=payload,
            memory_context=memory_context,
            allowed_actions=allowed_actions,
            allowed_tools=allowed_tools,
            model_name=model_name,
            capabilities=capabilities,
            started_at=datetime.now(UTC),
        )

    def assemble_worker_prompt(self, context: WorkerExecutionContext) -> str:
        instructions = normalize_whitespace(context.template.instructions or "")
        if not instructions:
            instructions = "Execute the worker mission and return structured JSON only."

        prompt_payload = {
            "worker_instance_id": str(context.instance.id),
            "worker_template_id": str(context.template.id),
            "worker_type": context.template.worker_type,
            "worker_category": context.template.worker_category,
            "model_name": context.model_name,
            "instructions": instructions,
            "config": context.instance.runtime_config_json or context.template.config_json or context.template.default_config_json or {},
            "capabilities": context.capabilities,
            "allowed_actions": context.allowed_actions,
            "allowed_tools": context.allowed_tools,
            "memory_context": context.memory_context,
            "runtime_input": context.runtime_input,
            "response_schema": {
                "summary": "string",
                "output": "object",
                "tool_calls": [{"tool": "string", "input": "object"}],
                "memory_updates": {"key": "value"},
                "suggested_actions": ["string"],
            },
        }
        return (
            "You are the Thorpe Workforce execution runtime. "
            "Produce JSON only with keys summary, output, tool_calls, memory_updates, suggested_actions. "
            "Do not include tools outside allowed_tools.\n\n"
            f"{json.dumps(prompt_payload)}"
        )

    def invoke_model(self, context: WorkerExecutionContext, prompt: str) -> WorkerModelResponse:
        provider = self.ai_provider_factory()
        try:
            response = provider.execute_worker(
                model_name=context.model_name,
                prompt=prompt,
                tools=context.allowed_tools,
                runtime_input=context.runtime_input,
                context={
                    "worker_type": context.template.worker_type,
                    "capabilities": context.capabilities,
                    "allowed_actions": context.allowed_actions,
                },
            )
        except Exception as exc:  # pragma: no cover - defensive fallback
            response = WorkerModelResponse(
                text=json.dumps(
                    {
                        "summary": "Worker execution failed while invoking model.",
                        "output": {"error": str(exc)},
                        "tool_calls": [],
                        "memory_updates": {},
                    }
                ),
                model=context.model_name,
                metadata={"provider_error": str(exc)},
            )

        if response.token_usage_input <= 0:
            response.token_usage_input = self._estimate_tokens(prompt)
        if response.token_usage_output <= 0:
            response.token_usage_output = self._estimate_tokens(response.text)
        if response.cost_cents <= 0:
            response.cost_cents = max((response.token_usage_input + response.token_usage_output) // 250, 1)
        return response

    def postprocess_output(
        self,
        context: WorkerExecutionContext,
        model_response: WorkerModelResponse,
    ) -> dict[str, Any]:
        parsed = parse_json_object(
            model_response.text,
            fallback={
                "summary": "Worker execution completed with fallback parsing.",
                "output": {"raw_text": normalize_whitespace(model_response.text)},
                "tool_calls": [],
                "memory_updates": {},
                "suggested_actions": [],
            },
        )
        summary = normalize_whitespace(str(parsed.get("summary", ""))) or "Worker execution completed."
        output = parsed.get("output", {})
        if not isinstance(output, dict):
            output = {"value": output}

        allowed_tools = set(context.allowed_tools)
        accepted_tool_calls: list[dict[str, Any]] = []
        rejected_tool_calls: list[dict[str, Any]] = []
        raw_tool_calls = parsed.get("tool_calls", [])
        if not isinstance(raw_tool_calls, list):
            raw_tool_calls = []

        for raw_call in raw_tool_calls:
            if not isinstance(raw_call, dict):
                continue
            tool_name = normalize_whitespace(str(raw_call.get("tool", "")))
            call_input = raw_call.get("input", {})
            if not tool_name:
                continue
            if tool_name in allowed_tools:
                accepted_tool_calls.append({"tool": tool_name, "input": call_input if isinstance(call_input, dict) else {}})
            else:
                rejected_tool_calls.append({"tool": tool_name, "reason": "tool_not_allowed"})

        suggested_actions = self._sanitize_string_list(parsed.get("suggested_actions", []))
        if context.allowed_actions:
            allowed_action_set = set(context.allowed_actions)
            suggested_actions = [item for item in suggested_actions if item in allowed_action_set]

        memory_updates = parsed.get("memory_updates", {})
        if not isinstance(memory_updates, dict):
            memory_updates = {}
        memory_updates = {normalize_whitespace(str(key)): value for key, value in memory_updates.items() if str(key).strip()}

        notes: list[str] = []
        if rejected_tool_calls:
            notes.append("Some tool calls were ignored because they were not allowed.")

        return {
            "summary": summary,
            "output": output,
            "tool_calls": accepted_tool_calls,
            "rejected_tool_calls": rejected_tool_calls,
            "suggested_actions": suggested_actions,
            "memory_updates": memory_updates,
            "notes": notes,
            "model": model_response.model,
            "metadata": model_response.metadata,
        }

    def persist_run(
        self,
        context: WorkerExecutionContext,
        *,
        processed_output: dict[str, Any] | None,
        model_response: WorkerModelResponse | None,
        error: Exception | None = None,
    ) -> WorkerRun:
        now = datetime.now(UTC)
        run = context.run
        run.finished_at = now
        started_at = self._coerce_utc(run.started_at or context.started_at)
        run.duration_ms = max(int((now - started_at).total_seconds() * 1000), 0)

        usage_input = model_response.token_usage_input if model_response else self._estimate_tokens(context.prompt)
        usage_output = model_response.token_usage_output if model_response else 1
        run.token_usage_input = max(int(usage_input), 0)
        run.token_usage_output = max(int(usage_output), 0)
        run.cost_cents = max(int(model_response.cost_cents if model_response else 1), 0)

        if error:
            message = normalize_whitespace(str(error)) or "Worker execution failed"
            run.status = WorkerRunStatus.FAILED.value
            run.summary = "Execution failed"
            run.error_message = message
            run.error_text = message
            run.output_json = {
                "error": message,
                "notes": processed_output.get("notes", []) if isinstance(processed_output, dict) else [],
            }
            context.instance.status = WorkerInstanceStatus.ERROR.value
            context.worker.status = WorkerStatus.ERROR.value
            context.worker.last_error_text = message
            context.worker.last_run_at = now
            context.worker.next_run_at = now + timedelta(minutes=15)
            if context.template.memory_enabled:
                store_worker_run_context(
                    context.db,
                    workspace_id=context.instance.workspace_id,
                    scope=context.instance.memory_scope,
                    instance_id=context.instance.id,
                    template_id=context.template.id,
                    run_id=run.id,
                    summary=run.summary or "Execution failed",
                    runtime_input=context.runtime_input,
                    output={"error": message},
                    suggested_actions=[],
                    notes=["execution_failed"],
                    token_usage_input=run.token_usage_input,
                    token_usage_output=run.token_usage_output,
                    cost_cents=run.cost_cents,
                )
            log_audit_event(
                context.db,
                workspace_id=context.instance.workspace_id,
                actor_type="system",
                actor_id="worker_execution_engine",
                event_name="worker_instance_run_failed",
                payload={"instance_id": str(context.instance.id), "run_id": str(run.id), "error": message},
            )
            context.db.flush()
            return run

        output = processed_output or {}
        run.status = WorkerRunStatus.COMPLETED.value
        run.summary = normalize_whitespace(str(output.get("summary", ""))) or "Execution completed"
        run.error_message = None
        run.error_text = None
        run.output_json = {
            "output": output.get("output", {}),
            "tool_calls": output.get("tool_calls", []),
            "tool_results": output.get("tool_results", []),
            "rejected_tool_calls": output.get("rejected_tool_calls", []),
            "suggested_actions": output.get("suggested_actions", []),
            "notes": output.get("notes", []),
            "runtime_input": context.runtime_input,
            "model": output.get("model", context.model_name),
            "provider_metadata": output.get("metadata", {}),
        }
        context.instance.status = WorkerInstanceStatus.ACTIVE.value
        context.instance.last_run_at = now
        context.instance.next_run_at = now + timedelta(minutes=60)
        context.worker.status = WorkerStatus.IDLE.value
        context.worker.last_error_text = None
        context.worker.last_run_at = now
        context.worker.next_run_at = context.instance.next_run_at

        if context.template.memory_enabled:
            for key, value in (output.get("memory_updates", {}) or {}).items():
                upsert_worker_memory(
                    context.db,
                    workspace_id=context.instance.workspace_id,
                    memory_key=key,
                    memory_value=value,
                    scope=context.instance.memory_scope,
                    instance_id=context.instance.id,
                    template_id=context.template.id,
                    memory_type="episodic",
                )
            store_worker_run_context(
                context.db,
                workspace_id=context.instance.workspace_id,
                scope=context.instance.memory_scope,
                instance_id=context.instance.id,
                template_id=context.template.id,
                run_id=run.id,
                summary=run.summary or "Execution completed",
                runtime_input=context.runtime_input,
                output=output.get("output", {}),
                suggested_actions=output.get("suggested_actions", []),
                notes=output.get("notes", []),
                token_usage_input=run.token_usage_input,
                token_usage_output=run.token_usage_output,
                cost_cents=run.cost_cents,
            )
        log_audit_event(
            context.db,
            workspace_id=context.instance.workspace_id,
            actor_type="system",
            actor_id="worker_execution_engine",
            event_name="worker_instance_run_completed",
            payload={"instance_id": str(context.instance.id), "run_id": str(run.id), "summary": run.summary},
        )
        context.db.flush()
        return run

    def execute_context(self, context: WorkerExecutionContext) -> WorkerRun:
        context.run.status = WorkerRunStatus.RUNNING.value
        context.run.started_at = context.started_at
        context.instance.status = WorkerInstanceStatus.ACTIVE.value
        context.worker.status = WorkerStatus.PROSPECTING.value
        log_audit_event(
            context.db,
            workspace_id=context.instance.workspace_id,
            actor_type="system",
            actor_id="worker_execution_engine",
            event_name="worker_instance_run_started",
            payload={"instance_id": str(context.instance.id), "run_id": str(context.run.id)},
        )
        context.db.flush()

        processed_output: dict[str, Any] | None = None
        model_response: WorkerModelResponse | None = None
        error: Exception | None = None
        try:
            context.prompt = self.assemble_worker_prompt(context)
            model_response = self.invoke_model(context, context.prompt)
            processed_output = self.postprocess_output(context, model_response)
            tool_results, tool_rejections = invoke_tool_calls(
                context.db,
                workspace_id=context.instance.workspace_id,
                instance_id=context.instance.id,
                template_id=context.template.id,
                worker_id=context.worker.id,
                run_id=context.run.id,
                tool_calls=processed_output.get("tool_calls", []) if isinstance(processed_output, dict) else [],
                allowed_tool_slugs=context.allowed_tools,
            )
            processed_output["tool_results"] = tool_results
            existing_rejections = processed_output.get("rejected_tool_calls", [])
            if not isinstance(existing_rejections, list):
                existing_rejections = []
            processed_output["rejected_tool_calls"] = existing_rejections + tool_rejections
            if tool_rejections:
                notes = processed_output.get("notes", [])
                if not isinstance(notes, list):
                    notes = []
                notes.append("Some tool invocations were rejected at runtime.")
                processed_output["notes"] = notes
        except Exception as exc:  # pragma: no cover - protection for unexpected runtime issues
            error = exc

        return self.persist_run(
            context,
            processed_output=processed_output,
            model_response=model_response,
            error=error,
        )

    def execute_worker_instance(
        self,
        db: Session,
        *,
        instance: WorkerInstance,
        runtime_input: dict[str, Any] | None = None,
        triggered_by: WorkerRunTriggerType | str = WorkerRunTriggerType.MANUAL,
        trigger_source: str | None = None,
        run: WorkerRun | None = None,
    ) -> WorkerRun:
        context = self.build_execution_context(
            db,
            instance=instance,
            runtime_input=runtime_input,
            triggered_by=triggered_by,
            trigger_source=trigger_source,
            run=run,
        )
        return self.execute_context(context)

    def execute_run_by_id(self, db: Session, run_id: uuid.UUID) -> WorkerRun:
        run = db.get(WorkerRun, run_id)
        if not run:
            raise HTTPException(status_code=404, detail="Worker run not found")
        if not run.instance_id:
            raise HTTPException(status_code=400, detail="Worker run is not tied to a worker instance")
        instance = db.get(WorkerInstance, run.instance_id)
        if not instance:
            run.status = WorkerRunStatus.FAILED.value
            run.error_message = "worker_instance_not_found"
            run.error_text = "worker_instance_not_found"
            db.flush()
            return run
        runtime_input = run.input_json if isinstance(run.input_json, dict) else {}
        return self.execute_worker_instance(
            db,
            instance=instance,
            runtime_input=runtime_input,
            triggered_by=run.triggered_by or WorkerRunTriggerType.MANUAL.value,
            trigger_source=run.trigger_source,
            run=run,
        )


def queue_worker_instance_run(
    db: Session,
    *,
    instance: WorkerInstance,
    runtime_input: dict[str, Any] | None = None,
    triggered_by: WorkerRunTriggerType | str = WorkerRunTriggerType.MANUAL,
    trigger_source: str | None = None,
) -> WorkerRun:
    engine = WorkerExecutionEngine()
    context = engine.build_execution_context(
        db,
        instance=instance,
        runtime_input=runtime_input,
        triggered_by=triggered_by,
        trigger_source=trigger_source,
    )
    context.instance.status = WorkerInstanceStatus.ACTIVE.value
    context.db.flush()
    return context.run


def execute_worker_instance_run(db: Session, *, run_id: uuid.UUID) -> WorkerRun:
    return WorkerExecutionEngine().execute_run_by_id(db, run_id)
