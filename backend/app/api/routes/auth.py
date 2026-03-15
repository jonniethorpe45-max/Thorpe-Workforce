from datetime import UTC, datetime
import hashlib

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.config import settings
from app.core.rate_limit import limit_requests
from app.core.security import create_access_token, hash_password, verify_password
from app.db.session import get_db
from app.models import PasswordResetToken, User, Workspace
from app.schemas.api import LoginRequest, PasswordResetConfirm, PasswordResetRequest, SignUpRequest, TokenResponse, UserRead
from app.services.audit import log_audit_event
from app.services.billing import ensure_workspace_subscription
from app.services.onboarding import get_or_create_onboarding_state
from app.services.subscription_plans import ensure_default_subscription_plans
from app.services.transactional_email import generate_password_reset_token, send_transactional_email

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/signup", response_model=TokenResponse, dependencies=[Depends(limit_requests("signup", 60, 20))])
def signup(payload: SignUpRequest, db: Session = Depends(get_db)):
    existing = db.query(User).filter(User.email == payload.email.lower()).first()
    if existing:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email already exists")

    workspace = Workspace(
        company_name=payload.company_name,
        website=payload.website,
        industry=payload.industry,
        subscription_plan="starter",
    )
    db.add(workspace)
    db.flush()
    user = User(
        workspace_id=workspace.id,
        full_name=payload.full_name,
        email=payload.email.lower(),
        password_hash=hash_password(payload.password),
        role="owner",
    )
    db.add(user)
    db.flush()
    ensure_default_subscription_plans(db)
    ensure_workspace_subscription(db, workspace=workspace)
    log_audit_event(
        db,
        workspace_id=workspace.id,
        actor_type="user",
        actor_id=str(user.id),
        event_name="user_signed_up",
        payload={"email": user.email},
    )
    get_or_create_onboarding_state(db, user=user)
    db.commit()
    try:
        send_transactional_email(
            to_email=user.email,
            template_key="welcome",
            recipient_name=user.full_name,
        )
        send_transactional_email(
            to_email=user.email,
            template_key="workspace_ready",
            recipient_name=user.full_name,
        )
    except Exception:
        pass
    token = create_access_token(subject=str(user.id), extra={"workspace_id": str(workspace.id)})
    return TokenResponse(access_token=token)


@router.post("/login", response_model=TokenResponse, dependencies=[Depends(limit_requests("login", 60, 60))])
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == payload.email.lower()).first()
    if not user or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    token = create_access_token(subject=str(user.id), extra={"workspace_id": str(user.workspace_id)})
    return TokenResponse(access_token=token)


@router.post("/logout")
def logout(response: Response):
    # JWT is stateless in MVP; frontend should clear local token.
    response.status_code = status.HTTP_200_OK
    return {"success": True}


@router.post(
    "/forgot-password",
    dependencies=[Depends(limit_requests("forgot_password", 60, 20))],
)
def forgot_password(payload: PasswordResetRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == str(payload.email).lower()).first()
    if not user:
        return {"success": True}
    db.query(PasswordResetToken).filter(
        PasswordResetToken.user_id == user.id,
        PasswordResetToken.used_at.is_(None),
    ).update({"used_at": datetime.now(UTC)}, synchronize_session=False)
    raw_token, token_hash, expires_at = generate_password_reset_token(
        ttl_minutes=settings.password_reset_token_ttl_minutes
    )
    db.add(
        PasswordResetToken(
            user_id=user.id,
            token_hash=token_hash,
            expires_at=expires_at,
        )
    )
    log_audit_event(
        db,
        workspace_id=user.workspace_id,
        actor_type="user",
        actor_id=str(user.id),
        event_name="password_reset_requested",
        payload={},
    )
    db.commit()
    try:
        send_transactional_email(
            to_email=user.email,
            template_key="password_reset",
            recipient_name=user.full_name,
            context={"reset_url": f"{settings.app_base_url}/reset-password?token={raw_token}"},
        )
    except Exception:
        pass
    return {"success": True}


@router.post(
    "/reset-password",
    dependencies=[Depends(limit_requests("reset_password", 60, 30))],
)
def reset_password(payload: PasswordResetConfirm, db: Session = Depends(get_db)):
    token_hash = hashlib.sha256(payload.token.encode("utf-8")).hexdigest()
    token = (
        db.query(PasswordResetToken)
        .filter(
            PasswordResetToken.token_hash == token_hash,
            PasswordResetToken.used_at.is_(None),
        )
        .first()
    )
    if not token or token.expires_at < datetime.now(UTC):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid or expired reset token")
    user = db.get(User, token.user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    user.password_hash = hash_password(payload.new_password)
    token.used_at = datetime.now(UTC)
    log_audit_event(
        db,
        workspace_id=user.workspace_id,
        actor_type="user",
        actor_id=str(user.id),
        event_name="password_reset_completed",
        payload={},
    )
    db.commit()
    return {"success": True}


@router.get("/me", response_model=UserRead)
def me(current_user: User = Depends(get_current_user)):
    return current_user
