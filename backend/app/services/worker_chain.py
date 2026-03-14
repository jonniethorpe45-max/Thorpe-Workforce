import uuid
from dataclasses import dataclass
from typing import Any

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models import (
    WorkerChain,
    WorkerChainStep,
    WorkerInstance,
    WorkerInstanceStatus,
    WorkerMemoryScope,
    WorkerRunStatus,
    WorkerRunTriggerType,
    WorkerTemplate,
)
from app.services.audit import log_audit_event
from app.services.worker_execution import WorkerExecutionEngine
from app.services.worker_templates import get_worker_template_details


@dataclass(frozen=True)
class ChainStepExecutionResult:
    step_order: int
    status: str
    run_id: uuid.UUID | None
    worker_instance_id: uuid.UUID | None
    worker_template_id: uuid.UUID | None
    summary: str | None
    error: str | None
    next_step_order: int | None
    skipped_reason: str | None = None


@dataclass(frozen=True)
class ChainExecutionResult:
    success: bool
    chain_id: uuid.UUID
    chain_run_id: str
    status: str
    executed_steps: list[ChainStepExecutionResult]
    total_steps_executed: int
    final_output: dict[str, Any]


def _extract_path(payload: Any, path: str) -> Any:
    current = payload
    for part in [item for item in path.split(".") if item]:
        if isinstance(current, dict) and part in current:
            current = current[part]
            continue
        return None
    return current


def _resolve_placeholder(value: str, context: dict[str, Any]) -> Any:
    if not value.startswith("$"):
        return value
    path = value[1:]
    if not path:
        return None
    return _extract_path(context, path)


def _evaluate_condition(condition_json: dict[str, Any] | None, context: dict[str, Any]) -> tuple[bool, str | None]:
    if not isinstance(condition_json, dict) or not condition_json:
        return True, None
    if condition_json.get("operator") == "always_false":
        return False, "condition_always_false"
    if condition_json.get("operator") == "always_true":
        return True, None

    path = str(condition_json.get("path", "")).strip()
    if not path:
        # Placeholder structure exists but is not active yet.
        return True, None
    value = _extract_path(context, path)
    if "equals" in condition_json:
        if value == condition_json.get("equals"):
            return True, None
        return False, "condition_equals_not_met"
    if "not_equals" in condition_json:
        if value != condition_json.get("not_equals"):
            return True, None
        return False, "condition_not_equals_not_met"
    if "exists" in condition_json:
        expected = bool(condition_json.get("exists"))
        actual = value is not None
        if actual == expected:
            return True, None
        return False, "condition_exists_not_met"
    # Future operators can be added here.
    return True, None


def _next_sequential_order(sorted_orders: list[int], current_order: int) -> int | None:
    for order in sorted_orders:
        if order > current_order:
            return order
    return None


def _resolve_step_instance(
    db: Session,
    *,
    workspace_id: uuid.UUID,
    step: WorkerChainStep,
    chain_id: uuid.UUID,
    actor_user_id: uuid.UUID | None,
) -> WorkerInstance:
    if step.worker_instance_id:
        instance = db.get(WorkerInstance, step.worker_instance_id)
        if not instance or instance.workspace_id != workspace_id:
            raise HTTPException(status_code=400, detail=f"Invalid worker_instance_id for chain step {step.step_order}")
        return instance
    if not step.worker_template_id:
        raise HTTPException(status_code=400, detail=f"Chain step {step.step_order} must reference an instance or template")

    template = get_worker_template_details(
        db,
        template_id=step.worker_template_id,
        workspace_id=workspace_id,
        include_public=True,
        include_global_non_public=False,
    )
    if not template.is_active:
        raise HTTPException(status_code=400, detail=f"Worker template is inactive for chain step {step.step_order}")

    instance_name = f"Chain {chain_id} Step {step.step_order} - {template.display_name or template.name}"
    existing = (
        db.query(WorkerInstance)
        .filter(
            WorkerInstance.workspace_id == workspace_id,
            WorkerInstance.template_id == template.id,
            WorkerInstance.name == instance_name,
        )
        .first()
    )
    if existing:
        return existing

    instance = WorkerInstance(
        workspace_id=workspace_id,
        template_id=template.id,
        owner_user_id=actor_user_id,
        name=instance_name,
        status=WorkerInstanceStatus.ACTIVE.value,
        runtime_config_json=dict(template.config_json or template.default_config_json or {}),
        memory_scope=WorkerMemoryScope.INSTANCE.value,
    )
    db.add(instance)
    db.flush()
    return instance


def _build_runtime_input(
    step: WorkerChainStep,
    *,
    chain_id: uuid.UUID,
    chain_run_id: str,
    chain_input: dict[str, Any],
    previous_step_output: dict[str, Any],
    step_outputs: dict[str, Any],
) -> dict[str, Any]:
    context = {
        "chain_input": chain_input,
        "previous_step_output": previous_step_output,
        "step_outputs": step_outputs,
    }
    mapped: dict[str, Any] = {}
    mapping = step.input_mapping_json if isinstance(step.input_mapping_json, dict) else {}
    for key, value in mapping.items():
        if isinstance(value, str) and value.startswith("$"):
            mapped[key] = _resolve_placeholder(value, context)
        else:
            mapped[key] = value

    previous_compact = {
        "summary": previous_step_output.get("summary") if isinstance(previous_step_output, dict) else None,
        "output": previous_step_output.get("output") if isinstance(previous_step_output, dict) else None,
        "error": previous_step_output.get("error") if isinstance(previous_step_output, dict) else None,
    }
    step_summaries = {
        key: {
            "summary": value.get("summary") if isinstance(value, dict) else None,
            "error": value.get("error") if isinstance(value, dict) else None,
        }
        for key, value in step_outputs.items()
    }
    runtime_input = {
        **chain_input,
        **mapped,
        "_chain": {
            "chain_id": str(chain_id),
            "chain_run_id": chain_run_id,
            "step_order": step.step_order,
        },
        # Keep runtime input JSON-safe and compact; full chain state is used only
        # during mapping inside this service.
        "previous_step_output": previous_compact,
        "step_outputs_summary": step_summaries,
    }
    return runtime_input


def run_worker_chain_manually(
    db: Session,
    *,
    chain: WorkerChain,
    workspace_id: uuid.UUID,
    actor_user_id: uuid.UUID | None,
    runtime_input: dict[str, Any] | None = None,
    max_steps: int | None = None,
) -> ChainExecutionResult:
    if chain.workspace_id != workspace_id:
        raise HTTPException(status_code=404, detail="Worker chain not found")
    steps = (
        db.query(WorkerChainStep)
        .filter(WorkerChainStep.chain_id == chain.id)
        .order_by(WorkerChainStep.step_order.asc())
        .all()
    )
    if not steps:
        raise HTTPException(status_code=400, detail="Worker chain has no steps")

    chain_input = runtime_input if isinstance(runtime_input, dict) else {}
    chain_run_id = str(uuid.uuid4())
    engine = WorkerExecutionEngine()
    step_by_order = {item.step_order: item for item in steps}
    sorted_orders = sorted(step_by_order.keys())
    execution_limit = max_steps if isinstance(max_steps, int) and max_steps > 0 else len(steps) * 3

    current_order = sorted_orders[0]
    previous_output: dict[str, Any] = {}
    step_outputs: dict[str, Any] = {}
    results: list[ChainStepExecutionResult] = []
    iterations = 0
    chain_failed = False
    final_output: dict[str, Any] = {}

    log_audit_event(
        db,
        workspace_id=workspace_id,
        actor_type="user",
        actor_id=str(actor_user_id or "unknown"),
        event_name="worker_chain_run_started",
        payload={"chain_id": str(chain.id), "chain_run_id": chain_run_id},
    )

    while current_order is not None:
        if iterations >= execution_limit:
            chain_failed = True
            results.append(
                ChainStepExecutionResult(
                    step_order=current_order,
                    status="failed",
                    run_id=None,
                    worker_instance_id=None,
                    worker_template_id=None,
                    summary=None,
                    error="chain_execution_limit_reached",
                    next_step_order=None,
                )
            )
            break

        step = step_by_order.get(current_order)
        if not step:
            chain_failed = True
            results.append(
                ChainStepExecutionResult(
                    step_order=current_order,
                    status="failed",
                    run_id=None,
                    worker_instance_id=None,
                    worker_template_id=None,
                    summary=None,
                    error="step_not_found",
                    next_step_order=None,
                )
            )
            break

        condition_ok, skip_reason = _evaluate_condition(
            step.condition_json if isinstance(step.condition_json, dict) else {},
            {
                "chain_input": chain_input,
                "previous_step_output": previous_output,
                "step_outputs": step_outputs,
            },
        )
        if not condition_ok:
            next_order = step.on_success_next_step or _next_sequential_order(sorted_orders, step.step_order)
            results.append(
                ChainStepExecutionResult(
                    step_order=step.step_order,
                    status="skipped",
                    run_id=None,
                    worker_instance_id=step.worker_instance_id,
                    worker_template_id=step.worker_template_id,
                    summary=None,
                    error=None,
                    next_step_order=next_order,
                    skipped_reason=skip_reason,
                )
            )
            current_order = next_order
            iterations += 1
            continue

        try:
            instance = _resolve_step_instance(
                db,
                workspace_id=workspace_id,
                step=step,
                chain_id=chain.id,
                actor_user_id=actor_user_id,
            )
            step_runtime_input = _build_runtime_input(
                step,
                chain_id=chain.id,
                chain_run_id=chain_run_id,
                chain_input=chain_input,
                previous_step_output=previous_output,
                step_outputs=step_outputs,
            )
            run = engine.execute_worker_instance(
                db,
                instance=instance,
                runtime_input=step_runtime_input,
                triggered_by=WorkerRunTriggerType.CHAIN,
                trigger_source=f"chain:{chain.id}:run:{chain_run_id}:step:{step.step_order}",
            )
        except Exception as exc:  # noqa: BLE001
            error_text = getattr(exc, "detail", None) or str(exc) or "step_execution_error"
            next_order = step.on_failure_next_step
            previous_output = {"error": str(error_text)}
            step_outputs[str(step.step_order)] = previous_output
            results.append(
                ChainStepExecutionResult(
                    step_order=step.step_order,
                    status="failed",
                    run_id=None,
                    worker_instance_id=step.worker_instance_id,
                    worker_template_id=step.worker_template_id,
                    summary=None,
                    error=str(error_text),
                    next_step_order=next_order,
                )
            )
            current_order = next_order
            iterations += 1
            if next_order is None:
                chain_failed = True
                break
            continue

        is_success = run.status == WorkerRunStatus.COMPLETED.value
        if is_success:
            next_order = step.on_success_next_step or _next_sequential_order(sorted_orders, step.step_order)
            previous_output = run.output_json if isinstance(run.output_json, dict) else {}
            step_outputs[str(step.step_order)] = previous_output
            final_output = previous_output
        else:
            next_order = step.on_failure_next_step
            previous_output = {"error": run.error_message or run.error_text or "step_failed"}
            step_outputs[str(step.step_order)] = previous_output
            if next_order is None:
                chain_failed = True

        results.append(
            ChainStepExecutionResult(
                step_order=step.step_order,
                status="completed" if is_success else "failed",
                run_id=run.id,
                worker_instance_id=instance.id,
                worker_template_id=step.worker_template_id,
                summary=run.summary,
                error=run.error_message or run.error_text,
                next_step_order=next_order,
            )
        )

        current_order = next_order
        iterations += 1
        if chain_failed:
            break

    status = "failed" if chain_failed else "completed"
    log_audit_event(
        db,
        workspace_id=workspace_id,
        actor_type="user",
        actor_id=str(actor_user_id or "unknown"),
        event_name="worker_chain_run_completed",
        payload={
            "chain_id": str(chain.id),
            "chain_run_id": chain_run_id,
            "status": status,
            "steps_executed": len(results),
        },
    )
    db.flush()
    return ChainExecutionResult(
        success=not chain_failed,
        chain_id=chain.id,
        chain_run_id=chain_run_id,
        status=status,
        executed_steps=results,
        total_steps_executed=len(results),
        final_output=final_output,
    )
