"""Main API router combining all endpoint modules."""

from fastapi import APIRouter

from app.api.v1 import health, tasks, employees, reports, distribution

api_router = APIRouter()

# Include all v1 routers
api_router.include_router(health.router)
api_router.include_router(tasks.router)
api_router.include_router(employees.router)
api_router.include_router(reports.router)
api_router.include_router(distribution.router)
