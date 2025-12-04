"""Contract API Endpoints."""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query

from app.models.contract import (
    ContractCreate,
    ContractFilter,
    ContractListResponse,
    ContractResponse,
    ContractStatus,
    ContractType,
    ContractUpdate,
)
from app.services.odoo.contract_service import ContractService, get_contract_service
from app.services.odoo.document_service import DocumentService, get_document_service
from app.services.ai.gemini_client import GeminiClient, get_gemini_client
from app.core.exceptions import ContractNotFoundError

router = APIRouter(prefix="/contracts", tags=["Contracts"])


@router.get("", response_model=ContractListResponse)
async def list_contracts(
    status: Optional[ContractStatus] = None,
    contract_type: Optional[ContractType] = None,
    partner_id: Optional[int] = None,
    expiring_in_days: Optional[int] = None,
    search: Optional[str] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    contract_service: ContractService = Depends(get_contract_service),
):
    """
    List contracts with optional filtering and pagination.

    - **status**: Filter by contract status
    - **contract_type**: Filter by contract type
    - **partner_id**: Filter by Odoo partner ID
    - **expiring_in_days**: Filter contracts expiring within N days
    - **search**: Search in contract name and partner name
    - **page**: Page number (default 1)
    - **page_size**: Items per page (default 20, max 100)
    """
    filter = ContractFilter(
        status=status,
        contract_type=contract_type,
        partner_id=partner_id,
        expiring_in_days=expiring_in_days,
        search=search,
    )

    result = await contract_service.list_contracts(
        filter=filter,
        page=page,
        page_size=page_size,
    )

    return ContractListResponse(**result)


@router.get("/expiring")
async def get_expiring_contracts(
    days: int = Query(30, ge=1, le=365, description="Days until expiry"),
    contract_service: ContractService = Depends(get_contract_service),
):
    """
    Get contracts expiring within the specified number of days.

    Returns contracts sorted by expiry date (soonest first).
    """
    contracts = await contract_service.get_expiring_contracts(days)
    return {
        "total": len(contracts),
        "days_threshold": days,
        "contracts": sorted(
            contracts,
            key=lambda x: x.get("days_until_expiry", 999),
        ),
    }


@router.get("/{contract_id}", response_model=ContractResponse)
async def get_contract(
    contract_id: int,
    contract_service: ContractService = Depends(get_contract_service),
):
    """Get a contract by ID."""
    try:
        return await contract_service.get_contract(contract_id)
    except ContractNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e.message))


@router.post("", response_model=ContractResponse, status_code=201)
async def create_contract(
    contract: ContractCreate,
    contract_service: ContractService = Depends(get_contract_service),
):
    """
    Create a new contract.

    Required fields:
    - **name**: Contract name/title
    - **contract_type**: Type of contract
    - **partner_id**: Odoo partner ID
    - **start_date**: Contract start date
    - **end_date**: Contract end date
    """
    return await contract_service.create_contract(contract)


@router.put("/{contract_id}", response_model=ContractResponse)
async def update_contract(
    contract_id: int,
    update: ContractUpdate,
    contract_service: ContractService = Depends(get_contract_service),
):
    """Update a contract."""
    try:
        return await contract_service.update_contract(contract_id, update)
    except ContractNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e.message))


@router.delete("/{contract_id}", status_code=204)
async def delete_contract(
    contract_id: int,
    contract_service: ContractService = Depends(get_contract_service),
):
    """Delete a contract."""
    try:
        await contract_service.delete_contract(contract_id)
    except ContractNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e.message))


@router.get("/{contract_id}/documents")
async def get_contract_documents(
    contract_id: int,
    contract_service: ContractService = Depends(get_contract_service),
    document_service: DocumentService = Depends(get_document_service),
):
    """Get documents attached to a contract."""
    try:
        contract = await contract_service.get_contract(contract_id)
        document_ids = contract.document_ids

        if not document_ids:
            return {"contract_id": contract_id, "documents": []}

        documents = document_service.get_documents(document_ids)
        return {
            "contract_id": contract_id,
            "total": len(documents),
            "documents": documents,
        }

    except ContractNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e.message))


@router.post("/{contract_id}/analyze")
async def analyze_contract(
    contract_id: int,
    contract_service: ContractService = Depends(get_contract_service),
    document_service: DocumentService = Depends(get_document_service),
    gemini: GeminiClient = Depends(get_gemini_client),
):
    """
    Trigger AI analysis of a contract.

    Extracts text from attached documents and performs:
    - Contract summary
    - Clause extraction
    - Risk assessment
    - Key date extraction
    """
    if not gemini.is_available():
        raise HTTPException(
            status_code=503,
            detail="AI service not available. Check GEMINI_API_KEY configuration.",
        )

    try:
        contract = await contract_service.get_contract(contract_id)
        document_ids = contract.document_ids

        if not document_ids:
            raise HTTPException(
                status_code=400,
                detail="No documents attached to this contract for analysis.",
            )

        # Extract text from first document
        document_id = document_ids[0]
        document_text = document_service.extract_text(document_id)

        # Perform AI analysis
        analysis = await gemini.analyze_contract_text(document_text, analysis_type="full")

        return {
            "contract_id": contract_id,
            "document_id": document_id,
            "analysis": analysis,
        }

    except ContractNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e.message))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")


@router.get("/{contract_id}/summary")
async def get_contract_summary(
    contract_id: int,
    contract_service: ContractService = Depends(get_contract_service),
    document_service: DocumentService = Depends(get_document_service),
    gemini: GeminiClient = Depends(get_gemini_client),
):
    """Get AI-generated contract summary."""
    if not gemini.is_available():
        raise HTTPException(
            status_code=503,
            detail="AI service not available.",
        )

    try:
        contract = await contract_service.get_contract(contract_id)
        document_ids = contract.document_ids

        if not document_ids:
            return {
                "contract_id": contract_id,
                "summary": f"Contract: {contract.name}. No documents available for detailed analysis.",
            }

        # Extract text and generate summary
        document_text = document_service.extract_text(document_ids[0])
        analysis = await gemini.analyze_contract_text(document_text, analysis_type="full")

        return {
            "contract_id": contract_id,
            "name": contract.name,
            "summary": analysis.get("summary", "Summary not available"),
            "key_terms": analysis.get("key_terms", []),
            "important_dates": analysis.get("important_dates", []),
        }

    except ContractNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e.message))
