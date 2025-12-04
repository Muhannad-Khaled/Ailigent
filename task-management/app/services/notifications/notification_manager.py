"""Unified Notification Manager."""

import logging
from typing import Dict, List, Optional

from app.config import settings
from app.services.notifications.email_service import EmailService
from app.services.notifications.webhook_service import WebhookService
from app.services.odoo.client import get_odoo_client
from app.services.odoo.employee_service import OdooEmployeeService

logger = logging.getLogger(__name__)


class NotificationManager:
    """Central notification orchestration for all channels."""

    def __init__(
        self,
        email_service: Optional[EmailService] = None,
        webhook_service: Optional[WebhookService] = None,
    ):
        self.email = email_service or EmailService()
        self.webhook = webhook_service or WebhookService()
        self._employee_service: Optional[OdooEmployeeService] = None

    @property
    def employee_service(self) -> OdooEmployeeService:
        """Lazy load employee service."""
        if self._employee_service is None:
            self._employee_service = OdooEmployeeService(get_odoo_client())
        return self._employee_service

    async def send_overdue_alerts(
        self,
        overdue_tasks_by_user: Dict[int, List[Dict]],
    ) -> Dict[str, int]:
        """
        Send overdue alerts to all affected users.

        Args:
            overdue_tasks_by_user: Dict mapping user_id to list of overdue tasks

        Returns:
            Summary of sent notifications
        """
        results = {"email_sent": 0, "email_failed": 0, "webhook_sent": 0, "webhook_failed": 0}

        for user_id, tasks in overdue_tasks_by_user.items():
            if not tasks:
                continue

            try:
                user_info = await self._get_user_info(user_id)
                if not user_info:
                    logger.warning(f"Could not find user info for user_id {user_id}")
                    continue

                user_name = user_info.get("name", "User")
                user_email = user_info.get("email")

                # Send email if configured
                if user_email and self.email.is_configured():
                    success = await self.email.send_overdue_alert(
                        to_email=user_email,
                        user_name=user_name,
                        tasks=tasks,
                    )
                    if success:
                        results["email_sent"] += 1
                    else:
                        results["email_failed"] += 1

                # Send webhook
                if self.webhook.is_configured():
                    success = await self.webhook.send_overdue_alert(
                        user_id=user_id,
                        user_name=user_name,
                        tasks=tasks,
                    )
                    if success:
                        results["webhook_sent"] += 1
                    else:
                        results["webhook_failed"] += 1

            except Exception as e:
                logger.error(f"Error sending overdue alert for user {user_id}: {e}")

        return results

    async def send_task_assigned_notification(
        self,
        task: Dict,
        user_id: int,
        assigned_by: str = "System",
    ) -> bool:
        """
        Send notification when a task is assigned.

        Args:
            task: Task data
            user_id: ID of assigned user
            assigned_by: Who assigned the task

        Returns:
            True if at least one notification was sent
        """
        success = False

        try:
            user_info = await self._get_user_info(user_id)
            if not user_info:
                logger.warning(f"Could not find user info for user_id {user_id}")
                return False

            user_name = user_info.get("name", "User")
            user_email = user_info.get("email")

            # Send email
            if user_email and self.email.is_configured():
                email_sent = await self.email.send_task_assigned(
                    to_email=user_email,
                    user_name=user_name,
                    task=task,
                    assigned_by=assigned_by,
                )
                success = success or email_sent

            # Send webhook
            if self.webhook.is_configured():
                webhook_sent = await self.webhook.send_task_assigned(
                    task_id=task.get("id"),
                    task_name=task.get("name", ""),
                    user_id=user_id,
                    user_name=user_name,
                    assigned_by=assigned_by,
                )
                success = success or webhook_sent

        except Exception as e:
            logger.error(f"Error sending task assignment notification: {e}")

        return success

    async def send_manager_alerts(
        self,
        alert_type: str,
        message: str,
        data: Optional[Dict] = None,
    ) -> Dict[str, int]:
        """
        Send alerts to all configured managers.

        Args:
            alert_type: Type of alert
            message: Alert message
            data: Additional data

        Returns:
            Summary of sent notifications
        """
        results = {"email_sent": 0, "email_failed": 0, "webhook_sent": 0, "webhook_failed": 0}

        manager_emails = settings.manager_email_list

        # Send emails to managers
        for email in manager_emails:
            if self.email.is_configured():
                success = await self.email.send_manager_alert(
                    to_email=email,
                    alert_type=alert_type,
                    message=message,
                    data=data,
                )
                if success:
                    results["email_sent"] += 1
                else:
                    results["email_failed"] += 1

        # Send webhook
        if self.webhook.is_configured():
            success = await self.webhook.send_manager_alert(
                alert_type=alert_type,
                message=message,
                data=data,
            )
            if success:
                results["webhook_sent"] += 1
            else:
                results["webhook_failed"] += 1

        return results

    async def send_report_notifications(
        self,
        report_type: str,
        report_data: Dict,
        recipients: Optional[List[str]] = None,
    ) -> Dict[str, int]:
        """
        Send report to specified recipients.

        Args:
            report_type: Type of report (daily, weekly, monthly)
            report_data: Report data including metrics and summary
            recipients: Email addresses (defaults to manager emails)

        Returns:
            Summary of sent notifications
        """
        results = {"email_sent": 0, "email_failed": 0, "webhook_sent": 0, "webhook_failed": 0}

        recipients = recipients or settings.manager_email_list

        # Send emails
        for email in recipients:
            if self.email.is_configured():
                success = await self.email.send_report(
                    to_email=email,
                    report_type=report_type,
                    report_data=report_data,
                )
                if success:
                    results["email_sent"] += 1
                else:
                    results["email_failed"] += 1

        # Send webhook
        if self.webhook.is_configured():
            success = await self.webhook.send_report_ready(
                report_type=report_type,
                report_id=report_data.get("report_id", "unknown"),
                summary={
                    "metrics": report_data.get("metrics", {}),
                    "executive_summary": report_data.get("executive_summary", ""),
                },
            )
            if success:
                results["webhook_sent"] += 1
            else:
                results["webhook_failed"] += 1

        return results

    async def _get_user_info(self, user_id: int) -> Optional[Dict]:
        """Get user information from Odoo."""
        try:
            # Try to get employee by user_id
            employee = self.employee_service.get_employee_by_user_id(user_id)
            if employee:
                return {
                    "name": employee.get("name"),
                    "email": employee.get("work_email"),
                }

            # Fallback to user info
            user = self.employee_service.get_user_by_id(user_id)
            return {
                "name": user.get("name"),
                "email": user.get("email"),
            }

        except Exception as e:
            logger.error(f"Error getting user info for {user_id}: {e}")
            return None


# Singleton instance
_notification_manager: Optional[NotificationManager] = None


def get_notification_manager() -> NotificationManager:
    """Get the singleton notification manager instance."""
    global _notification_manager
    if _notification_manager is None:
        _notification_manager = NotificationManager()
    return _notification_manager
