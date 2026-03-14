from datetime import UTC, datetime, timedelta
import base64
import hashlib
import hmac
import secrets
from typing import Any

from jose import JWTError, jwt

from app.core.config import settings

ALGORITHM = "HS256"

PBKDF2_ALGORITHM = "sha256"
PBKDF2_ITERATIONS = 390000


def hash_password(password: str) -> str:
    salt = secrets.token_bytes(16)
    hashed = hashlib.pbkdf2_hmac(PBKDF2_ALGORITHM, password.encode("utf-8"), salt, PBKDF2_ITERATIONS)
    return (
        f"pbkdf2_{PBKDF2_ALGORITHM}${PBKDF2_ITERATIONS}$"
        f"{base64.b64encode(salt).decode('utf-8')}${base64.b64encode(hashed).decode('utf-8')}"
    )


def verify_password(plain_password: str, hashed_password: str) -> bool:
    try:
        algorithm, iterations_str, salt_b64, hash_b64 = hashed_password.split("$")
        if not algorithm.startswith("pbkdf2_"):
            return False
        iterations = int(iterations_str)
        salt = base64.b64decode(salt_b64.encode("utf-8"))
        expected = base64.b64decode(hash_b64.encode("utf-8"))
        candidate = hashlib.pbkdf2_hmac(
            algorithm.replace("pbkdf2_", ""),
            plain_password.encode("utf-8"),
            salt,
            iterations,
        )
        return hmac.compare_digest(candidate, expected)
    except (ValueError, TypeError):
        return False


def create_access_token(subject: str, expires_minutes: int | None = None, extra: dict[str, Any] | None = None) -> str:
    expire = datetime.now(UTC) + timedelta(minutes=expires_minutes or settings.access_token_expire_minutes)
    payload: dict[str, Any] = {"sub": subject, "exp": expire}
    if extra:
        payload.update(extra)
    return jwt.encode(payload, settings.secret_key, algorithm=ALGORITHM)


def decode_token(token: str) -> dict[str, Any] | None:
    try:
        return jwt.decode(token, settings.secret_key, algorithms=[ALGORITHM])
    except JWTError:
        return None
