"""FastAPI application entry point."""
import logging
import os
import sys
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

# ensure project root on path when run via uvicorn app.main:app
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from app.api.v1 import api_router
from app.core.config import settings
from app.core.database import Base, engine
from app.core.exceptions import BizError, E_BAD_REQUEST, get_request_id
from app.core.logging import new_request_id

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
)
logger = logging.getLogger("ops-ledger")


@asynccontextmanager
async def lifespan(app: FastAPI):
    os.makedirs(settings.upload_dir, exist_ok=True)
    os.makedirs(os.path.dirname(settings.database_url.replace("sqlite:///", "", 1)) or ".", exist_ok=True)
    # Dev convenience: auto-create schema. Production deploys use Alembic.
    if settings.environment != "production":
        Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(title=settings.app_name, version="1.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def request_id_middleware(request: Request, call_next):
    new_request_id()
    response = await call_next(request)
    response.headers["X-Request-ID"] = get_request_id()
    return response


def _http_status_for_code(code: int) -> int:
    return int(str(code)[:3])


@app.exception_handler(BizError)
async def biz_error_handler(request: Request, exc: BizError):
    return JSONResponse(
        status_code=_http_status_for_code(exc.code),
        content={
            "code": exc.code,
            "message": exc.message,
            "data": exc.data,
            "request_id": get_request_id(),
        },
    )


@app.exception_handler(RequestValidationError)
async def validation_error_handler(request: Request, exc: RequestValidationError):
    return JSONResponse(
        status_code=422,
        content={
            "code": E_BAD_REQUEST,
            "message": "请求参数校验失败",
            "data": {"errors": exc.errors()},
            "request_id": get_request_id(),
        },
    )


@app.exception_handler(Exception)
async def unhandled_error_handler(request: Request, exc: Exception):
    logger.exception("Unhandled error: %s", exc)
    return JSONResponse(
        status_code=500,
        content={
            "code": 50001,
            "message": "服务器内部错误",
            "data": None,
            "request_id": get_request_id(),
        },
    )


@app.get("/health", tags=["meta"])
def health():
    return {"code": 0, "message": "ok", "data": None, "request_id": get_request_id()}


app.include_router(api_router, prefix="/api/v1")
