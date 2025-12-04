"""Workload Balance Monitoring Job."""

import logging

from app.services.odoo.client import get_odoo_client
from app.services.odoo.task_service import OdooTaskService
from app.services.odoo.employee_service import OdooEmployeeService
from app.services.ai.gemini_client import get_gemini_client
from app.services.ai.workload_optimizer import WorkloadOptimizer
from app.services.ai.bottleneck_detector import BottleneckDetector
from app.services.notifications.notification_manager import get_notification_manager
from app.core.constants import WORKLOAD_OVERLOADED_THRESHOLD

logger = logging.getLogger(__name__)


async def check_workload_balance():
    """
    Check workload distribution and alert if imbalanced.
    Runs every hour.
    """
    logger.info("Starting workload balance check")

    try:
        odoo_client = get_odoo_client()
        task_service = OdooTaskService(odoo_client)
        employee_service = OdooEmployeeService(odoo_client)
        optimizer = WorkloadOptimizer(get_gemini_client())
        notification_manager = get_notification_manager()

        # Get current workload
        workload_summary = employee_service.get_team_workload_summary()
        employees = workload_summary.get("employees", [])

        # Get pending tasks
        tasks = task_service.get_all_tasks(limit=500, include_closed=False)

        # Analyze workload
        analysis = await optimizer.analyze_team_workload(
            employees=employees,
            tasks=tasks,
        )

        balance_score = analysis.get("balance_score", 100)
        overloaded = analysis.get("overloaded_employees", [])
        underutilized = analysis.get("underutilized_employees", [])

        logger.info(
            f"Workload analysis: balance_score={balance_score}, "
            f"overloaded={len(overloaded)}, underutilized={len(underutilized)}"
        )

        # Alert if significant imbalance detected
        if balance_score < 50 or len(overloaded) > 2:
            await notification_manager.send_manager_alerts(
                alert_type="workload_imbalance",
                message=f"Workload imbalance detected (score: {balance_score}). "
                f"{len(overloaded)} employee(s) overloaded, "
                f"{len(underutilized)} underutilized.",
                data={
                    "balance_score": balance_score,
                    "overloaded_employees": [
                        {"name": e.get("name"), "utilization": e.get("utilization")}
                        for e in overloaded
                    ],
                    "recommendations": analysis.get("recommendations", []),
                },
            )
            logger.info("Sent workload imbalance alert to managers")

        # Check for rebalancing suggestions
        rebalancing = await optimizer.suggest_rebalancing(workload_summary)

        if rebalancing.get("rebalancing_needed"):
            logger.info(
                f"Rebalancing suggested: {len(rebalancing.get('suggestions', []))} transfers"
            )

        logger.info("Workload balance check completed")

    except Exception as e:
        logger.error(f"Error in workload balance check: {e}", exc_info=True)


async def check_bottlenecks():
    """
    Check for workflow bottlenecks.
    Can be scheduled or run on-demand.
    """
    logger.info("Starting bottleneck analysis")

    try:
        odoo_client = get_odoo_client()
        task_service = OdooTaskService(odoo_client)
        employee_service = OdooEmployeeService(odoo_client)
        detector = BottleneckDetector(get_gemini_client())
        notification_manager = get_notification_manager()

        # Get data for analysis
        tasks = task_service.get_all_tasks(limit=1000, include_closed=False)
        stages = task_service.get_stage_statistics()
        workload = employee_service.get_team_workload_summary()

        # Detect bottlenecks
        analysis = await detector.detect_bottlenecks(
            tasks=tasks,
            employees=workload.get("employees", []),
            stages=stages,
        )

        bottlenecks = analysis.get("bottlenecks", [])
        critical_count = analysis.get("critical_count", 0)
        high_count = analysis.get("high_count", 0)

        logger.info(
            f"Bottleneck analysis: {len(bottlenecks)} found, "
            f"{critical_count} critical, {high_count} high severity"
        )

        # Alert managers for critical/high severity bottlenecks
        if critical_count > 0 or high_count > 1:
            await notification_manager.send_manager_alerts(
                alert_type="bottleneck_detected",
                message=f"Bottlenecks detected: {critical_count} critical, {high_count} high severity",
                data={
                    "bottlenecks": bottlenecks[:5],  # Top 5 bottlenecks
                    "priority_actions": analysis.get("priority_actions", []),
                    "summary": analysis.get("summary", ""),
                },
            )
            logger.info("Sent bottleneck alert to managers")

        logger.info("Bottleneck analysis completed")

    except Exception as e:
        logger.error(f"Error in bottleneck analysis: {e}", exc_info=True)
