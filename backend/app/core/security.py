"""Password hashing (bcrypt) and JWT access-token helpers.

NOTE: the manual lists ``passlib[bcrypt]``. We hash with the ``bcrypt`` library
directly because recent ``bcrypt`` releases are unreliable through passlib's
backend shim. The result is identical bcrypt hashing (prefix ``$2b$``).
"""
from datetime import datetime, timedelta, timezone

import bcrypt
from jose import jwt

from app.core.config import settings


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(plain: str, hashed: str) -> bool:
    try:
        return bcrypt.checkpw(plain.encode("utf-8"), hashed.encode("utf-8"))
    except Exception:
        return False


def create_access_token(subject: str | int, extra: dict | None = None) -> str:
    now = datetime.now(timezone.utc)
    expire = now + timedelta(minutes=settings.access_token_expire_minutes)
    payload = {"sub": str(subject), "iat": now, "exp": expire}
    if extra:
        payload.update(extra)
    return jwt.encode(payload, settings.secret_key, algorithm=settings.algorithm)


def decode_access_token(token: str) -> dict:
    return jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])


# ---------------------------------------------------------------------------
# Role based permission model (manual section 13)
# ---------------------------------------------------------------------------
ROLE_PERMISSIONS: dict[str, set[str]] = {
    "operator": {
        "meeting:view", "meeting:create", "meeting:update",
        "network_asset:view", "network_asset:create", "network_asset:update",
        "network_asset:history",
        "account_batch:view", "account_batch:create", "account_batch:update",
        "maintenance:view", "maintenance:create", "maintenance:update",
        "maintenance:delete",
    },
    "manager": {
        "meeting:view", "meeting:create", "meeting:update", "meeting:export",
        "network_asset:view", "network_asset:create", "network_asset:update",
        "network_asset:history", "network_asset:import", "network_asset:export",
        "account_batch:view", "account_batch:create", "account_batch:update",
        "account_batch:import", "account_batch:export",
        "maintenance:view", "maintenance:create", "maintenance:update",
        "maintenance:delete", "maintenance:export",
    },
    # admin has every permission
    "admin": {
        "meeting:view", "meeting:create", "meeting:update", "meeting:delete",
        "meeting:export",
        "network_asset:view", "network_asset:create", "network_asset:update",
        "network_asset:history", "network_asset:import", "network_asset:export",
        "account_batch:view", "account_batch:create", "account_batch:update",
        "account_batch:import", "account_batch:export", "account_batch:delete",
        "maintenance:view", "maintenance:create", "maintenance:update",
        "maintenance:delete", "maintenance:export",
        "system:user_manage", "system:department_manage",
        "system:log_view", "system:backup_manage",
    },
}


def user_permissions(role: str) -> list[str]:
    if role == "admin":
        return sorted(ROLE_PERMISSIONS["admin"])
    return sorted(ROLE_PERMISSIONS.get(role, set()))


def has_permission(user, perm: str) -> bool:
    if user.role == "admin":
        return True
    return perm in ROLE_PERMISSIONS.get(user.role, set())
