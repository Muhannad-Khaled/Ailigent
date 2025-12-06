from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ConversationHandler,
    CallbackQueryHandler,
    ContextTypes,
    filters,
)
from loguru import logger

from app.services.odoo_service import OdooService
from app.services import GeminiService  # Uses LangChain-based agent (backward compatible)
from app.services.email_service import send_otp_email
from app.utils.otp import otp_manager


# Conversation states
AWAITING_EMAIL, AWAITING_OTP = range(2)

# Store service references
_odoo_service: OdooService = None
_gemini_service: GeminiService = None


# ==================== Bilingual Messages ====================

MESSAGES = {
    "welcome": {
        "en": """👋 *Welcome to Ailigent!*

I'm your intelligent employee assistant. I can help you with:
• Leave balance and requests
• Payslip information
• Attendance tracking
• Task management
• Company policies
• Daily work summaries

*Quick Commands:*
/link - Link your Telegram account
/help - Show all commands

Let's get started! Use /link to connect your employee account.""",
        "ar": """👋 *مرحباً بك في أيليجنت!*

أنا مساعدك الذكي للموظفين. يمكنني مساعدتك في:
• رصيد الإجازات والطلبات
• معلومات كشف الراتب
• متابعة الحضور والانصراف
• إدارة المهام
• سياسات الشركة
• ملخصات العمل اليومية

*الأوامر السريعة:*
/link - ربط حسابك
/help - عرض جميع الأوامر

لنبدأ! استخدم /link لربط حساب الموظف الخاص بك.""",
    },
    "welcome_linked": {
        "en": "👋 *Welcome back, {name}!*\n\nHow can I help you today? Type your question or use /help to see available commands.",
        "ar": "👋 *أهلاً بعودتك، {name}!*\n\nكيف يمكنني مساعدتك اليوم؟ اكتب سؤالك أو استخدم /help لعرض الأوامر المتاحة.",
    },
    "help": {
        "en": """📚 *Available Commands*

*Account:*
/start - Start the bot
/link - Link your Telegram to employee account
/unlink - Unlink your account

*Information:*
/leave - View leave balance and requests
/payslip - View recent payslips
/attendance - View attendance summary
/tasks - View your tasks
/summary - Get daily work summary
/policy - Search company policies

/help - Show this help message
/cancel - Cancel current operation

You can also just type your question and I'll help you!""",
        "ar": """📚 *الأوامر المتاحة*

*الحساب:*
/start - بدء البوت
/link - ربط حسابك بحساب الموظف
/unlink - إلغاء ربط حسابك

*المعلومات:*
/leave - عرض رصيد الإجازات والطلبات
/payslip - عرض كشوف الرواتب الأخيرة
/attendance - عرض ملخص الحضور
/tasks - عرض مهامك
/summary - الحصول على ملخص العمل اليومي
/policy - البحث في سياسات الشركة

/help - عرض هذه المساعدة
/cancel - إلغاء العملية الحالية

يمكنك أيضاً كتابة سؤالك مباشرة وسأساعدك!""",
    },
    "not_linked": {
        "en": "⚠️ Your account is not linked yet. Please use /link to connect your employee account first.",
        "ar": "⚠️ حسابك غير مرتبط بعد. يرجى استخدام /link لربط حساب الموظف الخاص بك أولاً.",
    },
    "link_start": {
        "en": "📧 Please enter your work email address to link your account:",
        "ar": "📧 يرجى إدخال بريدك الإلكتروني الخاص بالعمل لربط حسابك:",
    },
    "link_email_not_found": {
        "en": "❌ No employee found with this email. Please check and try again, or contact HR.",
        "ar": "❌ لم يتم العثور على موظف بهذا البريد الإلكتروني. يرجى التحقق والمحاولة مرة أخرى، أو التواصل مع الموارد البشرية.",
    },
    "link_otp_sent": {
        "en": "✅ A verification code has been sent to your email.\n\n📬 Please enter the 6-digit code:",
        "ar": "✅ تم إرسال رمز التحقق إلى بريدك الإلكتروني.\n\n📬 يرجى إدخال الرمز المكون من 6 أرقام:",
    },
    "link_otp_invalid": {
        "en": "❌ Invalid code. Please try again or use /cancel to start over.",
        "ar": "❌ رمز غير صحيح. يرجى المحاولة مرة أخرى أو استخدام /cancel للبدء من جديد.",
    },
    "link_otp_expired": {
        "en": "⏰ The verification code has expired. Please use /link to start again.",
        "ar": "⏰ انتهت صلاحية رمز التحقق. يرجى استخدام /link للبدء مرة أخرى.",
    },
    "link_success": {
        "en": "🎉 *Account linked successfully!*\n\nWelcome, {name}! You can now use all features. Type /help to see available commands.",
        "ar": "🎉 *تم ربط الحساب بنجاح!*\n\nأهلاً بك، {name}! يمكنك الآن استخدام جميع الميزات. اكتب /help لعرض الأوامر المتاحة.",
    },
    "link_already": {
        "en": "✅ Your account is already linked. Use /unlink if you want to disconnect.",
        "ar": "✅ حسابك مرتبط بالفعل. استخدم /unlink إذا كنت تريد إلغاء الربط.",
    },
    "unlink_confirm": {
        "en": "Are you sure you want to unlink your account?",
        "ar": "هل أنت متأكد من إلغاء ربط حسابك؟",
    },
    "unlink_success": {
        "en": "✅ Your account has been unlinked successfully.",
        "ar": "✅ تم إلغاء ربط حسابك بنجاح.",
    },
    "cancelled": {
        "en": "❌ Operation cancelled.",
        "ar": "❌ تم إلغاء العملية.",
    },
    "no_leave_balance": {
        "en": "📋 No leave allocations found.",
        "ar": "📋 لم يتم العثور على مخصصات إجازات.",
    },
    "no_payslips": {
        "en": "📋 No payslips found.",
        "ar": "📋 لم يتم العثور على كشوف رواتب.",
    },
    "no_tasks": {
        "en": "📋 No tasks assigned to you.",
        "ar": "📋 لا توجد مهام مسندة إليك.",
    },
    "no_policies": {
        "en": "📋 No policies found.",
        "ar": "📋 لم يتم العثور على سياسات.",
    },
    "error": {
        "en": "❌ An error occurred. Please try again later.",
        "ar": "❌ حدث خطأ. يرجى المحاولة لاحقاً.",
    },
}


def get_user_language(update: Update) -> str:
    """Detect user's preferred language"""
    # Check if user has sent Arabic text before
    if update.message and update.message.text:
        import re
        arabic_pattern = re.compile(r"[\u0600-\u06FF]")
        if arabic_pattern.search(update.message.text):
            return "ar"
    # Check Telegram language setting
    if update.effective_user and update.effective_user.language_code:
        if update.effective_user.language_code.startswith("ar"):
            return "ar"
    return "en"


def msg(key: str, lang: str, **kwargs) -> str:
    """Get message in specified language"""
    text = MESSAGES.get(key, {}).get(lang, MESSAGES.get(key, {}).get("en", ""))
    if kwargs:
        text = text.format(**kwargs)
    return text


async def is_user_linked(telegram_id: int) -> tuple[bool, int | None]:
    """Check if user is linked and return employee_id"""
    employee_id = await _odoo_service.get_employee_by_telegram(telegram_id)
    return (True, employee_id) if employee_id else (False, None)


# ==================== Command Handlers ====================

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /start command"""
    lang = get_user_language(update)
    telegram_id = update.effective_user.id

    linked, employee_id = await is_user_linked(telegram_id)

    if linked:
        employee = await _odoo_service.get_employee_by_id(employee_id)
        name = employee.name if employee else "User"
        await update.message.reply_text(
            msg("welcome_linked", lang, name=name),
            parse_mode="Markdown",
        )
    else:
        await update.message.reply_text(
            msg("welcome", lang),
            parse_mode="Markdown",
        )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /help command"""
    lang = get_user_language(update)
    await update.message.reply_text(msg("help", lang), parse_mode="Markdown")


async def cancel_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle /cancel command"""
    lang = get_user_language(update)
    otp_manager.clear_session(update.effective_user.id)
    await update.message.reply_text(msg("cancelled", lang))
    return ConversationHandler.END


# ==================== Link Account Flow ====================

async def link_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Start the account linking process"""
    lang = get_user_language(update)
    telegram_id = update.effective_user.id

    linked, _ = await is_user_linked(telegram_id)
    if linked:
        await update.message.reply_text(msg("link_already", lang))
        return ConversationHandler.END

    await update.message.reply_text(msg("link_start", lang))
    return AWAITING_EMAIL


async def link_email(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle email input during linking"""
    lang = get_user_language(update)
    email = update.message.text.strip().lower()
    telegram_id = update.effective_user.id
    telegram_username = update.effective_user.username

    # Find employee by email
    employee = await _odoo_service.find_employee_by_email(email)

    if not employee:
        await update.message.reply_text(msg("link_email_not_found", lang))
        return AWAITING_EMAIL

    # Generate OTP and create session
    otp = otp_manager.create_session(
        telegram_id=telegram_id,
        employee_id=employee.id,
        employee_email=email,
    )

    # Send OTP email
    email_sent = await send_otp_email(
        odoo_service=_odoo_service,
        employee_email=email,
        employee_name=employee.name,
        otp=otp,
    )

    if not email_sent:
        logger.warning(f"Failed to send OTP email to {email}, but continuing...")
        # DEMO MODE: Show OTP directly when email fails (remove in production!)
        demo_msg = {
            "en": f"⚠️ Email server not configured. For demo, use this code: **{otp}**\n\nEnter the 6-digit code:",
            "ar": f"⚠️ خادم البريد غير مكون. للعرض التوضيحي، استخدم هذا الرمز: **{otp}**\n\nأدخل الرمز المكون من 6 أرقام:",
        }
        await update.message.reply_text(demo_msg.get(lang, demo_msg["en"]), parse_mode="Markdown")
        return AWAITING_OTP

    await update.message.reply_text(msg("link_otp_sent", lang))
    return AWAITING_OTP


async def link_verify_otp(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Verify OTP code"""
    lang = get_user_language(update)
    otp_input = update.message.text.strip()
    telegram_id = update.effective_user.id
    telegram_username = update.effective_user.username

    success, session_data = otp_manager.verify_otp(telegram_id, otp_input)

    if not success:
        # Check if session expired or max attempts
        session = otp_manager.get_session(telegram_id)
        if not session:
            await update.message.reply_text(msg("link_otp_expired", lang))
            return ConversationHandler.END

        await update.message.reply_text(msg("link_otp_invalid", lang))
        return AWAITING_OTP

    # Link successful - save to Odoo
    await _odoo_service.save_telegram_link(
        telegram_id=telegram_id,
        employee_id=session_data["employee_id"],
        telegram_username=telegram_username,
    )

    # Get employee name for welcome message
    employee = await _odoo_service.get_employee_by_id(session_data["employee_id"])
    name = employee.name if employee else "User"

    await update.message.reply_text(
        msg("link_success", lang, name=name),
        parse_mode="Markdown",
    )
    return ConversationHandler.END


# ==================== Unlink Account ====================

async def unlink_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /unlink command"""
    lang = get_user_language(update)
    telegram_id = update.effective_user.id

    linked, _ = await is_user_linked(telegram_id)
    if not linked:
        await update.message.reply_text(msg("not_linked", lang))
        return

    keyboard = [
        [
            InlineKeyboardButton("Yes / نعم", callback_data="unlink_yes"),
            InlineKeyboardButton("No / لا", callback_data="unlink_no"),
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(
        msg("unlink_confirm", lang),
        reply_markup=reply_markup,
    )


async def unlink_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle unlink confirmation callback"""
    query = update.callback_query
    await query.answer()

    lang = "ar" if query.from_user.language_code and query.from_user.language_code.startswith("ar") else "en"

    if query.data == "unlink_yes":
        await _odoo_service.remove_telegram_link(query.from_user.id)
        _gemini_service.clear_session(query.from_user.id)
        await query.edit_message_text(msg("unlink_success", lang))
    else:
        await query.edit_message_text(msg("cancelled", lang))


# ==================== Information Commands ====================

async def leave_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /leave command - show leave balance"""
    lang = get_user_language(update)
    telegram_id = update.effective_user.id

    linked, employee_id = await is_user_linked(telegram_id)
    if not linked:
        await update.message.reply_text(msg("not_linked", lang))
        return

    balances = await _odoo_service.get_leave_balance(employee_id)

    if not balances:
        await update.message.reply_text(msg("no_leave_balance", lang))
        return

    if lang == "ar":
        text = "📊 *رصيد إجازاتك:*\n\n"
        for b in balances:
            text += f"*{b.leave_type}*\n"
            text += f"  • المخصص: {b.allocated} يوم\n"
            text += f"  • المستخدم: {b.taken} يوم\n"
            text += f"  • المتبقي: {b.remaining} يوم\n\n"
    else:
        text = "📊 *Your Leave Balance:*\n\n"
        for b in balances:
            text += f"*{b.leave_type}*\n"
            text += f"  • Allocated: {b.allocated} days\n"
            text += f"  • Taken: {b.taken} days\n"
            text += f"  • Remaining: {b.remaining} days\n\n"

    await update.message.reply_text(text, parse_mode="Markdown")


async def payslip_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /payslip command - show recent payslips"""
    lang = get_user_language(update)
    telegram_id = update.effective_user.id

    linked, employee_id = await is_user_linked(telegram_id)
    if not linked:
        await update.message.reply_text(msg("not_linked", lang))
        return

    payslips = await _odoo_service.get_payslips(employee_id, limit=3)

    if not payslips:
        await update.message.reply_text(msg("no_payslips", lang))
        return

    if lang == "ar":
        text = "💰 *كشوف الرواتب الأخيرة:*\n\n"
        for ps in payslips:
            text += f"*{ps.name}*\n"
            text += f"  • الفترة: {ps.date_from} - {ps.date_to}\n"
            text += f"  • الصافي: {ps.net_wage:,.2f}\n"
            text += f"  • الحالة: {ps.state}\n\n"
    else:
        text = "💰 *Recent Payslips:*\n\n"
        for ps in payslips:
            text += f"*{ps.name}*\n"
            text += f"  • Period: {ps.date_from} - {ps.date_to}\n"
            text += f"  • Net: {ps.net_wage:,.2f}\n"
            text += f"  • Status: {ps.state}\n\n"

    await update.message.reply_text(text, parse_mode="Markdown")


async def attendance_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /attendance command - show attendance summary"""
    lang = get_user_language(update)
    telegram_id = update.effective_user.id

    linked, employee_id = await is_user_linked(telegram_id)
    if not linked:
        await update.message.reply_text(msg("not_linked", lang))
        return

    summary = await _odoo_service.get_attendance_summary(employee_id)

    if not summary or summary.get("total_days", 0) == 0:
        if lang == "ar":
            await update.message.reply_text("📋 لا توجد سجلات حضور لهذا الشهر.")
        else:
            await update.message.reply_text("📋 No attendance records for this month.")
        return

    if lang == "ar":
        text = f"📅 *ملخص الحضور - {summary['month']}/{summary['year']}*\n\n"
        text += f"• إجمالي أيام العمل: {summary['total_days']}\n"
        text += f"• إجمالي ساعات العمل: {summary['total_hours']}\n"
    else:
        text = f"📅 *Attendance Summary - {summary['month']}/{summary['year']}*\n\n"
        text += f"• Total working days: {summary['total_days']}\n"
        text += f"• Total working hours: {summary['total_hours']}\n"

    await update.message.reply_text(text, parse_mode="Markdown")


async def tasks_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /tasks command - show assigned tasks"""
    lang = get_user_language(update)
    telegram_id = update.effective_user.id

    linked, employee_id = await is_user_linked(telegram_id)
    if not linked:
        await update.message.reply_text(msg("not_linked", lang))
        return

    tasks = await _odoo_service.get_employee_tasks(employee_id)

    if not tasks:
        await update.message.reply_text(msg("no_tasks", lang))
        return

    if lang == "ar":
        text = "📋 *مهامك:*\n\n"
        for i, task in enumerate(tasks[:10], 1):
            stage = task.get("stage_id", [None, ""])[1] if task.get("stage_id") else ""
            deadline = task.get("date_deadline", "غير محدد") or "غير محدد"
            text += f"{i}. *{task.get('name', 'بدون اسم')}*\n"
            text += f"   المرحلة: {stage}\n"
            text += f"   الموعد النهائي: {deadline}\n\n"
    else:
        text = "📋 *Your Tasks:*\n\n"
        for i, task in enumerate(tasks[:10], 1):
            stage = task.get("stage_id", [None, ""])[1] if task.get("stage_id") else ""
            deadline = task.get("date_deadline", "Not set") or "Not set"
            text += f"{i}. *{task.get('name', 'Unnamed')}*\n"
            text += f"   Stage: {stage}\n"
            text += f"   Deadline: {deadline}\n\n"

    await update.message.reply_text(text, parse_mode="Markdown")


async def summary_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /summary command - generate daily work summary"""
    lang = get_user_language(update)
    telegram_id = update.effective_user.id

    linked, employee_id = await is_user_linked(telegram_id)
    if not linked:
        await update.message.reply_text(msg("not_linked", lang))
        return

    # Get employee data
    employee = await _odoo_service.get_employee_by_id(employee_id)
    attendance = await _odoo_service.get_attendance_summary(employee_id)
    tasks = await _odoo_service.get_employee_tasks(employee_id)
    leave_balance = await _odoo_service.get_leave_balance(employee_id)

    # Prepare data for summary
    employee_data = {
        "name": employee.name if employee else "Employee",
        "department": employee.department if employee else "",
        "hours_today": attendance.get("total_hours", 0) if attendance else 0,
        "check_in": "N/A",
        "check_out": "N/A",
        "completed_tasks": len([t for t in tasks if t.get("stage_id", [None, ""])[1] == "Done"]) if tasks else 0,
        "pending_tasks": len([t for t in tasks if t.get("stage_id", [None, ""])[1] != "Done"]) if tasks else 0,
        "leave_balance": f"{leave_balance[0].remaining} days" if leave_balance else "N/A",
    }

    # Generate summary using AI
    if lang == "ar":
        await update.message.reply_text("⏳ جاري إنشاء ملخصك اليومي...")
    else:
        await update.message.reply_text("⏳ Generating your daily summary...")

    summary = await _gemini_service.generate_daily_summary(employee_data, lang)
    await update.message.reply_text(summary, parse_mode="Markdown")


async def policy_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /policy command - show company policies"""
    lang = get_user_language(update)
    telegram_id = update.effective_user.id

    linked, _ = await is_user_linked(telegram_id)
    if not linked:
        await update.message.reply_text(msg("not_linked", lang))
        return

    policies = await _odoo_service.get_company_policies()

    if not policies:
        await update.message.reply_text(msg("no_policies", lang))
        return

    if lang == "ar":
        text = "📜 *سياسات الشركة:*\n\n"
        for i, policy in enumerate(policies[:10], 1):
            text += f"{i}. {policy.get('name', 'غير مسمى')}\n"
        text += "\nاسألني عن أي سياسة للحصول على تفاصيل!"
    else:
        text = "📜 *Company Policies:*\n\n"
        for i, policy in enumerate(policies[:10], 1):
            text += f"{i}. {policy.get('name', 'Unnamed')}\n"
        text += "\nAsk me about any policy for details!"

    await update.message.reply_text(text, parse_mode="Markdown")


# ==================== AI Conversation Handler ====================

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle free-form messages using AI"""
    lang = get_user_language(update)
    telegram_id = update.effective_user.id
    message_text = update.message.text

    linked, employee_id = await is_user_linked(telegram_id)

    if not linked:
        await update.message.reply_text(msg("not_linked", lang))
        return

    # Get employee context
    employee = await _odoo_service.get_employee_by_id(employee_id)

    # Build context for AI with employee_id for MCP tools
    ai_context = {
        "employee_id": employee_id,  # Required for MCP tool calls
        "employee_name": employee.name if employee else "",
        "department": employee.department if employee else "",
        "job_title": employee.job_title if employee else "",
    }

    # The AI will now use MCP tools to fetch data as needed
    # No need to pre-fetch data - Gemini will call the appropriate tools

    # Process with AI (supports MCP function calling)
    response = await _gemini_service.process_message(
        user_id=telegram_id,
        message=message_text,
        context=ai_context,
    )

    await update.message.reply_text(response, parse_mode="Markdown")


# ==================== Error Handler ====================

async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle errors"""
    logger.error(f"Update {update} caused error {context.error}")
    if update and update.effective_message:
        lang = get_user_language(update)
        await update.effective_message.reply_text(msg("error", lang))


# ==================== Setup Function ====================

def setup_handlers(
    app: Application,
    odoo_service: OdooService,
    gemini_service: GeminiService,
) -> None:
    """Setup all bot handlers"""
    global _odoo_service, _gemini_service
    _odoo_service = odoo_service
    _gemini_service = gemini_service

    # Link account conversation handler
    link_handler = ConversationHandler(
        entry_points=[CommandHandler("link", link_start)],
        states={
            AWAITING_EMAIL: [MessageHandler(filters.TEXT & ~filters.COMMAND, link_email)],
            AWAITING_OTP: [MessageHandler(filters.TEXT & ~filters.COMMAND, link_verify_otp)],
        },
        fallbacks=[CommandHandler("cancel", cancel_command)],
    )

    # Add handlers
    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(link_handler)
    app.add_handler(CommandHandler("unlink", unlink_command))
    app.add_handler(CallbackQueryHandler(unlink_callback, pattern="^unlink_"))
    app.add_handler(CommandHandler("leave", leave_command))
    app.add_handler(CommandHandler("payslip", payslip_command))
    app.add_handler(CommandHandler("attendance", attendance_command))
    app.add_handler(CommandHandler("tasks", tasks_command))
    app.add_handler(CommandHandler("summary", summary_command))
    app.add_handler(CommandHandler("policy", policy_command))
    app.add_handler(CommandHandler("cancel", cancel_command))

    # Message handler for AI conversations (must be last)
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    # Error handler
    app.add_error_handler(error_handler)

    logger.info("Bot handlers configured successfully")
