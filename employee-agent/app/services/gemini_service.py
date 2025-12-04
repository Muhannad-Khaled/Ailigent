import re
import json
from typing import Dict, List, Optional, Any, TYPE_CHECKING
from datetime import datetime
from loguru import logger

import google.generativeai as genai
from google.generativeai.types import HarmCategory, HarmBlockThreshold
from google.generativeai import protos

from app.models.employee import Task

if TYPE_CHECKING:
    from app.services.odoo_service import OdooService


# Define MCP-style tools as Gemini function declarations using protos
def _create_odoo_tools():
    """Create Odoo tools compatible with current google-generativeai version."""
    return [
        protos.Tool(
            function_declarations=[
                protos.FunctionDeclaration(
                    name="get_employee_info",
                    description="Get detailed information about an employee including name, email, department, job title, and manager",
                    parameters=protos.Schema(
                        type=protos.Type.OBJECT,
                        properties={
                            "employee_id": protos.Schema(
                                type=protos.Type.INTEGER,
                                description="The Odoo employee ID"
                            )
                        },
                        required=["employee_id"]
                    )
                ),
                protos.FunctionDeclaration(
                    name="get_leave_balance",
                    description="Get the leave balance for an employee showing all leave types with allocated, taken, and remaining days",
                    parameters=protos.Schema(
                        type=protos.Type.OBJECT,
                        properties={
                            "employee_id": protos.Schema(
                                type=protos.Type.INTEGER,
                                description="The Odoo employee ID"
                            )
                        },
                        required=["employee_id"]
                    )
                ),
                protos.FunctionDeclaration(
                    name="get_leave_requests",
                    description="Get leave requests for an employee, optionally filtered by state (draft, confirm, validate, refuse)",
                    parameters=protos.Schema(
                        type=protos.Type.OBJECT,
                        properties={
                            "employee_id": protos.Schema(
                                type=protos.Type.INTEGER,
                                description="The Odoo employee ID"
                            ),
                            "state": protos.Schema(
                                type=protos.Type.STRING,
                                description="Filter by state: draft, confirm, validate, refuse"
                            )
                        },
                        required=["employee_id"]
                    )
                ),
                protos.FunctionDeclaration(
                    name="get_payslips",
                    description="Get recent payslips for an employee with net and gross wages",
                    parameters=protos.Schema(
                        type=protos.Type.OBJECT,
                        properties={
                            "employee_id": protos.Schema(
                                type=protos.Type.INTEGER,
                                description="The Odoo employee ID"
                            ),
                            "limit": protos.Schema(
                                type=protos.Type.INTEGER,
                                description="Maximum number of payslips to return (default 6)"
                            )
                        },
                        required=["employee_id"]
                    )
                ),
                protos.FunctionDeclaration(
                    name="get_attendance_summary",
                    description="Get attendance summary for an employee for a specific month including total days and hours worked",
                    parameters=protos.Schema(
                        type=protos.Type.OBJECT,
                        properties={
                            "employee_id": protos.Schema(
                                type=protos.Type.INTEGER,
                                description="The Odoo employee ID"
                            ),
                            "month": protos.Schema(
                                type=protos.Type.INTEGER,
                                description="Month number (1-12), defaults to current month"
                            ),
                            "year": protos.Schema(
                                type=protos.Type.INTEGER,
                                description="Year, defaults to current year"
                            )
                        },
                        required=["employee_id"]
                    )
                ),
                protos.FunctionDeclaration(
                    name="get_employee_tasks",
                    description="Get tasks assigned to an employee with deadlines and status",
                    parameters=protos.Schema(
                        type=protos.Type.OBJECT,
                        properties={
                            "employee_id": protos.Schema(
                                type=protos.Type.INTEGER,
                                description="The Odoo employee ID"
                            )
                        },
                        required=["employee_id"]
                    )
                ),
                protos.FunctionDeclaration(
                    name="create_task",
                    description="Create a new task for an employee",
                    parameters=protos.Schema(
                        type=protos.Type.OBJECT,
                        properties={
                            "employee_id": protos.Schema(
                                type=protos.Type.INTEGER,
                                description="The Odoo employee ID to assign the task to"
                            ),
                            "name": protos.Schema(
                                type=protos.Type.STRING,
                                description="Task name/title"
                            ),
                            "description": protos.Schema(
                                type=protos.Type.STRING,
                                description="Task description"
                            ),
                            "due_date": protos.Schema(
                                type=protos.Type.STRING,
                                description="Due date in YYYY-MM-DD format"
                            )
                        },
                        required=["employee_id", "name"]
                    )
                ),
                protos.FunctionDeclaration(
                    name="get_company_policies",
                    description="Get list of company policies and documents",
                    parameters=protos.Schema(
                        type=protos.Type.OBJECT,
                        properties={}
                    )
                ),
            ]
        )
    ]


ODOO_TOOLS = None  # Will be lazily initialized


class GeminiService:
    """AI service using Google Gemini for employee assistance with MCP-style tool integration"""

    def __init__(self, api_key: str, odoo_service: Optional["OdooService"] = None):
        genai.configure(api_key=api_key)
        self._odoo_service = odoo_service

        # Configure the model with safety settings and tools
        self.model = genai.GenerativeModel(
            model_name="gemini-2.0-flash",
            safety_settings={
                HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
                HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
                HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE,
                HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
            },
            generation_config={
                "temperature": 0.7,
                "top_p": 0.95,
                "top_k": 40,
                "max_output_tokens": 1024,
            },
            tools=_create_odoo_tools() if odoo_service else None,
        )

        # Model without tools for simple responses
        self.model_simple = genai.GenerativeModel(
            model_name="gemini-2.0-flash",
            safety_settings={
                HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
                HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
                HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE,
                HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
            },
            generation_config={
                "temperature": 0.7,
                "top_p": 0.95,
                "top_k": 40,
                "max_output_tokens": 1024,
            },
        )

        # Store chat sessions per user
        self._chat_sessions: Dict[int, Any] = {}

        logger.info(f"GeminiService initialized (MCP tools: {odoo_service is not None})")

    def set_odoo_service(self, odoo_service: "OdooService") -> None:
        """Set the Odoo service for MCP tool calls"""
        self._odoo_service = odoo_service
        # Recreate model with tools
        self.model = genai.GenerativeModel(
            model_name="gemini-2.0-flash",
            safety_settings={
                HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
                HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
                HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE,
                HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
            },
            generation_config={
                "temperature": 0.7,
                "top_p": 0.95,
                "top_k": 40,
                "max_output_tokens": 1024,
            },
            tools=_create_odoo_tools(),
        )
        # Clear existing sessions to use new model
        self._chat_sessions.clear()
        logger.info("GeminiService updated with Odoo MCP tools")

    async def _execute_tool(self, function_name: str, args: Dict[str, Any]) -> Dict[str, Any]:
        """Execute an MCP tool call and return the result"""
        if not self._odoo_service:
            return {"error": "Odoo service not configured"}

        try:
            if function_name == "get_employee_info":
                employee = await self._odoo_service.get_employee_by_id(args["employee_id"])
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

            elif function_name == "get_leave_balance":
                balances = await self._odoo_service.get_leave_balance(args["employee_id"])
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

            elif function_name == "get_leave_requests":
                requests = await self._odoo_service.get_leave_requests(
                    args["employee_id"], args.get("state")
                )
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

            elif function_name == "get_payslips":
                payslips = await self._odoo_service.get_payslips(
                    args["employee_id"], args.get("limit", 6)
                )
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

            elif function_name == "get_attendance_summary":
                summary = await self._odoo_service.get_attendance_summary(
                    args["employee_id"], args.get("month"), args.get("year")
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

            elif function_name == "get_employee_tasks":
                tasks = await self._odoo_service.get_employee_tasks(args["employee_id"])
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

            elif function_name == "create_task":
                task_id = await self._odoo_service.create_task(
                    employee_id=args["employee_id"],
                    name=args["name"],
                    description=args.get("description", ""),
                    due_date=args.get("due_date"),
                )
                if task_id:
                    return {"success": True, "task_id": task_id}
                return {"success": False, "error": "Failed to create task"}

            elif function_name == "get_company_policies":
                policies = await self._odoo_service.get_company_policies()
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

            else:
                return {"error": f"Unknown function: {function_name}"}

        except Exception as e:
            logger.error(f"Error executing tool {function_name}: {e}")
            return {"error": str(e)}

    def _detect_language(self, text: str) -> str:
        """Detect if text is Arabic or English based on character analysis"""
        # Arabic Unicode range: \u0600-\u06FF
        arabic_pattern = re.compile(r"[\u0600-\u06FF]")
        arabic_chars = len(arabic_pattern.findall(text))
        total_alpha = sum(1 for c in text if c.isalpha())

        if total_alpha == 0:
            return "en"

        arabic_ratio = arabic_chars / total_alpha
        return "ar" if arabic_ratio > 0.3 else "en"

    def _get_system_prompt(self, language: str, employee_name: str = "", department: str = "") -> str:
        """Get system prompt based on language"""
        if language == "ar":
            return f"""أنت "أيليجنت"، مساعد الموظفين الذكي للشركة. أنت تساعد الموظفين في:
- الإجابة على أسئلة سياسات الشركة
- توفير معلومات الإجازات والرواتب
- إدارة المهام وتتبعها
- تقديم ملخصات العمل اليومية
- مساعدة في استخدام الأنظمة

الموظف الحالي: {employee_name}
القسم: {department}

قواعد مهمة:
- أجب دائماً باللغة العربية
- كن مختصراً ومفيداً
- استخدم تنسيق Telegram المناسب (markdown)
- إذا لم تكن متأكداً، اطلب التوضيح
- لا تخترع معلومات غير موجودة"""
        else:
            return f"""You are "Ailigent", the company's intelligent employee assistant. You help employees with:
- Answering company policy questions
- Providing leave and payroll information
- Managing and tracking tasks
- Providing daily work summaries
- Assisting with system usage

Current employee: {employee_name}
Department: {department}

Important rules:
- Always respond in English
- Be concise and helpful
- Use proper Telegram formatting (markdown)
- If unsure, ask for clarification
- Don't make up information that doesn't exist"""

    def _get_chat_session(
        self,
        user_id: int,
        employee_name: str = "",
        department: str = "",
        language: str = "en",
    ) -> Any:
        """Get or create a chat session for a user"""
        if user_id not in self._chat_sessions:
            system_prompt = self._get_system_prompt(language, employee_name, department)
            self._chat_sessions[user_id] = self.model.start_chat(
                history=[
                    {"role": "user", "parts": [system_prompt]},
                    {"role": "model", "parts": ["Understood. I'm ready to help." if language == "en" else "مفهوم. أنا جاهز للمساعدة."]},
                ]
            )
        return self._chat_sessions[user_id]

    async def process_message(
        self,
        user_id: int,
        message: str,
        context: Optional[Dict[str, Any]] = None,
    ) -> str:
        """
        Process a user message and return AI response.
        Supports MCP-style function calling for Odoo integration.

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

            # Get or create chat session
            chat = self._get_chat_session(user_id, employee_name, department, language)

            # Build the message with employee context for tool calls
            if employee_id and self._odoo_service:
                full_message = f"{message}\n\n[Employee ID for tool calls: {employee_id}]"
            else:
                full_message = message

            # Generate response (may include function calls)
            response = chat.send_message(full_message)

            # Handle function calls if present
            max_iterations = 5  # Prevent infinite loops
            iteration = 0

            while response.candidates and iteration < max_iterations:
                candidate = response.candidates[0]

                # Check if there are function calls
                function_calls = []
                for part in candidate.content.parts:
                    if hasattr(part, 'function_call') and part.function_call:
                        function_calls.append(part.function_call)

                if not function_calls:
                    # No more function calls, return the text response
                    break

                # Execute each function call and collect results
                function_responses = []
                for fc in function_calls:
                    function_name = fc.name
                    args = dict(fc.args) if fc.args else {}

                    # Inject employee_id if not provided but available
                    if employee_id and "employee_id" not in args:
                        args["employee_id"] = employee_id

                    logger.info(f"Executing MCP tool: {function_name} with args: {args}")
                    result = await self._execute_tool(function_name, args)

                    function_responses.append({
                        "name": function_name,
                        "response": result,
                    })

                # Send function results back to the model
                response = chat.send_message([
                    genai.protos.Part(function_response=genai.protos.FunctionResponse(
                        name=fr["name"],
                        response={"result": json.dumps(fr["response"])}
                    ))
                    for fr in function_responses
                ])

                iteration += 1

            # Extract text from final response
            if response.candidates:
                text_parts = []
                for part in response.candidates[0].content.parts:
                    if hasattr(part, 'text') and part.text:
                        text_parts.append(part.text)
                if text_parts:
                    return "\n".join(text_parts)

            return response.text if hasattr(response, 'text') else "I processed your request."

        except Exception as e:
            logger.error(f"Error processing message for user {user_id}: {e}")
            language = self._detect_language(message)
            if language == "ar":
                return "عذراً، حدث خطأ في معالجة طلبك. يرجى المحاولة مرة أخرى."
            return "Sorry, an error occurred while processing your request. Please try again."

    async def extract_tasks(self, conversation: str, employee_id: int) -> List[Task]:
        """
        Extract action items/tasks from a conversation.

        Args:
            conversation: The conversation text to analyze
            employee_id: Employee ID to assign tasks to

        Returns:
            List of extracted Task objects
        """
        try:
            prompt = f"""Analyze the following conversation and extract any tasks or action items mentioned.
For each task, provide:
1. Task name (brief, action-oriented)
2. Description (if details are available)
3. Due date (if mentioned, in YYYY-MM-DD format)
4. Priority (high, normal, low)

Format your response as a structured list. If no tasks are found, respond with "NO_TASKS".

Conversation:
{conversation}"""

            response = self.model.generate_content(prompt)
            response_text = response.text

            if "NO_TASKS" in response_text:
                return []

            # Parse tasks from response (simple parsing)
            tasks = []
            lines = response_text.strip().split("\n")
            current_task = {}

            for line in lines:
                line = line.strip()
                if line.startswith("Task:") or line.startswith("1.") or line.startswith("-"):
                    if current_task.get("name"):
                        tasks.append(Task(
                            name=current_task.get("name", ""),
                            description=current_task.get("description"),
                            employee_id=employee_id,
                            due_date=current_task.get("due_date"),
                            priority=current_task.get("priority", "normal"),
                        ))
                    current_task = {"name": line.split(":", 1)[-1].strip() if ":" in line else line[2:].strip()}
                elif line.lower().startswith("description:"):
                    current_task["description"] = line.split(":", 1)[-1].strip()
                elif line.lower().startswith("due:") or line.lower().startswith("due date:"):
                    current_task["due_date"] = line.split(":", 1)[-1].strip()
                elif line.lower().startswith("priority:"):
                    current_task["priority"] = line.split(":", 1)[-1].strip().lower()

            # Add last task
            if current_task.get("name"):
                tasks.append(Task(
                    name=current_task.get("name", ""),
                    description=current_task.get("description"),
                    employee_id=employee_id,
                    due_date=current_task.get("due_date"),
                    priority=current_task.get("priority", "normal"),
                ))

            return tasks

        except Exception as e:
            logger.error(f"Error extracting tasks: {e}")
            return []

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

            response = self.model.generate_content(prompt)
            return response.text

        except Exception as e:
            logger.error(f"Error generating daily summary: {e}")
            if language == "ar":
                return "عذراً، لم نتمكن من إنشاء الملخص اليومي. يرجى المحاولة لاحقاً."
            return "Sorry, we couldn't generate the daily summary. Please try again later."

    def clear_session(self, user_id: int) -> None:
        """Clear chat session for a user"""
        if user_id in self._chat_sessions:
            del self._chat_sessions[user_id]
            logger.info(f"Cleared chat session for user {user_id}")

    def clear_all_sessions(self) -> None:
        """Clear all chat sessions"""
        self._chat_sessions.clear()
        logger.info("Cleared all chat sessions")
