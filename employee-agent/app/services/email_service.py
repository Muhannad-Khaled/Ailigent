from typing import TYPE_CHECKING
from loguru import logger

if TYPE_CHECKING:
    from app.services.odoo_service import OdooService


async def send_otp_email(
    odoo_service: "OdooService",
    employee_email: str,
    employee_name: str,
    otp: str,
) -> bool:
    """
    Send OTP verification email via Odoo mail.mail model.

    Args:
        odoo_service: Connected OdooService instance
        employee_email: Employee's work email address
        employee_name: Employee's name for personalization
        otp: The OTP code to send

    Returns:
        True if email was sent successfully, False otherwise
    """
    try:
        # Email content in both Arabic and English
        subject = "Ailigent - Verification Code | رمز التحقق"

        body_html = f"""
        <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px;">
            <div style="text-align: center; margin-bottom: 30px;">
                <h1 style="color: #2563eb;">Ailigent</h1>
                <p style="color: #6b7280;">Internal Employee Agent</p>
            </div>

            <div style="background: #f3f4f6; border-radius: 10px; padding: 30px; text-align: center;">
                <h2 style="color: #1f2937; margin-bottom: 10px;">Hello {employee_name},</h2>
                <p style="color: #4b5563; margin-bottom: 20px;">
                    Your verification code for linking your Telegram account is:
                </p>
                <div style="background: #2563eb; color: white; font-size: 32px; font-weight: bold;
                            letter-spacing: 8px; padding: 15px 30px; border-radius: 8px; display: inline-block;">
                    {otp}
                </div>
                <p style="color: #6b7280; margin-top: 20px; font-size: 14px;">
                    This code will expire in 10 minutes.
                </p>
            </div>

            <hr style="border: none; border-top: 1px solid #e5e7eb; margin: 30px 0;">

            <div style="background: #f3f4f6; border-radius: 10px; padding: 30px; text-align: center; direction: rtl;">
                <h2 style="color: #1f2937; margin-bottom: 10px;">مرحباً {employee_name}،</h2>
                <p style="color: #4b5563; margin-bottom: 20px;">
                    رمز التحقق لربط حساب تيليجرام الخاص بك هو:
                </p>
                <div style="background: #2563eb; color: white; font-size: 32px; font-weight: bold;
                            letter-spacing: 8px; padding: 15px 30px; border-radius: 8px; display: inline-block;">
                    {otp}
                </div>
                <p style="color: #6b7280; margin-top: 20px; font-size: 14px;">
                    سينتهي هذا الرمز خلال 10 دقائق.
                </p>
            </div>

            <div style="text-align: center; margin-top: 30px; color: #9ca3af; font-size: 12px;">
                <p>If you did not request this code, please ignore this email.</p>
                <p style="direction: rtl;">إذا لم تطلب هذا الرمز، يرجى تجاهل هذا البريد الإلكتروني.</p>
            </div>
        </div>
        """

        # Create mail using Odoo's mail.mail model
        mail_id = odoo_service._execute(
            "mail.mail",
            "create",
            [{
                "subject": subject,
                "body_html": body_html,
                "email_to": employee_email,
                "email_from": "noreply@ailigent.local",
                "auto_delete": True,
            }],
        )

        if mail_id:
            # Handle both single ID and list of IDs (Odoo 18 compatibility)
            if isinstance(mail_id, list):
                mail_id = mail_id[0]

            # Send the email immediately using proper Odoo 18 syntax
            odoo_service.models.execute_kw(
                odoo_service.db,
                odoo_service.uid,
                odoo_service.password,
                "mail.mail",
                "send",
                [[mail_id]],
                {}
            )
            logger.info(f"OTP email sent successfully to {employee_email}")
            return True

        logger.error(f"Failed to create mail record for {employee_email}")
        return False

    except Exception as e:
        logger.error(f"Error sending OTP email to {employee_email}: {e}")
        return False
