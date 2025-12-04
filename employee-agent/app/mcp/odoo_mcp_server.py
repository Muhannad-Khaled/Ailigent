"""
Odoo MCP Server - Model Context Protocol server for Odoo ERP integration.

This module provides MCP tools that allow AI models (like Gemini) to directly
interact with Odoo ERP system for employee-related operations.
"""

from typing import Any, Optional
from datetime import datetime
from mcp.server.fastmcp import FastMCP
from loguru import logger

from app.services.odoo_service import OdooService


def create_odoo_mcp_server(odoo_service: OdooService) -> FastMCP:
    """
    Create and configure an MCP server with Odoo tools.

    Args:
        odoo_service: Connected OdooService instance

    Returns:
        Configured FastMCP server
    """

    mcp = FastMCP(
        "Odoo Employee Agent",
        instructions="""You are an HR assistant with access to Odoo ERP.
        Use these tools to help employees with leave balance, payroll, attendance,
        tasks, and company policies. Always be helpful and respond in the user's language."""
    )

    # ==================== Employee Tools ====================

    @mcp.tool()
    async def get_employee_info(employee_id: int) -> dict[str, Any]:
        """
        Get detailed information about an employee.

        Args:
            employee_id: The Odoo employee ID

        Returns:
            Employee details including name, email, department, job title, manager
        """
        try:
            employee = await odoo_service.get_employee_by_id(employee_id)
            if employee:
                return {
                    "success": True,
                    "employee": {
                        "id": employee.id,
                        "name": employee.name,
                        "email": employee.email,
                        "job_title": employee.job_title,
                        "department": employee.department,
                        "manager": employee.manager_name,
                        "work_phone": employee.work_phone,
                        "mobile_phone": employee.mobile_phone,
                    }
                }
            return {"success": False, "error": "Employee not found"}
        except Exception as e:
            logger.error(f"MCP get_employee_info error: {e}")
            return {"success": False, "error": str(e)}

    @mcp.tool()
    async def find_employee_by_email(email: str) -> dict[str, Any]:
        """
        Find an employee by their work email address.

        Args:
            email: Employee's work email address

        Returns:
            Employee details if found
        """
        try:
            employee = await odoo_service.find_employee_by_email(email)
            if employee:
                return {
                    "success": True,
                    "employee": {
                        "id": employee.id,
                        "name": employee.name,
                        "email": employee.email,
                        "department": employee.department,
                    }
                }
            return {"success": False, "error": "No employee found with this email"}
        except Exception as e:
            logger.error(f"MCP find_employee_by_email error: {e}")
            return {"success": False, "error": str(e)}

    # ==================== Leave Management Tools ====================

    @mcp.tool()
    async def get_leave_balance(employee_id: int) -> dict[str, Any]:
        """
        Get the leave balance for an employee showing all leave types.

        Args:
            employee_id: The Odoo employee ID

        Returns:
            List of leave balances with allocated, taken, and remaining days
        """
        try:
            balances = await odoo_service.get_leave_balance(employee_id)
            return {
                "success": True,
                "balances": [
                    {
                        "leave_type": b.leave_type,
                        "allocated": b.allocated,
                        "taken": b.taken,
                        "remaining": b.remaining,
                    }
                    for b in balances
                ]
            }
        except Exception as e:
            logger.error(f"MCP get_leave_balance error: {e}")
            return {"success": False, "error": str(e)}

    @mcp.tool()
    async def get_leave_requests(
        employee_id: int,
        state: Optional[str] = None
    ) -> dict[str, Any]:
        """
        Get leave requests for an employee.

        Args:
            employee_id: The Odoo employee ID
            state: Optional filter by state (draft, confirm, validate, refuse)

        Returns:
            List of leave requests with details
        """
        try:
            requests = await odoo_service.get_leave_requests(employee_id, state)
            return {
                "success": True,
                "requests": [
                    {
                        "id": r.id,
                        "leave_type": r.leave_type,
                        "date_from": r.date_from,
                        "date_to": r.date_to,
                        "days": r.number_of_days,
                        "state": r.state,
                        "reason": r.reason,
                    }
                    for r in requests
                ]
            }
        except Exception as e:
            logger.error(f"MCP get_leave_requests error: {e}")
            return {"success": False, "error": str(e)}

    @mcp.tool()
    async def create_leave_request(
        employee_id: int,
        leave_type_id: int,
        date_from: str,
        date_to: str,
        reason: str = ""
    ) -> dict[str, Any]:
        """
        Create a new leave request for an employee.

        Args:
            employee_id: The Odoo employee ID
            leave_type_id: The leave type ID from Odoo
            date_from: Start date in YYYY-MM-DD format
            date_to: End date in YYYY-MM-DD format
            reason: Optional reason for the leave

        Returns:
            Created leave request ID
        """
        try:
            leave_id = await odoo_service.create_leave_request(
                employee_id=employee_id,
                leave_type_id=leave_type_id,
                date_from=date_from,
                date_to=date_to,
                reason=reason,
            )
            if leave_id:
                return {"success": True, "leave_id": leave_id}
            return {"success": False, "error": "Failed to create leave request"}
        except Exception as e:
            logger.error(f"MCP create_leave_request error: {e}")
            return {"success": False, "error": str(e)}

    # ==================== Payroll Tools ====================

    @mcp.tool()
    async def get_payslips(
        employee_id: int,
        limit: int = 6
    ) -> dict[str, Any]:
        """
        Get recent payslips for an employee.

        Args:
            employee_id: The Odoo employee ID
            limit: Maximum number of payslips to return (default 6)

        Returns:
            List of payslip summaries
        """
        try:
            payslips = await odoo_service.get_payslips(employee_id, limit)
            return {
                "success": True,
                "payslips": [
                    {
                        "id": p.id,
                        "name": p.name,
                        "period": f"{p.date_from} to {p.date_to}",
                        "state": p.state,
                        "net_wage": p.net_wage,
                        "gross_wage": p.gross_wage,
                    }
                    for p in payslips
                ]
            }
        except Exception as e:
            logger.error(f"MCP get_payslips error: {e}")
            return {"success": False, "error": str(e)}

    # ==================== Attendance Tools ====================

    @mcp.tool()
    async def get_attendance_summary(
        employee_id: int,
        month: Optional[int] = None,
        year: Optional[int] = None
    ) -> dict[str, Any]:
        """
        Get attendance summary for an employee for a specific month.

        Args:
            employee_id: The Odoo employee ID
            month: Month number (1-12), defaults to current month
            year: Year, defaults to current year

        Returns:
            Attendance summary with total days and hours
        """
        try:
            summary = await odoo_service.get_attendance_summary(
                employee_id, month, year
            )
            return {
                "success": True,
                "summary": {
                    "month": summary.get("month"),
                    "year": summary.get("year"),
                    "total_days": summary.get("total_days", 0),
                    "total_hours": summary.get("total_hours", 0),
                }
            }
        except Exception as e:
            logger.error(f"MCP get_attendance_summary error: {e}")
            return {"success": False, "error": str(e)}

    # ==================== Task Management Tools ====================

    @mcp.tool()
    async def get_employee_tasks(employee_id: int) -> dict[str, Any]:
        """
        Get tasks assigned to an employee.

        Args:
            employee_id: The Odoo employee ID

        Returns:
            List of tasks with details
        """
        try:
            tasks = await odoo_service.get_employee_tasks(employee_id)
            return {
                "success": True,
                "tasks": [
                    {
                        "id": t.get("id"),
                        "name": t.get("name"),
                        "description": t.get("description"),
                        "deadline": t.get("date_deadline"),
                        "priority": t.get("priority"),
                        "stage": t.get("stage_id", [None, ""])[1] if t.get("stage_id") else None,
                    }
                    for t in tasks
                ]
            }
        except Exception as e:
            logger.error(f"MCP get_employee_tasks error: {e}")
            return {"success": False, "error": str(e)}

    @mcp.tool()
    async def create_task(
        employee_id: int,
        name: str,
        description: str = "",
        due_date: Optional[str] = None
    ) -> dict[str, Any]:
        """
        Create a new task for an employee.

        Args:
            employee_id: The Odoo employee ID to assign the task to
            name: Task name/title
            description: Task description
            due_date: Optional due date in YYYY-MM-DD format

        Returns:
            Created task ID
        """
        try:
            task_id = await odoo_service.create_task(
                employee_id=employee_id,
                name=name,
                description=description,
                due_date=due_date,
            )
            if task_id:
                return {"success": True, "task_id": task_id}
            return {"success": False, "error": "Failed to create task"}
        except Exception as e:
            logger.error(f"MCP create_task error: {e}")
            return {"success": False, "error": str(e)}

    # ==================== Policy Tools ====================

    @mcp.tool()
    async def get_company_policies() -> dict[str, Any]:
        """
        Get list of company policies and documents.

        Returns:
            List of available policies
        """
        try:
            policies = await odoo_service.get_company_policies()
            return {
                "success": True,
                "policies": [
                    {
                        "id": p.get("id"),
                        "name": p.get("name"),
                        "description": p.get("description"),
                        "created": p.get("create_date"),
                    }
                    for p in policies
                ]
            }
        except Exception as e:
            logger.error(f"MCP get_company_policies error: {e}")
            return {"success": False, "error": str(e)}

    # ==================== Telegram Link Tools ====================

    @mcp.tool()
    async def check_telegram_link(telegram_id: int) -> dict[str, Any]:
        """
        Check if a Telegram user is linked to an Odoo employee.

        Args:
            telegram_id: Telegram user ID

        Returns:
            Link status and employee ID if linked
        """
        try:
            employee_id = await odoo_service.get_employee_by_telegram(telegram_id)
            if employee_id:
                employee = await odoo_service.get_employee_by_id(employee_id)
                return {
                    "success": True,
                    "linked": True,
                    "employee_id": employee_id,
                    "employee_name": employee.name if employee else None,
                }
            return {"success": True, "linked": False}
        except Exception as e:
            logger.error(f"MCP check_telegram_link error: {e}")
            return {"success": False, "error": str(e)}

    @mcp.tool()
    async def link_telegram_account(
        telegram_id: int,
        employee_id: int,
        telegram_username: Optional[str] = None
    ) -> dict[str, Any]:
        """
        Link a Telegram account to an Odoo employee.

        Args:
            telegram_id: Telegram user ID
            employee_id: Odoo employee ID
            telegram_username: Optional Telegram username

        Returns:
            Success status
        """
        try:
            success = await odoo_service.save_telegram_link(
                telegram_id=telegram_id,
                employee_id=employee_id,
                telegram_username=telegram_username,
            )
            return {"success": success}
        except Exception as e:
            logger.error(f"MCP link_telegram_account error: {e}")
            return {"success": False, "error": str(e)}

    @mcp.tool()
    async def unlink_telegram_account(telegram_id: int) -> dict[str, Any]:
        """
        Remove the link between a Telegram account and Odoo employee.

        Args:
            telegram_id: Telegram user ID

        Returns:
            Success status
        """
        try:
            success = await odoo_service.remove_telegram_link(telegram_id)
            return {"success": success}
        except Exception as e:
            logger.error(f"MCP unlink_telegram_account error: {e}")
            return {"success": False, "error": str(e)}

    # ==================== Resources ====================

    @mcp.resource("employee://{employee_id}/summary")
    async def get_employee_summary(employee_id: int) -> str:
        """Get a complete summary of an employee's current status."""
        try:
            emp_id = int(employee_id)
            employee = await odoo_service.get_employee_by_id(emp_id)
            if not employee:
                return "Employee not found"

            leave_balance = await odoo_service.get_leave_balance(emp_id)
            attendance = await odoo_service.get_attendance_summary(emp_id)
            tasks = await odoo_service.get_employee_tasks(emp_id)

            summary = f"""
# Employee Summary: {employee.name}

## Profile
- **Department:** {employee.department or 'N/A'}
- **Job Title:** {employee.job_title or 'N/A'}
- **Manager:** {employee.manager_name or 'N/A'}
- **Email:** {employee.email or 'N/A'}

## Leave Balance
"""
            for b in leave_balance:
                summary += f"- {b.leave_type}: {b.remaining}/{b.allocated} days remaining\n"

            summary += f"""
## Attendance (This Month)
- **Total Days:** {attendance.get('total_days', 0)}
- **Total Hours:** {attendance.get('total_hours', 0)}

## Active Tasks
"""
            if tasks:
                for t in tasks[:5]:
                    summary += f"- {t.get('name', 'Unnamed')}\n"
            else:
                summary += "- No active tasks\n"

            return summary

        except Exception as e:
            logger.error(f"MCP get_employee_summary error: {e}")
            return f"Error generating summary: {e}"

    @mcp.resource("policies://list")
    async def get_policies_list() -> str:
        """Get list of all company policies."""
        try:
            policies = await odoo_service.get_company_policies()
            if not policies:
                return "No policies found"

            result = "# Company Policies\n\n"
            for p in policies:
                result += f"- **{p.get('name', 'Unnamed')}**\n"
                if p.get('description'):
                    result += f"  {p.get('description')}\n"

            return result
        except Exception as e:
            logger.error(f"MCP get_policies_list error: {e}")
            return f"Error fetching policies: {e}"

    # ==================== Prompts ====================

    @mcp.prompt()
    def daily_summary_prompt(employee_name: str, language: str = "en") -> str:
        """Generate a prompt for creating a daily work summary."""
        if language == "ar":
            return f"""قم بإنشاء ملخص عمل يومي للموظف {employee_name}.

اشمل المعلومات التالية:
1. ساعات العمل اليوم
2. المهام المكتملة
3. المهام المعلقة
4. أي ملاحظات مهمة

اكتب الملخص بشكل مهني ومختصر باللغة العربية."""
        else:
            return f"""Generate a daily work summary for employee {employee_name}.

Include the following information:
1. Work hours today
2. Completed tasks
3. Pending tasks
4. Any important notes

Write the summary in a professional and concise manner."""

    @mcp.prompt()
    def leave_request_prompt(
        employee_name: str,
        leave_type: str,
        date_from: str,
        date_to: str
    ) -> str:
        """Generate a prompt for processing a leave request."""
        return f"""Process a leave request with the following details:

- **Employee:** {employee_name}
- **Leave Type:** {leave_type}
- **From:** {date_from}
- **To:** {date_to}

Please check if the employee has sufficient leave balance and confirm the request."""

    logger.info("Odoo MCP Server created with all tools and resources")
    return mcp
