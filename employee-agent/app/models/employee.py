from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class Employee(BaseModel):
    """Employee data from Odoo"""
    id: int
    name: str
    email: Optional[str] = None
    job_title: Optional[str] = None
    department: Optional[str] = None
    manager_name: Optional[str] = None
    work_phone: Optional[str] = None
    mobile_phone: Optional[str] = None


class EmployeeLink(BaseModel):
    """Link between Telegram user and Odoo employee"""
    telegram_id: int
    telegram_username: Optional[str] = None
    odoo_employee_id: int
    employee_email: str
    linked_at: datetime
    is_verified: bool = False
    verification_code: Optional[str] = None


class LeaveBalance(BaseModel):
    """Employee leave balance"""
    leave_type: str
    allocated: float
    taken: float
    remaining: float


class LeaveRequest(BaseModel):
    """Leave request details"""
    id: int
    leave_type: str
    date_from: str
    date_to: str
    number_of_days: float
    state: str
    reason: Optional[str] = None


class PayslipSummary(BaseModel):
    """Payslip summary"""
    id: int
    name: str
    date_from: str
    date_to: str
    state: str
    net_wage: float
    gross_wage: float


class Task(BaseModel):
    """Task/Activity from conversation"""
    id: Optional[int] = None
    name: str
    description: Optional[str] = None
    employee_id: int
    due_date: Optional[str] = None
    priority: str = "normal"
    state: str = "pending"
    created_from_chat: bool = True


class VerificationSession(BaseModel):
    """OTP verification session for linking Telegram to Odoo"""
    telegram_id: int
    telegram_username: Optional[str] = None
    employee_id: int
    employee_email: str
    otp_code: str
    created_at: datetime
    expires_at: datetime
    attempts: int = 0


class ConversationContext(BaseModel):
    """Context for AI conversation"""
    employee_id: int
    employee_name: str
    department: Optional[str] = None
    job_title: Optional[str] = None
    language: str = "en"  # 'en' or 'ar'
    last_topic: Optional[str] = None
