"""Pagination + safe sorting helpers (manual 8.1: sort uses a whitelist)."""
from sqlalchemy import func


def paginate(query, page: int, page_size: int):
    # 防御：夹紧分页参数，避免负数/超大 page_size 造成异常或拖垮 SQLite
    page = max(1, int(page or 1))
    page_size = min(200, max(1, int(page_size or 20)))
    total = query.count()
    pages = (total + page_size - 1) // page_size if total else 0
    items = query.offset((page - 1) * page_size).limit(page_size).all()
    return items, total, pages


def apply_sort(query, model, sort_by: str | None, sort_order: str, whitelist: dict):
    """whitelist maps allowed client sort keys to ORM columns."""
    if sort_by and sort_by in whitelist:
        col = whitelist[sort_by]
    else:
        col = getattr(model, "created_at", None) or getattr(model, "id")
    query = query.order_by(col.desc() if sort_order == "desc" else col.asc())
    return query
