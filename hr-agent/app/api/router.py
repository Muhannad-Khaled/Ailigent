"""Main API Router."""

from fastapi import APIRouter

from app.api.v1 import health, recruitment, appraisals, reports, attendance

api_router = APIRouter()

# Include all v1 routers
api_router.include_router(health.router, prefix="/health", tags=["Health"])
api_router.include_router(recruitment.router, prefix="/recruitment", tags=["Recruitment"])
api_router.include_router(appraisals.router, prefix="/appraisals", tags=["Appraisals"])
api_router.include_router(reports.router, prefix="/reports", tags=["Reports"])
api_router.include_router(attendance.router, prefix="/attendance", tags=["Attendance"])
