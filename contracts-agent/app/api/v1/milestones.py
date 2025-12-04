"""Milestone API Endpoints."""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query

from app.models.milestone import MilestoneStatus, ResponsibleParty
from app.services.odoo.contract_service import ContractService, get_contract_service

router = APIRouter(prefix="/milestones", tags=["Milestones"])


@router.get("/upcoming")
async def get_upcoming_milestones(
    days: int = Query(7, ge=1, le=90, description="Days to look ahead"),
    contract_service: ContractService = Depends(get_contract_service),
):
    """
    Get milestones due within the specified number of days.

    Returns milestones sorted by due date (soonest first).
    """
    milestones = await contract_service.get_upcoming_milestones(days)
    return {
        "total": len(milestones),
        "days_threshold": days,
        "milestones": sorted(
            milestones,
            key=lambda x: x.get("days_until_due", 999),
        ),
    }


@router.get("/overdue")
async def get_overdue_milestones(
    contract_service: ContractService = Depends(get_contract_service),
):
    """
    Get all overdue milestones.

    Returns milestones sorted by days overdue (most overdue first).
    """
    milestones = await contract_service.get_overdue_milestones()
    return {
        "total": len(milestones),
        "milestones": sorted(
            milestones,
            key=lambda x: x.get("days_overdue", 0),
            reverse=True,
        ),
    }


@router.get("/contract/{contract_id}")
async def get_contract_milestones(
    contract_id: int,
    status: Optional[MilestoneStatus] = None,
    contract_service: ContractService = Depends(get_contract_service),
):
    """Get milestones for a specific contract."""
    # This would be implemented with a proper milestone store
    # For now, return empty list
    return {
        "contract_id": contract_id,
        "total": 0,
        "milestones": [],
    }


@router.get("/statuses")
async def list_milestone_statuses():
    """Get list of available milestone statuses."""
    return {
        "statuses": [
            {"value": ms.value, "name": ms.name.replace("_", " ").title()}
            for ms in MilestoneStatus
        ]
    }
