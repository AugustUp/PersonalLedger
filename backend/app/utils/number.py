"""Business number generation: module-prefix + date + daily sequence.

Format: PREFIX-YYYYMMDD-NNN  (e.g. MTG-20260726-001).
Concurrent-safe enough for SQLite single-writer: callers should retry the whole
create on unique-constraint failure (manual 7.5).
"""
from datetime import date

from sqlalchemy import func


def _date_str(d: date | None = None) -> str:
    d = d or date.today()
    return d.strftime("%Y%m%d")


def next_daily_sequence(db, model, field: str, prefix: str, date_str: str) -> int:
    like = f"{prefix}-{date_str}-%"
    col = getattr(model, field)
    cnt = db.query(func.count(model.id)).filter(col.like(like)).scalar() or 0
    return cnt + 1


def format_no(prefix: str, date_str: str, seq: int) -> str:
    return f"{prefix}-{date_str}-{seq:03d}"


def generate_no(db, model, field: str, prefix: str, d: date | None = None) -> str:
    date_str = _date_str(d)
    seq = next_daily_sequence(db, model, field, prefix, date_str)
    return format_no(prefix, date_str, seq)


def commit_with_no(db, obj, model, field: str, prefix: str, max_attempts: int = 10):
    """Commit ``obj`` assigning a daily-unique business number, retrying on
    unique-constraint collision (manual 7.5)."""
    from sqlalchemy.exc import IntegrityError

    from app.core.exceptions import BizError, E_INTERNAL

    date_str = _date_str()
    for attempt in range(max_attempts):
        seq = next_daily_sequence(db, model, field, prefix, date_str) + attempt
        setattr(obj, field, format_no(prefix, date_str, seq))
        try:
            db.commit()
            db.refresh(obj)
            return obj
        except IntegrityError:
            db.rollback()
    raise BizError(E_INTERNAL, "生成业务编号失败，请稍后重试")
