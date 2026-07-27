"""Server-side import preview sessions (manual 11.2).

Preview results are kept on the server, keyed by an ``import_token``. The commit
step trusts only the server session, never the client's preview payload.
Entries auto-expire so temp storage stays bounded (single-worker deployment).
"""
import time
import uuid
from typing import Any

_TTL_SECONDS = 3600
_store: dict[str, dict[str, Any]] = {}


def _purge():
    now = time.time()
    expired = [k for k, v in _store.items() if now - v["ts"] > _TTL_SECONDS]
    for k in expired:
        _store.pop(k, None)


def put(payload: dict) -> str:
    _purge()
    token = uuid.uuid4().hex
    _store[token] = {"ts": time.time(), "payload": payload}
    return token


def get(token: str) -> dict | None:
    _purge()
    entry = _store.get(token)
    return entry["payload"] if entry else None


def drop(token: str) -> None:
    _store.pop(token, None)
