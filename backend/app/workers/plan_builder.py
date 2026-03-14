from app.models import Campaign, Worker
from app.workers.definitions import WorkerDefinition
from app.workers.plan import WorkerPlan, WorkerStep


class WorkerPlanBuilder:
    def build_plan(self, worker: Worker, campaign: Campaign, definition: WorkerDefinition) -> WorkerPlan:
        custom_step_overrides: dict[str, dict] = {}
        if isinstance(worker.config_json, dict):
            raw = worker.config_json.get("step_overrides", {})
            if isinstance(raw, dict):
                custom_step_overrides = raw

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

        return WorkerPlan(
            worker_type=definition.worker_type,
            plan_version=definition.plan_version,
            allowed_actions=list(definition.allowed_actions),
            steps=steps,
            metadata={"campaign_id": str(campaign.id), "worker_id": str(worker.id)},
        )
