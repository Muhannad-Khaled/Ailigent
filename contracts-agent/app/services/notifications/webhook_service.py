"""Webhook Notification Service."""

import hashlib
import hmac
import json
import logging
from datetime import datetime
from typing import Any, Dict, Optional

import httpx

from app.config import settings
from app.core.constants import (
    EVENT_COMPLIANCE_ALERT,
    EVENT_CONTRACT_EXPIRED,
    EVENT_CONTRACT_EXPIRING,
    EVENT_MILESTONE_OVERDUE,
    EVENT_MILESTONE_UPCOMING,
    EVENT_REPORT_READY,
)

logger = logging.getLogger(__name__)


class WebhookService:
    """Async webhook delivery service with retry and signature."""

    def __init__(self):
        self.secret = settings.WEBHOOK_SECRET
        self.timeout = httpx.Timeout(30.0)
        self.max_retries = 3

    def is_configured(self) -> bool:
        """Check if webhook service has any webhooks configured."""
        return bool(
            settings.WEBHOOK_CONTRACT_EXPIRY_URL
            or settings.WEBHOOK_MILESTONE_URL
            or settings.WEBHOOK_COMPLIANCE_URL
            or settings.WEBHOOK_REPORT_URL
        )

    async def send(
        self,
        url: str,
        event_type: str,
        payload: Dict[str, Any],
        headers: Optional[Dict[str, str]] = None,
    ) -> bool:
        """
        Send webhook with signature and retry logic.

        Args:
            url: Webhook endpoint URL
            event_type: Type of event (e.g., 'contract.expiring')
            payload: Data to send
            headers: Additional headers

        Returns:
            True if sent successfully
        """
        if not url:
            logger.debug(f"Webhook URL not configured for event {event_type}")
            return False

        webhook_payload = {
            "event_type": event_type,
            "timestamp": datetime.utcnow().isoformat(),
            "source": "contracts-agent",
            "data": payload,
        }

        signature = self._generate_signature(webhook_payload)

        request_headers = {
            "Content-Type": "application/json",
            "X-Webhook-Signature": signature,
            "X-Event-Type": event_type,
            "X-Timestamp": webhook_payload["timestamp"],
            **(headers or {}),
        }

        for attempt in range(self.max_retries):
            try:
                async with httpx.AsyncClient(timeout=self.timeout) as client:
                    response = await client.post(
                        url,
                        json=webhook_payload,
                        headers=request_headers,
                    )

                    if 200 <= response.status_code < 300:
                        logger.info(f"Webhook sent successfully to {url}")
                        return True
                    else:
                        logger.warning(
                            f"Webhook to {url} returned {response.status_code}: {response.text[:200]}"
                        )

            except httpx.TimeoutException:
                logger.warning(f"Webhook timeout (attempt {attempt + 1}/{self.max_retries}): {url}")
            except Exception as e:
                logger.error(f"Webhook error (attempt {attempt + 1}/{self.max_retries}): {e}")

            # Wait before retry (exponential backoff)
            if attempt < self.max_retries - 1:
                import asyncio
                await asyncio.sleep(2 ** attempt)

        logger.error(f"All webhook attempts to {url} failed")
        return False

    def _generate_signature(self, payload: Dict) -> str:
        """Generate HMAC signature for webhook payload."""
        if not self.secret:
            return "none"

        payload_str = json.dumps(payload, sort_keys=True, default=str)
        signature = hmac.new(
            self.secret.encode(),
            payload_str.encode(),
            hashlib.sha256,
        ).hexdigest()

        return f"sha256={signature}"

    async def send_contract_expiry_alert(
        self,
        contract_id: int,
        contract_name: str,
        expiry_date: str,
        days_until_expiry: int,
        partner_name: str,
        contract_value: Optional[float] = None,
    ) -> bool:
        """Send contract expiry alert webhook."""
        urgency = "low"
        if days_until_expiry <= 7:
            urgency = "critical"
        elif days_until_expiry <= 14:
            urgency = "high"
        elif days_until_expiry <= 30:
            urgency = "medium"

        return await self.send(
            url=settings.WEBHOOK_CONTRACT_EXPIRY_URL,
            event_type=EVENT_CONTRACT_EXPIRING,
            payload={
                "contract_id": contract_id,
                "contract_name": contract_name,
                "expiry_date": expiry_date,
                "days_until_expiry": days_until_expiry,
                "partner_name": partner_name,
                "contract_value": contract_value,
                "urgency": urgency,
                "action_required": "Review for renewal or termination",
            },
        )

    async def send_contract_expired_alert(
        self,
        contract_id: int,
        contract_name: str,
        expiry_date: str,
        partner_name: str,
    ) -> bool:
        """Send contract expired alert webhook."""
        return await self.send(
            url=settings.WEBHOOK_CONTRACT_EXPIRY_URL,
            event_type=EVENT_CONTRACT_EXPIRED,
            payload={
                "contract_id": contract_id,
                "contract_name": contract_name,
                "expiry_date": expiry_date,
                "partner_name": partner_name,
                "urgency": "critical",
                "action_required": "Immediate attention required - contract has expired",
            },
        )

    async def send_milestone_alert(
        self,
        milestone_id: int,
        milestone_name: str,
        contract_id: int,
        contract_name: str,
        due_date: str,
        days_until_due: int,
        is_overdue: bool = False,
    ) -> bool:
        """Send milestone alert webhook."""
        event_type = EVENT_MILESTONE_OVERDUE if is_overdue else EVENT_MILESTONE_UPCOMING

        urgency = "low"
        if is_overdue:
            urgency = "critical"
        elif days_until_due <= 1:
            urgency = "high"
        elif days_until_due <= 3:
            urgency = "medium"

        return await self.send(
            url=settings.WEBHOOK_MILESTONE_URL,
            event_type=event_type,
            payload={
                "milestone_id": milestone_id,
                "milestone_name": milestone_name,
                "contract_id": contract_id,
                "contract_name": contract_name,
                "due_date": due_date,
                "days_until_due": days_until_due,
                "is_overdue": is_overdue,
                "urgency": urgency,
                "action_required": "Milestone overdue - immediate action required" if is_overdue else "Milestone approaching deadline",
            },
        )

    async def send_compliance_alert(
        self,
        compliance_id: int,
        contract_id: int,
        contract_name: str,
        requirement: str,
        status: str,
        due_date: Optional[str] = None,
    ) -> bool:
        """Send compliance alert webhook."""
        urgency = "high" if status == "non_compliant" else "medium"

        return await self.send(
            url=settings.WEBHOOK_COMPLIANCE_URL,
            event_type=EVENT_COMPLIANCE_ALERT,
            payload={
                "compliance_id": compliance_id,
                "contract_id": contract_id,
                "contract_name": contract_name,
                "requirement": requirement,
                "status": status,
                "due_date": due_date,
                "urgency": urgency,
                "action_required": f"Compliance issue: {status}",
            },
        )

    async def send_report_ready(
        self,
        report_type: str,
        report_id: str,
        summary: Dict[str, Any],
    ) -> bool:
        """Send report ready webhook."""
        return await self.send(
            url=settings.WEBHOOK_REPORT_URL,
            event_type=EVENT_REPORT_READY,
            payload={
                "report_type": report_type,
                "report_id": report_id,
                "summary": summary,
            },
        )


def get_webhook_service() -> WebhookService:
    """Get webhook service instance."""
    return WebhookService()
