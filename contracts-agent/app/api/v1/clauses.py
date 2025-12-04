"""Clause API Endpoints."""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query

from app.models.clause import ClauseType
from app.services.odoo.contract_service import ContractService, get_contract_service
from app.services.odoo.document_service import DocumentService, get_document_service
from app.services.ai.clause_extractor import ClauseExtractor, get_clause_extractor
from app.services.ai.gemini_client import GeminiClient, get_gemini_client
from app.core.exceptions import ContractNotFoundError, DocumentProcessingError

router = APIRouter(prefix="/clauses", tags=["Clauses"])


@router.post("/extract/{contract_id}")
async def extract_clauses(
    contract_id: int,
    document_id: Optional[int] = None,
    contract_service: ContractService = Depends(get_contract_service),
    document_service: DocumentService = Depends(get_document_service),
    clause_extractor: ClauseExtractor = Depends(get_clause_extractor),
):
    """
    Extract clauses from a contract document using AI.

    If document_id is not specified, uses the first attached document.
    """
    try:
        contract = await contract_service.get_contract(contract_id)

        if document_id is None:
            if not contract.document_ids:
                raise HTTPException(
                    status_code=400,
                    detail="No documents attached to this contract.",
                )
            document_id = contract.document_ids[0]

        # Extract text from document
        document_text = document_service.extract_text(document_id)

        # Extract clauses using AI
        result = await clause_extractor.extract_clauses(
            document_text=document_text,
            contract_id=contract_id,
            document_id=document_id,
        )

        return result

    except ContractNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e.message))
    except DocumentProcessingError as e:
        raise HTTPException(status_code=400, detail=str(e.message))


@router.post("/analyze-risk")
async def analyze_clause_risk(
    clause_content: str,
    clause_type: ClauseType = ClauseType.OTHER,
    clause_extractor: ClauseExtractor = Depends(get_clause_extractor),
):
    """
    Analyze risk for a specific clause.

    Provide the clause content and optionally the clause type for better analysis.
    """
    try:
        analysis = await clause_extractor.analyze_clause_risk(
            clause_content=clause_content,
            clause_type=clause_type.value,
        )
        return {
            "clause_type": clause_type,
            "analysis": analysis,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")


@router.post("/batch-analyze")
async def batch_analyze_clauses(
    clauses: list,
    clause_extractor: ClauseExtractor = Depends(get_clause_extractor),
):
    """
    Analyze multiple clauses for risk.

    Expects a list of objects with 'content' and optionally 'clause_type'.
    """
    try:
        results = await clause_extractor.batch_analyze_clauses(clauses)
        return {
            "total": len(results),
            "analyzed": len([r for r in results if r.get("risk_analysis")]),
            "clauses": results,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Batch analysis failed: {str(e)}")


@router.get("/types")
async def list_clause_types():
    """Get list of available clause types."""
    return {
        "clause_types": [
            {"value": ct.value, "name": ct.name.replace("_", " ").title()}
            for ct in ClauseType
        ]
    }
