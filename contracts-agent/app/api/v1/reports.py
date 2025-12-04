"""Report API Endpoints."""

from datetime import date, datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query

from app.models.report import ReportType
from app.services.odoo.contract_service import ContractService, get_contract_service
from app.services.ai.gemini_client import GeminiClient, get_gemini_client

router = APIRouter(prefix="/reports", tags=["Reports"])


@router.get("/portfolio")
async def get_portfolio_report(
    contract_service: ContractService = Depends(get_contract_service),
):
    """
    Get portfolio overview report.

    Includes:
    - Total contracts by status
    - Total contract value
    - Contracts by type
    - Average compliance score
    """
    contracts = await contract_service.get_all_contracts()

    # Calculate metrics
    total_value = sum(c.get("value", 0) or 0 for c in contracts)
    by_status = {}
    by_type = {}

    for c in contracts:
        status = c.get("status", "unknown")
        ctype = c.get("contract_type", "unknown")
        by_status[status] = by_status.get(status, 0) + 1
        by_type[ctype] = by_type.get(ctype, 0) + 1

    # Count expiring
    expiring = len([c for c in contracts if c.get("status") == "expiring_soon"])
    expired = len([c for c in contracts if c.get("status") == "expired"])

    # Calculate average compliance
    scores = [c.get("compliance_score") for c in contracts if c.get("compliance_score") is not None]
    avg_compliance = sum(scores) / len(scores) if scores else 100.0

    return {
        "report_type": "portfolio",
        "generated_at": datetime.utcnow().isoformat(),
        "metrics": {
            "total_contracts": len(contracts),
            "active_contracts": by_status.get("active", 0),
            "expiring_soon": expiring,
            "expired": expired,
            "total_value": total_value,
            "currency": "USD",
            "by_type": by_type,
            "by_status": by_status,
            "average_compliance_score": round(avg_compliance, 2),
        },
    }


@router.get("/expiry")
async def get_expiry_report(
    contract_service: ContractService = Depends(get_contract_service),
):
    """
    Get expiry timeline report.

    Shows contracts expiring in:
    - 30 days
    - 60 days
    - 90 days
    """
    expiring_30 = await contract_service.get_expiring_contracts(30)
    expiring_60 = await contract_service.get_expiring_contracts(60)
    expiring_90 = await contract_service.get_expiring_contracts(90)

    # Remove duplicates (30 is subset of 60, etc.)
    ids_30 = {c["id"] for c in expiring_30}
    ids_60 = {c["id"] for c in expiring_60}

    only_60 = [c for c in expiring_60 if c["id"] not in ids_30]
    only_90 = [c for c in expiring_90 if c["id"] not in ids_60]

    total_value_at_risk = sum(
        c.get("value", 0) or 0 for c in expiring_90
    )

    return {
        "report_type": "expiry",
        "generated_at": datetime.utcnow().isoformat(),
        "contracts_expiring_30_days": expiring_30,
        "contracts_expiring_31_60_days": only_60,
        "contracts_expiring_61_90_days": only_90,
        "summary": {
            "total_expiring_90_days": len(expiring_90),
            "total_value_at_risk": total_value_at_risk,
            "currency": "USD",
        },
        "recommendations": [
            "Review contracts expiring in 30 days for renewal decisions",
            "Initiate renewal negotiations for high-value contracts",
            "Update stakeholders on expiring contracts",
        ],
    }


@router.get("/compliance")
async def get_compliance_report(
    contract_service: ContractService = Depends(get_contract_service),
):
    """
    Get compliance summary report.

    Shows:
    - Overall compliance score
    - Contracts by compliance status
    - Non-compliant items
    - Pending reviews
    """
    contracts = await contract_service.get_all_contracts()
    pending = await contract_service.get_pending_compliance_items()
    non_compliant = await contract_service.get_non_compliant_items()

    # Calculate scores
    scores = []
    for contract in contracts:
        score = await contract_service.calculate_compliance_score(contract["id"])
        scores.append({
            "contract_id": contract["id"],
            "contract_name": contract.get("name"),
            "score": score,
        })

    overall_score = sum(s["score"] for s in scores) / len(scores) if scores else 100.0

    return {
        "report_type": "compliance",
        "generated_at": datetime.utcnow().isoformat(),
        "overall_compliance_score": round(overall_score, 2),
        "total_contracts": len(contracts),
        "contracts_by_score": sorted(scores, key=lambda x: x["score"]),
        "non_compliant_items": non_compliant,
        "pending_reviews": pending,
        "recommendations": [
            "Address non-compliant items immediately",
            "Complete pending compliance reviews",
            "Schedule regular compliance audits",
        ],
    }


@router.get("/contract/{contract_id}")
async def get_contract_status_report(
    contract_id: int,
    contract_service: ContractService = Depends(get_contract_service),
    gemini: GeminiClient = Depends(get_gemini_client),
):
    """Get detailed status report for a single contract."""
    try:
        contract = await contract_service.get_contract(contract_id)
        compliance_score = await contract_service.calculate_compliance_score(contract_id)

        return {
            "report_type": "contract_status",
            "generated_at": datetime.utcnow().isoformat(),
            "contract_id": contract_id,
            "contract_name": contract.name,
            "contract_type": contract.contract_type,
            "status": contract.status,
            "partner_name": contract.partner_name,
            "start_date": contract.start_date.isoformat(),
            "end_date": contract.end_date.isoformat(),
            "days_until_expiry": contract.days_until_expiry,
            "value": contract.value,
            "currency": contract.currency,
            "compliance_score": compliance_score,
            "documents_attached": len(contract.document_ids),
        }

    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/types")
async def list_report_types():
    """Get list of available report types."""
    return {
        "report_types": [
            {"value": rt.value, "name": rt.name.replace("_", " ").title()}
            for rt in ReportType
        ]
    }
