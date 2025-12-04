"""Contract Service for managing contracts."""

import logging
from datetime import date, datetime, timedelta
from typing import Any, Dict, List, Optional

from app.core.exceptions import ContractNotFoundError
from app.models.contract import (
    ContractCreate,
    ContractFilter,
    ContractResponse,
    ContractStatus,
    ContractUpdate,
)
from app.models.milestone import MilestoneStatus
from app.models.compliance import ComplianceStatus
from app.services.odoo.client import OdooClient, get_odoo_client

logger = logging.getLogger(__name__)


# In-memory storage for contracts (can be replaced with database)
_contracts_db: Dict[int, Dict[str, Any]] = {}
_milestones_db: Dict[int, Dict[str, Any]] = {}
_compliance_db: Dict[int, Dict[str, Any]] = {}
_next_contract_id = 1
_next_milestone_id = 1
_next_compliance_id = 1


class ContractService:
    """Service for managing contracts."""

    def __init__(self, odoo_client: Optional[OdooClient] = None):
        self.odoo = odoo_client or get_odoo_client()

    def _calculate_status(self, contract: Dict[str, Any]) -> ContractStatus:
        """Calculate contract status based on dates."""
        today = date.today()
        end_date = contract.get("end_date")

        if isinstance(end_date, str):
            end_date = datetime.fromisoformat(end_date).date()

        if not end_date:
            return ContractStatus.DRAFT

        if end_date < today:
            return ContractStatus.EXPIRED

        days_until_expiry = (end_date - today).days
        if days_until_expiry <= 30:
            return ContractStatus.EXPIRING_SOON

        return ContractStatus.ACTIVE

    def _calculate_days_until_expiry(self, end_date: date) -> Optional[int]:
        """Calculate days until contract expires."""
        if not end_date:
            return None
        today = date.today()
        return (end_date - today).days

    async def create_contract(self, contract: ContractCreate) -> ContractResponse:
        """Create a new contract."""
        global _next_contract_id

        now = datetime.utcnow()
        contract_id = _next_contract_id
        _next_contract_id += 1

        # Get partner name from Odoo
        partner_name = None
        try:
            partners = self.odoo.read("res.partner", [contract.partner_id], ["name"])
            if partners:
                partner_name = partners[0].get("name")
        except Exception as e:
            logger.warning(f"Failed to get partner name: {e}")

        contract_data = {
            "id": contract_id,
            "name": contract.name,
            "contract_type": contract.contract_type.value,
            "partner_id": contract.partner_id,
            "partner_name": partner_name or contract.partner_name,
            "start_date": contract.start_date.isoformat(),
            "end_date": contract.end_date.isoformat(),
            "value": contract.value,
            "currency": contract.currency,
            "description": contract.description,
            "project_ids": contract.project_ids,
            "document_ids": contract.document_ids,
            "clause_count": 0,
            "milestone_count": 0,
            "compliance_score": None,
            "active_alerts": 0,
            "created_at": now.isoformat(),
            "updated_at": now.isoformat(),
        }

        contract_data["status"] = self._calculate_status(contract_data)
        contract_data["days_until_expiry"] = self._calculate_days_until_expiry(contract.end_date)

        _contracts_db[contract_id] = contract_data

        return ContractResponse(**contract_data)

    async def get_contract(self, contract_id: int) -> ContractResponse:
        """Get a contract by ID."""
        contract_data = _contracts_db.get(contract_id)
        if not contract_data:
            raise ContractNotFoundError(
                f"Contract with ID {contract_id} not found",
                details={"contract_id": contract_id},
            )

        # Recalculate status and days
        contract_data["status"] = self._calculate_status(contract_data)
        end_date = contract_data.get("end_date")
        if isinstance(end_date, str):
            end_date = datetime.fromisoformat(end_date).date()
        contract_data["days_until_expiry"] = self._calculate_days_until_expiry(end_date)

        return ContractResponse(**contract_data)

    async def update_contract(
        self, contract_id: int, update: ContractUpdate
    ) -> ContractResponse:
        """Update a contract."""
        contract_data = _contracts_db.get(contract_id)
        if not contract_data:
            raise ContractNotFoundError(
                f"Contract with ID {contract_id} not found",
                details={"contract_id": contract_id},
            )

        update_dict = update.model_dump(exclude_unset=True)
        for key, value in update_dict.items():
            if value is not None:
                if isinstance(value, date):
                    contract_data[key] = value.isoformat()
                elif hasattr(value, "value"):
                    contract_data[key] = value.value
                else:
                    contract_data[key] = value

        contract_data["updated_at"] = datetime.utcnow().isoformat()
        contract_data["status"] = self._calculate_status(contract_data)

        end_date = contract_data.get("end_date")
        if isinstance(end_date, str):
            end_date = datetime.fromisoformat(end_date).date()
        contract_data["days_until_expiry"] = self._calculate_days_until_expiry(end_date)

        return ContractResponse(**contract_data)

    async def delete_contract(self, contract_id: int) -> bool:
        """Delete a contract."""
        if contract_id not in _contracts_db:
            raise ContractNotFoundError(
                f"Contract with ID {contract_id} not found",
                details={"contract_id": contract_id},
            )

        del _contracts_db[contract_id]
        return True

    async def list_contracts(
        self,
        filter: Optional[ContractFilter] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> Dict[str, Any]:
        """List contracts with filtering and pagination."""
        contracts = list(_contracts_db.values())

        # Apply filters
        if filter:
            if filter.status:
                contracts = [c for c in contracts if c.get("status") == filter.status.value]
            if filter.contract_type:
                contracts = [c for c in contracts if c.get("contract_type") == filter.contract_type.value]
            if filter.partner_id:
                contracts = [c for c in contracts if c.get("partner_id") == filter.partner_id]
            if filter.search:
                search_lower = filter.search.lower()
                contracts = [
                    c for c in contracts
                    if search_lower in c.get("name", "").lower()
                    or search_lower in (c.get("partner_name") or "").lower()
                ]
            if filter.expiring_in_days:
                today = date.today()
                max_date = today + timedelta(days=filter.expiring_in_days)
                contracts = [
                    c for c in contracts
                    if c.get("end_date") and datetime.fromisoformat(c["end_date"]).date() <= max_date
                ]

        # Recalculate status for all contracts
        for contract in contracts:
            contract["status"] = self._calculate_status(contract)
            end_date = contract.get("end_date")
            if isinstance(end_date, str):
                end_date = datetime.fromisoformat(end_date).date()
            contract["days_until_expiry"] = self._calculate_days_until_expiry(end_date)

        total = len(contracts)
        start = (page - 1) * page_size
        end = start + page_size
        paginated = contracts[start:end]

        return {
            "total": total,
            "page": page,
            "page_size": page_size,
            "contracts": paginated,
        }

    async def get_expiring_contracts(self, days: int) -> List[Dict[str, Any]]:
        """Get contracts expiring within specified days."""
        today = date.today()
        target_date = today + timedelta(days=days)

        expiring = []
        for contract in _contracts_db.values():
            end_date = contract.get("end_date")
            if isinstance(end_date, str):
                end_date = datetime.fromisoformat(end_date).date()

            if end_date and today <= end_date <= target_date:
                contract["days_until_expiry"] = (end_date - today).days
                expiring.append(contract)

        return expiring

    async def get_all_contracts(self) -> List[Dict[str, Any]]:
        """Get all contracts."""
        return list(_contracts_db.values())

    # Milestone methods
    async def get_upcoming_milestones(self, days: int) -> List[Dict[str, Any]]:
        """Get milestones due within specified days."""
        today = date.today()
        target_date = today + timedelta(days=days)

        upcoming = []
        for milestone in _milestones_db.values():
            due_date = milestone.get("due_date")
            if isinstance(due_date, str):
                due_date = datetime.fromisoformat(due_date).date()

            if due_date and today <= due_date <= target_date:
                if milestone.get("status") not in [MilestoneStatus.COMPLETED.value, MilestoneStatus.CANCELLED.value]:
                    milestone["days_until_due"] = (due_date - today).days
                    upcoming.append(milestone)

        return upcoming

    async def get_overdue_milestones(self) -> List[Dict[str, Any]]:
        """Get overdue milestones."""
        today = date.today()

        overdue = []
        for milestone in _milestones_db.values():
            due_date = milestone.get("due_date")
            if isinstance(due_date, str):
                due_date = datetime.fromisoformat(due_date).date()

            if due_date and due_date < today:
                if milestone.get("status") not in [MilestoneStatus.COMPLETED.value, MilestoneStatus.CANCELLED.value]:
                    milestone["days_overdue"] = (today - due_date).days
                    overdue.append(milestone)

        return overdue

    # Compliance methods
    async def get_pending_compliance_items(self) -> List[Dict[str, Any]]:
        """Get compliance items pending review."""
        return [
            item for item in _compliance_db.values()
            if item.get("status") == ComplianceStatus.PENDING_REVIEW.value
        ]

    async def get_non_compliant_items(self) -> List[Dict[str, Any]]:
        """Get non-compliant items."""
        return [
            item for item in _compliance_db.values()
            if item.get("status") == ComplianceStatus.NON_COMPLIANT.value
        ]

    async def calculate_compliance_score(self, contract_id: int) -> float:
        """Calculate compliance score for a contract."""
        items = [
            item for item in _compliance_db.values()
            if item.get("contract_id") == contract_id
        ]

        if not items:
            return 100.0

        compliant = sum(
            1 for item in items
            if item.get("status") in [
                ComplianceStatus.COMPLIANT.value,
                ComplianceStatus.EXEMPTED.value,
                ComplianceStatus.NOT_APPLICABLE.value,
            ]
        )

        return (compliant / len(items)) * 100

    async def update_compliance_score(self, contract_id: int, score: float) -> None:
        """Update compliance score for a contract."""
        if contract_id in _contracts_db:
            _contracts_db[contract_id]["compliance_score"] = score
            _contracts_db[contract_id]["updated_at"] = datetime.utcnow().isoformat()


def get_contract_service() -> ContractService:
    """Get contract service instance."""
    return ContractService()
