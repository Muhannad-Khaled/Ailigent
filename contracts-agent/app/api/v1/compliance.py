"""Compliance API Endpoints."""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query

from app.models.compliance import ComplianceStatus, ComplianceCategory
from app.services.odoo.contract_service import ContractService, get_contract_service

router = APIRouter(prefix="/compliance", tags=["Compliance"])


@router.get("/pending")
async def get_pending_compliance_items(
    contract_service: ContractService = Depends(get_contract_service),
):
    """Get all compliance items pending review."""
    items = await contract_service.get_pending_compliance_items()
    return {
        "total": len(items),
        "status": "pending_review",
        "items": items,
    }


@router.get("/non-compliant")
async def get_non_compliant_items(
    contract_service: ContractService = Depends(get_contract_service),
):
    """Get all non-compliant items."""
    items = await contract_service.get_non_compliant_items()
    return {
        "total": len(items),
        "status": "non_compliant",
        "items": items,
    }


@router.get("/contract/{contract_id}")
async def get_contract_compliance(
    contract_id: int,
    status: Optional[ComplianceStatus] = None,
    category: Optional[ComplianceCategory] = None,
    contract_service: ContractService = Depends(get_contract_service),
):
    """Get compliance items for a specific contract."""
    # This would be implemented with a proper compliance store
    return {
        "contract_id": contract_id,
        "total": 0,
        "items": [],
    }


@router.get("/score/{contract_id}")
async def get_compliance_score(
    contract_id: int,
    contract_service: ContractService = Depends(get_contract_service),
):
    """Get compliance score for a specific contract."""
    score = await contract_service.calculate_compliance_score(contract_id)
    return {
        "contract_id": contract_id,
        "score": score,
        "rating": "excellent" if score >= 90 else "good" if score >= 70 else "needs_attention" if score >= 50 else "critical",
    }


@router.get("/categories")
async def list_compliance_categories():
    """Get list of available compliance categories."""
    return {
        "categories": [
            {"value": cc.value, "name": cc.name.replace("_", " ").title()}
            for cc in ComplianceCategory
        ]
    }


@router.get("/statuses")
async def list_compliance_statuses():
    """Get list of available compliance statuses."""
    return {
        "statuses": [
            {"value": cs.value, "name": cs.name.replace("_", " ").title()}
            for cs in ComplianceStatus
        ]
    }
