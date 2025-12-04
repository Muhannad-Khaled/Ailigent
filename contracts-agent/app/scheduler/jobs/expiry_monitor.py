"""Contract Expiry Monitor Job."""

import logging
from datetime import datetime

logger = logging.getLogger(__name__)


async def check_contract_expiry():
    """
    Check for contracts expiring soon and send alerts.

    Runs daily at 7:00 AM.
    Alerts for contracts expiring in 30, 14, and 7 days.
    """
    logger.info("Starting contract expiry check...")

    try:
        from app.services.odoo.contract_service import ContractService
        from app.services.notifications.webhook_service import WebhookService
        from app.config import settings

        contract_service = ContractService()
        webhook_service = WebhookService()

        alert_days = settings.expiry_alert_days_list  # [30, 14, 7]

        for days in alert_days:
            expiring_contracts = await contract_service.get_expiring_contracts(days)

            for contract in expiring_contracts:
                # Send webhook notification
                await webhook_service.send_contract_expiry_alert(
                    contract_id=contract["id"],
                    contract_name=contract["name"],
                    expiry_date=contract["end_date"],
                    days_until_expiry=days,
                    partner_name=contract.get("partner_name", "Unknown"),
                    contract_value=contract.get("value"),
                )

                logger.info(
                    f"Sent expiry alert for contract {contract['id']} "
                    f"({contract['name']}) - expires in {days} days"
                )

        logger.info("Contract expiry check completed")

    except Exception as e:
        logger.error(f"Contract expiry check failed: {e}")
