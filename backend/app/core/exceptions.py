"""Unified response structure and business error handling.

All successful responses follow:
    {"code": 0, "message": "success", "data": ..., "request_id": "..."}
All failures follow the same envelope with a non-zero ``code``.
"""
from fastapi import Request

from app.core.logging import get_request_id


def ok(data=None, message: str = "success"):
    return {"code": 0, "message": message, "data": data, "request_id": get_request_id()}


class BizError(Exception):
    """Raised by services; converted to a unified error response by the handler."""

    def __init__(self, code: int, message: str, data=None):
        self.code = code
        self.message = message
        self.data = data
        super().__init__(message)


# Error code ranges (see manual 8.4)
E_BAD_REQUEST = 40000
E_DUPLICATE = 40021
E_UNAUTHORIZED = 40101
E_FORBIDDEN = 40301
E_NOT_FOUND = 40411
E_CONFLICT = 40911
E_FILE_TOO_LARGE = 41301
E_TOO_MANY_REQUESTS = 42901
E_IMPORT_FORMAT = 42211
E_INTERNAL = 50001


def bad_request(message: str, data=None):
    return BizError(E_BAD_REQUEST, message, data)


def unauthorized(message: str = "登录已过期或无效", data=None):
    return BizError(E_UNAUTHORIZED, message, data)


def forbidden(message: str = "权限不足", data=None):
    return BizError(E_FORBIDDEN, message, data)


def not_found(message: str = "资源不存在", data=None):
    return BizError(E_NOT_FOUND, message, data)


def conflict(message: str, data=None):
    return BizError(E_CONFLICT, message, data)


def duplicate(message: str, data=None):
    return BizError(E_DUPLICATE, message, data)


def file_too_large(message: str = "文件超过上传限制", data=None):
    return BizError(E_FILE_TOO_LARGE, message, data)


def too_many_requests(message: str = "请求过于频繁，请稍后再试", data=None):
    return BizError(E_TOO_MANY_REQUESTS, message, data)


def import_format(message: str, data=None):
    return BizError(E_IMPORT_FORMAT, message, data)
