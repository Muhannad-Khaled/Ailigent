"""Overdue Task Monitoring Job."""

import logging
from datetime import datetime
from typing import Dict, List

from app.services.odoo.client import get_odoo_client
from app.services.odoo.task_service import OdooTaskService
from app.services.notifications.notification_manager import get_notification_manager

logger = logging.getLogger(__name__)


async def check_overdue_tasks():
    """
    Check for overdue tasks and send notifications.
    Runs every 15 minutes.
    """
    logger.info("Starting overdue task check")

    try:
        odoo_client = get_odoo_client()
        task_service = OdooTaskService(odoo_client)
        notification_manager = get_notification_manager()

        # Get overdue tasks
        overdue_tasks = task_service.get_overdue_tasks()

        if not overdue_tasks:
            logger.info("No overdue tasks found")
            return

        logger.info(f"Found {len(overdue_tasks)} overdue tasks")

        # Group by assignee
        tasks_by_user = _group_tasks_by_user(overdue_tasks)

        # Send notifications
        results = await notification_manager.send_overdue_alerts(tasks_by_user)
        logger.info(f"Overdue alerts sent: {results}")

        # Check for critically overdue tasks (>3 days)
        critical_tasks = []
        today = datetime.now().date()

        for task in overdue_tasks:
            deadline = task.get("date_deadline")
            if deadline:
                try:
                    deadline_date = datetime.fromisoformat(deadline).date()
                    days_overdue = (today - deadline_date).days
                    if days_overdue > 3:
                        task["days_overdue"] = days_overdue
                        critical_tasks.append(task)
                except (ValueError, TypeError):
                    pass

        # Alert managers for critical overdue tasks
        if critical_tasks:
            await notification_manager.send_manager_alerts(
                alert_type="critical_overdue",
                message=f"{len(critical_tasks)} tasks are critically overdue (>3 days)",
                data={
                    "critical_count": len(critical_tasks),
                    "tasks": [
                        {
                            "id": t["id"],
                            "name": t["name"],
                            "days_overdue": t.get("days_overdue"),
                        }
                        for t in critical_tasks[:10]
                    ],
                },
            )

        logger.info("Overdue task check completed")

    except Exception as e:
        logger.error(f"Error in overdue task check: {e}", exc_info=True)


def _group_tasks_by_user(tasks: List[Dict]) -> Dict[int, List[Dict]]:
    """Group tasks by assigned user."""
    grouped = {}
    for task in tasks:
        user_ids = task.get("user_ids", [])
        for user_id in user_ids:
            if user_id not in grouped:
                grouped[user_id] = []
            grouped[user_id].append(task)
    return grouped
