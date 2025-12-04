"""Application constants for HR Agent."""

# Odoo Models
ODOO_MODEL_EMPLOYEE = "hr.employee"
ODOO_MODEL_DEPARTMENT = "hr.department"
ODOO_MODEL_JOB = "hr.job"
ODOO_MODEL_APPLICANT = "hr.applicant"
ODOO_MODEL_CANDIDATE = "hr.candidate"
ODOO_MODEL_RECRUITMENT_STAGE = "hr.recruitment.stage"
ODOO_MODEL_APPRAISAL = "hr.appraisal"
ODOO_MODEL_APPRAISAL_GOAL = "hr.appraisal.goal"
ODOO_MODEL_APPRAISAL_NOTE = "hr.appraisal.note"
ODOO_MODEL_ATTENDANCE = "hr.attendance"
ODOO_MODEL_LEAVE = "hr.leave"
ODOO_MODEL_LEAVE_TYPE = "hr.leave.type"
ODOO_MODEL_LEAVE_ALLOCATION = "hr.leave.allocation"
ODOO_MODEL_CONTRACT = "hr.contract"
ODOO_MODEL_CALENDAR_EVENT = "calendar.event"
ODOO_MODEL_ATTACHMENT = "ir.attachment"
ODOO_MODEL_USER = "res.users"

# Applicant Stages (common names, may vary by Odoo instance)
STAGE_NEW = "New"
STAGE_INITIAL_QUALIFICATION = "Initial Qualification"
STAGE_FIRST_INTERVIEW = "First Interview"
STAGE_SECOND_INTERVIEW = "Second Interview"
STAGE_CONTRACT_PROPOSAL = "Contract Proposal"
STAGE_HIRED = "Hired"
STAGE_REFUSED = "Refused"

# Appraisal States
APPRAISAL_STATE_NEW = "new"
APPRAISAL_STATE_PENDING = "pending"
APPRAISAL_STATE_DONE = "done"
APPRAISAL_STATE_CANCEL = "cancel"

# Leave Request States
LEAVE_STATE_DRAFT = "draft"
LEAVE_STATE_CONFIRM = "confirm"
LEAVE_STATE_VALIDATE = "validate"
LEAVE_STATE_VALIDATE1 = "validate1"
LEAVE_STATE_REFUSE = "refuse"

# Contract States
CONTRACT_STATE_DRAFT = "draft"
CONTRACT_STATE_OPEN = "open"
CONTRACT_STATE_CLOSE = "close"
CONTRACT_STATE_CANCEL = "cancel"

# CV Analysis Scores
SCORE_STRONG_HIRE = "strong_hire"
SCORE_HIRE = "hire"
SCORE_MAYBE = "maybe"
SCORE_NO_HIRE = "no_hire"

# Report Types
REPORT_HEADCOUNT = "headcount"
REPORT_TURNOVER = "turnover"
REPORT_DEPARTMENT = "department"
REPORT_ATTENDANCE = "attendance"
REPORT_LEAVE_BALANCE = "leave_balance"
REPORT_APPRAISAL = "appraisal"

# Export Formats
EXPORT_PDF = "pdf"
EXPORT_EXCEL = "excel"

# Notification Types
NOTIFICATION_INTERVIEW = "interview"
NOTIFICATION_APPRAISAL = "appraisal"
NOTIFICATION_LEAVE = "leave"
NOTIFICATION_REPORT = "report"
NOTIFICATION_ANOMALY = "anomaly"

# Attendance Anomaly Types
ANOMALY_LATE_ARRIVAL = "late_arrival"
ANOMALY_EARLY_DEPARTURE = "early_departure"
ANOMALY_MISSING_CHECKOUT = "missing_checkout"
ANOMALY_EXCESSIVE_OVERTIME = "excessive_overtime"
ANOMALY_PATTERN = "pattern"

# Severity Levels
SEVERITY_LOW = "low"
SEVERITY_MEDIUM = "medium"
SEVERITY_HIGH = "high"

# Time Constants (in hours)
STANDARD_WORK_HOURS = 8
MAX_OVERTIME_HOURS = 4
LATE_THRESHOLD_MINUTES = 15
EARLY_LEAVE_THRESHOLD_MINUTES = 30

# Pagination Defaults
DEFAULT_PAGE_SIZE = 20
MAX_PAGE_SIZE = 100
