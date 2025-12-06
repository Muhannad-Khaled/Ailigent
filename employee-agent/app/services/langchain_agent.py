"""
LangChain-based Employee Agent Service

This module provides an AI-powered employee assistant using LangChain with Google Gemini.
It replaces the direct Gemini API integration with full LangChain support including:
- Tool-calling agents with @tool decorated functions
- Conversation memory with ConversationBufferWindowMemory
- Structured outputs with Pydantic models
- Bilingual support (English/Arabic)
"""

import re
import json
from typing import Dict, List, Optional, Any, TYPE_CHECKING
from datetime import datetime
from loguru import logger

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.agents import AgentExecutor, create_tool_calling_agent
from langchain.memory import ConversationBufferWindowMemory
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.tools import tool, StructuredTool
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from pydantic import BaseModel, Field

if TYPE_CHECKING:
    from app.services.odoo_service import OdooService


# ==================== Pydantic Output Models ====================

class EmployeeInfo(BaseModel):
    """Employee information structure"""
    id: int = Field(description="Employee ID")
    name: str = Field(description="Employee name")
    email: Optional[str] = Field(description="Work email")
    job_title: Optional[str] = Field(description="Job title")
    department: Optional[str] = Field(description="Department name")
    manager: Optional[str] = Field(description="Manager name")


class LeaveBalanceItem(BaseModel):
    """Single leave balance item"""
    leave_type: str = Field(description="Type of leave")
    allocated: float = Field(description="Days allocated")
    taken: float = Field(description="Days taken")
    remaining: float = Field(description="Days remaining")


class LeaveRequestItem(BaseModel):
    """Single leave request item"""
    id: int = Field(description="Leave request ID")
    leave_type: str = Field(description="Type of leave")
    date_from: str = Field(description="Start date")
    date_to: str = Field(description="End date")
    days: float = Field(description="Number of days")
    state: str = Field(description="Request state")
    reason: Optional[str] = Field(description="Request reason")


class PayslipItem(BaseModel):
    """Single payslip item"""
    id: int = Field(description="Payslip ID")
    name: str = Field(description="Payslip name")
    period: str = Field(description="Pay period")
    state: str = Field(description="Payslip state")
    net_wage: float = Field(description="Net wage amount")
    gross_wage: float = Field(description="Gross wage amount")


class TaskItem(BaseModel):
    """Single task item"""
    id: int = Field(description="Task ID")
    name: str = Field(description="Task name")
    description: Optional[str] = Field(description="Task description")
    deadline: Optional[str] = Field(description="Due date")
    priority: Optional[str] = Field(description="Priority level")
    stage: Optional[str] = Field(description="Current stage")


# ==================== Global Service Reference ====================
# This will be set by the LangChainEmployeeAgent when initializing tools
_odoo_service: Optional["OdooService"] = None


def _set_odoo_service(service: "OdooService") -> None:
    """Set the global Odoo service reference for tools"""
    global _odoo_service
    _odoo_service = service


# ==================== LangChain Tools ====================

@tool
async def get_employee_info(employee_id: int) -> Dict[str, Any]:
    """
    Get detailed information about an employee including name, email, department, job title, and manager.

    Args:
        employee_id: The Odoo employee ID

    Returns:
        Dictionary with employee details or error message
    """
    if not _odoo_service:
        return {"error": "Odoo service not configured"}

    try:
        employee = await _odoo_service.get_employee_by_id(employee_id)
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
                }
            }
        return {"success": False, "error": "Employee not found"}
    except Exception as e:
        logger.error(f"Error in get_employee_info: {e}")
        return {"error": str(e)}


@tool
async def get_leave_balance(employee_id: int) -> Dict[str, Any]:
    """
    Get the leave balance for an employee showing all leave types with allocated, taken, and remaining days.

    Args:
        employee_id: The Odoo employee ID

    Returns:
        Dictionary with leave balances for all leave types
    """
    if not _odoo_service:
        return {"error": "Odoo service not configured"}

    try:
        balances = await _odoo_service.get_leave_balance(employee_id)
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
        logger.error(f"Error in get_leave_balance: {e}")
        return {"error": str(e)}


@tool
async def get_leave_requests(employee_id: int, state: Optional[str] = None) -> Dict[str, Any]:
    """
    Get leave requests for an employee, optionally filtered by state.

    Args:
        employee_id: The Odoo employee ID
        state: Optional filter by state (draft, confirm, validate, refuse)

    Returns:
        Dictionary with list of leave requests
    """
    if not _odoo_service:
        return {"error": "Odoo service not configured"}

    try:
        requests = await _odoo_service.get_leave_requests(employee_id, state)
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
        logger.error(f"Error in get_leave_requests: {e}")
        return {"error": str(e)}


@tool
async def get_payslips(employee_id: int, limit: int = 6) -> Dict[str, Any]:
    """
    Get recent payslips for an employee with net and gross wages.

    Args:
        employee_id: The Odoo employee ID
        limit: Maximum number of payslips to return (default 6)

    Returns:
        Dictionary with list of payslips
    """
    if not _odoo_service:
        return {"error": "Odoo service not configured"}

    try:
        payslips = await _odoo_service.get_payslips(employee_id, limit)
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
        logger.error(f"Error in get_payslips: {e}")
        return {"error": str(e)}


@tool
async def get_attendance_summary(
    employee_id: int,
    month: Optional[int] = None,
    year: Optional[int] = None
) -> Dict[str, Any]:
    """
    Get attendance summary for an employee for a specific month including total days and hours worked.

    Args:
        employee_id: The Odoo employee ID
        month: Month number (1-12), defaults to current month
        year: Year, defaults to current year

    Returns:
        Dictionary with attendance summary
    """
    if not _odoo_service:
        return {"error": "Odoo service not configured"}

    try:
        summary = await _odoo_service.get_attendance_summary(employee_id, month, year)
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
        logger.error(f"Error in get_attendance_summary: {e}")
        return {"error": str(e)}


@tool
async def get_employee_tasks(employee_id: int) -> Dict[str, Any]:
    """
    Get tasks assigned to an employee with deadlines and status.

    Args:
        employee_id: The Odoo employee ID

    Returns:
        Dictionary with list of tasks
    """
    if not _odoo_service:
        return {"error": "Odoo service not configured"}

    try:
        tasks = await _odoo_service.get_employee_tasks(employee_id)
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
        logger.error(f"Error in get_employee_tasks: {e}")
        return {"error": str(e)}


@tool
async def create_task(
    employee_id: int,
    name: str,
    description: str = "",
    due_date: Optional[str] = None
) -> Dict[str, Any]:
    """
    Create a new task for an employee.

    Args:
        employee_id: The Odoo employee ID to assign the task to
        name: Task name/title
        description: Task description (optional)
        due_date: Due date in YYYY-MM-DD format (optional)

    Returns:
        Dictionary with task creation result
    """
    if not _odoo_service:
        return {"error": "Odoo service not configured"}

    try:
        task_id = await _odoo_service.create_task(
            employee_id=employee_id,
            name=name,
            description=description,
            due_date=due_date,
        )
        if task_id:
            return {"success": True, "task_id": task_id, "message": f"Task '{name}' created successfully"}
        return {"success": False, "error": "Failed to create task"}
    except Exception as e:
        logger.error(f"Error in create_task: {e}")
        return {"error": str(e)}


@tool
async def get_company_policies() -> Dict[str, Any]:
    """
    Get list of company policies and documents.

    Returns:
        Dictionary with list of company policies
    """
    if not _odoo_service:
        return {"error": "Odoo service not configured"}

    try:
        policies = await _odoo_service.get_company_policies()
        return {
            "success": True,
            "policies": [
                {
                    "id": p.get("id"),
                    "name": p.get("name"),
                    "description": p.get("description"),
                }
                for p in policies
            ]
        }
    except Exception as e:
        logger.error(f"Error in get_company_policies: {e}")
        return {"error": str(e)}


# ==================== System Prompts ====================

SYSTEM_PROMPT_EN = """You are "Ailigent", the company's intelligent employee assistant. You help employees with:
- Answering company policy questions
- Providing leave and payroll information
- Managing and tracking tasks
- Providing daily work summaries
- Assisting with system usage

Current employee: {employee_name}
Department: {department}
Employee ID: {employee_id}

Important rules:
- Always respond in English
- Be concise and helpful
- Use proper Telegram formatting (markdown)
- If unsure, ask for clarification
- Don't make up information that doesn't exist
- Use the available tools to fetch real data from the system
- When calling tools, always use the employee_id provided in the context"""

SYSTEM_PROMPT_AR = """أنت "أيليجنت"، مساعد الموظفين الذكي للشركة. أنت تساعد الموظفين في:
- الإجابة على أسئلة سياسات الشركة
- توفير معلومات الإجازات والرواتب
- إدارة المهام وتتبعها
- تقديم ملخصات العمل اليومية
- مساعدة في استخدام الأنظمة

الموظف الحالي: {employee_name}
القسم: {department}
رقم الموظف: {employee_id}

قواعد مهمة:
- أجب دائماً باللغة العربية
- كن مختصراً ومفيداً
- استخدم تنسيق Telegram المناسب (markdown)
- إذا لم تكن متأكداً، اطلب التوضيح
- لا تخترع معلومات غير موجودة
- استخدم الأدوات المتاحة للحصول على بيانات حقيقية من النظام
- عند استدعاء الأدوات، استخدم دائماً رقم الموظف المقدم في السياق"""


# ==================== LangChain Employee Agent ====================

class LangChainEmployeeAgent:
    """
    AI service using LangChain for employee assistance.

    Features:
    - Google Gemini LLM via langchain-google-genai
    - 8 Odoo integration tools with @tool decorator
    - Per-user conversation memory with window buffer
    - Bilingual support (English/Arabic)
    - Tool-calling agent with automatic function execution
    """

    def __init__(self, api_key: str, odoo_service: Optional["OdooService"] = None):
        """
        Initialize the LangChain Employee Agent.

        Args:
            api_key: Google AI API key
            odoo_service: OdooService instance for tool calls
        """
        # Initialize LLM
        self.llm = ChatGoogleGenerativeAI(
            model="gemini-2.0-flash",
            google_api_key=api_key,
            temperature=0.7,
            max_output_tokens=1024,
            convert_system_message_to_human=True,
        )

        # Simple LLM for non-tool responses
        self.llm_simple = ChatGoogleGenerativeAI(
            model="gemini-2.0-flash",
            google_api_key=api_key,
            temperature=0.7,
            max_output_tokens=1024,
        )

        # Set Odoo service for tools
        self._odoo_service = odoo_service
        if odoo_service:
            _set_odoo_service(odoo_service)

        # Define tools list
        self._tools = [
            get_employee_info,
            get_leave_balance,
            get_leave_requests,
            get_payslips,
            get_attendance_summary,
            get_employee_tasks,
            create_task,
            get_company_policies,
        ]

        # Per-user memory storage
        self._user_memories: Dict[int, ConversationBufferWindowMemory] = {}

        logger.info(f"LangChainEmployeeAgent initialized (tools: {len(self._tools)})")

    def set_odoo_service(self, odoo_service: "OdooService") -> None:
        """Set the Odoo service for tool calls"""
        self._odoo_service = odoo_service
        _set_odoo_service(odoo_service)
        logger.info("LangChainEmployeeAgent updated with Odoo service")

    def _get_memory(self, user_id: int) -> ConversationBufferWindowMemory:
        """Get or create conversation memory for a user"""
        if user_id not in self._user_memories:
            self._user_memories[user_id] = ConversationBufferWindowMemory(
                memory_key="chat_history",
                return_messages=True,
                k=10,  # Keep last 10 message exchanges
            )
        return self._user_memories[user_id]

    def _detect_language(self, text: str) -> str:
        """Detect if text is Arabic or English based on character analysis"""
        arabic_pattern = re.compile(r"[\u0600-\u06FF]")
        arabic_chars = len(arabic_pattern.findall(text))
        total_alpha = sum(1 for c in text if c.isalpha())

        if total_alpha == 0:
            return "en"

        arabic_ratio = arabic_chars / total_alpha
        return "ar" if arabic_ratio > 0.3 else "en"

    def _get_prompt(
        self,
        language: str,
        employee_name: str,
        department: str,
        employee_id: int,
    ) -> ChatPromptTemplate:
        """Create the prompt template with system message and placeholders"""
        system_template = SYSTEM_PROMPT_AR if language == "ar" else SYSTEM_PROMPT_EN
        system_message = system_template.format(
            employee_name=employee_name,
            department=department,
            employee_id=employee_id,
        )

        return ChatPromptTemplate.from_messages([
            ("system", system_message),
            MessagesPlaceholder(variable_name="chat_history"),
            ("human", "{input}"),
            MessagesPlaceholder(variable_name="agent_scratchpad"),
        ])

    async def process_message(
        self,
        user_id: int,
        message: str,
        context: Optional[Dict[str, Any]] = None,
    ) -> str:
        """
        Process a user message and return AI response.
        Supports LangChain tool-calling for Odoo integration.

        Args:
            user_id: Telegram user ID
            message: User's message text
            context: Optional context with employee info (employee_id required for tools)

        Returns:
            AI response text
        """
        try:
            # Detect language
            language = self._detect_language(message)

            # Get context info
            employee_name = context.get("employee_name", "") if context else ""
            department = context.get("department", "") if context else ""
            employee_id = context.get("employee_id") if context else None

            # Get memory for this user
            memory = self._get_memory(user_id)

            # Build the prompt with employee context
            prompt = self._get_prompt(language, employee_name, department, employee_id or 0)

            # Create the tool-calling agent
            agent = create_tool_calling_agent(self.llm, self._tools, prompt)

            # Create executor with memory
            executor = AgentExecutor(
                agent=agent,
                tools=self._tools,
                memory=memory,
                verbose=True,
                max_iterations=5,
                handle_parsing_errors=True,
            )

            # Build input message with employee_id hint for tools
            if employee_id:
                input_message = f"{message}\n\n[Use employee_id={employee_id} for any tool calls]"
            else:
                input_message = message

            # Execute agent
            result = await executor.ainvoke({"input": input_message})

            return result.get("output", "I processed your request.")

        except Exception as e:
            logger.error(f"Error processing message for user {user_id}: {e}")
            language = self._detect_language(message)
            if language == "ar":
                return "عذراً، حدث خطأ في معالجة طلبك. يرجى المحاولة مرة أخرى."
            return "Sorry, an error occurred while processing your request. Please try again."

    async def generate_daily_summary(
        self,
        employee_data: Dict[str, Any],
        language: str = "en",
    ) -> str:
        """
        Generate a daily work summary for an employee.

        Args:
            employee_data: Dict containing attendance, tasks, etc.
            language: 'en' or 'ar'

        Returns:
            Formatted summary text
        """
        try:
            today = datetime.now().strftime("%Y-%m-%d")

            if language == "ar":
                prompt = f"""اكتب ملخص عمل يومي موجز للموظف بناءً على البيانات التالية:

التاريخ: {today}
الاسم: {employee_data.get('name', 'الموظف')}
القسم: {employee_data.get('department', 'غير محدد')}

بيانات الحضور:
- ساعات العمل اليوم: {employee_data.get('hours_today', 'غير متاح')}
- وقت الحضور: {employee_data.get('check_in', 'غير متاح')}
- وقت الانصراف: {employee_data.get('check_out', 'غير متاح')}

المهام:
- المهام المكتملة: {employee_data.get('completed_tasks', 0)}
- المهام المعلقة: {employee_data.get('pending_tasks', 0)}

رصيد الإجازات: {employee_data.get('leave_balance', 'غير متاح')}

اكتب الملخص بشكل مختصر ومهني باللغة العربية. استخدم تنسيق Telegram."""
            else:
                prompt = f"""Write a brief daily work summary for the employee based on the following data:

Date: {today}
Name: {employee_data.get('name', 'Employee')}
Department: {employee_data.get('department', 'Not specified')}

Attendance data:
- Hours worked today: {employee_data.get('hours_today', 'N/A')}
- Check-in time: {employee_data.get('check_in', 'N/A')}
- Check-out time: {employee_data.get('check_out', 'N/A')}

Tasks:
- Completed tasks: {employee_data.get('completed_tasks', 0)}
- Pending tasks: {employee_data.get('pending_tasks', 0)}

Leave balance: {employee_data.get('leave_balance', 'N/A')}

Write the summary in a concise, professional manner. Use Telegram formatting."""

            response = await self.llm_simple.ainvoke([HumanMessage(content=prompt)])
            return response.content

        except Exception as e:
            logger.error(f"Error generating daily summary: {e}")
            if language == "ar":
                return "عذراً، لم نتمكن من إنشاء الملخص اليومي. يرجى المحاولة لاحقاً."
            return "Sorry, we couldn't generate the daily summary. Please try again later."

    async def extract_tasks(self, conversation: str, employee_id: int) -> List[Dict[str, Any]]:
        """
        Extract action items/tasks from a conversation.

        Args:
            conversation: The conversation text to analyze
            employee_id: Employee ID to assign tasks to

        Returns:
            List of extracted task dictionaries
        """
        try:
            prompt = f"""Analyze the following conversation and extract any tasks or action items mentioned.
For each task, provide:
1. Task name (brief, action-oriented)
2. Description (if details are available)
3. Due date (if mentioned, in YYYY-MM-DD format)
4. Priority (high, normal, low)

Format your response as JSON array. If no tasks are found, respond with [].

Conversation:
{conversation}"""

            response = await self.llm_simple.ainvoke([HumanMessage(content=prompt)])

            # Try to parse JSON from response
            try:
                tasks = json.loads(response.content)
                return tasks if isinstance(tasks, list) else []
            except json.JSONDecodeError:
                return []

        except Exception as e:
            logger.error(f"Error extracting tasks: {e}")
            return []

    def clear_session(self, user_id: int) -> None:
        """Clear chat session/memory for a user"""
        if user_id in self._user_memories:
            del self._user_memories[user_id]
            logger.info(f"Cleared chat session for user {user_id}")

    def clear_all_sessions(self) -> None:
        """Clear all chat sessions"""
        self._user_memories.clear()
        logger.info("Cleared all chat sessions")


# ==================== Backward Compatibility Alias ====================
# This allows existing code to import GeminiService and get the new LangChain agent
GeminiService = LangChainEmployeeAgent
