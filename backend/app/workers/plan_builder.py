from app.models import Campaign, Worker
from app.workers.definitions import WorkerDefinition
from app.workers.plan import WorkerPlan, WorkerStep


class WorkerPlanBuilder:
    def build_plan(self, worker: Worker, campaign: Campaign, definition: WorkerDefinition) -> WorkerPlan:
        worker_config = worker.config_json if isinstance(worker.config_json, dict) else {}
        custom_step_overrides: dict[str, dict] = {}
        execution_steps = worker_config.get("execution_steps", [])
        if isinstance(worker.config_json, dict):
            raw = worker.config_json.get("step_overrides", {})
            if isinstance(raw, dict):
                custom_step_overrides = raw

        if isinstance(execution_steps, list) and execution_steps:
            steps = []
            for raw_step in execution_steps:
                if not isinstance(raw_step, dict):
                    continue
                key = str(raw_step.get("key", "")).strip()
                action_key = str(raw_step.get("action_key", "")).strip()
                if not key or not action_key:
                    continue
                steps.append(
                    WorkerStep(
                        key=key,
                        name=str(raw_step.get("name", key.replace("_", " ").title())),
                        action_key=action_key,
                        status=raw_step.get("status"),
                        config=raw_step.get("config", {}) if isinstance(raw_step.get("config", {}), dict) else {},
                    )
                )
            allowed_actions = (
                list(worker.allowed_actions)
                if isinstance(worker.allowed_actions, list) and worker.allowed_actions
                else list({step.action_key for step in steps})
            )
            return WorkerPlan(
                worker_type=worker.worker_type,
                plan_version=worker.plan_version or definition.plan_version,
                allowed_actions=allowed_actions,
                steps=steps,
                metadata={"campaign_id": str(campaign.id), "worker_id": str(worker.id)},
            )

        steps = []
        for step_definition in definition.steps:
            override = custom_step_overrides.get(step_definition.key, {})
            steps.append(
                WorkerStep(
                    key=step_definition.key,
                    name=step_definition.name or step_definition.key.replace("_", " ").title(),
                    action_key=step_definition.action_key,
                    status=override.get("status", step_definition.status),
                    config={**step_definition.config, **override},
                )
            )

        allowed_actions = (
            list(worker.allowed_actions)
            if isinstance(worker.allowed_actions, list) and worker.allowed_actions
            else list(definition.allowed_actions)
        )

        return WorkerPlan(
            worker_type=definition.worker_type,
            plan_version=worker.plan_version or definition.plan_version,
            allowed_actions=allowed_actions,
            steps=steps,
            metadata={"campaign_id": str(campaign.id), "worker_id": str(worker.id)},
        )
