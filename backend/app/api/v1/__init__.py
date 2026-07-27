"""Aggregate all v1 routers under a single APIRouter mounted at /api/v1."""
from fastapi import APIRouter

from app.api.v1.routers import (
    account_batches, attachments, auth, dashboard, departments, maintenance,
    meetings, network_assets, operation_logs, users,
)

api_router = APIRouter()
api_router.include_router(auth.router)
api_router.include_router(users.router)
api_router.include_router(departments.router)
api_router.include_router(meetings.router)
api_router.include_router(network_assets.router)
api_router.include_router(account_batches.router)
api_router.include_router(maintenance.router)
api_router.include_router(attachments.router)
api_router.include_router(dashboard.router)
api_router.include_router(operation_logs.router)
