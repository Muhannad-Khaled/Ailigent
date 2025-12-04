"""Constants for the Contracts Agent."""

# Odoo Model Names
ODOO_ATTACHMENT_MODEL = "ir.attachment"
ODOO_PARTNER_MODEL = "res.partner"
ODOO_PROJECT_MODEL = "project.project"
ODOO_INVOICE_MODEL = "account.move"
ODOO_EMPLOYEE_MODEL = "hr.employee"

# Attachment fields to fetch
ATTACHMENT_FIELDS = [
    "id",
    "name",
    "datas",
    "mimetype",
    "file_size",
    "create_date",
    "write_date",
    "res_model",
    "res_id",
    "description",
]

# Contract document mimetypes
SUPPORTED_MIMETYPES = [
    "application/pdf",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",  # docx
    "application/msword",  # doc
]

# Contract status values
CONTRACT_STATUS_DRAFT = "draft"
CONTRACT_STATUS_ACTIVE = "active"
CONTRACT_STATUS_EXPIRING_SOON = "expiring_soon"
CONTRACT_STATUS_EXPIRED = "expired"
CONTRACT_STATUS_TERMINATED = "terminated"
CONTRACT_STATUS_RENEWED = "renewed"

# Clause types
CLAUSE_TYPE_PAYMENT_TERMS = "payment_terms"
CLAUSE_TYPE_DELIVERY = "delivery"
CLAUSE_TYPE_WARRANTY = "warranty"
CLAUSE_TYPE_LIABILITY = "liability"
CLAUSE_TYPE_TERMINATION = "termination"
CLAUSE_TYPE_CONFIDENTIALITY = "confidentiality"
CLAUSE_TYPE_PENALTY = "penalty"
CLAUSE_TYPE_RENEWAL = "renewal"
CLAUSE_TYPE_FORCE_MAJEURE = "force_majeure"
CLAUSE_TYPE_COMPLIANCE = "compliance"
CLAUSE_TYPE_OTHER = "other"

# Risk levels
RISK_LEVEL_LOW = "low"
RISK_LEVEL_MEDIUM = "medium"
RISK_LEVEL_HIGH = "high"
RISK_LEVEL_CRITICAL = "critical"

# Milestone status values
MILESTONE_STATUS_PENDING = "pending"
MILESTONE_STATUS_IN_PROGRESS = "in_progress"
MILESTONE_STATUS_COMPLETED = "completed"
MILESTONE_STATUS_OVERDUE = "overdue"
MILESTONE_STATUS_AT_RISK = "at_risk"

# Compliance status values
COMPLIANCE_STATUS_COMPLIANT = "compliant"
COMPLIANCE_STATUS_NON_COMPLIANT = "non_compliant"
COMPLIANCE_STATUS_PENDING_REVIEW = "pending_review"
COMPLIANCE_STATUS_EXEMPTED = "exempted"

# Webhook event types
EVENT_CONTRACT_EXPIRING = "contract.expiring"
EVENT_CONTRACT_EXPIRED = "contract.expired"
EVENT_CONTRACT_RENEWED = "contract.renewed"
EVENT_MILESTONE_UPCOMING = "milestone.upcoming"
EVENT_MILESTONE_OVERDUE = "milestone.overdue"
EVENT_MILESTONE_COMPLETED = "milestone.completed"
EVENT_COMPLIANCE_ALERT = "compliance.alert"
EVENT_COMPLIANCE_RESOLVED = "compliance.resolved"
EVENT_ANALYSIS_COMPLETE = "analysis.complete"
EVENT_REPORT_READY = "report.ready"
