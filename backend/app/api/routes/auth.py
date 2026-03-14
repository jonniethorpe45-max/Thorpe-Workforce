from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.rate_limit import limit_requests
from app.core.security import create_access_token, hash_password, verify_password
from app.db.session import get_db
from app.models import User, Workspace
from app.schemas.api import LoginRequest, SignUpRequest, TokenResponse, UserRead
from app.services.audit import log_audit_event

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
    log_audit_event(
        db,
        workspace_id=workspace.id,
        actor_type="user",
        actor_id=str(user.id),
        event_name="user_signed_up",
        payload={"email": user.email},
    )
    db.commit()
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


@router.get("/me", response_model=UserRead)
def me(current_user: User = Depends(get_current_user)):
    return current_user
