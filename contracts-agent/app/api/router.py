"""Main API Router."""

from fastapi import APIRouter

from app.api.v1 import health, contracts, clauses, milestones, compliance, reports

api_router = APIRouter()

# Include all v1 routers
api_router.include_router(health.router)
api_router.include_router(contracts.router)
api_router.include_router(clauses.router)
api_router.include_router(milestones.router)
api_router.include_router(compliance.router)
api_router.include_router(reports.router)
