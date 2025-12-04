"""Delivery Date Monitor Job."""

import logging
from datetime import datetime

logger = logging.getLogger(__name__)


async def check_delivery_dates():
    """
    Check for upcoming and overdue milestones.

    Runs every 6 hours.
    Alerts for milestones due in 7, 3, and 1 days, and overdue milestones.
    """
    logger.info("Starting delivery date check...")

    try:
        from app.services.odoo.contract_service import ContractService
        from app.services.notifications.webhook_service import WebhookService
        from app.config import settings

        contract_service = ContractService()
        webhook_service = WebhookService()

        alert_days = settings.milestone_alert_days_list  # [7, 3, 1]

        # Check for upcoming milestones
        for days in alert_days:
            upcoming_milestones = await contract_service.get_upcoming_milestones(days)

            for milestone in upcoming_milestones:
                await webhook_service.send_milestone_alert(
                    milestone_id=milestone["id"],
                    milestone_name=milestone["name"],
                    contract_id=milestone["contract_id"],
                    contract_name=milestone.get("contract_name", "Unknown"),
                    due_date=milestone["due_date"],
                    days_until_due=days,
                    is_overdue=False,
                )

                logger.info(
                    f"Sent upcoming milestone alert: {milestone['name']} "
                    f"(contract {milestone['contract_id']}) - due in {days} days"
                )

        # Check for overdue milestones
        overdue_milestones = await contract_service.get_overdue_milestones()

        for milestone in overdue_milestones:
            await webhook_service.send_milestone_alert(
                milestone_id=milestone["id"],
                milestone_name=milestone["name"],
                contract_id=milestone["contract_id"],
                contract_name=milestone.get("contract_name", "Unknown"),
                due_date=milestone["due_date"],
                days_until_due=milestone.get("days_overdue", 0) * -1,
                is_overdue=True,
            )

            logger.info(
                f"Sent overdue milestone alert: {milestone['name']} "
                f"(contract {milestone['contract_id']})"
            )

        logger.info("Delivery date check completed")

    except Exception as e:
        logger.error(f"Delivery date check failed: {e}")
