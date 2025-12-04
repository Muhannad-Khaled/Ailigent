"""Weekly Report Generation Job."""

import logging
from datetime import date, timedelta

from app.config import settings

logger = logging.getLogger(__name__)


async def run_weekly_report():
    """Generate and send weekly HR report."""
    logger.info("Running weekly HR report generation...")

    try:
        from app.services.odoo.employee_service import get_employee_service
        from app.services.ai.gemini_client import get_gemini_client

        employee_service = get_employee_service()
        gemini = get_gemini_client()

        # Generate reports
        headcount = employee_service.get_headcount_report()
        turnover = employee_service.get_turnover_report()

        # Compile weekly summary
        summary = {
            "report_date": date.today(),
            "period": "weekly",
            "headcount": headcount,
            "turnover": turnover,
        }

        # Generate AI insights if available
        if gemini.is_available():
            try:
                insights = await gemini.generate_hr_insights(summary)
                summary["ai_insights"] = insights
                logger.info("AI insights generated successfully")
            except Exception as e:
                logger.warning(f"Failed to generate AI insights: {e}")

        # Store report
        report = employee_service.generate_custom_report(
            report_type="headcount",
            include_ai_insights=gemini.is_available(),
        )

        logger.info(f"Weekly report generated: {report.get('id')}")

        # Send to HR managers
        hr_emails = settings.hr_manager_email_list
        if hr_emails:
            logger.info(f"Would send report to: {', '.join(hr_emails)}")
            # Would integrate with notification service here

        logger.info("Weekly HR report job completed")

    except Exception as e:
        logger.error(f"Weekly HR report job failed: {e}")
