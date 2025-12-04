"""Email Notification Service."""

import logging
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Dict, List, Optional

import aiosmtplib

from app.config import settings

logger = logging.getLogger(__name__)


class EmailService:
    """Async email service using aiosmtplib."""

    def __init__(self):
        self.smtp_host = settings.SMTP_HOST
        self.smtp_port = settings.SMTP_PORT
        self.smtp_user = settings.SMTP_USER
        self.smtp_password = settings.SMTP_PASSWORD
        self.from_email = settings.FROM_EMAIL or settings.SMTP_USER

    def is_configured(self) -> bool:
        """Check if email service is properly configured."""
        return bool(
            self.smtp_host
            and self.smtp_port
            and self.smtp_user
            and self.smtp_password
        )

    async def send_email(
        self,
        to_email: str,
        subject: str,
        html_content: str,
        text_content: Optional[str] = None,
        cc: Optional[List[str]] = None,
        bcc: Optional[List[str]] = None,
    ) -> bool:
        """
        Send an email.

        Args:
            to_email: Recipient email address
            subject: Email subject
            html_content: HTML body content
            text_content: Plain text alternative
            cc: CC recipients
            bcc: BCC recipients

        Returns:
            True if sent successfully
        """
        if not self.is_configured():
            logger.warning("Email service not configured. Skipping email send.")
            return False

        try:
            message = MIMEMultipart("alternative")
            message["From"] = self.from_email
            message["To"] = to_email
            message["Subject"] = subject

            if cc:
                message["Cc"] = ", ".join(cc)

            if text_content:
                message.attach(MIMEText(text_content, "plain"))
            message.attach(MIMEText(html_content, "html"))

            recipients = [to_email]
            if cc:
                recipients.extend(cc)
            if bcc:
                recipients.extend(bcc)

            await aiosmtplib.send(
                message,
                hostname=self.smtp_host,
                port=self.smtp_port,
                username=self.smtp_user,
                password=self.smtp_password,
                start_tls=True,
            )

            logger.info(f"Email sent successfully to {to_email}")
            return True

        except Exception as e:
            logger.error(f"Failed to send email to {to_email}: {e}")
            return False

    async def send_overdue_alert(
        self,
        to_email: str,
        user_name: str,
        tasks: List[Dict],
    ) -> bool:
        """Send overdue task alert email."""
        task_list = ""
        for task in tasks[:10]:  # Limit to 10 tasks
            deadline = task.get("date_deadline", "No deadline")
            project = "N/A"
            if isinstance(task.get("project_id"), list) and len(task["project_id"]) > 1:
                project = task["project_id"][1]

            task_list += f"""
            <tr>
                <td style="padding: 8px; border-bottom: 1px solid #eee;">{task.get('name', 'Unnamed')}</td>
                <td style="padding: 8px; border-bottom: 1px solid #eee;">{project}</td>
                <td style="padding: 8px; border-bottom: 1px solid #eee;">{deadline}</td>
            </tr>
            """

        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background-color: #dc3545; color: white; padding: 20px; text-align: center; }}
                .content {{ padding: 20px; background-color: #f8f9fa; }}
                table {{ width: 100%; border-collapse: collapse; }}
                th {{ background-color: #343a40; color: white; padding: 10px; text-align: left; }}
                .footer {{ padding: 20px; text-align: center; font-size: 12px; color: #666; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h2>Action Required: Overdue Tasks</h2>
                </div>
                <div class="content">
                    <p>Hello {user_name},</p>
                    <p>You have <strong>{len(tasks)}</strong> overdue task(s) that require your attention:</p>
                    <table>
                        <thead>
                            <tr>
                                <th>Task</th>
                                <th>Project</th>
                                <th>Deadline</th>
                            </tr>
                        </thead>
                        <tbody>
                            {task_list}
                        </tbody>
                    </table>
                    <p style="margin-top: 20px;">Please review and update these tasks as soon as possible.</p>
                </div>
                <div class="footer">
                    <p>This is an automated message from Task Management Agent</p>
                </div>
            </div>
        </body>
        </html>
        """

        return await self.send_email(
            to_email=to_email,
            subject=f"Action Required: {len(tasks)} Overdue Task(s)",
            html_content=html_content,
        )

    async def send_task_assigned(
        self,
        to_email: str,
        user_name: str,
        task: Dict,
        assigned_by: str = "System",
    ) -> bool:
        """Send task assignment notification email."""
        project = "N/A"
        if isinstance(task.get("project_id"), list) and len(task["project_id"]) > 1:
            project = task["project_id"][1]

        priority_map = {"0": "Low", "1": "Normal", "2": "High", "3": "Urgent"}
        priority = priority_map.get(task.get("priority", "1"), "Normal")

        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background-color: #007bff; color: white; padding: 20px; text-align: center; }}
                .content {{ padding: 20px; background-color: #f8f9fa; }}
                .task-details {{ background-color: white; padding: 15px; border-radius: 5px; margin: 15px 0; }}
                .label {{ font-weight: bold; color: #495057; }}
                .footer {{ padding: 20px; text-align: center; font-size: 12px; color: #666; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h2>New Task Assigned</h2>
                </div>
                <div class="content">
                    <p>Hello {user_name},</p>
                    <p>A new task has been assigned to you by <strong>{assigned_by}</strong>:</p>
                    <div class="task-details">
                        <p><span class="label">Task:</span> {task.get('name', 'Unnamed')}</p>
                        <p><span class="label">Project:</span> {project}</p>
                        <p><span class="label">Priority:</span> {priority}</p>
                        <p><span class="label">Deadline:</span> {task.get('date_deadline', 'No deadline')}</p>
                        <p><span class="label">Estimated Hours:</span> {task.get('planned_hours', 'Not specified')}</p>
                    </div>
                    <p>Please review the task details and start working on it.</p>
                </div>
                <div class="footer">
                    <p>This is an automated message from Task Management Agent</p>
                </div>
            </div>
        </body>
        </html>
        """

        return await self.send_email(
            to_email=to_email,
            subject=f"New Task Assigned: {task.get('name', 'Unnamed')}",
            html_content=html_content,
        )

    async def send_report(
        self,
        to_email: str,
        report_type: str,
        report_data: Dict,
    ) -> bool:
        """Send productivity report email."""
        metrics = report_data.get("metrics", {})
        summary = report_data.get("executive_summary", "No summary available.")
        recommendations = report_data.get("recommendations", [])

        rec_html = ""
        for rec in recommendations[:5]:
            rec_html += f"<li>{rec}</li>"

        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background-color: #28a745; color: white; padding: 20px; text-align: center; }}
                .content {{ padding: 20px; background-color: #f8f9fa; }}
                .metrics {{ display: flex; justify-content: space-around; flex-wrap: wrap; margin: 20px 0; }}
                .metric {{ text-align: center; padding: 15px; background-color: white; border-radius: 5px; margin: 5px; min-width: 120px; }}
                .metric-value {{ font-size: 24px; font-weight: bold; color: #007bff; }}
                .metric-label {{ font-size: 12px; color: #666; }}
                .footer {{ padding: 20px; text-align: center; font-size: 12px; color: #666; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h2>{report_type.title()} Productivity Report</h2>
                    <p>{metrics.get('period_start', '')} - {metrics.get('period_end', '')}</p>
                </div>
                <div class="content">
                    <h3>Executive Summary</h3>
                    <p>{summary}</p>

                    <h3>Key Metrics</h3>
                    <div class="metrics">
                        <div class="metric">
                            <div class="metric-value">{metrics.get('completion_rate', 0):.1f}%</div>
                            <div class="metric-label">Completion Rate</div>
                        </div>
                        <div class="metric">
                            <div class="metric-value">{metrics.get('on_time_rate', 0):.1f}%</div>
                            <div class="metric-label">On-Time Rate</div>
                        </div>
                        <div class="metric">
                            <div class="metric-value">{metrics.get('completed', 0)}</div>
                            <div class="metric-label">Completed</div>
                        </div>
                        <div class="metric">
                            <div class="metric-value">{metrics.get('overdue', 0)}</div>
                            <div class="metric-label">Overdue</div>
                        </div>
                    </div>

                    <h3>Recommendations</h3>
                    <ul>
                        {rec_html if rec_html else '<li>No specific recommendations</li>'}
                    </ul>
                </div>
                <div class="footer">
                    <p>This is an automated report from Task Management Agent</p>
                </div>
            </div>
        </body>
        </html>
        """

        return await self.send_email(
            to_email=to_email,
            subject=f"{report_type.title()} Productivity Report",
            html_content=html_content,
        )

    async def send_manager_alert(
        self,
        to_email: str,
        alert_type: str,
        message: str,
        data: Optional[Dict] = None,
    ) -> bool:
        """Send alert to managers."""
        alert_colors = {
            "critical_overdue": "#dc3545",
            "workload_imbalance": "#ffc107",
            "bottleneck_detected": "#fd7e14",
            "default": "#17a2b8",
        }

        color = alert_colors.get(alert_type, alert_colors["default"])

        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background-color: {color}; color: white; padding: 20px; text-align: center; }}
                .content {{ padding: 20px; background-color: #f8f9fa; }}
                .footer {{ padding: 20px; text-align: center; font-size: 12px; color: #666; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h2>Manager Alert: {alert_type.replace('_', ' ').title()}</h2>
                </div>
                <div class="content">
                    <p>{message}</p>
                    {f'<pre>{str(data)}</pre>' if data else ''}
                </div>
                <div class="footer">
                    <p>This is an automated alert from Task Management Agent</p>
                </div>
            </div>
        </body>
        </html>
        """

        return await self.send_email(
            to_email=to_email,
            subject=f"Manager Alert: {alert_type.replace('_', ' ').title()}",
            html_content=html_content,
        )
