"""Compliance Status Checker Job."""

import logging
from datetime import datetime

logger = logging.getLogger(__name__)


async def check_compliance_status():
    """
    Review compliance items and flag issues.

    Runs weekly on Monday at 8:00 AM.
    Checks for:
    - Items pending review
    - Items past due date
    - Non-compliant contracts
    """
    logger.info("Starting compliance status check...")

    try:
        from app.services.odoo.contract_service import ContractService
        from app.services.notifications.webhook_service import WebhookService

        contract_service = ContractService()
        webhook_service = WebhookService()

        # Get items pending review
        pending_items = await contract_service.get_pending_compliance_items()

        for item in pending_items:
            await webhook_service.send_compliance_alert(
                compliance_id=item["id"],
                contract_id=item["contract_id"],
                contract_name=item.get("contract_name", "Unknown"),
                requirement=item["requirement"],
                status="pending_review",
                due_date=item.get("due_date"),
            )

            logger.info(
                f"Sent pending compliance alert: {item['requirement']} "
                f"(contract {item['contract_id']})"
            )

        # Get non-compliant items
        non_compliant_items = await contract_service.get_non_compliant_items()

        for item in non_compliant_items:
            await webhook_service.send_compliance_alert(
                compliance_id=item["id"],
                contract_id=item["contract_id"],
                contract_name=item.get("contract_name", "Unknown"),
                requirement=item["requirement"],
                status="non_compliant",
                due_date=item.get("due_date"),
            )

            logger.info(
                f"Sent non-compliant alert: {item['requirement']} "
                f"(contract {item['contract_id']})"
            )

        # Calculate and update compliance scores
        contracts = await contract_service.get_all_contracts()
        for contract in contracts:
            score = await contract_service.calculate_compliance_score(contract["id"])
            await contract_service.update_compliance_score(contract["id"], score)

        logger.info("Compliance status check completed")

    except Exception as e:
        logger.error(f"Compliance status check failed: {e}")
