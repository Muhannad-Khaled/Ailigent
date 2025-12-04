"""Notification-related Pydantic models."""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class NotificationType(str, Enum):
    """Types of notifications."""

    TASK_OVERDUE = "task.overdue"
    TASK_ASSIGNED = "task.assigned"
    TASK_COMPLETED = "task.completed"
    WORKLOAD_ALERT = "workload.alert"
    REPORT_READY = "report.ready"
    BOTTLENECK_DETECTED = "bottleneck.detected"
    MANAGER_ALERT = "manager.alert"


class NotificationChannel(str, Enum):
    """Notification delivery channels."""

    EMAIL = "email"
    WEBHOOK = "webhook"


class NotificationPayload(BaseModel):
    """Base notification payload."""

    notification_type: NotificationType
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    title: str
    message: str
    data: Dict[str, Any] = Field(default_factory=dict)
    recipients: List[str] = Field(default_factory=list)


class EmailNotification(BaseModel):
    """Email notification details."""

    to_email: str
    subject: str
    html_content: str
    text_content: Optional[str] = None
    cc: List[str] = Field(default_factory=list)
    bcc: List[str] = Field(default_factory=list)


class WebhookPayload(BaseModel):
    """Webhook notification payload."""

    event_type: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    data: Dict[str, Any] = Field(default_factory=dict)
    signature: Optional[str] = None


class OverdueAlertData(BaseModel):
    """Data for overdue task alert."""

    user_id: int
    user_name: str
    user_email: Optional[str] = None
    overdue_tasks: List[Dict[str, Any]] = Field(default_factory=list)
    total_overdue: int = 0
    most_overdue_days: int = 0


class TaskAssignmentData(BaseModel):
    """Data for task assignment notification."""

    task_id: int
    task_name: str
    project_name: Optional[str] = None
    assigned_to_id: int
    assigned_to_name: str
    assigned_by: str = "System"
    deadline: Optional[str] = None
    priority: str = "1"
    estimated_hours: Optional[float] = None


class WorkloadAlertData(BaseModel):
    """Data for workload alert."""

    alert_type: str  # overloaded, rebalance_needed
    affected_employees: List[Dict[str, Any]] = Field(default_factory=list)
    recommendations: List[str] = Field(default_factory=list)
    urgency: str = "medium"


class NotificationResult(BaseModel):
    """Result of sending a notification."""

    success: bool
    channel: NotificationChannel
    recipient: str
    notification_type: NotificationType
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    error_message: Optional[str] = None
    retry_count: int = 0
