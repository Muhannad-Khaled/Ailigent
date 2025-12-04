"""Application constants."""

# Task priorities
PRIORITY_LOW = "0"
PRIORITY_NORMAL = "1"
PRIORITY_HIGH = "2"
PRIORITY_URGENT = "3"

PRIORITY_LABELS = {
    PRIORITY_LOW: "Low",
    PRIORITY_NORMAL: "Normal",
    PRIORITY_HIGH: "High",
    PRIORITY_URGENT: "Urgent",
}

# Kanban states
KANBAN_NORMAL = "normal"
KANBAN_DONE = "done"
KANBAN_BLOCKED = "blocked"

# Odoo model names
ODOO_MODEL_TASK = "project.task"
ODOO_MODEL_PROJECT = "project.project"
ODOO_MODEL_STAGE = "project.task.type"
ODOO_MODEL_USER = "res.users"
ODOO_MODEL_EMPLOYEE = "hr.employee"
ODOO_MODEL_DEPARTMENT = "hr.department"

# Default task fields to fetch from Odoo 18
# Note: planned_hours/remaining_hours/effective_hours/kanban_state don't exist in Odoo 18 base project
# Using allocated_hours and state instead
DEFAULT_TASK_FIELDS = [
    "id",
    "name",
    "project_id",
    "user_ids",
    "stage_id",
    "date_deadline",
    "date_assign",
    "priority",
    "tag_ids",
    "allocated_hours",
    "description",
    "create_date",
    "write_date",
    "parent_id",
    "child_ids",
    "date_last_stage_update",
    "state",
]

# Default employee fields
DEFAULT_EMPLOYEE_FIELDS = [
    "id",
    "name",
    "user_id",
    "work_email",
    "department_id",
    "job_title",
    "parent_id",
]

# Workload thresholds
WORKLOAD_OVERLOADED_THRESHOLD = 0.8  # 80% utilization
WORKLOAD_UNDERUTILIZED_THRESHOLD = 0.5  # 50% utilization
DEFAULT_WEEKLY_HOURS = 40

# Cache TTL (seconds)
CACHE_TTL_SHORT = 300  # 5 minutes
CACHE_TTL_MEDIUM = 900  # 15 minutes
CACHE_TTL_LONG = 3600  # 1 hour

# Bottleneck thresholds
BOTTLENECK_STAGE_CONGESTION = 0.3  # >30% of tasks in one stage
BOTTLENECK_BLOCKED_RATIO = 0.1  # >10% blocked = process issue
BOTTLENECK_AVG_TIME_MULTIPLIER = 2.0  # 2x average = bottleneck

# Report types
REPORT_DAILY = "daily"
REPORT_WEEKLY = "weekly"
REPORT_MONTHLY = "monthly"

# Severity levels
SEVERITY_CRITICAL = "critical"
SEVERITY_HIGH = "high"
SEVERITY_MEDIUM = "medium"
SEVERITY_LOW = "low"
