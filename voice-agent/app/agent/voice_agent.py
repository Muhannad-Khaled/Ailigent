"""LiveKit Voice Agent for Ailigent Suite."""
import asyncio
from typing import Optional
from loguru import logger

from livekit import rtc
from livekit.agents import (
    AutoSubscribe,
    JobContext,
    WorkerOptions,
    cli,
    llm,
)
from livekit.agents.voice import Agent
from livekit.plugins import google, silero

from app.config import settings
from app.services.odoo_service import get_odoo_service
from app.services.http_clients import get_task_client, get_hr_client, get_contract_client
from app.utils.language import detect_language, get_greeting
from app.utils.prompts import get_system_prompt


class AiligentVoiceAgent:
    """Voice AI Agent for Ailigent Suite with function calling."""

    def __init__(self):
        self.odoo = get_odoo_service()
        self.task_client = get_task_client()
        self.hr_client = get_hr_client()
        self.contract_client = get_contract_client()
        self.language = settings.DEFAULT_LANGUAGE

    def get_tools(self) -> list[llm.FunctionTool]:
        """Get all function tools for the agent."""
        return [
            # Employee self-service tools
            llm.FunctionTool(
                name="get_all_employees",
                description="Get a list of all employees in the company with their basic information",
                parameters={
                    "type": "object",
                    "properties": {
                        "limit": {
                            "type": "integer",
                            "description": "Maximum number of employees to return",
                            "default": 50,
                        }
                    },
                },
                callable=self._get_all_employees,
            ),
            llm.FunctionTool(
                name="get_employee_info",
                description="Get detailed information about a specific employee by their ID",
                parameters={
                    "type": "object",
                    "properties": {
                        "employee_id": {
                            "type": "integer",
                            "description": "The employee ID",
                        }
                    },
                    "required": ["employee_id"],
                },
                callable=self._get_employee_info,
            ),
            llm.FunctionTool(
                name="get_leave_balance",
                description="Get leave balance for an employee showing all leave types and remaining days",
                parameters={
                    "type": "object",
                    "properties": {
                        "employee_id": {
                            "type": "integer",
                            "description": "The employee ID",
                        }
                    },
                    "required": ["employee_id"],
                },
                callable=self._get_leave_balance,
            ),
            llm.FunctionTool(
                name="get_leave_requests",
                description="Get leave requests for an employee",
                parameters={
                    "type": "object",
                    "properties": {
                        "employee_id": {
                            "type": "integer",
                            "description": "The employee ID",
                        },
                        "state": {
                            "type": "string",
                            "description": "Filter by state: draft, confirm, validate, refuse",
                        }
                    },
                    "required": ["employee_id"],
                },
                callable=self._get_leave_requests,
            ),
            llm.FunctionTool(
                name="get_payslips",
                description="Get recent payslips for an employee",
                parameters={
                    "type": "object",
                    "properties": {
                        "employee_id": {
                            "type": "integer",
                            "description": "The employee ID",
                        },
                        "limit": {
                            "type": "integer",
                            "description": "Number of payslips to return",
                            "default": 3,
                        }
                    },
                    "required": ["employee_id"],
                },
                callable=self._get_payslips,
            ),
            llm.FunctionTool(
                name="get_attendance",
                description="Get attendance summary for an employee",
                parameters={
                    "type": "object",
                    "properties": {
                        "employee_id": {
                            "type": "integer",
                            "description": "The employee ID",
                        },
                        "month": {
                            "type": "integer",
                            "description": "Month number (1-12)",
                        },
                        "year": {
                            "type": "integer",
                            "description": "Year",
                        }
                    },
                    "required": ["employee_id"],
                },
                callable=self._get_attendance,
            ),
            llm.FunctionTool(
                name="get_employee_tasks",
                description="Get tasks assigned to an employee",
                parameters={
                    "type": "object",
                    "properties": {
                        "employee_id": {
                            "type": "integer",
                            "description": "The employee ID",
                        }
                    },
                    "required": ["employee_id"],
                },
                callable=self._get_employee_tasks,
            ),
            # Team/Manager tools
            llm.FunctionTool(
                name="get_all_tasks",
                description="Get all tasks in the system (team view)",
                parameters={
                    "type": "object",
                    "properties": {
                        "limit": {
                            "type": "integer",
                            "description": "Maximum number of tasks",
                            "default": 50,
                        }
                    },
                },
                callable=self._get_all_tasks,
            ),
            llm.FunctionTool(
                name="get_overdue_tasks",
                description="Get all overdue tasks that need attention",
                parameters={
                    "type": "object",
                    "properties": {},
                },
                callable=self._get_overdue_tasks,
            ),
            llm.FunctionTool(
                name="get_workload_analysis",
                description="Get team workload analysis from task management service",
                parameters={
                    "type": "object",
                    "properties": {},
                },
                callable=self._get_workload_analysis,
            ),
            # HR Management tools
            llm.FunctionTool(
                name="get_pending_leave_approvals",
                description="Get leave requests pending approval (for managers)",
                parameters={
                    "type": "object",
                    "properties": {},
                },
                callable=self._get_pending_leave_approvals,
            ),
            llm.FunctionTool(
                name="get_hr_headcount_report",
                description="Get headcount report with department breakdown",
                parameters={
                    "type": "object",
                    "properties": {},
                },
                callable=self._get_hr_headcount_report,
            ),
            llm.FunctionTool(
                name="get_hr_insights",
                description="Get AI-powered HR insights and recommendations",
                parameters={
                    "type": "object",
                    "properties": {},
                },
                callable=self._get_hr_insights,
            ),
            # Contract tools
            llm.FunctionTool(
                name="get_expiring_contracts",
                description="Get contracts that are expiring soon",
                parameters={
                    "type": "object",
                    "properties": {
                        "days": {
                            "type": "integer",
                            "description": "Number of days to look ahead",
                            "default": 30,
                        }
                    },
                },
                callable=self._get_expiring_contracts,
            ),
            llm.FunctionTool(
                name="get_contract_compliance_report",
                description="Get contract compliance report",
                parameters={
                    "type": "object",
                    "properties": {},
                },
                callable=self._get_contract_compliance_report,
            ),
            # Utility
            llm.FunctionTool(
                name="switch_language",
                description="Switch the conversation language between English and Arabic",
                parameters={
                    "type": "object",
                    "properties": {
                        "language": {
                            "type": "string",
                            "description": "Target language: 'en' for English, 'ar' for Arabic",
                            "enum": ["en", "ar"],
                        }
                    },
                    "required": ["language"],
                },
                callable=self._switch_language,
            ),
        ]

    # Tool implementations
    async def _get_all_employees(self, limit: int = 50) -> str:
        employees = self.odoo.get_all_employees(limit)
        if not employees:
            return "No employees found."
        result = f"Found {len(employees)} employees:\n"
        for emp in employees[:10]:  # Limit voice output
            result += f"- {emp['name']} (ID: {emp['id']}) - {emp['job_title'] or 'No title'}\n"
        if len(employees) > 10:
            result += f"... and {len(employees) - 10} more"
        return result

    async def _get_employee_info(self, employee_id: int) -> str:
        emp = self.odoo.get_employee_by_id(employee_id)
        if not emp:
            return f"Employee with ID {employee_id} not found."
        return (
            f"Employee: {emp['name']}\n"
            f"Job Title: {emp['job_title'] or 'Not set'}\n"
            f"Department: {emp['department'] or 'Not set'}\n"
            f"Manager: {emp['manager'] or 'Not set'}\n"
            f"Email: {emp['email'] or 'Not set'}"
        )

    async def _get_leave_balance(self, employee_id: int) -> str:
        balances = self.odoo.get_leave_balance(employee_id)
        if not balances:
            return "No leave allocations found for this employee."
        result = "Leave balance:\n"
        for bal in balances:
            result += f"- {bal['leave_type']}: {bal['remaining']} days remaining (used {bal['taken']} of {bal['allocated']})\n"
        return result

    async def _get_leave_requests(self, employee_id: int, state: Optional[str] = None) -> str:
        requests = self.odoo.get_leave_requests(employee_id, state)
        if not requests:
            return "No leave requests found."
        result = f"Found {len(requests)} leave requests:\n"
        for req in requests[:5]:
            result += f"- {req['leave_type']}: {req['date_from']} to {req['date_to']} ({req['days']} days) - Status: {req['state']}\n"
        return result

    async def _get_payslips(self, employee_id: int, limit: int = 3) -> str:
        payslips = self.odoo.get_payslips(employee_id, limit)
        if not payslips:
            return "No payslips found for this employee."
        result = f"Recent payslips:\n"
        for ps in payslips:
            result += f"- {ps['name']}: Net {ps['net_wage']}, Gross {ps['gross_wage']} ({ps['state']})\n"
        return result

    async def _get_attendance(
        self, employee_id: int, month: Optional[int] = None, year: Optional[int] = None
    ) -> str:
        summary = self.odoo.get_attendance_summary(employee_id, month, year)
        return (
            f"Attendance for {summary['month']}/{summary['year']}:\n"
            f"- Total days worked: {summary['total_days']}\n"
            f"- Total hours: {summary['total_hours']}"
        )

    async def _get_employee_tasks(self, employee_id: int) -> str:
        tasks = self.odoo.get_employee_tasks(employee_id)
        if not tasks:
            return "No tasks assigned to this employee."
        result = f"Found {len(tasks)} tasks:\n"
        for task in tasks[:5]:
            deadline = task['deadline'] or 'No deadline'
            result += f"- {task['name']} ({task['stage']}) - Due: {deadline}\n"
        if len(tasks) > 5:
            result += f"... and {len(tasks) - 5} more tasks"
        return result

    async def _get_all_tasks(self, limit: int = 50) -> str:
        tasks = self.odoo.get_all_tasks(limit)
        if not tasks:
            return "No tasks found."
        result = f"Found {len(tasks)} tasks:\n"
        for task in tasks[:10]:
            deadline = task['deadline'] or 'No deadline'
            result += f"- {task['name']} ({task['project']}) - Due: {deadline}\n"
        return result

    async def _get_overdue_tasks(self) -> str:
        tasks = self.odoo.get_overdue_tasks()
        if not tasks:
            return "Great news! No overdue tasks found."
        result = f"Warning: {len(tasks)} overdue tasks:\n"
        for task in tasks[:5]:
            result += f"- {task['name']} - Was due: {task['deadline']}\n"
        return result

    async def _get_workload_analysis(self) -> str:
        result = await self.task_client.get_employees_workload()
        if "error" in result:
            return f"Could not fetch workload data: {result.get('error')}"
        employees = result.get("employees", [])
        if not employees:
            return "No workload data available."
        output = "Team workload:\n"
        for emp in employees[:5]:
            output += f"- {emp.get('name', 'Unknown')}: {emp.get('task_count', 0)} tasks\n"
        return output

    async def _get_pending_leave_approvals(self) -> str:
        result = await self.hr_client.get_pending_leaves()
        if "error" in result:
            return f"Could not fetch pending leaves: {result.get('error')}"
        leaves = result.get("leaves", [])
        if not leaves:
            return "No pending leave requests."
        output = f"{len(leaves)} pending leave requests:\n"
        for leave in leaves[:5]:
            output += f"- {leave.get('employee_name', 'Unknown')}: {leave.get('days', 0)} days\n"
        return output

    async def _get_hr_headcount_report(self) -> str:
        result = await self.hr_client.get_headcount_report()
        if "error" in result:
            return f"Could not fetch headcount report: {result.get('error')}"
        return f"Headcount report: {result}"

    async def _get_hr_insights(self) -> str:
        result = await self.hr_client.get_hr_insights()
        if "error" in result:
            return f"Could not fetch HR insights: {result.get('error')}"
        return f"HR Insights: {result.get('insights', 'No insights available')}"

    async def _get_expiring_contracts(self, days: int = 30) -> str:
        result = await self.contract_client.get_expiring_contracts(days)
        if "error" in result:
            return f"Could not fetch expiring contracts: {result.get('error')}"
        contracts = result.get("contracts", [])
        if not contracts:
            return f"No contracts expiring in the next {days} days."
        output = f"{len(contracts)} contracts expiring in {days} days:\n"
        for c in contracts[:5]:
            output += f"- {c.get('name', 'Unknown')}: expires {c.get('expiry_date', 'Unknown')}\n"
        return output

    async def _get_contract_compliance_report(self) -> str:
        result = await self.contract_client.get_compliance_report()
        if "error" in result:
            return f"Could not fetch compliance report: {result.get('error')}"
        return f"Compliance report: {result}"

    async def _switch_language(self, language: str) -> str:
        self.language = language
        if language == "ar":
            return "تم التبديل إلى اللغة العربية. كيف يمكنني مساعدتك؟"
        return "Switched to English. How can I help you?"


async def entrypoint(ctx: JobContext):
    """Main entry point for the LiveKit agent."""
    logger.info(f"Connecting to room: {ctx.room.name}")

    # Initialize agent tools
    agent_instance = AiligentVoiceAgent()

    # Connect to room first
    await ctx.connect(auto_subscribe=AutoSubscribe.AUDIO_ONLY)

    # Create voice agent with new API
    agent = Agent(
        instructions=get_system_prompt(settings.DEFAULT_LANGUAGE),
        vad=silero.VAD.load(),
        stt=google.STT(),
        llm=google.LLM(model="gemini-2.0-flash-exp"),
        tts=google.TTS(voice=settings.VOICE_EN),
        tools=agent_instance.get_tools(),
        allow_interruptions=True,
    )

    # Start the agent session
    session = agent.start(ctx.room)

    # Greet user
    await session.say(get_greeting(settings.DEFAULT_LANGUAGE))

    logger.info("Voice agent started successfully")


def run_agent():
    """Run the LiveKit agent worker."""
    cli.run_app(
        WorkerOptions(
            entrypoint_fnc=entrypoint,
            api_key=settings.LIVEKIT_API_KEY,
            api_secret=settings.LIVEKIT_API_SECRET,
            ws_url=settings.LIVEKIT_URL,
        )
    )
