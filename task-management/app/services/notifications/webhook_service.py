"""Webhook Notification Service."""

import hashlib
import hmac
import json
import logging
from datetime import datetime
from typing import Any, Dict, Optional

import httpx

from app.config import settings

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
            settings.WEBHOOK_OVERDUE_URL
            or settings.WEBHOOK_ASSIGNMENT_URL
            or settings.WEBHOOK_REPORT_URL
            or settings.WEBHOOK_MANAGER_URL
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
            event_type: Type of event (e.g., 'task.overdue')
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

    async def send_overdue_alert(
        self,
        user_id: int,
        user_name: str,
        tasks: list,
    ) -> bool:
        """Send overdue task alert webhook."""
        return await self.send(
            url=settings.WEBHOOK_OVERDUE_URL,
            event_type="task.overdue",
            payload={
                "user_id": user_id,
                "user_name": user_name,
                "overdue_count": len(tasks),
                "tasks": [
                    {
                        "id": t.get("id"),
                        "name": t.get("name"),
                        "deadline": t.get("date_deadline"),
                        "priority": t.get("priority"),
                    }
                    for t in tasks[:20]  # Limit to 20 tasks
                ],
            },
        )

    async def send_task_assigned(
        self,
        task_id: int,
        task_name: str,
        user_id: int,
        user_name: str,
        assigned_by: str = "System",
    ) -> bool:
        """Send task assignment webhook."""
        return await self.send(
            url=settings.WEBHOOK_ASSIGNMENT_URL,
            event_type="task.assigned",
            payload={
                "task_id": task_id,
                "task_name": task_name,
                "assigned_to_id": user_id,
                "assigned_to_name": user_name,
                "assigned_by": assigned_by,
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
            event_type="report.ready",
            payload={
                "report_type": report_type,
                "report_id": report_id,
                "summary": summary,
            },
        )

    async def send_manager_alert(
        self,
        alert_type: str,
        message: str,
        data: Optional[Dict] = None,
    ) -> bool:
        """Send manager alert webhook."""
        return await self.send(
            url=settings.WEBHOOK_MANAGER_URL,
            event_type=f"alert.{alert_type}",
            payload={
                "alert_type": alert_type,
                "message": message,
                "data": data or {},
            },
        )

    async def send_bottleneck_detected(
        self,
        bottleneck_type: str,
        location: str,
        severity: str,
        recommendation: str,
    ) -> bool:
        """Send bottleneck detection webhook."""
        return await self.send(
            url=settings.WEBHOOK_MANAGER_URL,
            event_type="bottleneck.detected",
            payload={
                "type": bottleneck_type,
                "location": location,
                "severity": severity,
                "recommendation": recommendation,
            },
        )
