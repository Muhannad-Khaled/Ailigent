"""Scheduled Report Generation Jobs."""

import logging
from datetime import date, timedelta

from app.services.odoo.client import get_odoo_client
from app.services.odoo.task_service import OdooTaskService
from app.services.odoo.employee_service import OdooEmployeeService
from app.services.ai.gemini_client import get_gemini_client
from app.services.ai.report_generator import AIReportGenerator
from app.services.notifications.notification_manager import get_notification_manager

logger = logging.getLogger(__name__)


async def generate_daily_report():
    """
    Generate and send daily productivity report.
    Runs at 6:00 AM every day.
    """
    logger.info("Starting daily report generation")

    try:
        odoo_client = get_odoo_client()
        task_service = OdooTaskService(odoo_client)
        employee_service = OdooEmployeeService(odoo_client)
        report_generator = AIReportGenerator(get_gemini_client())
        notification_manager = get_notification_manager()

        # Get metrics for yesterday
        end_date = date.today()
        start_date = end_date - timedelta(days=1)

        completion_metrics = task_service.get_completion_rates(
            start_date=start_date,
            end_date=end_date,
        )

        stage_metrics = task_service.get_stage_statistics()
        workload_summary = employee_service.get_team_workload_summary()

        # Generate AI-enhanced report
        report = await report_generator.generate_productivity_report(
            completion_metrics=completion_metrics,
            stage_metrics=stage_metrics,
            employee_performance=workload_summary.get("employees", []),
            report_type="daily",
        )

        # Send report notifications
        results = await notification_manager.send_report_notifications(
            report_type="daily",
            report_data=report,
        )

        logger.info(f"Daily report generated and sent: {results}")

    except Exception as e:
        logger.error(f"Error generating daily report: {e}", exc_info=True)


async def generate_weekly_report():
    """
    Generate and send weekly productivity report.
    Runs at 7:00 AM every Monday.
    """
    logger.info("Starting weekly report generation")

    try:
        odoo_client = get_odoo_client()
        task_service = OdooTaskService(odoo_client)
        employee_service = OdooEmployeeService(odoo_client)
        report_generator = AIReportGenerator(get_gemini_client())
        notification_manager = get_notification_manager()

        # Get metrics for last 7 days
        end_date = date.today()
        start_date = end_date - timedelta(days=7)

        completion_metrics = task_service.get_completion_rates(
            start_date=start_date,
            end_date=end_date,
        )

        stage_metrics = task_service.get_stage_statistics()
        workload_summary = employee_service.get_team_workload_summary()

        # Generate AI-enhanced report
        report = await report_generator.generate_productivity_report(
            completion_metrics=completion_metrics,
            stage_metrics=stage_metrics,
            employee_performance=workload_summary.get("employees", []),
            report_type="weekly",
        )

        # Send report notifications
        results = await notification_manager.send_report_notifications(
            report_type="weekly",
            report_data=report,
        )

        logger.info(f"Weekly report generated and sent: {results}")

    except Exception as e:
        logger.error(f"Error generating weekly report: {e}", exc_info=True)


async def generate_monthly_report():
    """
    Generate and send monthly productivity report.
    Can be triggered manually or scheduled for 1st of each month.
    """
    logger.info("Starting monthly report generation")

    try:
        odoo_client = get_odoo_client()
        task_service = OdooTaskService(odoo_client)
        employee_service = OdooEmployeeService(odoo_client)
        report_generator = AIReportGenerator(get_gemini_client())
        notification_manager = get_notification_manager()

        # Get metrics for last 30 days
        end_date = date.today()
        start_date = end_date - timedelta(days=30)

        completion_metrics = task_service.get_completion_rates(
            start_date=start_date,
            end_date=end_date,
        )

        stage_metrics = task_service.get_stage_statistics()
        workload_summary = employee_service.get_team_workload_summary()

        # Generate AI-enhanced report
        report = await report_generator.generate_productivity_report(
            completion_metrics=completion_metrics,
            stage_metrics=stage_metrics,
            employee_performance=workload_summary.get("employees", []),
            report_type="monthly",
        )

        # Send report notifications
        results = await notification_manager.send_report_notifications(
            report_type="monthly",
            report_data=report,
        )

        logger.info(f"Monthly report generated and sent: {results}")

    except Exception as e:
        logger.error(f"Error generating monthly report: {e}", exc_info=True)
