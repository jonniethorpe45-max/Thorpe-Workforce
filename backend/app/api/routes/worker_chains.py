import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models import User, WorkerChain, WorkerChainStep, WorkerInstance
from app.schemas.api import (
    WorkerChainCreate,
    WorkerChainListResponse,
    WorkerChainRead,
    WorkerChainStepCreate,
    WorkerChainStepRead,
    WorkerChainUpdate,
)
from app.services.worker_templates import get_worker_template_details

router = APIRouter(prefix="/worker-chains", tags=["worker_chains"])


def _get_workspace_chain(db: Session, *, chain_id: uuid.UUID, workspace_id: uuid.UUID) -> WorkerChain:
    chain = db.get(WorkerChain, chain_id)
    if not chain or chain.workspace_id != workspace_id:
        raise HTTPException(status_code=404, detail="Worker chain not found")
    return chain


def _validate_step_reference(db: Session, *, workspace_id: uuid.UUID, step: WorkerChainStepCreate) -> None:
    if step.worker_instance_id:
        instance = db.get(WorkerInstance, step.worker_instance_id)
        if not instance or instance.workspace_id != workspace_id:
            raise HTTPException(status_code=400, detail="worker_instance_id must belong to the same workspace")
    if step.worker_template_id:
        get_worker_template_details(
            db,
            template_id=step.worker_template_id,
            workspace_id=workspace_id,
            include_public=True,
            include_global_non_public=False,
        )


def _replace_chain_steps(db: Session, *, chain_id: uuid.UUID, workspace_id: uuid.UUID, steps: list[WorkerChainStepCreate]) -> None:
    db.query(WorkerChainStep).filter(WorkerChainStep.chain_id == chain_id).delete(synchronize_session=False)
    for step in sorted(steps, key=lambda item: item.step_order):
        _validate_step_reference(db, workspace_id=workspace_id, step=step)
        db.add(
            WorkerChainStep(
                chain_id=chain_id,
                step_order=step.step_order,
                worker_instance_id=step.worker_instance_id,
                worker_template_id=step.worker_template_id,
                step_name=step.step_name,
                input_mapping_json=step.input_mapping_json,
                condition_json=step.condition_json,
                on_success_next_step=step.on_success_next_step,
                on_failure_next_step=step.on_failure_next_step,
            )
        )
    db.flush()


def _serialize_chain(db: Session, chain: WorkerChain) -> WorkerChainRead:
    steps = (
        db.query(WorkerChainStep)
        .filter(WorkerChainStep.chain_id == chain.id)
        .order_by(WorkerChainStep.step_order.asc())
        .all()
    )
    return WorkerChainRead(
        id=chain.id,
        workspace_id=chain.workspace_id,
        name=chain.name,
        description=chain.description,
        status=chain.status,
        trigger_type=chain.trigger_type,
        trigger_config_json=chain.trigger_config_json,
        created_at=chain.created_at,
        updated_at=chain.updated_at,
        steps=[WorkerChainStepRead.model_validate(step) for step in steps],
    )


@router.post("", response_model=WorkerChainRead)
def create_chain(
    payload: WorkerChainCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    chain = WorkerChain(
        workspace_id=current_user.workspace_id,
        name=payload.name,
        description=payload.description,
        status=payload.status.value,
        trigger_type=payload.trigger_type.value,
        trigger_config_json=payload.trigger_config_json,
    )
    db.add(chain)
    db.flush()
    _replace_chain_steps(db, chain_id=chain.id, workspace_id=current_user.workspace_id, steps=payload.steps)
    db.commit()
    db.refresh(chain)
    return _serialize_chain(db, chain)


@router.get("", response_model=WorkerChainListResponse)
def list_chains(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    chains = (
        db.query(WorkerChain)
        .filter(WorkerChain.workspace_id == current_user.workspace_id)
        .order_by(WorkerChain.created_at.desc())
        .all()
    )
    return WorkerChainListResponse(items=[_serialize_chain(db, chain) for chain in chains], total=len(chains))


@router.get("/{chain_id}", response_model=WorkerChainRead)
def get_chain(chain_id: uuid.UUID, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    chain = _get_workspace_chain(db, chain_id=chain_id, workspace_id=current_user.workspace_id)
    return _serialize_chain(db, chain)


@router.patch("/{chain_id}", response_model=WorkerChainRead)
def update_chain(
    chain_id: uuid.UUID,
    payload: WorkerChainUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    chain = _get_workspace_chain(db, chain_id=chain_id, workspace_id=current_user.workspace_id)
    updates = payload.model_dump(exclude_unset=True)
    for field in ["name", "description", "trigger_config_json"]:
        if field in updates:
            setattr(chain, field, updates[field])
    if "status" in updates and payload.status is not None:
        chain.status = payload.status.value
    if "trigger_type" in updates and payload.trigger_type is not None:
        chain.trigger_type = payload.trigger_type.value
    if payload.steps is not None:
        _replace_chain_steps(db, chain_id=chain.id, workspace_id=current_user.workspace_id, steps=payload.steps)
    db.commit()
    db.refresh(chain)
    return _serialize_chain(db, chain)
