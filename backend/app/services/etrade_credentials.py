from __future__ import annotations

import base64
import hashlib
import uuid
from typing import Any

from cryptography.fernet import Fernet, InvalidToken
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models import ConnectedAccount

ETRADE_PROVIDER = "etrade"


def _fernet() -> Fernet:
    # Derive a deterministic Fernet key from SECRET_KEY to avoid storing extra key material.
    key_material = hashlib.sha256(settings.secret_key.encode("utf-8")).digest()
    return Fernet(base64.urlsafe_b64encode(key_material))


def encrypt_secret(value: str) -> str:
    if not value:
        raise ValueError("Cannot encrypt empty secret")
    return _fernet().encrypt(value.encode("utf-8")).decode("utf-8")


def decrypt_secret(value: str | None) -> str | None:
    if not value:
        return None
    try:
        return _fernet().decrypt(value.encode("utf-8")).decode("utf-8")
    except InvalidToken:
        return None


def _get_workspace_account(db: Session, workspace_id: uuid.UUID) -> ConnectedAccount | None:
    return (
        db.query(ConnectedAccount)
        .filter(
            ConnectedAccount.workspace_id == workspace_id,
            ConnectedAccount.provider_type == ETRADE_PROVIDER,
        )
        .first()
    )


def begin_workspace_oauth(
    db: Session,
    *,
    workspace_id: uuid.UUID,
    request_token: str,
    request_token_secret: str,
    redirect_uri: str,
    account_id_key: str | None = None,
) -> ConnectedAccount:
    account = _get_workspace_account(db, workspace_id)
    if not account:
        account = ConnectedAccount(workspace_id=workspace_id, provider_type=ETRADE_PROVIDER)
        db.add(account)

    metadata = dict(account.metadata_json or {})
    metadata.update(
        {
            "status": "pending_oauth",
            "pending_request_token": request_token,
            "redirect_uri": redirect_uri,
            "account_id_key": (account_id_key or metadata.get("account_id_key", "")).strip() or None,
        }
    )
    account.access_token_encrypted = encrypt_secret(request_token_secret)
    account.refresh_token_encrypted = None
    account.metadata_json = metadata
    return account


def complete_workspace_oauth(
    db: Session,
    *,
    workspace_id: uuid.UUID,
    expected_request_token: str,
    access_token: str,
    access_token_secret: str,
    account_id_key: str | None = None,
) -> ConnectedAccount:
    account = _get_workspace_account(db, workspace_id)
    if not account:
        raise ValueError("No pending E*Trade connection found for this workspace.")

    metadata = dict(account.metadata_json or {})
    pending_token = str(metadata.get("pending_request_token", ""))
    if not pending_token or pending_token != expected_request_token:
        raise ValueError("OAuth token mismatch for pending E*Trade connection.")

    metadata.update(
        {
            "status": "connected",
            "pending_request_token": None,
            "connected_via": "oauth1",
            "account_id_key": (account_id_key or metadata.get("account_id_key", "")).strip() or None,
        }
    )
    account.access_token_encrypted = encrypt_secret(access_token)
    account.refresh_token_encrypted = encrypt_secret(access_token_secret)
    account.metadata_json = metadata
    return account


def get_workspace_tokens(db: Session, *, workspace_id: uuid.UUID) -> tuple[str, str, dict[str, Any]] | None:
    account = _get_workspace_account(db, workspace_id)
    if not account:
        return None
    metadata = dict(account.metadata_json or {})
    if metadata.get("status") != "connected":
        return None

    access_token = decrypt_secret(account.access_token_encrypted)
    access_token_secret = decrypt_secret(account.refresh_token_encrypted)
    if not access_token or not access_token_secret:
        return None
    return access_token, access_token_secret, metadata


def get_pending_request_secret(
    db: Session,
    *,
    workspace_id: uuid.UUID,
    oauth_token: str,
) -> tuple[str, dict[str, Any]]:
    account = _get_workspace_account(db, workspace_id)
    if not account:
        raise ValueError("No pending E*Trade connection found for this workspace.")

    metadata = dict(account.metadata_json or {})
    if metadata.get("status") != "pending_oauth":
        raise ValueError("No pending E*Trade OAuth request for this workspace.")

    pending_token = str(metadata.get("pending_request_token", ""))
    if pending_token != oauth_token:
        raise ValueError("OAuth token mismatch for pending E*Trade connection.")

    secret = decrypt_secret(account.access_token_encrypted)
    if not secret:
        raise ValueError("Missing request-token secret for E*Trade OAuth completion.")
    return secret, metadata


def disconnect_workspace_account(db: Session, *, workspace_id: uuid.UUID) -> bool:
    account = _get_workspace_account(db, workspace_id)
    if not account:
        return False
    db.delete(account)
    return True
