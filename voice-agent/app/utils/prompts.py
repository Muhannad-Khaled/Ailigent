"""System prompts for the voice agent."""


def get_system_prompt(language: str = "en") -> str:
    """Get the system prompt for the voice agent.

    Args:
        language: 'en' for English, 'ar' for Arabic

    Returns:
        System prompt string
    """
    if language == "ar":
        return """أنت مساعد صوتي ذكي لنظام إدارة الموارد البشرية. يمكنك مساعدة الموظفين في:

1. **الإجازات**: عرض رصيد الإجازات، تقديم طلبات إجازة
2. **الرواتب**: عرض كشوف المرتبات الأخيرة
3. **الحضور**: عرض ملخص الحضور الشهري
4. **المهام**: عرض المهام المسندة إليك
5. **السياسات**: البحث في سياسات الشركة

للمديرين:
- الموافقة على طلبات الإجازة
- عرض تقارير الموارد البشرية
- تحليل عبء العمل

تحدث بشكل طبيعي وودود. أجب بإيجاز ووضوح."""

    return """You are an intelligent voice assistant for the HR management system. You can help employees with:

1. **Leave**: Check leave balance, submit leave requests
2. **Payroll**: View recent payslips
3. **Attendance**: View monthly attendance summary
4. **Tasks**: View assigned tasks and team workload
5. **Policies**: Search company policies
6. **Contracts**: Check expiring contracts, view contract summaries

For managers:
- Approve leave requests
- View HR reports (headcount, turnover)
- Analyze team workload

Speak naturally and friendly. Keep responses concise and clear.

Important guidelines:
- Be helpful and proactive in suggesting what information you can provide
- If you're unsure about something, ask for clarification
- When presenting numbers or lists, organize them clearly
- Adapt your language based on what the user speaks (English or Arabic)"""


def get_tool_description(tool_name: str, language: str = "en") -> str:
    """Get description for a specific tool."""
    descriptions = {
        "en": {
            "get_leave_balance": "Check your available leave days by type",
            "get_tasks": "View your assigned tasks",
            "get_payslips": "View your recent payslips",
            "get_attendance": "View your attendance summary",
            "request_leave": "Submit a new leave request",
            "get_team_tasks": "View all team tasks",
            "get_overdue_tasks": "View overdue tasks",
            "approve_leave": "Approve or reject leave requests",
            "get_hr_report": "Generate HR analytics report",
        },
        "ar": {
            "get_leave_balance": "عرض رصيد إجازاتك حسب النوع",
            "get_tasks": "عرض مهامك المسندة",
            "get_payslips": "عرض كشوف مرتباتك الأخيرة",
            "get_attendance": "عرض ملخص حضورك",
            "request_leave": "تقديم طلب إجازة جديد",
            "get_team_tasks": "عرض جميع مهام الفريق",
            "get_overdue_tasks": "عرض المهام المتأخرة",
            "approve_leave": "الموافقة على طلبات الإجازة",
            "get_hr_report": "إنشاء تقرير الموارد البشرية",
        }
    }
    return descriptions.get(language, descriptions["en"]).get(tool_name, tool_name)
