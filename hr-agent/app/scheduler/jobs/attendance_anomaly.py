"""Attendance Anomaly Detection Job."""

import logging
from datetime import date

from app.config import settings

logger = logging.getLogger(__name__)


async def run_attendance_check():
    """Check for attendance anomalies."""
    logger.info("Running attendance anomaly check...")

    try:
        from app.services.odoo.attendance_service import get_attendance_service
        from app.services.ai.gemini_client import get_gemini_client

        attendance_service = get_attendance_service()
        gemini = get_gemini_client()

        # Get attendance data for the past 7 days
        attendance_data = attendance_service.get_attendance_for_analysis(days=7)

        if not attendance_data.get("records"):
            logger.info("No attendance records to analyze")
            return

        # Use AI if available, otherwise use basic detection
        if gemini.is_available():
            analysis = await gemini.detect_attendance_anomalies(attendance_data)
        else:
            analysis = attendance_service.detect_anomalies_basic(attendance_data)

        anomalies = analysis.get("anomalies", [])
        high_severity = [a for a in anomalies if a.get("severity") == "high"]

        logger.info(
            f"Anomaly check completed: {len(anomalies)} anomalies found, "
            f"{len(high_severity)} high severity"
        )

        # Send notifications for high severity anomalies
        if high_severity:
            logger.warning(f"High severity anomalies detected: {len(high_severity)}")
            # Would send notifications here

        logger.info("Attendance anomaly check completed")

    except Exception as e:
        logger.error(f"Attendance anomaly check failed: {e}")
